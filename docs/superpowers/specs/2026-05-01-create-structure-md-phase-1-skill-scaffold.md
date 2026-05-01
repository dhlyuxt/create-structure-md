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

## Tests

Phase 1 tests cover:

- `SKILL.md` front matter exists and matches the contract.
- `requirements.txt` contains `jsonschema` and no dev-only dependency.
- Required directories and placeholder files exist.
- `python -m unittest discover -s tests` runs.

## Acceptance Criteria

- The skill skeleton exists in the expected layout.
- `SKILL.md` can be discovered by Codex skill metadata.
- Runtime dependency boundary is explicit.
- Test harness uses `unittest`.
- No repository-analysis behavior is introduced.

## Out of Scope

- JSON Schema completeness.
- DSL semantic validation.
- Mermaid validation.
- Markdown rendering.
- End-to-end example correctness.
