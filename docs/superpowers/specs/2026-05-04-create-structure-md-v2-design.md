# create-structure-md V2 Design

## Summary

V2 upgrades create-structure-md from a fixed 9-chapter Markdown renderer into a clearer structure-document renderer while preserving the current skill boundary: this skill consumes prepared DSL content and does not analyze repositories.

The primary changes are:

- Evidence support blocks are hidden by default in final Markdown.
- Chapter 4 is rebuilt around module scope, configuration, dependencies, data objects, public interfaces, internal mechanism, and known limitations.
- Mermaid diagrams receive an auditable readability review artifact before strict validation, plus rendered diagram completeness checks.
- Section 5.2 runtime unit tables are simplified.
- Mermaid validator files and Mermaid rule files are not changed in this phase.

## Goals

- Make generated Markdown easier to read by removing inline evidence noise by default.
- Make Chapter 4 explain usable module structure instead of generic responsibility summaries.
- Preserve evidence references inside DSL for validation, traceability, and upstream tools.
- Keep create-structure-md separate from future repository-analysis skills.
- Improve Mermaid readability and diagram rendering completeness before final acceptance without changing Mermaid validation implementation.
- Keep the V2 migration focused enough to implement in one plan.

## Non-Goals

- Do not add repository analysis to this skill.
- Do not infer missing requirements or missing design content from source code.
- Do not add an evidence appendix mode.
- Do not modify `scripts/validate_mermaid.py`.
- Do not modify `references/mermaid-rules.md`.
- Do not replace strict Mermaid validation with static-only validation.
- Do not generate Word, PDF, image exports, or multiple output documents.

## Product Boundary

The skill continues to consume prepared structured content:

```text
repo-analysis skill or human analysis -> structure DSL -> create-structure-md -> Markdown
```

`SKILL.md` must continue to state that create-structure-md does not perform repository analysis. V2 only makes the DSL and renderer better at expressing and rendering structure supplied by another actor.

## DSL Version

V2 is a breaking DSL shape change.

The only supported DSL version is `0.2.0`. The V2 schema, validator, renderer, examples, and tests target `0.2.0` only.

Inputs with any `dsl_version` other than `0.2.0` must fail fast before rendering. The error must state that V1 DSL is not supported by the V2 renderer and that the input must be migrated to `0.2.0`.

This phase does not implement a migration tool. Legacy V1 examples may be retained only as rejected fixtures.

## Evidence Rendering

V2 adds a final Markdown evidence rendering switch as a renderer CLI option. This option must not be stored in DSL instances because the DSL should remain document content, not rendering policy.

Supported modes:

| Mode | Behavior |
| --- | --- |
| `hidden` | Default. Do not render generated evidence support blocks such as `支持数据（...）`. |
| `inline` | Render evidence support blocks near the content that references them, preserving V1 behavior. |

`appendix` mode is intentionally not supported.

### CLI Shape

Add a renderer option:

```text
python3 scripts/render_markdown.py structure.dsl.json --evidence-mode hidden
python3 scripts/render_markdown.py structure.dsl.json --evidence-mode inline
```

If `--evidence-mode` is absent, the renderer defaults to `hidden`.

### Hidden Mode Semantics

`hidden` mode fully suppresses evidence-node rendering in final Markdown. This includes rendered evidence, traceability, source snippet blocks, and table-row support-data groups generated from those nodes. It does not hide structural facts in normal content.

Markdown may still show:

- file paths
- function names
- interface prototypes
- parameters
- return values
- configuration values
- dependency names
- data object names
- known limitations
- Mermaid diagrams

DSL fields such as `evidence_refs`, `traceability_refs`, and `source_snippet_refs` remain available for validation and upstream tooling. They are not rendered in final Markdown when mode is `hidden`.

## Chapter 4 Design

V2 replaces the V1 module subsection template.

V2 intentionally overrides the V1 rule that Chapter 4 must not center on function prototypes or parameter lists. In V2, public function and command-line interfaces are first-class module structure. This allowance is limited to public interfaces listed under `public_interfaces`; V2 still does not require documenting arbitrary private helper functions or full internal call chains.

Remove the V1 Chapter 4 subsections:

- module responsibilities
- external capability summary
- provided capability table
- standalone internal structure diagram section
- supplement section as the primary extension mechanism

Each module renders seven fixed subsections:

```text
4.x.1 模块定位与源码/产物范围
4.x.2 配置
4.x.3 依赖
4.x.4 数据对象
4.x.5 对外接口
4.x.6 实现机制说明
4.x.7 已知限制
```

The renderer must output these subsections in this exact order.

### Chapter 4 and Chapter 6 Split

Chapter 4 renders module-local configuration, dependencies, and data objects. These items explain one module's boundary and behavior.

Chapter 6 renders system-level configuration, dependencies, and data artifacts. These items explain cross-module, whole-skill, installation, or runtime-environment concerns.

Use this rule of thumb:

- If an item applies to exactly one module and helps explain that module's contract, place it in Chapter 4.
- If an item is shared by multiple modules, affects the whole workflow, represents an external runtime environment, or describes final/installed artifacts at system scope, place it in Chapter 6.
- If the same underlying object appears in both chapters, Chapter 4 describes module-local use and Chapter 6 describes the system-level relationship.
- The renderer must not try to deduplicate Chapter 4 and Chapter 6 automatically.

### Chapter 4 DSL

`module_design.modules[]` must use this V2 shape:

