# 文件驱动的 Agent 开发工作流

通过 `AGENTS.md` 约定协作规则，Task 管理当前任务和验收，Handoff 交接项目状态，Debug 保存关键排查过程，Note 经用户明确授权整理专题知识。

当前版本：26.1125.5

## 1.工作流引入

**AI 引入**：将下面这段话直接发给实际项目中的AI。

```text
仅执行开发工作流引入，不进行代码审查、全仓库扫描、构建或测试。
将 https://github.com/keeshow/file-based-workflow 仓库中 workflow/ 目录下的内容复制到当前项目根目录，
不要在当前项目中创建 workflow/ 目录。引入后，AGENTS.md、handoff.md 和 docs/ 必须直接位于当前项目根目录。
如果发现同名文件，立即停止并列出冲突文件，等待我的决定。
没有冲突时直接复制。如果你不会在新会话中自动读取 AGENTS.md，在你所用的入口文件中引用它，不复制其内容；
入口文件已存在时追加引用，不覆盖原有内容。完成后只报告新增或修改的文件。
```

**人工引入**：将 [workflow/](workflow/) 内的全部内容复制到实际项目根目录即可使用，复制后 `AGENTS.md`、`handoff.md` 和 `docs/` 均位于项目根目录下。所用 Agent 工具不自动读取 `AGENTS.md` 时，在该工具约定的入口文件中引用它。

两种引入方式遇到已有同名文件时，先比较、合并，保留项目原有规则、文档和状态，勿直接用工作流文件覆盖已有内容。

## 2.工作流简介

```text
workflow/                         # 当前版本的完整工作流
├── AGENTS.md                     # 通用协作、任务管理、验证与文档维护规范
├── handoff.md                    # 项目状态与交接快照，初始为空
└── docs/                         # 项目文档目录
    ├── README.md                 # 重要文档导航索引，预置通用目录入口
    ├── project-rules.md          # 项目专属约束，初始为空，由用户确定内容
    ├── tasks/                    # 独立任务的目标、实施进度、验收结果与遗留问题
    ├── notes/                    # 排查记录与专题笔记，专题笔记须用户明确授权
    ├── guides/                   # 各类文档的具体写法，Agent 在对应时机按需阅读
    ├── examples/                 # Task、Handoff、Debug、Note 及项目规则的写法示例
    └── references/               # 原始参考资料及其来源、版本信息
```

`docs/README.md` 按主题或文档类型组织重要文档，每项包含相对链接和一句用途说明；文档新增、移动或删除时维护入口，不重复记录任务进度或验收结果。维护要求见 [AGENTS.md](workflow/AGENTS.md) 第 2、6 节。

`AGENTS.md` 只保留每次会话都需要的核心规则，各类文档的具体写法放在 `docs/guides/`，由 Agent 在创建或更新对应文档前阅读，以减少每次会话加载的内容。写法示例集中在 `docs/examples/`，Agent 首次创建或整理对应文档时参考其结构和写法；示例中的项目、路径和结果均为虚构，不作为实际状态或验收证据。

版本变更见 [CHANGELOG.md](CHANGELOG.md)。

## 3.多对话使用建议

本工作流针对跨对话、跨 Agent 工具接续工作而设计，减少对聊天历史的依赖。独立 Task 建议开启新对话，同一 Task 也可跨多个对话完成。

建议在约 2～3 次上下文压缩后，选择阶段完成或其他安全交接点开启新对话。次数仅供参考，应根据任务和实际表现调整。

切换前通知 Agent 检查进度并更新 Task、相关 Debug 及必要的 `handoff.md`，保存关键证据，记录未提交修改及下一步。

开启新对话后，Agent 会通过 `AGENTS.md` 或其入口文件加载规则；未自动加载时，提醒 Agent 先阅读 `AGENTS.md`。接续已有任务时，可明确对应 Task，核对实际状态后继续。

## 4.工作流升级

实际项目所用的工作流版本记录在其 `AGENTS.md` 开头的“工作流版本”中，升级时对照 [CHANGELOG.md](CHANGELOG.md) 查看该版本之后的变更。

**AI 升级**：将下面这段话直接发给实际项目中的AI。

```text
仅执行开发工作流升级，不进行代码审查、全仓库扫描、构建或测试。
读取当前项目 AGENTS.md 开头的工作流版本，对照 https://github.com/keeshow/file-based-workflow 仓库的 CHANGELOG.md，
列出该版本之后的变更；AGENTS.md 中没有版本号时，先按内容比对判断所基于的版本，无法判断时整体比对。
只更新来自工作流的通用文件（AGENTS.md、docs/guides/ 下的写法说明和 docs/examples/ 下的示例），保留项目对 AGENTS.md 的自定义修改；
不修改 handoff.md、docs/project-rules.md、docs/tasks/、docs/notes/、docs/references/ 等项目自有内容。
涉及文件移动、删除或与项目修改冲突时，先列出处理方案并等待我的决定。
完成后报告升级前后的版本号，以及新增、修改、删除的文件。
```

**人工升级**：按 CHANGELOG 中的变更说明，用新版 [workflow/](workflow/) 中的 `AGENTS.md`、`docs/guides/` 和 `docs/examples/` 替换项目中的对应文件，并合并项目自行修改过的规则；变更说明涉及文件移动或删除时一并处理。项目自有的状态、任务和规则文档不随升级替换。
