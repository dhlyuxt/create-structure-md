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

## Schema Version And Top-Level Fields

The schema validates `dsl_version` as a required non-empty string. The MVP example value is `0.1.0`.

Top-level required fields:

- `dsl_version`
- `document`
- `system_overview`
- `architecture_views`
- `module_design`
- `runtime_view`
- `configuration_data_dependencies`
- `cross_module_collaboration`
- `key_flows`
- `structure_issues_and_suggestions`
- `evidence`
- `traceability`
- `risks`
- `assumptions`
- `source_snippets`

The schema must reject generic wrappers such as `required_tables`, `required_diagrams`, `recommended_diagrams`, and validation policy fields such as `empty_allowed`, `required`, `min_rows`, `max_rows`, or `render_when_empty`.

## Common Definitions

Common metadata object, when allowed:

```json
{
  "confidence": "observed",
  "evidence_refs": [],
  "traceability_refs": [],
  "source_snippet_refs": []
}
```

Schema rules:

- `confidence` enum: `observed`, `inferred`, `unknown`.
- `evidence_refs`, `traceability_refs`, and `source_snippet_refs` are arrays of non-empty strings.
- Common metadata is not automatically allowed everywhere; each object schema must explicitly include the allowed metadata fields.
- `notes` arrays contain non-empty plain-text strings when the object-level field is an array.
- Fixed table row `notes` fields are plain-text strings.
- `responsibilities` is an array of non-empty plain-text strings.

## Document Object

`document` required fields:

- `title`
- `project_name`
- `project_version`
- `document_version`
- `status`
- `generated_at`
- `generated_by`
- `language`
- `source_type`
- `scope_summary`
- `not_applicable_policy`
- `output_file`

Schema-level enums:

- `status`: `draft`, `reviewed`, `final`
- `source_type`: `code`, `requirements`, `mixed`, `notes`

Schema-level string rules:

- `title`, `project_name`, `document_version`, `status`, `language`, `source_type`, and `output_file` are non-empty.
- `generated_at` may be empty because the renderer can fill the rendered value.
- `output_file` ends with `.md`.
- `output_file` does not contain `/`, `\`, `..`, or control characters.

Semantic filename specificity is Phase 3, but Phase 2 schema examples must already use concrete names such as `create-structure-md_STRUCTURE_DESIGN.md`.

## Chapter 2 Schema: system_overview

`system_overview` required fields:

- `summary`
- `purpose`
- `core_capabilities`
- `notes`

`core_capabilities[]` object fields:

- `capability_id`
- `name`
- `description`
- `confidence`

The schema requires all four fields and the `confidence` enum. Non-empty semantics for `summary`, `purpose`, `name`, and `description` are also represented where JSON Schema can express them without cross-object logic.

## Chapter 3 Schema: architecture_views

`architecture_views` required fields:

- `summary`
- `notes`
- `module_intro`
- `module_relationship_diagram`
- `extra_tables`
- `extra_diagrams`

`module_intro` contains only:

- `rows`

`module_intro.rows[]` fields:

- `module_id`
- `module_name`
- `responsibility`
- `inputs`
- `outputs`
- `notes`
- `confidence`
- `evidence_refs`
- `traceability_refs`
- `source_snippet_refs`

The schema must not allow `id`, `title`, or `columns` under fixed table nodes.

`module_relationship_diagram` is a required full diagram object. Schema can require the full object shape; Phase 3 enforces non-empty `source`.

## Chapter 4 Schema: module_design

`module_design` required fields:

- `summary`
- `notes`
- `modules`

`modules[]` fields:

- `module_id`
- `name`
- `summary`
- `responsibilities`
- `external_capability_summary`
- `external_capability_details`
- `internal_structure`
- `extra_tables`
- `extra_diagrams`
- `evidence_refs`
- `traceability_refs`
- `source_snippet_refs`
- `notes`
- `confidence`

`module_design.modules[].module_id` is a reference field in semantic validation, not a new canonical module definition.

`external_capability_summary` fields:

- `description`
- `consumers`
- `interface_style`
- `boundary_notes`

`consumers` and `boundary_notes` are arrays of non-empty plain-text strings.

`external_capability_details` fields:

- `provided_capabilities`
- `extra_tables`
- `extra_diagrams`

`provided_capabilities` contains only `rows`.

`provided_capabilities.rows[]` fields:

- `capability_id`
- `capability_name`
- `interface_style`
- `description`
- `inputs`
- `outputs`
- `notes`
- `confidence`
- `evidence_refs`
- `traceability_refs`
- `source_snippet_refs`

`internal_structure` fields:

- `summary`
- `diagram`
- `textual_structure`
- `not_applicable_reason`

The `diagram` field is present as a full diagram object. Its `source` may be empty at schema level because Phase 3 allows textual internal structure as the alternative.

## Chapter 5 Schema: runtime_view

`runtime_view` required fields:

- `summary`
- `notes`
- `runtime_units`
- `runtime_flow_diagram`
- `extra_tables`
- `extra_diagrams`

`runtime_sequence_diagram` is optional. If present, it must be a full diagram object and must not be `{}`.

`runtime_units` contains only `rows`.

`runtime_units.rows[]` fields:

- `unit_id`
- `unit_name`
- `unit_type`
- `entrypoint`
- `entrypoint_not_applicable_reason`
- `responsibility`
- `related_module_ids`
- `external_environment_reason`
- `notes`
- `confidence`
- `evidence_refs`
- `traceability_refs`
- `source_snippet_refs`

`related_module_ids` is an array of non-empty strings. Reference resolution is Phase 3.

## Chapter 6 Schema: configuration_data_dependencies

`configuration_data_dependencies` required fields:

- `summary`
- `notes`
- `configuration_items`
- `structural_data_artifacts`
- `dependencies`
- `extra_tables`
- `extra_diagrams`

All three fixed table nodes contain only `rows`; their rows may be empty arrays.

`configuration_items.rows[]` fields:

- `config_id`
- `config_name`
- `source`
- `used_by`
- `purpose`
- `notes`
- `confidence`
- `evidence_refs`
- `traceability_refs`
- `source_snippet_refs`

`structural_data_artifacts.rows[]` fields:

- `artifact_id`
- `artifact_name`
- `artifact_type`
- `owner`
- `producer`
- `consumer`
- `notes`
- `confidence`
- `evidence_refs`
- `traceability_refs`
- `source_snippet_refs`

`dependencies.rows[]` fields:

- `dependency_id`
- `dependency_name`
- `dependency_type`
- `used_by`
- `purpose`
- `notes`
- `confidence`
- `evidence_refs`
- `traceability_refs`
- `source_snippet_refs`

Display fields such as `used_by`, `owner`, `producer`, and `consumer` are plain text, not schema-level references.

## Chapter 7 Schema: cross_module_collaboration

`cross_module_collaboration` required fields:

- `summary`
- `notes`
- `collaboration_scenarios`
- `extra_tables`
- `extra_diagrams`

`collaboration_relationship_diagram` is optional in schema because it is required only when the module count is at least two. If present, it must be a full diagram object and must not be `{}`.

`collaboration_scenarios` contains only `rows`.

`collaboration_scenarios.rows[]` fields:

- `collaboration_id`
- `scenario`
- `initiator_module_id`
- `participant_module_ids`
- `collaboration_method`
- `description`
- `confidence`
- `evidence_refs`
- `traceability_refs`
- `source_snippet_refs`

`participant_module_ids` is an array of non-empty strings. Multi-module semantics are Phase 3.

## Chapter 8 Schema: key_flows

`key_flows` required fields:

- `summary`
- `notes`
- `flow_index`
- `flows`
- `extra_tables`
- `extra_diagrams`

`flow_index` contains only `rows`.

`flow_index.rows[]` fields:

- `flow_id`
- `flow_name`
- `trigger_condition`
- `participant_module_ids`
- `participant_runtime_unit_ids`
- `main_steps`
- `output_result`
- `notes`

`flow_index.rows[]` is index-only. The schema must reject common metadata fields on these rows.

`flows[]` fields:

- `flow_id`
- `name`
- `overview`
- `steps`
- `branches_or_exceptions`
- `related_module_ids`
- `related_runtime_unit_ids`
- `confidence`
- `evidence_refs`
- `traceability_refs`
- `source_snippet_refs`
- `diagram`

`steps[]` fields:

- `step_id`
- `order`
- `description`
- `actor`
- `related_module_ids`
- `related_runtime_unit_ids`
- `input`
- `output`
- `confidence`
- `evidence_refs`
- `traceability_refs`
- `source_snippet_refs`

`order` is an integer with minimum `1`.

`branches_or_exceptions[]` fields:

- `branch_id`
- `condition`
- `handling`
- `related_module_ids`
- `related_runtime_unit_ids`
- `confidence`
- `evidence_refs`
- `traceability_refs`
- `source_snippet_refs`

Every `flows[].diagram` is a full diagram object. Phase 3 enforces non-empty source.

## Chapter 9 Schema

`structure_issues_and_suggestions` is a required string. It may be empty. Markdown restrictions are semantic validation and renderer concerns, not JSON Schema concerns beyond type.

## Support Data Schemas

`evidence[]` fields:

- `id`
- `kind`
- `title`
- `location`
- `description`
- `confidence`

`evidence[].kind` enum: `source`, `requirement`, `note`, `analysis`.

`traceability[]` fields:

- `id`
- `source_external_id`
- `source_type`
- `target_type`
- `target_id`
- `description`

`traceability[].source_type` enum: `requirement`, `note`, `code`, `user_input`.

`traceability[].target_type` enum:

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

`risks[]` fields:

- `id`
- `description`
- `impact`
- `mitigation`
- `confidence`
- `evidence_refs`
- `traceability_refs`
- `source_snippet_refs`

`assumptions[]` fields:

- `id`
- `description`
- `rationale`
- `validation_suggestion`
- `confidence`
- `evidence_refs`
- `traceability_refs`
- `source_snippet_refs`

`source_snippets[]` fields:

- `id`
- `path`
- `line_start`
- `line_end`
- `language`
- `purpose`
- `content`
- `confidence`

`line_start` and `line_end` are positive integers. The ordering check is Phase 3.

## Examples

Create structurally valid:

- `examples/minimal-from-code.dsl.json`
- `examples/minimal-from-requirements.dsl.json`

Examples must:

- Use a module- or system-specific `document.output_file`.
- Use all required top-level fields.
- Avoid validation policy fields such as `empty_allowed`, `required`, `min_rows`, or `render_when_empty`.
- Use Mermaid source strings that are syntactically plausible, but strict Mermaid validation is not required in this phase.
- Include every required fixed table node, even when its `rows` array is empty by chapter rule.
- Omit optional diagrams or provide full diagram objects; never use `{}`.
- Include at least one module, one runtime unit, and one key flow so later phases can tighten semantic validation without replacing the examples wholesale.

## Tests

Phase 2 tests cover:

- Schema file is valid JSON.
- Example DSL files pass JSON Schema validation.
- Unknown fields fail.
- Empty diagram object `{}` fails.
- Generic-only output filenames fail.
- Extra table rows reject `traceability_refs` and `source_snippet_refs`.
- `additionalProperties: false` is applied to normal schema objects.
- Fixed table nodes reject `columns`.
- `flow_index.rows[]` rejects common metadata fields.
- Optional diagram fields reject `{}` but allow omission.
- Support data objects reject unknown fields.
- Source snippet line numbers reject non-integers and integers below `1`.

## Acceptance Criteria

- Schema validates the example DSL files.
- Schema rejects malformed shapes before semantic validation is needed.
- The DSL shape no longer depends on ambiguous examples.
- Every field needed by the renderer is represented in schema.
- Every field ending with `_id` or `_ids` is either a modeled defining field, a modeled reference field, or rejected as unknown.

## Out of Scope

- Cross-reference validation.
- Semantic requiredness.
- Mermaid CLI or Mermaid static validation.
- Markdown rendering.
