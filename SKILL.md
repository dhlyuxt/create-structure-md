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
- module responsibilities
- module relationships
- module-level external capabilities or interface requirements
- module internal structure information
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
3. Write one complete DSL JSON file.
4. Run `python scripts/validate_dsl.py structure.dsl.json`.
5. Read references/mermaid-rules.md before creating/revising Mermaid.
6. Run `python scripts/validate_mermaid.py --from-dsl structure.dsl.json --strict --work-dir <temporary-work-directory>/mermaid`.
7. Render exactly one document with `python scripts/render_markdown.py structure.dsl.json --output-dir <output-dir>`.
8. Run `python scripts/validate_mermaid.py --from-markdown <output-file> --static`.
9. Review with references/review-checklist.md.
10. Report output path, temporary work directory, assumptions, low-confidence items, and static-only Mermaid acceptance.

Strict Mermaid validation is the default. If local Mermaid CLI tooling unavailable, stop and ask user before static-only validation. A final report that relies on static-only validation must say Mermaid diagrams were not proven renderable by Mermaid CLI, tooling unavailable, and user explicitly accepts static-only validation.

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
