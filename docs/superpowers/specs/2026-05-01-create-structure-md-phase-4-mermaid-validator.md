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

## DSL Input Mode

For `--from-dsl`:

- Extract diagram nodes with non-empty `source`.
- Skip omitted optional diagrams.
- Skip optional full diagram objects whose `source` is empty.
- Requiredness of diagram source belongs to `validate_dsl.py`, not `validate_mermaid.py`.
- `diagram_type` comes from the diagram node.
- First meaningful Mermaid line must be compatible with `diagram_type`.
- Errors include diagram ID and JSON path.

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

## Acceptance Criteria

- Mermaid validation can run independently of DSL rendering.
- Rendered Markdown can be checked with `--from-markdown --static`.
- Strict failure due to missing tooling is explicit and safe.

## Out of Scope

- Final image generation.
- Mermaid diagram semantic coverage beyond lightweight syntax and first-line checks.
- Modeling Mermaid nodes or edges in the DSL.
