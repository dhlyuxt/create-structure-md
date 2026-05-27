---
name: create-structure-md
description: Use when rendering, validating, or authoring a human-first repository reader guide from a create-structure-md 0.4.0 manifest package.
---

# create-structure-md

Use this skill to produce one human-first repository structure Markdown document from a create-structure-md 0.4.0 DSL package. The main agent owns skill execution, package orchestration, package-level JSON, validation, rendering, and final review. Planning, detail authoring, and adversarial review subagents own repository understanding, reader-facing detail decisions, and source-backed detail JSON.

## Core Boundary

Active create-structure-md is 0.4.0 only. The 0.3.0 implementation exists only under `docs/superpowers/history/V3/` as historical reference and is not the active contract.

`structure.manifest.json` and referenced child JSON files are authoritative. Rendered Markdown is generated output and must not be edited as source.

Process records, subagent reports, command transcripts, rejected drafts, scan logs, repository-understanding notes, and other process metadata stay outside JSON.

## Step-by-Step Workflow

### Step 1: Confirm Inputs And Mode

**Do:** Establish whether the user has an existing package to validate/render or needs repository-backed DSL authoring.

**How:**
- Confirm repository root.
- Confirm package root containing or intended to contain `structure.manifest.json`.
- Confirm intended Markdown output path if the user has a preference.
- Record reader audience, language, scope, exclusions, and any user-stated constraints.
- Check whether the package already has the active 0.4.0 child-file layout.

**References:** Use `references/dsl-spec.md` for package shape and `references/document-structure.md` for rendered section order.

**Watch:** Do not infer target readers, flow boundaries, or module ownership from directory names before planning. If the request is ambiguous, carry the ambiguity into the planning brief or ask the user.

**Output:** Known repository root, package root, output intent, audience constraints, and task mode.

**Continue when:** You know whether to validate/render existing JSON or author/update the package first.

### Step 2: Read The Contract And Authoring Guides

**Do:** Load the DSL rules before writing, accepting, validating, or rendering JSON.

**How:**
- Treat `references/dsl-spec.md` as the authoritative 0.4.0 DSL contract.
- Use `references/dsl-authoring-guide.md` before writing or reviewing child JSON.
- Use `references/document-structure.md` to keep rendered headings and ordering aligned.
- Use `references/mermaid-rules.md` before accepting Mermaid blocks.
- Use `references/review-checklist.md` before final acceptance.

**References:** Keep the five reference files above in scope for all later decisions.

**Watch:** Active create-structure-md is 0.4.0 only. Do not treat 0.3.0 or `docs/superpowers/history/V3/` as the active contract.

**Output:** A clear map from each JSON file type to the contract rules used to author or validate it.

**Continue when:** You can reject old package shapes and name the active files required by 0.4.0.

### Step 3: Capture Dispatch Briefs Outside JSON

**Do:** Create neutral briefs for planning and ownership work without putting process records into package JSON.

**How:**
- Record user request, repository root, package root, output path, validation mode, and constraints.
- Quote user-stated reader audience, scope, inclusion rules, and exclusion rules verbatim.
- Record open questions without resolving them from source layout alone.
- Keep subagent reports, command transcripts, scan logs, rejected drafts, repository-understanding notes, and process metadata outside the DSL package.

**References:** Use `references/dsl-spec.md` for the process-metadata boundary and `references/review-checklist.md` for hygiene checks.

**Watch:** Do not write `repository_identity`, `target_readers`, `reader_questions`, raw scan logs, subagent identities, or review notes into JSON unless the DSL contract explicitly defines a field for that content. Planning subagents may propose `repository_identity`, `target_readers`, `reader_questions`, behavior paths, responsibility units, and ownership boundaries, but their reports are process records.

**Output:** Planning and ownership dispatch briefs that can be handed to subagents.

**Continue when:** The briefs contain enough context for subagents and no process metadata has entered JSON.

### Step 4: Plan Reader-Facing Flows And Modules

