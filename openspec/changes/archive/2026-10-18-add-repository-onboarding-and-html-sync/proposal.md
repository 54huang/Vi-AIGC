# Proposal

## Why

仓库已包含生产框架和可选结构化记录，但新使用者缺少从克隆、发现 Skills 到按 OPSX 安全 DIY 的完整入口；同时，生产框架更新后图形化 HTML 说明可能落后于 Skill、参考流程或主规格。需要把可复用的维护规则和用户指引纳入仓库，降低贡献门槛并避免文档漂移。

## What Changes

- 在 README 增加克隆/fork、Codex Skills、OpenSpec CLI、受约束变更、验证、归档及贡献的操作指南。
- 建立仓库级 Agent 指令：影响生产框架的变更必须核对 HTML；若页面落后，同一变更同步更新并验证。
- 将当前结构化生产记录及机器校验/人工审查边界补充到 HTML 概览。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

无。此变更仅更新维护/入门文档，不改变视频生产行为契约；按项目要求设置 `skip_specs: true`。

## Impact

影响 `README.md`、`AGENTS.md`、`video-production-pipeline.html` 与本 OpenSpec 变更记录；无代码、API、依赖或生产数据格式变更。
