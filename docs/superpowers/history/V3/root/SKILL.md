---
name: create-structure-md
description: Render and validate one human-first repository structure Markdown document from a prepared create-structure-md 0.3.0 manifest package.
---

# create-structure-md

Use this skill to render one human-first repository structure Markdown document from an already prepared 0.3.0 DSL package.

0.3.0 不兼容 0.2.0. The input is `structure.manifest.json`, not `structure.dsl.json`. JSON payloads do not carry `dsl_version`; the 0.3.0 contract is selected by the manifest name, validator, schemas, and renderer.

## Boundary

This skill renders and validates a prepared DSL package. Repository understanding happens before the DSL is finalized. For unfamiliar C repositories, use `repo-understand` before writing final child JSON, especially for Chapter 6 mechanism deep dives.

不要把分析过程写入 DSL.

The DSL stores accepted, renderable document content. It does not store raw repo-understand logs, subagent identities, command transcripts, or draft reasoning. If provenance is needed, keep it outside the manifest package until an explicit sidecar format exists.

## Input Shape

The main input file is `structure.manifest.json`. It is a fixed eight-key chapter directory:

- `document`
- `repository_overview`
- `directory_map`
- `module_layers`
- `repository_mainline`
- `key_mechanisms`
- `integration_boundaries`
- `risks_validation`

The rendered document uses 固定八章. Every value except `key_mechanisms` is one relative POSIX child JSON path. `key_mechanisms` is an array of direct Chapter 6 mechanism child JSON paths, such as `chapters/06-key-mechanisms/storage-flow.json`.

Chapter 6 is split directly in `key_mechanisms`. There is no aggregate `chapters/06-key-mechanisms.json` file.

## Workflow

1. Confirm the package root contains `structure.manifest.json` and child JSON files.
2. Run `python scripts/validate_structure.py <package>/structure.manifest.json`.
3. Fix diagnostics in the manifest or child JSON files.
4. Re-run `validate_structure` until validation succeeds.
5. Run `python scripts/render_markdown.py <package>/structure.manifest.json`.
6. Review the rendered Markdown with `references/review-checklist.md`.

The renderer writes `document.output_file` in the package root unless `--output` is supplied. An explicit `--output` path overrides `document.output_file`.

## References

- `references/dsl-spec.md`
- `references/document-structure.md`
- `references/mermaid-rules.md`
- `references/repo-understand-workflow.md`
- `references/review-checklist.md`