**Do:** Use planning subagents to identify reader-facing main flows and responsibility-unit modules.

**How:**
- Ask planning subagents to analyze the repository from the reader's questions, not from directory enumeration.
- For main flows, prefer important behavior paths that cross components or explain how the repository accomplishes user-visible work.
- For modules, prefer responsibility units that a maintainer or reader would understand as an owned area of change.
- Ask planning subagents to propose includes, exclusions, merge/split notes, and unresolved questions.
- If the repository is C code and repository analysis is needed, invoke `repo-understand` first and prefer `repo-analysis-tools`; raw source reading is supplemental.

**References:** Use `references/dsl-authoring-guide.md` for authoring intent, `references/document-structure.md` for the reader journey, and `references/review-checklist.md` for rejecting call-chain dumps or file listings.

**Watch:** Reject plans that mirror folders, file lists, API catalogs, platform encyclopedias, or helper layers. A planned main flow must answer "what path does the reader need to understand?" A planned module must answer "what responsibility unit does the reader need to change or reason about?"

**Output:** Proposed main-flow detail files and module detail files, each with reader question, scope, include reason, exclusion notes, and suggested output path.

**Continue when:** Planned flows and modules are reader-facing and have enough ownership information for review.

### Step 5: Freeze Detail Ownership

**Do:** Freeze the one-file-one-owner plan before any detail prose is drafted.

**How:**
- Dispatch an ownership review subagent to challenge the planning proposal.
- Require a decision for every proposed flow and module: accept, merge, split, exclude, or ask planning to revise.
- Assign exactly one authoring subagent and one separate adversarial review subagent for every accepted detail file.
- Preserve target output paths:
  - `chapters/04-main-flow-details/<flow-key>.json`
  - `chapters/05-module-details/<module-key>.json`
- If planning and ownership review disagree materially, dispatch a revised planning pass, request another review, or ask the user.

**References:** Use `references/dsl-spec.md` for detail file shape and `references/review-checklist.md` for ownership and review gates.

**Watch:** The main agent checks that the frozen table is complete and consistent, but does not bypass subagent repository analysis by directly authoring substantive detail prose.

**Output:** Frozen ownership table for all accepted main-flow and module detail files.

**Continue when:** Every accepted detail file has a stable path, scope, authoring owner, and separate review owner.

### Step 6: Write Or Update The Manifest

**Do:** Create or update `structure.manifest.json` with the active eight-field 0.4.0 shape.

**How:** The manifest must contain exactly these top-level fields:

```json
{
  "document": "chapters/00-document.json",
  "overview": "chapters/01-overview.json",
  "quick_start": "chapters/02-quick-start.json",
  "architecture_overview": "chapters/03-architecture-overview.json",
  "main_flow_overview": "chapters/04-main-flow-overview.json",
  "main_flow_details": [
    "chapters/04-main-flow-details/<flow-key>.json"
  ],
  "module_overview": "chapters/05-module-overview.json",
  "module_details": [
    "chapters/05-module-details/<module-key>.json"
  ]
}
```

**References:** Use `references/dsl-spec.md` for manifest shape and key inference rules.

**Watch:** Neither manifest nor payload JSON files carry `dsl_version`. `main_flow_details` and `module_details` are non-empty arrays. Detail keys are inferred from file stems and are not repeated inside detail JSON. Reject the old aggregate shape: `main_flows`, `chapters/04-main-flows.json`, one aggregate `chapters/05-module-details.json`, `intro_blocks`, `modules[]`, `module_details.modules`, and `generated_module_object`.

**Output:** Manifest pointing to the planned child JSON files in render order.

**Continue when:** The manifest contains the eight active fields and no rejected old fields.

### Step 7: Write Main-Owned Introductory Files

**Do:** Write or update the child JSON files owned by the main agent before or alongside detail dispatch.

