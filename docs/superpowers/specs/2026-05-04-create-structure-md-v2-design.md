# create-structure-md V2 Design

## Summary

V2 upgrades create-structure-md from a fixed 9-chapter Markdown renderer into a clearer structure-document renderer while preserving the current skill boundary: this skill consumes prepared DSL content and does not analyze repositories.

The primary changes are:

- Evidence support blocks are hidden by default in final Markdown.
- Chapter 4 is rebuilt around module scope, configuration, dependencies, data objects, public interfaces, and known limitations.
- Mermaid diagrams receive an adversarial readability review by a subagent before strict validation.
- Section 5.2 runtime unit tables are simplified.
- Mermaid validator files and Mermaid rule files are not changed in this phase.

## Goals

- Make generated Markdown easier to read by removing inline evidence noise by default.
- Make Chapter 4 explain usable module structure instead of generic responsibility summaries.
- Preserve evidence references inside DSL for validation, traceability, and upstream tools.
- Keep create-structure-md separate from future repository-analysis skills.
- Improve Mermaid readability before strict checks without changing Mermaid validation implementation.
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

`SKILL.md` should continue to state that create-structure-md does not perform repository analysis. V2 only makes the DSL and renderer better at expressing and rendering structure supplied by another actor.

## DSL Version

V2 should use `dsl_version: "0.2.0"`.

The validator may keep compatibility with `0.1.0` only if that does not complicate the main implementation. The V2 examples and tests should use `0.2.0`.

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

Each module renders six fixed subsections:

```text
4.x.1 模块定位与源码/产物范围
4.x.2 配置
4.x.3 依赖
4.x.4 数据对象
4.x.5 对外接口
4.x.6 已知限制
```

The renderer should output these subsections in this exact order.

### Chapter 4 DSL

