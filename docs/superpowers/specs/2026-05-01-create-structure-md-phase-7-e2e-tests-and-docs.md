# create-structure-md Phase 7 Spec: End-to-End Tests And References

## Goal

Finish the skill by making it usable by Codex end to end.

This phase completes examples, reference documentation, review checklist, and end-to-end validation of the workflow:

```text
validate DSL -> validate Mermaid from DSL -> render Markdown -> validate Mermaid from Markdown -> review checklist
```

## Dependencies

Depends on Phases 1 through 6.

All scripts and base behavior should exist before this phase.

## Reference Files

Complete:

- `references/dsl-spec.md`
- `references/document-structure.md`
- `references/mermaid-rules.md`
- `references/review-checklist.md`

Reference files should hold detailed rules so `SKILL.md` remains concise.

## Reference File Content Requirements

`references/dsl-spec.md` must include:

- input readiness contract
- DSL top-level fields
- common metadata
- ID prefix conventions
- defining ID fields and reference ID fields
- authoritative field contract
- fixed table row fields
- support data object shapes
- traceability target mapping
- validation policy outside DSL
- source snippet rules

`references/document-structure.md` must include:

- output filename policy
- fixed 9-chapter outline
- fixed subchapter numbering
- chapter-by-chapter rendering positions
- fixed table visible columns
- empty-state sentences
- table-row support-data placement
- Chapter 9 rendering behavior

`references/mermaid-rules.md` must include:

- Mermaid-only output rule
- supported MVP diagram types
- unsupported diagram types rule
- diagram field policy
- DSL source without fences
- strict/static validation difference
- CLI examples
- Graphviz/DOT rejection
- static-only acceptance reporting requirement

`references/review-checklist.md` must include:

- no repo analysis by skill
- module- or system-specific output file
- generic filename rejection
- fixed 9 chapters
- fixed numbering
- required Mermaid diagrams
- post-render Markdown Mermaid validation
- evidence and snippet restraint
- source snippet secret review
- Chapter 9 risk/assumption/low-confidence visibility
- output path and temporary directory in final report

## SKILL.md Final Behavior

`SKILL.md` should:

- keep the YAML front matter from Phase 1
- state the input readiness contract
- tell Codex not to analyze repositories as part of the skill
- point to `references/dsl-spec.md` before writing DSL
- point to `references/mermaid-rules.md` before creating Mermaid diagrams
- instruct Codex to run the full workflow
- instruct Codex to report output path, temporary directory, assumptions, low-confidence items, and static-only Mermaid acceptance if applicable

## Examples

Complete:

- `examples/minimal-from-code.dsl.json`
- `examples/minimal-from-requirements.dsl.json`

Each example must:

- use module- or system-specific `document.output_file`
- satisfy schema validation
- satisfy semantic DSL validation
- include renderable Mermaid for required diagrams
- exercise all fixed chapters
- avoid repository-analysis facts that were not represented as prepared design content

The examples should remain small enough to read quickly.

Example minimum content:

- concrete `document.output_file`
- one non-empty system overview
- at least one core capability
- at least one module
- Chapter 3 module intro table and module relationship diagram
- Chapter 4 matching module design for every module
- at least one provided capability per module
- internal structure diagram or textual structure per module
- at least one runtime unit
- runtime flow diagram
- Chapter 6 tables present, with empty rows allowed
- Chapter 7 single-module or multi-module behavior exercised across the two examples
- at least one key flow with steps and diagram
- Chapter 9 string present, empty or non-empty
- support data arrays present

At least one example should include:

- `evidence`
- `traceability`
- a risk or assumption
- a low-confidence whitelisted item
- a safe source snippet

The examples must not include validation policy fields such as `empty_allowed`, `required`, or `min_rows`.

## End-To-End Workflow

The required workflow:

```bash
python scripts/validate_dsl.py examples/minimal-from-code.dsl.json
python scripts/validate_mermaid.py --from-dsl examples/minimal-from-code.dsl.json --strict
python scripts/render_markdown.py examples/minimal-from-code.dsl.json --output-dir .codex-tmp/create-structure-md-e2e
python scripts/validate_mermaid.py --from-markdown .codex-tmp/create-structure-md-e2e/<output-file> --static
```

Repeat equivalent coverage for `minimal-from-requirements.dsl.json`.

If strict Mermaid tooling is unavailable, tests should cover `--check-env` and static validation, while documentation states that final generation requires either strict validation or explicit user acceptance of static-only validation.

Final user-facing workflow documentation must say:

- run `validate_dsl.py` before rendering
- run `validate_mermaid.py --from-dsl --strict` before rendering
- render exactly one output file
- run `validate_mermaid.py --from-markdown --static` after rendering
- review the document checklist
- report output file and temporary directory

If strict Mermaid validation cannot run because local tooling is unavailable, Codex must ask the user before using static-only validation. The final report must explicitly say that Mermaid diagrams were not proven renderable by Mermaid CLI.

## Review Checklist

`references/review-checklist.md` must verify:

- Skill did not perform repo analysis or requirements inference.
- Output file is module- or system-specific.
- Fixed 9-chapter structure is present.
- Section numbering is fixed.
- Required Mermaid diagrams render.
- Optional empty sections use fixed empty states.
- Evidence and snippets are not overused.
- Source snippets do not contain obvious secrets.
- Chapter 9 risks, assumptions, and low-confidence items are visible when present.
- Final report includes output path and temporary directory.

## Tests

Phase 7 tests cover:

- both examples pass `validate_dsl.py`
- both examples pass static Mermaid validation from DSL
- rendered Markdown exists at `document.output_file`
- rendered Markdown passes `validate_mermaid.py --from-markdown --static`
- fixed section numbering in rendered Markdown
- review checklist file exists and includes required review points
- `SKILL.md` references the detailed reference files
- `python -m unittest discover -s tests` passes
- reference files mention all fixed 9 chapters
- reference files mention all supported Mermaid core diagram types
- examples do not use generic-only output filenames
- examples do not contain Graphviz/DOT source
- examples do not contain schema policy fields
- examples render without shifting optional section numbering
- review checklist includes static-only Mermaid fallback reporting

## Acceptance Criteria

- A fresh Codex session can use the skill by reading `SKILL.md` and needed references.
- Both examples complete the full workflow.
- The test suite passes using standard-library `unittest`.
- The skill is ready for local personal use.
- The reference files make the original monolithic design spec unnecessary for normal implementation and use.
- End-to-end tests prove the phase contracts work together.

## Out of Scope

- Publishing the skill to a marketplace.
- Adding non-Markdown outputs.
- Adding repository analysis or requirements inference.
- Supporting Mermaid diagram types beyond the MVP core set.
