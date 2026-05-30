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
- The main agent coordinates the workflow and does not directly write substantive chapter prose.
- When the target repository is C, every subagent that needs repository understanding must invoke the `repo-understand` skill first and prefer `repo-analysis-tools` before reading raw source.

## Workflow

### Step 1: Confirm Inputs

**Do:** Confirm repository root, package root, intended output path, scope, exclusions, and user constraints.

**References:** Use `references/dsl-spec.md` only to recognize the package shape.

**Watch:** Do not infer content structure from source layout at this stage.

**Output:** Known paths, output intent, and constraints.

### Step 2: Load Orchestration Contract And Route References

**Do:** Load only the contract needed to route work and enforce gates.

**References:**
- Main agent uses `references/dsl-spec.md` for manifest/package shape.
- Main agent uses `references/document-structure.md` for rendered section order.
- Main agent uses `references/review-checklist.md` for final gates.
- Authoring subagents use `references/dsl-authoring-guide.md`.
- Authoring or review subagents that touch Mermaid use `references/mermaid-rules.md`.
- For C repositories, subagents that analyze repository structure, files, symbols, or behavior must invoke `repo-understand` first and follow its `repo-analysis-tools` CLI-first route.

**Watch:** The main agent routes references; it does not use authoring references to write substantive chapter prose itself.

**Output:** A routing map from each step to its reference files.

### Step 3: Write Manifest And Document Metadata

**Do:** Main agent writes or updates `structure.manifest.json` and `chapters/00-document.json`.

**References:** Use `references/dsl-spec.md`.

**Watch:**
- Manifest uses exactly these keys: `document`, `overview`, `quick_start`, `architecture_overview`, `main_flow_overview`, `main_flow_details`, `module_overview`, and `module_details`.
- `chapters/00-document.json` contains only `repository_name`, `output_file`, and optional `summary`.
- Revisit the manifest after flow/module lists are frozen so detail arrays are non-empty and ordered.
- Reject old shapes such as `main_flows`, `chapters/04-main-flows.json`, aggregate `chapters/05-module-details.json`, `module_details.modules`, and `generated_module_object`.
- Do not add `dsl_version`, `repository_identity`, or process metadata.

**Output:** Manifest and document metadata source files.

### Step 4: Write Repository Overview

**Do:** Assign one authoring subagent to write `chapters/01-overview.json`.

**References:** Give the subagent `references/dsl-spec.md` and `references/dsl-authoring-guide.md`.

**Watch:** Repository overview renders as `## 仓库概述`. It explains what the repository is, what problem it solves, and how users and learners should orient themselves. It must not contain setup steps, module mechanisms, call chains, or directory encyclopedias.

**Output:** `chapters/01-overview.json`; authoring notes stay outside JSON.

### Step 5: Review Repository Overview

**Do:** Assign a separate review subagent to review `chapters/01-overview.json`.

**References:** Give the reviewer `references/dsl-spec.md`, `references/dsl-authoring-guide.md`, and `references/review-checklist.md`.

**Watch:** Reject missing `core_components.component_table.rows`, setup steps, architecture detail, module internals, process metadata, scan logs, or subagent identity in JSON.

**Output:** Review conclusion outside JSON; approved or returned overview file.

### Step 6: Write Quick Start

**Do:** Assign one authoring subagent to write `chapters/02-quick-start.json`.

**References:** Give the subagent `references/dsl-spec.md` and `references/dsl-authoring-guide.md`.

**Watch:** Quick start explains the first usable path and minimal verification for users, while helping learners see entry points, commands, dependencies, and outputs. It must not become a platform encyclopedia, full configuration manual, or troubleshooting catalog.

**Output:** `chapters/02-quick-start.json`; authoring notes stay outside JSON.

### Step 7: Review Quick Start

**Do:** Assign a separate review subagent to review `chapters/02-quick-start.json`.

**References:** Give the reviewer `references/dsl-spec.md`, `references/dsl-authoring-guide.md`, and `references/review-checklist.md`.

**Watch:** Reject missing or empty `first_run.steps[]`, unclear command order, vague outputs, process metadata, or content that belongs in overview, architecture overview, flow details, or module details.

**Output:** Review conclusion outside JSON; approved or returned quick start file.

### Step 8: Write Architecture Overview

**Do:** Assign one authoring subagent to write `chapters/03-architecture-overview.json`.

**References:** Give the subagent `references/dsl-spec.md` and `references/dsl-authoring-guide.md`.

**Watch:** Architecture overview maps layers, modules, and collaboration for users and learners. It must not contain detailed behavior paths, module mechanisms, quick-start steps, call chains, or directory encyclopedias.

**Output:** `chapters/03-architecture-overview.json`; authoring notes stay outside JSON.

### Step 9: Review Architecture Overview

**Do:** Assign a separate review subagent to review `chapters/03-architecture-overview.json`.

**References:** Give the reviewer `references/dsl-spec.md`, `references/dsl-authoring-guide.md`, and `references/review-checklist.md`.

**Watch:** Reject missing `layers.layer_table.rows` or `module_map.module_table.rows`, source-directory tours, function call graphs, process metadata, and module internals.

**Output:** Review conclusion outside JSON; approved or returned architecture overview file.

### Step 10: Plan Main Flow List

**Do:** Assign one subagent to decide which main flow detail files should exist.

**References:** Give the subagent `references/dsl-authoring-guide.md` and relevant repository context.

**Watch:** Flow selection is driven by what users want to know. Do not split flows too finely. Do not create separate flows for auxiliary paths, glue work, non-essential implementation details, source directories, or function call chains.

