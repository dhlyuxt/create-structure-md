# create-structure-md Phase Coverage Matrix

## Purpose

This matrix records how the original monolithic `create-structure-md` design spec is split across phase specs.

The phase specs remain specifications, not implementation plans. They describe requirements, contracts, validation rules, rendering rules, tests, acceptance criteria, and non-goals. They do not prescribe step-by-step implementation tasks.

## Phase Index

| Phase | Spec file | Primary responsibility |
| --- | --- | --- |
| 1 | `2026-05-01-create-structure-md-phase-1-skill-scaffold.md` | Skill scaffold, `SKILL.md`, dependencies, test harness, input readiness, workflow, output/temp directory contract. |
| 2 | `2026-05-01-create-structure-md-phase-2-dsl-schema.md` | JSON Schema, DSL object shapes, field contract, fixed table row schemas, support data schemas, examples at structural level. |
| 3 | `2026-05-01-create-structure-md-phase-3-dsl-validator.md` | Semantic DSL validation, ID/reference validation, chapter rules, traceability, snippets, Markdown safety, structure-design boundary lint. |
| 4 | `2026-05-01-create-structure-md-phase-4-mermaid-validator.md` | Mermaid extraction and validation from DSL or Markdown, strict/static modes, supported diagram types, Graphviz rejection. |
| 5 | `2026-05-01-create-structure-md-phase-5-markdown-renderer.md` | Programmatic Markdown rendering, fixed numbering, output file handling, tables, Mermaid fences, empty states. |
| 6 | `2026-05-01-create-structure-md-phase-6-support-data-rendering.md` | Evidence, traceability, risks, assumptions, source snippets, low-confidence rendering, table-row support data. |
| 7 | `2026-05-01-create-structure-md-phase-7-e2e-tests-and-docs.md` | Final references, examples, end-to-end workflow, review checklist, integrated test requirements. |

## Monolithic Spec Coverage

