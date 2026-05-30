---
name: create-structure-md
description: Use when rendering, validating, or authoring a human-first repository reader guide from a create-structure-md 0.4.0 manifest package.
---

# create-structure-md

Use this skill to produce one human-first repository structure Markdown document from a create-structure-md 0.4.0 DSL package. The main agent owns orchestration, package-level files, validation, rendering, and final review. Content-writing and review subagents produce and challenge chapter content.

## Core Boundaries

- Active create-structure-md is 0.4.0 only. Historical 0.3.0 material under `docs/superpowers/history/V3/` is not the active contract.
- `structure.manifest.json` and referenced child JSON files are authoritative. Rendered Markdown is generated output.
- Process records, subagent reports, command transcripts, rejected drafts, scan logs, repository-understanding notes, and review conclusions stay outside JSON.
- Do not use `target_readers` or `reader_questions`. The fixed templates already cover the two content layers: users and learners.
- The main agent is a workflow owner, not a repository analyst. It coordinates inputs, routing, subagent dispatch, package-level files, validation, rendering, and final review.
- The main agent may list target repository files and directories to understand package size and dispatch scope.
- The main agent must not open, read, quote, summarize, or inspect target repository source files to understand behavior, choose flows, choose modules, explain mechanisms, or select examples.
- The main agent may read create-structure-md package files, generated manifest files, reference files, validators, renderer code, and skill documentation when maintaining this create-structure-md repository itself.
- The main agent may read subagent-produced repository understanding briefs, candidate lists, review conclusions, and accepted JSON payloads.
- The main agent coordinates the workflow and does not directly write substantive chapter prose.
- When the target repository is also the current maintenance repository, the repository-access boundary applies to the repository being documented, not to create-structure-md files being edited as part of skill maintenance.
- When the target repository is C, every subagent that needs repository understanding must invoke the `repo-understand` skill first and prefer `repo-analysis-tools` before reading raw source.

## Workflow

### Step 1: Confirm Inputs

**Do:** Confirm repository root, package root, intended output path, scope, exclusions, and user constraints.

**References:** Use `references/dsl-spec.md` only to recognize the package shape.

**Watch:** The main agent may list files and directories to size the package and dispatch scope, but must not open target repository source files or infer content structure from implementation details.

**Output:** Known paths, output intent, and constraints.

### Step 2: Load Orchestration Contract And Route References

**Do:** Load only the contract needed to route work and enforce gates.

**References:**
- Main agent uses `references/dsl-spec.md` for manifest/package shape.
- Main agent uses `references/document-structure.md` for rendered section order.
- Main agent uses `references/review-checklist.md` for final gates.
- Repository-understanding subagents use `references/dsl-authoring-guide.md` plus relevant repository context.
- Authoring subagents use `references/dsl-authoring-guide.md`.
- Authoring or review subagents that touch Mermaid use `references/mermaid-rules.md` for rendering constraints and `references/dsl-authoring-guide.md` for diagram selection guidance.
- For C repositories, subagents that analyze repository structure, files, symbols, or behavior must invoke `repo-understand` first and follow its `repo-analysis-tools` CLI-first route.

**Watch:** The main agent routes references and repository context; it does not use authoring references or target source files to write substantive chapter prose itself.

**Output:** A routing map from each step to its reference files.

### Step 3: Create Repository Understanding Brief

**Do:** Assign one repository-understanding subagent before chapter authoring, flow planning, or module planning.

**Input:** Repository root, package root, scope, exclusions, user constraints, file list or directory shape gathered by the main agent, and relevant authoring guidance.

**References:** Give the subagent `references/dsl-authoring-guide.md`; for C repositories, require `repo-understand` first and `repo-analysis-tools` before raw source reading.

**Watch:** The brief is the main agent's repository context. The main agent must not replace it by opening target repository source files.

