# create-structure-md 0.4.0 DSL 规范

## Package Shape

create-structure-md 0.4.0 package 由一个 `structure.manifest.json` 和 manifest 引用的 child JSON files 组成。`structure.manifest.json` 和 referenced child JSON files 是权威源；rendered Markdown 是 generated output。

Payload JSON files do not carry `dsl_version`; the manifest also does not include `dsl_version`.

Process records, subagent reports, command transcripts, rejected drafts, scan logs, repository-understanding notes, and other process metadata stay outside JSON.

Example upgraded eight-field `structure.manifest.json`:

```json
{
  "document": "chapters/00-document.json",
  "overview": "chapters/01-overview.json",
  "quick_start": "chapters/02-quick-start.json",
  "architecture_overview": "chapters/03-architecture-overview.json",
  "main_flow_overview": "chapters/04-main-flow-overview.json",
  "main_flow_details": [
    "chapters/04-main-flow-details/validate-and-render.json"
  ],
  "module_overview": "chapters/05-module-overview.json",
  "module_details": [
    "chapters/05-module-details/validator.json"
  ]
}
```

`main_flow_details` and `module_details` are non-empty arrays.

Detail keys are inferred from file stems.

Detail JSON does not repeat the inferred key.

Detail file stems match `^[a-z0-9][a-z0-9_-]*$`.

Rejected old active 0.4.0 shape: `main_flows`, `chapters/04-main-flows.json`, one aggregate `chapters/05-module-details.json`, `intro_blocks`, `modules[]`, `module_details.modules`, and `generated_module_object`.

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
  "language": "bash",
  "title": "验证",
  "content": "python scripts/validate_structure.py package/structure.manifest.json --strict"
}
```

For code blocks, `title` is optional. List block `items` values are string arrays only.

## Overview

The overview child file contains fixed subsections for the rendered `### 概述` section. Fixed sections are renderer-owned and do not carry `key` or `title`.

