# create-structure-md 0.4.0 Detail List Upgrade Design

Date: 2026-05-27
Status: draft for user review

## Context

The current active create-structure-md 0.4.0 package has a fixed six-file shape:

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

This shape keeps the rendered document simple, but it makes the most content-heavy sections too coarse for reliable subagent ownership:

- Chapter 4 stores all main flows in one aggregate file.
- Chapter 5 stores all module details in one aggregate file.
- `SKILL.md` does not yet enforce a create-interface-md-style workflow where each substantive detail file is authored and reviewed by a bounded subagent.
- Overview tables for Chapter 4 and Chapter 5 are not derived from accepted detail files.

The next phase is a breaking upgrade to the active 0.4.0 contract. It keeps the version name `0.4.0`, but changes the manifest shape, authoring workflow, schema, renderer, examples, and tests. This is intentional: old active 0.4.0 aggregate packages should be rejected after the upgrade.

The historical 0.3.0 implementation under `docs/superpowers/history/V3/` remains historical reference and should continue to be dispatchable by the root CLIs where that behavior already exists.

## Goals

- Upgrade active 0.4.0 to use manifest-listed detail files for main flows and modules.
- Make one main-flow detail file the only JSON deliverable for one main-flow authoring subagent.
- Make one module detail file the only JSON deliverable for one module authoring subagent.
- Require separate adversarial review for each accepted detail file.
- Make `main_flow_overview` and `module_overview` fixed table overview files synthesized after detail files are accepted.
- Align `SKILL.md` with create-interface-md's main-agent orchestration model.
- Keep process metadata, subagent reports, command transcripts, raw scan logs, and rejected drafts outside renderable JSON.
- Preserve the reader-first shape of the rendered guide:

```markdown
# <repository_name> 结构说明

## 入门

### 概述
### 快速开始

## 深入解析

### 架构概述
### 主线流程
### 模块详解
```

## Non-Goals

- Do not preserve compatibility with the old active 0.4.0 six-field manifest.
- Do not introduce a new public version name such as 0.5.0.
- Do not move 0.3.0 out of `docs/superpowers/history/V3/`.
- Do not turn main-flow details into function-by-function call chains.
- Do not turn module details into file dumps, API references, or platform encyclopedias.
- Do not let subagent reports become DSL payload.
- Do not execute deletion commands as part of implementation. Old files may need to be removed, but commands must be given to the user to run.

## Package Shape

The upgraded active 0.4.0 manifest has exactly eight top-level fields:

```json
{
  "document": "chapters/00-document.json",
  "overview": "chapters/01-overview.json",
  "quick_start": "chapters/02-quick-start.json",
  "architecture_overview": "chapters/03-architecture-overview.json",
  "main_flow_overview": "chapters/04-main-flow-overview.json",
  "main_flow_details": [
    "chapters/04-main-flow-details/init-flow.json"
  ],
  "module_overview": "chapters/05-module-overview.json",
  "module_details": [
    "chapters/05-module-details/storage.json"
  ]
}
```

Rules:

- `document`, `overview`, `quick_start`, `architecture_overview`, `main_flow_overview`, and `module_overview` are fixed single child paths.
- `main_flow_details` is a non-empty array of main-flow detail paths.
- `module_details` is a non-empty array of module detail paths.
- Array order is render order.
- Detail keys are inferred from file stems. The key is not repeated in JSON.
- Detail file stems must match `^[a-z0-9][a-z0-9_-]*$`.
- Manifest paths must be unique relative POSIX `.json` paths.
- Manifest paths must not be absolute, contain backslashes, contain `//`, contain `.` or `..` path segments, or resolve outside the package root.
- The old aggregate paths are invalid in active 0.4.0:
  - `chapters/04-main-flows.json`
  - `chapters/05-module-details.json` as a single aggregate file
- Neither the manifest nor payload JSON files include `dsl_version`.

## Rendered Structure

The renderer keeps the visible high-level structure:

```markdown
# <repository_name> 结构说明

## 入门

### 概述
### 快速开始

## 深入解析

### 架构概述
### 主线流程
### 模块详解
```

Chapter 4 renders:

1. `### 主线流程`
2. Optional `main_flow_overview.intro`
3. A fixed main-flow overview table
4. Each file in `main_flow_details[]` as one `#### <title>` section, in manifest order

Chapter 5 renders:

1. `### 模块详解`
2. Optional `module_overview.intro`
3. A fixed module overview table
4. Each file in `module_details[]` as one `#### <name>` section, in manifest order

