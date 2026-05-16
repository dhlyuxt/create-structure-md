# create-structure-md 0.3.0 DSL Spec

## Purpose

The 0.3.0 DSL stores renderable repository-structure content for one human-first Markdown document. The main JSON is a chapter directory only. It composes the document by pointing at chapter JSON files; it does not carry document prose, repository metadata, workflow notes, validation policy, output guidance, or version metadata.

The input file is `structure.manifest.json`. It is not `structure.dsl.json`, and JSON payloads do not carry `dsl_version`.

## Manifest Contract

The manifest contains exactly eight fixed keys:

- `document`
- `repository_overview`
- `directory_map`
- `module_layers`
- `repository_mainline`
- `key_mechanisms`
- `integration_boundaries`
- `risks_validation`

The manifest contains only chapter paths. The seven single chapters use one relative POSIX JSON path each. `key_mechanisms` is an array of direct mechanism child JSON paths in render order.

There is no `chapters/06-key-mechanisms.json` aggregate file. Chapter 6 is assembled directly from `key_mechanisms`, and each mechanism JSON path is a direct manifest child.

## Shared Contracts

`DocumentInfo.language` is fixed to `zh-CN`.

`SourceRef` is an object with `path` and optional `symbol`:

```json
{
  "path": "src/example.c",
  "symbol": "example_init"
}
```

`SourceRef` is never encoded as `path#symbol`, never as a symbol-only string, and never as a path-only string when a structured object is required.

Chapter 6 mechanism keys are inferred from each mechanism file stem. For example, `chapters/06-key-mechanisms/storage-flow.json` has the mechanism key `storage-flow`.

Mechanism JSON stores accepted content, not analysis transcript. repo-understand notes, subagent logs, command output, and rejected interpretations stay outside the renderable DSL.

## Chapter Contracts

The fixed eight-chapter Markdown structure is described in `references/document-structure.md`. The detailed schema contract is implemented by:

- `schemas/v0.3.0/structure.manifest.schema.json`
- `schemas/v0.3.0/chapter.schema.json`

The redesign rationale and chapter boundaries are recorded in `docs/superpowers/specs/2026-05-16-create-structure-md-0.3.0-redesign.md`.

Chapter JSON files are content-bearing. They must store facts, prose, tables, references, and Mermaid sources that can be rendered. They must not store prompts, analysis workflow rules, or repository-reading transcripts.
