# create-structure-md V2 Phase 5: Examples, Tests, Docs, and Acceptance

## Summary

This phase completes V2 by migrating examples, updating documentation, adding accepted and rejected fixtures, and verifying the full workflow end to end.

The root design remains `docs/superpowers/specs/2026-05-04-create-structure-md-v2-design.md`. Phases 1 through 4 define the behavior this phase documents and tests.

## Goals

- Make V2 usable through examples and documentation.
- Convert acceptance criteria into tests.
- Keep V1 examples only as rejected fixtures.
- Verify schema, semantic validation, renderer behavior, Mermaid gates, and final Markdown output.
- Ensure no out-of-scope Mermaid files are modified.

## Non-Goals

- Do not implement repository analysis.
- Do not implement a migration tool.
- Do not accept V1 examples as valid renderer inputs.
- Do not generate Word, PDF, image exports, or multiple output documents.
- Do not modify `scripts/validate_mermaid.py`.
- Do not modify `references/mermaid-rules.md`.

## Documentation Updates

Update:

- `SKILL.md`
- `references/dsl-spec.md`
- `references/document-structure.md`
- `references/review-checklist.md`
- examples
- tests

Do not update:

- `references/mermaid-rules.md`

Documentation must state:

- create-structure-md consumes prepared structured content
- create-structure-md does not analyze repositories
- create-structure-md does not infer missing requirements
- create-structure-md does not invent missing design content from source code
- V2 supports only `dsl_version: "0.2.0"`
- V1 inputs fail fast and require migration outside this phase
- evidence rendering is controlled by renderer CLI, not DSL
- hidden evidence mode is default
- Chapter 4 uses the seven-subsection module model
- Chapter 9 keeps risks, assumptions, low-confidence items, and structure issues
- strict Mermaid validation of rendered Markdown is required
- Mermaid readability review artifact is required before strict validation
- static-only Mermaid acceptance is insufficient

## Example Migration

Examples must be migrated to `dsl_version: "0.2.0"` and exercise the V2 shape.

At least one accepted example should include:

- Chapter 4 source scope
- module configuration parameters
- module dependencies
- module data objects
- public interface index and details
- executable interface with non-empty `execution_flow_diagram.source`
- contract interface with `required_items`
- internal mechanism index and detail content blocks
- typed related anchors
- known limitations
- Chapter 9 structure issue content blocks
- at least one content block diagram
- hidden evidence refs that validate but do not render by default

Legacy V1 examples may remain only as rejected fixtures. They must not be treated as renderer acceptance fixtures.

## Test Coverage

The full test suite must cover:

- Phase 1 foundation rules
- Phase 2 Chapter 4 module model
- Phase 3 content blocks and Chapter 9
- Phase 4 renderer and Mermaid gates
- accepted V2 examples
- rejected V1 fixtures
- full rendered Markdown workflow

Full test command:

```text
python3 -m unittest discover -s tests -v
```

Strict Mermaid validation and rendered diagram completeness must both be part of the verification story for rendered Markdown. Static-only Mermaid acceptance is not sufficient.

## Required Test Themes

Add or update tests for:

- non-`0.2.0` `dsl_version` fails before rendering
- legacy V1 fixtures are rejected fixtures, not renderer acceptance fixtures
- default hidden evidence mode suppresses evidence-node rendering
- inline evidence mode preserves V1 evidence rendering
- hidden evidence mode suppresses content-block support refs while preserving structural content
- Chapter 4 new subsection order
- `module_design.modules[]` matches Chapter 3 modules one-to-one
- removed V1 Chapter 4 module fields fail validation
- source scope rendering
- `module_kind` enum validation
- `module_kind: "other"` requires `module_kind_reason`
- configuration rendering
- configuration `value_source` enum validation
- not-applicable mutual exclusion for rows, blocks, public interfaces, and internal mechanism index/details
- not-applicable mutual exclusion uses the documented content/reason path mapping
- invalid `source_scope.not_applicable_reason`
- invalid `configuration.not_applicable_reason`
- dependency rendering
- dependency `dependency_type` enum validation
- dependency `usage_relation` enum validation
- dependency target reference validation for `internal_module` and `data_object`
- module and system dependencies cannot reuse the same `dependency_id`
- module dependency can reference a system dependency through `system_dependency_ref`
- invalid `system_dependency_ref`
- `system_dependency_ref` resolves against `configuration_data_dependencies.dependencies.rows[]`
- data object rendering
- public interface index rendering
- public interface detail rendering
- interface details render in index order, not physical details array order
- orphan interface detail validation failure
- executable interface validation
- executable interface parameter row requiredness
- executable interface return value row requiredness
- contract interface validation
- contract interface requiredness
- contract interface optional `constraints` validation
- contract interface uses `required_items`
- contract interface rejects `required_fields`
- `other` interface requires `interface_type_reason`
- interface location allows null line values
- interface location rejects fake `1-1` placeholder ranges
- local interface Mermaid rendering
- local interface Mermaid `source` requiredness
- internal mechanism index rendering
- internal mechanism detail rendering
- internal mechanism index/detail one-to-one validation
- internal mechanism detail sections render in mechanism index order
- orphan mechanism detail validation failure
- typed related anchors render correctly
- bare string `related_anchors[]` fails validation
- related anchors require non-empty `value`
- unknown non-file anchor IDs fail validation
- `file_path` anchors do not require file-system checks
- `other` anchors require reason
- internal mechanism details require at least one text block
- reusable content block helper renders text, diagram, and table blocks for both Chapter 4 and Chapter 9
- content block title requiredness
- content block support refs validate but do not render in hidden mode
- diagram and table ID global uniqueness
- known limitations rendering
- Chapter 9 content block rendering
- Chapter 9 structure issues summary renders before blocks
- Chapter 9 summary participates in not-applicable mutual exclusion
- Chapter 9 fixed `9.1` to `9.4` rendering order
- Chapter 9 requires at least one text block when blocks are present
- Section 5.2 simplified columns
- Section 5.2 runtime unit DSL no longer uses `entrypoint_not_applicable_reason` or `external_environment_reason`
- Section 5.2 `entrypoint: "不适用"` requires non-empty `notes`
- Section 5.2 `entrypoint` beginning with `不适用：` fails validation
- shared expected diagram collector returns the same expected ID set for readability artifact validation and rendered completeness
- Mermaid fences include `diagram-id` metadata comments
- missing Mermaid readability review artifact fails strict verification workflow
- malformed or mismatched readability artifact `source_dsl` fails verification
- incomplete readability artifact diagram coverage fails verification
- skipped readability review diagram requires reason
- rendered diagram completeness catches missing interface diagrams
- rendered diagram completeness catches missing internal mechanism diagrams
- rendered diagram completeness catches missing Chapter 9 diagrams
- rendered diagram completeness rejects title-only matches without a metadata-bound Mermaid fence
- rendered diagram completeness reports JSON path and diagram ID
- V2 schema acceptance
- V2 semantic validation failures for missing required structural fields
- strict validation of rendered Markdown containing local interface and content block diagrams

## Implementation Impact Checklist

Expected implementation files:

- `schemas/structure-design.schema.json`
- `scripts/validate_dsl.py`
- `scripts/render_markdown.py`
- `SKILL.md`
- `references/dsl-spec.md`
- `references/document-structure.md`
- `references/review-checklist.md`
- `examples/*.dsl.json`
- `tests/*`

Files intentionally out of scope:

- `scripts/validate_mermaid.py`
- `references/mermaid-rules.md`

## Acceptance Criteria

- V2 examples validate successfully.
- Final Markdown defaults to hidden evidence mode.
- Final Markdown can opt into inline evidence mode.
- Inputs with `dsl_version` other than `0.2.0` fail before rendering.
- Chapter 4 renders the seven agreed subsections in order.
- Executable interface detail sections include prototype, purpose, location, parameter table, return value table, local non-empty Mermaid flow diagram, side effects, error behavior, and consumers.
- Contract interface detail sections include purpose, location, contract scope, contract location, required items, constraints when present, consumers, and validation behavior.
- Internal mechanism renders a mechanism index plus one detail subsection per mechanism.
- Interface details and internal mechanism details render in index order.
- Internal mechanism details render text, diagram, and table content blocks in DSL order through the reusable content-block renderer.
- Chapter 9 renders risks, assumptions, low-confidence items, then structure issues in the agreed order.
- Chapter 9 structure issues render summary before content blocks.
- Chapter 9 structure issues render text, diagram, and table content blocks in DSL order through the reusable content-block renderer.
- Content block support refs remain valid DSL metadata and are hidden from final Markdown by default.
- Section 5.2 no longer shows `入口不适用原因` or `外部环境原因` columns.
- Section 5.2 DSL no longer uses `entrypoint_not_applicable_reason` or `external_environment_reason`.
- Runtime unit `entrypoint: "不适用"` stores its explanation in `notes`.
- Mermaid readability review artifact exists before strict validation and covers every expected DSL diagram.
- Readability artifact validation and rendered diagram completeness use the same expected diagram collector.
- Every rendered Mermaid fence has a `diagram-id` metadata comment.
- Every expected diagram collected from DSL is rendered into final Markdown unless its owning section is explicitly not applicable.
- Rendered Markdown Mermaid diagrams pass strict validation.
- Rendered diagram completeness check passes.
- No Mermaid validator or Mermaid rules files are changed.
