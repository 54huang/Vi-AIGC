# 通用视频生产流水线框架

> **把每条视频从“临时灵感”变成可复用、可审查、可迭代的生产流程。**

本仓库维护一套面向 AI 辅助视频制作的**项目无关框架**：从项目背景采集、事实与素材授权核验，到选题、脚本、镜头、声音、参考资产、预演、成片验收和复盘。它帮助创作者稳定地产出可执行的视频方案，并降低反复沟通、返工和素材漂移。

**当前版本：** `v1.1.0`　|　**项目形态：** 文档与 Agent Skill 驱动的工作流框架　|　**主要语言：** 简体中文

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
│   ├── schemas/                     # 七类记录的结构契约
│   ├── examples/                    # 完整正例与故意无效的负例
│   ├── scripts/                     # 本地 YAML/关联校验入口
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
- **仓库维护者 / 贡献者：** 在修改生产框架、工作流或规格时，使用 `.agents/skills/openspec-*/` 管理变更，并维护 `openspec/specs/` 与 `openspec/changes/`。这些 Skills 是仓库维护流程，不是视频生产功能。
- **分发边界：** 若只分发核心 Markdown 制作 Skill，包含 `video-production-pipeline/` 目录即可；若要使用结构化记录校验功能，还需一并分发 `production-data/` 并安装其 Python 依赖。OPSX Skills 和 `openspec/` 属于本仓库的维护体系，不是视频生产运行依赖。

| 路径 | 面向对象 | 用途 |
|---|---|---|
| `.agents/skills/video-production-pipeline/` | 视频制作者 | 视频 Brief、脚本、分镜、生成提示词与质量检查 |
| `production-data/` | 视频制作者（可选） | 项目/Brief/Claim/Asset/Shot/Review/Release 结构化记录、Schema、本地验证器与迁移指南 |
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
| 2026-10-18 | `v1.1.0` | `add-structured-production-validation` | 新增可选结构化生产记录、Schema 与本地关联校验器，明确机器门禁和人工审核边界。 |
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
