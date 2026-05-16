# create-structure-md 0.3.0 Redesign

Date: 2026-05-16
Status: working design

## Context

The current create-structure-md 0.2.0 output is too close to a machine-verifiable structure dump. The generated EasyFlash document shows two core failures:

- Visible diagrams and prose leak internal IDs such as `MOD-*`, `RUN-*`, `FLOW-*`, and `MER-*`, which makes the document feel written for validation rather than for human understanding.
- Chapter 4 expands every module into detailed API, configuration, dependency, data-object, interface, and mechanism sections. This buries a first-time reader in detail before they understand how the repository works.

The 0.3.0 redesign intentionally breaks compatibility with 0.2.0. It restarts the mainline around a human-first repository guide with structured verification kept behind the scenes.

## Product Direction

The default reader is a first-time engineer opening an unfamiliar C repository.

The document should help that reader answer:

- What is this repository for?
- Which directories and files should I read first?
- What are the main layers and responsibilities?
- What are the main repository paths from entrypoint to behavior?
- Which mechanisms are worth understanding deeply?
- What must be configured or ported before integration?
- Where should I start when modifying or extending behavior?
- What assumptions, risks, and validation gaps remain?

The default depth is "guide plus key mechanisms". The document is not an API reference, not a full detailed design dump, and not a raw scan report.

## Fixed Chapter Contract

0.3.0 keeps a fixed eight-chapter contract, but replaces the chapter meanings.

1. **文档说明**
   - Title, scope, target repository, generation time, analysis boundary, confidence summary.
   - Raw scan metrics such as file count, symbol count, and call-edge count must not dominate the first screen.

2. **仓库概述与阅读路线**
   - Explain what the repository solves, who it is for, its core capabilities, and the recommended source-reading order.
   - This chapter should name the first files/directories a new reader should inspect.

3. **目录地图**
   - Explain the repository tree by role, not by exhaustive listing.
   - Distinguish main library code, port/adaptation code, plugins, demos, bundled third-party code, docs, tests, and generated or temporary artifacts when applicable.

4. **系统分层与模块职责**
   - Provide module/layer responsibility cards.
   - Explain where each module lives, what it owns, what it consumes, what it produces, what it does not own, and neighboring modules.
   - Do not render function prototypes, parameter tables, return-value tables, or per-interface execution diagrams here.

5. **仓库主线**
   - Use one to three mainlines to connect the repository.
   - A mainline is an important end-to-end path such as application integration, initialization, persistence, upgrade, logging, request handling, or build/test flow.
   - Each mainline should show entrypoint, layers crossed, key files, and final effect.

6. **关键机制深读**
   - Deepen only mechanisms that help readers understand how the repository works.
   - There is no hard maximum number of mechanisms.
   - A mechanism is justified by structural value, not by the existence of a function or API.
   - Each mechanism should cover what the reader should know first, related source files, core flow, key state/data, common misunderstandings, and validation gaps.

7. **配置、移植与集成边界**
   - Explain required configuration, required platform hooks, integration assumptions, relevant demos, external dependencies, and responsibilities intentionally left outside the library.

8. **风险、假设与验证缺口**
   - Render risks, assumptions, low-confidence items, and validation gaps in one honest review-oriented chapter.
   - Static analysis only, missing target builds, missing hardware validation, skipped demos, and inferred behavior should be visible here.

## Chapter 4 And Chapter 6 Boundary

Chapter 4 is for orientation. It answers "what is this module and where does it sit?"

Chapter 6 is for mechanism understanding. It answers "how does this behavior actually work?"

Chapter 4 must not become an API reference. Function prototypes, parameter tables, return-value tables, and exhaustive interface details belong outside the default document shape. Chapter 6 may mention important functions, states, and data structures when they explain a mechanism.

## Diagram Rules

Mermaid diagrams and visible prose must be human-first.

- Visible Mermaid labels must use human-readable names such as "初始化流程", "持久化存储", or "平台适配".
- Visible Mermaid labels must not show internal IDs such as `MOD-*`, `RUN-*`, `FLOW-*`, or `MER-*`.
- Internal IDs may remain in child JSON reference fields and validation metadata.
- Mermaid source may use technical node identifiers when the visible node labels remain human-readable.
- The readability gate checks rendered/visible labels, not every raw Mermaid source token.
- `diagram-id` metadata may remain in Markdown source if gate tooling needs it, but the rendered diagram and surrounding prose must not depend on it for meaning.
- Diagrams are included only when they help readers build a mental model.
- Chapter 6 does not require every mechanism to have a diagram.
- A readability gate should reject visible diagram labels that leak internal IDs.

## DSL Version And Compatibility

0.3.0 is intentionally incompatible with 0.2.0.