```json
{
  "module_id": "MOD-MARKDOWN-RENDERER",
  "name": "Markdown 渲染器模块",
  "module_kind": "renderer",
  "summary": "说明该模块的整体定位。",
  "confidence": "observed",

  "source_scope": {
    "summary": "说明该模块在系统中的定位和覆盖范围。",
    "primary_files": [
      {
        "path": "scripts/render_markdown.py",
        "role": "Markdown 渲染器实现",
        "language": "python",
        "notes": ""
      }
    ],
    "consumed_inputs": [
      "structure.dsl.json"
    ],
    "owned_outputs": [
      "document.output_file 指定的 Markdown 文件"
    ],
    "out_of_scope": [
      "不负责仓库分析",
      "不负责推理缺失设计内容"
    ]
  },

  "configuration": {
    "summary": "说明该模块使用的模块级参数、宏定义、常量、默认值或运行配置。",
    "parameters": {
      "rows": [
        {
          "parameter_id": "MPARAM-RENDER-OUTPUT-DIR",
          "prototype": "--output-dir",
          "value_or_default": "当前目录",
          "value_source": "default",
          "meaning": "指定最终 Markdown 文件写入目录。",
          "confidence": "observed",
          "evidence_refs": []
        }
      ],
      "not_applicable_reason": ""
    }
  },

  "dependencies": {
    "summary": "说明该模块依赖的运行时、库、工具或外部能力。",
    "rows": [
      {
        "dependency_id": "MDEP-RENDER-PYTHON",
        "name": "Python 3",
        "dependency_type": "runtime",
        "usage_relation": "uses",
        "target_module_id": "",
        "target_data_id": "",
        "system_dependency_ref": "SYSDEP-PYTHON",
        "required_for": "运行渲染脚本",
        "failure_behavior": "命令无法执行",
        "confidence": "observed",
        "evidence_refs": []
      }
    ],
    "not_applicable_reason": ""
  },

  "data_objects": {
    "summary": "说明该模块读取、写入或拥有的数据对象和结构产物。",
    "rows": [
      {
        "data_id": "DATA-STRUCTURE-DSL",
        "name": "structure.dsl.json",
        "data_type": "json",
        "role": "渲染输入",
        "producer": "Codex 或上游分析 skill",
        "consumer": "Markdown 渲染器",
        "shape_or_contract": "符合 structure-design.schema.json",
        "confidence": "observed",
        "evidence_refs": []
      }
    ],
    "not_applicable_reason": ""
  },

  "public_interfaces": {
    "summary": "说明模块对外暴露的函数接口、命令行接口、schema 契约或文档契约。",
    "interface_index": {
      "rows": [
        {
          "interface_id": "IFACE-RENDER-CLI",
          "interface_name": "render_markdown.py",
          "interface_type": "command_line",
          "description": "把通过校验的 DSL 渲染为最终 Markdown 文件。"
        }
      ]
    },
    "interfaces": [
      {
        "interface_id": "IFACE-RENDER-CLI",
        "interface_name": "render_markdown.py",
        "interface_type": "command_line",
        "prototype": "python3 scripts/render_markdown.py structure.dsl.json --output-dir <dir>",
        "purpose": "把 DSL 渲染为最终 Markdown 文件。",
        "location": {
          "file_path": "scripts/render_markdown.py",
          "symbol": "main",
          "line_start": null,
          "line_end": null
        },
        "parameters": {
          "rows": [
            {
              "parameter_name": "structure.dsl.json",
              "parameter_type": "path",
              "description": "待渲染的 DSL JSON 文件路径。",
              "direction": "input"
            }
          ],
          "not_applicable_reason": ""
        },
        "return_values": {
          "rows": [
            {
              "return_name": "exit_code",
              "return_type": "int",
              "description": "0 表示成功，非 0 表示失败。",
              "condition": "命令结束时返回"
            }
          ],
          "not_applicable_reason": ""
        },
        "execution_flow_diagram": {
          "id": "MER-IFACE-RENDER-CLI-FLOW",
          "kind": "interface_execution_flow",
          "title": "render_markdown.py 执行流程图",
          "diagram_type": "flowchart",
          "description": "展示 CLI 从读取 DSL 到写出 Markdown 的流程。",
          "source": "flowchart TD\n  A[\"Parse args\"] --> B[\"Load DSL\"]\n  B --> C[\"Render Markdown\"]\n  C --> D[\"Write output\"]",
          "confidence": "observed"
        },
        "side_effects": [
          "读取 DSL 文件",
          "写入 Markdown 输出文件"
        ],
        "error_behavior": [
          {
            "condition": "DSL 文件不可读",
            "behavior": "报告错误并返回非 0 退出码"
          }
        ],
        "consumers": [
          "Codex",
          "仓库维护者"
        ],
        "confidence": "observed",
        "evidence_refs": []
      }
    ],
    "not_applicable_reason": ""
  },

  "internal_mechanism": {
    "summary": "说明该模块内部如何完成职责。该节不是补充说明，而是第四章解释模块内部机制的核心区域。",
    "mechanism_index": {
      "rows": [
        {
          "mechanism_id": "MECH-RENDER-CHAPTER-DISPATCH",
          "mechanism_name": "固定章节调度机制",
          "purpose": "按固定章节顺序组织全文 Markdown 渲染。",
          "input": "通过校验的 DSL document 和支持数据上下文",
          "processing": "按固定顺序调用各章渲染逻辑并拼接输出。",
          "output": "完整 Markdown 字符串",
          "structural_significance": "决定文档章节顺序稳定，并让每章渲染逻辑保持可测试边界。",
          "related_anchors": [
            {
              "anchor_type": "file_path",
              "value": "scripts/render_markdown.py",
              "reason": ""
            },
            {
              "anchor_type": "interface_id",
              "value": "IFACE-RENDER-CLI",
              "reason": ""
            },
            {
              "anchor_type": "data_id",
              "value": "DATA-STRUCTURE-DSL",
              "reason": ""
            }
          ],
          "confidence": "observed",
          "evidence_refs": [],
          "traceability_refs": [],
          "source_snippet_refs": []
        }
      ],
      "not_applicable_reason": ""
    },
    "mechanism_details": [
      {
        "mechanism_id": "MECH-RENDER-CHAPTER-DISPATCH",
        "blocks": [
          {
            "block_id": "MECH-RENDER-TEXT",
            "block_type": "text",
            "title": "固定章节调度机制说明",
            "text": "渲染器读取 DSL 后构建渲染上下文，再按固定章节顺序生成 Markdown。第四章由模块设计数据驱动，依次输出范围、配置、依赖、数据对象、接口、实现机制和已知限制。",
            "confidence": "observed",
            "evidence_refs": [],
            "traceability_refs": [],
            "source_snippet_refs": []
          },
          {
            "block_id": "MECH-RENDER-DIAGRAM",
            "block_type": "diagram",
            "title": "固定章节调度机制图",
            "confidence": "observed",
            "evidence_refs": [],
            "traceability_refs": [],
            "source_snippet_refs": [],
            "diagram": {
              "id": "MER-MECH-RENDER-FLOW",
              "kind": "internal_mechanism",
              "title": "固定章节调度机制图",
              "diagram_type": "flowchart",
              "description": "展示渲染器如何组织章节输出。",
              "source": "flowchart TD\n  A[\"Load DSL\"] --> B[\"Build context\"]\n  B --> C[\"Render chapters\"]\n  C --> D[\"Write Markdown\"]",
              "confidence": "observed"
            }
          },
          {
            "block_id": "MECH-RENDER-TABLE",
            "block_type": "table",
            "title": "关键阶段",
            "confidence": "observed",
            "evidence_refs": [],
            "traceability_refs": [],
            "source_snippet_refs": [],
            "table": {
              "id": "TBL-MECH-RENDER-STAGES",
              "title": "关键阶段",
              "columns": [
                { "key": "stage", "title": "阶段" },
                { "key": "description", "title": "说明" }
              ],
              "rows": [
                {
                  "stage": "上下文构建",
                  "description": "收集 DSL 中的结构信息和支持数据索引。"
                },
                {
                  "stage": "章节渲染",
                  "description": "按固定章节顺序调用对应渲染逻辑。"
                }
              ]
            }
          }
        ]
      }
    ],
    "not_applicable_reason": ""
  },

  "known_limitations": {
    "summary": "说明该模块当前已知的结构、运行、渲染或维护限制。",
    "rows": [
      {
        "limitation_id": "LIMIT-MERMAID-LABEL-LENGTH",
        "limitation": "Mermaid 图中长标签在 Markdown 渲染后可能显示不完整。",
        "impact": "图可通过语法校验，但视觉可读性不足。",
        "mitigation_or_next_step": "strict check 前派子代理审阅图的可读性，压缩标签、换行或调整节点布局。",
        "confidence": "observed",
        "evidence_refs": []
      }
    ],
    "not_applicable_reason": ""
  },

  "evidence_refs": [],
  "traceability_refs": [],
  "source_snippet_refs": [],
  "notes": []
}
```