## Main Flow Overview

`chapters/04-main-flow-overview.json` is a post-detail synthesis artifact. It is generated or updated only after all accepted main-flow detail files have passed authoring and review.

It has a fixed table shape:

```json
{
  "main_flow_overview": {
    "intro": "本章按读者最常遇到的行为路径说明仓库如何工作。",
    "flow_table": {
      "rows": [
        {
          "flow": "初始化主线",
          "purpose": "理解初始化请求如何跨组件完成。",
          "entry": "example_init",
          "location": "src/api/init.py",
          "anchor": "初始化主线"
        }
      ]
    }
  }
}
```

Rules:

- `intro` is optional and must be a short string when present.
- `flow_table.rows` is required and non-empty.
- Overview files do not contain `blocks`, `extra_subsections`, Mermaid, code, examples, or detail prose.
- Rows must match `main_flow_details[]` exactly in count and order.
- `flow` and `anchor` must match the corresponding detail file's `title`.
- `purpose`, `entry`, and `location` must match the corresponding detail file's `purpose` and `entry`.
- The renderer turns `flow` into a link to the corresponding detail heading.

Rendered form:

```markdown
### 主线流程

本章按读者最常遇到的行为路径说明仓库如何工作。

| 主线 | 目的 | 入口 | 位置 |
| --- | --- | --- | --- |
| [初始化主线](#初始化主线) | 理解初始化请求如何跨组件完成。 | `example_init` | src/api/init.py |
```

## Main Flow Detail

Each file in `main_flow_details[]` describes exactly one reader-facing behavior path. The file does not contain a top-level `chapter` object and does not contain its inferred key.

Example:

```json
{
  "title": "初始化主线",
  "purpose": "帮助读者理解初始化请求如何跨组件完成。",
  "reader_goal": "读者想知道调用初始化入口后仓库内部发生什么。",
  "entry": {
    "name": "example_init",
    "location": "src/api/init.py"
  },
  "blocks": [
    {
      "type": "text",
      "content": "初始化入口读取配置，协调存储模块写入初始状态。"
    }
  ],
  "extra_subsections": []
}
```

Rules:

- Required fields: `title`, `purpose`, `reader_goal`, `entry`, `blocks`, and `extra_subsections`.
- `entry.name` is required.
- `entry.location` is optional.
- `blocks` uses the existing shared block types.
- `extra_subsections` uses the existing `key`, `title`, `blocks` shape.
- The file must describe a behavior path that matters to the reader.
- The file must not contain a step-by-step call-chain dump.
- The file must not contain process metadata.

Rendered form:

```markdown
#### 初始化主线

目的：帮助读者理解初始化请求如何跨组件完成。

读者目标：读者想知道调用初始化入口后仓库内部发生什么。

入口：`example_init`

位置：src/api/init.py

初始化入口读取配置，协调存储模块写入初始状态。
```

## Module Overview

`chapters/05-module-overview.json` is a post-detail synthesis artifact. It is generated or updated only after all accepted module detail files have passed authoring and adversarial review.

It has a fixed table shape:

```json
{
  "module_overview": {
    "intro": "本章按责任单元说明仓库的关键模块。",
    "module_table": {
      "rows": [
        {
          "module": "存储模块",
          "purpose": "保存初始化流程产生的状态。",
          "location": "src/storage.py",
          "anchor": "存储模块"
        }
      ]
    }
  }
}
```

Rules:

- `intro` is optional and must be a short string when present.
- `module_table.rows` is required and non-empty.
- Overview files do not contain `blocks`, `extra_subsections`, Mermaid, code, examples, mechanisms, or detail prose.
- Rows must match `module_details[]` exactly in count and order.
- `module` and `anchor` must match the corresponding detail file's `name`.
- `purpose` and `location` must match the corresponding detail file's `purpose` and `location`.
- The renderer turns `module` into a link to the corresponding detail heading.

Rendered form:

```markdown
### 模块详解

本章按责任单元说明仓库的关键模块。

| 模块 | 职责 | 位置 |
| --- | --- | --- |
| [存储模块](#存储模块) | 保存初始化流程产生的状态。 | src/storage.py |
```

## Module Detail

Each file in `module_details[]` describes exactly one responsibility unit. The file does not contain a top-level `chapter` object and does not contain its inferred key.

Example:

```json
{
  "name": "存储模块",
  "location": "src/storage.py",
  "purpose": "保存初始化流程产生的状态。",
  "responsibilities": [
    "保存初始化结果",
    "提供追加写入机制"
  ],
  "blocks": [
    {
      "type": "text",
      "content": "存储模块负责把初始化结果持久化到本地状态。"
    }
  ],
  "mechanisms": [
    {
      "title": "追加写入",
      "blocks": [
        {
          "type": "text",
          "content": "追加写入保留已有记录并写入新的初始化结果。"
        }
      ]
    }
  ],
  "extra_subsections": []
}
```

Rules:

- Required fields: `name`, `location`, `purpose`, `responsibilities`, `blocks`, `mechanisms`, and `extra_subsections`.
- `responsibilities` is a non-empty string array.
- `mechanisms` is an array. It may be empty when no mechanism needs reader-level explanation.
- Mechanisms live inside the owning module detail file.
- The file must describe a responsibility unit, not a source file listing.
- The file must not become an API reference page.
- The file must not contain process metadata.

Rendered form:

```markdown
#### 存储模块

位置：src/storage.py

职责：保存初始化流程产生的状态。

##### 责任

- 保存初始化结果
- 提供追加写入机制

存储模块负责把初始化结果持久化到本地状态。

##### 追加写入

追加写入保留已有记录并写入新的初始化结果。
```

## Shared Blocks

The existing 0.4.0 shared block types remain valid in detail files and existing fixed sections:

```text
text
unordered_list
ordered_list
table
mermaid
code
```

Overview files for Chapter 4 and Chapter 5 do not use shared blocks. They render only optional `intro` plus their fixed overview table.

## Subagent Workflow

`SKILL.md` must be rewritten to make create-structure-md behave like create-interface-md's orchestration model.

### Main Agent Responsibilities

The main agent owns:

- package orchestration
- dispatch brief creation
- contract and authoring-guide loading
- planning and ownership-review dispatch
- manifest creation
- overview synthesis after details are accepted
- validation
- rendering
- final review

The main agent does not directly author substantive Chapter 4 or Chapter 5 detail prose.

### Planning Subagent

The planning subagent analyzes user intent and repository evidence, then proposes:

```text
repository_identity
target_readers
reader_questions
overview_candidates
quick_start_candidates
architecture_candidates
main_flow_candidates
module_candidates
excluded_or_deferred_content
open_questions
repo_understand_usage
```

It does not write DSL JSON.

### Ownership Freeze Subagent

The ownership/freeze subagent challenges the planning output and freezes:

```text
accepted_main_flows:
  - flow_key
    title
    reader_goal
    target_output_path
    authoring_owner
    review_owner

accepted_modules:
  - module_key
    name
    responsibility_unit
    target_output_path
    authoring_owner
    review_owner
```

It decides whether each candidate is accepted, merged, split, excluded, or sent back for planning revision.

### Main Flow Authoring Subagents

Each main-flow authoring subagent writes exactly one file:

```text
chapters/04-main-flow-details/<flow-key>.json
```

It may only modify its assigned file. It must not edit the manifest, overview files, other flow files, module files, references, scripts, or tests.

Output contract:

```text
flow_key
title
purpose
reader_goal
entry
generated_file
source_evidence_summary
excluded_details
unresolved_gaps
repo_understand_usage
```

### Module Authoring Subagents

Each module authoring subagent writes exactly one file:

```text
chapters/05-module-details/<module-key>.json
```

It may only modify its assigned file. It must not edit the manifest, overview files, other module files, flow files, references, scripts, or tests.

Output contract:

```text
module_key
name
location
purpose
responsibilities
generated_file
mechanisms
source_evidence_summary
excluded_details
unresolved_gaps
repo_understand_usage
```

### Adversarial Review Subagents

Every detail file gets a separate adversarial reviewer.

Main-flow reviewers ask:

- Is this a reader-facing behavior path?
- Is it avoiding function-by-function call-chain dumping?
- Is the entry meaningful to the target reader?
- Are Mermaid labels readable?
- Is process metadata absent?

Module reviewers ask:

- Is this a responsibility unit?
- Is it avoiding file listing and API-reference behavior?
- Are mechanisms inside the owning module?
- Are Mermaid labels readable?
- Is process metadata absent?

Reviewers may modify only the assigned detail file. They must not edit package-level files or other detail files.

Output contract:

```text
detail_key
review_decision: accept | changes_applied | reject_detail | split_required
generated_file
kept_content
removed_content
required_changes
validation_command
validation_result
repo_understand_usage
```