**Output:** Candidate flow list outside JSON, with `flow_key`, title, scope, include reason, merge or exclude notes, and target path `chapters/04-main-flow-details/<flow-key>.json`.

### Step 11: Review Main Flow List

**Do:** Assign a separate review subagent to challenge and freeze the main flow list.

**References:** Give the reviewer the candidate list, `references/dsl-authoring-guide.md`, and `references/review-checklist.md`.

**Watch:** Reject too many or too few flows, overlapping flows, directory-driven flow names, call-chain flow names, detail prose in the list, or missing include/exclude rationale.

**Output:** Frozen main flow list outside JSON.

### Step 12: Write Main Flow Details

**Do:** Assign one authoring subagent per frozen main flow detail file. Dispatch at most 3 authoring subagents at the same time.

**References:** Give each subagent its frozen list row, `references/dsl-spec.md`, `references/dsl-authoring-guide.md`, and `references/mermaid-rules.md` when diagrams are expected.

**Watch:** Each subagent writes only its assigned `chapters/04-main-flow-details/<flow-key>.json`. It must not change the flow list, overview files, manifest, or other detail files.

**Output:** One main flow detail JSON per frozen flow; authoring reports stay outside JSON.

### Step 13: Review Main Flow Details

**Do:** Assign one separate review subagent per main flow detail file. Dispatch at most 3 review subagents at the same time.

**References:** Give each reviewer the frozen list row, assigned detail JSON, `references/dsl-spec.md`, `references/dsl-authoring-guide.md`, `references/mermaid-rules.md` when needed, and `references/review-checklist.md`.

**Watch:** Reject content that deviates from the frozen flow, becomes a call graph, duplicates module detail, includes process metadata, or modifies files outside the assigned detail file.

**Output:** Accepted main flow detail files, or rejection instructions outside JSON.

### Step 14: Plan Module List

**Do:** Assign one subagent to decide which module detail files should exist.

**References:** Give the subagent `references/dsl-authoring-guide.md` and relevant repository context.

**Watch:** Module selection is driven by what users want to know. Do not split modules too finely. Do not create standalone modules for auxiliary code, glue code, non-important implementation layers, source directories, file groups, or helper APIs. Merge auxiliary material into the larger responsibility unit it supports.

**Output:** Candidate module list outside JSON, with `module_key`, module name, responsibility scope, include reason, merge or exclude notes, and target path `chapters/05-module-details/<module-key>.json`.

### Step 15: Review Module List

**Do:** Assign a separate review subagent to challenge and freeze the module list.

**References:** Give the reviewer the candidate list, `references/dsl-authoring-guide.md`, and `references/review-checklist.md`.

**Watch:** Reject too many or too few modules, directory-driven modules, auxiliary-code modules, overlapping responsibilities, detail prose in the list, or missing include/exclude rationale.

**Output:** Frozen module list outside JSON.

### Step 16: Write Module Details

**Do:** Assign one authoring subagent per frozen module detail file. Dispatch at most 3 authoring subagents at the same time.

**References:** Give each subagent its frozen list row, `references/dsl-spec.md`, `references/dsl-authoring-guide.md`, and `references/mermaid-rules.md` when diagrams are expected.

**Watch:** Each subagent writes only its assigned `chapters/05-module-details/<module-key>.json`. It must not change the module list, overview files, manifest, or other detail files.

**Output:** One module detail JSON per frozen module; authoring reports stay outside JSON.

### Step 17: Review Module Details

**Do:** Assign one separate review subagent per module detail file. Dispatch at most 3 review subagents at the same time.

**References:** Give each reviewer the frozen list row, assigned detail JSON, `references/dsl-spec.md`, `references/dsl-authoring-guide.md`, `references/mermaid-rules.md` when needed, and `references/review-checklist.md`.

**Watch:** Reject content that deviates from the frozen module, becomes a directory encyclopedia, API reference, file list, or call chain, makes auxiliary code the module focus, includes process metadata, or modifies files outside the assigned detail file.

**Output:** Accepted module detail files, or rejection instructions outside JSON.

### Step 18: Synthesize Overview Tables

**Do:** Main agent writes `chapters/04-main-flow-overview.json` and `chapters/05-module-overview.json` after all corresponding detail files pass review.

**References:** Use `references/dsl-spec.md`, `references/document-structure.md`, and `references/review-checklist.md`.

**Watch:** Overview rows must match manifest detail arrays in count and order. Overview files contain fixed table artifacts only; no `blocks`, `extra_subsections`, Mermaid, code, examples, detail prose, or process metadata.

**Output:** Main flow and module overview table JSON files.

### Step 19: Validate, Render, And Final Review

**Do:** Main agent validates every relevant source file, renders Markdown, and reviews the rendered result.

**References:** Use `references/review-checklist.md`, `references/document-structure.md`, and `references/mermaid-rules.md` when diagrams are present.

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
- Mermaid blocks, when present, follow `references/mermaid-rules.md` and must render under strict validation.
- Overview tables are synthesized only after corresponding detail files pass review.
- Generated Markdown is never the source of truth.

## References

- `references/dsl-spec.md`: canonical 0.4.0 DSL package and payload shape.
- `references/dsl-authoring-guide.md`: canonical authoring guidance and block usage rules.
- `references/document-structure.md`: active rendered section order.
- `references/mermaid-rules.md`: auxiliary Mermaid validation guidance.
- `references/review-checklist.md`: review gates before final acceptance.
