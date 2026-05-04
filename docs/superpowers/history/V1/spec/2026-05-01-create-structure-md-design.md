# create-structure-md Skill Design

## Status

Ready for user review.

## Purpose

`create-structure-md` is a local personal Codex skill for creating a single software structure design document. It does not analyze code, infer requirements, run repository intelligence tools, or decide what the system means. Codex performs any code or requirement understanding outside the skill. This skill only turns Codex-prepared structured design content into a validated module- or system-specific Markdown file named by `document.output_file`.

The skill optimizes for document quality, repeatability, and renderable Mermaid diagrams. Mermaid is a first-class output surface, not a decorative afterthought.

## Confirmed Requirements

- Skill name: `create-structure-md`.
- Scope: local personal skill.
- Final output: one Markdown file named by Codex through `document.output_file`.
- Output file names must be module- or system-specific, typically `<documented-object-name>_STRUCTURE_DESIGN.md`, and must not use a generic-only filename.
- Intermediate outputs: one or more JSON DSL files may be created in a temporary working directory.
- Language: Chinese by default, with English terms where they are clearer or conventional.
- Mermaid only: Graphviz, DOT, SVG files, and image export are out of scope as final deliverables.
- Mermaid diagrams are written as Markdown Mermaid code blocks; no final image files are generated.
- `validate_mermaid.py` is an independent script because Mermaid validity is critical.
- DSL coverage is complete for the document, not only a minimal subset.
- Key design items and fixed table rows that represent design items carry confidence according to the DSL schema: `observed`, `inferred`, or `unknown`. Index-only rows such as `flow_index.rows[]` do not carry confidence; their matching detail objects carry it.
- DSL JSON contains document content only. Validation policy fields such as `empty_allowed`, `required`, `min_rows`, or rendering control flags must not appear in DSL instances.
- Necessary source snippets are allowed when they improve the document.
- Architecture issues such as cycles, reverse dependencies, and unclear ownership are recorded honestly when Codex supplies them.
- The final Markdown uses fixed 9 chapters. Section-specific non-empty rules are enforced by Python validation scripts and documented for Codex before it writes the DSL.
- Runtime Python dependencies are explicit and minimal. `jsonschema` is required for schema validation; Jinja2 is not used.
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
- Automatically delete the skill working directory or generated artifacts.

## Alternatives Considered

### Full Repository Analysis Pipeline

The old direction used static analysis scripts, repository facts, evidence indexes, and rendering. That is too broad for this skill. It mixes two responsibilities: understanding a project and creating a document. The user explicitly narrowed the skill to document creation.

### Direct Markdown Generation

Codex could write the final Markdown directly from its understanding. This is simple, but it gives up validation, reusable examples, Mermaid checks, and consistent structure. It also makes later improvements hard because document shape is embedded in free-form Markdown.

### DSL-Driven Single Document

This is the selected approach. Codex creates a complete JSON DSL in a temporary directory, validates the DSL, validates Mermaid blocks independently, and renders a single Markdown file programmatically. This keeps the skill focused while preserving quality gates.

## Proposed Skill Structure

```text
create-structure-md/
├── SKILL.md
├── requirements.txt
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
├── examples/
│   ├── minimal-from-code.dsl.json
│   └── minimal-from-requirements.dsl.json
└── tests/
    ├── test_validate_dsl.py
    ├── test_validate_mermaid.py
    └── test_render_markdown.py
```

`requirements.txt` contains required Python runtime dependencies:

```text
jsonschema
```

Testing uses Python standard library `unittest`; no third-party test framework is required in the MVP.

`requirements.txt` contains runtime dependencies only. The MVP does not require `requirements-dev.txt`, `pytest`, or any other third-party test dependency.

Test command:

```bash
python -m unittest discover -s tests
```

Jinja2 is intentionally not used in the MVP. Markdown rendering is code-driven so fixed chapter order, fixed table headers, empty states, support-data insertion, and Markdown escaping stay under deterministic renderer control.

## SKILL.md Contract

`SKILL.md` must include YAML front matter.

Required front matter:

```yaml
---
name: create-structure-md
description: Use when the user asks Codex to generate a single module-specific software structure design document, such as <documented-object-name>_STRUCTURE_DESIGN.md, from already-prepared structured design content using the create-structure-md DSL and Mermaid diagrams. Do not use for repo analysis, requirements inference, multi-document generation, Word/PDF output, or image export.
---
```

Rules:

- `name` must be exactly `create-structure-md`.
- `description` must mention `software structure design document`, `STRUCTURE_DESIGN.md`, `DSL`, and `Mermaid`.
- `description` must explicitly exclude repo analysis, requirements inference, multi-document generation, Word/PDF output, and image export.
- The description should make clear that the final file is module- or system-specific rather than the generic-only `STRUCTURE_DESIGN.md`.

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
- confidence values and support-data references where the schema requires or allows them
- evidence references or source snippets when available and safe to disclose

If these inputs are not available, Codex must not invoke the renderer and must not invent missing content to satisfy validation. Codex should first perform project or requirements understanding outside this skill, then create the DSL and invoke this skill.

## Skill Workflow

1. Codex understands the target codebase, requirements, or user-provided notes outside this skill.
2. Codex invokes `create-structure-md` when the user asks for a software structure design document.
3. The skill instructs Codex to create a temporary working directory.
4. Codex writes one complete DSL JSON file and may write smaller staged JSON files first.
5. Codex runs `validate_dsl.py structure.dsl.json` against the complete DSL.
6. Codex runs `validate_mermaid.py --from-dsl structure.dsl.json --strict` to validate Mermaid diagram blocks.
7. Codex runs `render_markdown.py structure.dsl.json --output-dir ...` to create the Markdown file named by `document.output_file`.
8. Codex runs `validate_mermaid.py --from-markdown <output-file> --static` to verify renderer-produced Mermaid fences and non-empty blocks.
9. Codex reviews the generated document with `references/review-checklist.md`.
10. Codex reports the output path, temporary working directory path, and any assumptions or low-confidence items.

Temporary files in the skill working directory are not automatically deleted. If cleanup is needed, Codex should provide the command for the user to run. Tool-local temporary files created by strict Mermaid validation may be cleaned up only when `--work-dir` is not provided.

## Output Location

Default final output path:

