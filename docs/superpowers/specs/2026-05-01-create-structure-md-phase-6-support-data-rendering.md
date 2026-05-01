# create-structure-md Phase 6 Spec: Support Data And Safe Rendering

## Goal

Complete rendering and validation behavior for support data, source snippets, traceability, risks, assumptions, extra tables, and extra diagrams.

This phase makes the generated document useful as an evidence-backed structure design document without turning it into a standalone code appendix or traceability matrix.

## Dependencies

Depends on Phases 3, 4, and 5.

The renderer already outputs the base fixed document. This phase fills in support-data placement and safety details.

## Support Data Categories

Support data includes:

- `evidence`
- `traceability`
- `risks`
- `assumptions`
- `source_snippets`

Support data does not create standalone Markdown chapters.

## Support Data Object Shapes

Evidence item:

```json
{
  "id": "EV-001",
  "kind": "source",
  "title": "",
  "location": "",
  "description": "",
  "confidence": "observed"
}
```

Rules:

- `kind` is `source`, `requirement`, `note`, or `analysis`.
- `id`, `kind`, and `confidence` are non-empty when the item is present.
- `title` and `description` may be empty only when the evidence item is intentionally a lightweight reference, but they should be populated when useful for review.
- `location` may be empty when no stable location exists.

Traceability item:

```json
{
  "id": "TR-001",
  "source_external_id": "REQ-001",
  "source_type": "requirement",
  "target_type": "module",
  "target_id": "MOD-001",
  "description": ""
}
```

Rules:

- `source_external_id` is an external identifier, not an internal DSL reference.
- `source_type` is `requirement`, `note`, `code`, or `user_input`.
- `target_type` and `target_id` are authoritative.
- `description` may be short but should explain the relationship when the source ID is not self-evident.

Risk item:

```json
{
  "id": "RISK-001",
  "description": "",
  "impact": "",
  "mitigation": "",
  "confidence": "inferred",
  "evidence_refs": [],
  "traceability_refs": [],
  "source_snippet_refs": []
}
```

Assumption item:

```json
{
  "id": "ASM-001",
  "description": "",
  "rationale": "",
  "validation_suggestion": "",
  "confidence": "unknown",
  "evidence_refs": [],
  "traceability_refs": [],
  "source_snippet_refs": []
}
```

Source snippet item:

```json
{
  "id": "SNIP-001",
  "path": "src/main.py",
  "line_start": 12,
  "line_end": 28,
  "language": "python",
  "purpose": "证明 CLI 入口调用文档生成流程",
  "content": "",
  "confidence": "observed"
}
```

Phase 6 uses these shapes for rendering and for any validator refinements not completed in Phase 3.

## Evidence Rendering

Evidence referenced by design nodes renders near those nodes as concise support notes.

For fixed table rows:

- the table renders visible columns only
- evidence notes render immediately after the table
- notes are grouped by stable row ID when available
- fallback grouping uses display name only when no stable ID exists

Unreferenced evidence items produce validation warnings, not failures.

Evidence display format should be compact:

- `依据：EV-001（标题）`
- include `location` only when useful and non-empty
- avoid long evidence descriptions inline
- do not render a standalone evidence appendix

When multiple evidence refs point to the same item near the same node, render it once.

## Traceability Rendering

Traceability binding is authoritative through:

- `traceability[].target_type`
- `traceability[].target_id`

Local `traceability_refs` are optional backlinks.

Rendering behavior:

- renderer may attach traceability entries by scanning authoritative targets
- local backlinks must target the current node
- duplicate traceability found by both paths renders once
- displayed text uses source identifiers such as `REQ-001` or `NOTE-002`

Traceability display format should be compact:

- `关联来源：REQ-001`
- include traceability description when it adds context
- do not render a standalone traceability matrix in the MVP

If a design node has no local `traceability_refs`, renderer may still attach matching traceability items by scanning authoritative targets.

If a design node has local `traceability_refs`, validator must already have proven those refs target the current node.

## Source Snippet Rendering

Source snippets are optional evidence, not design content.

Rules:

- every snippet must be referenced by at least one `source_snippet_refs`
- snippets render near referencing module, runtime unit, collaboration, flow, or table-row support note
- snippets never render as a standalone appendix
- snippets never render inside Markdown table cells

Fence safety:

- renderer chooses a fence delimiter longer than any consecutive backtick run in snippet content, or
- uses an escaping or indented-code strategy that cannot be broken by snippet content

Security:

- obvious high-risk secrets fail best-effort validation
- this does not prove snippets are free of secrets
- Codex remains responsible for redaction before writing DSL

Snippet rendering format:

- show `path:line_start-line_end`
- show `purpose`
- render code using `language` as the fence info string when safe
- keep the snippet visually subordinate to the design prose

Snippets may contain existing source code, including existing function definitions, classes, structs, enums, data models, or implementation fragments. They must be presented as evidence excerpts, not as new design definitions.

Prototype/detail-design lint does not apply to `source_snippets[].content`, but it applies to normal design text surrounding snippets.

