# Design

## Context

仓库已有 `video-production-pipeline.html`、生产 Skill、OpenSpec 工作流 Skills、结构化记录试点和主规格。README 操作指南与 HTML 同步规则属于仓库维护层面的文档治理，不需要扩展视频生产主规格；现有生产流程、Schema 与校验器行为均保持不变。

## Goals / Non-Goals

**Goals:**
- 让首次使用者可从 README 按顺序完成克隆、使用 Skill、提出和实施 OPSX 变更、验证、归档及贡献。
- 让 Agent 在相关生产框架更新时比对 HTML，并在页面落后时同一变更修复。
- 让 HTML 正确概述结构化记录是可选方式，以及确定性机器校验和人工内容审核的分工。

**Non-Goals:**
- 不新增生产能力、Schema、验证器行为或主规格要求。
- 不自动生成 HTML，也不引入文档构建、链接检查或 CI 依赖。
- 不要求与生产框架无关的维护变更修改 HTML。

## Decisions

- 使用根目录 `AGENTS.md` 表达仓库级约束，确保 Agent 处理仓库任务时可发现，而不是将规则放入只对 `.agents/` 子目录生效的位置。
- README 用可复制的 Git/CLI 示例解释上游与 fork 的关系，并明确 Skills 调用与终端命令不同。
- HTML 继续保持自包含；更新只覆盖与主规格/生产资料相关的概览，不复制整份字段规范。
- 机器 PASS 仅代表已实现的结构和关联规则通过，不作为事实、权利、审美、合规或发布批准。
- 此次没有生产行为要求变化，因此不创建 delta spec，使用 `skip_specs: true`，避免为满足工具形式而制造无关要求。

## Risks / Trade-offs

- Agent 可能未加载仓库级指令；README 和 HTML 仍提供人工可读的维护提示，检查规则也明确要求在相关变更中执行。
- HTML 手工同步仍可能被遗漏；按更新任务执行的对照和验证降低风险，但不提供 CI 强制保证。
- Git 默认分支名称因 fork 状态而异；指南标明示例假设 `main`，使用者应确认自己的默认分支。
