# Phase 7 End-to-End Tests And References Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Finish `create-structure-md` for local personal use by completing reference documentation, examples, `SKILL.md` workflow guidance, and end-to-end tests for the full validation and rendering workflow.

**Architecture:** Keep the implementation code stable unless an end-to-end test exposes a contract gap. Phase 7 mainly adds acceptance-level `unittest` coverage around the already implemented validators and renderer, expands the reference documents that `SKILL.md` points to, and upgrades the two minimal examples so they exercise fixed chapters, support data, Mermaid validation, and rendered Markdown checks together.

**Tech Stack:** Python 3 standard library `unittest`, `subprocess`, `json`, `pathlib`, `importlib.util`, `contextlib`, `io`, `uuid`, and `unittest.mock`; existing runtime dependency `jsonschema`; existing scripts `scripts/validate_dsl.py`, `scripts/validate_mermaid.py`, and `scripts/render_markdown.py`. Do not add Python dependencies.

---

## File Structure

- Modify: `SKILL.md`
  - Keep the existing YAML front matter exactly.
  - Make the workflow point to `references/dsl-spec.md` before writing DSL and `references/mermaid-rules.md` before creating Mermaid.
  - State the full workflow: validate DSL, strict Mermaid from DSL, render one Markdown file, static Mermaid from Markdown, review checklist, final report.
  - State that static-only Mermaid acceptance requires explicit user acceptance and must be reported.
- Modify: `references/dsl-spec.md`
  - Expand from signposts into the normal authoring contract for the DSL.
  - Cover input readiness, top-level fields, common metadata, ID fields, reference fields, support data, traceability mapping, validation policy exclusion, fixed table row ownership, and source snippet rules.
- Modify: `references/document-structure.md`
  - Expand the fixed 9-chapter outline into chapter-by-chapter rendering rules.
  - Cover output filename policy, fixed subchapter numbering, visible table columns, empty-state wording, support-data placement, and chapter 9 behavior.
- Modify: `references/mermaid-rules.md`
  - Expand supported diagram rules, unsupported diagram rules, strict/static validation difference, CLI examples, Graphviz/DOT rejection, and static-only acceptance reporting.
- Modify: `references/review-checklist.md`
  - Expand the checklist to cover all Phase 7 acceptance points, including final report requirements.
- Modify: `examples/minimal-from-code.dsl.json`
  - Keep it small and code-sourced.
  - Ensure it validates, renders, includes all fixed chapters, and contains no policy fields or Graphviz/DOT.
- Modify: `examples/minimal-from-requirements.dsl.json`
  - Keep it small and requirements-sourced.
  - Add at least one referenced evidence item, one traceability item, one risk or assumption, one low-confidence whitelisted item, and one safe source snippet.
- Create: `tests/test_phase7_e2e.py`
  - Own Phase 7 acceptance tests instead of making the already large script-specific test files larger.
  - Cover reference document content, example content contracts, static end-to-end workflow, mocked strict Mermaid workflow, static-only fallback documentation, fixed rendered numbering, and Graphviz/DOT absence.

Implementation constraints:

- Do not run deletion commands such as `rm`, `rmdir`, `git clean`, `git reset --hard`, checkout-discard commands, worktree removal, or branch deletion. If cleanup is needed, give the command to the user instead of executing it.
- Do not add dependencies. `requirements.txt` remains runtime-only and should still contain `jsonschema`.
- Use the agent Python for commands that are executed while implementing this plan because this workspace does not provide a bare `python` command:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest discover -s tests -v
```

- Documentation snippets inside `SKILL.md` and references may use generic `python` because the skill is portable; executable implementation commands in this plan must use `/home/hyx/miniconda3/envs/agent/bin/python`.
- Tests must not use `tempfile.TemporaryDirectory()` because its cleanup deletes files. Use a unique `.codex-tmp/create-structure-md-phase7-tests/<name>-<uuid>/` directory and leave cleanup commands for the user instead.
- Keep Phase 7 scope to docs, examples, E2E tests, and any small code fixes required by those tests.

---

### Task 1: Reference Docs And Skill Workflow Contract

**Files:**
- Create: `tests/test_phase7_e2e.py`
- Modify: `SKILL.md`
- Modify: `references/dsl-spec.md`
- Modify: `references/document-structure.md`
- Modify: `references/mermaid-rules.md`
- Modify: `references/review-checklist.md`

- [ ] **Step 1: Write failing tests for Phase 7 reference and `SKILL.md` coverage**

Create `tests/test_phase7_e2e.py` with this initial content:

```python
import contextlib
import importlib.util
import io
import json
import subprocess
import sys
import unittest
import uuid
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
VALIDATE_DSL = ROOT / "scripts/validate_dsl.py"
VALIDATE_MERMAID = ROOT / "scripts/validate_mermaid.py"
RENDER_MARKDOWN = ROOT / "scripts/render_markdown.py"
EXAMPLE_PATHS = [
    ROOT / "examples/minimal-from-code.dsl.json",
    ROOT / "examples/minimal-from-requirements.dsl.json",
]
PHASE7_TMP_ROOT = ROOT / ".codex-tmp/create-structure-md-phase7-tests"