- Do not preserve the old `dsl_version: "0.2.0"` contract.
- Do not promise compatibility with old `structure.dsl.json` inputs.
- Use `structure.manifest.json` as the new main input name.
- JSON payloads do not carry `dsl_version`.
- The DSL version is selected by validator, schema path, and renderer mode, such as `schemas/v0.3.0/structure.manifest.schema.json`.

0.3.0 targets C-oriented repositories first. Other language profiles are out of scope for this version unless a later profile explicitly extends the chapter contracts.

## Layered DSL Model

0.3.0 uses a layered DSL.

Chapter JSON files are generic content models, not repository-specific prompts. Field names, allowed values, examples, schema fixtures, and reference docs must not make the skill appear tailored to EasyFlash or any other single repository. EasyFlash may be mentioned only as a motivating failure case or as one optional example fixture clearly labeled as an example.

Chapter JSON must be content-bearing, not prompt-bearing. It should store facts and renderable content for a repository document. Generation instructions, analysis workflow rules, and writer guidance belong in reference docs, skill instructions, or implementation code, not in chapter JSON and not in the manifest.

During design discussion, chapter JSON shapes should be expressed as generic field contracts rather than repository-specific filled examples. This avoids making one repository's content look like the DSL contract.

The main JSON is a chapter directory only. It must not carry document metadata, repository metadata, repository-understanding workflow details, validation policy, output filename, writing guidance, or DSL version metadata.

The manifest owns only the fixed chapter keys and directly referenced child JSON paths. The chapter count and chapter keys are fixed by the 0.3.0 contract.

Only the manifest may compose the document by referencing child JSON files. Chapter JSON files must not include, load, or compose other JSON files.

Diagnostic fields may point at a manifest child path only to identify where an issue was found. Such diagnostic path fields do not authorize the renderer or validator to load additional chapter JSON beyond the manifest-owned file set.

Chapter 6 is the only exception to the one-path-per-chapter shape. The manifest splits the fixed `key_mechanisms` chapter into multiple mechanism subchapter JSON files directly in the manifest. These files are directly referenced by the manifest, not grandchildren referenced from another DSL JSON file.

There is no `chapters/06-key-mechanisms.json` aggregate file. The Chapter 6 title comes from the fixed chapter contract. The order of `key_mechanisms` paths in `structure.manifest.json` is the render order of Chapter 6 subchapters.

Suggested child files:

- `chapters/01-document.json`
- `chapters/02-repository-overview.json`
- `chapters/03-directory-map.json`
- `chapters/04-module-layers.json`
- `chapters/05-repository-mainline.json`
- `chapters/06-key-mechanisms/<mechanism-key>.json`
- `chapters/07-integration-boundaries.json`
- `chapters/08-risks-validation.json`

This keeps the top-level document navigable and prevents process metadata from leaking into the content model.

## Skill Behavior And Analysis Workflow

This section describes skill behavior, not DSL fields. None of the workflow details below should appear in `structure.manifest.json` or in chapter JSON content unless a later explicit provenance sidecar is designed.

### Repository Understanding Stage

0.3.0 introduces a repository understanding stage for C repositories.

The repo-understand skill is the preferred workflow for analyzing an unfamiliar C repository. It uses `repo-analysis-tools` first and raw source reading only as a supplement.

create-structure-md should no longer pretend that repository understanding is out of scope. Instead, the new workflow separates responsibilities:

- repo-understand prepares structured repository understanding material.
- create-structure-md organizes that material into 0.3.0 manifest and child JSON.
- render tooling turns the DSL into the fixed eight-chapter Markdown document.

repo-understand produces understanding material, not final Markdown. Final documentation still comes from the DSL renderer.

### Key Mechanism Subagent Workflow

Chapter 6 is the main place where repo-understand should be used deeply.

The main agent identifies candidate mechanisms from repository overview, directory map, module responsibilities, and mainlines. Then it dispatches subagents for independent mechanism-reading tasks.

Each subagent should:

- use repo-understand;
- confirm the installed repo-analysis-tools CLI help before relying on command syntax;
- rebuild or use the repository snapshot as appropriate;
- inspect priority files, file info, symbols, call relations, root functions, and call paths;
- use raw source only after CLI context is established;
- return structured mechanism material;
- avoid writing final Markdown directly.

The main agent integrates each accepted subagent output into one direct manifest child under `chapters/06-key-mechanisms/<mechanism-key>.json`.

The mechanism JSON stores the accepted content, not the analysis transcript. Subagent identity, CLI query logs, and repo-understand command summaries belong in implementation logs or a future explicit provenance sidecar, not in the renderable DSL.

## Historical Archive Policy

