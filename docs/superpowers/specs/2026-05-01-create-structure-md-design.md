# create-structure-md Skill Design

## Status

Ready for user review.

## Purpose

`create-structure-md` is a local personal Codex skill for creating a single software structure design document. It does not analyze code, infer requirements, run repository intelligence tools, or decide what the system means. Codex performs any code or requirement understanding outside the skill. This skill only turns Codex-prepared structured design content into a validated `STRUCTURE_DESIGN.md`.

The skill optimizes for document quality, repeatability, and renderable Mermaid diagrams. Mermaid is a first-class output surface, not a decorative afterthought.

## Confirmed Requirements

- Skill name: `create-structure-md`.
- Scope: local personal skill.
- Final output: one Markdown file named `STRUCTURE_DESIGN.md`.
- Intermediate outputs: one or more JSON DSL files may be created in a temporary working directory.
- Language: Chinese by default, with English terms where they are clearer or conventional.
- Mermaid only: Graphviz, DOT, SVG files, and image export are out of scope as final outputs.
- Mermaid diagrams are written as Markdown Mermaid code blocks; no separate image files are generated.
- `validate_mermaid.py` is an independent script because Mermaid validity is critical.
- DSL coverage is complete for the document, not only a minimal subset.
- Every design item should carry confidence where useful: `observed`, `inferred`, or `unknown`.
- DSL JSON contains document content only. Validation policy fields such as `empty_allowed`, `required`, `min_rows`, or rendering control flags must not appear in DSL instances.
- Necessary source snippets are allowed when they improve the document.
- Architecture issues such as cycles, reverse dependencies, and unclear ownership are recorded honestly when Codex supplies them.
- The final Markdown uses fixed 9 chapters. Section-specific non-empty rules are enforced by Python validation scripts and documented for Codex before it writes the DSL.
- Examples and tests are required.

## Non-Goals

The skill will not:

- Inspect or understand a target repository.
- Generate `repo_facts.json`.
- Include `analyze_repo.py`.
- Depend on Tree-sitter, Doxygen, pyreverse, cflow, libclang, or Graphviz.
- Create multiple Markdown chapter files.
- Generate Word, PDF, SVG, PNG, or other rendered document formats as final deliverables.
- Include C2000, TI driverlib, CPU1/CPU2, ISR, or embedded-C-specific profiles in the first version.
- Automatically delete temporary files or generated artifacts.

## Alternatives Considered

### Full Repository Analysis Pipeline

The old direction used static analysis scripts, repository facts, evidence indexes, and rendering. That is too broad for this skill. It mixes two responsibilities: understanding a project and creating a document. The user explicitly narrowed the skill to document creation.

### Direct Markdown Generation

Codex could write `STRUCTURE_DESIGN.md` directly from its understanding. This is simple, but it gives up validation, reusable examples, Mermaid checks, and consistent structure. It also makes later improvements hard because document shape is embedded in free-form Markdown.

### DSL-Driven Single Document

This is the selected approach. Codex creates a complete JSON DSL in a temporary directory, validates the DSL, validates Mermaid blocks independently, and renders a single Markdown file through a template. This keeps the skill focused while preserving quality gates.

## Proposed Skill Structure

```text
create-structure-md/
├── SKILL.md
├── references/
│   ├── dsl-spec.md
│   ├── document-structure.md
│   ├── mermaid-rules.md
│   └── review-checklist.md
├── schemas/
│   └── structure-design.schema.json
├── scripts/
│   ├── validate_dsl.py
│   ├── validate_mermaid.py
│   └── render_markdown.py
├── templates/
│   └── STRUCTURE_DESIGN.md.tpl
├── examples/
│   ├── minimal-from-code.dsl.json
│   └── minimal-from-requirements.dsl.json
└── tests/
    ├── test_validate_dsl.py
    ├── test_validate_mermaid.py
    └── test_render_markdown.py
```

## Input Readiness Contract

`create-structure-md` must be invoked only after Codex has already prepared enough structured design content outside this skill.

Before invoking the skill, Codex must have enough information to populate all required chapters without fabrication, including:

- module list and stable module IDs
- module responsibilities
- module relationships
- module-level external capabilities or interface requirements
- module internal structure information
- runtime units and runtime flow
- configuration, structural data/artifact, and dependency information when applicable
- cross-module collaboration scenarios
- key flows and one diagram concept per key flow
- confidence values where useful
- evidence references or source snippets when available

If these inputs are not available, Codex must not invoke the renderer and must not invent missing content to satisfy validation. Codex should first perform project or requirements understanding outside this skill, then create the DSL and invoke this skill.

## Skill Workflow

