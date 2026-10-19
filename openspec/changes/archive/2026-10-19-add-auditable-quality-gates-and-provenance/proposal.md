# Proposal

## Why

G0–G4 目前有门禁原则，却缺少版本化清单、统一结论/证据记录和可重复验收，因此“通过”难以复核、跨项目难以比较。生产记录虽能追溯业务对象 ID/版本，但尚未把输入素材权利、模型/工作流执行、生成输出哈希、QA 证据和最终剪辑引用串成完整链路，无法稳定复现或定位风险。

## What Changes

- 为 G0–G4 定义版本化门禁清单与结果契约：每项记录 `pass`、`fail`、`blocked` 或 `not-applicable`，精确绑定受检对象版本，保存证据、检查人/责任人、配置和工具版本；规定门禁汇总及阻断规则。
- 将确定性、低风险检查优先纳入本地可复现验证器，包括媒体/导出规格、必需文件与引用、时长、字幕时间边界及配置化覆盖检查、配置化音频峰值、授权记录存在性和有效期；缺少检查前提时不得误报通过。
- 保留事实真实性、授权是否充分、品牌适配、表达与字幕可读性、音画质量、审美及法律/平台合规等人工判断；机器校验不自动批准。
- 建立轻量 Asset Registry 与生成/制作 manifest，关联输入 Asset、来源和权利记录、模型服务/模型权重及版本、模型卡快照/链接、工作流与提示词版本、参数、输出哈希、QA 结果、历史版本及最终 Shot/Release 引用。
- 分别记录开源代码许可、模型权重许可、输入素材权利和输出使用条件；任何一种许可不得推导另一种商业使用权限。未知或缺失权利记录不得自动放行。
- 为新增契约提供 Schema、正反例、回归测试和渐进迁移；旧 Markdown 工作流和未采用新门禁/manifest 的数据包有明确兼容策略。

## Capabilities

### New Capabilities

无；这些要求扩展现有视频生产与结构化追溯能力。

### Modified Capabilities

- `video-production-pipeline`：增强质量门禁证据契约、确定性自动检查和生成资产端到端溯源要求。

## Impact

影响 `openspec/specs/video-production-pipeline/spec.md`、`.agents/skills/video-production-pipeline/`、`production-data/` 中的 Schema/样例/验证器/测试/迁移说明、README 及 `video-production-pipeline.html`。优先使用现有 Python + JSON Schema/YAML 离线验证架构，不引入数据库、云服务或指定媒体供应商。Hugging Face Model Cards 文档列出用途/局限、训练与实验信息、数据集和评测等模型说明内容；本方案仅将这些作为模型元数据来源之一，不把 Model Card 或其中的许可证视为具体输入素材/输出权利审查的替代品。

参考：[Hugging Face Hub — Model Cards](https://huggingface.co/docs/hub/main/model-cards)
