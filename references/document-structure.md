# create-structure-md 0.4.0 Document Structure

This file documents only the active rendered section order for create-structure-md 0.4.0.

Rendered Markdown is generated output. The source of truth is `structure.manifest.json` plus child JSON files.

## Rendered Section Order

1. Document title and summary from document metadata.
2. 概述 from `overview`.
3. 入门 from `quick_start`.
4. 架构概述 from `architecture_overview`.
5. 主线流程 from `main_flows`.
6. 深入解析 from `module_details`.
7. Extra subsections from `extra_subsections`, in array order.

## Fixed Headings

Renderer-owned fixed headings are not repeated as `title` fields in fixed DSL sections. Fixed sections also do not carry `key` fields.

Module headings come from `module_details.modules[].name`.

Extra subsection headings come from each extra subsection `title`; their stable identifiers come from `key`.