1. Codex understands the target codebase, requirements, or user-provided notes outside this skill.
2. Codex invokes `create-structure-md` when the user asks for a software structure design document.
3. The skill instructs Codex to create a temporary working directory.
4. Codex writes one complete DSL JSON file and may write smaller staged JSON files first.
5. Codex runs `validate_dsl.py` against the complete DSL.
6. Codex runs `validate_mermaid.py` to validate Mermaid diagram blocks.
7. Codex runs `render_markdown.py` to create `STRUCTURE_DESIGN.md`.
8. Codex reviews the generated document with `references/review-checklist.md`.
9. Codex reports the output path, temporary working directory path, and any assumptions or low-confidence items.

Temporary files are not automatically deleted. If cleanup is needed, Codex should provide the command for the user to run.

## Output Location

Default final output path:

- If the user provides an output directory, write `STRUCTURE_DESIGN.md` there.
- Otherwise write `STRUCTURE_DESIGN.md` to the target repository root, or to the current working directory when no target repository root is known.
- The final file name must be exactly `STRUCTURE_DESIGN.md`.

Temporary work directory:

- Preferred: `<workspace>/.codex-tmp/create-structure-md-<run-id>/`.
- Fallback: system temp directory, such as `/tmp/create-structure-md-<run-id>`, if the workspace temp directory cannot be created.
- Temporary files are not automatically deleted. Codex reports the temporary work directory path after generation.

## DSL Design

The DSL is the contract between Codex's understanding and the renderer. It should be expressive enough to create the whole document, but not so elaborate that Codex fights the schema.

Top-level fields:

- `dsl_version`: schema version.
- `document`: rendered as chapter 1, with title, project name, versions, status, source type, generation metadata, and output filename.
- `system_overview`: rendered as chapter 2, with a compact system summary and core capabilities.
- `architecture_views`: rendered as chapter 3, with architecture summary, fixed module introduction table, and required module relationship Mermaid diagram.
- `module_design`: rendered as chapter 4, with one subsection per module from chapter 3.
- `runtime_view`: rendered as chapter 5, with runtime units, runtime flow, and optional runtime sequence diagram.
- `configuration_data_dependencies`: rendered as chapter 6, with configuration items, key structural data/artifacts, and dependencies.
- `cross_module_collaboration`: rendered as chapter 7, with cross-module collaboration scenarios and collaboration diagrams.
- `key_flows`: rendered as chapter 8, with key flow index and one Mermaid flow diagram per listed flow.
- `structure_issues_and_suggestions`: rendered as chapter 9, as optional free-form Markdown text.
- `evidence`, `traceability`, `risks`, `assumptions`, and `source_snippets`: DSL support data only. They may inform rendered chapters, but they do not become standalone Markdown chapters.

Important repeated fields:

- `id`: stable local identifier.
- `name`: human-readable Chinese name.
- `description`: concise explanation.
- `confidence`: `observed`, `inferred`, or `unknown`.
- `evidence_refs`: references to evidence items supplied in the DSL.
- `notes`: short supplemental notes where needed.

### MVP DSL Shape

The MVP uses semantic chapter fields instead of generic `required_tables`, `required_diagrams`, or `recommended_diagrams` wrappers. Fixed tables and fixed diagrams are named directly by their chapter meaning. Free-form supplemental content remains in `extra_tables` and `extra_diagrams`.

```json
{
  "dsl_version": "0.1.0",
  "document": {},
  "system_overview": {},
  "architecture_views": {
    "summary": "",
    "module_intro": { "rows": [] },
    "module_relationship_diagram": {},
    "extra_tables": [],
    "extra_diagrams": []
  },
  "module_design": {
    "summary": "",
    "modules": []
  },
  "runtime_view": {
    "summary": "",
    "runtime_units": { "rows": [] },
    "runtime_flow_diagram": {},
    "runtime_sequence_diagram": {},
    "extra_tables": [],
    "extra_diagrams": []
  },
  "configuration_data_dependencies": {
    "summary": "",
    "configuration_items": { "rows": [] },
    "structural_data_artifacts": { "rows": [] },
    "dependencies": { "rows": [] },
    "extra_tables": [],
    "extra_diagrams": []
  },
  "cross_module_collaboration": {
    "summary": "",
    "collaboration_scenarios": { "rows": [] },
    "collaboration_relationship_diagram": {},
    "extra_tables": [],
    "extra_diagrams": []
  },
  "key_flows": {
    "summary": "",
    "flow_index": { "rows": [] },
    "flows": [],
    "extra_tables": [],
    "extra_diagrams": []
  },
  "structure_issues_and_suggestions": "",
  "evidence": [],
  "traceability": [],
  "risks": [],
  "assumptions": [],
  "source_snippets": []
}
```

Fixed table nodes contain only rows:

```json
{
  "rows": [
    { "name": "示例" }
  ]
}
```

The renderer owns the fixed title and visible columns for each semantic table key. The validator checks that rows use the fixed content fields and metadata fields, and satisfy chapter-specific non-empty rules. DSL instances must not repeat fixed table `id`, `title`, or `columns`.

Some fixed table rows include metadata fields that are required for validation but are not necessarily rendered as visible table columns. For example, `module_intro.rows[].module_id` is the stable matching key for chapter 4, while chapter 3 still renders the fixed five user-facing columns: module name, responsibility, inputs, outputs, and notes.

Extra table node:

```json
{
  "id": "TBL-001",
  "title": "表格标题",
  "columns": [
    { "key": "name", "title": "名称" }
  ],
  "rows": [
    { "name": "示例" }
  ]
}
```

Common Mermaid diagram node:

```json
{
  "id": "MER-001",
  "kind": "module_relationship",
  "title": "图标题",
  "diagram_type": "flowchart",
  "description": "",
  "source": "flowchart TD\n  A[模块A] --> B[模块B]",
  "confidence": "observed"
}
```

MVP core Mermaid `diagram_type` values are fully supported and tested:

```json
[
  "flowchart",
  "graph",
  "sequenceDiagram",
  "classDiagram",
  "stateDiagram-v2"
]
```

Extended Mermaid `diagram_type` values are allowed in strict mode and receive only lightweight static checks in the MVP:

```json
[
  "erDiagram",
  "requirementDiagram",
  "C4Context",
  "C4Container",
  "C4Component",
  "C4Dynamic"
]
```

Mermaid diagrams are embedded under the section that renders them. There is no global diagram routing field and no attempt to model Mermaid nodes or edges in the DSL.

These Mermaid diagram types are not supported in the MVP: `journey`, `gantt`, `timeline`, `mindmap`, and `quadrantChart`.

### Validation Policy Outside DSL

DSL instances must not include validation policy fields. In particular, JSON written by Codex must not contain `empty_allowed`, `required`, `min_rows`, `max_rows`, `render_when_empty`, or similar control fields. The DSL says what the document contains; `validate_dsl.py` decides whether that content is sufficient.

The selected policy split is:

- `schemas/structure-design.schema.json` enforces structural shape, required object fields, primitive types, fixed table row content/metadata fields, and enum values.
- `validate_dsl.py` enforces semantic rules that need project-wide knowledge: non-empty table rows, one-to-one references, module coverage, flow coverage, and Mermaid source presence.
- `references/dsl-spec.md` and `references/document-structure.md` tell Codex which fields are required before it writes the DSL.
- `render_markdown.py` assumes the DSL has already passed validation. It renders optional empty content with fixed wording, but it does not decide whether required content may be missing.

Requiredness is documented as rules beside each chapter below, not encoded as fields in JSON examples.

### Chapter 1: Document Information

`document` renders as a compact information table.

```json
{
  "document": {
    "title": "软件结构设计说明书",
    "project_name": "",
    "project_version": "",
    "document_version": "",
    "status": "draft",
    "generated_at": "",
    "generated_by": "Codex",
    "language": "zh-CN",
    "source_type": "mixed",
    "scope_summary": "",
    "not_applicable_policy": "固定章节；按章节规则处理空内容",
    "output_file": "STRUCTURE_DESIGN.md"
  }
}
```

### Chapter 2: System Overview

`system_overview` is intentionally brief. It should not duplicate architecture or module details.

```json
{
  "system_overview": {
    "summary": "",
    "purpose": "",
    "core_capabilities": [
      {
        "id": "CAP-001",
        "name": "",
        "description": "",
        "confidence": "observed"
      }
    ],
    "notes": []
  }
}
```

### Chapter 3: Architecture Views

Chapter 3 is the architecture overview. It must include a fixed module introduction table and at least one module relationship Mermaid diagram. It does not include an architecture-view inventory table.

```json
{
  "architecture_views": {
    "summary": "",
    "notes": [],
    "module_intro": {
      "rows": [
        {
          "module_id": "MOD-001",
          "module_name": "",
          "responsibility": "",
          "inputs": "",
          "outputs": "",
          "notes": ""
        }
      ]
    },
    "module_relationship_diagram": {
      "id": "MER-ARCH-MODULES",
      "kind": "module_relationship",
      "title": "模块关系图",
      "diagram_type": "flowchart",
      "description": "展示系统内部主要模块及其关系。",
      "source": "",
      "confidence": "observed"
    },
    "extra_tables": [],
    "extra_diagrams": []
  }
}
```

Rules:

- `module_intro` must exist.
- `module_intro.rows` must include `module_id` plus five visible table fields: `module_name`, `responsibility`, `inputs`, `outputs`, and `notes`.
- `module_intro.rows[].module_id` is validation metadata, not a visible table column. It must be non-empty and unique.
- `module_intro.rows` must contain at least one module. If no module can be identified, Codex must revise its structure understanding before rendering.
- `module_relationship_diagram` must exist.
- `module_relationship_diagram.diagram_type` is not fixed, but it must be one of the supported Mermaid diagram types.
- `module_relationship_diagram.source` must be non-empty and pass Mermaid validation.
- `extra_tables` and `extra_diagrams` may be used for additional architecture material.

### Chapter 4: Module Design

Chapter 4 expands each module listed in chapter 3. Every module must be explainable at the structure-design level. This chapter describes module-level capabilities, interface requirements, and internal structure relationships. It must not become a function-level API reference, function signature list, or detailed design document.

```json
{
  "module_design": {
    "summary": "",
    "notes": [],
    "modules": [
      {
        "id": "MOD-001",
        "name": "",
        "summary": "",
        "responsibilities": [],
        "external_capability_summary": {
          "description": "",
          "consumers": [],
          "interface_style": "",
          "boundary_notes": []
        },
        "external_capability_details": {
          "provided_capabilities": {
            "rows": [
              {
                "capability_name": "",
                "interface_style": "",
                "description": "",
                "inputs": "",
                "outputs": "",
                "notes": ""
              }
            ]
          },
          "extra_tables": [],
          "extra_diagrams": []
        },
        "internal_structure": {
          "summary": "",
          "diagram": {
            "id": "MER-MOD-001-STRUCT",
            "kind": "internal_structure",
            "title": "模块内部结构关系图",
            "diagram_type": "flowchart",
            "description": "展示模块内部组成、数据/控制关系或子职责关系。",
            "source": "",
            "confidence": "observed"
          },
          "textual_structure": "",
          "not_applicable_reason": ""
        },
        "extra_tables": [],
        "extra_diagrams": [],
        "source_snippet_refs": [],
        "notes": [],
        "confidence": "observed"
      }
    ]
  }
}
```

Rules:

- `module_design.modules` must cover every module in `architecture_views.module_intro.rows` by matching `modules[].id` to `module_intro.rows[].module_id`.
- Each module renders as its own subsection.
- Each module must have a non-empty `id`, `name`, and `summary`.
- Each module must have at least one responsibility.
- `external_capability_summary.description` must be non-empty.
- `external_capability_summary.interface_style` is free text, not an enum.
- `external_capability_details.provided_capabilities` must exist.
- The provided capabilities table uses fixed row fields: `capability_name`, `interface_style`, `description`, `inputs`, `outputs`, and `notes`.
- The provided capabilities table must have at least one row.
- Each provided capability row must include non-empty `capability_name` and `description`.
- `internal_structure.summary` must be non-empty.
- `internal_structure.diagram.source` is preferred. If present, it must use a supported Mermaid `diagram_type` and pass Mermaid validation.
- If `internal_structure.diagram.source` is empty, `internal_structure.textual_structure` must be non-empty and describe the module's internal composition, data/control relationships, or sub-responsibility relationships.
- `internal_structure.not_applicable_reason` may explain why a diagram is not useful, but it cannot by itself satisfy internal structure validation.
- Missing a function call graph is not a reason to force module re-partitioning.
- If a module has neither an internal structure diagram nor a textual internal structure description, final rendering stops and Codex must revise the module design.
- Function names may appear as observed evidence or existing interface names when useful, but the chapter must not center on function prototypes, parameter lists, return-value definitions, or full call chains.

### Chapter 5: Runtime View

Chapter 5 explains how the system runs. A runtime unit is something that is started, triggered, scheduled, or continuously executed, such as a CLI command, service process, worker, event loop, interrupt path, library call path, or document-generation phase.

```json
{
  "runtime_view": {
    "summary": "",
    "notes": [],
    "runtime_units": {
      "rows": [
        {
          "unit_name": "",
          "unit_type": "",
          "entrypoint": "",
          "responsibility": "",
          "related_modules": [],
          "notes": ""
        }
      ]
    },
    "runtime_flow_diagram": {
      "id": "MER-RUNTIME-FLOW",
      "kind": "runtime_flow",
      "title": "运行时流程图",
      "diagram_type": "flowchart",
      "description": "展示系统启动、运行单元协作和主要调度路径。",
      "source": "",
      "confidence": "observed"
    },
    "runtime_sequence_diagram": {
      "id": "MER-RUNTIME-SEQUENCE",
      "kind": "runtime_sequence",
      "title": "运行时序图",
      "diagram_type": "sequenceDiagram",
      "description": "推荐生成，用于展示关键运行路径中对象或模块之间的时序交互。",
      "source": "",
      "confidence": "observed"
    },
    "extra_tables": [],
    "extra_diagrams": []
  }
}
```

