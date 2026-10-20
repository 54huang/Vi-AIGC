# 通用视频生产流水线框架

> **把每条视频从“临时灵感”变成可复用、可审查、可迭代的生产流程。**

本仓库维护一套面向 AI 辅助视频制作的**项目无关框架**：从项目背景采集、事实与素材授权核验，到选题、脚本、镜头、声音、参考资产、预演、成片验收和复盘。它帮助创作者稳定地产出可执行的视频方案，并降低反复沟通、返工和素材漂移。

**当前版本：** `v2.0.0`　|　**项目形态：** 文档与 Agent Skill 驱动的工作流框架　|　**主要语言：** 简体中文

## 这是什么 / 不是什么

- 是一套可复用的**生产方法、输入模板、质量门禁和 OPSX 变更归档流程**。
- 不是一个可直接渲染视频的应用；仓库不绑定特定模型、生成平台、剪辑软件或付费服务。
- 不预设某个品牌、产品、受众、平台、视觉风格、音乐或视频时长。上述内容必须来自项目档案或本条任务 Brief。
- 生成模型无法保证跨镜头完全一致；参考素材、连续性账本、预演与人工验收用于降低漂移并尽早发现问题。

## 生产流水线

```text
项目背景与证据
      ↓
单条视频 Brief
      ↓
选题与故事结构 → 旁白/屏幕文字/镜头/声音设计
      ↓
参考资产与连续性账本
      ↓
低成本分镜/animatic → 代表镜头校准
      ↓
生成、剪辑与音画整合
      ↓
事实/授权/可读性/连续性/声音验收
      ↓
发布记录与复盘 → 下一轮可验证改进
```

各项目共用流水线核心，但项目事实与创作设定分开保存。任何未核实的信息都标为待确认，不得为了让脚本完整而编造产品能力、效果、价格、承诺或数据。

## 快速开始

1. 在 Codex 或兼容的 Agent 环境中打开本仓库，并让 Agent 读取 [`video-production-pipeline` Skill](.agents/skills/video-production-pipeline/SKILL.md)。
2. 若是新项目，先按[背景采集流程](.agents/skills/video-production-pipeline/references/background-intake.md)填写[项目背景模板](.agents/skills/video-production-pipeline/references/project-background-template.md)。已有信息可直接整理；缺失事实留作待确认。
3. 提交本条任务需求：目标、目标观众、观众问题、单一核心结论、时长/平台（如已知）、素材/音乐、资源边界及所需交付物。
4. 按[生产工作流与质量门禁](.agents/skills/video-production-pipeline/references/production-workflow.md)逐阶段推进。先确认脚本和低成本预演，再批量生成；按反馈只返修受影响的部分。可选采用结构化记录时，先读 [`production-data/README.md`](production-data/README.md)，并依[迁移指南](production-data/MIGRATION.md)试点。
5. **仅仓库维护者需要：** 修改生产框架或规范时，使用 OPSX Skills 建立变更方案、实施、同步规格并归档；归档后的版本、提交和推送遵循[归档发布规则](.agents/skills/openspec-archive-change/SKILL.md)。普通视频制作不依赖 OPSX。

## 克隆、使用与 DIY / 贡献指南

本仓库既可以直接作为视频生产方法库使用，也可以 fork 后按 OpenSpec 流程修改并维护自己的版本。推荐用 fork + 分支 + Pull Request，避免把个人定制、项目资料或未审查的改动直接推到上游。

### 1. 克隆到本地

只想阅读或使用生产流程时，可直接克隆上游：

```bash
git clone https://github.com/54huang/Vi-AIGC.git
cd Vi-AIGC
```

要长期 DIY 或准备贡献代码，先在 GitHub 上 fork 本仓库，再克隆你自己的 fork：

```bash
git clone https://github.com/<你的 GitHub 用户名>/Vi-AIGC.git
cd Vi-AIGC
git remote add upstream https://github.com/54huang/Vi-AIGC.git
git remote -v
```

确认 `origin` 指向自己的 fork、`upstream` 指向本项目上游；需要更新时先在 GitHub 同步 fork，再拉取已同步的默认分支并从它创建工作分支（以下以 `main` 为例）：

```bash
git switch main
git pull origin main
git switch -c docs/my-change
```

开始前运行 `git status --short --branch`，确认当前分支和工作区，先提交或妥善保留自己的改动，不要用 `reset --hard`、强制覆盖或清理命令处理未知文件。

### 2. 在 Codex 中使用仓库 Skills

用 Codex 打开**仓库根目录**。本仓库已包含视频生产 Skill 和 OpenSpec/OPSX 工作流 Skills，通常无需把它们复制到个人全局目录：

