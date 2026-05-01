# create-structure-md Phase 1 Spec: Skill Scaffold

## Goal

Build the installable skill skeleton and execution contract for `create-structure-md`.

This phase creates the directory structure, `SKILL.md` trigger metadata, runtime dependency file, test harness, and placeholder references needed by later phases. It must not implement DSL validation, Mermaid validation, or Markdown rendering behavior yet.

## Scope

Phase 1 owns:

- Skill directory layout.
- `SKILL.md` YAML front matter and concise workflow.
- Runtime dependency declaration.
- Standard-library `unittest` test harness.
- Empty or minimal placeholder files required by later phases.

## Required Files

Create the following structure:

```text
create-structure-md/
├── SKILL.md
├── requirements.txt
├── references/
│   ├── dsl-spec.md
│   ├── document-structure.md
│   ├── mermaid-rules.md
│   └── review-checklist.md
├── schemas/
│   └── structure-design.schema.json
├── scripts/
│   ├── validate_dsl.py
│   ├── validate_mermaid.py
│   └── render_markdown.py
├── examples/
│   ├── minimal-from-code.dsl.json
│   └── minimal-from-requirements.dsl.json
└── tests/
    ├── test_validate_dsl.py
    ├── test_validate_mermaid.py
    └── test_render_markdown.py
```

## SKILL.md Contract

`SKILL.md` must include YAML front matter:

```yaml
---
name: create-structure-md
description: Use when the user asks Codex to generate a single module-specific software structure design document, such as <documented-object-name>_STRUCTURE_DESIGN.md, from already-prepared structured design content using the create-structure-md DSL and Mermaid diagrams. Do not use for repo analysis, requirements inference, multi-document generation, Word/PDF output, or image export.
---
```

Rules:

- `name` is exactly `create-structure-md`.
- `description` mentions `software structure design document`, `STRUCTURE_DESIGN.md`, `DSL`, and `Mermaid`.
- `description` excludes repo analysis, requirements inference, multi-document generation, Word/PDF output, and image export.
- The body stays concise and points Codex to `references/` for detailed DSL and rendering rules.

## Dependency Contract

`requirements.txt` contains runtime dependencies only:

```text
jsonschema
```

Testing uses Python standard library `unittest`.

Required test command:

```bash
python -m unittest discover -s tests
```

The MVP must not require `pytest`, `requirements-dev.txt`, or other third-party test dependencies.

## Script Placeholders

Phase 1 may implement CLI stubs only.

Each script should:

- Be executable as Python.
- Print a clear "not implemented in this phase" style message or expose a minimal argument parser.
- Avoid pretending validation or rendering has succeeded.

## Input Readiness Contract

`SKILL.md` must describe the skill as a document creation skill, not a project understanding skill.

Before Codex invokes this skill, Codex must already have prepared enough structured design content outside the skill to populate required DSL sections without fabrication.

The body of `SKILL.md` must state that Codex needs, at minimum:

- module list and stable module IDs
- module responsibilities
- module relationships
- module-level external capabilities or interface requirements
- module internal structure information
- runtime units and runtime flow
- configuration, structural data/artifact, and dependency information when applicable
- cross-module collaboration scenarios when more than one module is identified
- key flows and one diagram concept per key flow
- confidence values and support-data references where the schema requires or allows them
- evidence references or source snippets when available and safe to disclose

If these inputs are missing, `SKILL.md` must instruct Codex to perform project or requirement understanding outside this skill before creating DSL JSON. It must not instruct Codex to run repository analysis tools as part of this skill.

## Workflow Contract In SKILL.md

`SKILL.md` must include the high-level workflow in this order:

1. Create a temporary work directory.
2. Write one complete DSL JSON file, optionally after smaller staged JSON files.
3. Run `python scripts/validate_dsl.py structure.dsl.json`.
4. Run `python scripts/validate_mermaid.py --from-dsl structure.dsl.json --strict`.
5. Render the document with `python scripts/render_markdown.py structure.dsl.json --output-dir ...`.
6. Run `python scripts/validate_mermaid.py --from-markdown <output-file> --static`.
7. Review the generated document with `references/review-checklist.md`.
8. Report the output path, temporary work directory, assumptions, low-confidence items, and any static-only Mermaid acceptance.

The workflow text must make clear that strict Mermaid validation is the default. Static-only Mermaid validation is allowed only when strict tooling is unavailable and the user explicitly accepts that limitation for the current run.

## Output And Temporary Directory Contract

`SKILL.md` must describe the output and temporary directory rules even before the scripts are implemented:

- Final output is one Markdown file named by `document.output_file`.
- If the user provides an output directory, write `document.output_file` there.
- Otherwise write `document.output_file` to the target repository root, or to the current working directory when no target repository root is known.
- The output file must be module- or system-specific, normally `<documented-object-name>_STRUCTURE_DESIGN.md`.
- Generic-only filenames such as `STRUCTURE_DESIGN.md`, `structure_design.md`, `design.md`, and `软件结构设计说明书.md` are forbidden.
- The output filename must end with `.md`.
- The output filename must not contain path separators `/` or `\`, must not contain `..`, and must not contain control characters.
- Spaces in the output filename should already be normalized to `_` before writing `document.output_file`.
- Preferred temporary work directory is `<workspace>/.codex-tmp/create-structure-md-<run-id>/`.
- Fallback temporary work directory is a system temp directory such as `/tmp/create-structure-md-<run-id>`.
- Temporary files in the skill working directory are not automatically deleted.
- If cleanup is needed, Codex should give the cleanup command to the user rather than deleting files itself.
- The workspace `.gitignore` should include `.codex-tmp/` unless the user intentionally versions temporary artifacts.
- Codex must not edit `.gitignore` automatically unless the user asks it to.

## Reference Placeholder Requirements

Placeholder reference files must be useful signposts, not empty files.

Minimum headings:

- `references/dsl-spec.md`: DSL purpose, top-level fields, chapter fields, support data.
- `references/document-structure.md`: fixed 9-chapter Markdown outline and output filename policy.
- `references/mermaid-rules.md`: supported MVP diagram types, strict/static validation distinction, no Graphviz.
- `references/review-checklist.md`: final output path, fixed chapters, Mermaid validation, no repo analysis.

The detailed content is completed in Phase 7, but Phase 1 must prevent a fresh Codex session from treating the skill as a repository analyzer or multi-document generator.

## Tests

Phase 1 tests cover:

- `SKILL.md` front matter exists and matches the contract.
- `requirements.txt` contains `jsonschema` and no dev-only dependency.
- Required directories and placeholder files exist.
- `python -m unittest discover -s tests` runs.
- `SKILL.md` mentions the input readiness contract.
- `SKILL.md` mentions the strict Mermaid workflow and static-only acceptance rule.
- `SKILL.md` mentions that temporary files are not automatically deleted.

## Acceptance Criteria

- The skill skeleton exists in the expected layout.
- `SKILL.md` can be discovered by Codex skill metadata.
- Runtime dependency boundary is explicit.
- Test harness uses `unittest`.
- No repository-analysis behavior is introduced.
- Output filename and temporary directory rules are visible before later phases are implemented.
- Placeholders point to the future reference files instead of duplicating all detailed rules in `SKILL.md`.

## Out of Scope

- JSON Schema completeness.
- DSL semantic validation.
- Mermaid validation.
- Markdown rendering.
- End-to-end example correctness.
