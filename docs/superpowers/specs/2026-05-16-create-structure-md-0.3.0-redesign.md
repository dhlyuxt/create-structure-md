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

- Visible Mermaid labels must use human-readable names such as "核心初始化", "ENV 存储", or "端口适配".
- Visible Mermaid labels must not show internal IDs such as `MOD-*`, `RUN-*`, `FLOW-*`, or `MER-*`.
- Internal IDs may remain in manifest data, child JSON, and validation metadata.
- `diagram-id` metadata may remain in Markdown source if gate tooling needs it, but the rendered diagram and surrounding prose must not depend on it for meaning.
- Diagrams are included only when they help readers build a mental model.
- Chapter 6 does not require every mechanism to have a diagram.
- A readability gate should reject visible diagram labels that leak internal IDs.

## DSL Version And Compatibility

0.3.0 is intentionally incompatible with 0.2.0.

- Do not preserve the old `dsl_version: "0.2.0"` contract.
- Do not promise compatibility with old `structure.dsl.json` inputs.
- Use `dsl_version: "0.3.0"`.
- Use `structure.manifest.json` as the new main input name.

## Layered DSL Model

0.3.0 uses a layered DSL.

Chapter JSON files are generic content models, not repository-specific prompts. Field names, allowed values, examples, schema fixtures, and reference docs must not make the skill appear tailored to EasyFlash or any other single repository. EasyFlash may be mentioned only as a motivating failure case or as one optional example fixture clearly labeled as an example.

Chapter JSON must be content-bearing, not prompt-bearing. It should store facts and renderable content for a repository document. Generation instructions, analysis workflow rules, and writer guidance belong in reference docs, skill instructions, or implementation code, not in chapter JSON and not in the manifest.

During design discussion, chapter JSON shapes should be expressed as generic field contracts rather than repository-specific filled examples. This avoids making one repository's content look like the DSL contract.

The main JSON is a chapter directory only. It must not carry document metadata, repository metadata, repository-understanding workflow details, validation policy, output filename, or writing guidance.

The manifest owns only the fixed chapter list and direct child JSON paths. The chapter count and chapter keys are fixed by the 0.3.0 contract.

Only the manifest may reference chapter JSON files. Chapter JSON files must not reference other JSON files.

Chapter 6 is the only exception to the one-path-per-chapter shape. The manifest may split the fixed `key_mechanisms` chapter into multiple mechanism subchapter JSON files directly in the manifest. These are still direct manifest children, not grandchildren referenced from a chapter JSON file.

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

## Repository Understanding Stage

0.3.0 introduces a repository understanding stage for C repositories.

The repo-understand skill is the preferred workflow for analyzing an unfamiliar C repository. It uses `repo-analysis-tools` first and raw source reading only as a supplement.

create-structure-md should no longer pretend that repository understanding is out of scope. Instead, the new workflow separates responsibilities:

- repo-understand prepares structured repository understanding material.
- create-structure-md organizes that material into 0.3.0 manifest and child JSON.
- render tooling turns the DSL into the fixed eight-chapter Markdown document.

repo-understand produces understanding material, not final Markdown. Final documentation still comes from the DSL renderer.

## Key Mechanism Subagent Workflow

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

This section records the current agreed 0.3.0 DSL shape. The shapes below are generic field contracts, not repository-specific filled examples.

### `structure.manifest.json`

The manifest is a chapter directory only. It contains no metadata other than direct child paths.

```json
{
  "chapters": [
    {
      "key": "document",
      "path": "chapters/01-document.json"
    },
    {
      "key": "repository_overview",
      "path": "chapters/02-repository-overview.json"
    },
    {
      "key": "directory_map",
      "path": "chapters/03-directory-map.json"
    },
    {
      "key": "module_layers",
      "path": "chapters/04-module-layers.json"
    },
    {
      "key": "repository_mainline",
      "path": "chapters/05-repository-mainline.json"
    },
    {
      "key": "key_mechanisms",
      "sections": [
        {
          "key": "mechanism-key",
          "path": "chapters/06-key-mechanisms/mechanism-key.json"
        }
      ]
    },
    {
      "key": "integration_boundaries",
      "path": "chapters/07-integration-boundaries.json"
    },
    {
      "key": "risks_validation",
      "path": "chapters/08-risks-validation.json"
    }
  ]
}
```

Rules:

- `chapters` contains exactly the fixed eight chapter keys in the fixed order shown above.
- All chapters except `key_mechanisms` use exactly one `path`.
- `key_mechanisms` uses `sections[]` and no chapter-level `path`.
- Each `sections[]` item renders as one Chapter 6 subchapter.
- Manifest children are direct children only; child JSON files must not reference other JSON files.

### `chapters/01-document.json`