| Original spec section | Covered by phases | Notes |
| --- | --- | --- |
| Status | 7 | Final readiness is represented by end-to-end acceptance. |
| Purpose | 1, 7 | Skill purpose appears in `SKILL.md` contract and final reference docs. |
| Confirmed Requirements | 1, 2, 3, 4, 5, 6, 7 | Requirements are distributed by responsibility: output/workflow in Phase 1 and 5, DSL in Phase 2 and 3, Mermaid in Phase 4, support data in Phase 6, final docs/tests in Phase 7. |
| Non-Goals | 1, 4, 5, 7 | No repo analysis, no Graphviz, no final images, no multi-document output, no Word/PDF, no C2000 profile. |
| Alternatives Considered | 1, 7 | Reflected as selected DSL-driven workflow and no repository analysis in skill docs. |
| Proposed Skill Structure | 1 | Required directory tree and placeholder files. |
| `requirements.txt` and unittest policy | 1, 7 | Runtime dependency only: `jsonschema`; tests use `python -m unittest discover -s tests`. |
| `SKILL.md` Contract | 1, 7 | Phase 1 creates the contract; Phase 7 verifies final behavior and reference links. |
| Input Readiness Contract | 1, 7 | Phase 1 requires it in `SKILL.md`; Phase 7 repeats it in final user docs. |
| Skill Workflow | 1, 4, 5, 7 | Phase 1 defines workflow; Phases 4 and 5 implement validation/rendering contracts; Phase 7 verifies end to end. |
| Output Location | 1, 5 | Phase 1 documents output/temp rules; Phase 5 implements output path, overwrite, and backup behavior. |
| DSL Design overview | 2 | Top-level fields and object shapes. |
| Common metadata | 2, 3, 6 | Schema shape in Phase 2, semantic refs in Phase 3, rendering in Phase 6. |
| ID prefix conventions | 2, 3 | Schema modeling and semantic prefix/reference checks. |
| Defining/reference ID field policy | 2, 3 | Phase 2 declares modeled fields; Phase 3 validates uniqueness and references. |
| Markdown safety | 3, 5, 6 | Validator rejects high-risk fields, renderer escapes prose/tables, snippets use safe fences. |
| Structure-design boundary lint | 3, 6 | Phase 3 validates normal text; Phase 6 preserves source snippets as evidence. |
| MVP DSL Shape | 2 | Full top-level and chapter object schemas. |
| Authoritative Field Contract | 2, 3, 5 | Schema presence in Phase 2, semantic requiredness in Phase 3, rendering positions in Phase 5. |
| Fixed table model | 2, 3, 5, 6 | Schema fields, semantic row checks, visible column rendering, row support-data placement. |
| Extra table rules | 2, 3, 5, 6 | Shape in Phase 2, row-key validation in Phase 3, rendering/support behavior in Phase 5 and 6. |
| Common Mermaid diagram node | 2, 4, 5 | Shape in Phase 2, validation in Phase 4, rendering fences in Phase 5. |
| Diagram field policy | 2, 3, 4, 5 | Optional/required shape, requiredness, non-empty validation, extraction, rendering. |
| Validation Policy Outside DSL | 2, 3, 5, 7 | Schema/validator/renderer split and reference documentation. |
| Support Data Structures | 2, 3, 6 | Object shapes, semantic refs, rendering behavior. |
| Traceability target mapping | 2, 3, 6 | Enum shape, target validation, rendering and de-duplication. |
| Low-confidence summary collection | 3, 6 | Validation whitelist and rendered Chapter 9 section. |
| Chapter 1: Document Information | 2, 3, 5 | Schema fields, semantic filename/status checks, rendering metadata table. |
| Chapter 2: System Overview | 2, 3, 5 | Schema, non-empty checks, rendering. |
| Chapter 3: Architecture Views | 2, 3, 4, 5, 6 | Schema, module table and diagram rules, Mermaid validation, rendering, row support notes. |
| Chapter 4: Module Design | 2, 3, 4, 5, 6 | Schema, one-to-one module matching, provided capabilities, internal structure, rendering/support. |
| Chapter 5: Runtime View | 2, 3, 4, 5, 6 | Schema, runtime unit rules, flow/sequence diagrams, rendering/support. |
| Chapter 6: Configuration, Data, and Dependencies | 2, 3, 5, 6 | Schema, empty table rules, display fields, rendering/support. |
| Chapter 7: Cross-Module Collaboration | 2, 3, 4, 5, 6 | Schema, single/multi-module rules, Mermaid validation, fixed empty rendering. |
| Chapter 8: Key Flows | 2, 3, 4, 5, 6 | Schema, flow index/detail matching, step/branch rules, required diagrams, rendering/support. |
| Chapter 9: Structure Issues and Suggestions | 2, 3, 5, 6 | String schema, Markdown restrictions, empty-state and appended sections. |
| Source Snippet Rules | 2, 3, 5, 6 | Schema fields, validation/security/length/ref checks, safe rendering. |
| Support Data Rendering Rules | 6 | Dedicated phase owns rendering placement and behavior. |
| Markdown Document Structure | 5 | Full fixed chapter/subchapter outline and empty-state behavior. |
| Mermaid Requirements | 4, 5, 7 | Validator, renderer fences, final workflow docs. |
| `validate_dsl.py` responsibilities | 3 | Dedicated semantic validator phase. |
| `validate_mermaid.py` responsibilities | 4 | Dedicated Mermaid validator phase. |
| `render_markdown.py` responsibilities | 5, 6 | Base rendering in Phase 5, support data in Phase 6. |
| Error Handling | 3, 4, 5, 7 | Validation failure behavior, strict Mermaid fallback, overwrite/backup, final reporting. |
| Testing Strategy | 1, 2, 3, 4, 5, 6, 7 | Each phase owns tests for its contract; Phase 7 verifies integrated workflow. |
| Examples | 2, 7 | Structural examples in Phase 2, semantically complete examples in Phase 7. |
| Implementation Notes | 1, 5, 7 | Minimal dependencies, no Jinja/templates, code-driven rendering, concise `SKILL.md`. |
| Review Checklist | 7 | Final reference checklist. |

## Coverage Rule

An implementation phase should not need to consult the monolithic design spec for normative behavior. If a missing rule is discovered during implementation, update the relevant phase spec and this matrix rather than adding hidden assumptions to code.

## Boundary Rule

These phase specs are not plans. They do not define task order, commit boundaries, or step-by-step implementation. A separate implementation plan may be written later from these specs if needed.
