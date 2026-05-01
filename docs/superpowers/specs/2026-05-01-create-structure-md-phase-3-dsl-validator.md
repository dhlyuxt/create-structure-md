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

## Failure, Warning, And Stop Policy

Semantic validation failures stop rendering. Warnings do not stop rendering, but must be visible in command output so Codex can include them in the final report when useful.

Failures include:

- invalid JSON or schema failure
- unsafe or generic-only `document.output_file`
- missing required chapter content
- invalid ID prefix or duplicate ID
- invalid internal reference
- invalid traceability target
- conflicting local traceability backlink
- unregistered `_id` or `_ids` field
- validation policy field in DSL JSON
- source snippet with unredacted obvious high-risk secret pattern
- unreferenced source snippet
- prototype/detail-design lint violation outside allowed fields

Warnings include:

- unreferenced `evidence[]`
- source snippet longer than 20 lines and up to 50 lines
- module relationship diagram that does not mention every listed module ID or module name
- `output_file` containing spaces; Codex should normalize spaces to `_` before writing the final DSL

If Codex lacks enough content for a field that is allowed to be empty, it should use the documented empty representation. If Codex lacks enough content for a required non-empty field, validation fails and Codex must revise the structured design content rather than fabricate filler.

## Document And Output Validation

`validate_dsl.py` validates `document` rules before chapter rules:

- `title`, `project_name`, `document_version`, `status`, `language`, `source_type`, and `output_file` are non-empty.
- `status` is `draft`, `reviewed`, or `final`.
- `source_type` is `code`, `requirements`, `mixed`, or `notes`.
- `generated_at`, when present, is treated as user-provided text and should follow ISO-8601 local datetime with timezone when available. The validator may warn rather than fail for format looseness.
- `output_file` ends with `.md`.
- `output_file` contains no `/`, `\`, `..`, or control characters.
- Spaces in `output_file` should produce a validation warning recommending normalization to `_`; the renderer writes exactly `document.output_file` rather than silently renaming it.
- Generic-only names fail: `STRUCTURE_DESIGN.md`, `structure_design.md`, `design.md`, and `软件结构设计说明书.md`.
- The filename must include a concrete documented object name such as a module, subsystem, system, package, or tool name. A generic prefix alone is invalid.

## ID And Reference Validation

Defining IDs:

| Field | Scope |
| --- | --- |
| `architecture_views.module_intro.rows[].module_id` | canonical module IDs |
| `system_overview.core_capabilities[].capability_id` | capability IDs |
| `module_design.modules[].external_capability_details.provided_capabilities.rows[].capability_id` | capability IDs |
| `runtime_view.runtime_units.rows[].unit_id` | runtime unit IDs |
| `configuration_data_dependencies.configuration_items.rows[].config_id` | configuration item IDs |
| `configuration_data_dependencies.structural_data_artifacts.rows[].artifact_id` | data/artifact IDs |
| `configuration_data_dependencies.dependencies.rows[].dependency_id` | dependency IDs |
| `cross_module_collaboration.collaboration_scenarios.rows[].collaboration_id` | collaboration IDs |
| `key_flows.flow_index.rows[].flow_id` and `key_flows.flows[].flow_id` | paired flow identity |
| `key_flows.flows[].steps[].step_id` | global flow step IDs |
| `key_flows.flows[].branches_or_exceptions[].branch_id` | global branch/exception IDs |
| diagram `id` fields | Mermaid diagram IDs |
| `extra_tables[].id` | extra table IDs |
| `evidence[].id` | evidence IDs |
| `traceability[].id` | traceability IDs |
| `risks[].id` | risk IDs |
| `assumptions[].id` | assumption IDs |
| `source_snippets[].id` | source snippet IDs |

Required prefix checks:

- `MOD-` for modules
- `CAP-` for capabilities
- `RUN-` for runtime units
- `CFG-` for configuration items
- `DATA-` for structural data/artifacts
- `DEP-` for dependencies
- `COL-` for collaborations
- `FLOW-` for flows
- `STEP-` for flow steps
- `BR-` for branches/exceptions
- `MER-` for Mermaid diagrams
- `TBL-` for extra tables
- `EV-` for evidence
- `TR-` for traceability
- `RISK-` for risks
- `ASM-` for assumptions
- `SNIP-` for snippets

The validator does not require a strict numeric suffix. Both `MOD-001` and `MOD-RENDER-001` are valid when unique.

Reference validation:

- `module_design.modules[].module_id` references canonical module IDs and must match them one-to-one.
- Runtime unit `related_module_ids` reference module IDs.
- Collaboration `initiator_module_id` and `participant_module_ids` reference module IDs.
- Flow participant and related module/runtime unit fields reference existing IDs.
- All `evidence_refs`, `traceability_refs`, and `source_snippet_refs` reference existing support-data IDs.
- `traceability[].source_external_id` is not an internal reference.
- Any unregistered `_id` or `_ids` field fails validation.

## Chapter-Specific Non-Empty Rules

Chapter 2:

- `system_overview.summary` and `system_overview.purpose` are non-empty.
- Every core capability has non-empty `capability_id`, `name`, `description`, and `confidence`.

Chapter 3:

- `architecture_views.summary` is non-empty.
- `module_intro.rows` has at least one row.
- Every module row has non-empty `module_id`, `module_name`, `responsibility`, and `confidence`.
- `module_relationship_diagram.source` is non-empty.
- The validator warns, not fails, when a module ID or name does not appear in the module relationship diagram source.

Chapter 4:

- `module_design.summary` is non-empty.
- Every chapter 3 module has exactly one matching `module_design.modules[]` entry.
- Every module has non-empty `module_id`, `name`, `summary`, `confidence`, and at least one responsibility.
- `external_capability_summary.description` is non-empty.
- `provided_capabilities.rows` has at least one row.
- Every provided capability row has non-empty `capability_id`, `capability_name`, `description`, and `confidence`.
- `internal_structure.summary` is non-empty.
- A module passes internal structure validation when either `internal_structure.diagram.source` is non-empty or `internal_structure.textual_structure` is non-empty.
- `internal_structure.not_applicable_reason` may explain absence of a diagram but does not by itself satisfy the internal structure rule.

Chapter 5:

- `runtime_view.summary` is non-empty.
- `runtime_units.rows` has at least one row.
- Every runtime unit has non-empty `unit_id`, `unit_name`, `unit_type`, `responsibility`, and `confidence`.
- Empty `entrypoint` requires non-empty `entrypoint_not_applicable_reason`.
- Empty `related_module_ids` requires non-empty `external_environment_reason`.
- Non-empty `related_module_ids` entries reference existing modules.
- `runtime_flow_diagram.source` is non-empty.
- `runtime_sequence_diagram`, when present with non-empty source, uses `sequenceDiagram`.

Chapter 6:

- `configuration_items.rows`, `structural_data_artifacts.rows`, and `dependencies.rows` may be empty.
- Non-empty configuration rows require `config_id`, `config_name`, `purpose`, and `confidence`.
- Non-empty structural data/artifact rows require `artifact_id`, `artifact_name`, `artifact_type`, `owner`, and `confidence`.
- Non-empty dependency rows require `dependency_id`, `dependency_name`, `dependency_type`, `purpose`, and `confidence`.
- Display fields such as `used_by`, `owner`, `producer`, and `consumer` are not treated as references.

Chapter 7:

- Single-module mode allows empty collaboration rows and omitted or empty collaboration diagram.
- Single-module mode allows `cross_module_collaboration.summary` to be empty.
- Multi-module mode requires a non-empty `cross_module_collaboration.summary` describing the collaboration scope.
- Multi-module mode requires at least one collaboration row and non-empty collaboration diagram source.
- In multi-module mode, every row has non-empty `collaboration_id`, `scenario`, `initiator_module_id`, `participant_module_ids`, `collaboration_method`, `description`, and `confidence`.
- In multi-module mode, each row involves at least two distinct modules.

Chapter 8:

- `key_flows.summary` is non-empty.
- `flow_index.rows` has at least one row.
- Every flow index row has non-empty `flow_id`, `flow_name`, `trigger_condition`, `main_steps`, and `output_result`.
- Every flow index row has at least one participant through module IDs or runtime unit IDs.
- `flow_index.rows[]` must not carry common metadata.
- Flow index rows and flow detail objects match one-to-one by `flow_id`.
- Every flow has non-empty `name`, `overview`, `confidence`, and `steps`.
- Every step has non-empty `step_id`, integer `order >= 1`, non-empty `description`, and `confidence`.
- Step `order` values are unique within one flow.
- `step_id` values are globally unique across all flows.
- Branch/exception items are optional; when present, each has non-empty `branch_id`, `condition`, `handling`, and `confidence`.
- `branch_id` values are globally unique across all flows.
- Every flow has a diagram with non-empty source.

Chapter 9:

- The field is a string and may be empty.
- It may contain paragraphs, unordered lists, ordered lists, emphasis, and inline code.
- It must not contain headings, Mermaid blocks, Markdown tables, unbalanced fenced code blocks, HTML blocks, embedded diagrams, raw graph definitions, or structured table/diagram objects.

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

Target mapping:

| target_type | target_id resolves to |
| --- | --- |
| `module` | `architecture_views.module_intro.rows[].module_id` |
| `core_capability` | `system_overview.core_capabilities[].capability_id` |
| `provided_capability` | provided capability row `capability_id` |
| `runtime_unit` | `runtime_view.runtime_units.rows[].unit_id` |
| `flow` | `key_flows.flows[].flow_id` |
| `flow_step` | `key_flows.flows[].steps[].step_id` |
| `flow_branch` | `key_flows.flows[].branches_or_exceptions[].branch_id` |
| `collaboration` | `cross_module_collaboration.collaboration_scenarios.rows[].collaboration_id` |
| `configuration_item` | `configuration_data_dependencies.configuration_items.rows[].config_id` |
| `data_artifact` | `configuration_data_dependencies.structural_data_artifacts.rows[].artifact_id` |
| `dependency` | `configuration_data_dependencies.dependencies.rows[].dependency_id` |
| `risk` | `risks[].id` |
| `assumption` | `assumptions[].id` |
| `source_snippet` | `source_snippets[].id` |

Traceability validation must use authoritative binding first: `traceability[].target_type` plus `traceability[].target_id`. Local backlinks are optional. If a local backlink points to a traceability entry targeting another object, validation fails.

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

Plain text fields are all DSL string fields except:

- fields ending with `_markdown`
- `structure_issues_and_suggestions`
- Mermaid diagram `source`
- `source_snippets[].content`

Plain text fields must not inject top-level or subsection headings, Markdown tables, Mermaid fences, unbalanced fences, or raw HTML blocks. Table-cell escaping is implemented by the renderer, but validator should reject high-risk content that would break document structure.

## Diagram Requiredness Boundary

`validate_dsl.py` decides whether a diagram source is required. `validate_mermaid.py` decides whether non-empty Mermaid source is syntactically valid.

Semantic rules:

- Required diagrams with empty source fail here.
- Optional diagrams with empty source pass here only when their chapter rule allows absence.
- `extra_diagrams[]` items fail here when source is empty.
- Empty object `{}` for any diagram should already fail schema validation.
- Diagram semantic coverage is limited to warnings in MVP; the validator does not prove edges match real module, runtime, collaboration, or flow relationships.

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
