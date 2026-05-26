# create-structure-md Reader Guide Redesign

Date: 2026-05-26
Status: approved design for implementation planning

## Context

The current 0.3.0 output is structurally valid but reads like a field dump. The DSL asks for many detailed slots, and the renderer expands those slots into repeated tables and module cards. For readers who want to understand a repository, this creates too much surface area before they have a mental model.

The next version intentionally breaks compatibility. It changes the product from an eight-chapter repository structure report into a two-part repository guide:

1. `入门`
2. `深入解析`

The guide should help readers first understand what the repository is and how to use it, then understand how it is organized internally.

## Goals

- Replace the fixed eight-chapter 0.3.0 document with a two-part guide.
- Keep the DSL structured enough to validate and render predictably.
- Give agents high authoring freedom inside each section through reusable content blocks.
- Move key mechanisms inside module details instead of rendering a standalone mechanism chapter.
- Add one canonical authoring reference file that tells agents how to think, choose content, and fill the DSL.
- Rebuild `SKILL.md` around a main-agent orchestration workflow with optional repository-planning, structure-review, module-authoring, and adversarial-review subagents.
- Keep process logs, analysis transcripts, subagent identities, and rejected reasoning out of the renderable DSL.

## Non-Goals

- No compatibility with 0.3.0 `structure.manifest.json` chapter keys.
- No standalone `关键机制` chapter.
- No standalone `验证与风险` chapter.
- No full directory tree dump.
- No API reference behavior in the structure guide.
- No deletion workflow. Cleanup, if ever needed, is handled by user-run commands.

## Document Structure

The rendered Markdown uses this visible structure:

```markdown
# <仓库名> 结构说明

## 入门

### 概述
### 快速开始

## 深入解析

### 架构概述
### 主线流程
### 模块详解
```

The renderer owns fixed section titles. Fixed DSL sections do not repeat `key` or `title`.

## Package Shape

The new manifest should contain fixed paths for the five content files plus minimal document metadata:

```json
{
  "document": "chapters/00-document.json",
  "overview": "chapters/01-overview.json",
  "quick_start": "chapters/02-quick-start.json",
  "architecture_overview": "chapters/03-architecture-overview.json",
  "main_flows": "chapters/04-main-flows.json",
  "module_details": "chapters/05-module-details.json"
}
```

The child files store renderable content only. They must not store prompts, command transcripts, raw scan logs, subagent names, or validation reports.

## Shared Content Blocks

Most sections are composed from free content blocks. Supported block types are:

```text
text
unordered_list
ordered_list
table
mermaid
code
```

### Text Block

```json
{
  "type": "text",
  "content": "EasyFlash 是一个面向嵌入式设备的 Flash 持久化存储库。"
}
```

### List Blocks

Lists use string arrays only. They do not support nested item objects or `details`.

```json
{
  "type": "unordered_list",
  "items": [
    "支持 ENV 键值持久化",
    "支持 Flash 日志保存"
  ]
}
```

```json
{
  "type": "ordered_list",
  "items": [
    "引入仓库",
    "完成必要配置",
    "运行最小示例"
  ]
}
```

### Table Block

```json
{
  "type": "table",
  "columns": ["功能", "说明"],
  "rows": [
    ["ENV", "保存配置数据"]
  ]
}
```

### Mermaid Block

```json
{
  "type": "mermaid",
  "title": "仓库定位",
  "diagram_type": "flowchart",
  "source": "flowchart LR\n  app[应用] --> api[公共 API]"
}
```

Mermaid labels should be human-readable and must not expose internal IDs.

### Code Block

```json
{
  "type": "code",
  "language": "c",
  "title": "最小入口",
  "content": "easyflash_init();"
}
```

`title` is optional for code blocks.

## Extra Subsections

Each major section can include extra subsections after its fixed content:

```json
{
  "key": "mental_model",
  "title": "理解这个仓库的方式",
  "blocks": [
    {
      "type": "text",
      "content": "可以把这个仓库理解为公共 API、核心实现和平台适配三层。"
    }
  ]
}
```

Extra subsection keys must be stable, lower-case identifiers. Extra subsections render in array order.

## Section DSL

### Overview

`overview` answers:

- 当前仓库是什么
- 当前仓库解决什么问题
- 当前仓库的主要功能是什么
- 当前仓库由哪些核心组件组成

DSL:

```json
{
  "overview": {
    "repository_intro": {
      "blocks": []
    },
    "problems_solved": {
      "blocks": []
    },
    "main_capabilities": {
      "blocks": []
    },
    "core_components": {
      "component_table": {
        "rows": [
          {
            "component": "公共 API",
            "role": "提供应用调用入口和编译期配置项。",
            "location": "easyflash/inc"
          }
        ]
      },
      "blocks": []
    },
    "extra_subsections": []
  }
}
```

Fixed subsections render as:

- `当前仓库介绍`
- `解决的问题`
- `主要功能`
- `核心组件`

`core_components.component_table` must render before `core_components.blocks`. The table has exactly these semantic fields:

- `component`
- `role`
- `location`

The rendered table columns are fixed:

```markdown
| 组件 | 作用 | 位置 |
| --- | --- | --- |
```

### Quick Start

`quick_start` answers:

- 这个仓库适合哪些最小使用场景
- 使用前需要准备什么
- 第一次运行或接入怎么做
- 最小示例是什么
- 成功结果应该是什么

DSL:

```json
{
  "quick_start": {
    "usage_scenarios": {
      "blocks": []
    },
    "setup": {
      "blocks": []
    },
    "first_run": {
      "steps": [
        {
          "title": "初始化仓库能力",
          "blocks": []
        }
      ],
      "blocks": []
    },
    "minimal_example": {
      "blocks": []
    },
    "expected_result": {
      "blocks": []
    },
    "extra_subsections": []
  }
}
```

Fixed subsections render as:

- `使用场景`
- `准备工作`
- `第一次运行/接入`
- `最小示例`
- `预期结果`

`first_run.steps` is required and non-empty. Each step has `title` and `blocks`. Step order is the array order; no `order` field is needed.

### Architecture Overview

`architecture_overview` answers:

- 这个仓库整体如何分层
- 模块如何划分
- 模块之间是什么关系
- 目录各自扮演什么角色

DSL:

```json
{
  "architecture_overview": {
    "architecture_summary": {
      "blocks": []
    },
    "layers": {
      "layer_table": {
        "rows": [
          {
            "layer": "公共接口层",
            "role": "暴露应用可调用 API 和配置入口。",
            "location": "easyflash/inc"
          }
        ]
      },
      "blocks": []
    },
    "module_map": {
      "module_table": {
        "rows": [
          {
            "module": "ENV 模块",
            "role": "负责键值数据持久化。",
            "layer": "核心实现层",
            "location": "easyflash/src/ef_env.c"
          }
        ]
      },
      "blocks": []
    },
    "repository_layout": {
      "blocks": []
    },
    "extra_subsections": []
  }
}
```

Fixed subsections render as:

- `架构总览`
- `软件分层`
- `模块划分`
- `目录角色`

`layers.layer_table` renders before `layers.blocks` and has fixed columns:

```markdown
| 层 | 作用 | 位置 |
| --- | --- | --- |
```

`module_map.module_table` renders before `module_map.blocks` and has fixed columns:

```markdown
| 模块 | 作用 | 所在层 | 位置 |
| --- | --- | --- | --- |
```

### Main Flows

`main_flows` answers:

- 仓库最重要的行为路径是什么
- 这些路径从哪个入口开始
- 它们经过哪些关键模块
- 最终产生什么结果

DSL:

```json
{
  "main_flows": {
    "flow_overview": {
      "blocks": []
    },
    "flows": [
      {
        "title": "初始化主线",
        "purpose": "说明应用如何把仓库从未初始化状态带到可用状态。",
        "entry": {
          "name": "easyflash_init",
          "location": "easyflash/src/easyflash.c"
        },
        "blocks": []
      }
    ],
    "extra_subsections": []
  }
}
```

`flows` is required and non-empty. Recommended count is one to three. A flow has no `steps`; the agent explains it through free blocks.

`entry.location` is optional. Main flows must not become full call-chain dumps.

### Module Details

`module_details` answers:

- 每个重要模块负责什么
- 模块在哪里
- 模块内部如何工作
- 模块内部有哪些关键机制

DSL:

```json
{
  "module_details": {
    "intro_blocks": [],
    "modules": [
      {
        "name": "ENV 模块",
        "location": "easyflash/src/ef_env.c",
        "purpose": "负责键值数据在 Flash 上的持久化保存、读取、删除和恢复。",
        "blocks": [],
        "mechanisms": [
          {
            "title": "追加写与状态提交",
            "blocks": []
          }
        ],
        "extra_subsections": []
      }
    ],
    "extra_subsections": []
  }
}
```