**How:**
- Write `chapters/00-document.json` for repository identity, output file, and summary.
- Write `chapters/01-overview.json` for repository intro, problems solved, main capabilities, and core components.
- Write `chapters/02-quick-start.json` for reader scenarios, setup, first run, and verification.
- Write `chapters/03-architecture-overview.json` for whole-repository layers, module map, and collaboration at a high level.
- Use blocks only where the DSL allows blocks.

**References:** Use `references/dsl-spec.md`, `references/dsl-authoring-guide.md`, and `references/document-structure.md`.

**Watch:** Keep introductory files human-first. Do not turn quick start into a platform encyclopedia, and do not put module internals into architecture overview. Keep process notes outside JSON.

**Output:** Main-owned child JSON for document metadata, overview, quick start, and architecture overview.

**Continue when:** Introductory files validate conceptually against their section purpose and do not duplicate detail-file responsibilities.

### Step 8: Dispatch Main-Flow Detail Authoring

**Do:** Send each main-flow authoring subagent exactly one assigned flow detail file.

**How:** Give each subagent:
- repository root
- package root
- frozen flow scope
- reader question
- target output path `chapters/04-main-flow-details/<flow-key>.json`
- relevant source areas or evidence from planning
- `references/dsl-spec.md`
- `references/dsl-authoring-guide.md`
- `references/mermaid-rules.md` when diagrams are expected
- validation command for its assigned file

Ask the subagent to describe the behavior path across components, including reader-visible inputs, actions, handoffs, outputs, and modification risks.

**References:** Use `references/dsl-authoring-guide.md` for detail authoring and `references/mermaid-rules.md` for Mermaid blocks.

**Watch:** A main-flow detail is not a function-by-function call graph. Reject raw call-chain dumps, scan logs, command transcripts, repository-understanding notes, or subagent identity markers inside JSON.

**Output:** One JSON file per accepted main flow under `chapters/04-main-flow-details/<flow-key>.json`.

**Continue when:** Every planned main-flow detail file exists or has an explicit rejection/regeneration path.

### Step 9: Dispatch Module Detail Authoring

**Do:** Send each module authoring subagent exactly one assigned module detail file.

**How:** Give each subagent:
- repository root
- package root
- frozen module scope
- responsibility-unit description
- reader question
- target output path `chapters/05-module-details/<module-key>.json`
- relevant source areas or evidence from planning
- `references/dsl-spec.md`
- `references/dsl-authoring-guide.md`
- `references/mermaid-rules.md` when diagrams are expected
- validation command for its assigned file

Ask the subagent to describe the module's responsibility, mechanisms, key files or paths, collaboration points, and modification risks.

**References:** Use `references/dsl-authoring-guide.md` for module detail requirements and `references/review-checklist.md` for responsibility-unit fit.

**Watch:** A module detail is not a file-by-file listing, generated API reference, or source directory tour. Keep mechanisms inside the owning module detail and keep process metadata outside JSON.

**Output:** One JSON file per accepted module under `chapters/05-module-details/<module-key>.json`.

**Continue when:** Every planned module detail file exists or has an explicit rejection/regeneration path.

### Step 10: Run Adversarial Detail Reviews

**Do:** Assign a separate reviewer to challenge every authored main-flow and module detail file.

**How:**
- Provide the reviewer the assigned JSON file, frozen ownership row, reader question, package root, repository root, DSL contract, authoring guide, Mermaid guidance, and validation command.
- Allow the reviewer to modify only the assigned detail file.
- Require the reviewer to report accepted content, removed or rewritten content, remaining risks, validation result, and whether the detail still fits its frozen scope.
- If a reviewer requests split, merge, or rejection, route that back through ownership review instead of silently rewriting ownership.

**References:** Use `references/review-checklist.md` for review gates, `references/dsl-authoring-guide.md` for block rules, and `references/mermaid-rules.md` for diagram checks.

**Watch:** The same subagent must not author and review the same detail file. Reviewers must not edit manifest, overview files, another detail file, or rendered Markdown.