Rules:

- `runtime_units` must exist and its rows use fixed fields: `unit_name`, `unit_type`, `entrypoint`, `responsibility`, `related_modules`, and `notes`.
- `runtime_units.rows` must contain at least one runtime unit.
- `runtime_flow_diagram` must exist.
- `runtime_flow_diagram.diagram_type` must be one of the supported Mermaid diagram types.
- `runtime_flow_diagram.source` must be non-empty and pass Mermaid validation.
- `runtime_sequence_diagram` is recommended but not required. If Codex does not generate it, the field may be omitted or left empty and the renderer does not output it. If it has a non-empty `source`, it must use `sequenceDiagram` and pass Mermaid validation.

### Chapter 6: Configuration, Data, and Dependencies

Chapter 6 is named `配置、数据与依赖关系`. It uses tables as the primary expression form. It does not define a recommended Mermaid diagram because mixing configuration, data, products, and dependencies into one diagram is usually unclear. Codex may add `extra_diagrams` only when a diagram has one clear subject.

```json
{
  "configuration_data_dependencies": {
    "summary": "",
    "notes": [],
    "configuration_items": {
      "rows": []
    },
    "structural_data_artifacts": {
      "rows": [
        {
          "artifact_name": "",
          "artifact_type": "",
          "owner": "",
          "producer": "",
          "consumer": "",
          "notes": ""
        }
      ]
    },
    "dependencies": {
      "rows": []
    },
    "extra_tables": [],
    "extra_diagrams": []
  }
}
```

Rules:

- `configuration_items` must exist and its rows use fixed fields: `config_name`, `source`, `used_by`, `purpose`, and `notes`.
- `configuration_items.rows` may be empty. If empty, the final Markdown renders a fixed `不适用` statement instead of an empty table.
- `structural_data_artifacts` must exist, its rows use fixed fields, and `rows` must contain at least one item.
- `dependencies` must exist and its rows use fixed fields: `dependency_name`, `dependency_type`, `used_by`, `purpose`, and `notes`.
- `dependencies.rows` may be empty. If empty, the final Markdown renders `未识别到需要在结构设计阶段单独说明的外部依赖项。`
- `dependencies` describes external, environment, tool, file, template, service, or product dependencies that need structural explanation. Internal module dependencies belong in chapter 3 module relationship diagrams or chapter 7 collaboration relationships.
- `extra_diagrams` are allowed only for a single clear subject, such as product flow or template dependency. There is no recommended combined diagram for this chapter.

### Chapter 7: Cross-Module Collaboration

Chapter 7 is named `跨模块协作关系`. It explains how multiple modules work together. It must not repeat the per-module interface details from chapter 4.

```json
{
  "cross_module_collaboration": {
    "summary": "",
    "notes": [],
    "collaboration_scenarios": {
      "rows": [
        {
          "scenario": "",
          "initiator_module_id": "MOD-001",
          "participant_module_ids": [],
          "collaboration_method": "",
          "description": ""
        }
      ]
    },
    "collaboration_relationship_diagram": {
      "id": "MER-COLLABORATION-RELATIONSHIP",
      "kind": "collaboration_relationship",
      "title": "跨模块协作关系图",
      "diagram_type": "flowchart",
      "description": "展示多个模块在协作场景中的调用、消息、数据传递或控制流。",
      "source": "",
      "confidence": "observed"
    },
    "extra_tables": [],
    "extra_diagrams": []
  }
}
```

Rules:

- `collaboration_scenarios` must exist and its rows use fixed fields: `scenario`, `initiator_module_id`, `participant_module_ids`, `collaboration_method`, and `description`.
- `collaboration_scenarios.rows` must contain at least one collaboration scenario.
- `initiator_module_id` and `participant_module_ids` should reference module IDs from `architecture_views.module_intro.rows`.
- `collaboration_relationship_diagram` must exist.
- `collaboration_relationship_diagram.diagram_type` must be one of the supported Mermaid diagram types.
- `collaboration_relationship_diagram.source` must be non-empty and pass Mermaid validation.
- This chapter describes cross-module collaboration only. It must not duplicate chapter 4 external interface tables or turn into a function signature list.

### Chapter 8: Key Flows

Chapter 8 is named `关键流程`. It explains the most important end-to-end flows. The flow index table is an index, not the whole content: every listed flow must have a matching detail node and a Mermaid diagram.