- If the user provides an output directory, write `document.output_file` there.
- Otherwise write `document.output_file` to the target repository root, or to the current working directory when no target repository root is known.
- The final file name must be a safe Markdown filename chosen by Codex and must include the documented module, subsystem, system, or scope name.
- Recommended filename format: `<documented-object-name>_STRUCTURE_DESIGN.md`.
- `<documented-object-name>` must come from the actual documented module, subsystem, system, or scope, not from a generic prefix such as `software`, `structure`, or `design`.
- Generic-only filenames are forbidden, including `STRUCTURE_DESIGN.md`, `structure_design.md`, `design.md`, and `软件结构设计说明书.md`.
- The file name must end with `.md`, must not contain path separators `/` or `\`, must not contain `..`, and must not contain control characters. Spaces should be normalized to `_`.

Temporary work directory:

- Preferred: `<workspace>/.codex-tmp/create-structure-md-<run-id>/`.
- Fallback: system temp directory, such as `/tmp/create-structure-md-<run-id>`, if the workspace temp directory cannot be created.
- Temporary files in this working directory are not automatically deleted. Codex reports the temporary work directory path after generation.
- The workspace `.gitignore` should include `.codex-tmp/` unless the user intentionally wants to version temporary artifacts. Codex should not edit `.gitignore` automatically unless requested.

Output overwrite policy:

- `render_markdown.py` must not overwrite an existing output file by default.
- If the target file already exists, default rendering fails with a clear message.
- `--overwrite` explicitly replaces the existing output file.
- `--backup` first preserves the existing file as `<output_file>.bak-<YYYYMMDD_HHMMSS>`, then writes the new output.
- The backup timestamp comes from the local system clock when `render_markdown.py` runs and uses `%Y%m%d_%H%M%S`.
- `--backup` and `--overwrite` are mutually exclusive.
- If the computed backup path already exists, rendering fails and tells the user to retry. It must not overwrite or delete an existing backup.

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

Important repeated fields and metadata:

- `id`: stable local identifier.
- `name`: human-readable Chinese name.
- `description`: concise explanation.
- `confidence`: `observed`, `inferred`, or `unknown`.
- `evidence_refs`: references to evidence items supplied in the DSL.
- `traceability_refs`: references to traceability items supplied in the DSL.
- `source_snippet_refs`: references to safe source snippets supplied in the DSL.
- `notes`: short supplemental notes where needed.

Common metadata, when allowed by a schema object, has this shape:

```json
{
  "confidence": "observed",
  "evidence_refs": [],
  "traceability_refs": [],
  "source_snippet_refs": []
}
```

Rules:

- `confidence` must be `observed`, `inferred`, or `unknown`.
- `evidence_refs` must reference `evidence[].id`.
- `traceability_refs` must reference `traceability[].id`.
- `source_snippet_refs` must reference `source_snippets[].id`.
- Whitelisted design content items with `confidence: unknown` are automatically summarized by the renderer at the end of chapter 9 under `低置信度项`.

ID prefix conventions:

- Module IDs use `MOD-...`.
- Capability IDs use `CAP-...`.
- Runtime unit IDs use `RUN-...`.
- Flow IDs use `FLOW-...`.
- Configuration item IDs use `CFG-...`.
- Data/artifact IDs use `DATA-...`.
- Dependency IDs use `DEP-...`.
- Collaboration IDs use `COL-...`.
- Flow step IDs use `STEP-...`.
- Flow branch/exception IDs use `BR-...`.
- Mermaid diagram IDs use `MER-...`.
- Extra table IDs use `TBL-...`.
- Evidence IDs use `EV-...`.
- Traceability IDs use `TR-...`.
- Risk IDs use `RISK-...`.
- Assumption IDs use `ASM-...`.
- Source snippet IDs use `SNIP-...`.

The validator checks prefixes and uniqueness, but the MVP does not require a strict three-digit numeric suffix. IDs such as `MOD-001` and `MOD-RENDER-001` are both acceptable when unique.

ID field policy:

- Fields listed in `Defining ID fields` define IDs.
- Fields listed in `Reference ID fields` must reference existing IDs.
- `key_flows.flow_index.rows[].flow_id` and `key_flows.flows[].flow_id` are paired identity fields for the same flow and must match one-to-one.
- `traceability[].source_external_id` is an external source identifier and is not an internal DSL reference.
- Any other `_id` or `_ids` field is invalid unless the schema explicitly allows it and this section registers it.
- Free-text fields must not be used for cross-node references.

Defining ID fields:

| Field | Defines |
| --- | --- |
| `architecture_views.module_intro.rows[].module_id` | canonical module ID |
| `system_overview.core_capabilities[].capability_id` | core capability ID |
| `module_design.modules[].external_capability_details.provided_capabilities.rows[].capability_id` | provided capability ID |
| `runtime_view.runtime_units.rows[].unit_id` | runtime unit ID |
| `configuration_data_dependencies.configuration_items.rows[].config_id` | configuration item ID |
| `configuration_data_dependencies.structural_data_artifacts.rows[].artifact_id` | data/artifact ID |
| `configuration_data_dependencies.dependencies.rows[].dependency_id` | dependency ID |
| `cross_module_collaboration.collaboration_scenarios.rows[].collaboration_id` | collaboration scenario ID |
| `key_flows.flow_index.rows[].flow_id` | paired flow identity |
| `key_flows.flows[].flow_id` | paired flow identity |
| `key_flows.flows[].steps[].step_id` | globally unique flow step ID |
| `key_flows.flows[].branches_or_exceptions[].branch_id` | globally unique branch/exception ID |
| Mermaid diagram `id` fields | Mermaid diagram ID |
| `extra_tables[].id` | extra table ID |
| `evidence[].id` | evidence ID |
| `traceability[].id` | traceability ID |
| `risks[].id` | risk ID |
| `assumptions[].id` | assumption ID |
| `source_snippets[].id` | source snippet ID |

Reference ID fields:

| Field | References |
| --- | --- |
| `module_design.modules[].module_id` | `architecture_views.module_intro.rows[].module_id` |
| `runtime_view.runtime_units.rows[].related_module_ids` | module IDs |
| `cross_module_collaboration.collaboration_scenarios.rows[].initiator_module_id` | module ID |
| `cross_module_collaboration.collaboration_scenarios.rows[].participant_module_ids` | module IDs |
| `key_flows.flow_index.rows[].participant_module_ids` | module IDs |
| `key_flows.flow_index.rows[].participant_runtime_unit_ids` | runtime unit IDs |
| `key_flows.flows[].related_module_ids` | module IDs |
| `key_flows.flows[].related_runtime_unit_ids` | runtime unit IDs |
| `key_flows.flows[].steps[].related_module_ids` | module IDs |
| `key_flows.flows[].steps[].related_runtime_unit_ids` | runtime unit IDs |
| `key_flows.flows[].branches_or_exceptions[].related_module_ids` | module IDs |
| `key_flows.flows[].branches_or_exceptions[].related_runtime_unit_ids` | runtime unit IDs |
| `evidence_refs` | `evidence[].id` |
| `traceability_refs` | `traceability[].id` |
| `source_snippet_refs` | `source_snippets[].id` |
| `traceability[].target_id` | ID resolved by `traceability[].target_type` mapping |

Array field defaults:

- Object-level `notes` and fields ending with `_notes` are arrays of non-empty plain-text strings unless explicitly specified otherwise.
- `responsibilities` is an array of non-empty plain-text strings.
- Empty strings inside these arrays are invalid.
- Table-row `notes` fields are plain-text strings, not arrays.

Markdown safety:

- All DSL string fields are plain text unless the field name explicitly ends with `_markdown`, the field is `structure_issues_and_suggestions`, the field is a Mermaid diagram `source`, or the field is `source_snippets[].content`.
- Plain text fields must not inject Markdown structure into the final document.
- The renderer must escape Markdown-sensitive content in plain text fields, including table pipes, table-cell newlines, fenced-code markers, leading heading markers, and raw HTML blocks.
- Mermaid diagram `source` fields must contain Mermaid source only and must not contain Markdown fences. The renderer adds the final Mermaid code fences.
- Source snippet content is rendered as evidence code and must be fenced or escaped safely by the renderer so it cannot break the surrounding Markdown.

Structure-design boundary lint:

- Prototype/detail-design lint applies to all normal plain-text fields and Markdown-capable chapter 9 text.
- The lint does not apply to Mermaid diagram `source` or `source_snippets[].content`.
- High-risk code-definition patterns in normal design text fail validation, including C/C++ function prototype-like lines, Python `def`/`class` definition-like lines, `typedef struct`, `typedef enum`, `enum { ... }`, `class { ... }`, full parameter-list style API definitions, and large code-like blocks outside source snippets.
- Function names and existing identifiers may still appear as short observed evidence or capability names when they are not written as prototypes, data definitions, or implementation blocks.

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
    "module_relationship_diagram": {
      "id": "MER-ARCH-MODULES",
      "kind": "module_relationship",
      "title": "",
      "diagram_type": "flowchart",
      "description": "",
      "source": "",
      "confidence": "observed"
    },
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
    "runtime_flow_diagram": {
      "id": "MER-RUNTIME-FLOW",
      "kind": "runtime_flow",
      "title": "",
      "diagram_type": "flowchart",
      "description": "",
      "source": "",
      "confidence": "observed"
    },
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
    "collaboration_relationship_diagram": {
      "id": "MER-COLLABORATION-RELATIONSHIP",
      "kind": "collaboration_relationship",
      "title": "",
      "diagram_type": "flowchart",
      "description": "",
      "source": "",
      "confidence": "observed"
    },
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

Optional diagram fields such as `runtime_sequence_diagram` may be omitted from the DSL. When present, they must use the full diagram object shape rather than `{}`.

### Authoritative Field Contract

JSON examples in this spec illustrate shape, but schema, validator, and renderer behavior must follow this authoritative field contract plus the chapter-specific rules.

| Field | Required in schema | May be empty | Semantic required | Rendering position | Notes |
| --- | --- | --- | --- | --- | --- |
| `dsl_version` | yes | no | yes | not rendered | Schema version. |
| `document` | yes | no | yes | Chapter 1 | Contains output filename and document metadata. |
| `document.output_file` | yes | no | yes | Output path and Chapter 1 | Codex-chosen safe filename; recommended `<documented-object-name>_STRUCTURE_DESIGN.md`; generic-only filenames forbidden. |
| `system_overview` | yes | no | yes | Chapter 2 |  |
| `system_overview.summary` | yes | no | yes | Chapter 2 intro |  |
| `system_overview.purpose` | yes | no | yes | Chapter 2 |  |
| `architecture_views` | yes | no | yes | Chapter 3 |  |
| `architecture_views.summary` | yes | no | yes | 3.1 |  |
| `architecture_views.module_intro` | yes | no | yes | 3.2 | Must contain at least one row. |
| `architecture_views.module_relationship_diagram` | yes | no | yes | 3.3 | Full diagram object with non-empty `source`. |
| `module_design` | yes | no | yes | Chapter 4 |  |
| `module_design.summary` | yes | no | yes | Chapter 4 intro | Rendered before per-module subsections. |
| `module_design.modules` | yes | no | yes | 4.x subsections | One-to-one with chapter 3 modules. |
| `runtime_view` | yes | no | yes | Chapter 5 |  |
| `runtime_view.summary` | yes | no | yes | 5.1 |  |
| `runtime_view.runtime_units` | yes | no | yes | 5.2 | Must contain at least one row. |
| `runtime_view.runtime_flow_diagram` | yes | no | yes | 5.3 | Full diagram object with non-empty `source`. |
| `runtime_view.runtime_sequence_diagram` | no | yes | no | 5.4 | Omitted or full diagram object. Empty source renders fixed empty state. |
| `configuration_data_dependencies` | yes | no | yes | Chapter 6 |  |
| `configuration_data_dependencies.summary` | yes | yes | no | Chapter 6 intro | Empty summary is allowed to avoid invented content. |
| `configuration_data_dependencies.configuration_items` | yes | yes | no | 6.1 | Empty table renders fixed empty state. |
| `configuration_data_dependencies.structural_data_artifacts` | yes | yes | no | 6.2 | Empty table renders fixed empty state. |
| `configuration_data_dependencies.dependencies` | yes | yes | no | 6.3 | Empty table renders fixed empty state. |
| `cross_module_collaboration` | yes | no | yes | Chapter 7 |  |
| `cross_module_collaboration.summary` | yes | yes | conditional | 7.1 | Multi-module content should summarize collaboration; single-module may be empty. |
| `cross_module_collaboration.collaboration_scenarios` | yes | conditional | conditional | 7.2 | Required non-empty only when module count is at least two. |
| `cross_module_collaboration.collaboration_relationship_diagram` | no | yes | conditional | 7.3 | Required with non-empty `source` only when module count is at least two. |
| `key_flows` | yes | no | yes | Chapter 8 |  |
| `key_flows.summary` | yes | no | yes | 8.1 |  |
| `key_flows.flow_index` | yes | no | yes | 8.2 | Index-only table. |
| `key_flows.flows` | yes | no | yes | 8.x subsections | One detail node per flow index row. |
| `structure_issues_and_suggestions` | yes | yes | no | Chapter 9 | Empty state depends on risks, assumptions, and low-confidence items. |
| `extra_tables` | yes where present in chapter objects | yes | no | chapter-specific supplement section | Empty arrays render fixed empty state in fixed numbered sections. |
| `extra_diagrams` | yes where present in chapter objects | yes | no | chapter-specific supplement section | Items, when present, must have non-empty `source`. |
| `evidence`, `traceability`, `risks`, `assumptions`, `source_snippets` | yes | yes | no | support data / Chapter 9 appendices | Support data does not create standalone chapters. |

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

Extra table rules:

- `columns[].key` must be unique.
- `columns[].title` must be non-empty.
- Rows may use only declared column keys plus `evidence_refs` in the MVP.
- Extra table rows must not use `traceability_refs` or `source_snippet_refs` in the MVP because they do not have stable row IDs or traceability target mappings.
- Missing declared column keys render as empty strings.
- Unknown row keys fail validation.

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

MVP Mermaid `diagram_type` values are fully supported and tested:

```json
[
  "flowchart",
  "graph",
  "sequenceDiagram",
  "classDiagram",
  "stateDiagram-v2"
]
```

Mermaid diagrams are embedded under the section that renders them. There is no global diagram routing field and no attempt to model Mermaid nodes or edges in the DSL.

The MVP validates Mermaid syntax and performs only lightweight coverage warnings. It does not prove that diagram edges semantically match module relationships, runtime paths, collaboration scenarios, or flow steps.

All other Mermaid diagram types are not supported in the MVP.

Diagram field policy:

- Required diagram fields must be full diagram objects with non-empty `source`.
- Optional diagram fields may be omitted entirely, or may be present as full diagram objects with `source` possibly empty.
- Empty object `{}` is not allowed for any diagram field.
- Optional diagrams with empty `source` are skipped by the renderer and by `validate_mermaid.py --from-dsl`.
- Any `extra_diagrams[]` item must be a full diagram object with non-empty `source`; optionality is expressed by omitting the extra diagram item, not by including an empty diagram.

### Validation Policy Outside DSL

DSL instances must not include validation policy fields. In particular, JSON written by Codex must not contain `empty_allowed`, `required`, `min_rows`, `max_rows`, `render_when_empty`, or similar control fields. The DSL says what the document contains; `validate_dsl.py` decides whether that content is sufficient.

The selected policy split is:

- `schemas/structure-design.schema.json` enforces structural shape, required object fields, primitive types, fixed table row content/metadata fields, enum values, and unknown-field rejection.
- Schema objects should use `additionalProperties: false` by default.
- Extra table row objects are an exception: their allowed keys come from `columns[].key` plus `evidence_refs` in the MVP and are checked by `validate_dsl.py`.
- Future extension objects may explicitly opt into additional properties, but must document why.
- `validate_dsl.py` must use the required `jsonschema` Python dependency to validate `schemas/structure-design.schema.json` before running semantic checks.
- `validate_dsl.py` then enforces semantic rules that need project-wide knowledge: non-empty table rows, one-to-one references, module coverage, flow coverage, and Mermaid source presence.
- `references/dsl-spec.md` and `references/document-structure.md` tell Codex which fields are required before it writes the DSL.
- `render_markdown.py` assumes the DSL has already passed validation. It renders optional empty content with fixed wording, escapes plain text, owns fixed table headers, and programmatically generates the fixed 9 chapters.

Requiredness is documented as rules beside each chapter below, not encoded as fields in JSON examples.

### Support Data Structures

Support data is referenced by design nodes and rendered near those nodes or at the end of chapter 9. It does not become standalone Markdown chapters.

```json
{
  "evidence": [
    {
      "id": "EV-001",
      "kind": "source",
      "title": "",
      "location": "",
      "description": "",
      "confidence": "observed"
    }
  ],
  "traceability": [
    {
      "id": "TR-001",
      "source_external_id": "REQ-001",
      "source_type": "requirement",
      "target_type": "module",
      "target_id": "MOD-001",
      "description": ""
    }
  ],
  "risks": [
    {
      "id": "RISK-001",
      "description": "",
      "impact": "",
      "mitigation": "",
      "confidence": "inferred",
      "evidence_refs": [],
      "traceability_refs": [],
      "source_snippet_refs": []
    }
  ],
  "assumptions": [
    {
      "id": "ASM-001",
      "description": "",
      "rationale": "",
      "validation_suggestion": "",
      "confidence": "unknown",
      "evidence_refs": [],
      "traceability_refs": [],
      "source_snippet_refs": []
    }
  ]
}
```

Rules:

- `evidence[].kind` must be `source`, `requirement`, `note`, or `analysis`.
- `traceability[].source_type` must be `requirement`, `note`, `code`, or `user_input`.
- `traceability[].source_external_id` is an external source identifier such as `REQ-001`; it is not an internal DSL reference.
- `traceability[].target_type` must be `module`, `core_capability`, `provided_capability`, `runtime_unit`, `flow`, `flow_step`, `flow_branch`, `collaboration`, `configuration_item`, `data_artifact`, `dependency`, `risk`, `assumption`, or `source_snippet`.
- `traceability[].target_id` must reference an existing object in the ID collection implied by `target_type`.
- `traceability[].target_type` and `traceability[].target_id` are the authoritative binding.
- `traceability_refs` on design nodes are optional local backlinks. When present, each referenced traceability item must target the current node.
- The renderer may attach traceability entries to target nodes by scanning `traceability[].target_type` and `traceability[].target_id`, even when the target node does not list `traceability_refs`.
- If the same traceability item is found through both authoritative target scanning and local backlinks, the renderer emits it only once.
- `risks` and `assumptions` are appended to chapter 9 by the renderer when present.
- Common metadata is allowed on module introduction rows, `module_design.modules[]`, provided capability rows, runtime unit rows, chapter 6 rows, collaboration scenario rows, flow objects, flow steps, branch/exception items, risks, and assumptions.

Traceability target mapping:

| `target_type` | `target_id` must reference |
| --- | --- |
| `module` | `architecture_views.module_intro.rows[].module_id` |
| `core_capability` | `system_overview.core_capabilities[].capability_id` |
| `provided_capability` | `module_design.modules[].external_capability_details.provided_capabilities.rows[].capability_id` |
| `runtime_unit` | `runtime_view.runtime_units.rows[].unit_id` |
| `flow` | `key_flows.flows[].flow_id` |
| `flow_step` | `key_flows.flows[].steps[].step_id` |
| `flow_branch` | `key_flows.flows[].branches_or_exceptions[].branch_id` |
| `collaboration` | `cross_module_collaboration.collaboration_scenarios.rows[].collaboration_id` |
| `configuration_item` | `configuration_data_dependencies.configuration_items.rows[].config_id` |
| `data_artifact` | `configuration_data_dependencies.structural_data_artifacts.rows[].artifact_id` |
| `dependency` | `configuration_data_dependencies.dependencies.rows[].dependency_id` |
| `risk` | `risks[].id` |
| `assumption` | `assumptions[].id` |
| `source_snippet` | `source_snippets[].id` |

Local `traceability_refs` validation uses this same mapping table to determine whether a referenced traceability entry targets the current node.

Low-confidence summary collection:

- The renderer summarizes `confidence: unknown` only for design content items in this whitelist: `architecture_views.module_intro.rows[]`, `module_design.modules[]`, provided capability rows, `runtime_view.runtime_units.rows[]`, chapter 6 fixed table rows, `cross_module_collaboration.collaboration_scenarios.rows[]`, `key_flows.flows[]`, `key_flows.flows[].steps[]`, and `key_flows.flows[].branches_or_exceptions[]`.
- The low-confidence summary excludes `evidence[]`, `traceability[]`, `source_snippets[]`, `risks[]`, `assumptions[]`, and Mermaid diagram nodes.

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
    "output_file": "create-structure-md_STRUCTURE_DESIGN.md"
  }
}
```