`module_design.modules[]` should use this V2 shape:

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
    ],
    "not_applicable_reason": ""
  },

  "configuration": {
    "summary": "说明该模块使用的模块级参数、宏定义、常量、默认值或运行配置。",
    "parameters": {
      "rows": [
        {
          "parameter_id": "MPARAM-RENDER-OUTPUT-DIR",
          "prototype": "--output-dir",
          "current_value": "当前目录",
          "meaning": "指定最终 Markdown 文件写入目录。",
          "confidence": "observed",
          "evidence_refs": []
        }
      ],
      "not_applicable_reason": ""
    },
    "not_applicable_reason": ""
  },

  "dependencies": {
    "summary": "说明该模块依赖的运行时、库、工具或外部能力。",
    "rows": [
      {
        "dependency_id": "DEP-PYTHON",
        "name": "Python 3",
        "dependency_type": "runtime",
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
        "persistence": "临时文件或用户指定文件",
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
          "line_start": 1,
          "line_end": 1
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

`module_kind` should be an enum. Initial values:

- `documentation_contract`
- `schema_contract`
- `validator`
- `renderer`
- `installer`
- `test_suite`
- `library`
- `other`

V2 does not require module-kind-specific rendering templates. The enum exists so upstream analysis skills can classify modules consistently and future versions can specialize rendering if needed.

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

| 原型 | 当前值 | 含义 |
| --- | --- | --- |

`parameter_id`, confidence, and evidence refs are internal DSL fields and are not shown by default.

### Dependencies Rendering

Render dependencies as:

| 名称 | 类型 | 用途 | 失败行为 |
| --- | --- | --- | --- |

`dependency_id`, confidence, and evidence refs are internal DSL fields and are not shown by default.

### Data Objects Rendering

Render data objects as:

| 名称 | 类型 | 角色 | 生产方 | 消费方 | 结构/契约 | 持久化 |
| --- | --- | --- | --- | --- | --- | --- |

`data_id`, confidence, and evidence refs are internal DSL fields and are not shown by default.

### Public Interfaces Rendering

Render public interfaces in two layers.

First render a module-level interface list:

| 接口名称 | 接口功能描述 | 接口类型 |
| --- | --- | --- |

Then render one detail section per interface:

- interface prototype
- purpose
- location
- parameter table
- return value table
- local Mermaid execution flow diagram
- side effects
- error behavior
- consumers

Parameter table:

| 参数名 | 参数类型 | 参数描述 | 输入/输出 |
| --- | --- | --- | --- |

Return value table:

| 返回名 | 返回类型 | 描述 | 条件 |
| --- | --- | --- | --- |

The execution flow diagram is stored locally on the interface object as `execution_flow_diagram`. It is not routed through supplemental diagram fields. `execution_flow_diagram.source` is required and must be non-empty for every public interface.

### Known Limitations Rendering

Render known limitations as:

| 限制 | 影响 | 缓解/后续 |
| --- | --- | --- |

`limitation_id`, confidence, and evidence refs are internal DSL fields and are not shown by default.

## Mermaid Readability Review

Before strict Mermaid validation, the skill workflow should dispatch an independent subagent to review every Mermaid diagram in the DSL for visual readability.

The subagent reviews:

- labels that are too long
- dense or ambiguous graph layout
- nodes whose text is likely to disappear in rendered Markdown
- diagrams that should be split
- places where long explanatory text should move out of nodes and into prose

The subagent suggests changes. The main agent applies appropriate changes to the DSL before validation.

This review does not replace strict validation.

## Mermaid Validation Strategy

This phase must not edit Mermaid validator files.

Because V2 adds local interface diagrams under `public_interfaces.interfaces[].execution_flow_diagram`, existing pre-render DSL strict validation may not see those new diagram paths if `scripts/validate_mermaid.py` remains unchanged.

To preserve strict acceptance without editing Mermaid validation code, V2 should use two strict gates:

1. Pre-render strict validation for existing Mermaid paths already supported by `scripts/validate_mermaid.py`.
2. Post-render strict validation from the rendered Markdown, so all rendered Mermaid fences, including local interface execution diagrams, are checked.

The final success criteria require strict validation of the rendered Markdown. Static-only Mermaid acceptance is not sufficient.

## Section 5.2 Runtime Unit Table

Section 5.2 should remove these columns:

- `入口不适用原因`
- `外部环境原因`

The new visible table columns are:

```text
运行单元 | 类型 | 入口 | 职责 | 关联模块 | 备注
```

If a runtime unit has no entrypoint, render `不适用` in the `入口` column and place any explanation in `备注`.

V2 should remove these V1 runtime-unit fields from the DSL:

- `entrypoint_not_applicable_reason`
- `external_environment_reason`

If no concrete entrypoint exists, write the reason directly in `entrypoint`, for example `不适用：由 render_markdown.py 内部调用`.

`external_environment_reason` should not be replaced. If a row only describes an external runtime, tool, browser, filesystem, or environment condition, model it as a dependency or configuration item instead of a runtime unit.

## Validation Rules

V2 validation should enforce:

- `dsl_version` is `0.2.0` for V2 examples.
- `module_design.modules[]` matches Chapter 3 modules one-to-one.
- Each module has non-empty `module_kind`, `summary`, and `source_scope.summary`.
- Each module has at least one of:
  - `source_scope.primary_files`
  - `source_scope.consumed_inputs`
  - `source_scope.owned_outputs`
- `configuration.parameters.rows[]`, when present, has non-empty `prototype`, `current_value`, and `meaning`.
- `dependencies.rows[]`, when present, has non-empty `name`, `dependency_type`, `required_for`, and `failure_behavior`.
- `data_objects.rows[]`, when present, has non-empty `name`, `data_type`, `role`, `producer`, `consumer`, `shape_or_contract`, and `persistence`.
- `public_interfaces.interface_index.rows[]` and `public_interfaces.interfaces[]` use matching `interface_id` sets.
- Each interface has non-empty `interface_name`, `interface_type`, `prototype`, `purpose`, and `location.file_path`.
- Each interface parameter row has non-empty `parameter_name`, `parameter_type`, `description`, and `direction`.
- Each return value row has non-empty `return_name`, `return_type`, `description`, and `condition`.
- Each interface execution diagram uses the existing diagram object shape and has non-empty `source`.
- Each known limitation row has non-empty `limitation`, `impact`, and `mitigation_or_next_step`.
- Runtime unit rows do not contain `entrypoint_not_applicable_reason` or `external_environment_reason`.
- Runtime unit `entrypoint` is non-empty. If there is no concrete executable entrypoint, the value must begin with `不适用：`.

## Renderer Requirements

Renderer changes:

- Add evidence mode handling.
- Suppress evidence-node rendering in `hidden` mode.
- Preserve V1 support-data rendering in `inline` mode.
- Render Chapter 4 using the new six-subsection structure.
- Render local interface execution flow diagrams.
- Render Section 5.2 with the simplified runtime-unit columns.
- Treat missing V2 optional arrays as empty where migration compatibility is desired.

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

- default hidden evidence mode suppresses evidence-node rendering
- inline evidence mode preserves V1 evidence rendering
- Chapter 4 new subsection order
- source scope rendering
- configuration rendering
- dependency rendering
- data object rendering
- public interface index rendering
- public interface detail rendering
- local interface Mermaid rendering
- local interface Mermaid `source` requiredness
- known limitations rendering
- Section 5.2 simplified columns
- Section 5.2 runtime unit DSL no longer uses `entrypoint_not_applicable_reason` or `external_environment_reason`
- V2 schema acceptance
- V2 semantic validation failures for missing required structural fields
- strict validation of rendered Markdown containing local interface diagrams

Full test command:

```text
python3 -m unittest discover -s tests -v
```

Strict Mermaid validation must be part of the verification story for rendered Markdown. Static-only Mermaid acceptance is not sufficient.

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
- Chapter 4 renders the six agreed subsections in order.
- Interface detail sections include prototype, purpose, location, parameter table, return value table, local non-empty Mermaid flow diagram, side effects, error behavior, and consumers.
- Section 5.2 no longer shows `入口不适用原因` or `外部环境原因` columns.
- Section 5.2 DSL no longer uses `entrypoint_not_applicable_reason` or `external_environment_reason`.
- Skill workflow requires subagent Mermaid readability review before strict validation.
- Rendered Markdown Mermaid diagrams pass strict validation.
- No Mermaid validator or Mermaid rules files are changed.