def read_text(relative_path):
    return (ROOT / relative_path).read_text(encoding="utf-8")


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def run_command(args):
    return subprocess.run(
        [PYTHON, *[str(arg) for arg in args]],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def make_run_dir(name):
    path = PHASE7_TMP_ROOT / f"{name}-{uuid.uuid4().hex}"
    path.mkdir(parents=True, exist_ok=False)
    return path


def load_mermaid_module():
    spec = importlib.util.spec_from_file_location("validate_mermaid_phase7", VALIDATE_MERMAID)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def call_main(module, argv):
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        try:
            result = module.main(argv)
        except SystemExit as exc:
            result = exc.code
    return result or 0, stdout.getvalue(), stderr.getvalue()


class Phase7ReferenceDocumentationTests(unittest.TestCase):
    REQUIRED_PHRASES = {
        "references/dsl-spec.md": [
            "input readiness contract",
            "DSL top-level fields",
            "common metadata",
            "ID prefix conventions",
            "defining ID fields",
            "reference ID fields",
            "authoritative field contract",
            "fixed table row fields",
            "support data object shapes",
            "traceability target mapping",
            "validation policy outside DSL",
            "source snippet rules",
            "empty_allowed",
            "required",
            "min_rows",
        ],
        "references/document-structure.md": [
            "output filename policy",
            "fixed 9-chapter outline",
            "fixed subchapter numbering",
            "chapter-by-chapter rendering positions",
            "fixed table visible columns",
            "empty-state sentences",
            "table-row support-data placement",
            "Chapter 9 rendering behavior",
            "module- or system-specific",
            "Generic-only filenames are forbidden",
        ],
        "references/mermaid-rules.md": [
            "Mermaid-only output rule",
            "supported MVP diagram types",
            "unsupported diagram types",
            "diagram field policy",
            "DSL source without fences",
            "strict/static validation difference",
            "CLI examples",
            "Graphviz/DOT rejection",
            "static-only acceptance reporting",
            "flowchart",
            "graph",
            "sequenceDiagram",
            "classDiagram",
            "stateDiagram-v2",
        ],
        "references/review-checklist.md": [
            "no repo analysis",
            "module- or system-specific output file",
            "generic filename rejection",
            "final output path",
            "temporary work directory",
            "default output overwrite protection",
            "`--overwrite`",
            "`--backup`",
            "Mermaid-only diagram output",
            "strict Mermaid validation",
            "static-only Mermaid fallback reporting",
            "Graphviz fully removed",
            "no final image artifacts",
            "no Jinja2",
            "validation policy outside DSL",
            "low-confidence summary whitelist",
            "source snippet secret review",
            "fixed 9 chapters",
            "fixed numbering",
            "post-render Markdown Mermaid validation",
        ],
    }

    def test_reference_files_contain_phase_7_contracts(self):
        for relative_path, phrases in self.REQUIRED_PHRASES.items():
            text = read_text(relative_path).casefold()
            with self.subTest(path=relative_path):
                for phrase in phrases:
                    self.assertIn(phrase.casefold(), text)

    def test_skill_points_to_references_and_full_workflow(self):
        text = read_text("SKILL.md")
        required = [
            "references/dsl-spec.md",
            "references/mermaid-rules.md",
            "references/document-structure.md",
            "references/review-checklist.md",
            "python scripts/validate_dsl.py structure.dsl.json",
            "python scripts/validate_mermaid.py --from-dsl structure.dsl.json --strict",
            "python scripts/render_markdown.py structure.dsl.json --output-dir",
            "python scripts/validate_mermaid.py --from-markdown <output-file> --static",
            "explicitly accepts static-only validation",
            "Mermaid diagrams were not proven renderable by Mermaid CLI",
            "output path",
            "temporary work directory",
            "assumptions",
            "low-confidence items",
        ]
        for phrase in required:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)
```

- [ ] **Step 2: Run tests to verify the documentation tests fail**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_phase7_e2e.Phase7ReferenceDocumentationTests -v
```

Expected: fail because the current reference docs are still short signpost documents and do not include the full Phase 7 contract phrases.

- [ ] **Step 3: Update `SKILL.md` workflow wording**

Keep the YAML front matter unchanged. Replace the current `## Workflow` section with content equivalent to:

The snippet below is portable skill documentation and intentionally uses generic `python`. Do not execute this generic snippet during implementation in this workspace; all executable verification commands in this plan use `/home/hyx/miniconda3/envs/agent/bin/python`.

```markdown
## Workflow

1. Create a temporary work directory.
2. Read `references/dsl-spec.md` before writing DSL content.
3. Write one complete DSL JSON file, optionally after smaller staged JSON files.
4. Run `python scripts/validate_dsl.py structure.dsl.json`.
5. Read `references/mermaid-rules.md` before creating or revising Mermaid diagrams.
6. Run `python scripts/validate_mermaid.py --from-dsl structure.dsl.json --strict --work-dir <temporary-work-directory>/mermaid`.
7. Render exactly one document with `python scripts/render_markdown.py structure.dsl.json --output-dir <output-dir>`.
8. Run `python scripts/validate_mermaid.py --from-markdown <output-file> --static`.
9. Review the generated document with `references/review-checklist.md`.
10. Report the output path, temporary work directory, assumptions, low-confidence items, and any static-only Mermaid acceptance.

Strict Mermaid validation is the default final-generation gate. If local Mermaid CLI tooling is unavailable, stop and ask the user before using static-only validation. The final report must say that Mermaid diagrams were not proven renderable by Mermaid CLI, that local tooling was unavailable, and that the user explicitly accepts static-only validation for this run.
```

Also update `## References` so it says:

```markdown
Read these references as needed instead of expanding `SKILL.md` into a monolithic guide:

- `references/dsl-spec.md`
- `references/document-structure.md`
- `references/mermaid-rules.md`
- `references/review-checklist.md`
```

- [ ] **Step 4: Expand `references/dsl-spec.md`**

Make sure the document includes these exact headings and bullet-level contracts:

```markdown
## Input Readiness Contract

Codex prepares project understanding outside this skill. The DSL must already contain enough document-ready content for modules, responsibilities, relationships, external capabilities, interfaces, internal structure, runtime units, key flows, Mermaid diagram concepts, configuration/data/dependency items when applicable, support references, confidence values, and safe snippets.

## DSL Top-Level Fields

The root fields are `dsl_version`, `document`, `system_overview`, `architecture_views`, `module_design`, `runtime_view`, `configuration_data_dependencies`, `cross_module_collaboration`, `key_flows`, `structure_issues_and_suggestions`, `evidence`, `traceability`, `risks`, `assumptions`, and `source_snippets`.

## Common Metadata

Design items that carry metadata use `confidence`, `evidence_refs`, `traceability_refs`, and `source_snippet_refs`. Confidence values are `observed`, `inferred`, or `unknown`.

## ID Prefix Conventions

Use `MOD-`, `CAP-`, `RUN-`, `FLOW-`, `CFG-`, `DATA-`, `DEP-`, `COL-`, `STEP-`, `BR-`, `MER-`, `TBL-`, `EV-`, `TR-`, `RISK-`, `ASM-`, and `SNIP-` according to the object kind.

## Defining ID Fields And Reference ID Fields

Defining ID fields create objects that can be referenced later. Reference ID fields must resolve to a compatible defining ID. Index-only rows such as `key_flows.flow_index.rows[]` reference flow details and do not carry confidence.

## Authoritative Field Contract

Fields owned by schema, renderer, and references must not be duplicated inside DSL instances. DSL instances provide content only.

## Fixed Table Row Fields

Fixed tables use fixed row fields owned by the schema. DSL instances must not include table-level rendering controls or table column declarations for fixed tables.

## Support Data Object Shapes

`evidence` records source, requirement, note, or analysis facts. `traceability` maps external sources to target IDs. `risks` and `assumptions` render in Chapter 9. `source_snippets` are evidence-only excerpts and must be referenced by at least one design item.

## Traceability Target Mapping

`traceability[].target_type` and `traceability[].target_id` are the authoritative binding. Local `traceability_refs` are backlinks and must point to traceability entries whose target matches the current node.

## Validation Policy Outside DSL

Validation policy outside DSL means DSL instances must not contain `empty_allowed`, `required`, `min_rows`, renderer flags, lint flags, or similar policy fields.

## Source Snippet Rules

Use snippets sparingly, keep them short, redact secrets and personal data, and use snippets only as evidence. Source snippets may render near supported nodes, but never inside Markdown table cells.
```

- [ ] **Step 5: Expand `references/document-structure.md`**

Keep the current fixed outline and add these sections with concrete wording. Ensure `references/document-structure.md` contains the exact phrase `fixed 9-chapter outline`:

```markdown
This section is the fixed 9-chapter outline for rendered Markdown.

## Fixed Subchapter Numbering

Optional content must not shift fixed numbering. Empty optional content renders a fixed empty-state sentence when the renderer owns an empty state, or renders no extra block when omission is allowed.

## Chapter-By-Chapter Rendering Positions

Chapter 1 renders document metadata. Chapter 2 renders summary, purpose, core capabilities, and notes. Chapter 3 renders architecture summary, module introduction table, required module relationship diagram, and optional architecture extras. Chapter 4 renders one module section per Chapter 3 module row. Chapter 5 renders runtime summary, runtime units, required runtime flow diagram, optional sequence diagram, and extras. Chapter 6 renders configuration, structural data/artifacts, dependencies, and extras. Chapter 7 renders collaboration summary, scenarios, required relationship diagram when applicable, and extras. Chapter 8 renders flow overview, optional extras, flow index, and flow details. Chapter 9 renders free-form issues, risks, assumptions, and low-confidence summaries.

## Fixed Table Visible Columns

Fixed tables expose human-readable columns only. IDs, confidence, evidence refs, traceability refs, and source snippet refs stay hidden from normal fixed tables except where Chapter 9 intentionally shows IDs and confidence for review.

## Empty-State Sentences

Chapter 6 empty tables render fixed empty-state sentences for configuration items, structural data/artifacts, and dependencies. Single-module Chapter 7 renders fixed collaboration absence text and no-diagram text while preserving sections 7.1 through 7.4.

## Table-Row Support-Data Placement

Support data for fixed table rows renders after the table and is grouped by stable row ID and display label. Extra table row evidence renders after the extra table by using the first non-empty displayed row value as the support label.

## Chapter 9 Rendering Behavior

Chapter 9 renders the free-form issue text when present. It also renders `risks`, `assumptions`, and the low-confidence summary whitelist. The low-confidence summary excludes evidence, traceability, source snippets, risks, assumptions, and Mermaid diagrams.
```

- [ ] **Step 6: Expand `references/mermaid-rules.md`**

Add sections with these exact contract points:

~~~markdown
## Mermaid-Only Output Rule

Final diagrams are Markdown Mermaid code blocks. The skill does not create final Graphviz, DOT, SVG, PNG, PDF, or image-export deliverables. Strict validation may create temporary Mermaid CLI artifacts under `--work-dir` solely for validation.

## Supported MVP Diagram Types

The supported MVP diagram types are `flowchart`, `graph`, `sequenceDiagram`, `classDiagram`, and `stateDiagram-v2`.

## Unsupported Diagram Types

Unsupported Mermaid diagram families such as `erDiagram`, `journey`, `gantt`, `pie`, `gitGraph`, `mindmap`, C4 diagrams, beta diagrams, and unknown diagram types must be rejected or revised before final generation.

## Diagram Field Policy

Required diagrams must be full diagram objects with non-empty `source`. Optional diagram fields may be omitted. If an optional diagram object is present, it must be a full diagram object; empty optional sources render the documented empty state only where the renderer explicitly supports that behavior.

## DSL Source Without Fences