```json
{
  "key_flows": {
    "summary": "",
    "notes": [],
    "flow_index": {
      "rows": [
        {
          "flow_id": "FLOW-001",
          "flow_name": "",
          "trigger_condition": "",
          "participants": [],
          "main_steps": "",
          "output_result": "",
          "notes": ""
        }
      ]
    },
    "flows": [
      {
        "flow_id": "FLOW-001",
        "name": "",
        "overview": "",
        "steps": [],
        "branches_or_exceptions": [],
        "related_modules": [],
        "diagram": {
          "id": "MER-FLOW-001",
          "kind": "key_flow",
          "title": "关键流程图",
          "diagram_type": "flowchart",
          "description": "",
          "source": "",
          "confidence": "observed"
        }
      }
    ],
    "extra_tables": [],
    "extra_diagrams": []
  }
}
```

Rules:

- `flow_index` must exist and its rows use fixed fields: `flow_id`, `flow_name`, `trigger_condition`, `participants`, `main_steps`, `output_result`, and `notes`.
- `flow_index.rows` must contain at least one key flow.
- Every `flow_index.rows[].flow_id` must match exactly one `flows[].flow_id`.
- Every `flows[].flow_id` must appear exactly once in `flow_index.rows`.
- Every flow must have non-empty `name`, `overview`, and `steps`.
- Every flow must have a `diagram`.
- Every flow diagram must use a supported Mermaid `diagram_type`.
- Every flow diagram `source` must be non-empty and pass Mermaid validation.

### Chapter 9: Structure Issues and Suggestions

Chapter 9 is named `结构问题与改进建议`. It is intentionally free-form so Codex can summarize useful structural observations without forcing another table model.

```json
{
  "structure_issues_and_suggestions": ""
}
```

Rules:

- `structure_issues_and_suggestions` is a string.
- It may be an empty string.
- Codex may write lightweight Markdown text in this string, such as paragraphs, unordered lists, ordered lists, emphasis, inline code, or headings at level 2 or deeper.
- It must not contain level-1 headings, Mermaid code blocks, Markdown tables, unbalanced fenced code blocks, HTML blocks, embedded diagrams, raw graph definitions, or structured table/diagram objects.
- If empty, the final Markdown renders `未识别到明确的结构问题与改进建议。`

### Source Snippet Rules

Source snippets are optional evidence, not design content.

```json
{
  "source_snippets": [
    {
      "id": "SNIP-001",
      "path": "src/main.py",
      "line_start": 12,
      "line_end": 28,
      "language": "python",
      "purpose": "证明 CLI 入口调用文档生成流程",
      "content": "",
      "confidence": "observed"
    }
  ]
}
```

Rules:

- Source snippets may support observed facts such as entrypoints, module boundaries, dependency relations, or flow evidence.
- Each snippet must include `id`, `path`, `line_start`, `line_end`, `language`, `purpose`, `content`, and `confidence`.
- Each snippet should be short, preferably no more than 20 lines. Longer snippets should produce at least a validation warning.
- Snippets must not define new APIs, structs, enums, data models, or implementation logic.
- Snippets must not substitute for module responsibility, interface requirement, internal structure, or flow descriptions.
- Rendered snippets appear near the relevant module, runtime unit, collaboration scenario, or flow only when helpful. They must not become a standalone appendix.
- If a snippet is used, `confidence` should normally be `observed`.

### Support Data Rendering Rules

Support data does not become standalone Markdown chapters.

- `evidence`: referenced through `evidence_refs` on related modules, capabilities, runtime units, collaborations, or flows when the schema explicitly allows those refs, and rendered near those items as `依据：EV-001, EV-002`.
- `traceability`: referenced through `traceability_refs` on related modules, capabilities, or flows when the schema explicitly allows those refs, and rendered near those items as `关联来源：REQ-001 / NOTE-002`.
- `risks`: appended to the end of chapter 9 under `风险` when present.
- `assumptions`: appended to the end of chapter 9 under `假设` when present.
- Low-confidence key items with `confidence: unknown` are summarized at the end of chapter 9 under `低置信度项`.
- `source_snippets`: rendered only near items that reference them through `source_snippet_refs`.

## Markdown Document Structure

`STRUCTURE_DESIGN.md` should use a stable single-file outline:

```text
# 软件结构设计说明书

1. 文档信息
2. 系统概览
3. 架构视图
4. 模块设计
5. 运行时视图
6. 配置、数据与依赖关系
7. 跨模块协作关系
8. 关键流程
9. 结构问题与改进建议
```

The final document always keeps the fixed chapters. Section-specific non-empty rules override the general fallback. Missing required content means the DSL is invalid and Codex must revise its structured content before rendering.

The chapters render as follows:

```text
1. 文档信息
   - Compact document metadata table.

2. 系统概览
   - System summary, purpose, core capabilities, and brief notes.

3. 架构视图
   3.1 架构概述
   3.2 各模块介绍
   3.3 模块关系图
   3.4 补充架构图表

4. 模块设计
   4.x 模块名
   4.x.1 模块概述
   4.x.2 模块职责
   4.x.3 对外能力说明
   4.x.4 对外接口需求清单
   4.x.5 模块内部结构关系图
   4.x.6 补充说明

5. 运行时视图
   5.1 运行时概述
   5.2 运行单元说明
   5.3 运行时流程图
   5.4 运行时序图（推荐，存在时渲染）
   5.5 补充运行时图表

6. 配置、数据与依赖关系
   6.1 配置项说明
   6.2 关键结构数据与产物
   6.3 依赖项说明
   6.4 补充图表

7. 跨模块协作关系
   7.1 协作关系概述
   7.2 跨模块协作说明
   7.3 跨模块协作关系图
   7.4 补充协作图表

8. 关键流程
   8.1 关键流程概述
   8.2 关键流程清单
   8.x 流程名
   8.x.1 流程概述
   8.x.2 步骤说明
   8.x.3 异常/分支说明
   8.x.4 流程图

9. 结构问题与改进建议
   - Free-form Markdown string, or a fixed empty-state sentence.
```

## Mermaid Requirements

All diagrams in the final Markdown must be Mermaid code blocks:

````markdown
```mermaid
flowchart TD
  A[输入] --> B[处理]
```
````

Mermaid diagrams are section-local child nodes. The DSL does not use global diagram routing metadata.

Core `diagram_type` values are fully supported and tested in the MVP:

```json
[
  "flowchart",
  "graph",
  "sequenceDiagram",
  "classDiagram",
  "stateDiagram-v2"
]
```

Extended `diagram_type` values are allowed in strict mode, but receive only lightweight static checks in the MVP:

```json
[
  "erDiagram",
  "requirementDiagram",
  "C4Context",
  "C4Container",
  "C4Component",
  "C4Dynamic"
]
```

Unsupported in the MVP: `journey`, `gantt`, `timeline`, `mindmap`, and `quadrantChart`.

`validate_mermaid.py` should validate Mermaid text without network access. Because the skill is expected to support Mermaid reliably rather than maintain a partial custom grammar, strict validation should delegate to local Mermaid CLI tooling. If strict validation tooling is unavailable, the script must say so clearly and must not claim that diagrams were proven renderable.

Strict validation requires local dependencies:

- `node`
- `@mermaid-js/mermaid-cli`
- `mmdc` available on `PATH`

The script should provide three modes:

- `--strict`: use local Mermaid tooling to parse or render-check diagram source. This is the default mode for final document generation.
- `--static`: run deterministic checks that catch common structural mistakes. This mode is useful for tests and quick feedback, but it is not a substitute for strict validation.
- `--check-env`: report whether strict validation dependencies are available.

Static checks:

- Code block language is `mermaid`.
- Diagram body is non-empty.
- `diagram_type` is one of the supported core or extended enum values.
- The first meaningful line is compatible with `diagram_type` for core diagram types.
- Markdown fences are balanced.
- Disallowed Graphviz/DOT constructs such as `digraph`, `rankdir`, and `node -> node;` are rejected when they appear as diagram source. Mermaid arrows such as `-->` and `->>` remain allowed.
- Diagram IDs are unique.

The script should fail closed for malformed diagram blocks. It should print actionable errors that name the diagram ID and field path.

## Script Responsibilities

### `validate_dsl.py`

Validates the complete JSON DSL against `schemas/structure-design.schema.json` and performs semantic checks that JSON Schema cannot express well.

Core checks:

- Required top-level fields exist.
- IDs are unique within their collections.
- References point to existing IDs.
- `confidence` values use the allowed enum.
- Required document sections can be rendered.
- DSL instances do not contain validation policy fields such as `empty_allowed`, `required`, `min_rows`, `max_rows`, or `render_when_empty`.
- Fixed table nodes do not contain `id`, `title`, or `columns`; they contain `rows`, and row objects contain only schema-approved content fields and support metadata.
- Extra table nodes include `id`, `title`, `columns`, and `rows`.
- Chapter 3 has the module introduction table and module relationship diagram.
- Chapter 3 module IDs are unique.
- Chapter 4 covers every module listed in chapter 3 by matching `module_design.modules[].id` to `architecture_views.module_intro.rows[].module_id`.
- Chapter 4 module details have non-empty provided capability rows and non-empty internal structure information.
- Chapter 5 has at least one runtime unit and a non-empty runtime flow diagram.
- Chapter 6 allows empty configuration item and dependency tables but requires non-empty structural data/artifact rows.
- Chapter 7 has at least one collaboration scenario and a non-empty collaboration relationship diagram.
- Chapter 8 has at least one key flow, the flow index and `flows` array are one-to-one by `flow_id`, and every listed flow has a non-empty Mermaid diagram.
- Chapter 9 is a string, may be empty, and uses only allowed lightweight Markdown.
- Source snippets satisfy path, line, language, purpose, content, confidence, and length rules.

