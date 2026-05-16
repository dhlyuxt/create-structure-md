# create-structure-md V2 Phase 2: Chapter 4 Module Model

## Summary

This phase defines the V2 Chapter 4 module model and the related Section 5.2 runtime-unit cleanup.

The root design remains `docs/superpowers/specs/2026-05-04-create-structure-md-v2-design.md`. Phase 1 global rules apply to this phase.

## Goals

- Replace the V1 Chapter 4 module subsection template.
- Make module-local structure explicit through scope, configuration, dependencies, data objects, public interfaces, internal mechanisms, and known limitations.
- Define Chapter 4 and Chapter 6 responsibilities so duplicated-looking configuration, data, and dependency content has a clear scope.
- Simplify Section 5.2 runtime unit rows.

## Non-Goals

- Do not implement repository analysis.
- Do not document arbitrary private helper functions or full internal call chains.
- Do not generate Word, PDF, image exports, or multiple output documents.
- Do not implement reusable content block rendering in this phase; Phase 3 owns the shared block model.
- Do not implement Mermaid gate behavior in this phase; Phase 4 owns Mermaid review and completeness.

## Chapter 4 Rendering Shape

V2 replaces these V1 module subsections:

- module responsibilities
- external capability summary
- provided capability table
- standalone internal structure diagram section
- supplement section as the primary extension mechanism

The removed V1 Chapter 4 fields are invalid as alternate V2 module-design inputs:

- `module_design.modules[].internal_structure`
- `module_design.modules[].external_capability_details`
- `module_design.modules[].extra_diagrams`
- `module_design.modules[].extra_tables`

Each module renders seven fixed subsections in this exact order:

```text
4.x.1 模块定位与源码/产物范围
4.x.2 配置
4.x.3 依赖
4.x.4 数据对象
4.x.5 对外接口
4.x.6 实现机制说明
4.x.7 已知限制
```

V2 intentionally overrides the V1 rule that Chapter 4 must not center on function prototypes or parameter lists. Public function, method, library API, workflow, and command-line interfaces are first-class module structure under `public_interfaces`.

## Chapter 4 and Chapter 6 Split

Chapter 4 renders module-local configuration, dependencies, and data objects. These items explain one module's boundary and behavior.

Chapter 6 renders system-level configuration, dependencies, and data artifacts. These items explain cross-module, whole-skill, installation, or runtime-environment concerns.

Rules:

- If an item applies to exactly one module and helps explain that module's contract, place it in Chapter 4.
- If an item is shared by multiple modules, affects the whole workflow, represents an external runtime environment, or describes final/installed artifacts at system scope, place it in Chapter 6.
- If the same underlying object appears in both chapters, Chapter 4 describes module-local use and Chapter 6 describes the system-level relationship.
- The renderer must not deduplicate Chapter 4 and Chapter 6 automatically.

The Chapter 6 system dependency collection is `$.configuration_data_dependencies.dependencies.rows[]`. If a module dependency corresponds to a system-level dependency, set `system_dependency_ref` to the Chapter 6 dependency ID.

## Module Kind

Each module must have:

- non-empty `module_id`
- non-empty `name`
- non-empty `module_kind`
- non-empty `summary`
- non-empty `source_scope.summary`
- `confidence`

`module_design.modules[]` must match Chapter 3 modules one-to-one.

`module_kind` uses the Phase 1 enum. If `module_kind` is `other`, `module_kind_reason` must be non-empty.

V2 does not require module-kind-specific rendering templates. The enum classifies modules consistently for upstream analysis and future specialization.

## Source Scope

`source_scope` explains module positioning and boundaries.

Expected fields:

- `summary`
- `primary_files[]`
- `consumed_inputs[]`
- `owned_outputs[]`
- `out_of_scope[]`

Do not include `primary_directories`.

At least one of these arrays must be non-empty:

- `primary_files[]`
- `consumed_inputs[]`
- `owned_outputs[]`

Render `source_scope` as:

- summary paragraph
- primary files table
- consumed inputs list
- owned outputs list
- out-of-scope list

`source_scope.not_applicable_reason` is invalid in V2.

## Configuration

Module configuration stores module-level parameters, macro-like constants, defaults, runtime switches, or computed settings.

`configuration.parameters.rows[]` renders as:

| 原型 | 当前/默认值 | 来源 | 含义 |
| --- | --- | --- | --- |

`parameter_id`, confidence, and evidence refs are internal DSL fields and are not shown by default.

Rules:

- Each row has non-empty `parameter_id`, `prototype`, `value_source`, and `meaning`.
- `value_source` uses the Phase 1 enum.
- `value_or_default` may be empty only when `value_source` is `unknown`.
- `configuration.parameters` follows the Phase 1 not-applicable mutual exclusion rule.
- `configuration.not_applicable_reason` is invalid in V2.

## Dependencies

Module dependencies describe runtimes, libraries, tools, internal modules, data objects, filesystem capabilities, services, fixtures, or contracts needed by one module.

`dependencies.rows[]` renders as:

| 名称 | 类型 | 关系 | 用途 | 失败行为 |
| --- | --- | --- | --- | --- |

Internal fields are not shown by default:

- `dependency_id`
- `target_module_id`
- `target_data_id`
- `system_dependency_ref`
- confidence
- evidence refs

Rules:

- Each row has non-empty `dependency_id`, `name`, `dependency_type`, `usage_relation`, `required_for`, and `failure_behavior`.
- `dependency_type` uses the Phase 1 enum.
- `usage_relation` uses the Phase 1 enum.
- `dependency_id` is globally unique across Chapter 4 and Chapter 6 dependency rows.
- If `system_dependency_ref` is present, it references an existing Chapter 6 system dependency and must not reference the same dependency row.
- If `dependency_type` is `internal_module`, `target_module_id` must reference an existing module.
- If `dependency_type` is `data_object`, `target_data_id` must reference an existing data object.
- `dependencies` follows the Phase 1 not-applicable mutual exclusion rule.

## Data Objects

Module data objects describe data read, written, owned, consumed, or produced by the module.

`data_objects.rows[]` renders as:

| 名称 | 类型 | 角色 | 生产方 | 消费方 | 结构/契约 |
| --- | --- | --- | --- | --- | --- |

`data_id`, confidence, and evidence refs are internal DSL fields and are not shown by default.

Rules:

- Each row has non-empty `data_id`, `name`, `data_type`, `role`, `producer`, `consumer`, and `shape_or_contract`.
- Do not include `persistence`.
- `data_objects` follows the Phase 1 not-applicable mutual exclusion rule.

## Public Interfaces

Public interfaces render in two layers.

First render a module-level interface list:

| 接口名称 | 接口功能描述 | 接口类型 |
| --- | --- | --- |

Then render one detail section per interface.

`public_interfaces.interface_index.rows[]` and `public_interfaces.interfaces[]` must use matching `interface_id` sets. Detail sections render in `interface_index.rows[]` order. `interfaces[]` is a lookup collection; its physical array order does not control rendering.

Executable interface types:

- `command_line`
- `function`
- `method`
- `library_api`
- `workflow`

Executable detail sections render:

- prototype
- purpose
- location
- parameter table
- return value table
- local Mermaid execution flow diagram
- side effects
- error behavior
- consumers

Executable interface `execution_flow_diagram.source` is required and non-empty.

`execution_flow_diagram` uses the existing Mermaid diagram object shape.

Contract interface types:

- `schema_contract`
- `dsl_contract`
- `document_contract`
- `configuration_contract`
- `data_contract`
- `test_fixture`

Contract detail sections render:

- purpose
- location
- contract scope
- contract location
- required items
- constraints, when present
- consumers
- validation behavior

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

