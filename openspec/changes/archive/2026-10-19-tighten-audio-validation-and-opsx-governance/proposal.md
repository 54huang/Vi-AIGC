# Proposal

## Why

昼白 30 秒内部测试暴露了有旁白项目在整轨制作前缺少试听确认、G2 对混音质量缺少可配置的可复现证据，以及流程验证时产物范围不清的问题；同时测试未使用仓库已有的结构化门禁，不能将“未执行”误判为“未实现”。仓库维护还需把“无论改动大小均走 OPSX”明确为 Agent 的强制规则，避免文档小修或热修绕开方案、验证与归档。

## What Changes

- 在既有 G1 中为有旁白且进入整轨制作的任务设置条件性声音试听/选定记录；无旁白项目按清单规则说明不适用，不新增通用 G1.5 阶段。
- 在 G2 增加按项目启用的音频测量与人工审听记录：明确测量口径、输入/工具/配置版本、实测值和阈值；区分 sample peak、true peak、RMS、LUFS，不把单次测试的数值当成通用标准。
- 增加最小验证、预演、成片的可选择交付范围说明，验证目标与升级条件由任务确认；继续允许部分交付，不把示例清单当作所有任务的硬性上限。
- 为本仓库新增贡献/维护治理规范：任何拟保留的仓库改动，大小不限，均先走 OPSX 提案/更新，实施、验证、适用时同步主规格并归档；在 AGENTS.md 与 README 中明确，检查 HTML 是否需要同步。
- 以报告中的虚构样本做本地回归，另验证无旁白和缺失测量前提的情形；不将测试素材上传、发布或作为商用证据。

## Capabilities

### New Capabilities

- `repository-change-governance`：约束本仓库全部拟保留改动的 OPSX 生命周期和可核验的完成条件。

### Modified Capabilities

- `video-production-pipeline`：补充条件性声音确认、G2 可配置音频质量证据和分级验证交付范围。

## Impact

受影响：`openspec/specs/`、视频生产 Skill 及 references、必要的 `production-data/` 清单/配置/检查器与测试、`AGENTS.md`、`README.md`，并按仓库规则核对 `video-production-pipeline.html`。不改写既有 GateRun/Asset/Manifest 的语义，不把音色偏好或响度数值固化为跨项目事实；既有 Markdown 项目可渐进采用结构化记录。
