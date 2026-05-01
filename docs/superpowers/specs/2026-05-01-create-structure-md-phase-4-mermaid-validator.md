# create-structure-md Phase 4 Spec: Mermaid Validator

## Goal

Implement `scripts/validate_mermaid.py` as an independent Mermaid validation tool.

Mermaid correctness is a first-class quality gate. This phase validates Mermaid blocks from DSL or rendered Markdown and supports both strict local Mermaid CLI validation and deterministic static checks.

## Dependencies

Depends on Phase 1.

It can be implemented after Phase 2 if DSL diagram extraction needs the final schema paths.

## CLI Contract

```bash
python scripts/validate_mermaid.py --from-dsl structure.dsl.json --strict
python scripts/validate_mermaid.py --from-dsl structure.dsl.json --strict --work-dir .codex-tmp/create-structure-md-xxx/mermaid
python scripts/validate_mermaid.py --from-dsl structure.dsl.json --static
python scripts/validate_mermaid.py --from-markdown <output-file> --strict
python scripts/validate_mermaid.py --from-markdown <output-file> --static
python scripts/validate_mermaid.py --check-env
```

Rules:

- `--from-dsl` and `--from-markdown` are mutually exclusive.
- `--check-env` is used by itself.
- `--strict` and `--static` are mutually exclusive.
- Default mode is `--strict`.
- `--work-dir` is valid in strict mode and preserves temporary validation artifacts there.

## Supported Diagram Types

MVP supports only:

- `flowchart`
- `graph`
- `sequenceDiagram`
- `classDiagram`
- `stateDiagram-v2`

All other Mermaid diagram types fail in MVP.

## Diagram Type Recognition

For DSL input, `diagram_type` comes from the diagram object and must be one of the MVP supported values.

For Markdown input, there is no DSL `diagram_type`. The script infers the type from the first meaningful line:

| First meaningful line starts with | Inferred type |
| --- | --- |
| `flowchart` | `flowchart` |
| `graph` | `graph` |
| `sequenceDiagram` | `sequenceDiagram` |
| `classDiagram` | `classDiagram` |
| `stateDiagram-v2` | `stateDiagram-v2` |

First meaningful line detection skips:

- blank lines
- Mermaid comments starting with `%%`
- Mermaid init directives such as `%%{init: ...}%%`

The validator should not over-require directions such as `TD` or `LR` for `flowchart` and `graph`; Mermaid itself should decide detailed grammar in strict mode.

## DSL Input Mode

For `--from-dsl`:

- Extract diagram nodes with non-empty `source`.
- Skip omitted optional diagrams.
- Skip optional full diagram objects whose `source` is empty.
- Requiredness of diagram source belongs to `validate_dsl.py`, not `validate_mermaid.py`.
- `diagram_type` comes from the diagram node.
- First meaningful Mermaid line must be compatible with `diagram_type`.
- Errors include diagram ID and JSON path.

DSL extraction must find diagram objects recursively under known DSL fields, including:

- `architecture_views.module_relationship_diagram`
- `architecture_views.extra_diagrams[]`
- `module_design.modules[].internal_structure.diagram`
- `module_design.modules[].external_capability_details.extra_diagrams[]`
- `module_design.modules[].extra_diagrams[]`
- `runtime_view.runtime_flow_diagram`
- `runtime_view.runtime_sequence_diagram`
- `runtime_view.extra_diagrams[]`
- `configuration_data_dependencies.extra_diagrams[]`
- `cross_module_collaboration.collaboration_relationship_diagram`
- `cross_module_collaboration.extra_diagrams[]`
- `key_flows.flows[].diagram`
- `key_flows.extra_diagrams[]`

The script validates only diagrams whose `source` is non-empty. It must not fail optional empty diagrams. Requiredness belongs to `validate_dsl.py`.

## Markdown Input Mode

For `--from-markdown`:

- Extract fenced code blocks whose language is `mermaid`.
- Every Mermaid block must have a non-empty body.
- There is no explicit `diagram_type`.
- Infer diagram type from the first meaningful line.
- Fail if inferred type is missing or unsupported.
- Errors include Mermaid block index.

First meaningful line ignores:

- blank lines
- Mermaid comments starting with `%%`
- Mermaid init directives

Markdown extraction validates renderer output, not DSL requiredness. It must detect:

- unbalanced fenced code blocks
- empty Mermaid fenced blocks
- Mermaid fenced blocks whose first meaningful line cannot be inferred
- Mermaid fenced blocks using unsupported diagram types

Errors should identify the block index and, when possible, line number.

## Static Validation

Static validation checks:

- Mermaid block body non-empty.
- Diagram type supported.
- First meaningful line compatible or inferable.
- Markdown fences balanced.
- DSL Mermaid source contains no Markdown fences.
- Graphviz/DOT constructs are rejected when used as diagram source.
- Diagram IDs unique for DSL input.

Static validation is useful for tests and renderer-output checks but does not prove Mermaid CLI renderability.

Graphviz/DOT rejection targets common accidental DOT syntax:

- `digraph`
- `rankdir`
- `node -> node;` style statements

Mermaid arrows remain allowed, including:

- `-->`
- `---`
- `->>`
- `-->|label|`

Static validation must fail closed for malformed blocks and produce actionable messages.

## Strict Validation

Strict mode delegates to local Mermaid CLI tooling.

Required local tooling:

- `node`
- `@mermaid-js/mermaid-cli`
- `mmdc` on `PATH`

Strict mode may render temporary SVG/PNG/PDF/HTML artifacts solely for validation. These artifacts are not final deliverables.

If tooling is unavailable:

- The command fails clearly.
- It must not claim diagrams are proven renderable.
- Static-only fallback is allowed only after explicit user acceptance in the skill workflow.

Strict validation workflow:

1. Confirm `mmdc` is available on `PATH`, or report missing tooling.
2. Write each Mermaid source to a temporary `.mmd` file.
3. Invoke Mermaid CLI to render-check the file.
4. Treat any Mermaid CLI non-zero exit as validation failure.
5. Preserve artifacts under `--work-dir` when provided.
6. Use an implementation-local system temp directory when `--work-dir` is omitted.
7. Never copy temporary render artifacts to the final output directory.

`--check-env` reports environment status without validating a diagram. It should check, at minimum:

- `node` availability
- `mmdc` availability
- Mermaid CLI version when available

The command may return non-zero when strict tooling is missing; tests should not require Mermaid CLI to be installed unless they explicitly mock or skip strict validation.

## Static-Only Acceptance Boundary

The script itself cannot infer user acceptance. If strict tooling is unavailable, it fails clearly.

The skill workflow may choose `--static` only after the user explicitly accepts static-only validation for the current run. That acceptance is recorded outside the DSL, normally in the final report and optionally in `.codex-tmp/create-structure-md-<run-id>/VALIDATION_NOTES.md`.

The report must say:

- Mermaid strict validation was not performed.
- The reason was local Mermaid CLI tooling unavailable.
- The user accepted static-only validation for this run.

## Mermaid Source Restrictions

DSL Mermaid source must contain Mermaid source only:

- no surrounding Markdown fences
- no nested triple-backtick fences
- no Graphviz code
- requiredness of empty source is enforced by `validate_dsl.py`, not by `validate_mermaid.py`

Renderer-produced Markdown adds the final fenced block. `validate_mermaid.py --from-markdown` validates those fences after rendering.

## Tests

Phase 4 tests cover:

- DSL extraction skips optional empty sources.
- DSL extraction validates non-empty diagram nodes.
- Markdown extraction finds Mermaid fences.
- Markdown inference succeeds for all MVP core types.
- Markdown inference fails for unsupported or missing types.
- Graphviz/DOT examples fail.
- Source containing Markdown fences fails.
- `--check-env` reports environment status without needing input.
- `--work-dir` strict mode preserves artifacts when strict validation is available or is mocked.
- First meaningful line detection skips blank lines, comments, and init directives.
- Markdown mode infers each supported core type.
- DSL mode rejects supported-type mismatches such as `diagram_type: sequenceDiagram` with `flowchart TD` source.
- Static mode does not falsely reject Mermaid arrows while rejecting DOT-like arrows.
- Strict tooling unavailable failure is explicit and does not claim diagrams are renderable.

## Acceptance Criteria

- Mermaid validation can run independently of DSL rendering.
- Rendered Markdown can be checked with `--from-markdown --static`.
- Strict failure due to missing tooling is explicit and safe.

## Out of Scope

- Final image generation.
- Mermaid diagram semantic coverage beyond lightweight syntax and first-line checks.
- Modeling Mermaid nodes or edges in the DSL.
