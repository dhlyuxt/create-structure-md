# create-structure-md V2 Phase 1: Foundation and Global Rules

## Summary

This phase establishes the V2 contract before any detailed Chapter 4, Chapter 9, renderer, or Mermaid work proceeds.

The root design remains `docs/superpowers/specs/2026-05-04-create-structure-md-v2-design.md`. This phase spec extracts the global invariants that every later phase must obey.

## Goals

- Make V2 a clear breaking DSL shape change.
- Keep create-structure-md separate from repository analysis.
- Move evidence rendering policy to renderer CLI options.
- Define global ID, enum, not-applicable, and error-reporting rules.
- Prevent compatibility ambiguity before implementation starts.

## Non-Goals

- Do not implement repository analysis.
- Do not implement a V1-to-V2 migration tool.
- Do not add evidence appendix mode.
- Do not generate Word, PDF, image exports, or multiple output documents.
- Do not modify Mermaid validator or Mermaid rules files.
- Do not render Chapter 4, Chapter 9, or Mermaid completeness behavior in this phase except where needed by global contracts.

## Product Boundary

The skill continues to consume prepared structured content:

```text
repo-analysis skill or human analysis -> structure DSL -> create-structure-md -> Markdown
```

`SKILL.md` must continue to state that create-structure-md does not analyze repositories, infer missing requirements, or invent missing design content from source code. V2 improves the DSL and renderer for structure already supplied by another actor.

## DSL Version Contract

V2 is a breaking DSL shape change.

- The only supported DSL version is `0.2.0`.
- The V2 schema, validator, renderer, examples, and acceptance tests target `0.2.0`.
- Any input with a different `dsl_version` fails before rendering.
- The failure message must say that V1 DSL is not supported by the V2 renderer and that the input must be migrated to `0.2.0`.
- This phase does not implement the migration tool.
- Legacy V1 examples may remain only as rejected fixtures.

## Evidence Rendering Contract

Evidence rendering is a renderer policy, not DSL document content.

The renderer must support:

| Mode | Behavior |
| --- | --- |
| `hidden` | Default. Suppress rendered evidence support blocks such as `支持数据（...）`. |
| `inline` | Preserve V1-style inline support-data rendering near referencing content. |

`appendix` mode is not supported.

Renderer CLI shape:

```text
python3 scripts/render_markdown.py structure.dsl.json --evidence-mode hidden
python3 scripts/render_markdown.py structure.dsl.json --evidence-mode inline
```

If `--evidence-mode` is absent, the renderer defaults to `hidden`.

Hidden mode suppresses rendered evidence, traceability, source snippet blocks, table-row support groups, and content-block support refs. It does not hide normal structural facts such as file paths, function names, prototypes, parameters, return values, configuration values, dependency names, data object names, limitations, or Mermaid diagrams.

DSL fields such as `evidence_refs`, `traceability_refs`, and `source_snippet_refs` remain available for validation and upstream tooling.

## Global ID Scope Rules

- `block_id` is unique within its parent content-block section.
- Mermaid `diagram.id` is globally unique across the DSL document.
- Table `table.id` is globally unique across the DSL document.
- `module_id`, `interface_id`, `parameter_id`, `data_id`, `dependency_id`, and `limitation_id` are globally unique within their own ID type.
- `dependency_id` is globally unique across both Chapter 4 module dependencies and Chapter 6 system dependencies.
- Module dependency IDs should use an `MDEP-...` prefix.
- Chapter 6 system dependency IDs should use a `SYSDEP-...` prefix.
- Use `system_dependency_ref` to connect a module dependency to a system dependency instead of reusing the same `dependency_id`.
- Existing V1 support IDs keep their V1 global/type scope rules.

Validation errors must include a JSON path and a stable ID when the item has an ID. For nested content block objects, report the nearest containing `block_id` plus nested `diagram.id` or `table.id` when present.

## Global Enums

Phase-specific specs may add field-level constraints, but these enum values are globally reserved by V2.

`module_kind`:

- `documentation_contract`
- `schema_contract`
- `validator`
- `renderer`
- `installer`
- `test_suite`
- `library`
- `other`

`value_source`:

- `default`
- `cli_argument`
- `environment`
- `constant`
- `config_file`
- `computed`
- `inferred`
- `unknown`

`dependency_type`:

- `runtime`
- `library`
- `tool`
- `schema_contract`
- `documentation_contract`
- `dsl_contract`
- `internal_module`
- `data_object`
- `filesystem`
- `external_service`
- `test_fixture`
- `other`

`usage_relation`:

- `reads`
- `writes`
- `validates_against`
- `renders`
- `invokes`
- `imports`
- `tests`
- `produces`
- `consumes`
- `uses`
- `other`

`interface_type`:

- `command_line`
- `function`
- `method`
- `library_api`
- `schema_contract`
- `dsl_contract`
- `document_contract`
- `configuration_contract`
- `data_contract`
- `test_fixture`
- `workflow`
- `other`

`anchor_type`:

- `file_path`
- `module_id`
- `interface_id`
- `data_id`
- `dependency_id`
- `parameter_id`
- `diagram_id`
- `table_id`
- `source_snippet_id`
- `evidence_id`
- `traceability_id`
- `other`

Every `other` enum value that has a corresponding reason field in the root spec must provide a non-empty reason.