**Output:** A concise repository understanding brief outside JSON, covering repository purpose and reader-facing value, major responsibility areas, likely architecture layers, important user-facing flows, candidate module responsibilities, setup or quick-start signals, exclusions, uncertainty, and evidence limits.

### Step 4: Write Manifest And Document Metadata

**Do:** Main agent writes or updates `structure.manifest.json` and `chapters/00-document.json`.

**References:** Use `references/dsl-spec.md`.

**Watch:**
- Manifest uses exactly these keys: `document`, `overview`, `quick_start`, `architecture_overview`, `main_flow_overview`, `main_flow_details`, `module_overview`, and `module_details`.
- `chapters/00-document.json` contains only `repository_name`, `output_file`, and optional `summary`.
- Revisit the manifest after flow/module lists are frozen so detail arrays are non-empty and ordered.
- Reject old shapes such as `main_flows`, `chapters/04-main-flows.json`, aggregate `chapters/05-module-details.json`, `module_details.modules`, and `generated_module_object`.
- Do not add `dsl_version`, `repository_identity`, or process metadata.

**Output:** Manifest and document metadata source files.

### Step 5: Write Repository Overview

**Do:** Assign one authoring subagent to write `chapters/01-overview.json`.

**References:** Give the subagent the repository understanding brief, `references/dsl-spec.md`, and `references/dsl-authoring-guide.md`.

**Watch:** Repository overview renders as `## 仓库概述`. It explains what the repository is, what problem it solves, and how users and learners should orient themselves. It must not contain setup steps, module mechanisms, call chains, or directory encyclopedias.

**Output:** `chapters/01-overview.json`; authoring notes stay outside JSON.

### Step 6: Review Repository Overview

**Do:** Assign a separate review subagent to review `chapters/01-overview.json`.

**References:** Give the reviewer `references/dsl-spec.md`, `references/dsl-authoring-guide.md`, and `references/review-checklist.md`.

**Watch:** Reject missing `core_components.component_table.rows`, setup steps, architecture detail, module internals, process metadata, scan logs, or subagent identity in JSON.

**Output:** Review conclusion outside JSON; approved or returned overview file.

### Step 7: Write Quick Start

**Do:** Assign one authoring subagent to write `chapters/02-quick-start.json`.

**References:** Give the subagent the repository understanding brief, `references/dsl-spec.md`, and `references/dsl-authoring-guide.md`.

**Watch:** Quick start explains the first usable path and minimal verification for users, while helping learners see entry points, commands, dependencies, and outputs. It must not become a platform encyclopedia, full configuration manual, or troubleshooting catalog.

**Output:** `chapters/02-quick-start.json`; authoring notes stay outside JSON.

### Step 8: Review Quick Start

**Do:** Assign a separate review subagent to review `chapters/02-quick-start.json`.

**References:** Give the reviewer `references/dsl-spec.md`, `references/dsl-authoring-guide.md`, and `references/review-checklist.md`.

**Watch:** Reject missing or empty `first_run.steps[]`, unclear command order, vague outputs, process metadata, or content that belongs in overview, architecture overview, flow details, or module details.

**Output:** Review conclusion outside JSON; approved or returned quick start file.

### Step 9: Write Architecture Overview

**Do:** Assign one authoring subagent to write `chapters/03-architecture-overview.json`.

**References:** Give the subagent the repository understanding brief, `references/dsl-spec.md`, `references/dsl-authoring-guide.md`, and `references/mermaid-rules.md`.

**Watch:** Architecture overview maps layers, modules, and collaboration for users and learners. It must include at least one Mermaid block. It must not contain detailed behavior paths, module mechanisms, quick-start steps, call chains, or directory encyclopedias.

**Output:** `chapters/03-architecture-overview.json`; authoring notes stay outside JSON.

### Step 10: Review Architecture Overview

**Do:** Assign a separate review subagent to review `chapters/03-architecture-overview.json`.

**References:** Give the reviewer `references/dsl-spec.md`, `references/dsl-authoring-guide.md`, `references/mermaid-rules.md`, and `references/review-checklist.md`.

