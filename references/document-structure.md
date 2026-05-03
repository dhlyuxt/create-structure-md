# create-structure-md Document Structure

## Fixed 9-Chapter Markdown Outline

The rendered document uses exactly nine fixed Chinese chapters. Optional content may render an empty-state sentence, but fixed section numbering must not shift.

1. 文档信息
2. 系统概览
3. 架构视图
   - 3.1 架构概述
   - 3.2 各模块介绍
   - 3.3 模块关系图
   - 3.4 补充架构图表
4. 模块设计
   - 4.x.1 模块概述
   - 4.x.2 模块职责
   - 4.x.3 对外能力说明
   - 4.x.4 对外接口需求清单
   - 4.x.5 模块内部结构关系图
   - 4.x.6 补充说明
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

## Output Filename Policy

The output is one module- or system-specific Markdown file named by `document.output_file`, normally `<documented-object-name>_STRUCTURE_DESIGN.md`. Generic-only filenames are forbidden, including `STRUCTURE_DESIGN.md`, `structure_design.md`, `design.md`, and `软件结构设计说明书.md`.

The renderer writes into the requested output directory and does not overwrite an existing output file by default. Use `--overwrite` only when replacing the existing Markdown is intended. Use `--backup` to preserve an existing file first; backup files use `<output_file>.bak-YYYYMMDD_HHMMSS`.

## Mermaid And Tables

Every non-empty DSL Mermaid source is rendered in exactly one Mermaid code fence. After rendering, run `validate_mermaid.py --from-markdown <output-file> --static` to validate the Markdown output.

Tables use fixed visible table columns for each section. IDs, confidence, evidence refs, traceability refs, and source snippet refs are hidden from normal tables. They may appear only in chapter 9 risks, assumptions, and low-confidence summaries where review traceability is the purpose.

Support data renders as compact notes near the relevant node or immediately after the relevant table. Fixed table rows keep fixed visible columns; evidence, traceability, and source snippet refs never become table cells. Extra table row evidence renders after the extra table using the first non-empty displayed row value as the support label; support metadata names are reserved and cannot be declared as extra table columns.

Chapter 6 empty tables render the documented empty-state sentences. Chapter 7 keeps sections 7.1 through 7.4 in single-module documents and renders the fixed collaboration absence text plus no-diagram text.
