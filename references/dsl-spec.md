# create-structure-md DSL Spec

## DSL Purpose

The DSL records document-ready structure design content prepared by Codex outside this skill. It does not analyze repositories, infer requirements, or decide what a target system means.

## V2 DSL Version Contract

V2 accepts only `dsl_version: "0.2.0"`. Inputs with any other version fail before semantic validation or rendering. The error says: `V1 DSL is not supported by the V2 renderer; migrate the input to dsl_version 0.2.0.`

V1 fixtures may remain in the repository only as rejected fixtures. They must not be used as renderer acceptance fixtures.

## Input Readiness Contract

The Input Readiness Contract is the gate before any DSL JSON is written. Codex must already have prepared structure design content from an earlier project-understanding step, including module IDs, responsibilities, relationships, runtime units, configuration/data/dependency details when applicable, key flows, diagram intent, confidence levels, assumptions, risks, evidence, traceability targets, and safe source snippets. If required facts are missing, do not invent placeholders inside the DSL; stop and gather the missing design input outside this skill.

## DSL Top-Level Fields

The DSL top level is a single JSON object. It must include `dsl_version`, `document`, `system_overview`, `architecture_views`, `module_design`, `runtime_view`, `configuration_data_dependencies`, `cross_module_collaboration`, `key_flows`, and `structure_issues_and_suggestions`. Support arrays are `evidence`, `traceability`, `risks`, `assumptions`, and `source_snippets`.

The schema owns structural validation through `required`, `min_rows`, and `empty_allowed` declarations. `required` fields must be present and meaningful. `min_rows` defines the minimum number of rows a fixed table section must contain unless the section explicitly declares `empty_allowed`. When `empty_allowed` is true, an empty array is valid and the renderer uses the documented empty-state sentence.

## Chapter Fields

The DSL is organized around the fixed 9-chapter Markdown output: document metadata, system overview, architecture views, module design, runtime view, configuration/data/dependencies, cross-module collaboration, key flows, and structure issues or suggestions.

## V2 Chapter 4 Module Model

`module_design.modules[]` uses the V2 module model for `dsl_version: "0.2.0"`.
Each module renders these fixed subsections in order:

1. `4.x.1 模块定位与源码/产物范围`
2. `4.x.2 配置`
3. `4.x.3 依赖`
4. `4.x.4 数据对象`
5. `4.x.5 对外接口`
6. `4.x.6 实现机制说明`
7. `4.x.7 已知限制`

The required V2 module fields include `source_scope`, `configuration`, `dependencies`, `data_objects`, `public_interfaces`, `internal_mechanism`, and `known_limitations`.

V1 fields `internal_structure`, `external_capability_details`, `extra_diagrams`, and `extra_tables` are invalid as alternate V2 module-design inputs.
Section 5.2 no longer accepts `entrypoint_not_applicable_reason` or `external_environment_reason`.
When a runtime unit has no concrete entrypoint, set `entrypoint` to exactly `不适用` and put the explanation in `notes`.

## Common Metadata

Design objects may carry common support metadata: `confidence`, `evidence_refs`, `traceability_refs`, `source_snippet_refs`, `risk_refs`, and `assumption_refs`. Metadata is never a visible fixed table column unless the document-structure contract explicitly allows a review-oriented chapter 9 rendering. Confidence values are for review summaries, not for replacing required design text.

## ID Prefix Conventions

IDs must be stable within one DSL file and use readable prefixes. Recommended prefixes are exactly: `MOD-`, `CAP-`, `RUN-`, `FLOW-`, `CFG-`, `DATA-`, `DEP-`, `COL-`, `STEP-`, `BR-`, `MER-`, `TBL-`, `EV-`, `TR-`, `RISK-`, `ASM-`, `SNIP-`. In order, these cover modules, capabilities, runtime units, key flows, configuration items, structural data/artifacts, dependencies, collaboration scenarios, flow steps, flow branches or exceptions, Mermaid diagrams, extra tables, evidence, traceability, risks, assumptions, and source snippets. Prefixes help reviewers read references, but uniqueness and schema constraints remain authoritative.

## Defining ID Fields And Reference ID Fields

Defining ID fields create targetable objects, such as `module_id`, `capability_id`, `unit_id`, `config_id`, `artifact_id`, `dependency_id`, `collaboration_id`, `flow_id`, `step_id`, and `branch_id`. Support objects use `id`: `evidence[].id`, `traceability[].id`, `risks[].id`, `assumptions[].id`, and `source_snippets[].id`. Mermaid diagrams and extra tables also use `id`. Reference ID fields point at existing definitions, such as `related_module_ids`, `participant_module_ids`, `participant_runtime_unit_ids`, `evidence_refs`, `traceability_refs`, `risk_refs`, `assumption_refs`, and `source_snippet_refs`. A reference field must not introduce a new object by implication.