**Watch:** Reject missing `layers.layer_table.rows`, missing `module_map.module_table.rows`, missing Mermaid, source-directory tours, function call graphs, process metadata, and module internals.

**Output:** Review conclusion outside JSON; approved or returned architecture overview file.

### Step 11: Plan Main Flow List

**Do:** Assign one subagent to decide which main flow detail files should exist.

**References:** Give the subagent the repository understanding brief, `references/dsl-authoring-guide.md`, and relevant user constraints.

**Watch:** Flow selection is driven by what users want to know. Do not split flows too finely. Do not create separate flows for auxiliary paths, glue work, non-essential implementation details, source directories, or function call chains.

**Output:** Candidate flow list outside JSON, with `flow_key`, title, scope, include reason, merge or exclude notes, and target path `chapters/04-main-flow-details/<flow-key>.json`.

### Step 12: Review Main Flow List

**Do:** Assign a separate review subagent to challenge and freeze the main flow list.

**References:** Give the reviewer the candidate list, `references/dsl-authoring-guide.md`, and `references/review-checklist.md`.

**Watch:** Reject too many or too few flows, overlapping flows, directory-driven flow names, call-chain flow names, detail prose in the list, or missing include/exclude rationale.

**Output:** Frozen main flow list outside JSON.

### Step 13: Write Main Flow Details

**Do:** Assign one authoring subagent per frozen main flow detail file. Dispatch at most 3 authoring subagents at the same time.

**References:** Give each subagent its frozen list row, the repository understanding brief, `references/dsl-spec.md`, `references/dsl-authoring-guide.md`, and `references/mermaid-rules.md`.

**Watch:** Each subagent writes only its assigned `chapters/04-main-flow-details/<flow-key>.json`. Each main flow detail must include at least one Mermaid block. It must not change the flow list, overview files, manifest, or other detail files.

**Output:** One main flow detail JSON per frozen flow; authoring reports stay outside JSON.

### Step 14: Review Main Flow Details

**Do:** Assign one separate review subagent per main flow detail file. Dispatch at most 3 review subagents at the same time.

**References:** Give each reviewer the frozen list row, the repository understanding brief, assigned detail JSON, `references/dsl-spec.md`, `references/dsl-authoring-guide.md`, `references/mermaid-rules.md` when needed, and `references/review-checklist.md`.

**Watch:** Reject content that deviates from the frozen flow, becomes a call graph, duplicates module detail, includes process metadata, modifies files outside the assigned detail file, or lacks at least one Mermaid block.

**Output:** Accepted main flow detail files, or rejection instructions outside JSON.

### Step 15: Plan Module List

**Do:** Assign one subagent to decide which module detail files should exist.

**References:** Give the subagent the repository understanding brief, `references/dsl-authoring-guide.md`, and relevant user constraints.

**Watch:** Module selection is driven by what users want to know. Do not split modules too finely. Do not create standalone modules for auxiliary code, glue code, non-important implementation layers, source directories, file groups, or helper APIs. Merge auxiliary material into the larger responsibility unit it supports.

**Output:** Candidate module list outside JSON, with `module_key`, module name, responsibility scope, include reason, merge or exclude notes, and target path `chapters/05-module-details/<module-key>.json`.

### Step 16: Review Module List

**Do:** Assign a separate review subagent to challenge and freeze the module list.

**References:** Give the reviewer the candidate list, `references/dsl-authoring-guide.md`, and `references/review-checklist.md`.

**Watch:** Reject too many or too few modules, directory-driven modules, auxiliary-code modules, overlapping responsibilities, detail prose in the list, or missing include/exclude rationale.

**Output:** Frozen module list outside JSON.

### Step 17: Write Module Details

**Do:** Assign one authoring subagent per frozen module detail file. Dispatch at most 3 authoring subagents at the same time.