### Overview Synthesis

After all accepted detail files pass review:

- The main agent synthesizes `chapters/04-main-flow-overview.json` from `main_flow_details[]`.
- The main agent synthesizes `chapters/05-module-overview.json` from `module_details[]`.
- The overview rows must exactly match accepted detail files in manifest order.

## Validation

The validator must enforce:

- Active 0.4.0 manifest uses exactly the upgraded eight-field shape.
- Old active 0.4.0 aggregate manifests are rejected.
- `main_flow_details[]` and `module_details[]` are non-empty arrays.
- Detail paths are unique and stay inside the package root.
- Detail stems match the key pattern.
- Forbidden aggregate detail paths are rejected.
- Detail files omit top-level `chapter`.
- Overview files have only their fixed table shapes.
- Overview rows match detail arrays exactly in count and order.
- Overview row values match corresponding detail metadata.
- Process metadata is absent from all JSON string fields.
- Existing Mermaid gate applies to all detail files.
- Existing shared block validation applies to all detail files.
- `main_flow_details[]` with more than three entries emits the existing warning.
- Module file-only warnings apply to module detail files.

Single-file validation helpers should be added for subagent handoff:

```bash
python scripts/validate_flow_detail.py <package>/chapters/04-main-flow-details/<flow-key>.json --package-root <package>
python scripts/validate_module_detail.py <package>/chapters/05-module-details/<module-key>.json --package-root <package>
```

These commands validate one assigned detail file in the context of the package and return clear paths using `$.main_flow_details[index]` or `$.module_details[index]`.

## Rendering

The renderer must:

- Render detail files in manifest array order.
- Render Chapter 4 overview as a fixed table before flow details.
- Render Chapter 5 overview as a fixed table before module details.
- Generate Markdown links from overview table rows to detail headings.
- Preserve current heading levels:
  - main-flow details render as `#### <title>`
  - module details render as `#### <name>`
  - module mechanisms render as `##### <title>`
- Preserve current table escaping and code fence safety behavior.
- Never render inferred keys unless they are useful in diagnostics. Keys are routing metadata, not reader-facing text.

## Implementation Discipline

Documentation-only changes do not use TDD. They require review instead.

Documentation-only files include:

- `SKILL.md`
- `references/*.md`
- `docs/superpowers/specs/*.md`
- `docs/superpowers/plans/*.md`

Documentation tasks must use:

- checklist comparison against this spec
- placeholder scan
- contradiction scan
- ambiguity scan
- subagent or human review where requested

Code, schema, and example-package changes use TDD.

TDD files include:

- `scripts/*.py`
- `schemas/v0.4.0/*.json`
- `tests/*.py`
- `examples/minimal-reader-guide/**/*.json`
- `requirements.txt` when behavior depends on it

For these tasks:

1. Write the failing test first.
2. Run it and confirm the expected failure.
3. Implement the minimum code, schema, or fixture change.
4. Run the test and confirm it passes.
5. Run relevant regression tests.

JSON schema is executable contract and follows the TDD path. Example packages are fixtures and follow the TDD path.

## Files To Modify In Implementation

Documentation and workflow:

- `SKILL.md`
- `references/dsl-spec.md`
- `references/dsl-authoring-guide.md`
- `references/document-structure.md`
- `references/review-checklist.md`

Code and schema:

- `scripts/v040_package.py`
- `scripts/build_v040_chapter_schema.py`
- `schemas/v0.4.0/structure.manifest.schema.json`
- `schemas/v0.4.0/chapter.schema.json`
- `scripts/v040_schema.py`
- `scripts/v040_semantics.py`
- `scripts/v040_mermaid.py`
- `scripts/v040_renderer.py`
- `scripts/validate_structure.py`
- `scripts/render_markdown.py`
- `scripts/validate_flow_detail.py`
- `scripts/validate_module_detail.py`

Examples:

- `examples/minimal-reader-guide/structure.manifest.json`
- `examples/minimal-reader-guide/chapters/04-main-flow-overview.json`
- `examples/minimal-reader-guide/chapters/04-main-flow-details/init-flow.json`
- `examples/minimal-reader-guide/chapters/05-module-overview.json`
- `examples/minimal-reader-guide/chapters/05-module-details/storage.json`

The old example aggregate files become invalid:

- `examples/minimal-reader-guide/chapters/04-main-flows.json`
- `examples/minimal-reader-guide/chapters/05-module-details.json`

