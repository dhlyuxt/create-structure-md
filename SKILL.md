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

A package contains a root `structure.manifest.json` plus child JSON files for the rendered reader guide sections. Payload JSON files do not carry `dsl_version`; the manifest owns the package contract.

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

- Identify reader questions and proposed sections.
- Name the repository areas inspected.
- Return recommendations, risks, and unknowns.
- Do not return renderable JSON as final authority.

Structure review subagent output contract:

- Check section boundaries, order, reader progression, and duplication.
- Flag missing context or misplaced detail.
- Return findings mapped to DSL sections.

Module-detail authoring subagent output contract:

- Draft bounded module summaries, responsibilities, mechanisms, and relevant paths.
- Avoid file-by-file listings and API reference pages.
- Mark uncertain claims explicitly for main-agent verification.

Adversarial review subagent output contract:

- Challenge whether the package follows 0.4.0 DSL, reader-first structure, block rules, and hygiene requirements.
- Identify overfitting to implementation scans, process leaks, unsupported block shapes, and unrenderable diagrams.
- Return concrete accept/reject findings.

## Acceptance Rules

Accept DSL only when:

- It follows create-structure-md 0.4.0.
- `structure.manifest.json` and child JSON files are the authoritative deliverables.
- Fixed sections omit renderer-owned `key` or `title` fields where the spec forbids them.
- Extra subsections include `key`, `title`, and `blocks`.
- Content starts from reader questions and uses paths as evidence, not as the organizing principle.
- Mermaid blocks, when present, follow the canonical authoring guidance and pass strict Mermaid CLI rendering.
- Process metadata remains outside the DSL package.

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