`key_flows.flow_index.rows[]` are index-only references for the matching `key_flows.flows[]` detail objects. They do not carry `confidence` or support metadata; confidence and support refs belong on the matching flow detail object.

## Authoritative Field Contract

Where both local backlinks and authoritative target fields exist, authoritative target fields win. For example, traceability binding is authoritative through `traceability[].target_type` and `traceability[].target_id`; local `traceability_refs` only serve as optional backlinks and must point to traceability objects that target the current node. Renderers and validators should deduplicate support found through both paths.

## Fixed Table Row Fields

Fixed table rows use section-specific content fields only. Support metadata such as `evidence_refs`, `traceability_refs`, `source_snippet_refs`, `risk_refs`, `assumption_refs`, and `confidence` must not become visible fixed table columns. Fixed rows that are allowed to be empty use `empty_allowed`; fixed rows that must be present use `required` and `min_rows` in the schema contract.

## Support Data Object Shapes

Evidence objects record `evidence[].id`, kind, title, location, description, and confidence. Traceability objects record `traceability[].id`, `target_type`, `target_id`, and source-to-design mapping text. Risk objects record `risks[].id`, risk text, impact, mitigation, confidence, and refs where present. Assumption objects record `assumptions[].id`, assumption text, rationale, validation suggestion, confidence, and refs where present. Source snippet objects record `source_snippets[].id`, language, source location, purpose, confidence, and snippet text that is safe to disclose.

Support data strengthens nearby design content and does not create standalone chapters except for chapter 9 review summaries of risks, assumptions, and low-confidence items.

## Traceability Target Mapping

`traceability[].target_type` identifies the kind of design object being supported, and `traceability[].target_id` identifies the exact object ID. Validators should reject unknown target types, missing targets, or target IDs that do not match a defining ID field. Traceability refs remain DSL metadata by default; when rendered with `--evidence-mode inline`, renderers should show the traceability note near the mapped object and avoid duplicate notes when a local backlink also references the same traceability object.

## Validation Policy Outside DSL

Validation policy outside DSL belongs in scripts and reference contracts, not embedded as prose inside design objects. The DSL records content and metadata. File overwrite behavior, Mermaid strict/static mode selection, output filename rejection, and repository-analysis boundaries are enforced by tooling and workflow documents.

## Source Snippet Rules

Source snippets must be necessary, minimal, and safe to disclose. Do not include secrets, tokens, private keys, credentials, personal data, or unrelated code. Snippets must be referenced by at least one `source_snippet_refs` field. Source snippet refs remain DSL metadata by default; when rendered with `--evidence-mode inline`, snippets render near the referencing node and never inside Markdown table cells. Fence selection must prevent snippet content from breaking the Markdown code fence.

## Support Data

Support data supplies confidence, evidence, traceability, source snippets, risks, and assumptions for design items. Support data helps render stronger documentation but does not create standalone Markdown chapters.

- Evidence refs remain DSL metadata by default; when rendered with `--evidence-mode inline`, evidence referenced by design nodes renders near those nodes as compact `依据：EV-...` notes.
- Unreferenced evidence produces a validation warning, not a failure.
- Traceability binding is authoritative through `traceability[].target_type` and `traceability[].target_id`; local `traceability_refs` are optional backlinks and must target the current node when present. Traceability refs remain DSL metadata by default and render near the mapped object only with `--evidence-mode inline`.
- Duplicate traceability discovered through both authoritative target scanning and local backlinks renders once in inline evidence mode.
- Source snippets must be referenced by at least one `source_snippet_refs` field. Source snippet refs remain DSL metadata by default and render near the referencing node only with `--evidence-mode inline`; snippets never render inside Markdown table cells.
- Snippet code fences are chosen so snippet content cannot break the fence.
- Extra table rows may use declared content column keys plus `evidence_refs`; extra table `columns[].key` must not use support metadata names such as `evidence_refs`, `traceability_refs`, `source_snippet_refs`, or `confidence`.
- Extra diagrams are optional by omission, must be full diagram objects when present, and must have non-empty Mermaid source.
- Risks and assumptions render under chapter 9 `风险` and `假设`; compact support refs on those rows appear only with `--evidence-mode inline`.
- Low-confidence summary excludes evidence, traceability, source snippets, risks, assumptions, and Mermaid diagrams.
