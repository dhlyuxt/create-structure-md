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

## Acceptance Criteria

- A fresh Codex session can use the skill by reading `SKILL.md` and needed references.
- Both examples complete the full workflow.
- The test suite passes using standard-library `unittest`.
- The skill is ready for local personal use.

## Out of Scope

- Publishing the skill to a marketplace.
- Adding non-Markdown outputs.
- Adding repository analysis or requirements inference.
- Supporting Mermaid diagram types beyond the MVP core set.
