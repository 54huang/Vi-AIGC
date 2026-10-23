---
name: video-production-pipeline
description: Build repeatable, tool-agnostic video production briefs, scripts, shot lists, generation prompts, and quality checks across brands and products. Use when creating or iterating videos; first load the current project's approved background rather than assuming one.
---

# Video Production Pipeline

Use this project skill as the reusable production core. It defines the method, not a specific brand, product, platform, genre, visual style, music choice, or video length.

## Every video task

1. Read `references/background-intake.md` and `references/project-background-template.md`; locate the active project's completed background profile. If none exists, run the intake flow before making product claims; unknown fields stay `unknown / needs confirmation`.
2. Apply `references/project-profile-governance.md` when creating, updating, or relying on project-specific claims or assets.
3. Read `references/production-workflow.md` for the current brief, production order, output contract, continuity ledger, quality gates, and revision rules.
4. Use `references/upstream-principles.md` when a workflow/tool question or external creative reference is relevant; do not treat a third-party repository's popularity as proof or its assets as licensed for reuse.
5. Separate three layers in every task: **reusable pipeline core**, **project profile** (approved, project-specific facts and settings), and **single-video brief** (this video's changeable choices). Never carry facts or style settings from one project into another.
6. Match the scope requested. A prompt-only request can receive a ready-to-use prompt; a full production plan follows the complete output contract. Do not expand into tool setup, paid services, publishing, or external mutations unless requested.

## Structured records (optional local validation)

When a project uses this repository's `production-data/` package, read `production-data/README.md` and `production-data/MIGRATION.md`, then validate the YAML package before a configured Release gate. For project-configured optional G2/G3 visual evidence, use `production-data/scripts/check_visual.py` with a pinned video hash, explicit scene ranges, analysis profile and metric definitions; its metrics and sample-frame indices are diagnostic only. Do not infer creative/readability/rights/release PASS from motion, luma or brand-color area; only configured objective limits may create a machine GateRun, and human review remains separate. Use `references/motion-handoff.md` for reusable MotionRecipe and multi-tool/version handoff; external gate names or statuses never imply this repository gate PASS. Keep descriptive briefs/scripts in Markdown; use YAML for stable IDs, versions, explicit scopes, references, and review status. For adopted structured gates, record each G0–G4 check as a versioned `GateRun` with `pass / fail / blocked / not-applicable`, exact target version, evidence, owner, timestamp, and rule/tool/config versions. `PASS` requires evidence; N/A requires checklist permission, rationale, and authorizer. Missing prerequisites are `blocked`, never silently skipped. Use `evaluate_gate.py` to summarize; changes to a target, dependency, rule, or key config invalidate affected prior evidence. Register generated/processed outputs with a `GenerationManifest` linking input rights, model/revision and weights license, workflow/prompt version or hash, parameters, output SHA-256, reviews, and downstream shots/releases. Keep code, model-weight, input-media, and output-use rights separate. A machine `PASS` confirms only deterministic record/media checks and never approves claims, rights sufficiency, creative quality, compliance, or publication. Do not invent missing values to make validation pass; unknown or expired data stays pending and is escalated to its owner. Projects that have not adopted structured records continue the existing Markdown workflow.

## Core rules

- Establish the audience, viewer problem, single takeaway, evidence, platform/format, resources, and requested deliverable before selecting production tools.
- Distinguish verified facts, attributed claims, opinions, assumptions, and creative fiction. Cite or record sources for claims that need evidence; do not invent product capabilities, results, performance, terms, endorsements, or data.
- Treat project-specific visual style and voice as configurable settings. If absent, ask or propose options; never turn a previous project's style into a universal default.
- For supplied, accessible music, analyze audible mood, energy, sections, and usable beats before fitting narration and visual actions. Without a provided track, label music suggestions as options; do not pretend to have heard a track or know its rights, BPM, or exact properties.
- At G1, if the task includes narration and will proceed to full-track production, require a representative listenable voice sample and a human-selected, versioned voice plan tied to script version, relevant voice settings, approver and time before scaling. Changes to script/voice/settings require renewed listening approval. A script-only task does not need produced audio; a no-narration task may record an authorized, reasoned N/A. Do not impose a universal sample length or candidate count.
- Make each time-coded segment actionable across picture, on-screen text, and sound. Sync meaningful actions/transitions with sound cues or intentional silence; keep speech intelligible.
- When visual continuity matters, establish approved reference assets and an asset/version ledger. Generate a low-cost storyboard/animatic and calibrate a representative shot before scaling. State that these methods reduce drift but cannot guarantee identical outputs from generative models.
- Scope the delivery as minimal validation, preview, or final production in the Brief: record objective, required artifacts, stop/upgrade conditions and uncompleted formal gates. A voice/process-only validation does not need a cover or full visuals and cannot authorize a G3 Release. For G2 with audio, separate configured measurements from human listening; missing required tracks, interval, tool or threshold is blocked, not passed.
- Block final approval for unresolved factual, rights, readability, continuity, or audio issues. Iterate only on requested changes and check their downstream effects.
- After release, use only supplied or verifiable performance data; record time window and definition, separate observation from inference, and avoid promises of reach or results.

See `references/production-workflow.md` for reusable templates and acceptance criteria.