DSL diagram `source` values contain Mermaid source only. They must not include Markdown fences such as ```` ```mermaid ````.

## Strict/Static Validation Difference

Strict validation runs local Mermaid CLI tooling and proves diagrams are renderable. Static validation checks deterministic source shape, supported types, non-empty Mermaid blocks, and Graphviz/DOT rejection.

## CLI Examples

```bash
python scripts/validate_mermaid.py --check-env
python scripts/validate_mermaid.py --from-dsl structure.dsl.json --strict --work-dir <temporary-work-directory>/mermaid
python scripts/validate_mermaid.py --from-dsl structure.dsl.json --static
python scripts/validate_mermaid.py --from-markdown output.md --static
```

## Graphviz/DOT Rejection

Graphviz/DOT rejection applies to both DSL and rendered Markdown. Do not use `digraph`, DOT edge syntax, `rankdir`, `dot`, or `graphviz` fenced code blocks.

## Static-Only Acceptance Reporting

If strict validation cannot run because Mermaid CLI tooling is unavailable, Codex must ask the user before using static-only validation. The final report must state that strict validation was not performed, local Mermaid CLI tooling was unavailable, the user accepted static-only validation, and Mermaid diagrams were not proven renderable by Mermaid CLI.
~~~

- [ ] **Step 7: Expand `references/review-checklist.md`**

Add checklist bullets covering each Phase 7 acceptance point. Include these exact phrases:

```markdown
## Final Report

- Confirm the final report includes the final output path and temporary work directory.
- Confirm assumptions and low-confidence items are reported when present.
- Confirm static-only Mermaid fallback reporting is included when strict validation was not run.
- Confirm strict Mermaid validation is the default final-generation gate unless the user accepted static-only validation.
- Confirm the module- or system-specific output file path is reported.
- Confirm generic filename rejection is reported when the renderer or validator refuses a generic-only filename.
- Confirm default output overwrite protection is reported when an existing file blocks rendering.

## Boundary Checks

- Confirm no repo analysis, requirements inference, multi-document generation, Word/PDF output, image export, Graphviz output, or Jinja2 template rendering happened inside the skill.
- Confirm Graphviz fully removed means no final image artifacts and no `dot` or `graphviz` code fences.
- Confirm Mermaid-only diagram output: final diagrams are Markdown Mermaid fences, not image artifacts.

## DSL Policy Checks

- Confirm validation policy outside DSL: DSL instances do not contain `empty_allowed`, `required`, `min_rows`, or similar policy fields.
- Confirm common metadata, canonical module IDs, traceability target mappings, and ID reference rules are respected.
- Confirm optional, required, and extra diagram rules are followed.
- Confirm low-confidence summary whitelist excludes support data, risks, assumptions, and diagrams.

## Text Safety

- Confirm plain text and Markdown-capable field safety.
- Confirm structure-design lint for normal design text.
- Confirm source snippets as evidence-only exceptions.
- Confirm source snippet secret review was performed.

## Rendered Structure

- Confirm fixed 9 chapters and fixed numbering.
- Confirm fixed table columns are owned by renderer/schema/reference docs, not DSL instances.
- Confirm table-row support data rendered outside Markdown table cells.
- Confirm required Mermaid diagrams and post-render Markdown Mermaid validation passed.
- Confirm evidence and snippet restraint.
- Confirm Chapter 9 risk/assumption/low-confidence visibility.
```

- [ ] **Step 8: Run documentation tests to verify they pass**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_phase7_e2e.Phase7ReferenceDocumentationTests -v
```

Expected: pass.

- [ ] **Step 9: Commit Task 1**

Run:

```bash
git add SKILL.md references/dsl-spec.md references/document-structure.md references/mermaid-rules.md references/review-checklist.md tests/test_phase7_e2e.py
git commit -m "docs: complete phase seven reference contracts"
```

Expected: commit succeeds with only the listed files staged.

---

### Task 2: Example DSL Coverage And Support Data

**Files:**
- Modify: `tests/test_phase7_e2e.py`
- Modify: `examples/minimal-from-code.dsl.json`
- Modify: `examples/minimal-from-requirements.dsl.json`

- [ ] **Step 1: Add failing tests for Phase 7 example content contracts**

Append this helper and test class to `tests/test_phase7_e2e.py`:

```python
POLICY_FIELD_NAMES = {"empty_allowed", "required", "min_rows"}


def walk_json(value, path="$"):
    if isinstance(value, dict):
        for key, child in value.items():
            yield f"{path}.{key}", key, child
            yield from walk_json(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from walk_json(child, f"{path}[{index}]")


def non_empty_rows(document, *path):
    current = document
    for part in path:
        current = current[part]
    return len(current["rows"]) > 0


class Phase7ExampleContractTests(unittest.TestCase):
    def test_examples_have_no_policy_fields_or_graphviz_content(self):
        for path in EXAMPLE_PATHS:
            document = load_json(path)
            text = path.read_text(encoding="utf-8")
            with self.subTest(path=path.name):
                for json_path, key, _ in walk_json(document):
                    self.assertNotIn(key, POLICY_FIELD_NAMES, json_path)
                self.assertNotIn("```dot", text)
                self.assertNotIn("```graphviz", text)
                self.assertNotRegex(text, r"(?im)^\s*digraph\b")
                self.assertNotRegex(text, r"(?im)^\s*rankdir\s*=")

    def test_examples_cover_minimum_fixed_chapter_content(self):
        for path in EXAMPLE_PATHS:
            document = load_json(path)
            with self.subTest(path=path.name):
                self.assertTrue(document["document"]["output_file"].endswith("_STRUCTURE_DESIGN.md"))
                self.assertNotIn(document["document"]["output_file"], {"STRUCTURE_DESIGN.md", "structure_design.md", "design.md", "软件结构设计说明书.md"})
                self.assertTrue(document["system_overview"]["summary"])
                self.assertGreaterEqual(len(document["system_overview"]["core_capabilities"]), 1)
                self.assertTrue(non_empty_rows(document, "architecture_views", "module_intro"))
                self.assertTrue(document["architecture_views"]["module_relationship_diagram"]["source"].strip())
                self.assertEqual(
                    len(document["architecture_views"]["module_intro"]["rows"]),
                    len(document["module_design"]["modules"]),
                )
                for module in document["module_design"]["modules"]:
                    self.assertGreaterEqual(len(module["external_capability_details"]["provided_capabilities"]["rows"]), 1)
                    self.assertTrue(
                        module["internal_structure"]["diagram"]["source"].strip()
                        or module["internal_structure"]["textual_structure"].strip()
                    )
                self.assertTrue(non_empty_rows(document, "runtime_view", "runtime_units"))
                self.assertTrue(document["runtime_view"]["runtime_flow_diagram"]["source"].strip())
                self.assertIn("configuration_items", document["configuration_data_dependencies"])
                self.assertIn("structural_data_artifacts", document["configuration_data_dependencies"])
                self.assertIn("dependencies", document["configuration_data_dependencies"])
                self.assertGreaterEqual(len(document["key_flows"]["flow_index"]["rows"]), 1)
                self.assertGreaterEqual(len(document["key_flows"]["flows"]), 1)
                for flow in document["key_flows"]["flows"]:
                    self.assertGreaterEqual(len(flow["steps"]), 1)
                    self.assertTrue(flow["diagram"]["source"].strip())
                self.assertIn("structure_issues_and_suggestions", document)
                for support_array in ["evidence", "traceability", "risks", "assumptions", "source_snippets"]:
                    self.assertIn(support_array, document)

    def test_examples_collectively_exercise_support_data_and_low_confidence(self):
        documents = [load_json(path) for path in EXAMPLE_PATHS]
        self.assertTrue(any(document["evidence"] for document in documents))
        self.assertTrue(any(document["traceability"] for document in documents))
        self.assertTrue(any(document["risks"] or document["assumptions"] for document in documents))
        self.assertTrue(any(document["source_snippets"] for document in documents))

        low_confidence_paths = []
        for document in documents:
            for json_path, key, value in walk_json(document):
                if key == "confidence" and value == "unknown":
                    low_confidence_paths.append(json_path)
        self.assertTrue(low_confidence_paths)
        self.assertTrue(any(".architecture_views.module_intro.rows" in path or ".module_design.modules" in path for path in low_confidence_paths))