`contract.required_fields` is invalid in V2; use `required_items`.

Parameter table:

| 参数名 | 参数类型 | 参数描述 | 输入/输出 |
| --- | --- | --- | --- |

Return value table:

| 返回名 | 返回类型 | 描述 | 条件 |
| --- | --- | --- | --- |

Public interface validation:

- each interface has non-empty `interface_id`, `interface_name`, `interface_type`, `purpose`, and `location.file_path`
- `interface_type` uses the Phase 1 enum
- `other` interfaces require non-empty `interface_type_reason`
- executable interface types require non-empty `prototype`, `parameters`, `return_values`, `execution_flow_diagram`, `side_effects`, and `error_behavior`
- executable interface `execution_flow_diagram` uses the existing Mermaid diagram object shape and has non-empty `source`
- each executable interface parameter row has non-empty `parameter_name`, `parameter_type`, `description`, and `direction`
- each executable interface return value row has non-empty `return_name`, `return_type`, `description`, and `condition`
- executable interface parameters and return values follow the Phase 1 not-applicable mutual exclusion rule
- contract interface types require non-empty `contract.contract_scope`, `contract.contract_location`, `contract.required_items`, `contract.consumers`, and `contract.validation_behavior`
- `contract.constraints`, when present, must be a non-empty string array
- contract interface types do not require `parameters`, `return_values`, or `execution_flow_diagram`
- if an interface has `confidence: "observed"` and `interface_type` is `function` or `method`, validation should warn unless `symbol` or a line range is provided
- orphan interface details fail validation

## Internal Mechanism

`internal_mechanism` is the primary Chapter 4 section for explaining how the module works internally. It is not miscellaneous notes.

This phase owns the mechanism index and one-to-one detail contract. Phase 3 owns reusable content block schema and rendering.

The renderer outputs:

- summary paragraph
- mechanism index table
- one mechanism detail subsection for each mechanism
- each mechanism detail's content blocks in DSL order
- `not_applicable_reason` only when the mechanism summary, index, and details are empty

Mechanism index table:

| 机制 | 用途 | 输入 | 处理方式 | 输出 | 结构意义 |
| --- | --- | --- | --- | --- | --- |

`mechanism_id`, related anchors, confidence, and support refs are internal DSL fields and are not shown by default.

Rules:

- `mechanism_index.rows[]` must be non-empty unless `internal_mechanism.not_applicable_reason` is non-empty.
- Each mechanism index row has non-empty `mechanism_id`, `mechanism_name`, `purpose`, `input`, `processing`, `output`, `structural_significance`, and at least one typed `related_anchors[]` value.
- `mechanism_id` values are unique within the module.
- `mechanism_details[]` corresponds one-to-one with `mechanism_index.rows[]` by `mechanism_id`.
- Mechanism detail subsections render in `mechanism_index.rows[]` order.
- `mechanism_details[]` is a lookup collection keyed by `mechanism_id`; physical array order does not control rendering.
- Each mechanism detail follows the Phase 3 reusable content block rules and includes at least one text block.

## Typed Related Anchors

`related_anchors[]` uses typed objects, not bare strings:

```json
[
  {
    "anchor_type": "interface_id",
    "value": "IFACE-RENDER-CLI",
    "reason": ""
  }
]
```

Rules:

- `anchor_type` uses the Phase 1 enum.
- Every anchor has non-empty `anchor_type` and `value`.
- `other` anchors must also have non-empty `reason`.
- `file_path` anchors only require non-empty `value`; they must not be checked against the file system and must not be resolved against repository files.
- Non-`file_path` ID anchors must resolve within DSL support data or structure objects.

Anchor resolution:

| Anchor type | Validation target |
| --- | --- |
| `file_path` | Non-empty `value` only. |
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

## Known Limitations

Known limitations render as:

| 限制 | 影响 | 缓解/后续 |
| --- | --- | --- |