`intro_blocks` render directly below `### 模块详解`; they do not create a subsection.

Each module renders as its own subsection. A module must represent a meaningful responsibility unit, not merely a file. `mechanisms` belong inside the module and do not require keys because they are not cross-section reference targets.

## Authoring Reference

Add one canonical reference file:

```text
references/dsl-authoring-guide.md
```

This file is required reading before an agent writes or revises DSL content. It should explain:

- how to think about the guide;
- how to choose content for each section;
- how to use each block type;
- how to avoid turning free blocks into unstructured dumps;
- what must not appear in each section;
- how to review the rendered document.

The reference should use this structure:

```markdown
# create-structure-md DSL 编写指南

## 总原则
## 内容块使用规则
## 概述怎么写
## 快速开始怎么写
## 架构概述怎么写
## 主线流程怎么写
## 模块详解怎么写
## 不要写什么
## 写完检查
```

The authoring guide should be concrete and operational. It should tell agents what evidence to inspect and how to decide whether content belongs in a section. It should not duplicate the full JSON Schema.

## Skill Redesign

`SKILL.md` should follow the same quality-control posture as `create-interface-md`: the skill is not just a render command wrapper. It owns workflow, delegation boundaries, acceptance checks, and final review. The detailed writing rules live in `references/dsl-authoring-guide.md`; `SKILL.md` stays concise and procedural.

### Target Skill Files

The implementation should update or add these files:

```text
SKILL.md
references/dsl-authoring-guide.md
references/dsl-spec.md
references/document-structure.md
references/review-checklist.md
```

The implementation should also create the matching schema, renderer, validator, tests, and examples for the new package shape. Historical 0.3.0 files may remain as reference material; do not delete them as part of this workflow.

### Core Boundary

`SKILL.md` must state these boundaries:

- The authoritative deliverables are the manifest and child JSON files.
- The rendered Markdown is generated from accepted DSL content.
- Repository understanding, subagent reports, command transcripts, and rejected drafts stay outside the DSL.
- The main agent owns package orchestration, cross-section consistency, validation, rendering, and final review.
- Subagents may analyze the repository or draft bounded content, but their reports are not renderable deliverables by themselves.

Unlike `create-interface-md`, this skill must not apply an external-interface-only test. Structure guides may explain internal modules, state machines, storage layouts, and implementation mechanisms when they help readers understand the repository.

### Step-by-Step Skill Workflow

`SKILL.md` should be rebuilt around this workflow:

1. **Confirm inputs and mode.**
   - Confirm package root.
   - Confirm repository root when repository-backed authoring or source validation is needed.
   - Confirm output path if the user has a preference.
   - Decide whether the user already has a package to validate/render or needs repository-backed DSL authoring.

2. **Read contract and authoring guide.**
   - Read `references/dsl-spec.md` for the authoritative data contract.
   - Read `references/dsl-authoring-guide.md` before writing or accepting JSON.
   - Read `references/document-structure.md` for rendered section order.
   - Read `references/review-checklist.md` before final acceptance.

3. **Capture a neutral dispatch brief.**
   - Record package root, repository root, output path, requested scope, known exclusions, and open questions.
   - Quote user-stated audience, scope, inclusion, and exclusion rules.
   - Do not turn raw directory names into modules before repository understanding.
   - Do not decide final main flows or module details before planning/review when subagents are used.

4. **Plan repository content.**
   - For unfamiliar repositories, use a planning pass before writing DSL.
   - For C repositories, prefer `repo-understand` and repo-analysis tools before raw source reading.
   - The planning output proposes repository identity, solved problems, main capabilities, core components, quick-start path, layers, modules, main flows, and module-detail candidates.
   - The planning output does not write final DSL unless the task is explicitly a small edit to an existing package.

5. **Review and freeze the guide outline.**
   - A structure-review pass challenges the planning output.
   - It freezes the component table rows, layer table rows, module table rows, selected main flows, and selected module-detail list.
   - It rejects source-layout-only modules, duplicate module purposes, excessive main flows, and content that belongs in another section.