```

- [ ] **Step 2: Run tests to verify the support-data coverage test fails**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_phase7_e2e.Phase7ExampleContractTests -v
```

Expected: `test_examples_collectively_exercise_support_data_and_low_confidence` fails because the current examples contain empty support arrays and no low-confidence whitelisted item.

- [ ] **Step 3: Add support-data coverage to `minimal-from-requirements.dsl.json`**

Update only `examples/minimal-from-requirements.dsl.json` unless the minimum-content test identifies a concrete gap in `minimal-from-code.dsl.json`.

Make these exact data changes:

1. Set `architecture_views.module_intro.rows[0].confidence` to `unknown`.
2. Set `module_design.modules[0].evidence_refs` to `["EV-REQ-INPUT"]`.
3. Set `module_design.modules[0].traceability_refs` to `["TR-REQ-MODULE"]`.
4. Set `module_design.modules[0].source_snippet_refs` to `["SNIP-WORKFLOW"]`.
5. Replace the final support arrays with:

```json
"evidence": [
  {
    "id": "EV-REQ-INPUT",
    "kind": "requirement",
    "title": "最小需求说明",
    "location": "examples/minimal-from-requirements.dsl.json",
    "description": "需求来源已经由 Codex 整理为结构设计 DSL 内容。",
    "confidence": "observed"
  }
],
"traceability": [
  {
    "id": "TR-REQ-MODULE",
    "source_external_id": "REQ-MIN-001",
    "source_type": "requirement",
    "target_type": "module",
    "target_id": "MOD-SKILL",
    "description": "需求示例映射到技能文档生成模块。"
  }
],
"risks": [
  {
    "id": "RISK-STATIC-ONLY",
    "description": "本地 Mermaid CLI 不可用时只能进行静态校验。",
    "impact": "图表语法未被 Mermaid CLI 证明可渲染。",
    "mitigation": "最终生成前优先运行 strict 校验；无法运行时取得用户显式接受并在报告中说明。",
    "confidence": "inferred",
    "evidence_refs": ["EV-REQ-INPUT"],
    "traceability_refs": [],
    "source_snippet_refs": ["SNIP-WORKFLOW"]
  }
],
"assumptions": [
  {
    "id": "ASM-PREPARED-CONTENT",
    "description": "调用方已经在技能外完成需求理解。",
    "rationale": "create-structure-md 只渲染已准备好的结构设计内容。",
    "validation_suggestion": "使用技能前检查输入准备契约。",
    "confidence": "unknown",
    "evidence_refs": ["EV-REQ-INPUT"],
    "traceability_refs": [],
    "source_snippet_refs": []
  }
],
"source_snippets": [
  {
    "id": "SNIP-WORKFLOW",
    "path": "SKILL.md",
    "line_start": 31,
    "line_end": 33,
    "language": "markdown",
    "purpose": "展示工作流入口中的 DSL 校验步骤。",
    "content": "1. Create a temporary work directory.\n2. Read `references/dsl-spec.md` before writing DSL content.\n3. Write one complete DSL JSON file, optionally after smaller staged JSON files.",
    "confidence": "observed"
  }
]
```

- [ ] **Step 4: Validate both examples**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python scripts/validate_dsl.py examples/minimal-from-code.dsl.json
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python scripts/validate_dsl.py examples/minimal-from-requirements.dsl.json
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python scripts/validate_mermaid.py --from-dsl examples/minimal-from-code.dsl.json --static
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python scripts/validate_mermaid.py --from-dsl examples/minimal-from-requirements.dsl.json --static
```

Expected:

```text
Validation succeeded
Mermaid validation succeeded
```

`minimal-from-requirements.dsl.json` may print a low-confidence warning; return code must still be `0`.

- [ ] **Step 5: Run example contract tests**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_phase7_e2e.Phase7ExampleContractTests -v
```

Expected: pass.

- [ ] **Step 6: Commit Task 2**

Run:

```bash
git add examples/minimal-from-code.dsl.json examples/minimal-from-requirements.dsl.json tests/test_phase7_e2e.py
git commit -m "test: cover phase seven example contracts"
```