Rules:

- `title`, `project_name`, `document_version`, `status`, `language`, `source_type`, and `output_file` must be non-empty.
- `status` must be `draft`, `reviewed`, or `final`.
- `source_type` must be `code`, `requirements`, `mixed`, or `notes`.
- `generated_at` may be supplied by Codex or filled by the renderer. When present, it should be an ISO-8601 local datetime with timezone when available.
- If `generated_at` is empty, `render_markdown.py` fills the rendered Markdown value but does not mutate the DSL file.
- `language` defaults to `zh-CN`.
- `output_file` must be a safe Markdown filename chosen by Codex and must include the documented module, subsystem, system, or scope name.
- `output_file` should normally follow `<documented-object-name>_STRUCTURE_DESIGN.md`.
- The documented object name must be concrete, such as a module, subsystem, system, package, or tool name; generic prefixes alone are invalid.
- `output_file` must not be a generic-only filename such as `STRUCTURE_DESIGN.md`, `structure_design.md`, `design.md`, or `软件结构设计说明书.md`.

### Chapter 2: System Overview

`system_overview` is intentionally brief. It should not duplicate architecture or module details.

```json
{
  "system_overview": {
    "summary": "",
    "purpose": "",
    "core_capabilities": [
      {
        "capability_id": "CAP-001",
        "name": "",
        "description": "",
        "confidence": "observed"
      }
    ],
    "notes": []
  }
}
```

