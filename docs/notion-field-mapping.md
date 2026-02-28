# Notion Field Mapping (MVP)

Target database: 🧩 产品需求与问题管理

## Fields used
- 标题 (title): Task title
- 状态 (status): workflow state
- 描述/复现步骤 (text): original context
- 验收标准/解决方案 (text): spec + test report + user doc + PR link
- 模块/范围 (text): optional
- 类型 (select): optional
- 优先级 (select): optional

## Status mapping
- 待处理 -> agent picks up
- 进行中 -> agent working
- 已完成 -> after human merge + doc writeback

## Writeback strategy (MVP)
- Spec is written into `验收标准/解决方案`
- Test report, PR link, and user doc are appended to `验收标准/解决方案`
- Original `描述/复现步骤` is preserved
