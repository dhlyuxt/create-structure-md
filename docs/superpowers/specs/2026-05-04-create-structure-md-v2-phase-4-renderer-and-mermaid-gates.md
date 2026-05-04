# create-structure-md V2 Phase 4: Renderer and Mermaid Gates

## Summary

This phase turns the V2 DSL model into final Markdown and adds auditable Mermaid readability, strict validation, and rendered diagram completeness gates.

The root design remains `docs/superpowers/specs/2026-05-04-create-structure-md-v2-design.md`. Phases 1 through 3 define the content this phase renders.

## Goals

- Render V2 Chapter 4, Chapter 9, Section 5.2, evidence modes, and content blocks.
- Preserve strict Mermaid validation while keeping Mermaid validator and rule files unchanged.
- Require an auditable Mermaid readability review artifact before strict validation.
- Detect diagrams that exist in DSL but are not rendered into final Markdown.

## Non-Goals

- Do not modify `scripts/validate_mermaid.py`.
- Do not modify `references/mermaid-rules.md`.
- Do not replace strict Mermaid validation with static-only validation.
- Do not generate Word, PDF, image exports, or multiple output documents.
- Do not store readability review artifacts in DSL instances.
- Do not render readability review artifacts into final Markdown.

## Renderer Requirements

Renderer changes:

- Fail fast for any `dsl_version` other than `0.2.0`.
- Add `--evidence-mode hidden|inline`.
- Default to hidden evidence mode.
- Suppress evidence-node rendering in hidden mode.
- Preserve inline support-data rendering when `--evidence-mode inline` is used.
- Render Chapter 4 using the seven-subsection V2 structure.
- Render module-local source scope, configuration, dependencies, data objects, public interfaces, internal mechanisms, and known limitations.
- Render public interface detail sections in `public_interfaces.interface_index.rows[]` order.
- Render internal mechanism detail subsections in `internal_mechanism.mechanism_index.rows[]` order.
- Render reusable content blocks through one shared helper used by Chapter 4 internal mechanism details and Chapter 9 structure issues.
- Render local executable interface execution flow diagrams.
- Render Chapter 9 in the fixed `9.1` to `9.4` order.
- Render `structure_issues_and_suggestions.summary` before Chapter 9 structure issue blocks.
- Render Section 5.2 with simplified runtime-unit columns.
- Fail fast if a not-applicable gated section contains both content and `not_applicable_reason`.
- Emit `<!-- diagram-id: ... -->` metadata immediately before every Mermaid fence.

The `diagram-id` comment is structural Markdown source metadata. It is not evidence and is not controlled by evidence rendering mode.

## Mermaid Readability Review

Before strict Mermaid validation, the workflow must dispatch an independent subagent to review every Mermaid diagram in the DSL for visual readability.

The subagent reviews:

- labels that are too long
- dense or ambiguous graph layout
- nodes whose text is likely to disappear in rendered Markdown
- diagrams that should be split
- places where long explanatory text should move out of nodes and into prose

The subagent suggests changes. The main agent applies appropriate changes to the DSL before validation.

This review does not replace strict validation.

## Readability Review Artifact

Mermaid readability review must produce a JSON artifact before strict validation.

The artifact is workflow metadata:

- not stored in DSL instances
- not rendered into final Markdown
- validated before strict Mermaid validation

Example artifact:

```json
{
  "artifact_schema_version": "1.0",
  "reviewer": "independent_subagent",
  "source_dsl": "structure.dsl.json",
  "checked_diagram_ids": [
    "MER-IFACE-RENDER-CLI-FLOW",
    "MER-MECH-RENDER-FLOW"
  ],
  "accepted_diagram_ids": [],
  "revised_diagram_ids": [],
  "split_diagram_ids": [],
  "skipped_diagrams": [
    {
      "diagram_id": "MER-OPTIONAL-FLOW",
      "reason": "Owning section is explicitly not applicable."
    }
  ],
  "remaining_readability_risks": []
}
```

Rules:

- Every expected DSL diagram ID appears in `checked_diagram_ids` or `skipped_diagrams[].diagram_id`.
- Each skipped diagram has a non-empty reason.
- `accepted_diagram_ids`, `revised_diagram_ids`, and `split_diagram_ids` refer to checked diagram IDs or diagrams derived from checked diagram IDs.
- `source_dsl` identifies the same DSL input used by the expected diagram collector after normal path normalization.
- Strict validation runs only after the artifact is produced and validated.
- The workflow fails fast when the artifact is missing, malformed, bound to a different DSL input, or incomplete.

The V2 strict verification workflow accepts an explicit artifact path:

```text
--mermaid-review-artifact <path>
```

## Expected Diagram Collector

V2 defines one shared expected diagram collector. Readability artifact validation and rendered diagram completeness must use this same collector output.

The collector gathers every present Mermaid diagram object that should render:

| DSL path | Notes |
| --- | --- |
| `$.architecture_views.module_relationship_diagram` | Existing V1 path. |
| `$.architecture_views.extra_diagrams[]` | Existing V1 path. |
| `$.runtime_view.runtime_flow_diagram` | Existing V1 path. |
| `$.runtime_view.runtime_sequence_diagram` | Existing V1 path when present. |
| `$.runtime_view.extra_diagrams[]` | Existing V1 path. |
| `$.configuration_data_dependencies.extra_diagrams[]` | Existing V1 path. |
| `$.cross_module_collaboration.collaboration_relationship_diagram` | Existing V1 path. |
| `$.cross_module_collaboration.extra_diagrams[]` | Existing V1 path. |
| `$.key_flows.flows[].diagram` | Existing V1 path. |
| `$.key_flows.extra_diagrams[]` | Existing V1 path. |
| `$.module_design.modules[].public_interfaces.interfaces[].execution_flow_diagram` | V2 public executable interface flow. |
| `$.module_design.modules[].internal_mechanism.mechanism_details[].blocks[].diagram` | V2 content block diagrams where `block_type` is `diagram`. |
| `$.structure_issues_and_suggestions.blocks[].diagram` | V2 Chapter 9 content block diagrams where `block_type` is `diagram`. |

Removed V1 Chapter 4 module diagram paths are not expected diagrams in V2 and must not be accepted as alternate V2 input fields:

- `$.module_design.modules[].internal_structure.diagram`
- `$.module_design.modules[].external_capability_details.extra_diagrams[]`
- `$.module_design.modules[].extra_diagrams[]`

Collector output includes:

- `json_path`
- `diagram.id`
- `diagram.title`
- `diagram.source`
- owning section path

Omitted optional diagrams are not expected diagrams. A present diagram object with empty `source` is a validation error, not a skipped diagram. A diagram may be skipped only when its owning section is explicitly not applicable under the not-applicable mutual exclusion table.

## Mermaid Validation Strategy

This phase uses two strict gates:

1. Pre-render strict validation for existing Mermaid paths already supported by `scripts/validate_mermaid.py`.
2. Post-render strict validation from the rendered Markdown, so all rendered Mermaid fences, including local interface execution diagrams and content block diagrams, are checked.

The final success criteria require strict validation of rendered Markdown. Static-only Mermaid acceptance is not sufficient.

## Rendered Diagram Completeness Check

Strict Mermaid validation proves that rendered Mermaid fences are syntactically valid. It does not prove that every DSL diagram that should render actually appeared in final Markdown.

The renderer emits metadata immediately before every Mermaid fence:

````markdown
<!-- diagram-id: MER-IFACE-RENDER-CLI-FLOW -->
```mermaid
flowchart TD
  A --> B
```
````

Completeness check requirements:

- collect expected diagrams with the shared expected diagram collector
- render Markdown
- verify that each expected `diagram.id` appears exactly once in a `diagram-id` metadata comment attached to an actual Mermaid fence
- verify that Mermaid fence count is at least the number of expected rendered diagrams
- report missing diagrams with JSON path, `diagram.id`, and `diagram.title`
- do not accept title-only matches

Rendered diagram completeness and strict Mermaid validation are separate gates. Both must pass.

## Testing Requirements

Add or update tests for:

- renderer rejects non-`0.2.0` input before rendering
- renderer defaults to hidden evidence mode
- renderer supports inline evidence mode
- renderer suppresses evidence-node rendering in hidden mode
- Chapter 4 V2 rendering
- public interface detail sections render in index order
- internal mechanism detail sections render in mechanism index order
- reusable content block rendering through one helper
- Chapter 9 fixed order and structure issue summary rendering
- Section 5.2 simplified rendering
- Mermaid fences include `diagram-id` metadata comments
- shared expected diagram collector returns the same expected ID set for readability artifact validation and rendered completeness
- missing Mermaid readability review artifact fails strict verification workflow
- malformed readability artifact fails verification
- mismatched readability artifact `source_dsl` fails verification
- incomplete readability artifact diagram coverage fails verification
- skipped readability review diagram requires reason
- rendered diagram completeness catches missing interface diagrams
- rendered diagram completeness catches missing internal mechanism diagrams
- rendered diagram completeness catches missing Chapter 9 diagrams
- rendered diagram completeness rejects title-only matches without a metadata-bound Mermaid fence
- rendered diagram completeness reports JSON path and diagram ID
- strict validation of rendered Markdown containing local interface and content block diagrams

## Acceptance Criteria

- Renderer emits V2 Markdown for Chapter 4, Chapter 9, and Section 5.2.
- Final Markdown defaults to hidden evidence mode and can opt into inline evidence mode.
- Every rendered Mermaid fence has a `diagram-id` metadata comment.
- Mermaid readability review artifact exists before strict validation and covers every expected DSL diagram.
- Readability artifact validation and rendered diagram completeness use the same expected diagram collector.
- Every expected diagram collected from DSL is rendered into final Markdown unless its owning section is explicitly not applicable.
- Rendered Markdown Mermaid diagrams pass strict validation.
- Rendered diagram completeness check passes.
- No Mermaid validator or Mermaid rules files are changed.