`limitation_id`, confidence, and evidence refs are internal DSL fields and are not shown by default.

Rules:

- Each known limitation row has non-empty `limitation_id`, `limitation`, `impact`, and `mitigation_or_next_step`.
- `known_limitations` follows the Phase 1 not-applicable mutual exclusion rule.

## Section 5.2 Runtime Unit Table

Section 5.2 removes these columns:

- `入口不适用原因`
- `外部环境原因`

The new visible table columns are:

```text
运行单元 | 类型 | 入口 | 职责 | 关联模块 | 备注
```

V2 removes these V1 runtime-unit fields from the DSL:

- `entrypoint_not_applicable_reason`
- `external_environment_reason`

If a runtime unit has no concrete entrypoint:

- set `entrypoint` to exactly `不适用`
- place the explanation in `notes`
- render `不适用` in the `入口` column
- render `notes` in the `备注` column

`entrypoint` must not contain an inline reason such as `不适用：由 render_markdown.py 内部调用`; this is invalid in V2.

`external_environment_reason` must not be replaced. If a row only describes an external runtime, tool, browser, filesystem, or environment condition, model it as a dependency or configuration item instead of a runtime unit.

## Testing Requirements

Add or update tests for:

- Chapter 4 seven-subsection order
- `module_design.modules[]` matches Chapter 3 modules one-to-one
- removed V1 Chapter 4 module fields fail validation
- Chapter 4 and Chapter 6 split behavior
- source scope rendering and validation
- `module_kind` enum validation
- `module_kind: "other"` requires `module_kind_reason`
- configuration rendering and `value_source` enum validation
- dependency rendering, dependency enum validation, and usage relation enum validation
- dependency target validation for `internal_module` and `data_object`
- module and system dependencies cannot reuse the same `dependency_id`
- `system_dependency_ref` resolves against `$.configuration_data_dependencies.dependencies.rows[]`
- data object rendering without `data_id` in final Markdown
- public interface index and detail rendering
- interface detail sections render in index order
- orphan interface detail validation failure
- executable interface validation
- executable interface `execution_flow_diagram` uses the existing Mermaid diagram object shape
- executable interface parameter row requiredness
- executable interface return value row requiredness
- executable interface Mermaid `source` requiredness
- contract interface validation
- contract interface requiredness
- contract interface optional `constraints` validation
- contract interface uses `required_items`
- contract interface rejects `required_fields`
- observed function or method interface without `symbol` or line range emits warning
- interface parameter and return value not-applicable mutual exclusion
- internal mechanism index and detail one-to-one validation
- internal mechanism details render in mechanism index order
- orphan mechanism detail validation failure
- bare string `related_anchors[]` fails validation
- typed related anchors validate and render correctly
- `file_path` anchors do not require file-system checks
- known limitations rendering
- Section 5.2 simplified columns
- Section 5.2 rejects `entrypoint_not_applicable_reason` and `external_environment_reason`
- Section 5.2 `entrypoint: "不适用"` requires non-empty `notes`
- Section 5.2 `entrypoint` beginning with `不适用：` fails validation

## Acceptance Criteria

- Chapter 4 renders the seven agreed subsections in order.
- Chapter 4 uses the V2 module model instead of V1 responsibility/capability/supplement subsections.
- Module-local configuration, dependencies, and data objects are distinct from Chapter 6 system-level items.
- Public interfaces render through index plus detail sections.
- Executable interfaces include prototype, purpose, location, parameter table, return value table, local non-empty Mermaid flow diagram, side effects, error behavior, and consumers.
- Contract interfaces include purpose, location, contract scope, contract location, required items, constraints when present, consumers, and validation behavior.
- Internal mechanisms render a mechanism index plus one detail subsection per mechanism.
- Interface details and internal mechanism details render in index order.
- Section 5.2 no longer shows or accepts V1 entrypoint/environment reason fields.