Rules:

- `system_overview.summary` and `system_overview.purpose` must be non-empty.
- `core_capabilities[].capability_id` must be non-empty, unique across all capability IDs, and use the `CAP-...` prefix.
- Each core capability must have non-empty `name`, `description`, and `confidence`.

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
          "notes": "",
          "confidence": "observed",
          "evidence_refs": [],
          "traceability_refs": [],
          "source_snippet_refs": []
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

- `architecture_views.summary` must be non-empty.
- `module_intro` must exist.
- `module_intro.rows` must include `module_id` plus five visible table fields: `module_name`, `responsibility`, `inputs`, `outputs`, and `notes`, plus common metadata.
- `module_intro.rows[].module_id` is validation metadata, not a visible table column. It must be non-empty and unique.
- Each `module_intro.rows[]` item must have non-empty `module_id`, `module_name`, `responsibility`, and `confidence`.
- `inputs`, `outputs`, and `notes` are optional plain-text fields.
- `module_intro.rows` must contain at least one module. If no module can be identified, Codex must revise its structure understanding before rendering.
- `module_relationship_diagram` must exist.
- `module_relationship_diagram.diagram_type` is not fixed, but it must be one of the supported Mermaid diagram types.
- `module_relationship_diagram.source` must be non-empty and pass Mermaid validation.
- `validate_dsl.py` should warn, not fail, when a `module_id` or `module_name` from `module_intro.rows[]` does not appear in `module_relationship_diagram.source`.
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
        "module_id": "MOD-001",
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
                "capability_id": "CAP-MOD-001-001",
                "capability_name": "",
                "interface_style": "",
                "description": "",
                "inputs": "",
                "outputs": "",
                "notes": "",
                "confidence": "observed",
                "evidence_refs": [],
                "traceability_refs": [],
                "source_snippet_refs": []
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
        "evidence_refs": [],
        "traceability_refs": [],
        "source_snippet_refs": [],
        "notes": [],
        "confidence": "observed"
      }
    ]
  }
}
```

Rules:

- `module_design.summary` must be non-empty.
- `module_design.modules` must cover every module in `architecture_views.module_intro.rows` by matching `modules[].module_id` to `module_intro.rows[].module_id`.
- `module_design.modules[].module_id` is a required reference to a canonical module ID from chapter 3, not a new module definition.
- `module_design.modules[].module_id` and `architecture_views.module_intro.rows[].module_id` must form an exact one-to-one set: no missing modules, no extra modules, and no duplicate modules.
- Each module renders as its own subsection.
- Each module must have a non-empty `module_id`, `name`, and `summary`.
- Each module must have at least one responsibility.
- `external_capability_summary.description` must be non-empty.
- `external_capability_summary.interface_style` is free text, not an enum.
- `external_capability_details.provided_capabilities` must exist.
- The provided capabilities table uses fixed visible row fields: `capability_name`, `interface_style`, `description`, `inputs`, `outputs`, and `notes`, plus `capability_id` and common metadata fields.
- The provided capabilities table must have at least one row.
- Each provided capability row must include non-empty `capability_id`, `capability_name`, and `description`.
- `capability_id` values must be unique across core capabilities and provided capabilities, and use the `CAP-...` prefix.
- Each provided capability row must include `confidence`.
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
          "unit_id": "RUN-001",
          "unit_name": "",
          "unit_type": "",
          "entrypoint": "",
          "entrypoint_not_applicable_reason": "",
          "responsibility": "",
          "related_module_ids": [],
          "external_environment_reason": "",
          "notes": "",
          "confidence": "observed",
          "evidence_refs": [],
          "traceability_refs": [],
          "source_snippet_refs": []
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

- `runtime_view.summary` must be non-empty.
- `runtime_units` must exist and its rows use fixed visible fields: `unit_name`, `unit_type`, `entrypoint`, `entrypoint_not_applicable_reason`, `responsibility`, `related_module_ids`, `external_environment_reason`, and `notes`, plus `unit_id` and common metadata.
- `runtime_units.rows[].unit_id` must be non-empty, unique, and use the `RUN-...` prefix.
- `runtime_units.rows[].related_module_ids` must reference module IDs from `architecture_views.module_intro.rows`.
- `runtime_units.rows` must contain at least one runtime unit.
- Each runtime unit row must have non-empty `unit_id`, `unit_name`, `unit_type`, `responsibility`, and `confidence`.
- `entrypoint` may be empty only when `entrypoint_not_applicable_reason` is non-empty.
- `related_module_ids` may be empty only when `external_environment_reason` is non-empty.
- `notes` is supplemental display text and must not be used as a validation condition.
- `runtime_flow_diagram` must exist.
- `runtime_flow_diagram.diagram_type` must be one of the supported Mermaid diagram types.
- `runtime_flow_diagram.source` must be non-empty and pass Mermaid validation.
- `runtime_sequence_diagram` is recommended but not required. If Codex does not generate it, the field may be omitted or present as a full diagram object with empty `source`; the renderer still keeps the fixed `5.4 运行时序图（推荐）` section and outputs the documented empty-state sentence instead of a Mermaid block. If it has a non-empty `source`, it must use `sequenceDiagram` and pass Mermaid validation.

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
      "rows": []
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

- `configuration_items` must exist and its rows use fixed visible fields: `config_name`, `source`, `used_by`, `purpose`, and `notes`, plus `config_id` and common metadata.
- `configuration_items.rows` may be empty. If empty, the final Markdown renders a fixed `不适用` statement instead of an empty table.
- Non-empty configuration item rows must have non-empty `config_id`, `config_name`, `purpose`, and `confidence`.
- `config_id` values use the `CFG-...` prefix.
- `structural_data_artifacts` must exist and its rows use fixed visible fields: `artifact_name`, `artifact_type`, `owner`, `producer`, `consumer`, and `notes`, plus `artifact_id` and common metadata.
- `structural_data_artifacts.rows` may be empty. If empty, the final Markdown renders `未识别到需要在结构设计阶段单独说明的关键结构数据或产物。`
- Non-empty structural data/artifact rows must have non-empty `artifact_id`, `artifact_name`, `artifact_type`, `owner`, and `confidence`.
- `artifact_id` values use the `DATA-...` prefix.
- Codex must not invent generic artifacts only to populate this table.
- `dependencies` must exist and its rows use fixed visible fields: `dependency_name`, `dependency_type`, `used_by`, `purpose`, and `notes`, plus `dependency_id` and common metadata.
- `dependencies.rows` may be empty. If empty, the final Markdown renders `未识别到需要在结构设计阶段单独说明的外部依赖项。`
- Non-empty dependency rows must have non-empty `dependency_id`, `dependency_name`, `dependency_type`, `purpose`, and `confidence`.
- `dependency_id` values use the `DEP-...` prefix.
- `dependencies` describes external, environment, tool, file, template, service, or product dependencies that need structural explanation. Internal module dependencies belong in chapter 3 module relationship diagrams or chapter 7 collaboration relationships.
- Chapter 6 visible fields such as `used_by`, `owner`, `producer`, and `consumer` are display text only. They are not validated as module or runtime-unit references.
- If strict references are needed in a future version, they should use explicit metadata fields such as `used_by_module_ids`, `owner_module_id`, `producer_module_ids`, or `consumer_module_ids`; these fields are not part of the MVP DSL.
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
          "collaboration_id": "COL-001",
          "scenario": "",
          "initiator_module_id": "MOD-001",
          "participant_module_ids": [],
          "collaboration_method": "",
          "description": "",
          "confidence": "observed",
          "evidence_refs": [],
          "traceability_refs": [],
          "source_snippet_refs": []
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

- `collaboration_scenarios` must exist and its rows use fixed visible fields: `scenario`, `initiator_module_id`, `participant_module_ids`, `collaboration_method`, and `description`, plus `collaboration_id` and common metadata.
- `initiator_module_id` and `participant_module_ids` must reference module IDs from `architecture_views.module_intro.rows`.
- If chapter 3 defines two or more modules, `collaboration_scenarios.rows` must contain at least one collaboration scenario.
- In multi-module mode, every collaboration row must have non-empty `collaboration_id`, `scenario`, `initiator_module_id`, `participant_module_ids`, `collaboration_method`, `description`, and `confidence`.
- `collaboration_id` values use the `COL-...` prefix.
- In multi-module mode, `participant_module_ids` must contain at least one module ID.
- In multi-module mode, at least one `participant_module_ids` item must be different from `initiator_module_id`.
- A multi-module collaboration scenario must involve at least two distinct modules.
- If chapter 3 defines two or more modules, `collaboration_relationship_diagram` must exist, have a supported `diagram_type`, and have non-empty `source` that passes Mermaid validation.
- If chapter 3 defines exactly one module, `collaboration_scenarios.rows` may be empty and `collaboration_relationship_diagram` may be omitted or present as a full diagram object with empty `source`.
- In single-module mode, if Codex provides collaboration rows or a diagram source, they must still pass normal validation.
- In single-module mode with no collaboration content, the renderer outputs: `本系统当前仅识别到一个结构模块，暂无跨模块协作关系。`
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
          "participant_module_ids": [],
          "participant_runtime_unit_ids": [],
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
        "steps": [
          {
            "step_id": "STEP-FLOW-001-001",
            "order": 1,
            "description": "",
            "actor": "",
            "related_module_ids": [],
            "related_runtime_unit_ids": [],
            "input": "",
            "output": "",
            "confidence": "observed",
            "evidence_refs": [],
            "traceability_refs": [],
            "source_snippet_refs": []
          }
        ],
        "branches_or_exceptions": [
          {
            "branch_id": "BR-FLOW-001-001",
            "condition": "",
            "handling": "",
            "related_module_ids": [],
            "related_runtime_unit_ids": [],
            "confidence": "inferred",
            "evidence_refs": [],
            "traceability_refs": [],
            "source_snippet_refs": []
          }
        ],
        "related_module_ids": [],
        "related_runtime_unit_ids": [],
        "confidence": "observed",
        "evidence_refs": [],
        "traceability_refs": [],
        "source_snippet_refs": [],
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

- `key_flows.summary` must be non-empty.
- `flow_index` must exist and its rows use fixed fields: `flow_id`, `flow_name`, `trigger_condition`, `participant_module_ids`, `participant_runtime_unit_ids`, `main_steps`, `output_result`, and `notes`.
- `flow_index.rows[]` is an index-only row and does not carry common metadata. Its confidence and support references are carried by the matching `key_flows.flows[]` object.
- `flow_index.rows` must contain at least one key flow.
- Each flow index row must have non-empty `flow_id`, `flow_name`, `trigger_condition`, `main_steps`, and `output_result`.
- Each flow index row must include at least one participant through `participant_module_ids` or `participant_runtime_unit_ids`.
- Every `flow_index.rows[].flow_id` must match exactly one `flows[].flow_id`.
- Every `flows[].flow_id` must appear exactly once in `flow_index.rows`.
- `participant_module_ids` and `related_module_ids` must reference module IDs from chapter 3.
- `participant_runtime_unit_ids` and `related_runtime_unit_ids` must reference runtime unit IDs from chapter 5.
- Every flow must have non-empty `name`, `overview`, `confidence`, and `steps`.
- `flows[].steps` must be a non-empty array of step objects.
- Each step must have non-empty `step_id`, integer `order >= 1`, non-empty `description`, and `confidence`.
- `step_id` values use the `STEP-...` prefix.
- `step_id` values must be globally unique across all `key_flows.flows[].steps[]`.
- Traceability target `flow_step` resolves by global `step_id`.
- Step `order` values must be unique within one flow.
- `branches_or_exceptions` may be empty. If present, each item must have non-empty `branch_id`, `condition`, `handling`, and `confidence`.
- `branch_id` values use the `BR-...` prefix and must be globally unique across all `key_flows.flows[].branches_or_exceptions[]`.
- Traceability target `flow_branch` resolves by global `branch_id`.
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
- Codex may write lightweight Markdown text in this string, such as paragraphs, unordered lists, ordered lists, emphasis, and inline code.
- It must not contain any Markdown headings, Mermaid code blocks, Markdown tables, unbalanced fenced code blocks, HTML blocks, embedded diagrams, raw graph definitions, or structured table/diagram objects.
- The renderer owns all chapter 9 headings, including `风险`, `假设`, and `低置信度项`.
- If empty and there are no risks, assumptions, or low-confidence items, the final Markdown renders `未识别到明确的结构问题与改进建议。`
- If empty but risks, assumptions, or low-confidence items exist, the renderer does not render the empty-state sentence and directly renders the appended sections.

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
- `line_start` and `line_end` must be positive integers, and `line_end` must be greater than or equal to `line_start`.
- If snippet content is redacted or excerpted, the validator does not require the number of content lines to equal the line range.
- Source snippets may contain existing source code, including existing function, class, struct, enum, data model, or implementation fragments.
- Snippets must not introduce newly invented APIs, structs, enums, data models, or implementation logic.
- Prototype/detail-design lint rules do not apply inside `source_snippets.content`, but they do apply to normal design text.
- Snippets must be rendered explicitly as evidence snippets, not as design definitions.
- Snippets must not include secrets, credentials, tokens, private keys, passwords, or personal data. Codex must redact such content before writing the DSL.
- Secret and personal-data validation is best-effort. `validate_dsl.py` must fail on obvious high-risk patterns such as private key headers, common token variable names, password-like key/value pairs, and long high-entropy credential-looking strings. This does not prove that snippets are free of secrets or personal data.
- Snippets should be short. More than 20 lines produces a validation warning. More than 50 lines fails validation unless `--allow-long-snippets` is passed.
- Snippets must not substitute for module responsibility, interface requirement, internal structure, or flow descriptions.
- Rendered snippets appear near the relevant module, runtime unit, collaboration scenario, or flow only when helpful. They must not become a standalone appendix.
- When rendering source snippets, the renderer must choose a fence delimiter longer than any consecutive backtick run found in the snippet content, or use an escaping or indented-code strategy that cannot be broken by snippet content.
- Every `source_snippets[]` item must be referenced by at least one `source_snippet_refs` field. Unreferenced source snippets fail validation.
- If a snippet is used, `confidence` should normally be `observed`.

### Support Data Rendering Rules

Support data does not become standalone Markdown chapters.

- `evidence`: referenced through `evidence_refs` on related modules, capabilities, runtime units, collaborations, or flows when the schema explicitly allows those refs, and rendered near those items as `依据：EV-001, EV-002`.
- Unreferenced `evidence[]` items produce a validation warning, not a failure.
- `traceability`: attached to target nodes by authoritative `target_type` and `target_id`, and optionally mirrored through local `traceability_refs` backlinks. Rendered traceability should show source identifiers such as `REQ-001 / NOTE-002`.
- Local `traceability_refs` must point to traceability entries whose target is the current node. Conflicting backlinks fail validation.
- `risks`: appended to the end of chapter 9 under `风险` when present.
- `assumptions`: appended to the end of chapter 9 under `假设` when present.
- Low-confidence whitelisted design content items with `confidence: unknown` are summarized at the end of chapter 9 under `低置信度项`.
- `source_snippets`: rendered only near items that reference them through `source_snippet_refs`.
- When a fixed table row references evidence, traceability, or source snippets, the table renders only its visible columns. Support data for those rows is rendered immediately after the table as grouped notes keyed by the row's stable ID when available, or by the row's display name when no stable ID exists.
- Source snippets referenced by table rows are rendered outside the Markdown table so code blocks never appear inside table cells.

## Markdown Document Structure

The rendered Markdown file should use a stable single-file outline:

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

Section numbering policy:

- The renderer uses fixed numbering for all chapters and subchapters.
- Optional content absence must not cause later sections to move forward.
- Optional sections render their heading and a fixed empty-state sentence when their content is absent.
- Empty `extra_tables` or `extra_diagrams` arrays render the corresponding supplement section with `无补充表格。`, `无补充图表。`, or a chapter-specific `无补充内容。` sentence.
- Single-module chapter 7 still renders `7.1` through `7.4`; sections without collaboration content use fixed empty states.

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
   5.4 运行时序图（推荐）
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
   - Free-form Markdown string, appended risk/assumption/low-confidence sections, or a fixed empty-state sentence when all are empty.
```

