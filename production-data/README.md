# 结构化生产记录：字段契约、质量门禁与追溯

本目录提供可选、离线优先的 YAML + JSON Schema 验证工具。Markdown 仍承载叙述性 Brief、脚本、创意依据和审查意见；结构化记录管理稳定 ID、版本、状态、证据和对象关系。机器检查不证明事实真实、授权充分、内容适当、审美合格或法律/平台合规。未采用该试点的项目可继续原 Markdown 流程。

## 快速开始

```powershell
python -m pip install -r production-data/requirements.txt
python production-data/scripts/validate_video_package.py production-data/examples/valid
python production-data/scripts/validate_video_package.py production-data/examples/advanced-valid
python -m unittest discover -s production-data/tests -v
```

退出码：`0` = 没有错误/警告的确定性 PASS；`1` = ERROR，阻断；`2` = 有需人工复核的 WARN。默认包路径是 `examples/valid`。增强样例 `examples/advanced-valid` 演示 G0 清单/执行和完整生成 manifest/权利分栏/哈希。

## 记录模型

基础记录包含 `ProjectProfile`、`VideoBrief`、`Claim`、`Asset`、`Shot`、`Review` 和 `Release`。引用使用稳定 ID + 精确 SemVer；Release 的资产引用必须与所选 Shot 版本的素材闭包一致，必需审查由 Profile 规则决定。

新增追溯记录：

- `GateChecklist`：G0–G4 某阶段的版本化检查项、规则版本、自动/人工类型、必需/阻断/允许 N/A 配置。
- `GateRun`：一次检查结论，状态仅可为 `pass`、`fail`、`blocked`、`not-applicable`；包含精确目标版本、证据、责任人、时间和清单/规则/工具/配置版本。PASS 必须有证据；N/A 必须有理由和授权人，且清单明确允许。
- `GenerationManifest`：一次生成/加工执行，关联精确输入/输出 Asset、模型及权重许可、模型卡引用、工作流/提示词版本或哈希、参数、QA/Review、GateRun 与下游 Shot/Release 关系。

Asset 可分别记录 `rights.code`、`rights.model_weights`、`rights.input_media`、`rights.output_use`；Manifest 记录 `model.weights_rights` 和工作流 `code_license`。这些许可维度不能互相推导。Model Card 可提供模型元数据，但不能替代具体素材来源/权利核验。字段完整/期限未到是机器可查的事实；授权范围是否充分及能否商用仍由责任人审查。提示词可只存受控引用或哈希，勿写入凭据或不宜共享的明文。

已有普通素材无需伪造生成历史。采用新追溯能力时，生成/加工输出必须登记 Manifest、输入/输出 Asset 和文件 SHA-256；本地文件哈希会自动复核，远程对象记录哈希而不由离线验证器下载。资产修订应创建新版本并保留 `change_history`，不得覆盖历史。

## G0–G4 门禁

每个项目配置版本化 `GateChecklist`，明确该阶段检查项、负责人类型、阻断等级和允许豁免范围。每次检查写独立 `GateRun`；不要覆盖旧结果。改变目标对象、输入依赖、规则或关键配置后，旧执行记录仍可审计，但不能作为新版本通过证据。

清单汇总命令示例：

```powershell
python production-data/scripts/evaluate_gate.py path/to/package --checklist-id gate_g0-demo --checklist-version 1.0.0 --target-id profile_demo --target-version 1.0.0
```

必需检查缺记录、失败、被阻断或不允许/未授权的 N/A 时，阶段不能 PASS。人工检查结果由对应 Review/责任人完成；自动检查与人工结论分别保留。

## 本地媒体检查

`schemas/media-check-config.schema.json` 描述本地配置。使用示例：

```powershell
python production-data/scripts/check_media.py final.mp4 --config media-check-config.json --subtitles final.srt
```

需本机提供 `ffprobe` 和 `ffmpeg`，且配置中记录版本字符串、目标宽高/帧率、预期时长及容差、字幕覆盖率阈值、音频峰值上限、是否必需字幕/音频。配置缺项、工具版本不匹配、媒体/字幕不可读时返回 `blocked`，不会误报 PASS。字幕覆盖率按 cue 时间区间并集/媒体时长计算；峰值使用 `ffmpeg volumedetect` 的 sample peak 口径。结果 JSON 可作为 GateRun 证据附件。机器只量化规格/时间/峰值，不判断字幕可读性、音画观感或许可充分性。

## 机器/人工边界

- 机器：Schema 必填与枚举、唯一 ID/版本、引用存在、目标版本、闭包、哈希格式/本地匹配、声明日期，以及明确配置的媒体规格/时长/字幕区间/音频峰值。
- 人工：事实真实性、来源可靠性、权利范围解释及充分性、品牌适配、表达与字幕可读性、连续性/审美、法规/平台合规。
- 权利字段缺失/未知或适用期限已过时，新 Manifest 的发布就绪检查阻断；`verified` 是责任人声明，不是机器推断。

## 文件清单

- `schemas/`：基础记录、GateChecklist/GateRun、GenerationManifest 和媒体配置 Schema。
- `examples/valid/`：基础结构示例；`examples/advanced-valid/`：门禁与生成追溯综合示例；`examples/invalid/`：负例。
- `scripts/validate_video_package.py`：记录包结构/引用/权利/哈希验证。
- `scripts/evaluate_gate.py`：按清单、目标精确版本汇总门禁结果。
- `scripts/check_media.py`：本地可复现媒体测量适配器。
- `tests/`：Schema、引用、门禁、追溯和媒体边界测试。
- `MIGRATION.md`：渐进迁移/回滚步骤。