### Module Kind

`module_kind` must be an enum. Initial values:

- `documentation_contract`
- `schema_contract`
- `validator`
- `renderer`
- `installer`
- `test_suite`
- `library`
- `other`

V2 does not require module-kind-specific rendering templates. The enum exists so upstream analysis skills can classify modules consistently and future versions can specialize rendering if needed.

If `module_kind` is `other`, the module must provide non-empty `module_kind_reason`.

### Source Scope Rendering

Render `source_scope` as:

- summary paragraph
- primary files table
- consumed inputs list
- owned outputs list
- out-of-scope list

Do not include `primary_directories`.

### Configuration Rendering

Render module-level parameters as:

| 原型 | 当前/默认值 | 来源 | 含义 |
| --- | --- | --- | --- |

`parameter_id`, confidence, and evidence refs are internal DSL fields and are not shown by default.

`value_source` is an enum:

- `default`
- `cli_argument`
- `environment`
- `constant`
- `config_file`
- `computed`
- `inferred`
- `unknown`

### Dependencies Rendering

Render dependencies as:

| 名称 | 类型 | 关系 | 用途 | 失败行为 |
| --- | --- | --- | --- | --- |

`dependency_id`, target refs, `system_dependency_ref`, confidence, and evidence refs are internal DSL fields and are not shown by default.

`dependency_id` remains globally unique across module-level and system-level dependencies. Module-local dependencies should use an `MDEP-...` prefix, and Chapter 6 system-level dependencies should use a `SYSDEP-...` prefix. If a module dependency corresponds to a system-level dependency, set `system_dependency_ref` to the Chapter 6 dependency ID instead of reusing the same `dependency_id`.

The Chapter 6 system dependency collection is `$.configuration_data_dependencies.dependencies.rows[]`. Each row in that collection must have a globally unique `dependency_id`. `system_dependency_ref` must reference one of those Chapter 6 `dependency_id` values.

`dependency_type` is an enum:

- `runtime`
- `library`
- `tool`
- `schema_contract`
- `documentation_contract`
- `dsl_contract`
- `internal_module`
- `data_object`
- `filesystem`
- `external_service`
- `test_fixture`
- `other`

`usage_relation` is an enum:

- `reads`
- `writes`
- `validates_against`
- `renders`
- `invokes`
- `imports`
- `tests`
- `produces`
- `consumes`
- `uses`
- `other`

### Data Objects Rendering

Render data objects as:

| 名称 | 类型 | 角色 | 生产方 | 消费方 | 结构/契约 |
| --- | --- | --- | --- | --- | --- |

`data_id`, confidence, and evidence refs are internal DSL fields and are not shown by default.

### Public Interfaces Rendering

Render public interfaces in two layers.

First render a module-level interface list:

| 接口名称 | 接口功能描述 | 接口类型 |
| --- | --- | --- |

Then render one detail section per interface:

Executable interface types render:

- prototype
- purpose
- location
- parameter table
- return value table
- local Mermaid execution flow diagram
- side effects
- error behavior
- consumers

Contract interface types render:

- purpose
- location
- contract scope
- contract location
- required items
- constraints, when present
- consumers
- validation behavior

Interface detail sections render in `public_interfaces.interface_index.rows[]` order. `public_interfaces.interfaces[]` is a lookup collection keyed by `interface_id`; its physical array order does not control rendering.

`interface_type` is an enum:

- `command_line`
- `function`
- `method`
- `library_api`
- `schema_contract`
- `dsl_contract`
- `document_contract`
- `configuration_contract`
- `data_contract`
- `test_fixture`
- `workflow`
- `other`

Executable interface types are `command_line`, `function`, `method`, `library_api`, and `workflow`.

Contract interface types are `schema_contract`, `dsl_contract`, `document_contract`, `configuration_contract`, `data_contract`, and `test_fixture`.

`other` requires `interface_type_reason`.

Location shape:

```json
{
  "file_path": "scripts/render_markdown.py",
  "symbol": "main",
  "line_start": null,
  "line_end": null
}
```

`file_path` is required. `symbol`, `line_start`, and `line_end` are optional. `line_start` and `line_end` may be `null`; if one line value is present, both must be present. Do not use `line_start: 1` and `line_end: 1` as an unknown placeholder. That range is allowed only when evidence proves the target is actually on line 1.

If `confidence` is `observed` and `interface_type` is `function` or `method`, validation should warn unless `symbol` or a line range is provided.

Contract interface object:

```json
{
  "contract": {
    "contract_scope": "说明契约覆盖什么。",
    "contract_location": "schemas/structure-design.schema.json#/properties/module_design",
    "required_items": ["module_id", "name", "source_scope"],
    "constraints": ["模块对象必须能渲染为第四章七个固定小节。"],
    "consumers": ["validate_dsl.py", "render_markdown.py"],
    "validation_behavior": "违反契约时 validate_dsl.py 失败。"
  }
}
```

Parameter table:

| 参数名 | 参数类型 | 参数描述 | 输入/输出 |
| --- | --- | --- | --- |

Return value table:

| 返回名 | 返回类型 | 描述 | 条件 |
| --- | --- | --- | --- |

The execution flow diagram is stored locally on executable interface objects as `execution_flow_diagram`. It is not routed through supplemental diagram fields. `execution_flow_diagram.source` is required and must be non-empty for executable interfaces.

### Internal Mechanism Rendering

Render `internal_mechanism` as the primary Chapter 4 section for explaining how the module works internally. It is not a miscellaneous notes section.

The renderer outputs:

- summary paragraph
- mechanism index table
- one mechanism detail subsection for each mechanism
- each mechanism detail's content blocks in DSL order
- `not_applicable_reason` only when summary, mechanism index, and details are all empty

Mechanism detail blocks use the reusable content block module.

