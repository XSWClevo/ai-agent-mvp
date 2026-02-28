# ai-agent-mvp

MVP scaffold for an AI agent that drives a Notion → GitHub workflow.

## Folders
- docs/: local notes and artifacts
- scripts/: automation entrypoints
- mocks/: per-task mock files

## Mock spec
See docs/mock-spec.md for the expected mock file structure.

## Quick start
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Set env vars:
```bash
export NOTION_TOKEN="<token>"
export NOTION_DATABASE_ID="74de144c5e284b79a450f4526a65d91a"
export GITHUB_REPO="XSWClevo/ai-agent-mvp"
```

Dry run:
```bash
DRY_RUN=1 ./scripts/agent_pipeline.py
```

Live run:
```bash
./scripts/agent_pipeline.py
```
