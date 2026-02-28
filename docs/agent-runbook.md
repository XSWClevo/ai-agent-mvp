# Agent Runbook (MVP)

## Inputs
- Notion task (Status=待处理)

## Outputs
- Spec
- Mock file
- PR link
- Test report
- User doc

## Steps
1. Fetch Notion task
2. Draft spec + risks, write back
3. Generate mock file
4. Implement code + commit
5. Self-review and fix issues
6. Run tests/CI
7. Create PR and write back link + test report
8. Move task to 待测试
9. After human merge, write back user doc and mark 已完成
