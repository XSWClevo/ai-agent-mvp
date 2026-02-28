#!/usr/bin/env python3
"""
MVP agent pipeline: Notion -> local git -> GitHub PR.

Requirements:
- Python 3.10+
- requests
- git + gh CLI

Env vars:
- NOTION_TOKEN
- NOTION_DATABASE_ID
- GITHUB_REPO (e.g. XSWClevo/ai-agent-mvp)
- BRANCH_PREFIX (default: feature)
- DRY_RUN (1 to skip git/gh actions)
- WAIT_FOR_CI (1 to block until `gh pr checks` completes)
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

NOTION_API = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"


@dataclass
class Config:
    notion_token: str
    notion_database_id: str
    github_repo: str
    branch_prefix: str = "feature"
    dry_run: bool = False


@dataclass
class NotionTask:
    page_id: str
    title: str
    description: str
    acceptance: str


def run(cmd: List[str], cwd: Optional[Path] = None) -> None:
    subprocess.run(cmd, cwd=cwd, check=True)


def sh(cmd: List[str], cwd: Optional[Path] = None) -> str:
    res = subprocess.run(cmd, cwd=cwd, check=True, stdout=subprocess.PIPE, text=True)
    return res.stdout.strip()


def load_config() -> Config:
    token = os.environ.get("NOTION_TOKEN", "").strip()
    dbid = os.environ.get("NOTION_DATABASE_ID", "").strip()
    repo = os.environ.get("GITHUB_REPO", "").strip()
    if not token or not dbid or not repo:
        print("Missing required env vars: NOTION_TOKEN, NOTION_DATABASE_ID, GITHUB_REPO", file=sys.stderr)
        sys.exit(2)
    return Config(
        notion_token=token,
        notion_database_id=dbid,
        github_repo=repo,
        branch_prefix=os.environ.get("BRANCH_PREFIX", "feature").strip() or "feature",
        dry_run=os.environ.get("DRY_RUN", "").strip() == "1",
    )


def notion_headers(token: str) -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


def notion_query_tasks(cfg: Config) -> List[NotionTask]:
    url = f"{NOTION_API}/databases/{cfg.notion_database_id}/query"
    payload = {
        "filter": {
            "property": "状态",
            "status": {"equals": "待处理"},
        }
    }
    res = requests.post(url, headers=notion_headers(cfg.notion_token), json=payload, timeout=30)
    res.raise_for_status()
    data = res.json()
    tasks: List[NotionTask] = []
    for page in data.get("results", []):
        props = page.get("properties", {})
        title_parts = props.get("标题", {}).get("title", [])
        title = "".join(t.get("plain_text", "") for t in title_parts).strip() or "Untitled"
        desc_parts = props.get("描述/复现步骤", {}).get("rich_text", [])
        desc = "".join(t.get("plain_text", "") for t in desc_parts).strip()
        acc_parts = props.get("验收标准/解决方案", {}).get("rich_text", [])
        acc = "".join(t.get("plain_text", "") for t in acc_parts).strip()
        tasks.append(NotionTask(page_id=page["id"], title=title, description=desc, acceptance=acc))
    return tasks


def build_spec(task: NotionTask) -> str:
    return (
        "# 功能概述\n"
        f"- 目标：{task.title}\n"
        f"- 背景：{task.description or '待补充'}\n\n"
        "# 需求范围\n"
        "- Must：\n"
        "- Should：\n"
        "- Optional：\n\n"
        "# 约束/依赖\n"
        "- 约束：\n"
        "- 依赖：\n\n"
        "# 接口/数据\n"
        "- 输入：\n"
        "- 输出：\n"
        "- 数据结构：\n\n"
        "# 验收标准\n"
        "- [ ] \n"
        "- [ ] \n\n"
        "# 测试点\n"
        "- [ ] \n"
        "- [ ] \n\n"
        "# 风险/待确认\n"
        "- \n"
    )

def build_section(title: str, body: str) -> str:
    return f"## {title}\n{body.strip()}\n"

def append_section(existing: str, title: str, body: str) -> str:
    if not existing:
        return build_section(title, body)
    return existing.rstrip() + "\n\n---\n\n" + build_section(title, body)


def update_notion_acceptance(cfg: Config, page_id: str, new_text: str, status: str) -> None:
    url = f"{NOTION_API}/pages/{page_id}"
    payload = {
        "properties": {
            "验收标准/解决方案": {
                "rich_text": [{"text": {"content": new_text}}]
            },
            "状态": {"status": {"name": status}},
        }
    }
    res = requests.patch(url, headers=notion_headers(cfg.notion_token), json=payload, timeout=30)
    res.raise_for_status()


def ensure_mock(task: NotionTask, repo_root: Path) -> Path:
    mock_dir = repo_root / "mocks"
    mock_dir.mkdir(parents=True, exist_ok=True)
    file_path = mock_dir / f"{task.page_id.replace('-', '')}.mock.json"
    if file_path.exists():
        return file_path
    payload = {
        "task_id": task.page_id,
        "title": task.title,
        "description": "mock purpose and scope",
        "inputs": {"params": {}, "body": {}},
        "outputs": {"status": 200, "body": {}},
        "cases": [{"name": "happy-path", "inputs": {}, "expected": {}}],
        "notes": "edge cases / exclusions",
    }
    file_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return file_path

def validate_mock(path: Path) -> None:
    required = {"task_id", "title", "description", "inputs", "outputs", "cases", "notes"}
    data = json.loads(path.read_text(encoding="utf-8"))
    missing = required - set(data.keys())
    if missing:
        raise ValueError(f"mock missing required fields: {', '.join(sorted(missing))}")


def git_branch_name(prefix: str, task: NotionTask) -> str:
    short_id = task.page_id.split("-")[0]
    safe_title = "".join(c for c in task.title.lower() if c.isalnum() or c in "-_ ").strip().replace(" ", "-")
    safe_title = safe_title[:40] if safe_title else "task"
    return f"{prefix}/{short_id}-{safe_title}"


def create_branch_and_commit(repo_root: Path, branch: str, message: str) -> None:
    run(["git", "checkout", "-b", branch], cwd=repo_root)
    run(["git", "add", "mocks"], cwd=repo_root)
    run(["git", "commit", "-m", message], cwd=repo_root)


def gh_create_pr(repo_root: Path, title: str, body: str) -> str:
    output = sh([
        "gh", "pr", "create",
        "--title", title,
        "--body", body,
        "--repo", os.environ.get("GITHUB_REPO", ""),
    ], cwd=repo_root)
    return output.splitlines()[-1].strip()

def gh_wait_for_checks(repo_root: Path, pr_url: str) -> str:
    # Blocks until checks complete and returns the summary text.
    output = sh(["gh", "pr", "checks", pr_url, "--watch"], cwd=repo_root)
    return output


def main() -> int:
    cfg = load_config()
    repo_root = Path(__file__).resolve().parents[1]
    tasks = notion_query_tasks(cfg)
    if not tasks:
        print("No tasks in status=待处理")
        return 0

    for task in tasks:
        spec = build_spec(task)
        acceptance_text = append_section(task.acceptance, "Spec", spec)
        print(f"Updating Notion task: {task.title}")
        update_notion_acceptance(cfg, task.page_id, acceptance_text, status="进行中")

        mock_path = ensure_mock(task, repo_root)
        validate_mock(mock_path)
        print(f"Mock file: {mock_path}")

        if cfg.dry_run:
            print("DRY_RUN=1, skipping git/gh actions")
            continue

        branch = git_branch_name(cfg.branch_prefix, task)
        create_branch_and_commit(repo_root, branch, f"Add mock for {task.title}")
        run(["git", "push", "-u", "origin", branch], cwd=repo_root)

        pr_body = (
            "## 需求摘要\n- 自动生成\n\n"
            "## 变更说明\n- 新增 mock 文件\n\n"
            "## 测试结果\n- Mock：通过\n\n"
            "## 风险/注意事项\n- 待补充\n"
        )
        pr_url = gh_create_pr(repo_root, task.title, pr_body)

        updated_text = append_section(acceptance_text, "PR", pr_url)

        if os.environ.get("WAIT_FOR_CI", "").strip() == "1":
            checks = gh_wait_for_checks(repo_root, pr_url)
            updated_text = append_section(updated_text, "Test Report", checks)
            update_notion_acceptance(cfg, task.page_id, updated_text, status="待测试")
        else:
            update_notion_acceptance(cfg, task.page_id, updated_text, status="待测试")
        print(f"PR created: {pr_url}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