The mechanism index table renders:

| 机制 | 用途 | 输入 | 处理方式 | 输出 | 结构意义 |
| --- | --- | --- | --- | --- | --- |

`mechanism_id`, related anchors, confidence, and support refs are internal DSL fields and are not shown by default.

`mechanism_details[]` must correspond one-to-one with `mechanism_index.rows[]` by `mechanism_id`. Each mechanism detail renders as a child subsection under `4.x.6`.

Mechanism detail subsections render in `mechanism_index.rows[]` order. `mechanism_details[]` is a lookup collection keyed by `mechanism_id`; its physical array order does not control rendering.

`related_anchors[]` uses typed anchors:

```json
[
  {
    "anchor_type": "interface_id",
    "value": "IFACE-RENDER-CLI",
    "reason": ""
  }
]
```

`anchor_type` is an enum:

- `file_path`
- `module_id`
- `interface_id`
- `data_id`
- `dependency_id`
- `parameter_id`
- `diagram_id`
- `table_id`
- `source_snippet_id`
- `evidence_id`
- `traceability_id`
- `other`

Every anchor must have non-empty `anchor_type` and `value`. `other` anchors must also have non-empty `reason`.

Anchor resolution:

| Anchor type | Validation target |
| --- | --- |
| `file_path` | Non-empty `value` only. Do not check file-system existence and do not resolve against repository files. |
| `module_id` | Any `module_id` in module design or module inventory. |
| `interface_id` | Any `public_interfaces.interfaces[].interface_id` or matching interface index ID. |
| `data_id` | Any Chapter 4 `data_objects.rows[].data_id`. |
| `dependency_id` | Any Chapter 4 or Chapter 6 `dependency_id`. |
| `parameter_id` | Any Chapter 4 `configuration.parameters.rows[].parameter_id`. |
| `diagram_id` | Any Mermaid `diagram.id` collected by the shared expected diagram collector. |
| `table_id` | Any reusable content block `table.id` or existing DSL table ID. |
| `source_snippet_id` | Any `source_snippets[].id`. |
| `evidence_id` | Any `evidence[].id`. |
| `traceability_id` | Any `traceability[].id`. |
| `other` | Non-empty `value` and non-empty `reason`; no automatic reference resolution. |

### Known Limitations Rendering

Render known limitations as:

| 限制 | 影响 | 缓解/后续 |
| --- | --- | --- |

`limitation_id`, confidence, and evidence refs are internal DSL fields and are not shown by default.

## Content Blocks

V2 introduces reusable content blocks for sections where Codex needs freedom to combine prose, diagrams, and tables.

Initial content-block users:

- `module_design.modules[].internal_mechanism.mechanism_details[].blocks[]`
- `structure_issues_and_suggestions.blocks[]`

Content blocks are rendered in DSL order. They are not raw Markdown. The renderer owns Markdown headings, Mermaid fences, and table formatting.

The same content-block schema definition, semantic validator helper, and renderer helper must be used by Chapter 4 internal mechanism details and Chapter 9 structure issues. Do not implement separate Chapter 4 and Chapter 9 block renderers with divergent behavior.

Every content block has common metadata:

```json
{
  "confidence": "observed",
  "evidence_refs": [],
  "traceability_refs": [],
  "source_snippet_refs": []
}
```

Hidden evidence mode suppresses rendering of these refs. Inline evidence mode may render support data after the block.

### Text Block

```json
{
  "block_id": "BLOCK-TEXT-001",
  "block_type": "text",
  "title": "说明标题",
  "text": "普通说明文字。",
  "confidence": "observed",
  "evidence_refs": [],
  "traceability_refs": [],
  "source_snippet_refs": []
}
```

`text` is plain text, not Markdown. It must follow the same Markdown safety rules as other normal DSL text fields.

### Diagram Block

```json
{
  "block_id": "BLOCK-DIAGRAM-001",
  "block_type": "diagram",
  "title": "图标题",
  "confidence": "observed",
  "evidence_refs": [],
  "traceability_refs": [],
  "source_snippet_refs": [],
  "diagram": {
    "id": "MER-BLOCK-001",
    "kind": "content_block",
    "title": "图标题",
    "diagram_type": "flowchart",
    "description": "图说明。",
    "source": "flowchart TD\n  A[\"Input\"] --> B[\"Output\"]",
    "confidence": "observed"
  }
}
```

`diagram` uses the existing Mermaid diagram object shape. `diagram.source` is required and must be non-empty.

### Table Block

```json
{
  "block_id": "BLOCK-TABLE-001",
  "block_type": "table",
  "title": "表标题",
  "confidence": "observed",
  "evidence_refs": [],
  "traceability_refs": [],
  "source_snippet_refs": [],
  "table": {
    "id": "TBL-BLOCK-001",
    "title": "表标题",
    "columns": [
      { "key": "name", "title": "名称" },
      { "key": "description", "title": "说明" }
    ],
    "rows": [
      {
        "name": "示例",
        "description": "示例说明。"
      }
    ]
  }
}
```

`table` uses the existing local table shape. Table block rows may only use declared column keys. They must not carry evidence, traceability, or source snippet refs. Support data attaches to the table block as a whole.

### Content Block Validation

For every content-block section:

- When the parent section has a `not_applicable_reason`, `blocks[]` participates in the not-applicable mutual exclusion rule.
- `internal_mechanism.mechanism_details[].blocks[]` does not have its own `not_applicable_reason`; it must be non-empty.
- If `blocks[]` is non-empty, at least one block must have `block_type: "text"` and non-empty `text`.
- `block_id` values must be unique within the parent content-block section.
- `block_type` must be `text`, `diagram`, or `table`.
- Every block must have non-empty `block_id`, `block_type`, `title`, and `confidence`.
- `evidence_refs`, `traceability_refs`, and `source_snippet_refs` are optional arrays on every block; when present, each referenced ID must resolve.
- Text blocks must have non-empty `text`.
- Diagram blocks must have a full Mermaid diagram object with non-empty `source`.
- Diagram block `confidence` must not conflict with `diagram.confidence`; if both are present, they must match.
- Table blocks must have non-empty `columns[]` and `rows[]`.
- Table block rows must not contain evidence, traceability, or source snippet refs.

Renderer uses `block.title` as the visible block heading. For diagram blocks, `diagram.title` may match `block.title` but does not have to. If they differ, `block.title` remains the visible block heading and `diagram.title` remains diagram metadata. Table blocks follow the same rule for `table.title`.

### ID Scope Rules

