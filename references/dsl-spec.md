# create-structure-md 0.4.0 DSL 规范

## Package Shape

create-structure-md 0.4.0 package 由一个 `structure.manifest.json` 和六个固定 child JSON files 组成。`structure.manifest.json` 是入口。

Payload JSON files do not carry `dsl_version`; the manifest also does not include `dsl_version`.

Example `structure.manifest.json`:

```json
{
  "document": "chapters/00-document.json",
  "overview": "chapters/01-overview.json",
  "quick_start": "chapters/02-quick-start.json",
  "architecture_overview": "chapters/03-architecture-overview.json",
  "main_flows": "chapters/04-main-flows.json",
  "module_details": "chapters/05-module-details.json"
}
```

The manifest has exactly these six keys: `document`, `overview`, `quick_start`, `architecture_overview`, `main_flows`, and `module_details`.

## Document Metadata

The document metadata child file defines repository identity, output path, and summary.

Example `chapters/00-document.json`:

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

Blocks are section-local content units. Supported free block types are `text`, `unordered_list`, `ordered_list`, `table`, `mermaid`, and `code`.

Text block:

```json
{
  "type": "text",
  "content": "这个仓库把结构化输入渲染成人类优先的阅读指南。"
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
  "title": "验证到渲染",
  "diagram_type": "flowchart",
  "source": "flowchart LR\n  Manifest[Manifest] --> Validator[Validator]\n  Validator --> Renderer[Renderer]"
}
```

Code block:

```json
{
  "type": "code",
  "language": "c",
  "title": "初始化",
  "content": "easyflash_init();"
}
```

For code blocks, `title` is optional. List block `items` values are string arrays only.

## Overview

The overview child file contains fixed subsections for the rendered `### 概述` section. Fixed sections are renderer-owned and do not carry `key` or `title`.

Example `chapters/01-overview.json`:

```json
{
  "overview": {
    "repository_intro": {
      "blocks": [
        {
          "type": "text",
          "content": "示例仓库展示如何把 0.4.0 DSL 包渲染成结构说明文档。"
        }
      ]
    },
    "problems_solved": {
      "blocks": [
        {
          "type": "unordered_list",
          "items": [
            "帮助读者快速理解仓库职责",
            "把结构说明源数据与生成文档分开"
          ]
        }
      ]
    },
    "main_capabilities": {
      "blocks": [
        {
          "type": "unordered_list",
          "items": [
            "验证 0.4.0 DSL package",
            "渲染人类优先的 Markdown reader guide"
          ]
        }
      ]
    },
    "core_components": {
      "component_table": {
        "columns": ["组件", "职责", "主要路径"],
        "rows": [
          ["Manifest", "声明六个固定 child JSON files", "structure.manifest.json"],
          ["Chapters", "保存各章节源内容", "chapters/*.json"],
          ["Renderer", "生成 Markdown", "scripts/render_markdown.py"]
        ]
      },
      "blocks": [
        {
          "type": "text",
          "content": "核心组件表只描述读者理解仓库所需的最高层职责。"
        }
      ]
    },
    "extra_subsections": [
      {
        "key": "reading_notes",
        "title": "阅读提示",
        "blocks": [
          {
            "type": "text",
            "content": "先读入门，再进入深入解析。"
          }
        ]
      }
    ]
  }
}
```

## Quick Start

The quick start child file contains fixed subsections for the rendered `### 快速开始` section. `first_run.steps[]` is ordered by array position and must be non-empty.

Example `chapters/02-quick-start.json`:

```json
{
  "quick_start": {
    "usage_scenarios": {
      "blocks": [
        {
          "type": "unordered_list",
          "items": [
            "首次接触仓库时建立阅读地图",
            "修改 DSL 后验证并重新渲染文档"
          ]
        }
      ]
    },
    "setup": {
      "blocks": [
        {
          "type": "code",
          "language": "bash",
          "content": "python scripts/validate_structure.py package/structure.manifest.json --strict"
        }
      ]
    },
    "first_run": {
      "steps": [
        {
          "title": "验证 DSL",
          "blocks": [
            {
              "type": "code",
              "language": "bash",
              "content": "python scripts/validate_structure.py package/structure.manifest.json --strict"
            }
          ]
        },
        {
          "title": "渲染文档",
          "blocks": [
            {
              "type": "code",
              "language": "bash",
              "content": "python scripts/render_markdown.py package/structure.manifest.json"
            }
          ]
        }
      ],
      "blocks": [
        {
          "type": "text",
          "content": "第一次运行只需要验证入口 manifest 并渲染同一个入口。"
        }
      ]
    },
    "minimal_example": {
      "blocks": [
        {
          "type": "code",
          "language": "json",
          "content": "{\"document\":\"chapters/00-document.json\"}"
        }
      ]
    },
    "expected_result": {
      "blocks": [
        {
          "type": "text",
          "content": "渲染器生成由固定章节组成的 Markdown 结构说明。"
        }
      ]
    },
    "extra_subsections": []
  }
}
```

## Architecture Overview

The architecture overview child file contains fixed subsections for the rendered `### 架构概述` section. Required table structures are `layers.layer_table.rows` and `module_map.module_table.rows`.

Example `chapters/03-architecture-overview.json`:

```json
{
  "architecture_overview": {
    "architecture_summary": {
      "blocks": [
        {
          "type": "text",
          "content": "仓库以 manifest 为入口，把章节 JSON 交给验证器和渲染器处理。"
        },
        {
          "type": "mermaid",
          "title": "DSL 处理路径",
          "diagram_type": "flowchart",
          "source": "flowchart LR\n  Package[DSL package] --> Validator[Validator]\n  Package --> Renderer[Renderer]\n  Renderer --> Markdown[Markdown]"
        }
      ]
    },
    "layers": {
      "layer_table": {
        "columns": ["层", "职责", "代表路径"],
        "rows": [
          ["Source package", "保存 manifest 和章节 JSON", "package/"],
          ["Validation", "检查 DSL contract", "scripts/validate_structure.py"],
          ["Rendering", "生成 Markdown", "scripts/render_markdown.py"]
        ]
      },
      "blocks": [
        {
          "type": "text",
          "content": "分层描述应停留在仓库级职责，不展开模块内部机制。"
        }
      ]
    },
    "module_map": {
      "module_table": {
        "columns": ["模块", "职责", "位置"],
        "rows": [
          ["Validator", "拒绝无效 DSL", "scripts/validate_structure.py"],
          ["Renderer", "输出 Markdown", "scripts/render_markdown.py"]
        ]
      },
      "blocks": []
    },
    "repository_layout": {
      "blocks": [
        {
          "type": "table",
          "columns": ["路径", "角色"],
          "rows": [
            ["chapters/", "固定章节 JSON"],
            ["structure.manifest.json", "package 入口"]
          ]
        }
      ]
    },
    "extra_subsections": []
  }
}
```

## Main Flows

The main flows child file contains reader-facing behavior paths. `main_flows.flows[]` must be non-empty and has no `steps` field.

Example `chapters/04-main-flows.json`:

```json
{
  "main_flows": {
    "flow_overview": {
      "blocks": [
        {
          "type": "text",
          "content": "主线流程说明读者关心的任务如何跨组件完成，而不是逐函数调用链。"
        }
      ]
    },
    "flows": [
      {
        "title": "验证并渲染结构说明",
        "purpose": "确认 DSL package 有效并生成 Markdown。",
        "entry": {
          "name": "structure.manifest.json",
          "location": "package/structure.manifest.json"
        },
        "blocks": [
          {
            "type": "text",
            "content": "使用者把 manifest 交给验证器，修复源 JSON 后再交给渲染器。"
          },
          {
            "type": "mermaid",
            "title": "验证与渲染",
            "diagram_type": "sequenceDiagram",
            "source": "sequenceDiagram\n  participant User\n  participant Validator\n  participant Renderer\n  User->>Validator: Validate manifest\n  User->>Renderer: Render manifest"
          }
        ]
      }
    ],
    "extra_subsections": []
  }
}
```

## Module Details

Module headings come from `module_details.modules[].name`. `module_details.modules[]` must be non-empty. Mechanisms live inside the owning module object.

Example `chapters/05-module-details.json`:

```json
{
  "module_details": {
    "intro_blocks": [
      {
        "type": "text",
        "content": "模块详解按责任单元组织，不按文件逐个罗列。"
      }
    ],
    "modules": [
      {
        "name": "Validator",
        "location": "scripts/validate_structure.py",
        "purpose": "检查 manifest 和 child JSON files 是否符合 0.4.0 contract。",
        "blocks": [
          {
            "type": "unordered_list",
            "items": [
              "验证入口始终是 structure.manifest.json",
              "错误应指向可修复的源 JSON"
            ]
          }
        ],
        "mechanisms": [
          {
            "title": "Strict validation",
            "blocks": [
              {
                "type": "text",
                "content": "严格模式拒绝未知字段、错误 block shape 和不符合章节约束的结构。"
              }
            ]
          }
        ],
        "extra_subsections": [
          {
            "key": "validator_risks",
            "title": "修改风险",
            "blocks": [
              {
                "type": "text",
                "content": "修改 schema 约束时要同步更新 DSL spec 和 authoring guide。"
              }
            ]
          }
        ]
      }
    ],
    "extra_subsections": []
  }
}
```

## Extra Subsections

Extra subsections are nested arrays inside fixed child files or module objects, not a separate child file. Each extra subsection carries `key`, `title`, and `blocks`.

Example nested extra subsection:

```json
{
  "key": "maintenance_notes",
  "title": "维护提示",
  "blocks": [
    {
      "type": "text",
      "content": "修改 DSL 后先验证源 JSON，再重新渲染 Markdown。"
    }
  ]
}
```

Extra subsections render after fixed content in array order at the level where they are declared.

## Validation Rules

Validation rejects:

- manifests that do not have exactly the six fixed keys;
- any manifest or payload JSON file containing `dsl_version`;
- missing fixed sections;
- unsupported block shapes or wrong block fields;
- list block `items` values that are not string arrays;
- missing `overview.core_components.component_table.rows`;
- missing `architecture_overview.layers.layer_table.rows`;
- missing `architecture_overview.module_map.module_table.rows`;
- empty `quick_start.first_run.steps`;
- empty `main_flows.flows`;
- any `main_flows.flows[]` entry with `steps`;
- empty `module_details.modules`;
- mechanisms outside owning module objects;
- fixed sections carrying renderer-owned `key` or `title` fields;
- extra subsections without `key`, `title`, or `blocks`;
- process metadata such as subagent names, command transcripts, raw scan logs, or rejected drafts.

Mermaid blocks must follow the canonical authoring guidance and pass strict Mermaid CLI rendering when present.
