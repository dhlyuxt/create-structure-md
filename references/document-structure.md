# create-structure-md Document Structure

## Fixed 9-Chapter Markdown Outline

The rendered document uses exactly nine fixed Chinese chapters. This is the fixed 9-chapter outline. Optional content may render an empty-state sentence, but fixed section numbering must not shift.

1. 文档信息
2. 系统概览
3. 架构视图
   - 3.1 架构概述
   - 3.2 各模块介绍
   - 3.3 模块关系图
   - 3.4 补充架构图表
4. 模块设计
   - 4.x.1 模块定位与源码/产物范围
   - 4.x.2 配置
   - 4.x.3 依赖
   - 4.x.4 数据对象
   - 4.x.5 对外接口
   - 4.x.6 实现机制说明
   - 4.x.7 已知限制
5. 运行时视图
   - 5.1 运行时概述
   - 5.2 运行单元说明
   - 5.3 运行时流程图
   - 5.4 运行时序图（推荐）
   - 5.5 补充运行时图表
6. 配置、数据与依赖关系
   - 6.1 配置项说明
   - 6.2 关键结构数据与产物
   - 6.3 依赖项说明
   - 6.4 补充图表
7. 跨模块协作关系
   - 7.1 协作关系概述
   - 7.2 跨模块协作说明
   - 7.3 跨模块协作关系图
   - 7.4 补充协作图表
8. 关键流程
   - 8.1 关键流程概述
   - 8.2 关键流程清单
   - 8.x 流程详情
9. 结构问题与改进建议

## Fixed Subchapter Numbering

Fixed subchapter numbering is part of the rendered contract. Chapters 1, 2, and 9 render as fixed top-level chapters. Chapters 3, 5, 6, and 7 keep their listed subchapters even when optional content is absent. Chapter 4 repeats the `4.x` module block for each module without renumbering inner module sections. Chapter 8 uses fixed 8.1 and 8.2 sections, then one `8.x` detail block per key flow.

## Chapter-By-Chapter Rendering Positions

Chapter 1 renders document metadata from `document`. Chapter 2 renders prepared system overview content. Chapter 3 renders architecture overview, module list, module relationship Mermaid, and supplemental architecture diagrams. Chapter 4 renders each module's V2 module model as seven fixed subsections: module positioning and source/output scope, configuration, dependencies, data objects, public interfaces, internal mechanism, and known limitations. Chapter 5 renders runtime overview, runtime units, runtime flow Mermaid, runtime sequence Mermaid, and supplemental runtime diagrams. Chapter 6 renders configuration items, structural data/artifacts, dependencies, and supplemental diagrams. Chapter 7 renders collaboration overview, collaboration rows, collaboration Mermaid, and supplemental diagrams. Chapter 8 renders flow overview, flow list, and per-flow details. Chapter 9 renders risks, assumptions, low-confidence summaries, and structure issues in a fixed order.

## Fixed Table Visible Columns

Fixed table visible columns are section-specific content columns only. IDs, confidence, evidence refs, traceability refs, source snippet refs, risk refs, and assumption refs are hidden from normal tables. They may appear only in chapter 9 review summaries when the purpose is review traceability.

Section 5.2 runtime units render these visible columns:

| 运行单元 | 类型 | 入口 | 职责 | 关联模块 | 备注 |
| --- | --- | --- | --- | --- | --- |

## Empty-State Sentences

Empty-state sentences are deterministic and section-specific. A section that is `empty_allowed` renders its documented empty-state sentence instead of disappearing. Chapter 6 empty configuration, data/artifact, and dependency tables use their fixed empty wording. Single-module chapter 7 documents keep 7.1 through 7.4 and render the fixed collaboration absence text plus no-diagram text.

## Table-Row Support-Data Placement

When `--evidence-mode inline` is used, table-row support-data placement happens immediately after the relevant table. Fixed table rows keep fixed visible columns; evidence, traceability, source snippets, confidence, risks, and assumptions never become table cells. Extra table row evidence renders after the extra table using the first non-empty displayed row value as the support label.

## Chapter 9 Rendering Behavior

Chapter 9 rendering behavior is review-oriented. Risks render under `9.1 风险清单`, assumptions render under `9.2 假设清单`, and low-confidence summaries render under `9.3 低置信度项目` only for design content that belongs in the whitelist. Evidence, traceability, source snippets, risks, assumptions, and Mermaid diagram nodes are excluded from the low-confidence summary whitelist.

## Chapter 9 Order

Chapter 9 renders in this fixed order:

1. `9.1 风险清单`
2. `9.2 假设清单`
3. `9.3 低置信度项目`
4. `9.4 结构问题与改进建议`

Section 9.4 renders `structure_issues_and_suggestions.summary` before the shared content blocks.

## Evidence Rendering Mode

Evidence support blocks are hidden by default in final Markdown. Use `python scripts/render_markdown.py structure.dsl.json --evidence-mode inline` only when final Markdown should preserve inline support-data blocks such as `支持数据（...）`.

## Output Filename Policy

The output is one module- or system-specific Markdown file named by `document.output_file`, normally `<documented-object-name>_STRUCTURE_DESIGN.md`. Generic-only filenames are forbidden, including `STRUCTURE_DESIGN.md`, `structure_design.md`, `design.md`, and `软件结构设计说明书.md`.

The renderer writes into the requested output directory and does not overwrite an existing output file by default. Use `--overwrite` only when replacing the existing Markdown is intended. Use `--backup` to preserve an existing file first; backup files use `<output_file>.bak-YYYYMMDD_HHMMSS`.

## Mermaid And Tables

Every non-empty DSL Mermaid source is rendered in exactly one Mermaid code fence. After rendering, run `validate_mermaid.py --from-markdown <output-file> --static` to validate the Markdown output.

Tables use fixed visible table columns for each section. IDs, confidence, evidence refs, traceability refs, and source snippet refs are hidden from normal tables. They may appear only in chapter 9 risks, assumptions, and low-confidence summaries where review traceability is the purpose.

When `--evidence-mode inline` is used, support data renders as compact notes near the relevant node or immediately after the relevant table. Fixed table rows keep fixed visible columns; evidence, traceability, and source snippet refs never become table cells. Extra table row evidence renders after the extra table using the first non-empty displayed row value as the support label; support metadata names are reserved and cannot be declared as extra table columns.

Chapter 6 empty tables render the documented empty-state sentences. Chapter 7 keeps sections 7.1 through 7.4 in single-module documents and renders the fixed collaboration absence text plus no-diagram text.
