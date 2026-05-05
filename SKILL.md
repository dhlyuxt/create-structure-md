---
name: create-structure-md
description: Use when the user asks Codex to generate a single module-specific software structure design document, such as <documented-object-name>_STRUCTURE_DESIGN.md, from already-prepared structured design content using the create-structure-md DSL and Mermaid diagrams. Do not use for repo analysis, requirements inference, multi-document generation, Word/PDF output, or image export.
---

# create-structure-md

Create one module- or system-specific Markdown file from already-prepared structured design content. The final file is a software structure design document rendered from the create-structure-md DSL with Mermaid diagrams.

## Boundary

This skill does not analyze repositories, infer requirements, generate multiple documents, produce Word/PDF files, or export images. Codex performs project or requirement understanding before invoking this skill. Do not run repository analysis tools as part of this skill.

## Input Readiness

Before creating DSL JSON, Codex must already have enough information to populate required sections without fabrication:

- module list and stable module IDs
- module scope
- module relationships
- Chapter 4 uses the V2 `module_design.modules[]` shape and renders seven fixed subsections: `4.x.1 模块定位与源码/产物范围`, `4.x.2 配置`, `4.x.3 依赖`, `4.x.4 数据对象`, `4.x.5 对外接口`, `4.x.6 实现机制说明`, and `4.x.7 已知限制`.
- Public function, method, library API, workflow, command-line, and contract interfaces belong under `public_interfaces`.
- public interfaces
- internal mechanisms
- reusable content-block sections use `blocks[]` with `block_type` values `text`, `diagram`, and `table`; every non-empty content-block section includes at least one text block.
- `structure_issues_and_suggestions` is a Phase 3 object with `summary`, `blocks`, and `not_applicable_reason`, not a free-form Markdown string.
- Chapter 9 renders risks, assumptions, low-confidence items, then structure issues in the fixed `9.1` through `9.4` order.
- Section 5.2 runtime units use visible columns `运行单元 | 类型 | 入口 | 职责 | 关联模块 | 备注`; if no concrete entrypoint exists, set `entrypoint: "不适用"` and put the reason in `notes`.
- runtime units and runtime flow
- configuration, structural data/artifact, and dependency information when applicable
- cross-module collaboration scenarios when more than one module is identified
- key flows and one diagram concept per key flow
- confidence values and support-data references where the schema requires or allows them
- evidence references or source snippets when available and safe to disclose

If any required input is missing, stop and perform project or requirement understanding outside this skill before creating DSL JSON.

## Workflow

1. Create a temporary work directory.
2. Read references/dsl-spec.md before writing DSL content.
3. Write one complete DSL JSON file at `<temporary-work-directory>/structure.dsl.json`.
4. Run `python scripts/validate_dsl.py <temporary-work-directory>/structure.dsl.json`.
5. Read references/mermaid-rules.md before creating/revising Mermaid.
6. Dispatch an independent Mermaid readability review subagent. Review every expected Mermaid diagram for readability. Save the JSON artifact as `<temporary-work-directory>/mermaid-readability-review.json`. Write `<temporary-work-directory>/mermaid-readability-review.json`.
7. Run `python scripts/verify_v2_mermaid_gates.py <temporary-work-directory>/structure.dsl.json --mermaid-review-artifact <temporary-work-directory>/mermaid-readability-review.json --pre-render --work-dir <temporary-work-directory>/mermaid`.
8. Render exactly one document with `python scripts/render_markdown.py <temporary-work-directory>/structure.dsl.json --output-dir <output-dir>`. Evidence support blocks are hidden by default; use `--evidence-mode inline` only when the user explicitly asks to preserve inline support data in final Markdown.
9. Run `python scripts/verify_v2_mermaid_gates.py <temporary-work-directory>/structure.dsl.json --mermaid-review-artifact <temporary-work-directory>/mermaid-readability-review.json --rendered-markdown <output-file> --post-render --work-dir <temporary-work-directory>/mermaid`.
10. Review with references/review-checklist.md.
11. Report output path, temporary work directory, assumptions, low-confidence items, and Mermaid gate results. Mermaid gate results include the Mermaid readability artifact path, rendered diagram completeness status, and strict rendered Markdown validation status.

Strict Mermaid validation is the default. The Mermaid readability artifact is workflow metadata. Do not store it inside DSL JSON and do not render it into final Markdown. The artifact `source_dsl` value must identify the same DSL path passed to `verify_v2_mermaid_gates.py`; prefer `<temporary-work-directory>/structure.dsl.json` or an absolute path. Every rendered Mermaid fence must have an adjacent `<!-- diagram-id: ... -->` comment immediately before the fence. Static-only Mermaid validation is not final acceptance for V2 Phase 4.

## Output And Temporary Files

Final output is one Markdown file named by document.output_file. If the user provides an output directory, write document.output_file there. Otherwise write document.output_file to the target repository root, or to the current working directory when no target repository root is known.

The output file must be module- or system-specific, normally <documented-object-name>_STRUCTURE_DESIGN.md. Generic-only filenames are forbidden, including STRUCTURE_DESIGN.md, structure_design.md, design.md, and 软件结构设计说明书.md. The output filename must end with .md, must not contain path separators, must not contain .., and must not contain control characters. Spaces in the output filename should already be normalized to _ before writing document.output_file.

Preferred temporary work directory: <workspace>/.codex-tmp/create-structure-md-<run-id>/. Fallback temporary work directory: /tmp/create-structure-md-<run-id>. Temporary files in the skill working directory are not automatically deleted. If cleanup is needed, give the cleanup command to the user instead of deleting files.

The workspace .gitignore should include .codex-tmp/ unless the user intentionally versions temporary artifacts. Codex must not edit .gitignore automatically unless the user asks it to.

## References

- `references/dsl-spec.md`
- `references/document-structure.md`
- `references/mermaid-rules.md`
- `references/review-checklist.md`