## Not Applicable Mutual Exclusion

For every not-applicable gated section:

- if any gated content is non-empty, `not_applicable_reason` must be empty
- if all gated content is empty, `not_applicable_reason` must be non-empty

The renderer must not guess priority between content and `not_applicable_reason`. If a contradictory state reaches rendering, the renderer must fail fast.

Mutual exclusion mapping:

| Section | Gated content paths | `not_applicable_reason` path | Summary participates |
| --- | --- | --- | --- |
| Module configuration parameters | `$.module_design.modules[].configuration.parameters.rows[]` | `$.module_design.modules[].configuration.parameters.not_applicable_reason` | No |
| Module dependencies | `$.module_design.modules[].dependencies.rows[]` | `$.module_design.modules[].dependencies.not_applicable_reason` | No |
| Module data objects | `$.module_design.modules[].data_objects.rows[]` | `$.module_design.modules[].data_objects.not_applicable_reason` | No |
| Public interfaces | `$.module_design.modules[].public_interfaces.interface_index.rows[]`, `$.module_design.modules[].public_interfaces.interfaces[]` | `$.module_design.modules[].public_interfaces.not_applicable_reason` | No |
| Executable interface parameters | `$.module_design.modules[].public_interfaces.interfaces[].parameters.rows[]` | `$.module_design.modules[].public_interfaces.interfaces[].parameters.not_applicable_reason` | No |
| Executable interface return values | `$.module_design.modules[].public_interfaces.interfaces[].return_values.rows[]` | `$.module_design.modules[].public_interfaces.interfaces[].return_values.not_applicable_reason` | No |
| Internal mechanism | `$.module_design.modules[].internal_mechanism.summary`, `$.module_design.modules[].internal_mechanism.mechanism_index.rows[]`, `$.module_design.modules[].internal_mechanism.mechanism_details[]` | `$.module_design.modules[].internal_mechanism.not_applicable_reason` | Yes |
| Known limitations | `$.module_design.modules[].known_limitations.rows[]` | `$.module_design.modules[].known_limitations.not_applicable_reason` | No |
| Chapter 9 structure issues | `$.structure_issues_and_suggestions.summary`, `$.structure_issues_and_suggestions.blocks[]` | `$.structure_issues_and_suggestions.not_applicable_reason` | Yes |

`internal_mechanism.mechanism_details[].blocks[]` is not a separate not-applicable gated section and has no `not_applicable_reason`; each mechanism detail must contain non-empty `blocks[]` with at least one text block.

The following fields are invalid in V2:

- `source_scope.not_applicable_reason`
- `configuration.not_applicable_reason`

## Location Anti-Placeholder Rule

Interface locations use this shape:

```json
{
  "file_path": "scripts/render_markdown.py",
  "symbol": "main",
  "line_start": null,
  "line_end": null
}
```

`file_path` is required. `symbol`, `line_start`, and `line_end` are optional. `line_start` and `line_end` may be `null`; if one line value is present, both must be present and non-null. When line values are present, `line_start` must be at least `1` and `line_end` must be greater than or equal to `line_start`. Do not use `line_start: 1` and `line_end: 1` as an unknown placeholder. That range is allowed only when support evidence proves the target is actually on line 1.

## Validation Requirements

- `dsl_version` must be exactly `0.2.0`.
- V1 `0.1.0` examples are accepted only as rejected fixtures.
- Global enum fields must use their defined enum values.
- `other` enum values that require reason fields must provide non-empty reasons.
- Global ID uniqueness rules must be enforced.
- Not-applicable gated sections must follow the mutual exclusion table.
- Invalid alternate reason fields must fail validation.
- Location line ranges must be complete, positive, and ordered when present.
- Location placeholder ranges must fail validation unless support evidence proves line 1 is real.

## Renderer Requirements

- Fail fast for any `dsl_version` other than `0.2.0`.
- Add `--evidence-mode hidden|inline`.
- Default to `hidden`.
- Suppress evidence-node rendering in hidden mode.
- Preserve V1 support-data rendering in inline mode where V2 content still references support data.
- Fail fast if a not-applicable gated section contains both content and `not_applicable_reason`.

## Testing Requirements

Add or update tests for:

- non-`0.2.0` `dsl_version` fails before rendering
- V1 fixtures are rejected fixtures, not renderer acceptance fixtures
- default hidden evidence mode suppresses evidence-node rendering
- inline evidence mode preserves V1-style evidence rendering
- hidden evidence mode suppresses content-block support refs while preserving structural content
- global enum validation
- `other` reason validation
- global ID uniqueness
- not-applicable mutual exclusion for every mapped section
- invalid `source_scope.not_applicable_reason`
- invalid `configuration.not_applicable_reason`
- fake interface location `1-1` placeholder rejection

## Acceptance Criteria

- V2 inputs use only `dsl_version: "0.2.0"`.
- Inputs with any other DSL version fail before rendering.
- Final Markdown defaults to hidden evidence mode.
- Final Markdown can opt into inline evidence mode.
- Evidence refs remain valid DSL metadata and are hidden from final Markdown by default.
- Not-applicable contradictions fail validation or renderer fail-fast checks.
- No repository-analysis behavior is added to create-structure-md.
- No Mermaid validator or Mermaid rules files are changed.
