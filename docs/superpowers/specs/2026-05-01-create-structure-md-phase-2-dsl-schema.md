# create-structure-md Phase 2 Spec: DSL Schema

## Goal

Implement the JSON Schema and authoritative DSL contracts for `create-structure-md`.

This phase makes the DSL structurally validatable. It defines top-level fields, fixed table row shapes, diagram object shapes, ID fields, output filename constraints, and example DSL files that pass schema validation.

## Dependencies

Depends on Phase 1.

Phase 2 assumes the skill skeleton, `requirements.txt`, schema path, examples path, and test harness already exist.

## Scope

Phase 2 owns:

- `schemas/structure-design.schema.json`.
- Schema-level definitions for all top-level DSL objects.
- Authoritative field contract.
- Defining/reference ID field contract.
- Diagram field policy.
- Output filename schema rules.
- Structurally valid example DSL files.

Semantic validation that requires cross-object knowledge belongs to Phase 3.

## Authoritative Field Contract

Schema and examples must align with the authoritative field contract from the full design spec.

Key rules:

- `document.output_file` is required, non-empty, safe, ends with `.md`, and is module- or system-specific.
- Generic-only output filenames are invalid, including `STRUCTURE_DESIGN.md`, `structure_design.md`, `design.md`, and `软件结构设计说明书.md`.
- `system_overview.summary`, `system_overview.purpose`, `architecture_views.summary`, `module_design.summary`, `runtime_view.summary`, and `key_flows.summary` are schema-present and semantically non-empty.
- `configuration_data_dependencies.summary` and `cross_module_collaboration.summary` are schema-present but may be empty.
- `runtime_sequence_diagram` is optional.
- `collaboration_relationship_diagram` is optional in schema because it is semantically required only in multi-module mode.

## ID Field Contract

Schema must make defining ID fields explicit.

Defining IDs include:

- `architecture_views.module_intro.rows[].module_id`
- `system_overview.core_capabilities[].capability_id`
- `module_design.modules[].external_capability_details.provided_capabilities.rows[].capability_id`
- `runtime_view.runtime_units.rows[].unit_id`
- `configuration_data_dependencies.configuration_items.rows[].config_id`
- `configuration_data_dependencies.structural_data_artifacts.rows[].artifact_id`
- `configuration_data_dependencies.dependencies.rows[].dependency_id`
- `cross_module_collaboration.collaboration_scenarios.rows[].collaboration_id`
- paired `key_flows.flow_index.rows[].flow_id` and `key_flows.flows[].flow_id`
- `key_flows.flows[].steps[].step_id`
- `key_flows.flows[].branches_or_exceptions[].branch_id`
- diagram `id`, extra table `id`, evidence `id`, traceability `id`, risk `id`, assumption `id`, source snippet `id`

Schema must reject unknown `_id` or `_ids` fields through `additionalProperties: false` unless explicitly modeled.

## Diagram Field Policy

Schema must represent diagrams consistently:

- Required diagram fields are full diagram objects.
- Optional diagram fields may be omitted or represented as full diagram objects.
- Empty object `{}` is invalid for all diagram fields.
- `extra_diagrams[]`, when present, must contain complete diagram objects.

Schema cannot enforce all source non-empty rules because some are semantic. Those checks are Phase 3.

## Extra Tables

Extra table nodes include:

- `id`
- `title`
- `columns`
- `rows`

Rows may contain only declared column keys plus `evidence_refs` in the MVP. `traceability_refs` and `source_snippet_refs` are not allowed for extra table rows.

## Additional Properties

Schema objects use `additionalProperties: false` by default.

Only explicitly documented extension points may allow additional keys. The MVP should avoid extension points unless they are necessary for extra table rows.

## Examples

Create structurally valid:

- `examples/minimal-from-code.dsl.json`
- `examples/minimal-from-requirements.dsl.json`

Examples must:

- Use a module- or system-specific `document.output_file`.
- Use all required top-level fields.
- Avoid validation policy fields such as `empty_allowed`, `required`, `min_rows`, or `render_when_empty`.
- Use Mermaid source strings that are syntactically plausible, but strict Mermaid validation is not required in this phase.

## Tests

Phase 2 tests cover:

- Schema file is valid JSON.
- Example DSL files pass JSON Schema validation.
- Unknown fields fail.
- Empty diagram object `{}` fails.
- Generic-only output filenames fail.
- Extra table rows reject `traceability_refs` and `source_snippet_refs`.
- `additionalProperties: false` is applied to normal schema objects.

## Acceptance Criteria

- Schema validates the example DSL files.
- Schema rejects malformed shapes before semantic validation is needed.
- The DSL shape no longer depends on ambiguous examples.

## Out of Scope

- Cross-reference validation.
- Semantic requiredness.
- Mermaid CLI or Mermaid static validation.
- Markdown rendering.
