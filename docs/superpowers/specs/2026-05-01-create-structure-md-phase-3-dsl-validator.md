# create-structure-md Phase 3 Spec: DSL Validator

## Goal

Implement `scripts/validate_dsl.py` semantic validation.

This phase turns structurally valid DSL JSON into document-ready structured content. It validates cross-references, required content, chapter-specific rules, metadata, snippets, Markdown safety, and structure-design boundaries.

## Dependencies

Depends on Phases 1 and 2.

Phase 3 assumes the schema exists and example DSL files pass schema validation.

## CLI Contract

```bash
python scripts/validate_dsl.py structure.dsl.json
python scripts/validate_dsl.py structure.dsl.json --allow-long-snippets
```

Rules:

- One positional DSL JSON path is required.
- Missing file fails.
- Invalid JSON fails.
- JSON Schema validation runs before semantic validation.
- `--allow-long-snippets` permits source snippets longer than 50 lines after warning.

## Core Validation

`validate_dsl.py` validates:

- Required top-level fields exist.
- `document.output_file` is safe, module- or system-specific, ends with `.md`, and is not generic-only.
- Authoritative field contract is internally consistent with chapter rules.
- Defining ID fields are unique within their required scope.
- Reference ID fields point to existing IDs.
- Paired `flow_id` values match one-to-one between flow index rows and flow detail objects.
- Unregistered `_id` or `_ids` fields fail validation.
- `confidence` is `observed`, `inferred`, or `unknown`.
- Chapter-specific required fields are non-empty.
- `flow_index.rows[]` is index-only and must not carry common metadata.

## Chapter Rules

Validator enforces:

- Chapter 2 summary and purpose are non-empty.
- Chapter 3 module introduction table exists and contains at least one module.
- Chapter 3 module relationship diagram exists and has non-empty source.
- Chapter 4 modules match Chapter 3 modules one-to-one.
- Chapter 4 module capabilities and internal structure are present.
- Chapter 5 runtime units are non-empty and runtime flow diagram is non-empty.
- Chapter 5 empty `entrypoint` requires `entrypoint_not_applicable_reason`.
- Chapter 5 empty `related_module_ids` requires `external_environment_reason`.
- Chapter 6 fixed tables may be empty.
- Chapter 7 collaboration rows and diagram are required only when module count is at least two.
- Chapter 8 flow index and flow detail nodes match one-to-one.
- Chapter 8 step IDs and branch IDs are globally unique in their collections.
- Chapter 9 Markdown string contains no headings, Mermaid blocks, tables, unbalanced fences, HTML blocks, or raw graph definitions.

## Traceability

Validator implements the traceability target mapping:

- `module`
- `core_capability`
- `provided_capability`
- `runtime_unit`
- `flow`
- `flow_step`
- `flow_branch`
- `collaboration`
- `configuration_item`
- `data_artifact`
- `dependency`
- `risk`
- `assumption`
- `source_snippet`

`traceability[].target_id` resolves according to `target_type`.

Local `traceability_refs` must point to traceability items targeting the current node.

## Source Snippets

Validator enforces:

- Required fields exist.
- `line_start` and `line_end` are positive integers.
- `line_end >= line_start`.
- Snippet longer than 20 lines warns.
- Snippet longer than 50 lines fails unless `--allow-long-snippets`.
- Every snippet is referenced by at least one `source_snippet_refs`.
- Obvious high-risk secret or personal-data patterns fail best-effort checks.

Validator must not apply prototype/detail-design lint to `source_snippets[].content`.

## Markdown Safety And Structure Boundary

Validator applies:

- Plain text Markdown injection checks.
- Mermaid source fence checks.
- Prototype/detail-design lint on normal design text and Chapter 9 text.

High-risk patterns fail outside snippets:

- C/C++ prototype-like lines.
- Python `def` or `class` definition-like lines.
- `typedef struct`
- `typedef enum`
- `enum { ... }`
- `class { ... }`
- large code-like blocks.

## Low-Confidence Collection

Validator or renderer support code collects `confidence: unknown` only from the whitelist:

- module intro rows
- module design nodes
- provided capability rows
- runtime unit rows
- Chapter 6 fixed table rows
- collaboration rows
- flow objects
- flow steps
- flow branches/exceptions

It excludes evidence, traceability, source snippets, risks, assumptions, and diagram nodes.

## Tests

Phase 3 tests cover:

- Schema validation runs first.
- Invalid references fail.
- Missing semantic content fails.
- Single-module Chapter 7 empty collaboration passes.
- Multi-module Chapter 7 empty collaboration fails.
- Flow and step identity rules.
- Source snippet length, references, and secret checks.
- Markdown injection and detailed-design lint.
- Low-confidence whitelist behavior.

## Acceptance Criteria

- `validate_dsl.py` rejects invalid DSL before rendering.
- Error messages include JSON path and concise correction hints.
- Examples pass semantic validation.

## Out of Scope

- Mermaid syntax validation.
- Markdown file generation.
- Rendering support data into Markdown.