- `block_id` is unique within its parent content-block section.
- Mermaid `diagram.id` is globally unique across the DSL document.
- Table `table.id` is globally unique across the DSL document.
- `module_id`, `interface_id`, `parameter_id`, `data_id`, `dependency_id`, and `limitation_id` are globally unique within their own ID type.
- `dependency_id` is globally unique across both Chapter 4 module dependencies and Chapter 6 system dependencies. Use `system_dependency_ref` to connect a module dependency to a system dependency.
- Existing V1 support IDs keep their V1 global/type scope rules.

Validation errors should include both JSON path and stable ID when the item has an ID. For nested content block objects, report the nearest containing `block_id` plus nested `diagram.id` or `table.id` where present.

## Chapter 9 Design

V2 keeps Chapter 9 as the place for risks, assumptions, low-confidence items, and structure improvement guidance. Only `structure_issues_and_suggestions` changes from a restricted free-form string to a reusable content-block section.

Chapter 9 renders:

```text
9.1 风险清单
9.2 假设清单
9.3 低置信度项目
9.4 结构问题与改进建议
```

`9.4 结构问题与改进建议` first renders `structure_issues_and_suggestions.summary` as a paragraph when non-empty, then renders `structure_issues_and_suggestions.blocks[]` in DSL order.

```json
{
  "structure_issues_and_suggestions": {
    "summary": "说明本系统当前识别到的结构问题、风险和改进方向。",
    "blocks": [
      {
        "block_id": "ISSUE-TEXT-001",
        "block_type": "text",
        "title": "第四章信息密度不足",
        "text": "V1 第四章容易停留在职责摘要，缺少模块实现机制说明。V2 通过对外接口和实现机制说明补足这一点。",
        "confidence": "observed",
        "evidence_refs": [],
        "traceability_refs": [],
        "source_snippet_refs": []
      },
      {
        "block_id": "ISSUE-DIAGRAM-001",
        "block_type": "diagram",
        "title": "质量门禁关系图",
        "confidence": "observed",
        "evidence_refs": [],
        "traceability_refs": [],
        "source_snippet_refs": [],
        "diagram": {
          "id": "MER-ISSUE-QUALITY-GATES",
          "kind": "structure_issue",
          "title": "质量门禁关系图",
          "diagram_type": "flowchart",
          "description": "展示 DSL、Mermaid 和 Markdown 渲染之间的质量门禁。",
          "source": "flowchart TD\n  A[\"DSL\"] --> B[\"DSL validation\"]\n  B --> C[\"Mermaid review\"]\n  C --> D[\"Strict validation\"]\n  D --> E[\"Markdown output\"]",
          "confidence": "observed"
        }
      },
      {
        "block_id": "ISSUE-TABLE-001",
        "block_type": "table",
        "title": "改进建议清单",
        "confidence": "observed",
        "evidence_refs": [],
        "traceability_refs": [],
        "source_snippet_refs": [],
        "table": {
          "id": "TBL-ISSUE-IMPROVEMENTS",
          "title": "改进建议清单",
          "columns": [
            { "key": "issue", "title": "问题" },
            { "key": "suggestion", "title": "建议" }
          ],
          "rows": [
            {
              "issue": "证据块噪声过多",
              "suggestion": "默认使用 hidden evidence mode"
            }
          ]
        }
      }
    ],
    "not_applicable_reason": ""
  }
}
```

Chapter 9 uses the same content block validation rules. If `blocks[]` is non-empty, it must include at least one non-empty text block. `structure_issues_and_suggestions.summary` participates in the not-applicable mutual exclusion rule: if either summary or blocks are non-empty, `not_applicable_reason` must be empty; if both are empty, `not_applicable_reason` must be non-empty.

## Mermaid Readability Review

Before strict Mermaid validation, the skill workflow must dispatch an independent subagent to review every Mermaid diagram in the DSL for visual readability.

The subagent reviews:

- labels that are too long
- dense or ambiguous graph layout
- nodes whose text is likely to disappear in rendered Markdown
- diagrams that should be split
- places where long explanatory text should move out of nodes and into prose

The subagent suggests changes. The main agent applies appropriate changes to the DSL before validation.

This review does not replace strict validation.

### Expected Diagram Collector

V2 must define one shared expected diagram collector. Mermaid readability artifact validation and rendered diagram completeness must use this same collector output.

The collector gathers every present Mermaid diagram object that should render:

| DSL path | Notes |
| --- | --- |
| `$.architecture_views.module_relationship_diagram` | Existing V1 path. |
| `$.architecture_views.extra_diagrams[]` | Existing V1 path. |
| `$.runtime_view.runtime_flow_diagram` | Existing V1 path. |
| `$.runtime_view.runtime_sequence_diagram` | Existing V1 path when present. |
| `$.runtime_view.extra_diagrams[]` | Existing V1 path. |
| `$.configuration_data_dependencies.extra_diagrams[]` | Existing V1 path. |
| `$.cross_module_collaboration.collaboration_relationship_diagram` | Existing V1 path. |
| `$.cross_module_collaboration.extra_diagrams[]` | Existing V1 path. |
| `$.key_flows.flows[].diagram` | Existing V1 path. |
| `$.key_flows.extra_diagrams[]` | Existing V1 path. |
| `$.module_design.modules[].public_interfaces.interfaces[].execution_flow_diagram` | V2 public executable interface flow. |
| `$.module_design.modules[].internal_mechanism.mechanism_details[].blocks[].diagram` | V2 content block diagrams where `block_type` is `diagram`. |
| `$.structure_issues_and_suggestions.blocks[].diagram` | V2 Chapter 9 content block diagrams where `block_type` is `diagram`. |

Removed V1 Chapter 4 module diagram paths are not expected diagrams in V2 and must not be accepted as alternate V2 input fields:

- `$.module_design.modules[].internal_structure.diagram`
- `$.module_design.modules[].external_capability_details.extra_diagrams[]`
- `$.module_design.modules[].extra_diagrams[]`

The collector output must include `json_path`, `diagram.id`, `diagram.title`, `diagram.source`, and owning section path for each expected diagram. Omitted optional diagrams are not expected diagrams. A present diagram object with empty `source` is a validation error, not a skipped diagram. A diagram may be skipped only when its owning section is explicitly not applicable under the not-applicable mutual exclusion table.

### Readability Review Artifact

Mermaid readability review must produce a JSON artifact before strict validation. This artifact is workflow metadata; it must not be stored in DSL instances and must not render into final Markdown.

Example artifact:

```json
{
  "artifact_schema_version": "1.0",
  "reviewer": "independent_subagent",
  "source_dsl": "structure.dsl.json",
  "checked_diagram_ids": [
    "MER-IFACE-RENDER-CLI-FLOW",
    "MER-MECH-RENDER-FLOW"
  ],
  "accepted_diagram_ids": [],
  "revised_diagram_ids": [],
  "split_diagram_ids": [],
  "skipped_diagrams": [
    {
      "diagram_id": "MER-OPTIONAL-FLOW",
      "reason": "Owning section is explicitly not applicable."
    }
  ],
  "remaining_readability_risks": []
}
```

