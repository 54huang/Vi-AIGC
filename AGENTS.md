# Repository Agent Instructions

## Keep the HTML overview in sync

When a change affects the video-production framework—its governing OpenSpec specification, production Skill or references, templates, quality gates, structured-record schemas/validation rules, or repository workflow—inspect `video-production-pipeline.html` against the changed source documents. If the HTML description is stale, update it in the same change; do not change only its update date. Keep terminology, process stages, machine-checkable rules, and human-review boundaries consistent with the source of truth. Purely administrative/documentation changes that do not affect the framework (for example, clone instructions) do not require HTML edits, but still assess whether the page is affected.

After editing the HTML, update its displayed update date and verify the page has no broken internal anchors, malformed markup, or stale descriptions. Keep the page self-contained and preserve its responsive visual design.

## All persistent repository changes use OPSX

Before adding, editing, or deleting **any file intended to be retained in this repository**, regardless of size or type (including docs, tests, configuration, Skill files, and urgent fixes), associate the work with an OpenSpec/OPSX change. Read-only investigation and disposable local build output are not persistent changes; do not use that distinction to bypass this rule.

Use the OPSX lifecycle: explore if uncertain; propose and review artifacts before implementation; start apply in a separate user request/turn; update the change first if scope or acceptance criteria shift; implement and mark verified tasks; run applicable tests and strict validation; sync delta specs into main specs when present; then archive. Documentation-only changes without behavioral impact may use a legitimate no-delta change instead of inventing a requirement. Do not claim completion if tests, tasks, required spec sync, or HTML consistency remain unresolved. Follow the archive workflow for any release/push.