The existing V1/V2 project line is treated as historical material after the 0.3.0 restart.

Archive, do not delete:

- old design documents and implementation plans;
- old references;
- old schemas;
- old scripts;
- old tests;
- old examples;
- old generated design documents when they are kept as reference artifacts.

After archival, old code is reference material only. The 0.3.0 mainline should be rebuilt with new manifest, schema, renderer, validators, examples, tests, and skill documentation.

Deletion is not part of this workflow. If cleanup requires deletion, provide commands for the user to run.

## Draft DSL Contracts

This section records the current agreed 0.3.0 DSL shape. The contracts below are not writing prompts and not repository-specific filled examples.

Schema and renderer implementation should depend on this section. The workflow section above explains how agents prepare content, not what schemas or renderers must accept.

JSON examples in this section must be valid JSON. Field contracts use prose so that placeholder strings such as `"high | medium | low"` are not mistaken for literal JSON values.

### Shared Types And Reference Rules

Common scalar types:

- `path`: normalized repository-relative POSIX path string.
- `symbol`: source symbol name string.
- `manifest-path`: normalized relative POSIX path string from `structure.manifest.json` to a child JSON file.
- `mechanism-key`: key inferred from a Chapter 6 mechanism file stem; it must match the mechanism key rules below.
- `diagram-source`: Mermaid source string.
- `confidence`: enum, one of `high`, `medium`, `low`.
- `chapter-key`: enum, one of `document`, `repository_overview`, `directory_map`, `module_layers`, `repository_mainline`, `key_mechanisms`, `integration_boundaries`, `risks_validation`.

Reference identifiers:

- `layer-id`, `module-id`, `mainline-id`, `risk-id`, `assumption-id`, `gap-id`, `item-id`, and `diagram-id` are internal reference IDs.
- Internal IDs must match `^[a-z0-9][a-z0-9_-]*$`, are case-sensitive, and must be unique within their owning collection.
- `module_ref` and `module_refs` values must resolve to `module-id` values declared in Chapter 4.
- `layer_id` values in modules must resolve to a `layer-id` declared in Chapter 4.
- `related_mechanisms` values must resolve to mechanism keys inferred from `key_mechanisms` file stems in `structure.manifest.json`.
- The fixed chapter contract defines chapter render order; JSON object property order is not semantic.
- Single-path chapter JSON `chapter.key` values must match the manifest property that references the file.
- Mechanism JSON files do not contain `chapter.key`; their mechanism keys come from manifest path stems.

JSON Schema defaults:

- Required fields must be present and non-null.
- Optional fields may be omitted; if present, optional fields must not be `null` unless a field contract explicitly permits `null`.
- String fields must have `minLength: 1` unless a field contract explicitly allows an empty string.
- Required arrays must be present. They may be empty unless a rule says `minItems 1`.
- Object schemas default to `additionalProperties: false`.
- Enum values are case-sensitive literal strings.
- Repository `path` values receive lexical schema validation in all modes; existence checks require repository snapshot context and belong to semantic validation.

Semantic validation defaults:

- Ordered arrays use positive integer `order` values starting at 1 without gaps.
- Manifest paths and diagnostic manifest paths must resolve to paths declared in `structure.manifest.json`, as specified by each field.
- ID references must resolve unless the owning field is explicitly described as free text.
- Repository `path` existence checks run only when repository snapshot context is available.

Named object contracts:

Notation:

- `field: type` means required field.
- `field?: type` means optional field.
- `array<T>` means an array whose items are `T`.
- `array<T>, minItems N` adds an array size rule.
- `enum(...)` means a case-sensitive enum.

Source references:

- `SourceRef`: `path: path`, `symbol?: symbol`.
- A `SourceRef` always has a `path`.
- If `symbol` is present, it is scoped to `path`.
- If `symbol` is present and repository snapshot context is available, semantic validation must confirm that `path` identifies a single source file.
- If repository snapshot context includes a symbol index, `symbol` must resolve within `path`; unresolved symbols are semantic errors.
- Without repository snapshot context or without a symbol index, validators must not fail a `SourceRef` because file type or symbol existence cannot be checked.
- Symbol-only references are not part of 0.3.0 because they require a repository-wide symbol registry and ambiguity policy.
- 0.3.0 does not define a string grammar such as `path#symbol` or `path:symbol`; source references are structured objects only.

Reusable objects:

- `ChapterHeader`: `key: chapter-key`, `title: string`.
- `DocumentInfo`: `title: string`, `version: string`, `status: enum(document_status)`, `language: enum(document_language)`, `generated_at: string`, `output_file: string`.
- `RepositoryInfo`: `name: string`, `root_display_path: string`, `kind: enum(repository_kind)`, `primary_languages: array<string>, minItems 1`.
- `Scope`: `included: array<ScopeIncluded>`, `excluded: array<ScopeExcluded>`.
- `ScopeIncluded`: `area: string`, `description: string`.
- `ScopeExcluded`: `area: string`, `reason: string`.
- `ConfidenceSummary`: `level: confidence`, `summary: string`, `validation_gaps: array<string>`.
- `RepositoryOverview`: `summary: string`, `problem_domain: string`, `repository_purpose: string`, `target_readers: array<string>, minItems 1`.
- `ReaderOrientation`: `read_first: array<string>`, `read_later: array<string>`, `can_skip_initially: array<string>`.
- `CoreCapability`: `name: string`, `description: string`, `entry_points: array<SourceRef>`, `notes: string`.
- `ReadingStep`: `order: integer`, `title: string`, `why_read_this: string`, `recommended_files: array<RecommendedFile>`, `expected_takeaway: string`.
- `RecommendedFile`: `path: path`, `reason: string`.
- `DirectoryGroup`: `name: string`, `role: enum(directory_group_role)`, `paths: array<path>, minItems 1`, `responsibility: string`, `read_when: string`, `notes: string`.
- `ImportantFile`: `path: path`, `role: string`, `why_it_matters: string`, `related_chapters: array<chapter-key>`.
- `RelationshipDiagram`: `summary: string`, `diagram?: Diagram`.
- `AreaBoundaryNote`: `area: string`, `note: string`.
- `TopicBoundaryNote`: `topic: string`, `note: string`.
- `Layer`: `layer_id: layer-id`, `name: string`, `role: string`, `responsibilities: array<string>`, `paths: array<path>, minItems 1`, `notes: string`.
- `Module`: `module_id: module-id`, `name: string`, `layer_id: layer-id`, `purpose: string`, `source_paths: array<path>, minItems 1`, `owns: array<string>`, `consumes: array<string>`, `produces: array<string>`, `does_not_own: array<string>`, `collaborates_with: array<ModuleCollaboration>`, `read_when: string`, `notes: string`.
- `ModuleCollaboration`: `module_ref: module-id`, `relationship: string`.
- `Mainline`: `mainline_id: mainline-id`, `name: string`, `purpose: string`, `entry: MainlineEntry`, `steps: array<MainlineStep>, minItems 1`, `result: string`, `detail_diagram?: Diagram`, `notes: string`.
- `MainlineEntry`: `kind: enum(mainline_entry_kind)`, `name: string`, `description: string`, `source_ref?: SourceRef`.
- `MainlineStep`: `order: integer`, `step: string`, `module_refs?: array<module-id>`, `source_refs: array<SourceRef>`, `effect: string`.
- `MechanismSection`: `title: string`.
- `SourceFocus`: `source_ref: SourceRef`, `reason: string`.
- `MechanismStep`: `order: integer`, `step: string`, `source_refs: array<SourceRef>`, `state_or_data: string`, `notes: string`.
- `StateOrData`: `name: string`, `kind: enum(state_or_data_kind)`, `description: string`, `source_refs: array<SourceRef>`.
- `CommonMisunderstanding`: `misunderstanding: string`, `correction: string`.
- `ConfigurationLocation`: `description: string`, `source_ref?: SourceRef`, `external_name?: string`.
- `RequiredConfiguration`: `name: string`, `kind: enum(required_configuration_kind)`, `location: ConfigurationLocation`, `purpose: string`, `required_when: string`, `notes: string`.
- `AdaptationLocation`: `description: string`, `source_ref?: SourceRef`, `external_name?: string`.
- `RequiredAdaptation`: `name: string`, `kind: enum(required_adaptation_kind)`, `location: AdaptationLocation`, `responsibility: string`, `caller_or_consumer: string`, `failure_if_missing: string`.
- `IntegrationEntry`: `description: string`, `source_ref?: SourceRef`, `external_name?: string`, `command?: string`.
- `IntegrationPath`: `name: string`, `scenario: string`, `recommended_entry: IntegrationEntry`, `steps: array<string>, minItems 1`, `reference_examples: array<path>`, `notes: string`.
- `ExternalDependency`: `name: string`, `kind: enum(external_dependency_kind)`, `used_by: string`, `integration_role: string`, `notes: string`.
- `OutOfScopeResponsibility`: `topic: string`, `owner: enum(out_of_scope_owner)`, `reason: string`.
- `Risk`: `risk_id: risk-id`, `description: string`, `impact: string`, `mitigation: string`, `related_modules: array<module-id>`, `related_mechanisms: array<mechanism-key>`, `confidence: confidence`.
- `Assumption`: `assumption_id: assumption-id`, `description: string`, `rationale: string`, `validation_suggestion: string`, `confidence: confidence`.
- `ValidationGap`: `gap_id: gap-id`, `gap_type: enum(validation_gap_type)`, `description: string`, `why_it_matters: string`, `suggested_validation: string`, `related_chapters: array<chapter-key>`, `confidence: confidence`.
- `LowConfidenceLocation`: `kind: enum(low_confidence_location_kind)`, `chapter?: chapter-key`, `path?: manifest-path`.
- `LowConfidenceItem`: `item_id: item-id`, `location: LowConfidenceLocation`, `description: string`, `reason: string`, `needed_evidence: string`.

