# create-structure-md Review Checklist

## Contract

- Confirms active create-structure-md is 0.4.0.
- Confirms manifest has exactly six keys: `document`, `overview`, `quick_start`, `architecture_overview`, `main_flows`, and `module_details`.
- Confirms neither manifest nor payload JSON files include `dsl_version`.
- Treats `structure.manifest.json` and child JSON files as source of truth.
- Treats rendered Markdown as generated output.
- Does not describe 0.3.0 as the active contract.
- Rejects JSON containing subagent names, command transcripts, raw scan logs, rejected drafts, or other process metadata.

## 入门

- Overview answers what the repository is and how to read it.
- Overview includes `core_components.component_table.rows`.
- Rejects overview that contains setup steps or module mechanisms.
- Quick start gives ordered first-run actions.
- Quick start has non-empty `first_run.steps[]`.
- Rejects quick start that becomes a platform encyclopedia.

## 深入解析

- Architecture overview explains whole-repository components and collaboration.
- Architecture overview includes `layers.layer_table.rows` and `module_map.module_table.rows`.
- Rejects architecture overview that explains module internals.
- Main flows explain important behavior paths across components.
- Main flows has non-empty `flows[]` entries with `title`, `purpose`, `entry`, and `blocks`, and no `steps` field.
- Rejects main flows that become function-by-function call graphs.
- Module details explain responsibilities, mechanisms, paths, and modification risks.
- Module details has non-empty `modules[]`, with mechanisms inside the owning module.
- Rejects module details that become file-by-file listings or API reference pages.

## Blocks

- Text blocks are narrative.
- Unordered lists contain parallel facts.
- Ordered lists contain ordered actions.
- Tables are compact comparisons.
- List block `items` values are string arrays only.
- Mermaid blocks are relationship or behavior diagrams and pass strict Mermaid CLI rendering.
- Missing `mmdc`, render failure, or missing SVG output after zero exit is a rejection.

## Subagent Hygiene

- Subagent reports stay outside the DSL package.
- Repository-understanding notes stay outside the DSL package.
- Command transcripts and raw scan logs stay outside the DSL package.
- Rejected drafts stay outside the DSL package.

## Final Render

- Runs strict validation against `structure.manifest.json`.
- Renders Markdown from source JSON.
- Reviews rendered structure: `# <repository_name> 结构说明`, `## 入门`, `### 概述`, `### 快速开始`, `## 深入解析`, `### 架构概述`, `### 主线流程`, and `### 模块详解`.
- Confirms extra subsections render after fixed content in array order.
- Fixes source JSON rather than editing generated Markdown.