`overview.core_components.component_table` is a semantic fixed-table object, not a generic free block table. `component_table.rows[]` objects contain exactly `component`, `role`, and `location`.

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
        "rows": [
          {
            "component": "Manifest",
            "role": "声明 child JSON files",
            "location": "structure.manifest.json"
          },
          {
            "component": "Validator",
            "role": "检查 0.4.0 contract",
            "location": "scripts/validate_structure.py"
          },
          {
            "component": "Renderer",
            "role": "生成 Markdown",
            "location": "scripts/render_markdown.py"
          }
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
          "content": "{\n  \"document\": \"chapters/00-document.json\",\n  \"overview\": \"chapters/01-overview.json\",\n  \"quick_start\": \"chapters/02-quick-start.json\",\n  \"architecture_overview\": \"chapters/03-architecture-overview.json\",\n  \"main_flow_overview\": \"chapters/04-main-flow-overview.json\",\n  \"main_flow_details\": [\"chapters/04-main-flow-details/validate-and-render.json\"],\n  \"module_overview\": \"chapters/05-module-overview.json\",\n  \"module_details\": [\"chapters/05-module-details/validator.json\"]\n}"
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

The architecture overview child file contains fixed subsections for the rendered `### 架构概述` section. Required table structures are `layers.layer_table.rows` and `module_map.module_table.rows`. These are semantic fixed-table objects, not generic free block tables.

`layers.layer_table.rows[]` objects contain exactly `layer`, `role`, and `location`. `module_map.module_table.rows[]` objects contain exactly `module`, `role`, `layer`, and `location`.

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
        "rows": [
          {
            "layer": "Source package",
            "role": "保存 manifest 和章节 JSON",
            "location": "package/"
          },
          {
            "layer": "Validation",
            "role": "检查 DSL contract",
            "location": "scripts/validate_structure.py"
          },
          {
            "layer": "Rendering",
            "role": "生成 Markdown",
            "location": "scripts/render_markdown.py"
          }
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
        "rows": [
          {
            "module": "Validator",
            "role": "拒绝无效 DSL",
            "layer": "Validation",
            "location": "scripts/validate_structure.py"
          },
          {
            "module": "Renderer",
            "role": "输出 Markdown",
            "layer": "Rendering",
            "location": "scripts/render_markdown.py"
          }
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

## Main Flow Overview

The main flow overview is synthesized after every file in `main_flow_details` passes authoring and separate adversarial review.

`main_flow_overview` is a fixed table artifact. It does not contain `blocks` or `extra_subsections`.

Neither overview file contains detail prose, Mermaid, code, examples, or process metadata.

Overview rows match detail arrays in count and order.

Example `chapters/04-main-flow-overview.json`:

```json
{
  "main_flow_overview": {
    "flow_table": {
      "rows": [
        {
          "flow": "验证并渲染结构说明",
          "purpose": "确认 DSL package 有效并生成 Markdown。",
          "entry": "structure.manifest.json",
          "location": "package/structure.manifest.json",
          "anchor": "验证并渲染结构说明"
        }
      ]
    }
  }
}
```

## Main Flow Detail

Main-flow detail files describe reader-facing behavior paths, not call-chain dumps. Each file is authored by exactly one assigned main-flow authoring subagent and reviewed by a separate adversarial review subagent.

The detail key is inferred from the file stem under `chapters/04-main-flow-details/<flow-key>.json`; the JSON does not repeat that key.

Example `chapters/04-main-flow-details/validate-and-render.json`:

```json
{
  "title": "验证并渲染结构说明",
  "purpose": "确认 DSL package 有效并生成 Markdown。",
  "reader_goal": "读者想知道一个 DSL package 如何从验证进入渲染。",
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
  ],
  "extra_subsections": [
    {
      "key": "reader_checks",
      "title": "读者检查点",
      "blocks": [
        {
          "type": "unordered_list",
          "items": [
            "先修复源 JSON",
            "再重新渲染 Markdown"
          ]
        }
      ]
    }
  ]
}
```

## Module Overview

The module overview is synthesized after every file in `module_details` passes authoring and separate adversarial review.

`module_overview` is a fixed table artifact. It does not contain `blocks` or `extra_subsections`.

Neither overview file contains detail prose, Mermaid, code, examples, or process metadata.

Overview rows match detail arrays in count and order.

Example `chapters/05-module-overview.json`:

```json
{
  "module_overview": {
    "module_table": {
      "rows": [
        {
          "module": "Validator",
          "purpose": "检查 manifest 和 child JSON files 是否符合 0.4.0 contract。",
          "location": "scripts/validate_structure.py",
          "anchor": "Validator"
        }
      ]
    }
  }
}
```

## Module Detail

Module detail files describe responsibility units, not source-file listings. Each file is authored by exactly one assigned module authoring subagent and reviewed by a separate adversarial review subagent.

The detail key is inferred from the file stem under `chapters/05-module-details/<module-key>.json`; the JSON does not repeat that key.

Example `chapters/05-module-details/validator.json`:

```json
{
  "name": "Validator",
  "location": "scripts/validate_structure.py",
  "purpose": "检查 manifest 和 child JSON files 是否符合 0.4.0 contract。",
  "responsibilities": [
    "验证入口始终是 structure.manifest.json",
    "错误应指向可修复的源 JSON"
  ],
  "blocks": [
    {
      "type": "text",
      "content": "Validator 负责把 manifest、章节 JSON、语义规则和 Mermaid 渲染门禁汇总成可操作的诊断。"
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
```

## Module Details

This heading names the rendered Chapter 5 detail family. The executable DSL contract for each individual file is the singular `Module Detail` object above.

## Extra Subsections

Extra subsections are nested arrays inside fixed child files or detail objects, not a separate child file. Each extra subsection carries `key`, `title`, and `blocks`.

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

- manifests that do not have exactly the upgraded eight fields;
- manifests containing the rejected old active 0.4.0 shape `main_flows`, `chapters/04-main-flows.json`, `module_details.modules`, `modules[]`, `intro_blocks`, or `generated_module_object`;
- any manifest or payload JSON file containing `dsl_version`;
- missing fixed sections;
- unsupported block shapes or wrong block fields;
- list block `items` values that are not string arrays;
- missing `overview.core_components.component_table.rows`;
- `overview.core_components.component_table.rows[]` objects without exactly `component`, `role`, and `location`;
- missing `architecture_overview.layers.layer_table.rows`;
- `architecture_overview.layers.layer_table.rows[]` objects without exactly `layer`, `role`, and `location`;
- missing `architecture_overview.module_map.module_table.rows`;
- `architecture_overview.module_map.module_table.rows[]` objects without exactly `module`, `role`, `layer`, and `location`;
- empty `quick_start.first_run.steps`;
- empty `main_flow_details` or `module_details` arrays;
- detail file stems that do not match `^[a-z0-9][a-z0-9_-]*$`;
- detail JSON that repeats the inferred key;
- `main_flow_overview` rows that do not match `main_flow_details` in count and order;
- `module_overview` rows that do not match `module_details` in count and order;
- `main_flow_overview` or `module_overview` containing `blocks` or `extra_subsections`;
- `main_flow_overview` or `module_overview` containing detail prose, Mermaid, code, examples, or process metadata;
- fixed sections carrying renderer-owned `key` or `title` fields;
- extra subsections without `key`, `title`, or `blocks`;
- process metadata such as subagent names, command transcripts, raw scan logs, scan logs, or rejected drafts.

Mermaid blocks must follow the canonical authoring guidance and pass strict Mermaid CLI rendering when present.