Every snippet must be referenced by at least one `source_snippet_refs` field. Unreferenced snippets fail validation because they would not render and may expose unnecessary code.

## Risks And Assumptions

Risks render under Chapter 9 `风险`.

Assumptions render under Chapter 9 `假设`.

They should not duplicate the free-form `structure_issues_and_suggestions` string.

Risk rendering fields:

- ID
- description
- impact
- mitigation
- confidence
- compact support refs when present

Assumption rendering fields:

- ID
- description
- rationale
- validation suggestion
- confidence
- compact support refs when present

If the free-form Chapter 9 string is empty but risks or assumptions exist, renderer must not output `未识别到明确的结构问题与改进建议。`.

## Low-Confidence Items

Low-confidence summary uses the whitelist from the full design spec.

It excludes:

- evidence
- traceability
- source snippets
- risks
- assumptions
- Mermaid diagram nodes

## Extra Tables

Extra table rows may use declared column keys plus `evidence_refs` only.

They must not use:

- `traceability_refs`
- `source_snippet_refs`

When evidence is present, it renders after the extra table using row display values.

Extra table support rules:

- `columns[].key` values are unique.
- `columns[].title` is non-empty.
- missing declared column keys render as empty cells.
- unknown row keys fail validation.
- row evidence renders after the table because extra table rows have no stable traceability target in MVP.

## Extra Diagrams

Extra diagrams:

- are optional by item omission
- must be full diagram objects when present
- must have non-empty source
- render in chapter-specific supplement sections
- must pass Mermaid validation

Extra diagram support data is limited to diagram-level confidence. Extra diagrams do not carry evidence or traceability refs in the MVP unless a future schema version explicitly adds them.

## Chapter 6 And Chapter 7 Empty Content

Complete empty-state behavior:

- empty Chapter 6 configuration table renders `不适用` statement
- empty structural data/artifact table renders fixed "未识别到..." statement
- empty dependencies table renders fixed "未识别到..." statement
- single-module Chapter 7 renders fixed collaboration absence text
- missing Chapter 7 diagram renders fixed no-diagram text

Chapter 6 empty-state text:

- configuration items empty: `不适用。`
- structural data/artifacts empty: `未识别到需要在结构设计阶段单独说明的关键结构数据或产物。`
- dependencies empty: `未识别到需要在结构设计阶段单独说明的外部依赖项。`

Chapter 7 fixed empty-state behavior:

- The renderer keeps `7.1` through `7.4` even in single-module mode.
- `7.2` renders `本系统当前仅识别到一个结构模块，暂无跨模块协作关系。`
- `7.3` renders `未提供跨模块协作关系图。`
- `7.4` renders an extras empty state when no extras exist.

## Table-Row Support Data Placement

Fixed table rows can carry `evidence_refs`, `traceability_refs`, and `source_snippet_refs` only when their schema explicitly allows those fields. `key_flows.flow_index.rows[]` is index-only and must not carry common metadata or support refs; support data for flows belongs on the matching `key_flows.flows[]` detail object.

Support data must not be rendered inside Markdown table cells.

Placement strategy:

1. Render the visible table columns.
2. After the table, render a compact support-data block.
3. Group support data by stable row ID when available.
4. Use the row display name only as fallback when no stable ID exists.
5. Render source snippets below the grouped note, never inside the table.

Stable row IDs include:

- `module_id`
- `capability_id`
- `unit_id`
- `config_id`
- `artifact_id`
- `dependency_id`
- `collaboration_id`
- `flow_id` on `key_flows.flows[]` detail objects, not on `key_flows.flow_index.rows[]`
- `step_id`
- `branch_id`

## Low-Confidence Rendering

The renderer summarizes `confidence: unknown` only for the agreed whitelist:

- architecture module intro rows
- module design nodes
- provided capability rows
- runtime unit rows
- Chapter 6 fixed table rows
- collaboration scenario rows
- flow objects
- flow steps
- flow branches/exceptions

It excludes:

- evidence
- traceability
- source snippets
- risks
- assumptions
- Mermaid diagram nodes

Each low-confidence item should be rendered with enough location context for review, such as module ID, flow ID, or row display name.

## Tests

Phase 6 tests cover:

- evidence rendering near modules, rows, and flows
- unreferenced evidence warning
- traceability authoritative target attachment
- conflicting traceability backlinks failure
- deduplicated traceability rendering
- source snippet references required
- source snippet safe fences
- snippets not rendered in table cells
- risk, assumption, and low-confidence Chapter 9 rendering
- extra table evidence behavior
- extra diagram non-empty source and rendering
- Chapter 6 and Chapter 7 empty states

## Acceptance Criteria

- Support data appears where useful and never bloats the document into appendices.
- Source snippets are safe to render in Markdown.
- Chapter 9 structured appendices behave consistently.

## Out of Scope

- Full traceability matrix chapter.
- Semantic proof that diagrams match relationships.
- Secret detection beyond best-effort high-risk pattern checks.