Expected: commit succeeds with only example/test changes staged.

---

### Task 3: End-To-End Workflow Tests

**Files:**
- Modify: `tests/test_phase7_e2e.py`
- Modify only if tests expose a real bug: `scripts/validate_dsl.py`
- Modify only if tests expose a real bug: `scripts/validate_mermaid.py`
- Modify only if tests expose a real bug: `scripts/render_markdown.py`

- [ ] **Step 1: Add deterministic static end-to-end workflow tests**

Append this helper and test class to `tests/test_phase7_e2e.py`. These tests use static Mermaid validation for deterministic local coverage; Step 2 separately covers the strict Mermaid gate with mocked tooling.

```python
FIXED_RENDERED_HEADINGS = [
    "## 1. 文档信息",
    "## 2. 系统概览",
    "## 3. 架构视图",
    "### 3.1 架构概述",
    "### 3.2 各模块介绍",
    "### 3.3 模块关系图",
    "### 3.4 补充架构图表",
    "## 4. 模块设计",
    "## 5. 运行时视图",
    "### 5.1 运行时概述",
    "### 5.2 运行单元说明",
    "### 5.3 运行时流程图",
    "### 5.4 运行时序图（推荐）",
    "### 5.5 补充运行时图表",
    "## 6. 配置、数据与依赖关系",
    "### 6.1 配置项说明",
    "### 6.2 关键结构数据与产物",
    "### 6.3 依赖项说明",
    "### 6.4 补充图表",
    "## 7. 跨模块协作关系",
    "### 7.1 协作关系概述",
    "### 7.2 跨模块协作说明",
    "### 7.3 跨模块协作关系图",
    "### 7.4 补充协作图表",
    "## 8. 关键流程",
    "### 8.1 关键流程概述",
    "### 8.2 关键流程清单",
    "## 9. 结构问题与改进建议",
]


def assert_markers_in_order(testcase, text, markers):
    cursor = -1
    for marker in markers:
        index = text.find(marker)
        testcase.assertGreater(index, cursor, marker)
        cursor = index


class Phase7EndToEndWorkflowTests(unittest.TestCase):
    def test_examples_complete_static_end_to_end_workflow(self):
        for dsl_path in EXAMPLE_PATHS:
            document = load_json(dsl_path)
            tmpdir = make_run_dir(dsl_path.stem)
            with self.subTest(path=dsl_path.name):
                validate_dsl = run_command([VALIDATE_DSL, dsl_path])
                self.assertEqual(0, validate_dsl.returncode, validate_dsl.stderr)
                self.assertIn("Validation succeeded", validate_dsl.stdout)

                validate_dsl_mermaid = run_command([VALIDATE_MERMAID, "--from-dsl", dsl_path, "--static"])
                self.assertEqual(0, validate_dsl_mermaid.returncode, validate_dsl_mermaid.stderr)
                self.assertIn("Mermaid validation succeeded", validate_dsl_mermaid.stdout)

                render = run_command([RENDER_MARKDOWN, dsl_path, "--output-dir", tmpdir])
                self.assertEqual(0, render.returncode, render.stderr)

                output_path = tmpdir / document["document"]["output_file"]
                self.assertTrue(output_path.is_file())
                self.assertEqual([output_path], sorted(tmpdir.glob("*.md")))

                markdown = output_path.read_text(encoding="utf-8")
                validate_markdown_mermaid = run_command([VALIDATE_MERMAID, "--from-markdown", output_path, "--static"])
                self.assertEqual(0, validate_markdown_mermaid.returncode, validate_markdown_mermaid.stderr)
                self.assertIn("Mermaid validation succeeded", validate_markdown_mermaid.stdout)

                self.assertNotIn("```dot", markdown)
                self.assertNotIn("```graphviz", markdown)
                self.assertNotRegex(markdown, r"(?im)^\s*digraph\b")
                self.assertNotRegex(markdown, r"(?im)^\s*rankdir\s*=")
                assert_markers_in_order(self, markdown, FIXED_RENDERED_HEADINGS)
                first_flow_name = document["key_flows"]["flows"][0]["name"]
                assert_markers_in_order(
                    self,
                    markdown,
                    [
                        f"### 8.3 {first_flow_name}",
                        "#### 8.3.1 流程概述",
                        "#### 8.3.2 步骤说明",
                        "#### 8.3.3 异常/分支说明",
                        "#### 8.3.4 流程图",
                    ],
                )

    def test_static_workflow_renders_without_shifting_optional_numbering(self):
        for dsl_path in EXAMPLE_PATHS:
            document = load_json(dsl_path)
            tmpdir = make_run_dir(f"{dsl_path.stem}-numbering")
            with self.subTest(path=dsl_path.name):
                render = run_command([RENDER_MARKDOWN, dsl_path, "--output-dir", tmpdir])
                self.assertEqual(0, render.returncode, render.stderr)
                markdown = (tmpdir / document["document"]["output_file"]).read_text(encoding="utf-8")
                self.assertEqual(1, markdown.count("### 3.4 补充架构图表"))
                self.assertEqual(1, markdown.count("### 5.4 运行时序图（推荐）"))
                self.assertEqual(1, markdown.count("### 6.4 补充图表"))
                self.assertEqual(1, markdown.count("### 7.4 补充协作图表"))
                self.assertEqual(1, markdown.count("### 8.2 关键流程清单"))
                self.assertEqual(1, markdown.count("### 8.3 "))