Every expected DSL diagram ID must appear in `checked_diagram_ids` or `skipped_diagrams[].diagram_id`. Each skipped diagram must provide a non-empty reason. `accepted_diagram_ids`, `revised_diagram_ids`, and `split_diagram_ids` must refer to checked diagram IDs or to diagrams derived from checked diagram IDs.

The V2 strict verification workflow must accept an explicit artifact path, for example:

```text
--mermaid-review-artifact <path>
```

The workflow must validate the artifact JSON before strict Mermaid validation. `source_dsl` must identify the same DSL input used by the expected diagram collector, after the workflow's normal path normalization. Strict validation must run after the readability review artifact is produced and validated. The strict verification workflow must fail fast when the artifact is missing, malformed, bound to a different DSL input, or does not cover every expected diagram from the shared collector.

## Mermaid Validation Strategy

This phase must not edit Mermaid validator files.

Because V2 adds local interface diagrams under `public_interfaces.interfaces[].execution_flow_diagram`, existing pre-render DSL strict validation may not see those new diagram paths if `scripts/validate_mermaid.py` remains unchanged.

To preserve strict acceptance without editing Mermaid validation code, V2 must use two strict gates:

1. Pre-render strict validation for existing Mermaid paths already supported by `scripts/validate_mermaid.py`.
2. Post-render strict validation from the rendered Markdown, so all rendered Mermaid fences, including local interface execution diagrams, are checked.

The final success criteria require strict validation of the rendered Markdown. Static-only Mermaid acceptance is not sufficient.

### Rendered Diagram Completeness Check

Strict Mermaid validation proves that rendered Mermaid fences are syntactically valid. It does not prove that every DSL diagram that should render actually appeared in final Markdown. V2 therefore requires a rendered diagram completeness check.

The renderer must emit a stable metadata comment immediately before every Mermaid fence:

````markdown
<!-- diagram-id: MER-IFACE-RENDER-CLI-FLOW -->
```mermaid
flowchart TD
  A --> B
```
````

This comment is structural Markdown source metadata, not evidence. It is not controlled by evidence rendering mode.

The completeness check must:

- collect expected diagrams with the shared expected diagram collector
- render Markdown
- verify that each expected `diagram.id` appears exactly once in a `diagram-id` metadata comment attached to an actual Mermaid fence
- verify that the Mermaid fence count is at least the number of expected rendered diagrams
- report missing diagrams with JSON path, `diagram.id`, and `diagram.title`

`diagram.title` may appear in error messages, but title text alone must not satisfy completeness.

Rendered diagram completeness and strict Mermaid validation are separate gates. Both must pass.

## Not Applicable Mutual Exclusion

For every not-applicable gated section, content and `not_applicable_reason` are mutually exclusive:

- if any gated content is non-empty, `not_applicable_reason` must be empty
- if all gated content is empty, `not_applicable_reason` must be non-empty

Mutual exclusion mapping:

| Section | Gated content paths | `not_applicable_reason` path | Summary participates |
| --- | --- | --- | --- |
| Module configuration parameters | `$.module_design.modules[].configuration.parameters.rows[]` | `$.module_design.modules[].configuration.parameters.not_applicable_reason` | No |
| Module dependencies | `$.module_design.modules[].dependencies.rows[]` | `$.module_design.modules[].dependencies.not_applicable_reason` | No |
| Module data objects | `$.module_design.modules[].data_objects.rows[]` | `$.module_design.modules[].data_objects.not_applicable_reason` | No |
| Public interfaces | `$.module_design.modules[].public_interfaces.interface_index.rows[]`, `$.module_design.modules[].public_interfaces.interfaces[]` | `$.module_design.modules[].public_interfaces.not_applicable_reason` | No |
| Executable interface parameters | `$.module_design.modules[].public_interfaces.interfaces[].parameters.rows[]` | `$.module_design.modules[].public_interfaces.interfaces[].parameters.not_applicable_reason` | No |
| Executable interface return values | `$.module_design.modules[].public_interfaces.interfaces[].return_values.rows[]` | `$.module_design.modules[].public_interfaces.interfaces[].return_values.not_applicable_reason` | No |
| Internal mechanism | `$.module_design.modules[].internal_mechanism.summary`, `$.module_design.modules[].internal_mechanism.mechanism_index.rows[]`, `$.module_design.modules[].internal_mechanism.mechanism_details[]` | `$.module_design.modules[].internal_mechanism.not_applicable_reason` | Yes |
| Known limitations | `$.module_design.modules[].known_limitations.rows[]` | `$.module_design.modules[].known_limitations.not_applicable_reason` | No |
| Chapter 9 structure issues | `$.structure_issues_and_suggestions.summary`, `$.structure_issues_and_suggestions.blocks[]` | `$.structure_issues_and_suggestions.not_applicable_reason` | Yes |

`internal_mechanism.mechanism_details[].blocks[]` is not a not-applicable gated section and has no `not_applicable_reason`; each mechanism detail must contain non-empty `blocks[]` with at least one text block.

The following fields are invalid in V2 and must not be used as alternate reason paths:

- `source_scope.not_applicable_reason`
- `configuration.not_applicable_reason`

The validator must block contradictory states. The renderer must not guess priority between content and `not_applicable_reason`; if such a state reaches rendering, the renderer must fail fast.

## Section 5.2 Runtime Unit Table

Section 5.2 must remove these columns:

- `入口不适用原因`
- `外部环境原因`

The new visible table columns are:

```text
运行单元 | 类型 | 入口 | 职责 | 关联模块 | 备注
```

If a runtime unit has no concrete entrypoint, set `entrypoint` to exactly `不适用` and place the explanation in `notes`.

V2 must remove these V1 runtime-unit fields from the DSL:

- `entrypoint_not_applicable_reason`
- `external_environment_reason`

If no concrete entrypoint exists, the renderer writes `不适用` in the `入口` column and renders the explanation from `notes` in `备注`.

`entrypoint` must not contain an inline reason such as `不适用：由 render_markdown.py 内部调用`; this is invalid in V2.

`external_environment_reason` must not be replaced. If a row only describes an external runtime, tool, browser, filesystem, or environment condition, model it as a dependency or configuration item instead of a runtime unit.

## Validation Rules

V2 validation must enforce:

- `dsl_version` must be exactly `0.2.0`; any other value fails before rendering.
- V1 `0.1.0` examples are accepted only as rejected fixtures.
- `module_design.modules[]` matches Chapter 3 modules one-to-one.
- Removed V1 Chapter 4 module fields such as `internal_structure`, `external_capability_details`, `extra_diagrams`, and `extra_tables` are invalid in V2 module objects.
- Each module has non-empty `module_kind`, `summary`, and `source_scope.summary`.
- `module_kind` must use the module kind enum defined in this spec.
- If `module_kind` is `other`, `module_kind_reason` must be non-empty.
- Each module has at least one of:
  - `source_scope.primary_files`
  - `source_scope.consumed_inputs`
  - `source_scope.owned_outputs`