- 做视频 Brief、脚本、分镜或质量检查：调用 `$video-production-pipeline`。
- 讨论问题和选项、不直接实现：调用 `$openspec-explore`。
- 建立有范围、规格和任务清单的变更：调用 `$openspec-propose`。
- 调整已有变更方案：调用 `$openspec-update-change`。
- 按已确认任务实施：调用 `$openspec-apply-change`。
- 将变更规格同步到主规格：调用 `$openspec-sync-specs`。
- 完成检查后归档：调用 `$openspec-archive-change`。

这些是 Codex 对话中的 Skill 调用，不是 PowerShell、Bash 或命令提示符里的终端命令。终端执行的是 `openspec ...` CLI 命令。本仓库提供的是上面列出的细分 Skills；单独的 `$opsx` 路由器不包含在仓库内，除非你的 Agent 环境另行安装了它，否则直接调用对应的 `$openspec-*` Skill。不同 Agent 对仓库级 `.agents/skills/` 的发现和调用方式可能不同；若 Skill 未自动出现，先确认已在仓库根目录打开项目，并按所用工具的官方说明配置/刷新 Skills。不要因为未发现 Skill 就盲目重新初始化或覆盖现有配置。

使用 OpenSpec CLI 前，按[官方安装说明](https://github.com/Fission-AI/OpenSpec/blob/main/docs/installation.md)检查运行环境并安装；例如使用 npm：

```bash
npm install -g @fission-ai/openspec@latest
openspec --version
```

若要运行 `production-data/` 的验证器和测试，另安装项目依赖：`python -m pip install -r production-data/requirements.txt`。

本仓库已经初始化 OpenSpec，并将 `openspec/config.yaml`、`openspec/specs/`、`openspec/changes/` 和工作流 Skills 纳入版本管理。**克隆后通常不需要再次运行 `openspec init`。** 若要为其他 Agent 增加集成，先读官方说明，在干净分支上按对应工具步骤操作；升级 CLI 或刷新 OpenSpec 生成文件前，检查工作区并审阅全部 diff，避免无意改写仓库中已有的配置和工作流。

### 3. 用有边界的流程修改

**本仓库任何拟保留的改动，无论大小或文件类型（包括文档、测试、配置及热修），都必须通过 OPSX 变更。** 只读调查与不拟保留的临时构建产物不算仓库改动；不能借此绕开小修。按以下顺序进行：

1. **先划范围。** 建立自己的分支；说明要解决的问题、涉及使用者、预期行为、明确不改的内容和验收方式。项目自己的品牌事实、提示词或制作资料优先放在项目自己的档案，不要写入通用生产框架。
2. **先探索/提案，不要直接改。** 不确定方案时先用 `$openspec-explore`；确认要做后用 `$openspec-propose <简短变更名>`。检查生成的 `proposal.md`、delta spec、`design.md` 与 `tasks.md`，确认范围、需求和验收条件准确；需要调整就用 `$openspec-update-change`。提案未确认前不要开始实现；propose 只生成方案，必须在后续独立的 apply 请求中实施。
3. **按任务实施。** 用 `$openspec-apply-change` 执行已确认的任务。每项完成后再勾选任务；需求、范围或验收标准变化时先更新方案，不要为了让校验通过而编造资料、放宽门禁或悄悄删掉未完成任务。
4. **验证后再同步/归档。** 运行变更要求的测试和 `openspec validate --all --strict`。若变更含 delta spec，先用 `$openspec-sync-specs` 同步并核对主规格；只有相关任务和验证完成后才用 `$openspec-archive-change`。纯文档等不改变规格级行为的维护变更仍须走 OPSX，但可明确理由并使用合法的无 delta 变更；不要为了归档而制造无关规格。
5. **先确认发布目标，再提交/推送。** 本仓库的归档 Skill 还包含版本提交、annotated tag 和推送规则。归档前确认 `git remote -v` 中的 `origin` 是你有权限的 fork，而不是上游；确认分支、工作区、版本号和标签均无冲突，再审阅归档 Skill 将执行的发布步骤。不要强推、移动已发布标签或提交密钥、客户资料和未经授权的素材。准备贡献上游时，通过 Pull Request 提交，由维护者审查。

常用本地检查（如本次改动适用）：

```bash
openspec status --change <变更名> --json
openspec validate --all --strict
python -m unittest discover -s production-data/tests -v
python production-data/scripts/validate_video_package.py production-data/examples/valid
python production-data/scripts/validate_video_package.py production-data/examples/advanced-valid
```

按改动类型运行适用检查即可；验证器的机器 `PASS` 只代表确定性结构/关联规则通过，不代表内容事实、素材权利、审美或法规审查通过。提交前检查 `git diff --check`、`git status --short --branch` 和完整 diff，只提交本次变更相关文件。

### 4. 同步上游与提交贡献

准备向上游贡献时，确认工作已提交到自己 fork 的主题分支，并在 GitHub 创建 Pull Request；在描述中写明变更背景、范围、验证命令和未解决事项。同步上游前也先保存工作区，再获取并审阅 `upstream` 的更新；不要把自己的未提交改动与上游更新混在一起。完整的 OpenSpec / Codex Skill 用法会随工具版本变化，可查阅 [OpenSpec 官方文档](https://github.com/Fission-AI/OpenSpec/tree/main/docs) 与 [Codex Skills 说明](https://developers.openai.com/codex/skills)。

也可以先查看[项目框架可视化说明](video-production-pipeline.html)。

## 仓库结构

仓库中的 Agent Skills 分为两类：**面向视频制作者的生产能力**与**面向仓库维护者的项目管理工具**。它们是独立的 Skill 包，虽然共用 `.agents/skills/` 发现目录，但职责、依赖和使用对象不同。

```text
.
├── .agents/skills/
│   ├── video-production-pipeline/   # 产品能力：AI 辅助视频生产流程，面向使用者
│   │   ├── SKILL.md                 # 入口与调用规则
│   │   ├── agents/                  # Agent 元数据
│   │   └── references/              # 背景采集、项目档案、生产工作流、治理规则
│   ├── openspec-explore/            # 以下 OPSX Skills 均为维护工具，只面向仓库维护者
│   ├── openspec-propose/            # 提出变更方案
│   ├── openspec-update-change/      # 更新方案
│   ├── openspec-apply-change/       # 实施已批准变更
│   ├── openspec-sync-specs/         # 同步规格
│   └── openspec-archive-change/     # 验证并归档变更
├── production-data/                 # 可选结构化生产记录、Schema 与本地校验器
│   ├── schemas/                     # 基础记录、G0–G4 门禁、生成溯源与媒体配置契约
│   ├── examples/                    # 基础/增强正例与故意无效的负例
│   ├── scripts/                     # 记录校验、门禁汇总与本地媒体测量
│   ├── tests/                       # 自动化验证
│   ├── README.md                    # 结构、命令与自动/人工边界
│   └── MIGRATION.md                 # 并行迁移及回滚说明
├── openspec/
│   ├── specs/                       # 当前生效的框架规格
│   └── changes/                     # 进行中的变更及已归档方案
├── README.md                        # 项目说明、快速开始与维护边界
└── video-production-pipeline.html  # 生产框架的图形化说明
```

### 两类 Skill 的使用边界

- **视频制作者 / 使用者：** 使用 `.agents/skills/video-production-pipeline/`。结构化记录是可选试点，需时使用 `production-data/` 提供的本地验证器；不采用时可继续 Markdown 工作流。正常创作不需要调用 OPSX 或安装 OpenSpec CLI。
- **仓库维护者 / 贡献者：** 在修改本仓库任何拟保留文件时，使用 `.agents/skills/openspec-*/` 管理变更，并维护 `openspec/specs/` 与 `openspec/changes/`。这些 Skills 是仓库维护流程，不是视频生产功能。
- **分发边界：** 若只分发核心 Markdown 制作 Skill，包含 `video-production-pipeline/` 目录即可；若要使用结构化记录校验功能，还需一并分发 `production-data/` 并安装其 Python 依赖。OPSX Skills 和 `openspec/` 属于本仓库的维护体系，不是视频生产运行依赖。

| 路径 | 面向对象 | 用途 |
|---|---|---|
| `.agents/skills/video-production-pipeline/` | 视频制作者 | 视频 Brief、脚本、分镜、生成提示词与质量检查 |
| `production-data/` | 视频制作者（可选） | 项目/Brief/Claim/Asset/Shot/Review/Release、G0–G4 GateChecklist/GateRun、生成 Manifest、Schema、本地媒体检查和迁移指南 |
| `.agents/skills/openspec-*/` | 仓库维护者 | OPSX 探索、提案、更新、实施、规格同步与归档 |
| `openspec/specs/` | 仓库维护者 | 当前生效的框架行为规格 |
| `openspec/changes/` | 仓库维护者 | 进行中的变更；已完成的方案、计划和任务归档于 `openspec/changes/archive/` |
| `video-production-pipeline.html` | 所有读者 | 框架流程的图形化说明 |
| `README.md` | 所有读者 | 项目介绍、快速开始、仓库结构和维护边界 |
| `.gitignore` | 仓库维护者 | 忽略本地凭据、缓存、临时文件和可再生输出；不忽略正式项目资料 |

## 关键生产原则

1. **先读项目档案，再写具体内容。** 没有档案时先采集背景，不把一个项目的品牌事实或风格带入另一个项目。
2. **证据和创意分开。** 可核验主张记录来源、范围、有效期和公开权限；推断、愿景与待确认项显式标注。
3. **音乐分析必须真实。** 有可读取的指定音乐时，先分析基调、能量和节奏段落再编排；没有音频时只给待选方向，不虚构曲名、BPM 或听感。
4. **镜头、文字与声音共同设计。** 时间码内写清画面变化、屏幕信息、旁白、音乐/音效及其衔接，保证口播清晰。
5. **先用低成本方法校准。** 先做分镜或 animatic，再选代表镜头验证人物、产品、场景和风格，之后再扩大制作。
6. **质量门禁不能被渲染完成替代。** 事实、授权、可读性、连续性、声音或规格存在阻断项时，明确返修或待确认，不标记为通过。
7. **复盘只基于可验证数据。** 记录口径和时间范围，区分观察与推断，不把单次表现写成因果或结果保证。

## 版本与变更

本项目使用语义化版本：

- `MAJOR`：对既有流程或规格做不兼容更改。
- `MINOR`：增加向后兼容的生产能力、流程阶段或交付类型。
- `PATCH`：兼容性修正、细化与文档改进。

每次 OPSX 变更按仓库归档 Skill 完成方案/计划、实施与检查、规格同步（适用时）、归档；归档完成后、提交和推送前必须更新本 README，校对项目说明、快速开始、目录、当前版本和归档记录，并检查内部链接。随后评估版本级别、创建提交和标签并推送到远程。不得覆盖已发布标签或强推远程历史。版本号不按提交数量递增。纯文档/维护推送如经用户明确要求保持当前版本，可不打新标签，但不得借此将行为或兼容性变化冒充原版本。

## 最近归档

| 日期 | 版本 | 归档变更 | 摘要 |
|---|---|---|---|
| 2026-10-19 | `v2.0.0` | `tighten-audio-validation-and-opsx-governance` | 将拟保留的仓库改动统一纳入 OPSX；增加 G1 旁白试听/版本确认、G2 音频测量与人工审听分离，以及最小验证交付边界。 |
| 2026-10-19 | `v1.2.0` | `add-auditable-quality-gates-and-provenance` | 新增可审计的 G0–G4 门禁、生成资产来源与权利追溯，以及可复现的本地媒体检查。 |
| 2026-10-18 | `v1.1.0` | `add-structured-production-validation` | 新增可选结构化生产记录、Schema 与本地关联校验器，明确机器门禁和人工审核边界。 |
| 2026-10-18 | —（文档维护，未发布） | add-repository-onboarding-and-html-sync | 补充克隆、Skills、OPSX DIY/贡献指南，并建立生产框架变更时核对/同步 HTML 的 Agent 规则。 |
| 2026-10-18 | `v1.0.0` | `generalize-video-production-pipeline` | 建立项目无关的视频生产框架，补齐背景采集、生产工作流、项目档案治理和质量门禁。 |

每次归档发布前更新此记录；只写简短、可公开的变更摘要，完整方案和任务以 `openspec/changes/archive/` 中的归档为准。

## 素材、隐私与 Git 管理

- 不要提交 API Key、访问令牌、密码、`.env` 本地配置、客户个人信息、未经授权的素材或敏感合同资料。
- 正式的项目背景档案、来源记录、获批参考图及生产文档是项目资产；在确认权限后按项目需要保存，不因文件类型而一概忽略。
- 临时生成内容建议放在 `outputs/generated/`，可再生缓存放在 `outputs/cache/`；这两个目录已列入 `.gitignore`。验收后需长期复用的素材应移入明确的受控目录并记录来源、授权和版本。
- 大体积成片、模型权重和中间渲染文件不适合直接塞进普通 Git 历史。按项目需要使用 Git LFS 或经批准的素材存储，并在仓库保留可追溯的清单和版本信息。

## 帮助与贡献

这是一个持续演进的工作流框架。提出改进时，请说明：所解决的生产问题、适用范围、对现有流程的影响、验收方式，以及是否会改变已批准项目档案。规范级改变先通过 OPSX 方案和任务记录；不要把一次视频的创意临时设定改成跨项目默认值。

---

**维护边界：** 本仓库提供生产流程和治理框架，不构成法律、平台政策、版权或商业收益保证。发布前仍需由项目责任人复核事实、授权和平台要求。