```json
{
  "chapter": {
    "key": "document",
    "title": "文档说明"
  },
  "document": {
    "title": "string",
    "version": "semver-string",
    "status": "draft | reviewed | final",
    "language": "language-tag",
    "generated_at": "iso-8601-string",
    "output_file": "filename.md"
  },
  "repository": {
    "name": "string",
    "root_path": "path-string",
    "kind": "c_library | c_application | firmware | mixed | other",
    "primary_languages": ["string"]
  },
  "scope": {
    "included": [
      {
        "area": "string",
        "description": "string"
      }
    ],
    "excluded": [
      {
        "area": "string",
        "reason": "string"
      }
    ]
  },
  "confidence": {
    "level": "high | medium | low",
    "summary": "string",
    "validation_gaps": ["string"]
  }
}
```

### `chapters/02-repository-overview.json`

```json
{
  "chapter": {
    "key": "repository_overview",
    "title": "仓库概述与阅读路线"
  },
  "overview": {
    "summary": "string",
    "problem_domain": "string",
    "repository_purpose": "string",
    "target_readers": ["string"]
  },
  "core_capabilities": [
    {
      "name": "string",
      "description": "string",
      "entry_points": ["path-or-symbol-string"],
      "notes": "string"
    }
  ],
  "reading_route": {
    "summary": "string",
    "steps": [
      {
        "order": 1,
        "title": "string",
        "why_read_this": "string",
        "recommended_files": [
          {
            "path": "string",
            "reason": "string"
          }
        ],
        "expected_takeaway": "string"
      }
    ]
  },
  "reader_orientation": {
    "read_first": ["string"],
    "read_later": ["string"],
    "can_skip_initially": ["string"]
  }
}
```

### `chapters/03-directory-map.json`

```json
{
  "chapter": {
    "key": "directory_map",
    "title": "目录地图"
  },
  "summary": "string",
  "directory_groups": [
    {
      "name": "string",
      "role": "main_source | public_headers | platform_port | plugin | demo | docs | tests | third_party | build | generated | other",
      "paths": ["path-string"],
      "responsibility": "string",
      "read_when": "string",
      "notes": "string"
    }
  ],
  "important_files": [
    {
      "path": "string",
      "role": "string",
      "why_it_matters": "string",
      "related_chapters": ["chapter-key-string"]
    }
  ],
  "directory_relationships": {
    "summary": "string",
    "diagram": {
      "id": "diagram-id",
      "title": "string",
      "diagram_type": "flowchart",
      "description": "string",
      "source": "mermaid-source"
    }
  },
  "boundary_notes": [
    {
      "area": "string",
      "note": "string"
    }
  ]
}
```

### `chapters/04-module-layers.json`

```json
{
  "chapter": {
    "key": "module_layers",
    "title": "系统分层与模块职责"
  },
  "summary": "string",
  "layers": [
    {
      "layer_id": "layer-id",
      "name": "string",
      "role": "string",
      "responsibilities": ["string"],
      "paths": ["path-string"],
      "notes": "string"
    }
  ],
  "modules": [
    {
      "module_id": "module-id",
      "name": "string",
      "layer_id": "layer-id",
      "purpose": "string",
      "source_paths": ["path-string"],
      "owns": ["string"],
      "consumes": ["string"],
      "produces": ["string"],
      "does_not_own": ["string"],
      "collaborates_with": [
        {
          "module_ref": "module-id",
          "relationship": "string"
        }
      ],
      "read_when": "string",
      "notes": "string"
    }
  ],
  "layer_diagram": {
    "id": "diagram-id",
    "title": "string",
    "diagram_type": "flowchart",
    "description": "string",
    "source": "mermaid-source"
  },
  "boundary_notes": [
    {
      "topic": "string",
      "note": "string"
    }
  ]
}
```

Rendering rules:

- `module_id`, `layer_id`, and `module_ref` are internal references.
- Visible output uses module and layer names, not IDs.
- Chapter 4 must not include function prototypes, parameter tables, return-value tables, or public interface detail fields.

### `chapters/05-repository-mainline.json`

```json
{
  "chapter": {
    "key": "repository_mainline",
    "title": "仓库主线"
  },
  "summary": "string",
  "mainline_overview_diagram": {
    "id": "diagram-id",
    "title": "string",
    "diagram_type": "flowchart",
    "description": "string",
    "source": "mermaid-source"
  },
  "mainlines": [
    {
      "mainline_id": "mainline-id",
      "name": "string",
      "purpose": "string",
      "entry": {
        "kind": "api | command | build_target | startup | user_action | external_event | other",
        "name": "string",
        "location": "path-or-symbol-string"
      },
      "path": [
        {
          "order": 1,
          "step": "string",
          "module_ref": "module-id",
          "source_refs": ["path-or-symbol-string"],
          "effect": "string"
        }
      ],
      "result": "string",
      "detail_diagram": {
        "id": "diagram-id",
        "title": "string",
        "diagram_type": "flowchart | sequenceDiagram",
        "description": "string",
        "source": "mermaid-source"
      },
      "notes": "string"
    }
  ],
  "cross_mainline_notes": [
    {
      "topic": "string",
      "note": "string"
    }
  ]
}
```

