# create-structure-md Mermaid Rules

## Mermaid-Only Output Rule

Final diagram deliverables are Markdown Mermaid code fences inside the single rendered Markdown document. There are no final Graphviz/DOT/SVG/PNG/PDF/image deliverables. Strict validation may create temporary Mermaid CLI artifacts under `--work-dir` solely for validation, but those artifacts are not final outputs and are not reported as deliverables.

## Supported MVP Diagram Types

The MVP supports Mermaid diagram sources for `flowchart`, `graph`, `sequenceDiagram`, `classDiagram`, and `stateDiagram-v2`.

## Unsupported Diagram Types

Unsupported diagram types include Graphviz, DOT, PlantUML, D2, raw SVG, PNG, PDF, and any generated image export. Unsupported Mermaid diagram families are also outside the MVP until scripts explicitly validate them. If prepared design content requires an unsupported type, stop and ask the user whether to simplify it into a supported Mermaid MVP type.

## Diagram Field Policy

Diagram fields contain Mermaid source text only. Diagram titles, descriptions, and confidence/support metadata belong in their own DSL fields. Diagram source must be non-empty when a diagram object is present, and omitted diagrams should be omitted rather than represented as empty Mermaid blocks.

## DSL Source Without Fences

DSL Source Without Fences means the DSL stores the Mermaid body only. Do not include triple backticks, Markdown code fences, rendered images, Graphviz/DOT source, or file paths to image assets inside a Mermaid source field. The renderer is responsible for creating the Markdown Mermaid fence.

## Strict/Static Validation Difference

Strict validation checks Mermaid sources before rendering whenever strict tooling is available. Static validation checks rendered Markdown Mermaid code blocks for fence shape and non-empty sources when strict tooling is unavailable and the user explicitly accepts that limitation.

Strict validation proves the supported Mermaid sources can be parsed by local Mermaid CLI tooling. Static validation proves only that the Markdown contains syntactically shaped Mermaid fences and non-empty source text; it does not prove CLI renderability.

## CLI Examples

Validate DSL diagrams strictly before rendering:

```bash
python scripts/validate_mermaid.py --from-dsl structure.dsl.json --strict --work-dir <temporary-work-directory>/mermaid
```

Validate rendered Markdown statically after rendering:

```bash
python scripts/validate_mermaid.py --from-markdown <output-file> --static
```

## Graphviz/DOT Rejection

Final diagrams are Markdown Mermaid code blocks. Graphviz, DOT files, SVG files, PNG files, and image export are outside this skill.

Graphviz/DOT Rejection is absolute for final output: do not produce `.dot`, `.gv`, `.svg`, `.png`, `.pdf`, or other image deliverables as replacements for Mermaid. If legacy content contains Graphviz or DOT, convert the intent to supported Mermaid or stop for user direction.

## Static-Only Acceptance Reporting

Static-only validation is a fallback, not a silent success path. If local Mermaid CLI tooling is unavailable, stop and ask user before using static-only validation. The final report must state that Mermaid diagrams were not proven renderable by Mermaid CLI, tooling unavailable was the reason, and the user explicitly accepts static-only validation.
