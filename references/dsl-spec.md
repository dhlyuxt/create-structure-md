# create-structure-md 0.4.0 DSL 规范

## Package Shape

create-structure-md 0.4.0 package 由一个 `structure.manifest.json` 和若干 child JSON files 组成。`structure.manifest.json` 是入口；payload JSON files 不携带 `dsl_version`。

Example `structure.manifest.json`:

```json
{
  "dsl_version": "0.4.0",
  "document": {
    "file": "document.json"
  },
  "sections": {
    "overview": "overview.json",
    "quick_start": "quick-start.json",
    "architecture_overview": "architecture-overview.json",
    "main_flows": "main-flows.json",
    "module_details": "module-details.json",
    "extra_subsections": "extra-subsections.json"
  }
}
```

## Document Metadata

The document metadata child file defines repository identity, output path, and summary.

Example `document.json`:

```json
{
  "document": {
    "repository_name": "示例仓库",
    "output_file": "Example_STRUCTURE_DESIGN.md",
    "summary": "一个用于演示 create-structure-md 0.4.0 的最小仓库说明。"
  }
}
```

## Shared Blocks

Blocks are section-local content units. Supported shapes should be used consistently across child files.

Text block:

```json
{
  "type": "text",
  "text": "这个仓库把结构化输入渲染成人类优先的阅读指南。"
}
```

Unordered list block:

```json
{
  "type": "unordered_list",
  "items": [
    "面向首次接触仓库的读者",
    "优先解释职责、边界和主线流程"
  ]
}
```

Ordered list block:

```json
{
  "type": "ordered_list",
  "items": [
    "安装依赖",
    "运行验证",
    "渲染 Markdown"
  ]
}
```

Table block:

```json
{
  "type": "table",
  "columns": ["区域", "作用"],
  "rows": [
    ["scripts", "验证和渲染 DSL"],
    ["schemas", "约束 JSON 结构"]
  ]
}
```

Mermaid block:

```json
{
  "type": "mermaid",
  "diagram": "flowchart LR\n  Manifest[Manifest] --> Validator[Validator]\n  Validator --> Renderer[Renderer]"
}
```

Code block:

```json
{
  "type": "code",
  "language": "bash",
  "code": "python scripts/validate_structure.py package/structure.manifest.json --strict"
}
```

List block `items` values are string arrays only.

## Overview

Fixed overview sections are renderer-owned and do not carry `key` or `title`.

Example `overview.json`:

```json
{
  "overview": {
    "blocks": [
      {
        "type": "text",
        "text": "示例仓库展示如何把 0.4.0 DSL 包渲染成结构说明文档。"
      },
      {
        "type": "unordered_list",
        "items": [
          "读者先理解仓库目标",
          "再进入快速开始和架构地图"
        ]
      }
    ]
  }
}
```

## Quick Start

Quick start contains first-run steps ordered by array position. Each step contains blocks.

Example `quick-start.json`:

```json
{
  "quick_start": {
    "first_run": {
      "steps": [
        {
          "name": "验证 DSL",
          "blocks": [
            {
              "type": "code",
              "language": "bash",
              "code": "python scripts/validate_structure.py package/structure.manifest.json --strict"
            }
          ]
        },
        {
          "name": "渲染文档",
          "blocks": [
            {
              "type": "code",
              "language": "bash",
              "code": "python scripts/render_markdown.py package/structure.manifest.json"
            }
          ]
        }
      ]
    }
  }
}
```

## Architecture Overview

Architecture overview explains the whole-repository map. `core_components` starts with one `component_table`, followed by optional blocks.

Example `architecture-overview.json`:

```json
{
  "architecture_overview": {
    "core_components": [
      {
        "type": "component_table",
        "columns": ["组件", "职责", "主要路径"],
        "rows": [
          ["Manifest package", "保存文档源数据", "package/*.json"],
          ["Validator", "检查 DSL 结构", "scripts/validate_structure.py"],
          ["Renderer", "生成 Markdown", "scripts/render_markdown.py"]
        ]
      },
      {
        "type": "mermaid",
        "diagram": "flowchart LR\n  Package[DSL package] --> Validator[Validator]\n  Package --> Renderer[Renderer]\n  Renderer --> Markdown[Markdown]"
      }
    ]
  }
}
```

## Main Flows

`main_flows.flows[]` has no `steps` field. Represent flow details with blocks.

Example `main-flows.json`:

```json
{
  "main_flows": {
    "flows": [
      {
        "name": "验证并渲染结构说明",
        "blocks": [
          {
            "type": "text",
            "text": "使用者先验证 manifest 指向的 child JSON files，再把同一入口交给 renderer 生成 Markdown。"
          },
          {
            "type": "mermaid",
            "diagram": "sequenceDiagram\n  participant User\n  participant Validator\n  participant Renderer\n  User->>Validator: Validate manifest\n  User->>Renderer: Render manifest"
          }
        ]
      }
    ]
  }
}
```

## Module Details

Module headings come from `module_details.modules[].name`. Mechanisms live inside module objects.

Example `module-details.json`:

```json
{
  "module_details": {
    "modules": [
      {
        "name": "Validator",
        "summary": "检查 manifest 和 child JSON files 是否符合 0.4.0 contract。",
        "paths": [
          "scripts/validate_structure.py",
          "schemas/"
        ],
        "mechanisms": [
          {
            "name": "Strict validation",
            "blocks": [
              {
                "type": "text",
                "text": "严格模式拒绝未知字段、错误 block shape 和不符合章节约束的结构。"
              }
            ]
          }
        ],
        "blocks": [
          {
            "type": "unordered_list",
            "items": [
              "验证入口始终是 structure.manifest.json",
              "错误应指向可修复的源 JSON"
            ]
          }
        ]
      }
    ]
  }
}
```

## Extra Subsections

Extra subsections are optional reader-facing sections. Each subsection carries `key`, `title`, and `blocks`.

Example `extra-subsections.json`:

```json
{
  "extra_subsections": [
    {
      "key": "maintenance_notes",
      "title": "维护提示",
      "blocks": [
        {
          "type": "text",
          "text": "修改 DSL 后先验证源 JSON，再重新渲染 Markdown。"
        }
      ]
    }
  ]
}
```

## Validation Rules

Validation rejects active-contract drift, unsupported block shapes, fixed-section `key` or `title` fields, extra subsections without `key`, `title`, or `blocks`, non-string list items, `main_flows.flows[]` entries with `steps`, `core_components` that do not start with one `component_table`, and mechanisms outside module objects.

Mermaid blocks must follow the canonical authoring guidance and pass strict Mermaid CLI rendering when present.
