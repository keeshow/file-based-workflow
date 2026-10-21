# 文件驱动的 Agent 开发工作流

当前版本：2026-10-21-01。

通过 `AGENTS.md` 约定协作规则，Task 管理当前任务和验收，Handoff 交接项目状态，Note 保存可复用的技术结论。

## 1.工作流引入

将 [workflow/](workflow/) 内的全部框架复制到实际项目根目录即可使用，复制后 `AGENTS.md`、`handoff.md` 和 `docs/` 均位于项目根目录下。

已有同名文件时先比较、合并，保留项目原有规则、文档和状态，勿用空白的 `handoff.md` 或 `docs/` 文件覆盖已有内容。

## 2.框架简介

```text
workflow/                         # 当前版本的完整工作流框架
├── AGENTS.md                     # 通用协作、任务管理、验证与文档维护规范
├── handoff.md                    # 项目状态与交接快照，初始为空
├── handoff.md.example            # Handoff 示例，展示项目状态、阻塞及下一步行动的写法
└── docs/                         # 项目文档目录
    ├── README.md                 # 重要文档导航索引，初始为空
    ├── project-rules.md          # 项目专属约束，初始为空，由用户确定内容
    ├── tasks/                    # 独立任务的目标、实施进度、验收结果与遗留问题
    │   └── 00-task.md.example    # Task 示例，展示功能已实现但验收尚未结束的记录方式
    ├── notes/                    # 可复用的方案、故障分析与技术结论
    └── references/               # 原始参考资料及其来源、版本信息
```

`.example` 文件中的项目、路径和结果均为示例。保留示例文件供查阅，实际 Task 和 handoff 另按项目事实编写；不把示例列入任务索引或当作完成证据。章节可以按需精简。

各版本的完整框架快照与修改原因见 [.history/README.md](.history/README.md)。
