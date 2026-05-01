# create-structure-md Phase 5 Spec: Markdown Renderer

## Goal

Implement `scripts/render_markdown.py` to render one module- or system-specific Markdown structure design document from a validated DSL file.

This phase focuses on deterministic document generation, fixed section numbering, safe output paths, fixed table rendering, Mermaid fences, overwrite protection, and chapter-level empty states.

## Dependencies

Depends on Phases 1, 2, and 3.

The renderer assumes the DSL passed `validate_dsl.py`, but still performs defensive checks.

## CLI Contract

```bash
python scripts/render_markdown.py structure.dsl.json --output-dir .
python scripts/render_markdown.py structure.dsl.json --output-dir . --overwrite
python scripts/render_markdown.py structure.dsl.json --output-dir . --backup
```

Rules:

- One positional DSL JSON path is required.
- Missing file fails.
- Invalid JSON fails.
- Missing or invalid `document.output_file` fails.
- `--overwrite` and `--backup` are mutually exclusive.
- Renderer writes `document.output_file` under `--output-dir`.

## Output Filename

Renderer writes exactly one Markdown file.

`document.output_file` must:

- end with `.md`
- be module- or system-specific
- follow the recommended pattern `<documented-object-name>_STRUCTURE_DESIGN.md`
- not be generic-only
- not contain `/`, `\`, `..`, or control characters

Backup path:

```text
<output_file>.bak-YYYYMMDD_HHMMSS
```

Backup timestamp uses local system clock and `%Y%m%d_%H%M%S`.

## Fixed Markdown Structure

Renderer uses fixed numbering for all chapters and subchapters.

Optional content absence must not move later sections forward.

The final document always renders:

1. 文档信息
2. 系统概览
3. 架构视图
4. 模块设计
5. 运行时视图
6. 配置、数据与依赖关系
7. 跨模块协作关系
8. 关键流程
9. 结构问题与改进建议

Required fixed empty states include:

- missing runtime sequence diagram: `未提供运行时序图。`
- single-module collaboration: `本系统当前仅识别到一个结构模块，暂无跨模块协作关系。`
- missing collaboration diagram: `未提供跨模块协作关系图。`
- empty supplement sections: `无补充内容。` or a more specific table/diagram sentence.

Full outline:

```text
# 软件结构设计说明书

1. 文档信息
2. 系统概览
3. 架构视图
   3.1 架构概述
   3.2 各模块介绍
   3.3 模块关系图
   3.4 补充架构图表
4. 模块设计
   4.x 模块名
   4.x.1 模块概述
   4.x.2 模块职责
   4.x.3 对外能力说明
   4.x.4 对外接口需求清单
   4.x.5 模块内部结构关系图
   4.x.6 补充说明
5. 运行时视图
   5.1 运行时概述
   5.2 运行单元说明
   5.3 运行时流程图
   5.4 运行时序图（推荐）
   5.5 补充运行时图表
6. 配置、数据与依赖关系
   6.1 配置项说明
   6.2 关键结构数据与产物
   6.3 依赖项说明
   6.4 补充图表
7. 跨模块协作关系
   7.1 协作关系概述
   7.2 跨模块协作说明
   7.3 跨模块协作关系图
   7.4 补充协作图表
8. 关键流程
   8.1 关键流程概述
   8.2 关键流程清单
   8.x 流程名
   8.x.1 流程概述
   8.x.2 步骤说明
   8.x.3 异常/分支说明
   8.x.4 流程图