**Output:** Reviewed detail files plus external reviewer reports that remain outside JSON.

**Continue when:** Every accepted detail file has a separate adversarial review decision and all findings are resolved in the assigned file.

### Step 11: Accept Or Reject Detail Files

**Do:** Accept only reviewed detail files that satisfy the frozen scope, DSL contract, and rendered-reader purpose.

**How:** For each detail file, check:
- file exists at the frozen target path
- required top-level fields are present
- detail key is inferred from the file stem and not repeated inside JSON
- blocks use supported types: `text`, `unordered_list`, `ordered_list`, `table`, `mermaid`, and `code`
- list block `items` values are string arrays
- extra subsections include `key`, `title`, and `blocks`
- Mermaid blocks follow canonical guidance and pass strict rendering when Mermaid validation is available
- review report confirms the file fits the assigned flow or module

**References:** Use `references/dsl-spec.md` for shape, `references/dsl-authoring-guide.md` for content rules, `references/mermaid-rules.md` for diagrams, and `references/review-checklist.md` for acceptance gates.

**Watch:** Reject files that contain process metadata, raw logs, rejected drafts, scan logs, subagent names, call-chain dumps, file-list dumps, unsupported blocks, or unreviewed detail prose.

**Output:** Accepted detail files, or rejection instructions sent back to the responsible subagent.

**Continue when:** All detail files needed by the manifest are accepted.

### Step 12: Synthesize Overview Tables From Accepted Details

**Do:** Write `main_flow_overview` and `module_overview` only after corresponding detail files pass review.

**How:**
- Build `chapters/04-main-flow-overview.json` from accepted main-flow details in manifest order.
- Build `chapters/05-module-overview.json` from accepted module details in manifest order.
- Keep rows aligned with detail arrays in count and order.
- Use anchors that link to rendered detail headings.
- Summarize accepted detail purpose without copying detail prose.

**References:** Use `references/dsl-spec.md` for fixed overview table shapes and `references/document-structure.md` for rendered placement.

**Watch:** Overview files contain fixed table artifacts only. Do not put `blocks`, `extra_subsections`, detail prose, Mermaid, code, examples, or process metadata in `main_flow_overview` or `module_overview`.

**Output:** Reviewed `chapters/04-main-flow-overview.json` and `chapters/05-module-overview.json`.

**Continue when:** Overview rows match accepted detail arrays exactly.

### Step 13: Validate The Package And Detail Files

**Do:** Run strict validation before rendering.

**How:** Validate the package and any changed detail files:

```bash
python scripts/validate_structure.py <package>/structure.manifest.json --strict
python scripts/validate_flow_detail.py <package>/chapters/04-main-flow-details/<flow-key>.json --package-root <package>
python scripts/validate_module_detail.py <package>/chapters/05-module-details/<module-key>.json --package-root <package>
```

**References:** Use `references/review-checklist.md` for required validation coverage and `references/mermaid-rules.md` for diagram validation expectations.

**Watch:** If validation fails in main-owned files, fix those source JSON files. If validation fails in subagent-owned detail prose, reject the file back to the responsible subagent or reviewer unless the fix is purely mechanical and within the accepted scope.

**Output:** Passing validation output or a concrete list of files that must be fixed.

**Continue when:** Strict package validation and relevant detail validation pass.

### Step 14: Render And Review The Markdown

**Do:** Render Markdown from the manifest and review the generated document.

**How:**

```bash
python scripts/render_markdown.py <package>/structure.manifest.json
```

Then inspect the rendered Markdown against the expected section order from `references/document-structure.md`.

**References:** Use `references/document-structure.md` for section order and `references/review-checklist.md` for final acceptance.

**Watch:** Rendered Markdown is generated output. If the rendered document is wrong, fix source JSON and render again; do not edit the Markdown as source.

**Output:** One human-first repository structure Markdown document.

**Continue when:** The rendered document matches the package intent, validation evidence is recorded outside JSON, and any remaining gaps are reported clearly.

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