**References:** Give each subagent its frozen list row, the repository understanding brief, `references/dsl-spec.md`, `references/dsl-authoring-guide.md`, and `references/mermaid-rules.md`.

**Watch:** Each subagent writes only its assigned `chapters/05-module-details/<module-key>.json`. Each module detail must include at least one Mermaid block. It must not change the module list, overview files, manifest, or other detail files.

**Output:** One module detail JSON per frozen module; authoring reports stay outside JSON.

### Step 18: Review Module Details

**Do:** Assign one separate review subagent per module detail file. Dispatch at most 3 review subagents at the same time.

**References:** Give each reviewer the frozen list row, the repository understanding brief, assigned detail JSON, `references/dsl-spec.md`, `references/dsl-authoring-guide.md`, `references/mermaid-rules.md` when needed, and `references/review-checklist.md`.

**Watch:** Reject content that deviates from the frozen module, becomes a directory encyclopedia, API reference, file list, or call chain, makes auxiliary code the module focus, includes process metadata, modifies files outside the assigned detail file, or lacks at least one Mermaid block.

**Output:** Accepted module detail files, or rejection instructions outside JSON.

### Step 19: Synthesize Overview Tables

**Do:** Main agent writes `chapters/04-main-flow-overview.json` and `chapters/05-module-overview.json` after all corresponding detail files pass review.

**References:** Use `references/dsl-spec.md`, `references/document-structure.md`, and `references/review-checklist.md`.

**Watch:** Overview rows must match manifest detail arrays in count and order. Overview files contain fixed table artifacts only; no `blocks`, `extra_subsections`, Mermaid, code, examples, detail prose, or process metadata.

**Output:** Main flow and module overview table JSON files.

### Step 20: Validate, Render, And Final Review

**Do:** Main agent validates every relevant source file, renders Markdown, and reviews the rendered result.

**References:** Use `references/review-checklist.md`, `references/document-structure.md`, and `references/mermaid-rules.md`.

**Commands:**

```bash
python scripts/validate_structure.py <package>/structure.manifest.json --strict
python scripts/validate_flow_detail.py <package>/chapters/04-main-flow-details/<flow-key>.json --package-root <package>
python scripts/validate_module_detail.py <package>/chapters/05-module-details/<module-key>.json --package-root <package>
python scripts/render_markdown.py <package>/structure.manifest.json
```

**Watch:** If output is wrong, fix source JSON and render again. Do not edit generated Markdown as source. Do not put validation logs or review notes into JSON.

**Output:** One rendered repository structure Markdown document plus validation evidence outside JSON.

## Non-Negotiables

- JSON files contain accepted content only, never process records.
- The same subagent must not both write and review the same assigned file or list.
- Main flow and module detail writers/reviewers are batched with a maximum concurrency of 3.
- Detail keys are inferred from file stems and are not repeated inside detail JSON.
- List block `items` values are string arrays.
- Architecture overview, every main flow detail, and every module detail must include at least one Mermaid block.
- Mermaid blocks follow `references/mermaid-rules.md` and must render under strict validation.
- Overview tables are synthesized only after corresponding detail files pass review.
- Generated Markdown is never the source of truth.
- The repository understanding brief is produced before chapter authoring, flow planning, and module planning.
- The main agent uses only file lists, directory shape, repository understanding briefs, candidate lists, review conclusions, and accepted JSON payloads as target-repository context.
- The main agent does not open, quote, summarize, or inspect target repository source files to understand behavior.
- Missing Mermaid in architecture overview, any main flow detail, or any module detail is a rejection.

## References

- `references/dsl-spec.md`: canonical 0.4.0 DSL package and payload shape.
- `references/dsl-authoring-guide.md`: canonical authoring guidance and block usage rules.
- `references/document-structure.md`: active rendered section order.
- `references/mermaid-rules.md`: auxiliary Mermaid validation guidance.
- `references/review-checklist.md`: review gates before final acceptance.
