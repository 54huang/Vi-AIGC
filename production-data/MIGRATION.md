# 渐进迁移指南

## 目标与边界

结构化记录是现有制作资料的可验证补充，不要求把所有叙述性创作说明改成机器字段。可读 Markdown 仍用于背景解释、脚本、创意理由、审查意见和制作协作；YAML 负责稳定 ID、状态、版本、明确范围和实体关联。

## 推荐试点步骤

1. 选择一条新视频或低风险项目，不迁移整个历史仓库。
2. 先照常完成人工背景采集和 Brief；确认责任人、来源和适用范围，不从空字段推断内容。
3. 复制 `examples/valid/`，为 Profile、Brief、Claim、Asset、Shot、Review、Release 分配项目内稳定 ID。记录版本从 `1.0.0` 开始；实质修改时递增版本，并创建绑定新版本的 Review。
4. 初期并行维护 Markdown 与 YAML。Markdown 保留丰富上下文；YAML 不必重复整段脚本，只保留可供校验的事实、引用与门禁数据。
5. 运行本地验证器，先修 ERROR，再由责任人处理 WARN 与内容审查。机器 PASS 不是审批或授权证明。
6. 完成一个生产周期后评估字段负担、失效审批范围和错误提示，再决定是否将验证纳入常规 Brief/Release 门禁。

## 未知、过期和冲突数据

- 未知信息不得猜填；使用明确的待确认状态，并预期出现 WARN 或阻断。
- 过期 Claim、Asset 范围或审批不能因旧 Markdown 中曾写“通过”而自动沿用；核验新版本后创建新版本/Review。
- 来源或项目记录冲突时，保留冲突并交由责任人解决，不通过结构迁移静默选边。
- 未录入权利材料、来源链接不可达或平台规则变化，不等于自动判断为无权/合规；系统只能提示记录缺项或需人工复核。

## 门禁与生成追溯迁移

1. 不要求为历史制作补造不可验证的模型参数或素材权利结论。旧 Asset 继续按既有 schema 记录；新生成/加工任务开始时为每个阶段建立版本化 GateChecklist。
2. 每次执行检查创建独立 GateRun，必须绑定清单、规则、目标 ID+版本、责任人和证据。经清单允许的 N/A 要填写理由及授权人；不要用缺失记录代表 N/A。
3. 新生成/加工输出登记 GenerationManifest，关联输入和输出 Asset、模型及权重许可、工作流/提示词版本或哈希、参数、输出 SHA-256 和受影响审查。输入素材/权利状态逐项核验；未知许可不得转成商业使用许可。
4. 先在小项目试用 `examples/advanced-valid/` 结构，再复制到项目数据包。配置本地媒体检查阈值，并保存工具版本及 JSON 结果作为 GateRun 证据。
5. 原始数据包无新字段时按旧记录继续验证；一旦声明使用新门禁或生成追溯记录，该记录必须符合新 Schema，缺项显示为 ERROR/BLOCKED，不会自动补成 PASS。

## 回滚

若试点负担过高，可停止调用验证器并继续原有 Markdown 工作流。不要删除既有结构化记录或改写历史 ID；它们可作为审计材料保留。之后恢复验证时，按记录声明的 schema 版本选择对应 schema/迁移程序。不要把 WARN/ERROR 强行改写成 PASS 来绕过门禁。

## 参考实现命令

```powershell
python -m pip install -r production-data/requirements.txt
python production-data/scripts/validate_video_package.py production-data/examples/valid
python production-data/scripts/validate_video_package.py production-data/examples/advanced-valid
python -m unittest discover -s production-data/tests -v
```