6. **Draft bounded content.**
   - The main agent writes package-level and cross-section content.
   - Module-detail authoring may be delegated one module at a time.
   - A module authoring subagent owns only one module object under `module_details.modules[]`.
   - A subagent must not edit manifest, overview, quick start, architecture overview, main flows, or other module objects unless specifically assigned.

7. **Run adversarial content review when substantial content was authored.**
   - Reviewers challenge whether sections answer their intended reader questions.
   - Reviewers reject call-graph dumps, file-list dumps, API-reference drift, mechanism content outside module details, and unsupported extra subsections.
   - Reviewers may recommend edits, but the main agent remains responsible for final package consistency.

8. **Accept or reject drafted DSL.**
   - Accept only content that matches the DSL contract and authoring guide.
   - Reject subagent output when it writes process logs into JSON, invents unsupported block shapes, duplicates sections, or contradicts frozen module/flow ownership.
   - The main agent may integrate and polish structure-guide prose, but must not silently change source-backed factual conclusions from subagent reports.

9. **Validate, render, and review.**
   - Run schema and semantic validation.
   - Validate Mermaid diagrams.
   - Render Markdown.
   - Review the rendered document for readability, reader flow, and section boundaries, not just schema validity.

### Subagent Output Contracts

`SKILL.md` should include concise output contracts for common subagent roles.

Repository planning subagent:

```text
repository_identity
problems_solved
main_capabilities
core_components_candidates
quick_start_candidates
layer_candidates
module_candidates
main_flow_candidates
module_detail_candidates
suggested_extra_subsections
excluded_or_deferred_content
open_questions
repo_understand_usage
```

Structure review subagent:

```text
review_decision: accept | revise | split_scope | ask_user
accepted_component_table_rows
accepted_layer_table_rows
accepted_module_table_rows
accepted_main_flows
accepted_module_details
section_boundary_issues
content_budget_issues
required_revisions
repo_understand_usage
```

Module-detail authoring subagent:

```text
module_name
module_location
module_purpose
generated_module_object
mechanisms
source_evidence_summary
excluded_details
unresolved_gaps
repo_understand_usage
```

Adversarial review subagent:

```text
review_decision: accept | changes_needed | reject
section_boundary_findings
dump_or_overdetail_findings
unsupported_block_findings
module_fit_findings
main_flow_fit_findings
required_revisions
```

These reports are not JSON child files and must not be copied into the renderable DSL.

### Acceptance And Rejection Rules

`SKILL.md` should tell the main agent to accept DSL only when:

- all fixed sections exist;
- all fixed table structures are present exactly where required;
- free blocks use supported block types only;
- `first_run.steps`, `main_flows.flows`, and `module_details.modules` are non-empty;
- main flows are few and reader-facing, not full call chains;
- module details are responsibility units, not file-by-file listings;
- module mechanisms live inside their owning module;
- extra subsections have clear reader value;
- process metadata is absent from JSON.

Reject or revise content when:

- overview includes quick-start instructions, deep module mechanisms, or validation/risk material;
- quick start becomes a platform encyclopedia instead of a shortest successful path;
- architecture overview expands into module internals;
- main flows become function-by-function call graphs;
- module details become API reference pages;
- free blocks are used to bypass DSL constraints;
- subagent reports are pasted into child JSON.

### Authoring Reference Relationship

`SKILL.md` should not duplicate every field rule. It should point agents to `references/dsl-authoring-guide.md` before any DSL authoring work and give subagents only the relevant task brief plus that authoring guide. The authoring guide should carry the detailed "how to think and fill" instructions; `SKILL.md` should carry process and ownership rules.

## Validation Direction

Schema validation should enforce structure:

- fixed manifest keys;
- valid child JSON shapes;
- valid content block discriminators;
- required fixed sections;
- required table shapes for core components, layers, and module map;
- non-empty `first_run.steps`;
- non-empty `main_flows.flows`;
- non-empty `module_details.modules`.

Semantic validation should warn or fail when:

- rendered Mermaid uses legacy `graph`;
- Mermaid labels expose internal IDs;
- too many main flows are selected;
- a module detail entry looks like a single source file instead of a responsibility unit;
- `core_components` lacks exactly one component table;
- `layers` lacks exactly one layer table;
- `module_map` lacks exactly one module table.

Review checks should focus on whether the output reads like a repository guide:

- `入门` should let a reader understand and try the repository quickly.
- `深入解析` should explain organization, behavior paths, and module internals.
- No section should become a full file listing, API reference, or call graph.