Required empty-state sentences include:

- `5.4 运行时序图（推荐）`: `未提供运行时序图。`
- Single-module `7.2 跨模块协作说明`: `本系统当前仅识别到一个结构模块，暂无跨模块协作关系。`
- Empty `7.3 跨模块协作关系图`: `未提供跨模块协作关系图。`
- Empty supplement sections: `无补充内容。` unless a more specific table or diagram empty state is clearer.

## Mermaid Requirements

All diagrams in the final Markdown must be Mermaid code blocks:

````markdown
```mermaid
flowchart TD
  A[输入] --> B[处理]
```
````

Mermaid diagrams are section-local child nodes. The DSL does not use global diagram routing metadata.

MVP `diagram_type` values are fully supported and tested:

```json
[
  "flowchart",
  "graph",
  "sequenceDiagram",
  "classDiagram",
  "stateDiagram-v2"
]
```

All other Mermaid diagram types are unsupported in the MVP.

Mermaid diagram `source` values in the DSL must not contain Markdown fences. The renderer adds the final Mermaid code fences.

`validate_mermaid.py` should validate Mermaid text without network access. Because the skill is expected to support Mermaid reliably rather than maintain a partial custom grammar, strict validation should delegate to local Mermaid CLI tooling. If strict validation tooling is unavailable, the script must say so clearly and must not claim that diagrams were proven renderable.

