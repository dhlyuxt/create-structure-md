# create-structure-md DSL Spec

## DSL Purpose

The DSL records document-ready structure design content prepared by Codex outside this skill. It does not analyze repositories, infer requirements, or decide what a target system means.

## Top-Level Fields

Later phases define the full schema for `dsl_version`, `document`, fixed chapter objects, `evidence`, `traceability`, `risks`, `assumptions`, and `source_snippets`.

## Chapter Fields

The DSL is organized around the fixed 9-chapter Markdown output: document metadata, system overview, architecture views, module design, runtime view, configuration/data/dependencies, cross-module collaboration, key flows, and structure issues or suggestions.

## Support Data

Support data supplies confidence, evidence, traceability, source snippets, risks, and assumptions for design items. Support data helps render stronger documentation but does not create standalone Markdown chapters.

- Evidence referenced by design nodes renders near those nodes as compact `依据：EV-...` notes.
- Unreferenced evidence produces a validation warning, not a failure.
- Traceability binding is authoritative through `traceability[].target_type` and `traceability[].target_id`; local `traceability_refs` are optional backlinks and must target the current node when present.
- Duplicate traceability discovered through both authoritative target scanning and local backlinks renders once.
- Source snippets must be referenced by at least one `source_snippet_refs` field, render near the referencing node, and never render inside Markdown table cells.
- Snippet code fences are chosen so snippet content cannot break the fence.
- Extra table rows may use declared content column keys plus `evidence_refs`; extra table `columns[].key` must not use support metadata names such as `evidence_refs`, `traceability_refs`, `source_snippet_refs`, or `confidence`.
- Extra diagrams are optional by omission, must be full diagram objects when present, and must have non-empty Mermaid source.
- Risks and assumptions render under chapter 9 `风险` and `假设`, with compact support refs when present.
- Low-confidence summary excludes evidence, traceability, source snippets, risks, assumptions, and Mermaid diagrams.
