# repo-understand Workflow For 0.3.0

## Purpose

For unfamiliar C repositories, run `repo-understand` before finalizing the create-structure-md DSL. The goal is to produce structured repository understanding material that can be accepted into the manifest package, not to produce final Markdown directly.

`repo-understand` should use `repo-analysis-tools` first and raw source reading as a supplement after the CLI context is clear.

## Division Of Work

The main agent owns the document shape. It identifies repository purpose, reading order, directory roles, layers, modules, one to three mainlines, integration boundaries, and candidate mechanisms.

Chapter 6 is the primary place for repo-understand depth. The main agent chooses mechanisms that explain how the repository works, then a subagent may inspect independent mechanisms in parallel when the mechanisms do not share state or require a strict sequence.

A mechanism investigation should return structured material:

- reader-facing mechanism summary
- related source files and important symbols
- core flow and state/data relationships
- common misunderstandings
- validation gaps and confidence notes

## Output Boundary

Subagents return structured mechanism material to the main agent. The main agent accepts, edits, and integrates that material into direct `key_mechanisms` child JSON files.

The mechanism JSON stores accepted content, not identity, logs, or transcript. Do not store subagent names, repo-understand command logs, raw tool output, chain-of-thought, rejected branches, or analysis transcripts in the DSL.

If a project needs provenance, keep it in implementation notes or a future explicit sidecar. It does not belong in `structure.manifest.json` or child chapter JSON.