Rendering rules:

- `mainline_overview_diagram` is required.
- `detail_diagram` is optional for each mainline.
- Visible diagram labels must not leak internal IDs.

### `chapters/06-key-mechanisms/<mechanism-key>.json`

Each mechanism file renders as one subchapter under Chapter 6.

```json
{
  "section": {
    "key": "mechanism-key",
    "title": "string"
  },
  "why_it_matters": "string",
  "reader_prerequisites": ["string"],
  "related_modules": ["module-id"],
  "source_focus": [
    {
      "path": "path-string",
      "symbols": ["symbol-name"],
      "reason": "string"
    }
  ],
  "mechanism_overview": "string",
  "flow": [
    {
      "order": 1,
      "step": "string",
      "source_refs": ["path-or-symbol-string"],
      "state_or_data": "string",
      "notes": "string"
    }
  ],
  "key_states_or_data": [
    {
      "name": "string",
      "kind": "state | struct | enum | macro | storage_layout | runtime_value | artifact | other",
      "description": "string",
      "source_refs": ["path-or-symbol-string"]
    }
  ],
  "diagram": {
    "id": "diagram-id",
    "title": "string",
    "diagram_type": "flowchart | sequenceDiagram | stateDiagram-v2",
    "description": "string",
    "source": "mermaid-source"
  },
  "common_misunderstandings": [
    {
      "misunderstanding": "string",
      "correction": "string"
    }
  ],
  "validation_gaps": ["string"],
  "understanding_notes": {
    "prepared_by": "main_agent | subagent",
    "repo_understand_used": true,
    "query_summary": ["string"]
  },
  "confidence": "high | medium | low"
}
```

Rendering rules:

- `understanding_notes` stays in the mechanism JSON and is not rendered by default.
- `related_modules` render as module names resolved from Chapter 4.
- If `repo_understand_used` is false, the mechanism needs a validation gap or explicit explanation.

### `chapters/07-integration-boundaries.json`

```json
{
  "chapter": {
    "key": "integration_boundaries",
    "title": "配置、移植与集成边界"
  },
  "summary": "string",
  "required_configuration": [
    {
      "name": "string",
      "kind": "macro | config_file | build_option | environment | runtime_setting | other",
      "location": "path-or-symbol-string",
      "purpose": "string",
      "required_when": "string",
      "notes": "string"
    }
  ],
  "required_adaptations": [
    {
      "name": "string",
      "kind": "port_function | platform_hook | driver_binding | memory_hook | logging_hook | other",
      "location": "path-or-symbol-string",
      "responsibility": "string",
      "caller_or_consumer": "string",
      "failure_if_missing": "string"
    }
  ],
  "integration_paths": [
    {
      "name": "string",
      "scenario": "string",
      "recommended_entry": "path-or-symbol-string",
      "steps": ["string"],
      "reference_examples": ["path-string"],
      "notes": "string"
    }
  ],
  "external_dependencies": [
    {
      "name": "string",
      "kind": "library | hardware | toolchain | os | protocol | service | other",
      "used_by": "string",
      "integration_role": "string",
      "notes": "string"
    }
  ],
  "out_of_scope_responsibilities": [
    {
      "topic": "string",
      "owner": "caller | platform | application | build_system | deployment | unknown",
      "reason": "string"
    }
  ]
}
```

### `chapters/08-risks-validation.json`

```json
{
  "chapter": {
    "key": "risks_validation",
    "title": "风险、假设与验证缺口"
  },
  "summary": "string",
  "risks": [
    {
      "risk_id": "risk-id",
      "description": "string",
      "impact": "string",
      "mitigation": "string",
      "related_modules": ["module-id"],
      "related_mechanisms": ["mechanism-key"],
      "confidence": "high | medium | low"
    }
  ],
  "assumptions": [
    {
      "assumption_id": "assumption-id",
      "description": "string",
      "rationale": "string",
      "validation_suggestion": "string",
      "confidence": "high | medium | low"
    }
  ],
  "validation_gaps": [
    {
      "gap_id": "gap-id",
      "description": "string",
      "why_it_matters": "string",
      "suggested_validation": "string",
      "related_chapters": ["chapter-key"],
      "confidence": "high | medium | low"
    }
  ],
  "low_confidence_items": [
    {
      "item_id": "item-id",
      "location": "chapter-key-or-json-path",
      "description": "string",
      "reason": "string",
      "needed_evidence": "string"
    }
  ]
}
```