### `validate_mermaid.py`

Extracts and validates Mermaid definitions from DSL or rendered Markdown. It does not render images. It exists to keep diagram correctness visible and independently testable.

### `render_markdown.py`

Renders `STRUCTURE_DESIGN.md` from the DSL and `templates/STRUCTURE_DESIGN.md.tpl` using Python standard-library rendering. It should not invent content. Missing optional content is rendered as a short explicit statement rather than silently disappearing.

## Error Handling

Validation failures should stop rendering. Rendering failures should preserve the DSL and temporary working directory so the issue can be inspected. Error messages should include the failing file, JSON path or diagram ID, and a short correction hint.

If Codex lacks enough content to populate a section that is allowed to be empty, it should use the section's documented empty representation rather than making up facts.

If Codex lacks enough content to populate a required non-empty section, final generation must stop and require Codex to revise its structured content. Chapter 4 missing module-level capabilities or internal structure requires revising module design. Missing a function call graph alone does not require module re-partitioning.

If Mermaid strict validation tooling is unavailable, final generation should stop with a clear message unless the user explicitly accepts static-only validation for that run.

## Testing Strategy

Tests should cover:

- The two example DSL files validate successfully.
- Missing required fields fail validation with clear errors.
- Invalid references fail validation.
- Invalid `confidence` values fail validation.
- Mermaid diagrams with Graphviz/DOT syntax fail validation.
- Valid Mermaid examples across MVP core diagram types pass lightweight validation.
- Rendering creates exactly one `STRUCTURE_DESIGN.md`.
- Rendered Markdown includes balanced fences and no Graphviz code block.
- Chapter 3 fails validation if the fixed module introduction table or required module relationship diagram is missing.
- Chapter 3 and chapter 4 fail validation if module IDs do not match one-to-one.
- Required fixed tables fail validation if they contain `columns`; extra tables fail validation if they omit `columns`.
- Chapter 4 fails validation if any listed module lacks a provided capability row.
- Chapter 4 fails validation if any listed module lacks both an internal structure diagram and textual internal structure.
- Chapter 5 fails validation if runtime units are empty or runtime flow Mermaid source is missing.
- Chapter 6 passes validation with empty configuration item and dependency tables but fails if structural data/artifacts are empty.
- Chapter 7 fails validation if collaboration scenarios are empty or the collaboration diagram source is missing.
- Chapter 8 fails validation if flow index rows and `flows` entries do not match one-to-one by `flow_id`, or if any flow lacks a Mermaid diagram.
- Chapter 9 accepts an empty string.
- Chapter 9 fails validation for level-1 headings, Mermaid code blocks, Markdown tables, unbalanced fences, or HTML blocks.
- Source snippet tests cover required fields, line range sanity, and warning/failure behavior for long snippets.
- DSL examples and tests prove that `empty_allowed` and similar validation policy fields do not appear in JSON instances.

## Examples

Two example DSL files are required:

- `minimal-from-code.dsl.json`: describes a document generated after Codex has understood an existing codebase.
- `minimal-from-requirements.dsl.json`: describes a document generated from requirements or design notes without an implemented codebase.

The examples should stay small enough to read quickly but complete enough to exercise every required top-level DSL section.

## Implementation Notes

The first implementation should avoid optional Python dependencies. Python standard library is preferred for JSON validation glue, Markdown rendering, and tests. Mermaid validation is the exception: strict Mermaid confidence should come from local Mermaid CLI tooling rather than an incomplete hand-written grammar.

The skill should keep `SKILL.md` concise. Detailed DSL fields, document outline, Mermaid rules, and review criteria belong in `references/` so Codex loads them only when needed.

## Review Checklist

Before implementation begins, verify:

- The design keeps project understanding outside the skill.
- The output contract is one `STRUCTURE_DESIGN.md`.
- Final output path and temporary work directory rules are explicit.
- Mermaid is the only supported diagram output.
- Mermaid validation script is named `validate_mermaid.py` and final generation defaults to strict validation.
- Graphviz is fully removed.
- Temporary JSON files are allowed but not part of the final deliverable.
- The DSL includes confidence and evidence support.
- DSL instances contain content only, while requiredness and emptiness rules live in schema, validator code, and reference documentation.
- Fixed tables keep columns in renderer/schema/reference, not in DSL instances.
- Tests cover schema, Mermaid validation, and Markdown rendering.
- The design is small enough for one implementation plan.