Do not delete these automatically. Provide deletion commands for the user when implementation reaches cleanup.

Tests:

- `tests/test_v040_manifest.py`
- `tests/test_v040_chapter_schema.py`
- `tests/test_v040_cli.py`
- `tests/test_v040_docs.py`
- `tests/test_v040_e2e.py`
- `tests/test_v040_mermaid.py`
- `tests/test_v040_renderer.py`
- `tests/test_v040_semantics.py`
- `tests/helpers_v040.py`

## Test Boundaries

Manifest tests:

- Accept the upgraded eight-field manifest.
- Reject the old six-field active 0.4.0 manifest.
- Reject empty `main_flow_details[]`.
- Reject empty `module_details[]`.
- Reject forbidden aggregate detail paths.
- Reject invalid detail file stems.
- Reject duplicate paths.
- Reject paths that escape the package root.

Schema tests:

- Accept valid main-flow overview.
- Accept valid module overview.
- Accept valid main-flow detail.
- Accept valid module detail.
- Reject overview `blocks` and `extra_subsections`.
- Reject detail top-level `chapter`.
- Reject unsupported block shapes.

Renderer tests:

- Render fixed Chapter 4 overview table.
- Render fixed Chapter 5 overview table.
- Link overview rows to detail headings.
- Render detail files in manifest order.
- Render module mechanisms inside the owning module.
- Preserve code fence safety and table escaping.

Semantic tests:

- Reject overview rows that do not match detail arrays.
- Reject overview rows out of order.
- Reject overview anchors that do not match detail headings.
- Reject process metadata anywhere in overview or detail JSON.
- Warn when more than three main-flow detail files are selected.
- Warn when a module detail looks like a file-only listing.

Mermaid tests:

- Traverse Mermaid blocks in flow detail files.
- Traverse Mermaid blocks in module detail files.
- Do not require Mermaid CLI when no detail file has Mermaid.
- Report missing CLI, non-zero CLI, timeout, and missing SVG with detail index/key paths.

CLI tests:

- Root validate/render accept the upgraded active 0.4.0 package.
- Root validate rejects the old active 0.4.0 aggregate package with a clear migration message.
- 0.3.0 historical dispatch remains functional.
- Single-file flow detail validation works.
- Single-file module detail validation works.

End-to-end tests:

- Minimal upgraded package validates in strict mode.
- Minimal upgraded package renders Markdown with fixed overview tables and detail sections.

## Migration Strategy

This is a breaking active 0.4.0 upgrade.

Migration rules:

1. Do not keep old active 0.4.0 aggregate format compatibility.
2. Migrate the minimal example package to the upgraded manifest shape.
3. Reject old active 0.4.0 aggregate manifest with a clear error.
4. Keep 0.3.0 historical dispatch unchanged.
5. Keep rendered Markdown generated from JSON only.
6. Do not execute deletion commands. Give cleanup commands to the user for old invalid files.

Suggested implementation order:

1. Update docs-only contract and skill workflow. Review only, no TDD.
2. Add failing manifest/package loader tests for the upgraded shape.
3. Implement upgraded manifest loading and path/key validation.
4. Add failing schema tests for overview/detail files.
5. Implement schema generation and regenerated schema files.
6. Add failing example/e2e tests for the upgraded package.
7. Migrate the minimal example package.
8. Add failing renderer tests for fixed overview tables and detail ordering.
9. Implement renderer changes.
10. Add failing semantic and Mermaid traversal tests.
11. Implement semantic and Mermaid traversal changes.
12. Add failing CLI and single-file validation tests.
13. Implement root CLI and detail validation commands.
14. Run full verification and provide user-run cleanup commands for old invalid aggregate files.

## Acceptance Criteria

The next phase is accepted when:

- `SKILL.md` enforces create-interface-md-style orchestration for structure guides.
- Manifest shape is the upgraded eight-field active 0.4.0 contract.
- Each main-flow detail is independently authorable and reviewable.
- Each module detail is independently authorable and reviewable.
- `main_flow_overview` and `module_overview` are fixed table post-detail synthesis artifacts.
- Old active 0.4.0 aggregate files are invalid.
- The minimal example package uses the upgraded shape.
- Full validation and render pass for the upgraded minimal package.
- 0.3.0 historical dispatch still works.
- Documentation tasks were reviewed rather than TDD-tested.
- Code, schema, and example-package changes followed TDD.
