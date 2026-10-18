# 结构化生产记录：字段契约与验证

本目录为可选的、离线优先的结构化生产数据试点。既有 Markdown Brief、项目档案和制作习惯继续有效；自动验证只检查记录与显式规则，不判断内容真假、授权是否充分、审美质量或法律/平台合规。

## 快速开始

1. 安装 Python 3.10+，并在当前环境安装 `production-data/requirements.txt`。
2. 复制 `production-data/examples/valid/` 为一个项目数据包，按项目替换样例值并保留稳定 ID。
3. 执行：

   ```powershell
   python production-data/scripts/validate_video_package.py path/to/package
   python -m unittest discover -s production-data/tests -v
   ```

默认路径是完整正向样例包。退出码：`0` = 无错误/警告的机器 PASS；`1` = 存在 ERROR（阻断）；`2` = 无 ERROR 但存在 WARN（必须人工复核）。

## 记录与关联

每个 YAML 文件保存一条记录。所有记录包含 `record_type`、带类型前缀的稳定 `id`、SemVer 形式的 `version` 和 `schema_version`。JSON Schema 位于 `schemas/`，当前 schema 版本为 `1.0.0`。

- `ProjectProfile`：项目状态、Claim/Asset ID 索引、必需审查类型规则。
- `VideoBrief`：精确档案 ID/版本、渠道、计划发布日期、Claim IDs 与 Shot IDs。
- `Claim`：确认状态、来源定位、项目/渠道/日期范围。存在来源字段不等于主张已被证实。
- `Asset`：状态、素材位置和声明的项目/渠道/日期适用范围；权利充分性始终人工判断。
- `Shot`：精确 Brief 版本、Claim IDs、版本化 Asset 引用和 Review ID。
- `Review`：人工审查人、结论、审查类型与被审对象的精确 ID/版本。
- `Release`：精确 Brief、Shot 版本、资产引用闭包和必需 Review IDs。所需审查由 Profile 规则决定，Release 无权删减。

ID 仅包含小写字母、数字和连字符，并使用 `profile_`、`brief_`、`claim_`、`asset_`、`shot_`、`review_`、`release_` 前缀。一个实体可保留多个版本，但同一个 ID+版本在一个数据包中必须唯一。由于首版 Review 引用采用 ID 列表，Review ID 不得有多个版本造成歧义。

## 校验边界

- `ERROR`：结构无效、断链、版本不存在、适用范围/有效期冲突、Release 素材闭包不一致或必需人工审查缺失/未通过；阻断当前校验。
- `WARN`：Claim 未确认、Asset 权限未核验或授权表述含糊等需责任人判断的情况；不自动批准。
- `PASS`：仅表示已实现的确定性记录规则通过。PASS 不改变 Review 状态，不会把 Release 改成 `approved`/`published`。

若授权语义不清、来源可靠性需要判断、文案表达/合规/审美需评估，保持人工复核状态。机器不得将未知解释为通过。

## 文件清单

- `schemas/`：七种记录类型 JSON Schema。
- `examples/valid/`：完整关联的可验证 YAML 样例，内容为虚构占位示例。
- `examples/invalid/`：故意无效的负例，仅供测试。
- `scripts/validate_video_package.py`：本地单入口验证器。
- `tests/`：schema、错误定位、引用、版本、范围、审批及退出码测试。
- `MIGRATION.md`：渐进迁移和回滚说明。
