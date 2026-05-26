# create-structure-md 0.3.0 Review Checklist

## Manifest Checks

- `structure.manifest.json` exists at the package root.
- The manifest contains exactly the fixed eight keys.
- The manifest contains only chapter paths.
- `key_mechanisms` is an array of direct mechanism child JSON paths.
- There is no aggregate `chapters/06-key-mechanisms.json`.
- Manifest paths are relative POSIX `.json` paths and are unique.
- JSON payloads do not contain `dsl_version`.

## Human-First Checks

- The document reads as a guide for a first-time engineer, not as a schema dump.
- The visible Mermaid labels use human-readable names, not internal IDs.
- Chapter 4 is not an API reference; it explains layers, modules, responsibilities, ownership, inputs, outputs, and neighbors.
- Chapter 5 contains one to three mainlines that connect entrypoints, layers, key files, and final effects.
- Chapter 6 explains mechanisms deeply enough for a maintainer to understand behavior, state, flow, and likely mistakes.
- Chapter 8 records validation gaps honestly, including static-only analysis, missing builds, missing hardware runs, inferred behavior, and low-confidence areas.

## Validation Commands

Run validation before rendering:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python scripts/validate_structure.py <package>/structure.manifest.json
```

Render after validation succeeds:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python scripts/render_markdown.py <package>/structure.manifest.json
```

Use an explicit output path when the rendered Markdown should be written outside the package root:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python scripts/render_markdown.py <package>/structure.manifest.json --output <output.md>
```