9. 结构问题与改进建议
```

The renderer owns all headings. Free-form DSL fields must not add new chapter or subchapter headings.

## Rendering Responsibilities

Renderer owns:

- fixed chapter order
- fixed section numbering
- fixed table headers
- empty-state text
- Mermaid fence generation
- safe source snippet fences
- support-data insertion hooks
- chapter 9 appended sections
- Markdown escaping

Renderer must not invent design content.

## Chapter Rendering Rules

Chapter 1 renders `document` as a compact metadata table. If `generated_at` is empty, the renderer fills the rendered value from the local system clock and does not mutate the DSL file.

Chapter 2 renders:

- system summary
- purpose
- core capability table or list
- notes when present

Chapter 3 renders:

- `3.1 架构概述`: `architecture_views.summary`
- `3.2 各模块介绍`: fixed five visible columns: module name, responsibility, inputs, outputs, notes
- `3.3 模块关系图`: Mermaid block from `module_relationship_diagram.source`
- `3.4 补充架构图表`: `extra_tables` and `extra_diagrams`, or fixed empty state

`module_id` is not a visible table column in `3.2`, but it is used for support-data grouping after the table.

Chapter 4 renders one module subsection per `module_design.modules[]`, ordered by the chapter 3 module order. Each module subsection renders:

- `4.x.1 模块概述`: module summary
- `4.x.2 模块职责`: responsibilities
- `4.x.3 对外能力说明`: external capability summary prose
- `4.x.4 对外接口需求清单`: provided capabilities table
- `4.x.5 模块内部结构关系图`: Mermaid diagram when source exists, otherwise textual structure and not-applicable reason when present
- `4.x.6 补充说明`: extra tables, extra diagrams, notes, and support data

Chapter 5 renders:

- `5.1 运行时概述`: runtime summary
- `5.2 运行单元说明`: runtime units table
- `5.3 运行时流程图`: required Mermaid block
- `5.4 运行时序图（推荐）`: sequence diagram when non-empty, otherwise `未提供运行时序图。`
- `5.5 补充运行时图表`: extras or empty state

Chapter 6 renders:

- `6.1 配置项说明`: configuration table or `不适用。`
- `6.2 关键结构数据与产物`: data/artifact table or `未识别到需要在结构设计阶段单独说明的关键结构数据或产物。`
- `6.3 依赖项说明`: dependency table or `未识别到需要在结构设计阶段单独说明的外部依赖项。`
- `6.4 补充图表`: extras or empty state

Chapter 7 renders fixed subsections even in single-module mode:

- `7.1 协作关系概述`: summary or single-module empty explanation
- `7.2 跨模块协作说明`: collaboration table, or `本系统当前仅识别到一个结构模块，暂无跨模块协作关系。`
- `7.3 跨模块协作关系图`: Mermaid block or `未提供跨模块协作关系图。`
- `7.4 补充协作图表`: extras or empty state

Chapter 8 renders:

- `8.1 关键流程概述`: key flow summary
- `8.2 关键流程清单`: flow index table
- one detail subsection per flow, ordered by flow index rows
- `8.x.1 流程概述`: overview and related participants
- `8.x.2 步骤说明`: ordered step table or list
- `8.x.3 异常/分支说明`: branch/exception table or empty state
- `8.x.4 流程图`: required Mermaid block

Chapter 9 rendering is described below and completed with support-data sections in Phase 6.

## Tables

Fixed table columns are owned by renderer, not DSL instances.

Fixed table nodes contain `rows`.

Extra table nodes include `id`, `title`, `columns`, and `rows`.

Table cell escaping must handle:

- `|`
- newlines
- unsafe fenced-code markers
- raw HTML block injection

Fixed visible columns:

| DSL table | Visible columns |
| --- | --- |
| `architecture_views.module_intro` | 模块名称, 职责, 输入, 输出, 备注 |
| `provided_capabilities` | 能力名称, 接口风格, 描述, 输入, 输出, 备注 |
| `runtime_units` | 运行单元, 类型, 入口, 入口不适用原因, 职责, 关联模块, 外部环境原因, 备注 |
| `configuration_items` | 配置项, 来源, 使用方, 用途, 备注 |
| `structural_data_artifacts` | 数据/产物, 类型, 归属, 生产方, 消费方, 备注 |
| `dependencies` | 依赖项, 类型, 使用方, 用途, 备注 |
| `collaboration_scenarios` | 场景, 发起模块, 参与模块, 协作方式, 描述 |
| `flow_index` | 流程, 触发条件, 参与模块, 参与运行单元, 主要步骤, 输出结果, 备注 |

Metadata fields such as IDs, confidence, and refs are not visible table columns unless a chapter explicitly renders them as support notes after the table.

`escape_table_cell()` behavior:

- replace newlines with `<br>` or a deterministic safe equivalent
- escape `|`
- prevent fenced code markers from opening code blocks
- prevent raw HTML block injection

`escape_plain_text()` behavior:

- preserve ordinary prose and inline code where safe
- prevent leading heading markers from becoming headings
- prevent raw HTML blocks
- prevent fenced code injection outside source snippet rendering

## Mermaid Blocks

Renderer wraps diagram source in Markdown:

````markdown
```mermaid
flowchart TD
  A --> B
```
````

DSL source must not already contain fences.

Empty optional diagrams render fixed empty-state text and no Mermaid block.

Extra diagrams always render because they must have non-empty source.

Renderer must never trust DSL Mermaid source that already includes fences. That condition should fail validation, but renderer should still avoid double-fencing malformed input if defensive checks detect it.

After rendering, workflow runs:

```bash
python scripts/validate_mermaid.py --from-markdown <output-file> --static
```

This post-render check catches broken fences, empty Mermaid blocks, and renderer wrapping mistakes.

## Chapter 9

Renderer outputs:

- free-form `structure_issues_and_suggestions` when non-empty
- `风险` section when risks exist
- `假设` section when assumptions exist
- `低置信度项` section when whitelist-collected unknown-confidence items exist

It renders `未识别到明确的结构问题与改进建议。` only when all of those are empty.

If `structure_issues_and_suggestions` is empty but risks, assumptions, or low-confidence items exist, the renderer must not output the empty-state sentence. It renders the structured appended sections directly.

The renderer owns the `风险`, `假设`, and `低置信度项` headings. The free-form string must not create its own headings.

## generated_at

If `document.generated_at` is empty, renderer fills the rendered Markdown value but does not mutate the DSL file.

## Existing Output Handling

Default behavior:

- if the target output path exists, rendering fails
- no bytes are written to the existing file
- the error message says to use `--overwrite` or `--backup`

`--overwrite` behavior:

- replace the existing output file
- do not create a backup

`--backup` behavior:

- compute backup name as `<output_file>.bak-YYYYMMDD_HHMMSS`
- timestamp uses the local system clock when the script runs
- fail if that backup path already exists
- copy or move the existing file to the backup path before writing the new output
- never overwrite an existing backup

`--overwrite` and `--backup` are mutually exclusive.

## Tests

Phase 5 tests cover:

- output file naming and generic-name rejection
- overwrite default failure
- `--overwrite`
- `--backup`
- fixed chapter and section numbering
- empty optional sections do not shift numbering
- fixed table rendering
- table cell escaping
- Mermaid fence generation
- generated_at fill without DSL mutation
- rendered output passes `validate_mermaid.py --from-markdown <output-file> --static`

## Acceptance Criteria

- A semantically valid DSL renders to exactly one Markdown file.
- Output file handling is safe and deterministic.
- Fixed structure is stable across optional content differences.

## Out of Scope

- DSL semantic validation beyond defensive checks.
- Strict Mermaid CLI validation.
- Advanced support-data rendering beyond basic hooks, which is completed in Phase 6.