`validate_mermaid.py` does not produce final image artifacts. In strict mode, it may render Mermaid diagrams to temporary files under `--work-dir` when provided, or under an implementation-local system temporary directory otherwise, solely for validation. Those temporary files are not part of the final deliverable.

Strict validation requires local dependencies:

- `node`
- `@mermaid-js/mermaid-cli`
- `mmdc` available on `PATH`

The script should provide three modes:

- `--strict`: use local Mermaid tooling to parse or render-check diagram source. This is the default mode for final document generation.
- `--static`: run deterministic checks that catch common structural mistakes. This mode is useful for tests and quick feedback, but it is not a substitute for strict validation.
- `--check-env`: report whether strict validation dependencies are available.

CLI contract:

```bash
python scripts/validate_mermaid.py --from-dsl structure.dsl.json --strict
python scripts/validate_mermaid.py --from-dsl structure.dsl.json --strict --work-dir .codex-tmp/create-structure-md-xxx/mermaid
python scripts/validate_mermaid.py --from-dsl structure.dsl.json --static
python scripts/validate_mermaid.py --from-markdown <output-file> --strict
python scripts/validate_mermaid.py --from-markdown <output-file> --static
python scripts/validate_mermaid.py --check-env
```

Rules:

- `--from-dsl <path>` and `--from-markdown <path>` are mutually exclusive.
- `--check-env` is used by itself and does not require an input file.
- `--strict` and `--static` are mutually exclusive.
- If neither `--strict` nor `--static` is passed, the script defaults to `--strict`.
- If `--work-dir <path>` is provided in strict mode, validation artifacts are created there and preserved for inspection.
- If `--work-dir` is not provided in strict mode, the script uses an implementation-local system temporary directory and may clean up its own temporary files.
- Final image artifacts are never copied to the output directory.
- DSL input extracts Mermaid diagram node `source` fields only when `source` is non-empty.
- Empty or missing diagram `source` fields in DSL input are skipped by `validate_mermaid.py`.
- Requiredness of diagram `source` is decided by `validate_dsl.py`, not `validate_mermaid.py`.
- Markdown input extracts fenced code blocks whose language is `mermaid`.
- Every Mermaid block extracted from Markdown must have a non-empty body.
- For `--from-dsl`, `diagram_type` comes from the diagram node and must match the first meaningful Mermaid line.
- For `--from-markdown`, there is no explicit `diagram_type`; the script infers it from the first meaningful Mermaid line.
- Markdown mode infers `flowchart`, `graph`, `sequenceDiagram`, `classDiagram`, or `stateDiagram-v2` from the matching first meaningful line. It fails if the inferred type is missing or not in the MVP supported set.
- Errors must include diagram ID and JSON path for DSL input, or Mermaid block index for Markdown input.

Static checks:

- Code block language is `mermaid`.
- Extracted diagram body is non-empty.
- For DSL input, `diagram_type` is one of the supported MVP enum values and is compatible with the first meaningful line.
- For Markdown input, the inferred diagram type is one of the supported MVP enum values.
- Blank lines, Mermaid comments starting with `%%`, and Mermaid init directives are ignored before first-line compatibility or inference checks.
- Markdown fences are balanced.
- Mermaid source from the DSL does not contain Markdown fences.
- Disallowed Graphviz/DOT constructs such as `digraph`, `rankdir`, and `node -> node;` are rejected when they appear as diagram source. Mermaid arrows such as `-->` and `->>` remain allowed.
- Diagram IDs are unique.

The script should fail closed for malformed diagram blocks. It should print actionable errors that name the diagram ID and field path.

## Script Responsibilities

### `validate_dsl.py`

Validates the complete JSON DSL against `schemas/structure-design.schema.json` with `jsonschema`, then performs semantic checks that JSON Schema cannot express well.

Core checks:

