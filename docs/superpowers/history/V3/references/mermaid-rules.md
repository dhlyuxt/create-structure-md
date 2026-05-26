# create-structure-md 0.3.0 Mermaid Rules

## Purpose

Mermaid diagrams exist to help readers build a mental model. The project validator must not implement a second Mermaid.

## Hard Boundary

Do not add a self-authored Mermaid syntax parser, grammar recognizer, source-level node parser, edge parser, participant parser, or visible-label parser.

Syntax validation is delegated to Mermaid official tooling, such as `mermaid.parse`, `mmdc`, or another official Mermaid package or CLI entry point.

## Supported DSL Types

- `flowchart`
- `sequenceDiagram`
- `stateDiagram-v2`

The validator maps Mermaid tool result names to DSL names before comparison. For example, `flowchart-v2` and `flowchart` both normalize to `flowchart`, and `sequence` normalizes to `sequenceDiagram`.

## Project Policy Checks

The validator keeps only narrow project policy checks outside Mermaid tooling:

- legacy `graph` declarations are rejected; authors must use `flowchart`
- the DSL `diagram_type` must match the Mermaid tool-reported diagram type after normalization

These checks are not a Mermaid grammar implementation.

## Visible Labels

Visible labels must be human-readable and must not expose internal IDs. In 0.3.0, the validator does not implement a source-level visible-label parser.

Future automated label gates must inspect Mermaid tooling output, such as rendered SVG text, rather than parsing Mermaid source locally.
