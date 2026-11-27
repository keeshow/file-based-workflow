# 基于文件驱动的 Agent 开发工作流

通过 `AGENTS.md` 约定协作规则，Task 管理当前任务和验收，Handoff 交接项目状态，Debug 保存关键排查过程，Note 经用户明确授权整理专题知识。

本项目是一套供 Agent 遵循的文件约定和协作规范，不是任务编排引擎，不需要安装或运行服务。

当前版本：26.1127.7

## 1.快速开始

### 方式一：安装 Skill（推荐）

Skill 只需在每台电脑上安装一次，之后在任意项目中都可以使用。Skill 压缩包随每个版本自动发布：[下载 file-based-workflow-skill.zip](https://github.com/keeshow/file-based-workflow/releases/latest/download/file-based-workflow-skill.zip)。

| 所用工具 | 安装方法 |
| --- | --- |
| Claude 网页版、桌面版的聊天界面 | 下载压缩包，在设置的 Skills 管理处上传 |
| Claude Code、Codex、WorkBuddy 等 Agent 工具 | 将下面这段话发给 AI，由 AI 自行安装 |
| 手动安装 | 解压后将 `file-based-workflow` 文件夹放入所用工具的 Skill 目录，如 Claude Code 为 `~/.claude/skills/` |

```text
从 https://github.com/keeshow/file-based-workflow/releases/latest/download/file-based-workflow-skill.zip 下载 Skill 压缩包，
解压后将其中的 file-based-workflow 文件夹安装为你的用户级 Skill，安装位置按你所用工具的约定。完成后告诉我安装路径。
```

安装后，在项目中对 AI 说：

- “引入文件工作流”：把工作流复制到当前项目。
- “升级文件工作流”：升级到最新版本，保留项目自己的文档和修改。
- “检查文件工作流”：运行文档校验并报告结果。

说全称“文件驱动工作流”也可以；只说“工作流”等泛称时不会触发，以免与项目中的其他流程混淆。

### 方式二：不安装 Skill

将下面这句话发给 AI，AI 会按 Skill 中的步骤执行：

```text
阅读 https://raw.githubusercontent.com/keeshow/file-based-workflow/main/skills/file-based-workflow/SKILL.md，按其中的“引入”步骤，把文件工作流引入当前项目。
```

### 方式三：人工复制

将 [workflow/](workflow/) 内的全部内容复制到项目根目录，复制后 `AGENTS.md` 和 `docs/` 均位于项目根目录下。所用 Agent 工具不自动读取 `AGENTS.md` 时，在该工具约定的入口文件中引用它。遇到已有同名文件时，先比较、合并，保留项目原有的规则、文档和状态，不直接覆盖。

## 2.工作流简介

```text
workflow/                         # 当前版本的完整工作流，引入时复制到项目根目录
├── AGENTS.md                     # 通用协作、任务管理、验证与文档维护规范
└── docs/                         # 项目文档目录
    ├── README.md                 # 重要文档导航索引，预置通用目录入口
    ├── handoff.md                # 项目状态与交接快照，初始为空
    ├── project-rules.md          # 项目专属约束，初始为空，由用户确定内容
    ├── tasks/                    # 独立任务的目标、实施进度、验收结果与遗留问题；预置任务总览
    ├── notes/                    # 排查记录与专题笔记，专题笔记须用户明确授权；预置索引
    ├── guides/                   # 各类文档的具体写法，Agent 在对应时机按需阅读
    ├── examples/                 # Task、Handoff、Debug、Note 及项目规则的写法示例
    ├── scripts/                  # 文档一致性校验脚本，需要 Python 3.7 及以上
    └── references/               # 原始参考资料及其来源、版本信息
```

`docs/README.md` 按主题或文档类型组织重要文档，每项包含相对链接和一句用途说明，不写状态或进展。全部 Task 列在 `docs/tasks/README.md`，全部 Debug 与 Note 列在 `docs/notes/README.md`，每项一行，状态只在这两份索引和各文档中维护。维护要求见 [AGENTS.md](workflow/AGENTS.md) 第 2、6 节。

各类文档分工明确：Handoff 只反映当前状态，Task 只记目标、步骤和验收结论，排查过程按问题分别记在 Debug 中，问题解决后结项；其他文档只放链接，避免同一内容多处维护、单个文档无限增长。

`AGENTS.md` 只保留每次会话都需要的核心规则，各类文档的具体写法放在 `docs/guides/`，由 Agent 在创建或更新对应文档前阅读，以减少每次会话加载的内容。写法示例集中在 `docs/examples/`，Agent 首次创建或整理对应文档时参考其结构和写法；示例中的项目、路径和结果均为虚构，不作为实际状态或验收证据。

Agent 更新文档后，在任务结束前运行 `docs/scripts/check-docs.py`，检查文档命名、编号、状态、索引和链接是否一致。脚本只读，只使用 Python 标准库；未安装 Python 时其余流程照常使用，Agent 会提示缺少的环境，经你同意后才安装。不需要校验时，在 `docs/project-rules.md` 中关闭，写法见 `docs/guides/check.md`。

Agent 在开发和验证中产生的截图、临时脚本、测试输出等本机产物，统一放在项目根目录的 `.agent-local/`，通过 `.git/info/exclude` 在本机忽略，不进入版本库，也不放入 `.git/` 目录；是否清理由用户决定。

`skills/file-based-workflow/` 是用于引入、升级和检查的 Skill，不复制到项目中；引入和升级的具体步骤只在其 `SKILL.md` 中维护。

版本变更见 [CHANGELOG.md](CHANGELOG.md)。

## 3.多对话使用建议

本工作流针对跨对话、跨 Agent 工具接续工作而设计，减少对聊天历史的依赖。独立 Task 建议开启新对话，同一 Task 也可跨多个对话完成。

建议在约 2～3 次上下文压缩后，选择阶段完成或其他安全交接点开启新对话。次数仅供参考，应根据任务和实际表现调整。

切换前通知 Agent 检查进度并更新 Task、相关 Debug 及必要的 `docs/handoff.md`，保存关键证据，记录未提交修改及下一步。

开启新对话后，Agent 会通过 `AGENTS.md` 或其入口文件加载规则；未自动加载时，提醒 Agent 先阅读 `AGENTS.md`。接续已有任务时，可明确对应 Task，核对实际状态后继续。

## 4.工作流升级

实际项目所用的工作流版本记录在其 `AGENTS.md` 开头的“工作流版本”中，各版本的变更见 [CHANGELOG.md](CHANGELOG.md)。

- **已安装 Skill**：对 AI 说“升级文件工作流”。
- **未安装 Skill**：将下面这句话发给 AI。

```text
阅读 https://raw.githubusercontent.com/keeshow/file-based-workflow/main/skills/file-based-workflow/SKILL.md，按其中的“升级”步骤，升级当前项目的文件工作流。
```

- **人工升级**：按 CHANGELOG 中的变更说明，用新版 [workflow/](workflow/) 中的 `AGENTS.md`、`docs/guides/`、`docs/examples/` 和 `docs/scripts/` 替换项目中的对应文件，并合并项目自行修改过的规则；变更说明涉及文件移动或删除时一并处理。项目自有的状态、任务和规则文档不随升级替换。

升级只更新来自工作流的通用文件。涉及文件移动、删除、新增预置文件或与项目修改冲突时，AI 会先列出处理方案，等待你的决定。

## 5.许可证

本项目以 [MIT 许可证](LICENSE)发布。