```

- [ ] **Step 2: Add mocked strict Mermaid and static fallback tests**

Append this class to `tests/test_phase7_e2e.py`:

```python
class Phase7StrictMermaidAndFallbackTests(unittest.TestCase):
    def test_examples_pass_strict_mermaid_workflow_when_cli_is_available(self):
        module = load_mermaid_module()

        def fake_which(name):
            return {
                "node": "/usr/bin/node",
                "mmdc": "/usr/local/bin/mmdc",
            }.get(name)

        completed = subprocess.CompletedProcess(["mmdc"], 0, stdout="", stderr="")
        with (
            mock.patch.object(module.shutil, "which", side_effect=fake_which),
            mock.patch.object(module.subprocess, "run", return_value=completed),
        ):
            for dsl_path in EXAMPLE_PATHS:
                tmpdir = make_run_dir(f"{dsl_path.stem}-strict")
                code, stdout, stderr = call_main(
                    module,
                    ["--from-dsl", str(dsl_path), "--strict", "--work-dir", str(tmpdir / "mermaid-work")],
                )
                with self.subTest(path=dsl_path.name):
                    self.assertEqual(0, code, stderr)
                    self.assertIn("Mermaid validation succeeded", stdout)

    def test_check_env_and_reference_docs_cover_static_only_fallback(self):
        module = load_mermaid_module()
        with mock.patch.object(module.shutil, "which", side_effect=lambda name: "/usr/bin/node" if name == "node" else None):
            code, stdout, stderr = call_main(module, ["--check-env"])

        self.assertEqual(1, code)
        self.assertIn("node: found at /usr/bin/node", stdout)
        self.assertIn("mmdc: missing", stdout)
        self.assertEqual("", stderr)

        combined_docs = "\n".join(
            read_text(path)
            for path in [
                "SKILL.md",
                "references/mermaid-rules.md",
                "references/review-checklist.md",
            ]
        )
        self.assertIn("ask the user before using static-only validation", combined_docs)
        self.assertIn("user accepted static-only validation", combined_docs)
        self.assertIn("Mermaid diagrams were not proven renderable by Mermaid CLI", combined_docs)
```

- [ ] **Step 3: Run the new E2E tests and inspect any implementation failures**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_phase7_e2e.Phase7EndToEndWorkflowTests tests.test_phase7_e2e.Phase7StrictMermaidAndFallbackTests -v
```

Expected: pass after Tasks 1 and 2. If a failure appears in `scripts/validate_dsl.py`, `scripts/validate_mermaid.py`, or `scripts/render_markdown.py`, fix only the failing contract and add a focused assertion to `tests/test_phase7_e2e.py` or the owning script test file.

- [ ] **Step 4: Commit Task 3**

Run:

```bash
git add tests/test_phase7_e2e.py scripts/validate_dsl.py scripts/validate_mermaid.py scripts/render_markdown.py
git commit -m "test: add phase seven end-to-end workflow coverage"
```

Expected: commit succeeds. If no script files changed, stage only `tests/test_phase7_e2e.py`.

---

### Task 4: Documentation-Driven Acceptance Sweep

**Files:**
- Modify if required by failing tests: `references/dsl-spec.md`
- Modify if required by failing tests: `references/document-structure.md`
- Modify if required by failing tests: `references/mermaid-rules.md`
- Modify if required by failing tests: `references/review-checklist.md`
- Modify if required by failing tests: `SKILL.md`
- Modify if required by failing tests: `examples/minimal-from-code.dsl.json`
- Modify if required by failing tests: `examples/minimal-from-requirements.dsl.json`
- Modify if required by failing tests: `tests/test_phase7_e2e.py`

- [ ] **Step 1: Run all Phase 7 acceptance tests**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_phase7_e2e -v
```

Expected: pass.

- [ ] **Step 2: Ask the user to run existing example and reference tests that overlap Phase 7**

The existing test modules still contain `tempfile.TemporaryDirectory()` cleanup. To respect the user rule against deletion operations, do not execute this command as an agent unless those existing tests have first been migrated away from auto-cleanup. Provide this command to the user and record their result:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_validate_dsl.SchemaExampleValidationTests tests.test_validate_dsl_semantics.AcceptanceTests tests.test_validate_mermaid.MermaidIntegrationRegressionTests tests.test_render_markdown.ReferenceSignpostTests tests.test_render_markdown.RendererIntegrationTests -v
```

Expected user-reported result: pass.

- [ ] **Step 3: Manually run the documented workflow for both examples**

