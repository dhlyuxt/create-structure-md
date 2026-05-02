# create-structure-md Mermaid Rules

## Supported MVP Diagram Types

The MVP supports Mermaid diagram sources for `flowchart`, `graph`, `sequenceDiagram`, `classDiagram`, and `stateDiagram-v2`.

## Strict And Static Validation

Strict validation checks Mermaid sources before rendering whenever strict tooling is available. Static validation checks rendered Markdown Mermaid code blocks for fence shape and non-empty sources when strict tooling is unavailable and the user explicitly accepts that limitation.

## No Graphviz

Final diagrams are Markdown Mermaid code blocks. Graphviz, DOT files, SVG files, PNG files, and image export are outside this skill.