Named enum values:

- `directory_group_role`: `main_source`, `public_headers`, `platform_port`, `plugin`, `demo`, `docs`, `tests`, `third_party`, `build`, `generated`, `other`.
- `mainline_entry_kind`: `api`, `command`, `build_target`, `startup`, `user_action`, `external_event`, `other`.
- `state_or_data_kind`: `state`, `struct`, `enum`, `macro`, `storage_layout`, `runtime_value`, `artifact`, `other`.
- `required_configuration_kind`: `macro`, `config_file`, `build_option`, `environment`, `runtime_setting`, `other`.
- `required_adaptation_kind`: `port_function`, `platform_hook`, `driver_binding`, `memory_hook`, `logging_hook`, `other`.
- `external_dependency_kind`: `library`, `hardware`, `toolchain`, `os`, `protocol`, `service`, `other`.
- `out_of_scope_owner`: `caller`, `platform`, `application`, `build_system`, `deployment`, `unknown`.
- `validation_gap_type`: `analysis_gap`, `missing_build_validation`, `missing_runtime_validation`, `uncertain_behavior`, `no_key_mechanisms_selected`, `other`.
- `document_status`: `draft`, `reviewed`, `final`.
- `document_language`: `zh-CN`.
- `repository_kind`: `c_library`, `c_application`, `firmware`, `mixed`, `other`.
- `low_confidence_location_kind`: `chapter`, `manifest_path`.

Language and title policy:

- 0.3.0 supports Chinese output first.
- Fixed chapter titles in this spec are Chinese literals and are valid for `DocumentInfo.language = "zh-CN"`.
- `DocumentInfo.language` must be `zh-CN`.
- Other output languages require a later localization profile and are hard validation errors in 0.3.0.

Path rules for `path`:

- A `path` must be normalized lexically as a relative POSIX path.
- A `path` must not start with `/`, contain `\`, contain empty path segments, or contain `.` or `..` path segments.
- A `path` may refer to a source file, source directory, build file, generated artifact, or documented repository artifact depending on field context.
- When repository snapshot context is available, `SourceRef.path` values must resolve or produce semantic validation errors.
- Non-`SourceRef` repository `path` fields are checked lexically by schema. Snapshot existence checks for those fields are semantic validator policy and may be warnings when the path intentionally describes generated, optional, or external artifacts.
- `root_display_path` is display text, not a repository-relative `path`; it may be a repository name or a sanitized display path. Renderers should not expose local absolute paths by default.

Conditional object rules:

- `LowConfidenceLocation.kind = "chapter"` requires `chapter` and forbids `path`.
- `LowConfidenceLocation.kind = "manifest_path"` requires `path` and forbids `chapter`.
- `LowConfidenceLocation.path` is a diagnostic manifest path. It must equal one normalized path declared in `structure.manifest.json`, but renderers and validators must not load files because of this field.
- `RequiredConfiguration.kind` values `environment`, `build_option`, and `runtime_setting` do not require `location.source_ref`; `location.description` and optional `location.external_name` carry the location.
- `RequiredAdaptation.kind` values `driver_binding` and `other` do not require `location.source_ref`; `location.description` and optional `location.external_name` carry the location.

Content quality guidance:

- `RequiredConfiguration.kind` values `macro` and `config_file` should include `location.source_ref` when source evidence is known.
- `RequiredAdaptation.kind` values `port_function`, `platform_hook`, `memory_hook`, and `logging_hook` should include `location.source_ref` when source evidence is known.
- These source evidence recommendations are not schema rules and do not produce validator diagnostics unless a later provenance mechanism makes evidence availability machine-checkable.

Internal ID uniqueness ranges:

- `layer-id`: unique within Chapter 4 `layers`.
- `module-id`: unique within Chapter 4 `modules`.
- `mainline-id`: unique within Chapter 5 `mainlines`.
- `risk-id`: unique within Chapter 8 `risks`.
- `assumption-id`: unique within Chapter 8 `assumptions`.
- `gap-id`: unique within Chapter 8 `validation_gaps`.
- `item-id`: unique within Chapter 8 `low_confidence_items`.
- `diagram-id`: unique package-wide.

### `structure.manifest.json`

The manifest is a pure chapter path directory. It contains exactly the fixed eight top-level properties shown below and no other fields.

```json
{
  "document": "chapters/01-document.json",
  "repository_overview": "chapters/02-repository-overview.json",
  "directory_map": "chapters/03-directory-map.json",
  "module_layers": "chapters/04-module-layers.json",
  "repository_mainline": "chapters/05-repository-mainline.json",
  "key_mechanisms": [
    "chapters/06-key-mechanisms/mechanism-key.json"
  ],
  "integration_boundaries": "chapters/07-integration-boundaries.json",
  "risks_validation": "chapters/08-risks-validation.json"
}
```

Rules:

- All properties are required.
- All values except `key_mechanisms` are single child JSON paths.
- `key_mechanisms` is an array of child JSON paths.
- `key_mechanisms` may contain any number of mechanisms. If it is empty, the renderer still emits the Chapter 6 title plus the fixed sentence `本次分析未选择可深读的关键机制。`, and Chapter 8 must record why no mechanism deep dive was selected.
- Each `key_mechanisms` path renders as one Chapter 6 subchapter.
- The order of `key_mechanisms` array entries is the Chapter 6 subchapter order.
- The mechanism key is inferred from the file stem of each `key_mechanisms` path.
- All manifest paths are relative to the directory containing `structure.manifest.json`.
- Manifest child files are direct DSL references only; this does not require them to be immediate filesystem children of the manifest directory.
- Child JSON files must not contain include/load/compose JSON references. Fields explicitly marked as diagnostic locations may contain manifest paths only to locate issues; renderers and validators must not load extra JSON from those diagnostic fields.
- `chapters/06-key-mechanisms.json` is forbidden; Chapter 6 has no aggregate child JSON.
- `structure.manifest.json` must not contain `dsl_version`, title, output filename, repository metadata, schema metadata, validation policy, or writing guidance.

Manifest path rules:

- A manifest path must be a normalized relative POSIX path.
- Normalization is lexical POSIX normalization, not operating-system-specific path resolution.
- A manifest path must not contain empty path segments, so `chapters//x.json` is invalid.
- A manifest path must not start with `/`.
- A manifest path must not contain `\`.
- A manifest path must not contain `.` or `..` path segments.
- A manifest path must end with the lowercase extension `.json`.
- Manifest paths must be unique across all eight manifest properties and all `key_mechanisms` entries after lexical normalization.
- Referenced files must exist when validation is run against a concrete DSL package.
- Filesystem validation resolves paths against the directory containing `structure.manifest.json`; symlinks that escape that directory are validation errors.

Mechanism key rules:

- The mechanism key is the basename of a `key_mechanisms` path after removing the final `.json`.
- The mechanism key must match `^[a-z0-9][a-z0-9_-]*$`.
- Mechanism keys are case-sensitive and must be unique within the manifest.
- Invalid mechanism paths, duplicate mechanism keys, or paths that do not end in `.json` are hard validation errors.

### `chapters/01-document.json`

Required:

- `chapter`: `ChapterHeader` with `key` equal to `document` and `title` equal to `文档说明`.
- `document`: `DocumentInfo`.
- `repository`: `RepositoryInfo`.
- `scope`: `Scope`.
- `confidence`: `ConfidenceSummary`.

Enums:

- `document.status`: `draft`, `reviewed`, or `final`.
- `repository.kind`: `c_library`, `c_application`, `firmware`, `mixed`, or `other`.
- `confidence.level`: `confidence`.

Rendering notes:

- This chapter introduces the document, not raw scan statistics.
- `document.output_file` is a suggested output filename for humans and default tooling. The actual write path is decided by the CLI or render invocation, and an explicit invocation path overrides `document.output_file`.

### `chapters/02-repository-overview.json`

Required:

- `chapter`: `ChapterHeader` with `key` equal to `repository_overview` and `title` equal to `仓库概述与阅读路线`.
- `overview`: `RepositoryOverview`.
- `core_capabilities`: array of `CoreCapability`, `minItems 1`.
- `reading_route.summary`: string.
- `reading_route.steps`: ordered array of `ReadingStep`, `minItems 1`.
- `reader_orientation`: `ReaderOrientation`.

Field details:

- `entry_points` is an array of `SourceRef`.
- `recommended_files` is an array of `RecommendedFile`.

Rendering notes:

- This chapter should name the first files or directories a new reader should inspect.
- It should not become an exhaustive feature list.

### `chapters/03-directory-map.json`

Required:

- `chapter`: `ChapterHeader` with `key` equal to `directory_map` and `title` equal to `目录地图`.
- `summary`: string.
- `directory_groups`: array of `DirectoryGroup`, `minItems 1`.
- `important_files`: array of `ImportantFile`.
- `directory_relationships`: `RelationshipDiagram`.
- `boundary_notes`: array of `AreaBoundaryNote`.

Enums:

- `directory_groups[].role`: `main_source`, `public_headers`, `platform_port`, `plugin`, `demo`, `docs`, `tests`, `third_party`, `build`, `generated`, or `other`.
- `important_files[].related_chapters`: array of `chapter-key`.

Rendering notes:

- Directory groups explain roles, not every file.

### `chapters/04-module-layers.json`

Required:

- `chapter`: `ChapterHeader` with `key` equal to `module_layers` and `title` equal to `系统分层与模块职责`.
- `summary`: string.
- `layers`: array of `Layer`, `minItems 1`.
- `modules`: array of `Module`, `minItems 1`.
- `boundary_notes`: array of `TopicBoundaryNote`.

Optional:

- `layer_diagram`: `Diagram`.

References:

- `modules[].layer_id` resolves to `layers[].layer_id`.
- `modules[].collaborates_with[].module_ref` resolves to `modules[].module_id`.

Rendering rules:

- `module_id`, `layer_id`, and `module_ref` are internal references.
- Visible output uses module and layer names, not IDs.
- Chapter 4 must not include function prototypes, parameter tables, return-value tables, or public interface detail fields.

### `chapters/05-repository-mainline.json`

Required:

- `chapter`: `ChapterHeader` with `key` equal to `repository_mainline` and `title` equal to `仓库主线`.
- `summary`: string.
- `mainline_overview_diagram`: `Diagram` with `diagram_type` equal to `flowchart`.
- `mainlines`: array of `Mainline`, `minItems 1`, `maxItems 3`.
- `cross_mainline_notes`: array of `TopicBoundaryNote`.

Optional:

- `mainlines[].detail_diagram`: `Diagram`.

Enums:

- `mainlines[].entry.kind`: `api`, `command`, `build_target`, `startup`, `user_action`, `external_event`, or `other`.
- `mainlines[].detail_diagram.diagram_type`: `flowchart` or `sequenceDiagram`.

References:

- `mainlines[].steps[].module_refs[]` resolves to Chapter 4 `module-id` values when present.

Field details:

- `mainlines[].entry` is `MainlineEntry`.
- `mainlines[].steps` is an ordered array of `MainlineStep`, `minItems 1`.
- A mainline step without `module_refs` is allowed when the step describes build, test, external, or user-triggered behavior that is not owned by a Chapter 4 module.
- `mainlines[].steps[].source_refs` may be an empty array when the step has no repository source location.

Rendering rules:

- `mainline_overview_diagram` is required.
- `detail_diagram` is optional for each mainline.
- Visible diagram labels must not leak internal IDs.

### `chapters/06-key-mechanisms/<mechanism-key>.json`

Each mechanism file renders as one subchapter under Chapter 6. The mechanism key is inferred from the file stem in `structure.manifest.json`, not stored inside the mechanism JSON.

Required:

- `section`: `MechanismSection`.
- `why_it_matters`: string.
- `reader_prerequisites`: array of strings.
- `related_modules`: array of Chapter 4 `module-id`.
- `source_focus`: array of `SourceFocus`, `minItems 1`.
- `mechanism_overview`: string.
- `flow`: ordered array of `MechanismStep`, `minItems 1`.
- `key_states_or_data`: array of `StateOrData`.
- `common_misunderstandings`: array of `CommonMisunderstanding`.
- `validation_gaps`: array of strings.
- `confidence`: `confidence`.

Optional:

- `diagram`: `Diagram`.

Enums:

- `key_states_or_data[].kind`: `state`, `struct`, `enum`, `macro`, `storage_layout`, `runtime_value`, `artifact`, or `other`.
- `diagram.diagram_type`: `flowchart`, `sequenceDiagram`, or `stateDiagram-v2`.

Rendering rules:

- The Chapter 6 title is fixed by the chapter contract, not by an aggregate JSON file.
- Each mechanism path in the manifest renders as `6.x` using `section.title`.
- If `key_mechanisms` is empty, the renderer still emits the Chapter 6 title and the fixed empty-chapter sentence defined by the manifest rules.
- `related_modules` render as module names resolved from Chapter 4.
- repo-understand usage notes, subagent names, and query summaries are not part of this JSON.

### `chapters/07-integration-boundaries.json`

Required:

- `chapter`: `ChapterHeader` with `key` equal to `integration_boundaries` and `title` equal to `配置、移植与集成边界`.
- `summary`: string.
- `required_configuration`: array of `RequiredConfiguration`.
- `required_adaptations`: array of `RequiredAdaptation`.
- `integration_paths`: array of `IntegrationPath`.
- `external_dependencies`: array of `ExternalDependency`.
- `out_of_scope_responsibilities`: array of `OutOfScopeResponsibility`.

Enums:

- `required_configuration[].kind`: `macro`, `config_file`, `build_option`, `environment`, `runtime_setting`, or `other`.
- `required_adaptations[].kind`: `port_function`, `platform_hook`, `driver_binding`, `memory_hook`, `logging_hook`, or `other`.
- `external_dependencies[].kind`: `library`, `hardware`, `toolchain`, `os`, `protocol`, `service`, or `other`.
- `out_of_scope_responsibilities[].owner`: `caller`, `platform`, `application`, `build_system`, `deployment`, or `unknown`.

Rendering notes:

- This chapter is allowed to be C/firmware oriented in 0.3.0.

### `chapters/08-risks-validation.json`

Required:

- `chapter`: `ChapterHeader` with `key` equal to `risks_validation` and `title` equal to `风险、假设与验证缺口`.
- `summary`: string.
- `risks`: array of `Risk`.
- `assumptions`: array of `Assumption`.
- `validation_gaps`: array of `ValidationGap`.
- `low_confidence_items`: array of `LowConfidenceItem`.

References:

- `risks[].related_modules` resolves to Chapter 4 `module-id`.
- `risks[].related_mechanisms` resolves to mechanism keys inferred from manifest paths.
- `validation_gaps[].related_chapters` uses `chapter-key`.

Rendering notes:

- If `key_mechanisms` is empty, package-level semantic validation requires this chapter to include a `validation_gaps[]` item whose `gap_type` is `no_key_mechanisms_selected` and whose `related_chapters` contains `key_mechanisms`.

### `Diagram`

Required:

- `id`: internal diagram identifier.
- `title`: visible diagram title.
- `diagram_type`: Mermaid diagram type.
- `description`: prose explanation.
- `source`: `diagram-source`.

Allowed diagram types:

- `flowchart`
- `sequenceDiagram`
- `stateDiagram-v2`

Schema rules:

- `id`, `title`, `diagram_type`, `description`, and `source` are required.
- `id` is a `diagram-id` and must match the internal ID pattern.
- `diagram_type` must be one of the allowed diagram types above.
- `source` must be a non-empty string.

Semantic validator rules:

- To match `diagram_type`, take the first non-empty line of `source`, trim it, split it on ASCII whitespace, and compare the first token.
- `diagram_type = "flowchart"` requires first token `flowchart`.
- `diagram_type = "sequenceDiagram"` requires first token `sequenceDiagram`.
- `diagram_type = "stateDiagram-v2"` requires first token `stateDiagram-v2`.
- Legacy `graph` declarations are not supported in 0.3.0; use `flowchart` instead.
- Visible labels in `source` must be human-readable.
- Internal node IDs in `source` are allowed only when rendered labels do not expose them.
- The 0.3.0 readability gate must document the Mermaid label syntax it can inspect.
- Unsupported visible-label syntax must produce a validation warning instead of being silently treated as checked.
- A validation warning has `code`, `json_path`, and `message`.
- Warnings do not block rendering by default.
- Strict validation mode promotes warnings to errors.

### Package-Level Semantic Validation Rules

These rules require multiple DSL files or repository context and are not single-file JSON Schema rules.

- All manifest paths must resolve to existing child JSON files within the DSL package.
- Every single-path chapter JSON `chapter.key` must match the manifest property that references it.
- Every value whose declared type is `module-id` or `array<module-id>` must resolve to a Chapter 4 `modules[].module_id`, including `module_ref`, `module_refs`, `related_modules`, and similarly named future module reference fields.
- Every value whose declared type is `layer-id` must resolve to a Chapter 4 `layers[].layer_id`.
- Every value whose declared type is `mechanism-key` or `array<mechanism-key>` must resolve to a manifest-inferred mechanism key, including `related_mechanisms`.
- Internal ID uniqueness ranges listed above must be enforced semantically, including package-wide `diagram-id` uniqueness.
- If `key_mechanisms` is empty, Chapter 8 must contain a `ValidationGap` with `gap_type = no_key_mechanisms_selected` and `related_chapters` containing `key_mechanisms`.
- `SourceRef.path` values must resolve against the repository snapshot when a snapshot is available.
- `SourceRef.symbol` file-type checks require repository snapshot context.
- `SourceRef.symbol` existence checks require repository snapshot context with a symbol index.
- Without the relevant snapshot context, validators check only `SourceRef` structure and lexical path validity.