First check whether strict Mermaid tooling is available:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python scripts/validate_dsl.py examples/minimal-from-code.dsl.json
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python scripts/validate_dsl.py examples/minimal-from-requirements.dsl.json
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python scripts/validate_mermaid.py --check-env
```

If `--check-env` exits `0`, run the strict pre-render workflow:

```bash
mkdir -p .codex-tmp/create-structure-md-e2e-code .codex-tmp/create-structure-md-e2e-requirements .codex-tmp/create-structure-md-e2e-code-mermaid .codex-tmp/create-structure-md-e2e-requirements-mermaid
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python scripts/validate_mermaid.py --from-dsl examples/minimal-from-code.dsl.json --strict --work-dir .codex-tmp/create-structure-md-e2e-code-mermaid
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python scripts/render_markdown.py examples/minimal-from-code.dsl.json --output-dir .codex-tmp/create-structure-md-e2e-code
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python scripts/validate_mermaid.py --from-markdown .codex-tmp/create-structure-md-e2e-code/create-structure-md_STRUCTURE_DESIGN.md --static
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python scripts/validate_mermaid.py --from-dsl examples/minimal-from-requirements.dsl.json --strict --work-dir .codex-tmp/create-structure-md-e2e-requirements-mermaid
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python scripts/render_markdown.py examples/minimal-from-requirements.dsl.json --output-dir .codex-tmp/create-structure-md-e2e-requirements
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python scripts/validate_mermaid.py --from-markdown .codex-tmp/create-structure-md-e2e-requirements/requirements-note-example_STRUCTURE_DESIGN.md --static
```

If `--check-env` exits non-zero, stop and ask the user whether static-only Mermaid validation is acceptable for this run. Only after the user explicitly accepts, run the static fallback:

```bash
mkdir -p .codex-tmp/create-structure-md-e2e-code .codex-tmp/create-structure-md-e2e-requirements
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python scripts/validate_mermaid.py --from-dsl examples/minimal-from-code.dsl.json --static
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python scripts/render_markdown.py examples/minimal-from-code.dsl.json --output-dir .codex-tmp/create-structure-md-e2e-code
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python scripts/validate_mermaid.py --from-markdown .codex-tmp/create-structure-md-e2e-code/create-structure-md_STRUCTURE_DESIGN.md --static
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python scripts/validate_mermaid.py --from-dsl examples/minimal-from-requirements.dsl.json --static
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python scripts/render_markdown.py examples/minimal-from-requirements.dsl.json --output-dir .codex-tmp/create-structure-md-e2e-requirements
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python scripts/validate_mermaid.py --from-markdown .codex-tmp/create-structure-md-e2e-requirements/requirements-note-example_STRUCTURE_DESIGN.md --static
```

Expected:

```text
Validation succeeded
node: found at <node-path>
mmdc: found at <mmdc-path>
mermaid-cli: <version>
Mermaid validation succeeded: <n> diagram(s) checked in strict mode.
Markdown rendered: <output-path>
Mermaid validation succeeded
```

If strict tooling is unavailable and the user accepts the static fallback, record in the final report that strict validation was not performed, local Mermaid CLI tooling was unavailable, the user accepted static-only validation, and Mermaid diagrams were not proven renderable by Mermaid CLI.

If the render step fails because a previous manual run left files in `.codex-tmp/create-structure-md-e2e-code`, `.codex-tmp/create-structure-md-e2e-requirements`, or the Mermaid work directories, do not delete them. Either use a new output directory name with a timestamp or give the cleanup command to the user to run.

- [ ] **Step 4: Review generated Markdown against checklist**

Open the two generated Markdown files and confirm:

```text
1. Each output filename is module- or system-specific.
2. Each document has exactly the fixed 9 chapter headings.
3. No rendered Markdown contains ```dot or ```graphviz fences.
4. Required Mermaid diagrams are rendered as ```mermaid fences.
5. Chapter 6 and Chapter 7 empty states do not shift numbering.
6. The requirements example renders risk, assumption, source snippet, and low-confidence information in Chapter 9.
7. Support data renders outside table cells.
8. The final report data points are documented in references/review-checklist.md.
```

- [ ] **Step 5: Commit Task 4**

Run:

```bash
git add SKILL.md references/dsl-spec.md references/document-structure.md references/mermaid-rules.md references/review-checklist.md examples/minimal-from-code.dsl.json examples/minimal-from-requirements.dsl.json tests/test_phase7_e2e.py
git commit -m "docs: align phase seven acceptance workflow"
```

Expected: commit succeeds only if Task 4 required adjustments. If there were no changes, do not create an empty commit.

---

### Task 5: Full Suite Verification And Handoff

**Files:**
- Verify only: all project files

- [ ] **Step 1: Ask the user to run the full test suite**

The existing suite still contains tests that use `tempfile.TemporaryDirectory()` cleanup. To respect the user rule against deletion operations, do not execute this command as an agent unless those tests have first been migrated away from auto-cleanup. Provide this command to the user and record their result:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest discover -s tests -v
```

Expected user-reported result: all tests pass.

- [ ] **Step 2: Check strict Mermaid tooling availability**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python scripts/validate_mermaid.py --check-env
```

Expected when Mermaid CLI is installed:

```text
node: found at <node-path>
mmdc: found at <mmdc-path>
mermaid-cli: <version>
```

Expected when Mermaid CLI is unavailable:

```text
node: found at <node-path> or node: missing
mmdc: missing
```

If `mmdc` is missing, do not claim strict validation passed. Report that static tests passed and strict Mermaid CLI validation remains environment-dependent.

- [ ] **Step 3: Inspect git status**

Run:

```bash
git status --short
```

Expected: either clean, or only intentional uncommitted generated files under `.codex-tmp/`. Do not delete generated files. If cleanup is desired, provide the cleanup command for the user to run.

- [ ] **Step 4: Final implementation report**

Report:

```text
Phase 7 completed.

Changed:
- Reference docs now contain the full normal-use contract.
- SKILL.md now points to references and the full workflow.
- Examples validate, render, and collectively cover support data and low-confidence behavior.
- End-to-end tests cover validate DSL, Mermaid static from DSL, render Markdown, Mermaid static from Markdown, mocked strict Mermaid, fixed numbering, and Graphviz/DOT absence.

Verification:
- Full unittest command: PASS
- Example workflow: PASS
- Strict Mermaid environment: <available/unavailable; include --check-env result>

Notes:
- Generated output path(s): <paths if manual workflow was run>
- Temporary work directory path(s): <paths if manual workflow was run>
- Assumptions: <any remaining assumptions>
- Low-confidence items: <items intentionally present in examples>
- Static-only Mermaid acceptance: <not used / user accepted static-only for this run>
```

---

## Spec Coverage Review

- Reference files: Task 1 covers all required content for `dsl-spec.md`, `document-structure.md`, `mermaid-rules.md`, and `review-checklist.md`.
- `SKILL.md` final behavior: Task 1 covers input readiness, repo-analysis boundary, reference pointers, full workflow, and final report content.
- Examples: Task 2 covers schema validation, semantic validation, Mermaid static validation, all fixed chapters, concrete output filenames, support data, low-confidence item, and no policy fields.
- End-to-end workflow: Task 3 covers `validate_dsl.py`, `validate_mermaid.py --from-dsl`, `render_markdown.py`, `validate_mermaid.py --from-markdown`, fixed numbering, rendered output existence, and Graphviz/DOT absence.
- Strict Mermaid unavailable path: Task 3 covers `--check-env`, static fallback documentation, and explicit user-acceptance wording.
- Review checklist: Task 1 and Task 4 cover the checklist file and manual checklist review.
- Full acceptance: Task 5 covers `python -m unittest discover -s tests`, strict tooling reporting, git status, and final handoff.