- Required top-level fields exist.
- Unknown properties fail schema validation by default through `additionalProperties: false`, except documented extension points.
- IDs are unique within their collections.
- IDs use the documented prefixes.
- References point to existing IDs.
- Traceability target validation uses the explicit `target_type` mapping table.
- `confidence` values use the allowed enum.
- Whitelisted design content items with `confidence: unknown` can be collected for chapter 9 low-confidence rendering.
- Required document sections can be rendered.
- The authoritative field contract is internally consistent with schema-required fields and chapter rules.
- ID fields are classified by the defining/reference ID field tables; unregistered `_id` or `_ids` fields fail validation.
- Required summary fields are non-empty according to chapter-specific rules.
- Fixed table row required fields are non-empty according to chapter-specific rules.
- Document metadata required fields are non-empty according to chapter 1 rules.
- `document.output_file` is safe, module- or system-specific, ends with `.md`, and is not generic-only.
- DSL instances do not contain validation policy fields such as `empty_allowed`, `required`, `min_rows`, `max_rows`, or `render_when_empty`.
- Fixed table nodes do not contain `id`, `title`, or `columns`; they contain `rows`, and row objects contain only schema-approved content fields and support metadata.
- Extra table nodes include `id`, `title`, `columns`, and `rows`; `columns[].key` values are unique; rows only use declared column keys plus `evidence_refs`.
- Required diagrams, optional diagrams, and extra diagrams follow the diagram field policy.
- Plain text fields do not contain unsafe Markdown injection patterns; Mermaid diagram source does not contain Markdown fences.
- Chapter 3 has the module introduction table and module relationship diagram.
- Chapter 3 module IDs are unique.
- Chapter 3 module relationship diagram coverage warning is emitted when a listed module ID or name is missing from the diagram source.
- Chapter 4 covers every module listed in chapter 3 by matching `module_design.modules[].module_id` to `architecture_views.module_intro.rows[].module_id`.
- Chapter 4 module details have non-empty provided capability rows and non-empty internal structure information.
- Chapter 5 has at least one runtime unit and a non-empty runtime flow diagram.
- Chapter 5 runtime unit IDs are unique, `related_module_ids` references exist, and empty `entrypoint` or empty `related_module_ids` use the structured reason fields rather than `notes`.
- Chapter 6 allows empty configuration item, structural data/artifact, and dependency tables.
- Chapter 7 enforces collaboration rows and collaboration diagram only when chapter 3 has two or more modules.
- Chapter 8 has at least one key flow, the flow index and `flows` array are one-to-one by `flow_id`, flow references use valid module/runtime-unit IDs, every listed flow has structured steps and a non-empty Mermaid diagram.
- Chapter 8 `flow_index.rows[]` is validated as an index-only table and does not carry common metadata.
- Flow step IDs and branch/exception IDs are globally unique in their respective collections.
- Chapter 9 is a string, may be empty, uses only allowed lightweight Markdown, and contains no headings.
- Traceability authoritative targets exist, local `traceability_refs` backlinks target the current node, and duplicate rendering candidates are de-duplicated by renderer.
- Normal design text does not contain prototype/detail-design patterns outside Mermaid source and source snippet content.
- Every source snippet is referenced by at least one `source_snippet_refs` field.
- Source snippets satisfy path, positive line range, language, purpose, content, confidence, best-effort secret/personal-data risk checks, and length rules.

CLI contract:

```bash
python scripts/validate_dsl.py structure.dsl.json
python scripts/validate_dsl.py structure.dsl.json --allow-long-snippets
```

- `validate_dsl.py` requires one positional DSL JSON path.
- It fails if the input file does not exist, is not valid JSON, or does not match the schema.
- `--allow-long-snippets` permits source snippets longer than 50 lines after warning. Without this flag, snippets longer than 50 lines fail validation.

### `validate_mermaid.py`

Extracts and validates Mermaid definitions from DSL or rendered Markdown. It does not produce final image artifacts. In strict mode, it may create temporary render-check artifacts under `--work-dir` when provided, or under an implementation-local system temporary directory otherwise, solely for validation. It exists to keep diagram correctness visible and independently testable.

### `render_markdown.py`

Programmatically renders the Markdown file named by `document.output_file` from the DSL. It does not use Jinja2 or a `.tpl` template. It should not invent content. It owns fixed chapter order, fixed section numbering, fixed table headers, empty-state text, support-data insertion, table-row support-data grouping, Mermaid fence generation, source snippet fence safety, source snippet rendering, chapter 9 appended sections, and Markdown escaping.

`render_markdown.py` assumes the input DSL has already passed `validate_dsl.py`, but it may still perform lightweight defensive checks and fail rather than producing malformed Markdown.

CLI contract:

```bash
python scripts/render_markdown.py structure.dsl.json --output-dir .
python scripts/render_markdown.py structure.dsl.json --output-dir . --overwrite
python scripts/render_markdown.py structure.dsl.json --output-dir . --backup
```

- `render_markdown.py` requires one positional DSL JSON path.
- It fails if the input file does not exist, is not valid JSON, or does not contain a valid module- or system-specific `document.output_file`.
- It may perform defensive validation, but it should not duplicate the full semantic validator.
- `--output-dir <path>` writes `document.output_file` to that directory.
- `--overwrite` explicitly replaces an existing output file.
- `--backup` preserves an existing output file as `<output_file>.bak-YYYYMMDD_HHMMSS` before writing the new file.
- `--overwrite` and `--backup` are mutually exclusive.

## Error Handling

Validation failures should stop rendering. Rendering failures should preserve the DSL and temporary working directory so the issue can be inspected. Error messages should include the failing file, JSON path or diagram ID, and a short correction hint.

If Codex lacks enough content to populate a section that is allowed to be empty, it should use the section's documented empty representation rather than making up facts.

If Codex lacks enough content to populate a required non-empty section, final generation must stop and require Codex to revise its structured content. Chapter 4 missing module-level capabilities or internal structure requires revising module design. Missing a function call graph alone does not require module re-partitioning.

If Mermaid strict validation tooling is unavailable, final generation should stop with a clear message unless the user explicitly accepts static-only validation for that run. If strict validation fails only because tooling is unavailable, Codex may run `validate_mermaid.py --static` only after that explicit acceptance, and must report that diagrams were not proven renderable by Mermaid CLI.

If the user explicitly accepts static-only Mermaid validation, Codex records that decision in the final report and may write a temporary note file at `.codex-tmp/create-structure-md-<run-id>/VALIDATION_NOTES.md`. The final report must state that Mermaid strict validation was not performed, the reason was local Mermaid CLI tooling unavailable, and the user accepted static-only validation for this run.

If the target output file already exists, rendering fails by default. The user must explicitly choose `--overwrite` or `--backup`. `--backup` preserves the existing file using `<output_file>.bak-YYYYMMDD_HHMMSS` and must not overwrite an existing backup.

If a source snippet exceeds 50 lines, validation fails unless `--allow-long-snippets` is passed. Snippets longer than 20 lines and up to 50 lines produce a warning.

## Testing Strategy

Tests should cover:

- The two example DSL files validate successfully.
- Tests use Python standard library `unittest` and run with `python -m unittest discover -s tests`.
- Tests do not require `pytest` or other third-party test frameworks in the MVP.
- `requirements.txt` contains runtime dependencies only, with `jsonschema` as the MVP Python dependency.
- `SKILL.md` front matter satisfies the skill contract.
- `validate_dsl.py` runs `jsonschema` validation before semantic validation.
- Schema validation rejects unknown fields by default through `additionalProperties: false`, while documented extension points are handled by semantic validation.
- Missing required fields fail validation with clear errors.
- Document metadata required fields fail validation when empty.
- Required fixed table row content fields fail validation when they are present but empty.
- Invalid references fail validation.
- Invalid ID prefixes fail validation.
- Invalid `confidence` values fail validation.
- Required summary fields fail validation when empty.
- Canonical module ID tests prove that module IDs are defined only by chapter 3 and chapter 4 `module_id` values are exact one-to-one references.
- Traceability tests cover `source_external_id`, the target mapping table including `flow_branch`, authoritative `target_type`/`target_id` binding, invalid targets, valid local backlinks, conflicting backlinks, and renderer de-duplication.
- Prototype/detail-design lint tests fail for function prototypes, `typedef struct`, `typedef enum`, and Python `def`/`class` definitions outside source snippets, while allowing the same content inside `source_snippets[].content`.
- Mermaid diagrams with Graphviz/DOT syntax fail validation.
- Mermaid diagram source containing Markdown fences fails validation.
- Valid Mermaid examples across MVP core diagram types pass lightweight validation.
- Non-core Mermaid diagram types fail validation in the MVP.
- Diagram policy tests cover optional diagram omission, optional full diagram object with empty `source`, rejection of `{}`, required diagram non-empty `source`, and `extra_diagrams[]` non-empty `source`.
- Mermaid static checks ignore leading blank lines, Mermaid comments, and Mermaid init directives when checking the first meaningful line.
- Markdown Mermaid validation infers diagram type from the first meaningful line and fails for missing or unsupported inferred types.
- `validate_mermaid.py --from-dsl` skips optional empty diagram sources, while required empty diagram sources fail in `validate_dsl.py`.
- `validate_mermaid.py --from-markdown` fails when a Mermaid fenced block has an empty body.
- `validate_mermaid.py --strict --work-dir ...` writes temporary validation artifacts under the requested work directory.
- Rendering creates exactly one Markdown file named by `document.output_file`.
- Rendering fails by default when the target output file already exists.
- Rendering with `--overwrite` replaces an existing output.
- Rendering with `--backup` preserves an existing output as `<output_file>.bak-YYYYMMDD_HHMMSS` before writing the new output, and does not overwrite an existing backup.
- Rendered Markdown includes balanced fences and no Graphviz code block.
- Rendered Markdown passes `validate_mermaid.py --from-markdown <output-file> --static` after generation.
- Plain text DSL fields are escaped so they cannot inject headings, tables, Mermaid fences, or raw HTML into the final document.
- Source snippet rendering uses a fence or escaping strategy that cannot be broken by snippet content containing backticks.
- Table row evidence, traceability, and source snippets render after the table as grouped notes rather than inside table cells.
- Chapter 3 fails validation if the fixed module introduction table or required module relationship diagram is missing.
- Chapter 3 and chapter 4 fail validation if module IDs do not match one-to-one.
- Chapter 3 emits a warning, not a failure, when the module relationship diagram source does not mention every listed module ID or module name.
- Required fixed tables fail validation if they contain `columns`; extra tables fail validation if they omit `columns`.
- Extra tables fail validation for duplicate column keys or row keys not declared by columns.
- Extra table rows may use `evidence_refs` but fail validation if they use `traceability_refs` or `source_snippet_refs`.
- Chapter 4 fails validation if any listed module lacks a provided capability row.
- Chapter 4 fails validation if any listed module lacks both an internal structure diagram and textual internal structure.
- Chapter 5 fails validation if runtime units are empty or runtime flow Mermaid source is missing.
- Chapter 5 fails validation if runtime unit IDs are duplicate or if runtime unit module references do not exist.
- Chapter 5 fails validation if `entrypoint` is empty without `entrypoint_not_applicable_reason`, or if `related_module_ids` is empty without `external_environment_reason`.
- Chapter 6 passes validation with empty configuration item, structural data/artifact, and dependency tables.
- Chapter 6 display fields such as `used_by`, `owner`, `producer`, and `consumer` are not treated as strict references.
- Chapter 7 passes validation with empty collaboration rows and empty diagram when chapter 3 has exactly one module.
- Chapter 7 fails validation with empty collaboration rows or empty diagram when chapter 3 has two or more modules.
- Chapter 7 fails validation in multi-module mode when a collaboration scenario does not involve at least two distinct modules.
- Chapter 8 fails validation if flow index rows and `flows` entries do not match one-to-one by `flow_id`, if module/runtime-unit references do not exist, if any flow lacks structured steps, or if any flow lacks a Mermaid diagram.
- Chapter 8 fails validation if `flow_index.rows[]` contains common metadata fields.
- Flow step tests cover required fields, globally unique `step_id`, unique `order`, branch/exception optionality, globally unique `branch_id`, and metadata refs.
- Chapter 9 accepts an empty `structure_issues_and_suggestions` string.
- Chapter 9 empty-state rendering appears only when the free-form string is empty and no risks, assumptions, or low-confidence items exist.
- Chapter 9 fails validation for any Markdown headings, Mermaid code blocks, Markdown tables, unbalanced fences, or HTML blocks.
- Support data tests cover evidence, traceability, risks, assumptions, refs, unreferenced evidence warnings, and whitelist-based low-confidence summary collection.
- Source snippet tests cover required fields, positive line range sanity, missing references, unreferenced snippet failures, best-effort secret/personal-data risk checks, warning at more than 20 lines, failure at more than 50 lines, and `--allow-long-snippets`.
- Strict Mermaid tooling unavailable tests cover explicit user acceptance before static-only fallback and the required warning that diagrams were not proven renderable by Mermaid CLI.
- `render_markdown.py` tests cover missing input file, invalid JSON, invalid or generic-only `document.output_file`, and filling rendered `generated_at` without mutating the DSL.
- Fixed numbering tests verify that optional sections do not cause later sections to move forward, including empty runtime sequence diagrams and single-module chapter 7.
- Authoritative field contract tests verify that schema, validator, and renderer agree on requiredness, emptiness, semantic requiredness, and rendering position for key fields.
- ID field contract tests verify defining ID fields, reference ID fields, paired flow identity, external source IDs, and rejection of unregistered `_id` or `_ids` fields.
- DSL examples and tests prove that `empty_allowed` and similar validation policy fields do not appear in JSON instances.

## Examples

Two example DSL files are required:

- `minimal-from-code.dsl.json`: describes a document generated after Codex has understood an existing codebase.
- `minimal-from-requirements.dsl.json`: describes a document generated from requirements or design notes without an implemented codebase.

The examples should stay small enough to read quickly but complete enough to exercise every required top-level DSL section.

## Implementation Notes

The first implementation should avoid unnecessary Python dependencies. `jsonschema` is required for JSON Schema validation. Markdown rendering, semantic validation glue, and tests should otherwise prefer the Python standard library. Jinja2 is not used in the MVP. Mermaid validation is the other exception: strict Mermaid confidence should come from local Mermaid CLI tooling rather than an incomplete hand-written grammar.

Future document types can reuse Python rendering helpers for headings, tables, Mermaid blocks, empty states, support-data references, and source snippets. The MVP does not introduce a template engine to solve future migration early.

Markdown escaping should use separate paths for paragraph text and table cells, such as `escape_plain_text()` and `escape_table_cell()`. Table cells need escaping for pipes and newlines; ordinary paragraph text should preserve normal prose while blocking heading, fence, and raw HTML block injection.

The skill should keep `SKILL.md` concise. Detailed DSL fields, document outline, Mermaid rules, and review criteria belong in `references/` so Codex loads them only when needed.

## Review Checklist

Before implementation begins, verify:

- The design keeps project understanding outside the skill.
- `SKILL.md` front matter is present and satisfies the skill contract.
- The output contract is one module- or system-specific Markdown file named by `document.output_file`.
- Generic-only output filenames are rejected.
- Final output path and temporary work directory rules are explicit.
- Existing output files are protected by default, with explicit `--overwrite` and `--backup` modes.
- Mermaid is the only supported diagram output.
- Mermaid validation script is named `validate_mermaid.py` and final generation defaults to strict validation.
- The workflow validates rendered Markdown Mermaid blocks after the output file is generated.
- Mermaid MVP supports only the five core diagram types.
- Graphviz is fully removed.
- Markdown rendering is code-driven and does not use `templates/` or Jinja2.
- Temporary JSON files are allowed but not part of the final deliverable.
- The DSL includes confidence, evidence, traceability, risk, assumption, and source snippet support.
- Common metadata, canonical module IDs, traceability target mappings, and ID reference rules are explicit.
- SKILL.md front matter, authoritative field contract, ID field contract, fixed numbering policy, and unittest test framework are explicit.
- `requirements.txt` contains runtime dependencies only and tests use `python -m unittest discover -s tests`.
- Optional diagrams, required diagrams, and extra diagrams have distinct schema and validation rules.
- Low-confidence summary collection uses an explicit whitelist.
- Plain text and Markdown-capable fields have clear escaping and validation rules.
- Prototype/detail-design lint applies to normal design text while source snippets remain evidence-only exceptions.
- DSL instances contain content only, while requiredness and emptiness rules live in schema, validator code, and reference documentation.
- Fixed tables keep columns in renderer/schema/reference, not in DSL instances.
- Table-row support data rendering is defined outside table cells.
- Tests cover schema, Mermaid validation, Markdown rendering, overwrite behavior, single-module chapter 7 behavior, chapter 6 empty tables, support data, source snippets, and Markdown injection resistance.
- The design is small enough for one implementation plan.
