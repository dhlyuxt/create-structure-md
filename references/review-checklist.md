# create-structure-md Review Checklist

## Contract

- Confirms active create-structure-md is 0.4.0.
- Confirms upgraded eight-field manifest: `document`, `overview`, `quick_start`, `architecture_overview`, `main_flow_overview`, `main_flow_details`, `module_overview`, and `module_details`.
- Confirms `main_flow_details` and `module_details` are non-empty arrays.
- Confirms neither manifest nor payload JSON files include `dsl_version`.
- Treats `structure.manifest.json` and referenced child JSON files as source of truth.
- Treats rendered Markdown as generated output.
- Does not describe 0.3.0 as the active contract.
- Rejects old aggregate path shape: `main_flows`, `chapters/04-main-flows.json`, one aggregate `chapters/05-module-details.json`, `intro_blocks`, `modules[]`, `module_details.modules`, or `generated_module_object`.
- Rejects JSON containing subagent names, command transcripts, raw scan logs, scan logs, rejected drafts, or other process metadata.

## Ownership And Review

- Confirms one-detail-per-subagent ownership for every file under `chapters/04-main-flow-details/`.
- Confirms one-detail-per-subagent ownership for every file under `chapters/05-module-details/`.
- Confirms separate adversarial detail review for every accepted detail file.
- Confirms reviewers modified only their assigned detail file.
- Confirms `main_flow_overview` and `module_overview` were synthesized only after details passed review.

## Main Sections

- Repository overview answers what the repository is and how to read it.
- Overview includes `core_components.component_table.rows`.
- Rejects overview that contains setup steps or module mechanisms.
- Quick start gives ordered first-run actions.
- Quick start has non-empty `first_run.steps[]`.
- Rejects quick start that becomes a platform encyclopedia.
- Architecture overview explains whole-repository components and collaboration.
- Architecture overview includes `layers.layer_table.rows` and `module_map.module_table.rows`.
- Rejects architecture overview that explains module internals.
- Main-flow detail files explain important behavior paths across components.
- Confirms main-flow behavior-path fit and rejects function-by-function call graphs.
- Module detail files explain responsibility units, mechanisms, paths, and modification risks.
- Confirms module responsibility-unit fit and rejects file-by-file listings or API reference pages.
- Confirms mechanisms live inside the owning module detail.

## Overview Tables

- Confirms fixed overview table shape for `main_flow_overview.flow_table.rows`.
- Confirms fixed overview table shape for `module_overview.module_table.rows`.
- Confirms overview rows match detail arrays in count and order.
- Confirms overview rows link to detail headings through `anchor`.
- Rejects `main_flow_overview` or `module_overview` containing `blocks`, `extra_subsections`, detail prose, Mermaid, code, examples, or process metadata.

## Blocks

- Text blocks are narrative.
- Unordered lists contain parallel facts.
- Ordered lists contain ordered actions.
- Tables are compact comparisons.
- List block `items` values are string arrays only.
- Mermaid readability is checked before final acceptance.
- Mermaid blocks are relationship or behavior diagrams and pass strict Mermaid CLI rendering.
- Missing `mmdc`, render failure, or missing SVG output after zero exit is a rejection.

## Subagent Hygiene

- Subagent reports stay outside the DSL package.
- Repository-understanding notes stay outside the DSL package.
- Command transcripts and raw scan logs stay outside the DSL package.
- Rejected drafts stay outside the DSL package.
- Process metadata absence is confirmed in every JSON file.

## Final Render

- Runs strict validation against `structure.manifest.json`.
- Runs flow detail validation for every file under `chapters/04-main-flow-details/`.
- Runs module detail validation for every file under `chapters/05-module-details/`.
- Renders Markdown from source JSON.
- Reviews rendered structure: `# <repository_name> 结构说明`, `## 仓库概述`, `## 快速开始`, `## 架构概述`, `## 主线流程`, and `## 模块详解`.
- Confirms extra subsections render after fixed content in array order.
- Fixes source JSON rather than editing generated Markdown.
