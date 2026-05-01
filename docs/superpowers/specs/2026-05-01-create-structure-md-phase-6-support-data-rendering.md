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

## Evidence Rendering

Evidence referenced by design nodes renders near those nodes as concise support notes.

For fixed table rows:

- the table renders visible columns only
- evidence notes render immediately after the table
- notes are grouped by stable row ID when available
- fallback grouping uses display name only when no stable ID exists

Unreferenced evidence items produce validation warnings, not failures.

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

## Risks And Assumptions

Risks render under Chapter 9 `风险`.

Assumptions render under Chapter 9 `假设`.

They should not duplicate the free-form `structure_issues_and_suggestions` string.

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

## Extra Diagrams

Extra diagrams:

- are optional by item omission
- must be full diagram objects when present
- must have non-empty source
- render in chapter-specific supplement sections
- must pass Mermaid validation

## Chapter 6 And Chapter 7 Empty Content

Complete empty-state behavior:

- empty Chapter 6 configuration table renders `不适用` statement
- empty structural data/artifact table renders fixed "未识别到..." statement
- empty dependencies table renders fixed "未识别到..." statement
- single-module Chapter 7 renders fixed collaboration absence text
- missing Chapter 7 diagram renders fixed no-diagram text

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
