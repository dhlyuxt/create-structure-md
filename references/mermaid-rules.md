# Mermaid Rules

This file is auxiliary validation guidance for Mermaid blocks. It points back to `references/dsl-authoring-guide.md` as the single canonical authoring reference and must not redefine or fork that guide.

## Active Gate

Every Mermaid block must render through Mermaid CLI when Mermaid blocks exist.

Missing `mmdc` is an error.

Render failure is an error.

Missing SVG output after zero exit is an error.

## Authoring Guidance

Prefer readable `flowchart` and `sequenceDiagram` diagrams.

Prefer `flowchart` over legacy `graph`.

Use human-readable labels.

Avoid internal IDs in visible labels.

Keep diagrams short enough to review directly in the DSL.

Do not include process logs, command transcripts, raw scan logs, rejected drafts, or subagent reports.

Static readability guidance does not replace CLI rendering. Mermaid blocks still need strict Mermaid CLI rendering before final acceptance.
