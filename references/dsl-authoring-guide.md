# create-structure-md DSL 编写指南

## 总原则

从读者问题开始，而不是从目录枚举开始。先判断读者为了理解仓库需要知道什么，再选择最少且最清楚的路径、模块、流程和机制作为证据。

主动区分源事实和过程材料。`structure.manifest.json` 与子 JSON 文件是可渲染 DSL；仓库理解笔记、子代理报告、命令记录、扫描日志、被拒草稿都不属于 DSL 包。

create-structure-md 0.4.0 的固定章节由渲染器拥有标题。固定章节不要携带 `key` 或 `title`；额外小节才携带 `key`、`title` 和 `blocks`。

## 内容块使用规则

Text blocks 用于叙述、解释、承接上下文。

Unordered lists 用于并列事实，例如能力、边界、注意事项。

Ordered lists 用于有顺序的动作，例如首次运行、调试路径、发布流程。

Tables 用于紧凑比较，例如组件职责、输入输出、文件和用途的少量对照。

Mermaid blocks 用于关系或行为路径，必须能通过 strict Mermaid CLI rendering。Mermaid 可读性规则以本指南为准：优先使用 `flowchart` 或 `sequenceDiagram`，优先用 `flowchart` 而不是 legacy `graph`，标签保持人类可读，不在可见标签中暴露内部 ID。

Code blocks 用于最小、具体、可执行或可识别的用法示例。不要用大段代码替代解释。

List block 的 `items` 值只能是字符串数组，不能混入对象、数字或嵌套结构。

## 概述怎么写

概述回答“这个仓库是什么、解决什么问题、读者接下来该怎么看”。它可以点出核心用途、主要读者、输入输出和阅读地图。

概述不要写安装步骤、模块内部机制、函数调用链或完整目录列表。细节应进入快速开始、架构概述、主线流程或模块详解。

## 快速开始怎么写

快速开始回答“怎样第一次跑起来或完成最小验证”。`first_run.steps[]` 按数组位置表达顺序，每个 step 包含自己的 blocks。

保持步骤可执行、短小、面向入门。不要把快速开始写成平台百科、依赖历史、全部配置项说明或故障排查合集。

## 架构概述怎么写

架构概述回答“仓库由哪些主要部分组成，它们如何协作”。`layers.layer_table.rows` 描述软件分层，`module_map.module_table.rows` 描述模块划分，二者后面都可以追加 blocks。

组件描述应帮助读者建立整体地图。不要在这里展开模块内部机制；机制应放在对应 module object 中。

## 主线流程怎么写

主线流程回答“一个重要任务如何跨组件移动”。`main_flows.flows[]` 没有 `steps` 字段；用 blocks 叙述流程，必要时配 Mermaid 表达关系或行为路径。

不要把主线流程写成逐函数调用链、日志转写或源码扫描结果。

## 模块详解怎么写

模块详解回答“每个重要模块负责什么、靠什么机制工作、读者修改时该注意什么”。模块标题来自 `module_details.modules[].name`。

Mechanisms 必须存在于 module objects 内。模块内容可以包含职责、关键路径、输入输出、机制、扩展点和风险，但不要变成逐文件清单或 API reference pages。

## 不要写什么

不要写 file-list dumps、call-chain dumps、API-reference drift、process metadata、unsupported block shapes。

不要把子代理名字、命令 transcripts、raw scan logs、rejected drafts 写进 JSON。

不要把 Mermaid 静态可读性检查当作渲染证明；存在 Mermaid blocks 时必须通过 strict Mermaid CLI rendering。

## 写完检查

检查内容是否从读者问题开始，而不是从目录枚举开始。

检查固定章节是否没有 `key` 或 `title`，额外小节是否有 `key`、`title` 和 `blocks`。

检查 overview 是否包含 `core_components.component_table.rows`，architecture overview 是否包含 `layers.layer_table.rows` 和 `module_map.module_table.rows`。

检查 `first_run.steps[]` 是否按数组位置表达顺序，且每个 step 包含 blocks。

检查 `main_flows.flows[]` 是否没有 `steps` 字段。

检查 mechanisms 是否在 module objects 内。

检查 list block `items` 是否全部为字符串数组。

检查 Mermaid blocks 是否简短、人类可读、不暴露内部 ID，并能通过 Mermaid CLI 渲染。
