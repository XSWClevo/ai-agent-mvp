# Agent Interfaces (MVP)

## Notion
- List tasks (Status = 待处理)
- Read task fields
- Write back: Spec, Risks, Test Report, User Doc, PR Link, Status

## GitHub
- Create branch
- Commit changes
- Create PR
- Read CI status
- Add labels (needs-fix)

## Local/CI
- Generate mock file: mocks/<task-id>.mock.json
- Run tests

## Guards
- Mock file must exist and be valid JSON
- Self-review must pass
- CI must pass before moving to 待测试
