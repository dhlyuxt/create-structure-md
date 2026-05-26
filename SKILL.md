---
name: create-structure-md
description: Use when rendering, validating, or authoring a human-first repository reader guide from a create-structure-md 0.4.0 manifest package.
---

# create-structure-md

## Boundary

Active create-structure-md is 0.4.0 only. The 0.3.0 implementation exists only under `docs/superpowers/history/V3/` as historical reference and is not the active contract.

The authoritative deliverables are `structure.manifest.json` and the child JSON files it references. Rendered Markdown is generated output, not the source of truth.

Keep repository-understanding notes, subagent reports, command transcripts, rejected drafts, scan logs, and other process metadata outside the DSL package.

## Required Reading

Before writing, accepting, validating, or rendering DSL, read:

- `references/dsl-spec.md`
- `references/dsl-authoring-guide.md`
- `references/document-structure.md`
- `references/review-checklist.md`

Use `references/mermaid-rules.md` only as auxiliary Mermaid validation guidance. It must not redefine or fork the canonical authoring rules in `references/dsl-authoring-guide.md`.

## Input Shape

A package contains a root `structure.manifest.json` plus six fixed child JSON files for the rendered reader guide sections. Neither the manifest nor payload JSON files carry `dsl_version`.

The package should describe a repository for human readers by answering reader questions first, then grounding those answers in paths, modules, flows, and mechanisms where useful.

## Workflow

1. Confirm inputs: repository path, package path, intended output file, reader audience, and any constraints.
2. Read the contract: `dsl-spec`, `dsl-authoring-guide`, `document-structure`, and `review-checklist`.
3. Capture a dispatch brief for any subagent work, including scope, files to inspect, expected output shape, and non-deliverable status of reports.
4. Plan repository content around reader questions, not directory enumeration.
5. Freeze the outline before drafting substantial content.
6. Draft package content in manifest and child JSON files.
7. Run adversarial review for substantial content before accepting it.
8. Accept or reject DSL against the spec, authoring guide, rendered order, and review checklist.
9. Validate, render, and review the generated Markdown.

## Subagent Roles

The main agent owns package orchestration, cross-section consistency, validation, rendering, and final review.

Subagents may draft bounded content, but their reports are not renderable deliverables and must stay outside the DSL package.

Repository planning subagent output contract:

- `repository_identity`
- `problems_solved`
- `main_capabilities`
- `core_components_candidates`
- `quick_start_candidates`
- `layer_candidates`
- `module_candidates`
- `main_flow_candidates`
- `module_detail_candidates`
- `suggested_extra_subsections`
- `excluded_or_deferred_content`
- `open_questions`
- `repo_understand_usage`

Structure review subagent output contract:

- `review_decision`
- accepted component rows, layer rows, and module rows
- accepted main flows and module details
- section boundary issues
- content budget issues
- required revisions
- `repo_understand_usage`

Module-detail authoring subagent output contract:

- `module_name`
- `module_location`
- `module_purpose`
- `generated_module_object`
- `mechanisms`
- `source_evidence_summary`
- `excluded_details`
- `unresolved_gaps`
- `repo_understand_usage`

Adversarial review subagent output contract:

- `review_decision`
- section boundary findings
- dump or overdetail findings
- unsupported block findings
- module and main flow fit findings
- required revisions

## Acceptance Rules

Accept DSL only when:

- It follows create-structure-md 0.4.0.
- `structure.manifest.json` and child JSON files are the authoritative deliverables.
- `structure.manifest.json` has exactly these six keys: `document`, `overview`, `quick_start`, `architecture_overview`, `main_flows`, and `module_details`.
- Every manifest value points to the intended child JSON file, and all six fixed sections exist.
- Neither the manifest nor payload JSON files include `dsl_version`.
- Required fixed table structures are present: `overview.core_components.component_table.rows`, `architecture_overview.layers.layer_table.rows`, and `architecture_overview.module_map.module_table.rows`.
- Fixed sections omit renderer-owned `key` or `title` fields where the spec forbids them.
- Extra subsections include `key`, `title`, and `blocks`.
- Free blocks use only supported block types: `text`, `unordered_list`, `ordered_list`, `table`, `mermaid`, and `code`.
- `first_run.steps`, `main_flows.flows`, and `module_details.modules` are non-empty.
- Main flows are reader-facing behavior paths, not call chains.
- Module details describe responsibility units, not file listings.
- Mechanisms live inside the owning module.
- Content starts from reader questions and uses paths as evidence, not as the organizing principle.
- Mermaid blocks, when present, follow the canonical authoring guidance and pass strict Mermaid CLI rendering.
- Process metadata is absent from JSON and remains outside the DSL package.

## Rejection Rules

Reject DSL that:

- Treats 0.3.0 as the active contract.
- Treats rendered Markdown as source of truth.
- Includes repository-understanding notes, subagent names, command transcripts, raw scan logs, rejected drafts, or other process metadata in JSON.
- Dumps file lists, call chains, platform encyclopedias, or API references.
- Places module mechanisms outside module objects.
- Uses unsupported block shapes or list `items` values that are not string arrays.
- Forks Mermaid authoring rules outside `references/dsl-authoring-guide.md`.

## Validate And Render

Validate strictly before rendering:

```bash
python scripts/validate_structure.py <package>/structure.manifest.json --strict
python scripts/render_markdown.py <package>/structure.manifest.json
```

Review the rendered Markdown after generation, but fix source JSON rather than editing generated output.

## References

- `references/dsl-spec.md`: canonical 0.4.0 DSL package and payload shape.
- `references/dsl-authoring-guide.md`: canonical authoring guidance and block usage rules.
- `references/document-structure.md`: active rendered section order.
- `references/mermaid-rules.md`: auxiliary Mermaid validation guidance.
- `references/review-checklist.md`: review gates before final acceptance.
