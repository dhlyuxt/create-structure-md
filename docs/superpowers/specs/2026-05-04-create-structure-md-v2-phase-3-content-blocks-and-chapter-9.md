# create-structure-md V2 Phase 3: Content Blocks and Chapter 9

## Summary

This phase defines the reusable text/diagram/table content block module and applies it to Chapter 4 internal mechanism details and Chapter 9 structure issues.

The root design remains `docs/superpowers/specs/2026-05-04-create-structure-md-v2-design.md`. Phase 1 and Phase 2 rules apply to this phase.

## Goals

- Provide one shared content block schema for free prose, diagrams, and tables.
- Avoid separate Chapter 4 and Chapter 9 implementations for the same free content behavior.
- Ensure flexible content still contains at least one explanatory text block.
- Preserve block-level evidence, traceability, and source snippet refs for validation and upstream tools.
- Keep Chapter 9 risks, assumptions, and low-confidence items while upgrading structure issues to content blocks.

## Non-Goals

- Do not allow raw Markdown blocks.
- Do not allow table rows to carry support refs.
- Do not generate Word, PDF, image exports, or multiple output documents.
- Do not implement Mermaid strict validation or completeness gates in this phase.
- Do not change the Chapter 4 mechanism index contract from Phase 2.

## Content Block Users

Initial content-block users:

- `module_design.modules[].internal_mechanism.mechanism_details[].blocks[]`
- `structure_issues_and_suggestions.blocks[]`

Both users must share the same schema definition, semantic validator helper, and renderer helper. Do not implement separate Chapter 4 and Chapter 9 block renderers with divergent behavior.

Content blocks are rendered in DSL order. They are not raw Markdown. The renderer owns headings, Mermaid fences, table formatting, and support-data rendering.

## Common Block Metadata

Every content block has:

```json
{
  "block_id": "BLOCK-001",
  "block_type": "text",
  "title": "说明标题",
  "confidence": "observed",
  "evidence_refs": [],
  "traceability_refs": [],
  "source_snippet_refs": []
}
```

Rules:

- `block_id` is unique within its parent content-block section.
- `block_type` is `text`, `diagram`, or `table`.
- `block_id`, `block_type`, `title`, and `confidence` are required and non-empty.
- `evidence_refs`, `traceability_refs`, and `source_snippet_refs` are optional arrays.
- When refs are present, every referenced ID must resolve.
- Hidden evidence mode suppresses rendering of these refs.
- Inline evidence mode may render support data after the block.

## Text Block

```json
{
  "block_id": "BLOCK-TEXT-001",
  "block_type": "text",
  "title": "说明标题",
  "text": "普通说明文字。",
  "confidence": "observed",
  "evidence_refs": [],
  "traceability_refs": [],
  "source_snippet_refs": []
}
```

Rules:

- `text` is plain text, not Markdown.
- `text` must be non-empty.
- `text` follows the same Markdown safety rules as other normal DSL text fields.

## Diagram Block

```json
{
  "block_id": "BLOCK-DIAGRAM-001",
  "block_type": "diagram",
  "title": "图标题",
  "confidence": "observed",
  "evidence_refs": [],
  "traceability_refs": [],
  "source_snippet_refs": [],
  "diagram": {
    "id": "MER-BLOCK-001",
    "kind": "content_block",
    "title": "图标题",
    "diagram_type": "flowchart",
    "description": "图说明。",
    "source": "flowchart TD\n  A[\"Input\"] --> B[\"Output\"]",
    "confidence": "observed"
  }
}
```

Rules:

- `diagram` uses the existing Mermaid diagram object shape.
- `diagram.source` is required and non-empty.
- Diagram block `confidence` must not conflict with `diagram.confidence`; if both are present, they must match.
- `diagram.id` is globally unique across the DSL document.

## Table Block

```json
{
  "block_id": "BLOCK-TABLE-001",
  "block_type": "table",
  "title": "表标题",
  "confidence": "observed",
  "evidence_refs": [],
  "traceability_refs": [],
  "source_snippet_refs": [],
  "table": {
    "id": "TBL-BLOCK-001",
    "title": "表标题",
    "columns": [
      { "key": "name", "title": "名称" },
      { "key": "description", "title": "说明" }
    ],
    "rows": [
      {
        "name": "示例",
        "description": "示例说明。"
      }
    ]
  }
}
```

Rules:

- `table` uses the existing local table shape.
- `table.id` is globally unique across the DSL document.
- `columns[]` and `rows[]` are non-empty.
- Table rows may only use declared column keys.
- Table rows must not carry evidence, traceability, or source snippet refs.
- Support data attaches to the table block as a whole.

## Content Block Validation

For every content-block section:

- If the parent section has a `not_applicable_reason`, `blocks[]` participates in the Phase 1 not-applicable mutual exclusion rule.
- If `blocks[]` is non-empty, at least one block must have `block_type: "text"` and non-empty `text`.
- `block_id` values are unique within the parent content-block section.
- `block_type` is `text`, `diagram`, or `table`.
- Every block has non-empty `block_id`, `block_type`, `title`, and `confidence`.
- Support ref arrays are optional, but referenced IDs must resolve when arrays are present.
- Text blocks have non-empty `text`.
- Diagram blocks have a full Mermaid diagram object with non-empty `source`.
- Table blocks have non-empty `columns[]` and `rows[]`.
- Table block rows do not contain evidence, traceability, or source snippet refs.

`internal_mechanism.mechanism_details[].blocks[]` does not have its own `not_applicable_reason`. Each mechanism detail must contain non-empty `blocks[]` with at least one text block.

## Content Block Rendering

Renderer uses `block.title` as the visible block heading.

For diagram blocks:

- `block.title` is the visible block heading.
- `diagram.title` remains diagram metadata.
- If `block.title` and `diagram.title` differ, do not replace one with the other.

For table blocks:

- `block.title` is the visible block heading.
- `table.title` may be used as table metadata or ignored by visible rendering.
- If `block.title` and `table.title` differ, `block.title` still controls the block heading.

Hidden evidence mode suppresses block support refs. Inline evidence mode may render support data after the block.

## Chapter 4 Internal Mechanism Integration

Phase 2 owns the `internal_mechanism` mechanism index and one-to-one detail contract. This phase owns the content blocks inside each mechanism detail.

Each mechanism detail:

- is keyed by `mechanism_id`
- contains non-empty `blocks[]`
- includes at least one text block
- renders as a child subsection under `4.x.6`
- renders blocks in DSL order through the shared content-block helper

## Chapter 9 Design

V2 keeps Chapter 9 as the place for:

- risks
- assumptions
- low-confidence items
- structure improvement guidance

Only `structure_issues_and_suggestions` changes from a restricted free-form string to a reusable content-block section.

Chapter 9 renders in this exact order:

```text
9.1 风险清单
9.2 假设清单
9.3 低置信度项目
9.4 结构问题与改进建议
```

`9.4 结构问题与改进建议` first renders `structure_issues_and_suggestions.summary` as a paragraph when non-empty, then renders `structure_issues_and_suggestions.blocks[]` in DSL order.

`structure_issues_and_suggestions.summary` participates in the Phase 1 not-applicable mutual exclusion rule. If either summary or blocks are non-empty, `not_applicable_reason` must be empty. If both are empty, `not_applicable_reason` must be non-empty.

## Chapter 9 Structure Issues Shape

```json
{
  "structure_issues_and_suggestions": {
    "summary": "说明本系统当前识别到的结构问题、风险和改进方向。",
    "blocks": [
      {
        "block_id": "ISSUE-TEXT-001",
        "block_type": "text",
        "title": "第四章信息密度不足",
        "text": "V1 第四章容易停留在职责摘要，缺少模块实现机制说明。V2 通过对外接口和实现机制说明补足这一点。",
        "confidence": "observed",
        "evidence_refs": [],
        "traceability_refs": [],
        "source_snippet_refs": []
      }
    ],
    "not_applicable_reason": ""
  }
}
```

Chapter 9 uses the same content block validation rules as Chapter 4 internal mechanism details.

## Testing Requirements

Add or update tests for:

- reusable content block helper renders text, diagram, and table blocks for both Chapter 4 and Chapter 9
- content block title requiredness
- content block text requiredness
- content block support refs validate but do not render in hidden mode
- content block table rows reject evidence, traceability, and source snippet refs
- content block table rows only use declared column keys
- diagram and table ID global uniqueness
- diagram block `diagram.source` requiredness
- diagram block confidence conflict validation
- internal mechanism details require at least one text block
- Chapter 9 fixed `9.1` to `9.4` rendering order
- Chapter 9 structure issues summary renders before blocks
- Chapter 9 summary participates in not-applicable mutual exclusion
- Chapter 9 requires at least one text block when blocks are present

## Acceptance Criteria

- Chapter 4 internal mechanism details render content blocks in DSL order through the shared content-block renderer.
- Chapter 9 structure issues render content blocks in DSL order through the same shared renderer.
- No separate Chapter 4 and Chapter 9 block renderers diverge in behavior.
- Every non-empty content-block section includes at least one text block.
- Content block support refs remain valid DSL metadata and are hidden from final Markdown by default.
- Chapter 9 renders risks, assumptions, low-confidence items, then structure issues in the agreed order.
- Chapter 9 structure issues render summary before content blocks.