- Not-applicable gated sections follow the not-applicable mutual exclusion rule.
- `source_scope.not_applicable_reason` and `configuration.not_applicable_reason` are invalid in V2.
- `configuration.parameters.rows[]`, when present, has non-empty `prototype`, `value_source`, and `meaning`.
- `configuration.parameters.rows[].value_source` is one of `default`, `cli_argument`, `environment`, `constant`, `config_file`, `computed`, `inferred`, or `unknown`.
- `configuration.parameters.rows[].value_or_default` may be empty only when `value_source` is `unknown`.
- `dependencies.rows[]`, when present, has non-empty `dependency_id`, `name`, `dependency_type`, `usage_relation`, `required_for`, and `failure_behavior`.
- `dependency_id` values are globally unique across module and system dependency scopes.
- `dependencies.rows[].dependency_type` must use the dependency enum defined in this spec.
- `dependencies.rows[].usage_relation` must use the usage relation enum defined in this spec.
- If `system_dependency_ref` is present, it must reference an existing Chapter 6 system dependency and must not reference the same dependency row.
- If `dependency_type` is `internal_module`, `target_module_id` must reference an existing module.
- If `dependency_type` is `data_object`, `target_data_id` must reference an existing data object.
- `data_objects.rows[]`, when present, has non-empty `data_id`, `name`, `data_type`, `role`, `producer`, `consumer`, and `shape_or_contract`.
- `public_interfaces.interface_index.rows[]` and `public_interfaces.interfaces[]` use matching `interface_id` sets.
- Interface detail sections render in `public_interfaces.interface_index.rows[]` order; `public_interfaces.interfaces[]` is only a lookup collection.
- Each interface has non-empty `interface_id`, `interface_name`, `interface_type`, `purpose`, and `location.file_path`.
- `interface_type` must use the interface enum defined in this spec.
- `other` interfaces require non-empty `interface_type_reason`.
- Executable interface types require non-empty `prototype`, `parameters`, `return_values`, `execution_flow_diagram`, `side_effects`, and `error_behavior`.
- Executable interface `execution_flow_diagram` uses the existing diagram object shape and has non-empty `source`.
- Executable interface parameter and return-value tables may be empty only when their `not_applicable_reason` is non-empty.
- Each executable interface parameter row has non-empty `parameter_name`, `parameter_type`, `description`, and `direction`.
- Each executable interface return value row has non-empty `return_name`, `return_type`, `description`, and `condition`.
- Contract interface types require non-empty `contract.contract_scope`, `contract.contract_location`, `contract.required_items`, `contract.consumers`, and `contract.validation_behavior`.
- Contract interface `contract.constraints` is optional; if present, it must be a non-empty string array.
- Contract interface `contract.required_fields` is invalid in V2; use `required_items`.
- Contract interface types do not require `parameters`, `return_values`, or `execution_flow_diagram`.
- Interface `location.file_path` is required; `symbol`, `line_start`, and `line_end` are optional.
- If either `line_start` or `line_end` is present and non-null, both must be present and non-null; `line_start` must be at least 1 and `line_end` must be greater than or equal to `line_start`.
- `line_start: 1` plus `line_end: 1` is invalid as an unknown placeholder unless support evidence proves the target is actually on line 1.
- If an interface has `confidence: "observed"` and `interface_type` is `function` or `method`, validation should warn unless `symbol` or a line range is provided.
- `internal_mechanism.mechanism_index.rows[]` must be non-empty unless `internal_mechanism.not_applicable_reason` is non-empty.
- Each mechanism index row has non-empty `mechanism_id`, `mechanism_name`, `purpose`, `input`, `processing`, `output`, `structural_significance`, and at least one typed `related_anchors[]` value.
- `related_anchors[]` must contain objects, not bare strings.
- `related_anchors[].anchor_type` must use the anchor type enum defined in this spec.
- `related_anchors[].value` must be non-empty for every anchor type.
- `file_path` anchors only require non-empty `value`; they must not be checked against the file system.
- Non-`file_path` ID anchors must resolve within the DSL support data or structure objects.
- `other` anchors require non-empty `reason`.
- `mechanism_id` values are unique within the module.
- `mechanism_details[]` corresponds one-to-one with `mechanism_index.rows[]` by `mechanism_id`.
- Mechanism detail subsections render in `mechanism_index.rows[]` order; `mechanism_details[]` is only a lookup collection.
- Each mechanism detail follows the reusable content block rules and includes at least one text block with non-empty `text`.
- Each known limitation row has non-empty `limitation_id`, `limitation`, `impact`, and `mitigation_or_next_step`.
- `structure_issues_and_suggestions` follows the reusable content block rules.
- Runtime unit rows do not contain `entrypoint_not_applicable_reason` or `external_environment_reason`.
- Runtime unit `entrypoint` is non-empty. If there is no concrete executable entrypoint, the value must be exactly `不适用`.
- If runtime unit `entrypoint` is `不适用`, `notes` must be non-empty.
- Runtime unit `entrypoint` must not begin with `不适用：`; put the reason in `notes`.
- Mermaid readability review artifact must exist before strict validation and must cover every expected DSL diagram.
- Mermaid readability artifact validation and rendered diagram completeness must use the shared expected diagram collector.
- Rendered diagram completeness check must pass before final acceptance.

## Renderer Requirements

Renderer changes:

- Fail fast for any `dsl_version` other than `0.2.0`; do not render V1 input.
- Add evidence mode handling.
- Suppress evidence-node rendering in `hidden` mode.
- Preserve V1 support-data rendering in `inline` mode.
- Render Chapter 4 using the new seven-subsection structure.
- Render local interface execution flow diagrams.
- Render interface detail sections in `public_interfaces.interface_index.rows[]` order.
- Render `internal_mechanism` mechanism index and one detail subsection per mechanism in `mechanism_index.rows[]` order.
- Render reusable content blocks through one shared helper used by internal mechanism details and Chapter 9 structure issues.
- Render Chapter 9 in the fixed `9.1` to `9.4` order defined in this spec.
- Render `structure_issues_and_suggestions.summary` before Chapter 9 structure issue blocks.
- Render Section 5.2 with the simplified runtime-unit columns.
- Fail fast if not-applicable gated sections contain both content and `not_applicable_reason`.
- Emit `<!-- diagram-id: ... -->` metadata immediately before every Mermaid fence.

## Documentation Requirements

Update:

- `SKILL.md`
- `references/dsl-spec.md`
- `references/document-structure.md`
- `references/review-checklist.md`
- examples
- tests

Do not update:

- `references/mermaid-rules.md`

## Testing Requirements

Add or update tests for:

- non-`0.2.0` `dsl_version` fails fast before rendering
- legacy V1 fixtures are rejected fixtures, not renderer acceptance fixtures
- default hidden evidence mode suppresses evidence-node rendering
- inline evidence mode preserves V1 evidence rendering
- hidden evidence mode suppresses content-block support refs while preserving structural content
- Chapter 4 new subsection order
- removed V1 Chapter 4 module fields fail validation
- source scope rendering
- `module_kind` enum validation
- `module_kind: "other"` requires `module_kind_reason`
- configuration rendering
- configuration `value_source` enum validation
- not-applicable mutual exclusion for rows, blocks, public interfaces, and internal mechanism index/details
- not-applicable mutual exclusion uses the documented content/reason path mapping
- `source_scope.not_applicable_reason` and `configuration.not_applicable_reason` fail validation
- dependency rendering
- dependency `dependency_type` enum validation
- dependency `usage_relation` enum validation
- dependency target reference validation for `internal_module` and `data_object`
- module and system dependencies cannot reuse the same `dependency_id`
- module dependency can reference a system dependency through `system_dependency_ref`
- invalid `system_dependency_ref` fails validation
- `system_dependency_ref` resolves against `configuration_data_dependencies.dependencies.rows[]`
- data object rendering
- public interface index rendering
- public interface detail rendering
- interface details render in index order, not physical details array order
- orphan interface detail fails validation
- interface parameter rows and return value rows follow not-applicable mutual exclusion
- executable interface validation
- contract interface validation
- contract interface uses `required_items`
- contract interface rejects V2 `required_fields`
- `other` interface requires `interface_type_reason`
- interface location allows null line values
- interface location rejects fake `1-1` placeholder ranges
- local interface Mermaid rendering
- local interface Mermaid `source` requiredness
- `internal_mechanism` mechanism index rendering
- `internal_mechanism` mechanism detail rendering
- `internal_mechanism` index/detail one-to-one validation
- `internal_mechanism` detail sections render in mechanism index order, not physical details array order
- orphan mechanism detail fails validation
- typed related anchors render correctly
- bare string `related_anchors[]` fails validation
- related anchors require non-empty `value`
- unknown non-file anchor IDs fail validation
- `file_path` anchors do not require file-system checks
- `other` anchors require reason
- `internal_mechanism` mechanism details require at least one text block
- reusable content block helper renders text, diagram, and table blocks for both Chapter 4 and Chapter 9
- content block title requiredness
- content block support refs validate but do not render in hidden mode
- diagram and table ID global uniqueness
- known limitations rendering
- Chapter 9 content block rendering
- Chapter 9 structure issues summary renders before blocks
- Chapter 9 summary participates in not-applicable mutual exclusion
- Chapter 9 fixed `9.1` to `9.4` rendering order
- Chapter 9 requires at least one text block when blocks are present
- Section 5.2 simplified columns
- Section 5.2 runtime unit DSL no longer uses `entrypoint_not_applicable_reason` or `external_environment_reason`
- Section 5.2 `entrypoint: "不适用"` requires non-empty `notes`
- Section 5.2 `entrypoint` beginning with `不适用：` fails validation
- shared expected diagram collector returns the same expected ID set for readability artifact validation and rendered completeness
- Mermaid fences include `diagram-id` metadata comments
- missing Mermaid readability review artifact fails strict verification workflow
- malformed or mismatched readability artifact `source_dsl` fails verification
- incomplete readability artifact diagram coverage fails verification
- skipped readability review diagram requires reason
- rendered diagram completeness check catches missing interface diagrams
- rendered diagram completeness check catches missing internal mechanism diagrams
- rendered diagram completeness check catches missing Chapter 9 diagrams
- rendered diagram completeness check rejects title-only matches without a metadata-bound Mermaid fence
- rendered diagram completeness check reports JSON path and diagram ID
- V2 schema acceptance
- V2 semantic validation failures for missing required structural fields
- strict validation of rendered Markdown containing local interface diagrams

Full test command:

```text
python3 -m unittest discover -s tests -v
```

Strict Mermaid validation and rendered diagram completeness must both be part of the verification story for rendered Markdown. Static-only Mermaid acceptance is not sufficient.

## Implementation Impact

Expected implementation files:

- `schemas/structure-design.schema.json`
- `scripts/validate_dsl.py`
- `scripts/render_markdown.py`
- `SKILL.md`
- `references/dsl-spec.md`
- `references/document-structure.md`
- `references/review-checklist.md`
- `examples/*.dsl.json`
- `tests/*`

Files intentionally out of scope:

- `scripts/validate_mermaid.py`
- `references/mermaid-rules.md`

## Acceptance Criteria

- V2 examples validate successfully.
- Final Markdown defaults to hidden evidence mode.
- Final Markdown can opt into inline evidence mode.
- Inputs with `dsl_version` other than `0.2.0` fail before rendering.
- Chapter 4 renders the seven agreed subsections in order.
- Executable interface detail sections include prototype, purpose, location, parameter table, return value table, local non-empty Mermaid flow diagram, side effects, error behavior, and consumers.
- Contract interface detail sections include purpose, location, contract scope, contract location, required items, constraints when present, consumers, and validation behavior.
- Internal mechanism renders a mechanism index plus one detail subsection per mechanism.
- Interface details and internal mechanism details render in index order.
- Internal mechanism details render text, diagram, and table content blocks in DSL order through the reusable content-block renderer.
- Chapter 9 renders risks, assumptions, low-confidence items, then structure issues in the agreed order.
- Chapter 9 structure issues render summary before content blocks.
- Chapter 9 structure issues render text, diagram, and table content blocks in DSL order through the reusable content-block renderer.
- Content block support refs remain valid DSL metadata and are hidden from final Markdown by default.
- Section 5.2 no longer shows `入口不适用原因` or `外部环境原因` columns.
- Section 5.2 DSL no longer uses `entrypoint_not_applicable_reason` or `external_environment_reason`.
- Runtime unit `entrypoint: "不适用"` stores its explanation in `notes`.
- Mermaid readability review artifact exists before strict validation and covers every expected DSL diagram.
- Readability artifact validation and rendered diagram completeness use the same expected diagram collector.
- Every rendered Mermaid fence has a `diagram-id` metadata comment.
- Every expected diagram collected from DSL is rendered into final Markdown unless its owning section is explicitly not applicable.
- Rendered Markdown Mermaid diagrams pass strict validation.
- Rendered diagram completeness check passes.
- No Mermaid validator or Mermaid rules files are changed.
