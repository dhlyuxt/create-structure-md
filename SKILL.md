---
name: create-structure-md
description: Use when rendering, validating, or authoring a human-first repository reader guide from a create-structure-md 0.4.0 manifest package.
---

# create-structure-md

## Boundary

Active create-structure-md is 0.4.0 only. The 0.3.0 implementation exists only under `docs/superpowers/history/V3/` as historical reference and is not the active contract.

`structure.manifest.json` and referenced child JSON files are authoritative. Rendered Markdown is generated output and must not be edited as source.

Process records, subagent reports, command transcripts, rejected drafts, scan logs, repository-understanding notes, and other process metadata stay outside JSON.

## Required Reading

Before writing, accepting, validating, or rendering DSL, read:

- `references/dsl-spec.md`
- `references/dsl-authoring-guide.md`
- `references/document-structure.md`
- `references/review-checklist.md`
- `references/mermaid-rules.md`

## Input Shape

A package contains a root `structure.manifest.json` plus referenced child JSON files. Neither the manifest nor payload JSON files carry `dsl_version`.

The active 0.4.0 manifest uses eight fields:

- `document`
- `overview`
- `quick_start`
- `architecture_overview`
- `main_flow_overview`
- `main_flow_details`
- `module_overview`
- `module_details`

`main_flow_details` is a non-empty array of files under `chapters/04-main-flow-details/<flow-key>.json`.

`module_details` is a non-empty array of files under `chapters/05-module-details/<module-key>.json`.

Rejected old active 0.4.0 shape: `main_flows` pointing to `chapters/04-main-flows.json`, `module_details` pointing to one aggregate `chapters/05-module-details.json`, `module_details.modules`, and `generated_module_object`.

## Step-by-Step Workflow

1. Confirm repository path, package path, intended output file, reader audience, and constraints.
2. Load the contract from required references.
3. Create dispatch briefs for repository planning and ownership freeze. Briefs stay outside JSON.
4. Plan reader-facing flows and responsibility-unit modules from reader questions, not directory enumeration.
5. Freeze ownership before detail drafting: one planned detail file belongs to one authoring subagent.
6. Create or update `structure.manifest.json` with the eight-field manifest and referenced child file paths.
7. Dispatch one authoring subagent per file under `chapters/04-main-flow-details/<flow-key>.json`.
8. Dispatch one authoring subagent per file under `chapters/05-module-details/<module-key>.json`.
9. Dispatch a separate adversarial review subagent for every accepted detail file.
10. Accept detail files only after review findings are resolved in the assigned file.
11. Synthesize `main_flow_overview` and `module_overview` only after all corresponding detail files pass review.
12. Validate package and detail files.
13. Render Markdown from the manifest.
14. Review rendered output against the checklist, then fix source JSON if needed.

## Main Agent Responsibilities

The main agent owns package orchestration, dispatch briefs, contract loading, planning dispatch, ownership freeze dispatch, manifest creation, overview synthesis, validation, rendering, and final review.

The main agent does not directly author substantive Chapter 4 or Chapter 5 detail prose. It may create scaffolds, assign files, reconcile contracts, apply review-required corrections, and synthesize overview tables after detail acceptance.

The main agent ensures `main_flow_overview` and `module_overview` are synthesized after all detail files pass review.

## Subagent Roles

Planning subagents may propose `repository_identity`, `target_readers`, `reader_questions`, behavior paths, responsibility units, and ownership boundaries. Their reports are process records and stay outside JSON.

Main-flow authoring subagents write exactly one assigned flow detail file under `chapters/04-main-flow-details/<flow-key>.json`.

Module authoring subagents write exactly one assigned module detail file under `chapters/05-module-details/<module-key>.json`.

Every accepted detail file requires a separate adversarial review subagent. Reviewers may modify only their assigned detail file.

Authoring and review subagents must not write process metadata, command transcripts, raw scan logs, rejected drafts, or subagent identities into JSON.

## Acceptance Rules

Accept DSL only when:

- It follows active create-structure-md 0.4.0.
- `structure.manifest.json` and referenced child JSON files are authoritative.
- Rendered Markdown is treated as generated output.
- The manifest has exactly the upgraded eight-field shape.
- `main_flow_details` and `module_details` are non-empty arrays of referenced detail files.
- Detail keys are inferred from file stems and are not repeated inside detail JSON.
- Every detail file has one owning authoring subagent and one separate adversarial review subagent.
- `main_flow_overview` and `module_overview` are synthesized after detail review passes.
- Overview rows match detail arrays in count and order.
- Overview files contain fixed table artifacts only and do not contain detail prose, Mermaid, code, examples, `blocks`, or `extra_subsections`.
- Main-flow detail files describe reader-facing behavior paths, not call-chain dumps.
- Module detail files describe responsibility units, not source-file listings.
- Free blocks use only supported block types: `text`, `unordered_list`, `ordered_list`, `table`, `mermaid`, and `code`.
- List block `items` values are string arrays.
- Extra subsections include `key`, `title`, and `blocks`.
- Mermaid blocks, when present in allowed files, follow the canonical authoring guidance and pass strict Mermaid CLI rendering.
- Process metadata is absent from JSON and remains outside the DSL package.

## Rejection Rules

Reject DSL that:

- Treats 0.3.0 as the active contract.
- Treats rendered Markdown as source of truth.
- Uses the rejected old active 0.4.0 aggregate shape: `main_flows`, `chapters/04-main-flows.json`, `intro_blocks`, `modules[]`, `module_details.modules`, or `generated_module_object`.
- Includes repository-understanding notes, subagent names, command transcripts, raw scan logs, scan logs, rejected drafts, or other process metadata in JSON.
- Lets the main agent directly author substantive Chapter 4 or Chapter 5 detail prose.
- Reuses the same subagent for authoring and adversarial review of a detail file.
- Lets a reviewer modify files outside the assigned detail file.
- Writes `main_flow_overview` or `module_overview` before corresponding detail files pass review.
- Places `blocks`, `extra_subsections`, detail prose, Mermaid, code, examples, or process metadata in overview files.
- Dumps file lists, call chains, platform encyclopedias, or API references.
- Uses unsupported block shapes or list `items` values that are not string arrays.
- Forks Mermaid authoring rules outside `references/dsl-authoring-guide.md`.

## Validate And Render

Validate strictly before rendering:

```bash
python scripts/validate_structure.py <package>/structure.manifest.json --strict
python scripts/validate_flow_detail.py <package>/chapters/04-main-flow-details/<flow-key>.json --package-root <package>
python scripts/validate_module_detail.py <package>/chapters/05-module-details/<module-key>.json --package-root <package>
python scripts/render_markdown.py <package>/structure.manifest.json
```

Review the rendered Markdown after generation, but fix source JSON rather than editing generated output.

## References

- `references/dsl-spec.md`: canonical 0.4.0 DSL package and payload shape.
- `references/dsl-authoring-guide.md`: canonical authoring guidance and block usage rules.
- `references/document-structure.md`: active rendered section order.
- `references/mermaid-rules.md`: auxiliary Mermaid validation guidance.
- `references/review-checklist.md`: review gates before final acceptance.
