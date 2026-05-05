# create-structure-md V2 Phase 3 Content Blocks And Chapter 9 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement V2 Phase 3 reusable content blocks for Chapter 4 internal mechanism details and Chapter 9 structure issues.

**Architecture:** Keep create-structure-md as a renderer for prepared DSL content only. Add one shared content-block schema, semantic helper, and renderer helper, then wire it into `module_design.modules[].internal_mechanism.mechanism_details[].blocks[]` and `structure_issues_and_suggestions.blocks[]`. Chapter 9 moves from a free-form string to a fixed object with summary, blocks, and `not_applicable_reason`, while retaining risks, assumptions, and low-confidence output.

**Tech Stack:** Python 3, standard-library `unittest`, `jsonschema` Draft 2020-12, existing renderer helpers in `scripts/render_markdown.py`, no new runtime dependencies.

---

## Scope And Constraints

- Do not add repository analysis, requirement inference, Word/PDF/image export, Mermaid strict validation gates, rendered diagram completeness gates, or a V1-to-V2 migration tool.
- Do not modify `scripts/validate_mermaid.py` or `references/mermaid-rules.md`; Phase 4 owns Mermaid gates.
- Do not run deletion commands. Workspace instruction: when cleanup is needed, give the command to the user instead of executing it.
- Code edits may replace obsolete lines as part of normal patching, but do not remove files/directories or run shell cleanup commands. If a file/directory cleanup is needed, give the command to the user instead.
- Keep `dsl_version` fixed at `0.2.0`.
- Preserve evidence, traceability, and source snippet refs on blocks for validation and upstream tooling.
- Hidden evidence mode remains the renderer default and suppresses block support data.
- Inline evidence mode may render support data after a whole block.
- Table row support refs are forbidden for content-block tables. Support data attaches to the table block, not individual rows.
- Existing `extra_tables` behavior keeps its current row-level `evidence_refs` contract; do not break it while adding content-block tables.
- Content-block diagram rendering uses the current shared `render_mermaid_block()` in this phase. `diagram-id` metadata comments, rendered diagram completeness checks, and strict Mermaid gates remain Phase 4 work; when Phase 4 updates the shared Mermaid renderer, content-block diagrams should inherit that behavior through the shared helper.
- Current baseline note: the full suite has 2 known strict Mermaid e2e failures in this sandbox because Puppeteer/Chromium cannot launch with the sandbox. Non-strict unit tests are the primary Phase 3 signal unless the environment supports `mmdc`.

Use the project Python for verification:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest discover -s tests -v
```

Targeted Phase 3 verification command:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_v2_phase3_content_blocks -v
```

Boundary guard after implementation:

```bash
git diff --exit-code -- scripts/validate_mermaid.py references/mermaid-rules.md
```

Expected: no diff.

---

## File Structure

- Create: `scripts/v2_phase3.py`
  - Owns reusable content-block semantic checks: shared section traversal, block ID uniqueness within parent, at-least-one-text-block rules, diagram/table ID shape rules that schema cannot fully express, block/diagram confidence matching, table row declared-key enforcement, table row support-ref rejection, and Chapter 9 summary/block/not-applicable contract checks that complement Phase 1 global gates.
- Modify: `scripts/validate_dsl.py`
  - Imports `v2_phase3.py`, calls Phase 3 checks after Phase 2 checks, registers content-block table IDs for global uniqueness, treats content-block diagram source fields as Mermaid source during Markdown safety checks, and keeps `validate_mermaid.py` untouched.
- Modify: `scripts/render_markdown.py`
  - Adds a shared content-block renderer helper and uses it from both Chapter 4 internal mechanism details and Chapter 9 structure issues. Replaces current Chapter 9 free-form rendering with fixed 9.1 to 9.4 sections.
- Modify: `schemas/structure-design.schema.json`
  - Adds reusable content-block definitions, updates `mechanismDetail.blocks[]` to accept text/diagram/table blocks, and replaces top-level `structure_issues_and_suggestions` string with an object.
- Create: `tests/test_v2_phase3_content_blocks.py`
  - Covers schema, semantic validation, rendering, hidden/inline support behavior, and Chapter 9 ordering for Phase 3.
- Modify: `tests/test_v2_phase2_module_model.py`
  - Removes or updates Phase 2 assertions that assume `mechanism_details[].blocks[]` only accepts text blocks.
- Modify: `tests/test_validate_dsl.py`
  - Updates schema-shape assertions for Chapter 9 object and reusable block definitions.
- Modify: `tests/test_validate_dsl_semantics.py`
  - Replaces free-form Chapter 9 Markdown-safety tests with object/summary/block tests and adds Phase 3 semantic regression coverage where this file already owns cross-cutting validation behavior.
- Modify: `tests/test_render_markdown.py`
  - Replaces the "Chapter 9 object shape fails" expectation with rendering expectations and adds shared block rendering assertions.
- Modify: `tests/test_phase7_e2e.py`
  - Updates example contract checks for the Chapter 9 object shape and content-block coverage.
- Modify: `tests/test_validate_mermaid.py`
  - Update expectations only if existing tests read schema/docs text that now mentions Phase 3 blocks. Do not add content-block DSL extraction expectations in this phase.
- Modify: `tests/fixtures/valid-v2-foundation.dsl.json`
  - Adds one text, one diagram, and one table block to the canonical internal mechanism detail, and migrates `structure_issues_and_suggestions` to the Phase 3 object shape.
- Modify: `examples/minimal-from-code.dsl.json`
  - Migrates Chapter 9 to object shape and keeps examples valid.
- Modify: `examples/minimal-from-requirements.dsl.json`
  - Migrates Chapter 9 to object shape and keeps examples valid.
- Modify: `references/dsl-spec.md`
  - Documents reusable content blocks and Chapter 9 object shape.
- Modify: `references/document-structure.md`
  - Documents Chapter 4 block rendering and the fixed Chapter 9 9.1 to 9.4 order.
- Modify: `references/review-checklist.md`
  - Adds Phase 3 reviewer checks for shared block behavior and Chapter 9 ordering.
- Modify: `SKILL.md`
  - Keeps the skill workflow aligned with the V2 Phase 3 DSL shape while preserving the no-repository-analysis boundary.
- Verify only: `scripts/validate_mermaid.py`
  - Must remain unchanged.
- Verify only: `references/mermaid-rules.md`
  - Must remain unchanged.
- Verify only: `requirements.txt`
  - Must still contain only `jsonschema`.

---

## Review History

This plan is intentionally review-driven. The main agent revises this section after each adversarial sub-agent pass.

- Draft: Initial main-agent plan before adversarial review.
- Round 1: Revised after adversarial review. Fixes added for the Mermaid CLI `--static` flag, pre-created output directories, object-aware `check_chapter_9`, Chapter 9 block ID registration, schema-vs-semantic test separation, recursive oneOf schema error reporting, Chapter 4 block title hierarchy, non-duplicated not-applicable checks, valid evidence fixture fields, and exact rendered example filenames.
- Round 2: Revised after adversarial review. Fixes added for Chapter 9 diagram block coverage, content-block diagram ID global uniqueness, explicit replacement of legacy Chapter 9 renderer tests, missing block support-ref validation, reserved support column keys, and repeat-safe `mktemp -d` render directories.
- Round 3: Final review found no Critical issues. Fixes added for dynamic `_id`/`_ids` content-block table row column names and an explicit Phase 4 boundary for `diagram-id` metadata comments.

---

### Task 1: Phase 3 Test Harness And Canonical Fixture Contract

**Files:**
- Create: `tests/test_v2_phase3_content_blocks.py`
- Modify: `tests/fixtures/valid-v2-foundation.dsl.json`

- [ ] **Step 1: Write the failing Phase 3 harness**

Create `tests/test_v2_phase3_content_blocks.py` with these imports, helpers, and contract tests:

```python
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas/structure-design.schema.json"
FIXTURE = ROOT / "tests/fixtures/valid-v2-foundation.dsl.json"
PYTHON = sys.executable


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def valid_document():
    return deepcopy(load_json(FIXTURE))


def write_json(tmpdir, name, document):
    path = Path(tmpdir) / name
    path.write_text(json.dumps(document, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def run_validator(path):
    return subprocess.run(
        [PYTHON, str(ROOT / "scripts/validate_dsl.py"), str(path)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def validation_stderr_for(document):
    with tempfile.TemporaryDirectory() as tmpdir:
        path = write_json(tmpdir, "case.dsl.json", document)
        completed = run_validator(path)
    return completed


def load_renderer_module():
    spec = importlib.util.spec_from_file_location(
        "render_markdown_phase3_under_test",
        ROOT / "scripts/render_markdown.py",
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def schema_errors(document):
    schema = load_json(SCHEMA)
    Draft202012Validator.check_schema(schema)
    return sorted(
        Draft202012Validator(schema).iter_errors(document),
        key=lambda error: list(error.path),
    )


class Phase3FixtureContractTests(unittest.TestCase):
    def test_valid_fixture_matches_phase3_schema_and_semantics(self):
        document = valid_document()
        self.assertEqual([], schema_errors(document))
        completed = run_validator(FIXTURE)
        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertIn("Validation succeeded", completed.stdout)

    def test_fixture_contains_reusable_blocks_in_chapter_4_and_chapter_9(self):
        document = valid_document()
        mechanism_blocks = document["module_design"]["modules"][0]["internal_mechanism"]["mechanism_details"][0]["blocks"]
        issue_blocks = document["structure_issues_and_suggestions"]["blocks"]

        self.assertEqual(["text", "diagram", "table"], [block["block_type"] for block in mechanism_blocks])
        self.assertEqual(["text", "diagram", "table"], [block["block_type"] for block in issue_blocks])
        self.assertEqual("MER-BLOCK-MECHANISM-FLOW", mechanism_blocks[1]["diagram"]["id"])
        self.assertEqual("TBL-BLOCK-MECHANISM-STAGES", mechanism_blocks[2]["table"]["id"])
        self.assertEqual("MER-BLOCK-STRUCTURE-ISSUES", issue_blocks[1]["diagram"]["id"])
        self.assertEqual("TBL-BLOCK-STRUCTURE-ISSUES", issue_blocks[2]["table"]["id"])

    def test_chapter_4_and_chapter_9_render_blocks_through_shared_visible_contract(self):
        renderer = load_renderer_module()
        markdown = renderer.render_markdown(valid_document())

        self.assertIn("DSL 校验管线说明", markdown)
        self.assertIn("DSL 校验管线图", markdown)
        self.assertIn("```mermaid\nflowchart TD", markdown)
        self.assertIn("| 阶段 | 说明 |", markdown)
        self.assertIn("### 9.1 风险清单", markdown)
        self.assertIn("### 9.2 假设清单", markdown)
        self.assertIn("### 9.3 低置信度项目", markdown)
        self.assertIn("### 9.4 结构问题与改进建议", markdown)
        self.assertIn("结构问题概览", markdown)
        self.assertIn("结构问题关系图", markdown)
        self.assertIn("| 问题 | 改进方向 |", markdown)

    def test_chapter_9_sections_render_in_fixed_order(self):
        renderer = load_renderer_module()
        markdown = renderer.render_markdown(valid_document())
        headings = [
            "### 9.1 风险清单",
            "### 9.2 假设清单",
            "### 9.3 低置信度项目",
            "### 9.4 结构问题与改进建议",
        ]
        positions = [markdown.index(heading) for heading in headings]
        self.assertEqual(sorted(positions), positions)
```

- [ ] **Step 2: Run the harness to verify it fails**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_v2_phase3_content_blocks.Phase3FixtureContractTests -v
```

Expected: FAIL or ERROR because the canonical fixture still has only text mechanism blocks and `structure_issues_and_suggestions` is still a string.

- [ ] **Step 3: Upgrade the canonical fixture to the Phase 3 target contract**

Modify `tests/fixtures/valid-v2-foundation.dsl.json`:

1. In `module_design.modules[0].internal_mechanism.mechanism_details[0].blocks`, keep the existing text block and append these two blocks:

```json
{
  "block_id": "BLOCK-SKILL-VALIDATION-DIAGRAM",
  "block_type": "diagram",
  "title": "DSL 校验管线图",
  "confidence": "observed",
  "evidence_refs": [],
  "traceability_refs": [],
  "source_snippet_refs": [],
  "diagram": {
    "id": "MER-BLOCK-MECHANISM-FLOW",
    "kind": "content_block",
    "title": "DSL 校验管线图",
    "diagram_type": "flowchart",
    "description": "展示校验管线如何从 DSL 输入走向校验结果。",
    "source": "flowchart TD\n  A[\"DSL JSON\"] --> B[\"Version gate\"]\n  B --> C[\"Schema validation\"]\n  C --> D[\"Semantic validation\"]\n  D --> E[\"Validation result\"]",
    "confidence": "observed"
  }
}
```

```json
{
  "block_id": "BLOCK-SKILL-VALIDATION-TABLE",
  "block_type": "table",
  "title": "DSL 校验管线阶段",
  "confidence": "observed",
  "evidence_refs": [],
  "traceability_refs": [],
  "source_snippet_refs": [],
  "table": {
    "id": "TBL-BLOCK-MECHANISM-STAGES",
    "title": "DSL 校验管线阶段",
    "columns": [
      { "key": "stage", "title": "阶段" },
      { "key": "description", "title": "说明" }
    ],
    "rows": [
      {
        "stage": "Version gate",
        "description": "拒绝非 0.2.0 DSL。"
      },
      {
        "stage": "Semantic validation",
        "description": "检查跨字段引用、not_applicable 互斥和内容安全。"
      }
    ]
  }
}
```

2. Replace top-level `structure_issues_and_suggestions` string with this object:

```json
{
  "summary": "结构问题概览：当前 V2 DSL 仍依赖上游提供完整结构内容，create-structure-md 只负责校验和渲染。",
  "blocks": [
    {
      "block_id": "ISSUE-TEXT-001",
      "block_type": "text",
      "title": "上游内容完整性",
      "text": "如果上游分析或人工整理没有提供完整 DSL，最终结构文档也会缺失对应章节内容。",
      "confidence": "observed",
      "evidence_refs": [],
      "traceability_refs": [],
      "source_snippet_refs": []
    },
    {
      "block_id": "ISSUE-DIAGRAM-001",
      "block_type": "diagram",
      "title": "结构问题关系图",
      "confidence": "observed",
      "evidence_refs": [],
      "traceability_refs": [],
      "source_snippet_refs": [],
      "diagram": {
        "id": "MER-BLOCK-STRUCTURE-ISSUES",
        "kind": "content_block",
        "title": "结构问题关系图",
        "diagram_type": "flowchart",
        "description": "展示上游内容完整性如何影响最终结构文档。",
        "source": "flowchart TD\n  A[\"Prepared DSL\"] --> B[\"Validation\"]\n  B --> C[\"Markdown rendering\"]\n  A --> D[\"Missing content risk\"]",
        "confidence": "observed"
      }
    },
    {
      "block_id": "ISSUE-TABLE-001",
      "block_type": "table",
      "title": "结构问题与改进方向",
      "confidence": "observed",
      "evidence_refs": [],
      "traceability_refs": [],
      "source_snippet_refs": [],
      "table": {
        "id": "TBL-BLOCK-STRUCTURE-ISSUES",
        "title": "结构问题与改进方向",
        "columns": [
          { "key": "issue", "title": "问题" },
          { "key": "improvement", "title": "改进方向" }
        ],
        "rows": [
          {
            "issue": "缺失仓库分析能力",
            "improvement": "由上游 repo-analysis skill 或人工准备 DSL。"
          }
        ]
      }
    }
  ],
  "not_applicable_reason": ""
}
```

- [ ] **Step 4: Run the harness again**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_v2_phase3_content_blocks.Phase3FixtureContractTests -v
```

Expected: still FAIL because the schema, validator, and renderer do not implement Phase 3 yet.

- [ ] **Step 5: Commit**

```bash
git add tests/test_v2_phase3_content_blocks.py tests/fixtures/valid-v2-foundation.dsl.json
git commit -m "test: define v2 phase 3 content block fixture"
```

---

### Task 2: Schema Shape For Shared Content Blocks And Chapter 9 Object

**Files:**
- Modify: `tests/test_v2_phase3_content_blocks.py`
- Modify: `schemas/structure-design.schema.json`

- [ ] **Step 1: Add failing schema-positive and schema-negative tests**

Append this test class to `tests/test_v2_phase3_content_blocks.py`:

```python
class Phase3SchemaShapeTests(unittest.TestCase):
    def flatten_schema_error_messages(self, errors):
        messages = []

        def visit(error):
            messages.append(f"{list(error.path)}: {error.message}")
            for child in error.context:
                visit(child)

        for error in errors:
            visit(error)
        return "\n".join(messages)

    def assert_schema_invalid(self, document, path_fragment):
        errors = schema_errors(document)
        self.assertTrue(errors, "Expected schema validation failure")
        rendered = self.flatten_schema_error_messages(errors)
        self.assertIn(path_fragment, rendered)

    def test_schema_accepts_content_block_shapes(self):
        document = valid_document()
        self.assertEqual([], schema_errors(document))

    def test_top_level_structure_issues_string_is_rejected(self):
        document = valid_document()
        document["structure_issues_and_suggestions"] = "旧版自由文本"
        self.assert_schema_invalid(document, "structure_issues_and_suggestions")

    def test_block_title_and_confidence_are_required(self):
        for field_name in ["title", "confidence"]:
            document = valid_document()
            block = document["structure_issues_and_suggestions"]["blocks"][0]
            block.pop(field_name)
            with self.subTest(field=field_name):
                self.assert_schema_invalid(document, field_name)

    def test_text_block_requires_text(self):
        document = valid_document()
        block = document["structure_issues_and_suggestions"]["blocks"][0]
        block.pop("text")
        self.assert_schema_invalid(document, "text")

    def test_diagram_block_requires_diagram_object(self):
        document = valid_document()
        block = document["module_design"]["modules"][0]["internal_mechanism"]["mechanism_details"][0]["blocks"][1]
        block.pop("diagram")
        self.assert_schema_invalid(document, "diagram")

    def test_table_block_requires_table_object(self):
        document = valid_document()
        block = document["structure_issues_and_suggestions"]["blocks"][2]
        block.pop("table")
        self.assert_schema_invalid(document, "table")

    def test_content_block_table_rows_reject_support_refs_at_schema_level(self):
        for field_name in ["evidence_refs", "traceability_refs", "source_snippet_refs"]:
            document = valid_document()
            row = document["structure_issues_and_suggestions"]["blocks"][2]["table"]["rows"][0]
            row[field_name] = []
            with self.subTest(field=field_name):
                self.assert_schema_invalid(document, field_name)
```

- [ ] **Step 2: Run schema tests to verify they fail**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_v2_phase3_content_blocks.Phase3SchemaShapeTests -v
```

Expected: FAIL because the schema still treats `structure_issues_and_suggestions` as a string and mechanism details only accept text blocks.

- [ ] **Step 3: Add content-block schema definitions**

In `schemas/structure-design.schema.json`:

1. Replace top-level property:

```json
"structure_issues_and_suggestions": {
  "$ref": "#/$defs/structureIssuesAndSuggestions"
}
```

2. Replace `mechanismDetail.blocks.items` with:

```json
"blocks": {
  "type": "array",
  "items": { "$ref": "#/$defs/contentBlock" }
}
```

3. Add these definitions near the existing `mechanismTextBlock` definition and update references to use the new names:

```json
"contentBlockBase": {
  "type": "object",
  "required": ["block_id", "block_type", "title", "confidence"],
  "properties": {
    "block_id": { "$ref": "#/$defs/nonEmptyString" },
    "block_type": { "type": "string", "enum": ["text", "diagram", "table"] },
    "title": { "$ref": "#/$defs/nonEmptyString" },
    "confidence": { "$ref": "#/$defs/confidence" },
    "evidence_refs": { "$ref": "#/$defs/referenceArray" },
    "traceability_refs": { "$ref": "#/$defs/referenceArray" },
    "source_snippet_refs": { "$ref": "#/$defs/referenceArray" }
  }
},
"textContentBlock": {
  "allOf": [
    { "$ref": "#/$defs/contentBlockBase" },
    {
      "type": "object",
      "required": ["block_type", "text"],
      "additionalProperties": false,
      "properties": {
        "block_id": { "$ref": "#/$defs/nonEmptyString" },
        "block_type": { "const": "text" },
        "title": { "$ref": "#/$defs/nonEmptyString" },
        "text": { "$ref": "#/$defs/nonEmptyString" },
        "confidence": { "$ref": "#/$defs/confidence" },
        "evidence_refs": { "$ref": "#/$defs/referenceArray" },
        "traceability_refs": { "$ref": "#/$defs/referenceArray" },
        "source_snippet_refs": { "$ref": "#/$defs/referenceArray" }
      }
    }
  ]
},
"diagramContentBlock": {
  "allOf": [
    { "$ref": "#/$defs/contentBlockBase" },
    {
      "type": "object",
      "required": ["block_type", "diagram"],
      "additionalProperties": false,
      "properties": {
        "block_id": { "$ref": "#/$defs/nonEmptyString" },
        "block_type": { "const": "diagram" },
        "title": { "$ref": "#/$defs/nonEmptyString" },
        "confidence": { "$ref": "#/$defs/confidence" },
        "evidence_refs": { "$ref": "#/$defs/referenceArray" },
        "traceability_refs": { "$ref": "#/$defs/referenceArray" },
        "source_snippet_refs": { "$ref": "#/$defs/referenceArray" },
        "diagram": { "$ref": "#/$defs/diagram" }
      }
    }
  ]
},
"contentBlockTableColumn": {
  "type": "object",
  "required": ["key", "title"],
  "additionalProperties": false,
  "properties": {
    "key": { "$ref": "#/$defs/nonEmptyString" },
    "title": { "$ref": "#/$defs/nonEmptyString" }
  }
},
"contentBlockTableRow": {
  "type": "object",
  "not": {
    "anyOf": [
      { "required": ["evidence_refs"] },
      { "required": ["traceability_refs"] },
      { "required": ["source_snippet_refs"] }
    ]
  },
  "additionalProperties": true
},
"contentBlockTable": {
  "type": "object",
  "required": ["id", "title", "columns", "rows"],
  "additionalProperties": false,
  "properties": {
    "id": { "$ref": "#/$defs/nonEmptyString" },
    "title": { "$ref": "#/$defs/nonEmptyString" },
    "columns": {
      "type": "array",
      "items": { "$ref": "#/$defs/contentBlockTableColumn" }
    },
    "rows": {
      "type": "array",
      "items": { "$ref": "#/$defs/contentBlockTableRow" }
    }
  }
},
"tableContentBlock": {
  "allOf": [
    { "$ref": "#/$defs/contentBlockBase" },
    {
      "type": "object",
      "required": ["block_type", "table"],
      "additionalProperties": false,
      "properties": {
        "block_id": { "$ref": "#/$defs/nonEmptyString" },
        "block_type": { "const": "table" },
        "title": { "$ref": "#/$defs/nonEmptyString" },
        "confidence": { "$ref": "#/$defs/confidence" },
        "evidence_refs": { "$ref": "#/$defs/referenceArray" },
        "traceability_refs": { "$ref": "#/$defs/referenceArray" },
        "source_snippet_refs": { "$ref": "#/$defs/referenceArray" },
        "table": { "$ref": "#/$defs/contentBlockTable" }
      }
    }
  ]
},
"contentBlock": {
  "oneOf": [
    { "$ref": "#/$defs/textContentBlock" },
    { "$ref": "#/$defs/diagramContentBlock" },
    { "$ref": "#/$defs/tableContentBlock" }
  ]
},
"structureIssuesAndSuggestions": {
  "type": "object",
  "required": ["summary", "blocks", "not_applicable_reason"],
  "additionalProperties": false,
  "properties": {
    "summary": { "type": "string" },
    "blocks": {
      "type": "array",
      "items": { "$ref": "#/$defs/contentBlock" }
    },
    "not_applicable_reason": { "type": "string" }
  }
}
```

Keep the existing `diagram` definition unchanged.

The schema intentionally leaves `columns[]` and `rows[]` without `minItems`; Phase 3 semantic validation owns the non-empty checks so it can report stable, path-specific messages.

- [ ] **Step 4: Run schema tests**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_v2_phase3_content_blocks.Phase3SchemaShapeTests -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tests/test_v2_phase3_content_blocks.py schemas/structure-design.schema.json
git commit -m "feat: add v2 phase 3 content block schema"
```

---

### Task 3: Semantic Validation For Shared Content Blocks

**Files:**
- Create: `scripts/v2_phase3.py`
- Modify: `scripts/validate_dsl.py`
- Modify: `tests/test_v2_phase3_content_blocks.py`

- [ ] **Step 1: Add failing semantic tests**

Append this class to `tests/test_v2_phase3_content_blocks.py`:

```python
class Phase3SemanticValidationTests(unittest.TestCase):
    def assert_invalid(self, mutate, expected):
        document = valid_document()
        mutate(document)
        completed = validation_stderr_for(document)
        self.assertEqual(1, completed.returncode, completed.stderr or completed.stdout)
        self.assertIn(expected, completed.stderr)

    def test_each_content_block_section_requires_at_least_one_text_block_when_blocks_present(self):
        def mutate(document):
            document["structure_issues_and_suggestions"]["blocks"] = [
                document["structure_issues_and_suggestions"]["blocks"][2]
            ]

        self.assert_invalid(mutate, "content block section must include at least one non-empty text block")

    def test_mechanism_detail_still_requires_at_least_one_text_block(self):
        def mutate(document):
            detail = document["module_design"]["modules"][0]["internal_mechanism"]["mechanism_details"][0]
            detail["blocks"] = [detail["blocks"][1], detail["blocks"][2]]

        self.assert_invalid(mutate, "content block section must include at least one non-empty text block")

    def test_block_ids_are_unique_within_parent_section(self):
        def mutate(document):
            blocks = document["structure_issues_and_suggestions"]["blocks"]
            blocks[1]["block_id"] = blocks[0]["block_id"]

        self.assert_invalid(mutate, "duplicate block_id ISSUE-TEXT-001")

    def test_same_block_id_can_recur_in_different_parent_sections(self):
        document = valid_document()
        mechanism_block = document["module_design"]["modules"][0]["internal_mechanism"]["mechanism_details"][0]["blocks"][0]
        issue_block = document["structure_issues_and_suggestions"]["blocks"][0]
        issue_block["block_id"] = mechanism_block["block_id"]
        completed = validation_stderr_for(document)
        self.assertEqual(0, completed.returncode, completed.stderr)

    def test_diagram_block_requires_non_empty_source(self):
        def mutate(document):
            block = document["module_design"]["modules"][0]["internal_mechanism"]["mechanism_details"][0]["blocks"][1]
            block["diagram"]["source"] = ""

        self.assert_invalid(mutate, "diagram.source must be non-empty")

    def test_diagram_block_confidence_must_match_nested_diagram(self):
        def mutate(document):
            block = document["module_design"]["modules"][0]["internal_mechanism"]["mechanism_details"][0]["blocks"][1]
            block["confidence"] = "observed"
            block["diagram"]["confidence"] = "unknown"

        self.assert_invalid(mutate, "diagram block confidence must match diagram.confidence")

    def test_content_block_table_requires_columns_and_rows(self):
        def mutate(document):
            table = document["structure_issues_and_suggestions"]["blocks"][2]["table"]
            table["columns"] = []
            table["rows"] = []

        completed = validation_stderr_for(valid_document())
        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assert_invalid(mutate, "table block must contain at least one column")

    def test_content_block_table_rows_must_use_declared_column_keys(self):
        def mutate(document):
            row = document["structure_issues_and_suggestions"]["blocks"][2]["table"]["rows"][0]
            row["undeclared"] = "bad"

        self.assert_invalid(mutate, "content block table row contains keys outside declared columns")

    def test_content_block_table_column_keys_must_be_unique(self):
        def mutate(document):
            columns = document["structure_issues_and_suggestions"]["blocks"][2]["table"]["columns"]
            columns[1]["key"] = columns[0]["key"]

        self.assert_invalid(mutate, "duplicate content block table column key issue")

    def test_content_block_table_column_keys_must_not_shadow_support_refs(self):
        def mutate(document):
            columns = document["structure_issues_and_suggestions"]["blocks"][2]["table"]["columns"]
            columns[0]["key"] = "evidence_refs"

        self.assert_invalid(mutate, "reserved support metadata key evidence_refs")

    def test_content_block_table_rows_may_use_declared_reference_like_column_names(self):
        document = valid_document()
        table = document["structure_issues_and_suggestions"]["blocks"][2]["table"]
        table["columns"] = [
            {"key": "issue_id", "title": "问题 ID"},
            {"key": "related_module_ids", "title": "关联模块"},
        ]
        table["rows"] = [
            {
                "issue_id": "ISSUE-001",
                "related_module_ids": "MOD-SKILL",
            }
        ]
        completed = validation_stderr_for(document)
        self.assertEqual(0, completed.returncode, completed.stderr)

    def test_chapter_9_not_applicable_reason_is_mutually_exclusive_with_summary_and_blocks(self):
        def mutate(document):
            document["structure_issues_and_suggestions"]["not_applicable_reason"] = "不适用"

        self.assert_invalid(mutate, "cannot provide both content and not_applicable_reason")

    def test_chapter_9_requires_not_applicable_reason_when_summary_and_blocks_are_empty(self):
        def mutate(document):
            issues = document["structure_issues_and_suggestions"]
            issues["summary"] = ""
            issues["blocks"] = []
            issues["not_applicable_reason"] = ""

        self.assert_invalid(mutate, "must provide not_applicable_reason when content is absent")

    def test_content_block_table_ids_participate_in_global_uniqueness(self):
        def mutate(document):
            document["structure_issues_and_suggestions"]["blocks"][2]["table"]["id"] = "TBL-BLOCK-MECHANISM-STAGES"

        self.assert_invalid(mutate, "duplicate ID TBL-BLOCK-MECHANISM-STAGES")

    def test_content_block_diagram_ids_participate_in_global_uniqueness(self):
        def mutate(document):
            document["structure_issues_and_suggestions"]["blocks"][1]["diagram"]["id"] = "MER-BLOCK-MECHANISM-FLOW"

        self.assert_invalid(mutate, "duplicate ID MER-BLOCK-MECHANISM-FLOW")

    def test_block_support_refs_are_resolved_by_global_support_ref_validation(self):
        def mutate(document):
            document["structure_issues_and_suggestions"]["blocks"][0]["evidence_refs"] = ["EV-MISSING"]

        self.assert_invalid(mutate, "references unknown evidence ID EV-MISSING")
```

- [ ] **Step 2: Run semantic tests to verify they fail**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_v2_phase3_content_blocks.Phase3SemanticValidationTests -v
```

Expected: FAIL because there is no Phase 3 semantic helper and content-block table IDs are not registered globally.

- [ ] **Step 3: Create the Phase 3 semantic helper**

Create `scripts/v2_phase3.py`:

```python
try:
    from v2_foundation import RuleViolation, has_reason
except ModuleNotFoundError:
    from scripts.v2_foundation import RuleViolation, has_reason


SUPPORT_REF_FIELDS = ("evidence_refs", "traceability_refs", "source_snippet_refs")


def _non_empty(value):
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, list):
        return len(value) > 0
    return value is not None


def _duplicate_values(values):
    seen = set()
    duplicates = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    return duplicates


def iter_content_block_sections(document):
    modules = document.get("module_design", {}).get("modules", [])
    if isinstance(modules, list):
        for module_index, module in enumerate(modules):
            if not isinstance(module, dict):
                continue
            details = module.get("internal_mechanism", {}).get("mechanism_details", [])
            if not isinstance(details, list):
                continue
            for detail_index, detail in enumerate(details):
                if not isinstance(detail, dict):
                    continue
                yield (
                    "$.module_design.modules"
                    f"[{module_index}].internal_mechanism.mechanism_details[{detail_index}].blocks",
                    detail.get("blocks", []),
                    None,
                )

    structure_issues = document.get("structure_issues_and_suggestions")
    if isinstance(structure_issues, dict):
        yield (
            "$.structure_issues_and_suggestions.blocks",
            structure_issues.get("blocks", []),
            structure_issues.get("not_applicable_reason"),
        )


def phase3_content_block_violations(document):
    violations = []
    if not isinstance(document, dict):
        return violations

    for section_path, blocks, not_applicable_reason in iter_content_block_sections(document):
        if not isinstance(blocks, list):
            continue
        if not blocks:
            continue
        if has_reason(not_applicable_reason):
            continue
        block_ids = [block.get("block_id") for block in blocks if isinstance(block, dict)]
        for duplicate in _duplicate_values(block_ids):
            violations.append(RuleViolation(section_path, f"duplicate block_id {duplicate}"))
        if not any(_is_non_empty_text_block(block) for block in blocks):
            violations.append(
                RuleViolation(
                    section_path,
                    "content block section must include at least one non-empty text block",
                )
            )
        for block_index, block in enumerate(blocks):
            if isinstance(block, dict):
                violations.extend(_block_violations(block, f"{section_path}[{block_index}]"))
    return violations


def _is_non_empty_text_block(block):
    return (
        isinstance(block, dict)
        and block.get("block_type") == "text"
        and _non_empty(block.get("text"))
    )


def _block_violations(block, base):
    block_type = block.get("block_type")
    if block_type == "text":
        if not _non_empty(block.get("text")):
            return [RuleViolation(f"{base}.text", "text block text must be non-empty")]
        return []
    if block_type == "diagram":
        return _diagram_block_violations(block, base)
    if block_type == "table":
        return _table_block_violations(block, base)
    return []


def _diagram_block_violations(block, base):
    violations = []
    diagram = block.get("diagram")
    if not isinstance(diagram, dict):
        return [RuleViolation(f"{base}.diagram", "diagram block must provide diagram")]
    if not _non_empty(diagram.get("source")):
        violations.append(RuleViolation(f"{base}.diagram.source", "diagram.source must be non-empty"))
    if block.get("confidence") != diagram.get("confidence"):
        violations.append(
            RuleViolation(
                f"{base}.diagram.confidence",
                "diagram block confidence must match diagram.confidence",
            )
        )
    return violations


def _table_block_violations(block, base):
    violations = []
    table = block.get("table")
    if not isinstance(table, dict):
        return [RuleViolation(f"{base}.table", "table block must provide table")]
    columns = table.get("columns", [])
    rows = table.get("rows", [])
    if not columns:
        violations.append(RuleViolation(f"{base}.table.columns", "table block must contain at least one column"))
    if not rows:
        violations.append(RuleViolation(f"{base}.table.rows", "table block must contain at least one row"))
    column_keys = [column.get("key") for column in columns if isinstance(column, dict)]
    for column_index, key in enumerate(column_keys):
        if key in SUPPORT_REF_FIELDS:
            violations.append(
                RuleViolation(
                    f"{base}.table.columns[{column_index}].key",
                    f"reserved support metadata key {key}",
                )
            )
    for duplicate in _duplicate_values(column_keys):
        violations.append(RuleViolation(f"{base}.table.columns", f"duplicate content block table column key {duplicate}"))
    allowed_keys = set(column_keys)
    for row_index, row in enumerate(rows):
        if not isinstance(row, dict):
            continue
        support_keys = set(row).intersection(SUPPORT_REF_FIELDS)
        if support_keys:
            violations.append(
                RuleViolation(
                    f"{base}.table.rows[{row_index}]",
                    "content block table rows must not carry support refs",
                )
            )
        unknown_keys = set(row) - allowed_keys
        if unknown_keys:
            violations.append(
                RuleViolation(
                    f"{base}.table.rows[{row_index}]",
                    "content block table row contains keys outside declared columns",
                )
            )
    return violations
```

Do not duplicate the Chapter 9 `summary`/`blocks`/`not_applicable_reason` mutual exclusion check here. `scripts/v2_foundation.py` already owns that gate for the Phase 3 object shape, so Phase 3 only adds block-specific rules.

- [ ] **Step 4: Wire Phase 3 into `scripts/validate_dsl.py`**

Modify the import block near the Phase 2 import:

```python
try:
    from v2_phase3 import phase3_content_block_violations
except ModuleNotFoundError:
    from scripts.v2_phase3 import phase3_content_block_violations
```

Add `check_v2_phase3_content_blocks` after `check_v2_phase2_module_model`:

```python
def check_v2_phase3_content_blocks(document, report):
    for violation in phase3_content_block_violations(document):
        report.error(violation.path, violation.message)
```

Call it in `run_semantic_checks` immediately after Phase 2:

```python
check_v2_phase2_module_model(document, context.report)
check_v2_phase3_content_blocks(document, context.report)
```

Register content-block table IDs globally without changing extra table row semantics:

```python
def is_content_block_table_registration_path(path):
    return re.search(r"\.blocks\[\d+\]\.table$", path) is not None


def is_content_block_table_row_path(path):
    return re.search(r"\.blocks\[\d+\]\.table\.rows\[\d+\]$", path) is not None
```

Update `_register_all_ids` table registration:

```python
elif is_extra_table_object(value) and (
    is_extra_table_registration_path(path) or is_content_block_table_registration_path(path)
):
    self.register("extra_table", value["id"], f"{path}.id")
```

Update `REGISTERED_REFERENCE_PATHS` with:

```python
re.compile(r"^\$\.structure_issues_and_suggestions\.blocks\[\d+\]\.block_id$"),
re.compile(r"^\$.*\.blocks\[\d+\]\.table\.id$"),
```

Treat content-block Mermaid source and diagram type fields as real diagram fields in `real_diagram_field_patterns`:

```python
rf"^\$\.module_design\.modules\[\d+\]\.internal_mechanism\.mechanism_details\[\d+\]\.blocks\[\d+\]\.diagram\.{escaped_field_name}$",
rf"^\$\.structure_issues_and_suggestions\.blocks\[\d+\]\.diagram\.{escaped_field_name}$",
```

Replace the old string-only `check_chapter_9` with an object-aware guard:

```python
def check_chapter_9(document, context):
    value = document["structure_issues_and_suggestions"]
    if isinstance(value, dict):
        return
    context.report.error(
        "$.structure_issues_and_suggestions",
        "structure_issues_and_suggestions must use the V2 Phase 3 object shape",
        "Use summary, blocks, and not_applicable_reason",
    )
```

Markdown safety for `structure_issues_and_suggestions.summary` and text block `text` fields is handled by `check_markdown_safety` as it walks normal string fields.

Update `_check_unregistered_id_fields` so dynamic content-block table row column names do not trigger false "unregistered reference-like field" errors:

```python
def _check_unregistered_id_fields(self, value, path="$"):
    if is_content_block_table_row_path(path):
        return
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if (key.endswith("_id") or key.endswith("_ids")) and not is_registered_reference_field(child_path, key):
                self.report.error(f"{path}.{key}", "unregistered reference-like field", "Add the field to the schema and validator registry before using it")
            self._check_unregistered_id_fields(child, child_path)
    elif isinstance(value, list):
        for i, child in enumerate(value):
            self._check_unregistered_id_fields(child, f"{path}[{i}]")
```

The Phase 3 table declared-key validator remains responsible for rejecting row keys that are not listed in `table.columns[]`.

- [ ] **Step 5: Run semantic tests**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_v2_phase3_content_blocks.Phase3SemanticValidationTests -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add scripts/v2_phase3.py scripts/validate_dsl.py tests/test_v2_phase3_content_blocks.py
git commit -m "feat: validate v2 phase 3 content blocks"
```

---

### Task 4: Shared Content Block Renderer And Chapter 9 Fixed Order

**Files:**
- Modify: `tests/test_v2_phase3_content_blocks.py`
- Modify: `tests/test_render_markdown.py`
- Modify: `scripts/render_markdown.py`

- [ ] **Step 1: Add failing renderer tests**

Append this class to `tests/test_v2_phase3_content_blocks.py`:

```python
class Phase3RenderingTests(unittest.TestCase):
    def markdown(self, document=None, evidence_mode="hidden"):
        renderer = load_renderer_module()
        return renderer.render_markdown(document or valid_document(), evidence_mode=evidence_mode)

    def test_hidden_mode_suppresses_block_support_refs(self):
        document = valid_document()
        document["evidence"] = [
            {
                "id": "EV-BLOCK",
                "kind": "source",
                "title": "块证据",
                "location": "tests/fixtures/valid-v2-foundation.dsl.json",
                "description": "块级证据",
                "confidence": "observed"
            }
        ]
        document["structure_issues_and_suggestions"]["blocks"][0]["evidence_refs"] = ["EV-BLOCK"]
        markdown = self.markdown(document, evidence_mode="hidden")
        self.assertNotIn("支持数据", markdown)
        self.assertNotIn("EV-BLOCK", markdown)

    def test_inline_mode_renders_block_support_after_block(self):
        document = valid_document()
        document["evidence"] = [
            {
                "id": "EV-BLOCK",
                "kind": "source",
                "title": "块证据",
                "location": "tests/fixtures/valid-v2-foundation.dsl.json",
                "description": "块级证据",
                "confidence": "observed"
            }
        ]
        document["structure_issues_and_suggestions"]["blocks"][0]["evidence_refs"] = ["EV-BLOCK"]
        markdown = self.markdown(document, evidence_mode="inline")
        block_position = markdown.index("上游内容完整性")
        support_position = markdown.index("支持数据（上游内容完整性）")
        self.assertLess(block_position, support_position)
        self.assertIn("依据：EV-BLOCK", markdown)

    def test_table_block_heading_uses_block_title_not_table_title(self):
        document = valid_document()
        block = document["structure_issues_and_suggestions"]["blocks"][2]
        block["title"] = "可见表标题"
        block["table"]["title"] = "内部表元数据标题"
        markdown = self.markdown(document)
        self.assertIn("#### 可见表标题", markdown)
        self.assertNotIn("#### 内部表元数据标题", markdown)

    def test_chapter_9_diagram_block_renders_under_structure_issues(self):
        markdown = self.markdown()
        section = markdown[markdown.index("### 9.4 结构问题与改进建议") :]
        self.assertIn("#### 结构问题关系图", section)
        self.assertIn("```mermaid\nflowchart TD", section)

    def test_chapter_4_diagram_block_uses_block_title_without_breaking_heading_hierarchy(self):
        document = valid_document()
        block = document["module_design"]["modules"][0]["internal_mechanism"]["mechanism_details"][0]["blocks"][1]
        block["title"] = "可见图标题"
        block["diagram"]["title"] = "内部图元数据标题"
        markdown = self.markdown(document)
        self.assertIn("**可见图标题**", markdown)
        self.assertIn("内部图元数据标题", markdown)

    def test_chapter_9_summary_renders_before_blocks(self):
        markdown = self.markdown()
        summary_position = markdown.index("结构问题概览")
        block_position = markdown.index("上游内容完整性")
        self.assertLess(summary_position, block_position)

    def test_chapter_9_empty_structure_issues_reason_renders_under_9_4(self):
        document = valid_document()
        issues = document["structure_issues_and_suggestions"]
        issues["summary"] = ""
        issues["blocks"] = []
        issues["not_applicable_reason"] = "未识别到结构问题。"
        markdown = self.markdown(document)
        section_position = markdown.index("### 9.4 结构问题与改进建议")
        reason_position = markdown.index("未识别到结构问题。")
        self.assertLess(section_position, reason_position)
```

In `tests/test_render_markdown.py`, replace `test_chapter_9_object_shape_fails_until_v2_rendering_is_supported` with a test that asserts object shape renders:

```python
def test_chapter_9_structure_issues_object_renders_summary_and_blocks(self):
    module = load_renderer_module()
    document = valid_document()
    markdown = module.render_markdown(document)
    self.assertIn("### 9.4 结构问题与改进建议", markdown)
    self.assertIn("结构问题概览", markdown)
    self.assertIn("上游内容完整性", markdown)
```

Replace `test_chapter_9_empty_state_appears_only_when_all_sources_are_empty` with:

```python
def test_chapter_9_empty_structure_issues_reason_renders_when_all_sources_are_empty(self):
    module = load_renderer_module()
    document = valid_document()
    document["risks"] = []
    document["assumptions"] = []
    issues = document["structure_issues_and_suggestions"]
    issues["summary"] = ""
    issues["blocks"] = []
    issues["not_applicable_reason"] = "未识别到结构问题。"
    markdown = module.render_markdown(document)
    section = markdown[markdown.index("## 9. 结构问题与改进建议") :]
    self.assertIn("### 9.1 风险清单", section)
    self.assertIn("无风险清单。", section)
    self.assertIn("### 9.2 假设清单", section)
    self.assertIn("无假设清单。", section)
    self.assertIn("### 9.4 结构问题与改进建议", section)
    self.assertIn("未识别到结构问题。", section)
```

Replace `test_free_form_chapter_9_text_is_escaped_and_cannot_create_headings` with an object-shape escaping test:

```python
def test_chapter_9_summary_and_text_blocks_are_escaped(self):
    module = load_renderer_module()
    document = valid_document()
    document["structure_issues_and_suggestions"]["summary"] = "# 伪造标题"
    document["structure_issues_and_suggestions"]["blocks"][0]["text"] = "<script>alert(1)</script>"
    markdown = module.render_markdown(document)
    section = markdown[markdown.index("### 9.4 结构问题与改进建议") :]
    self.assertNotIn("\n# 伪造标题", section)
    self.assertIn("\\# 伪造标题", section)
    self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", section)
```

- [ ] **Step 2: Run renderer tests to verify they fail**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_v2_phase3_content_blocks.Phase3RenderingTests tests.test_render_markdown.ChapterNineRenderingTests -v
```

Expected: FAIL because `render_chapter_9` still rejects object shape and Chapter 4 only renders text blocks.

- [ ] **Step 3: Add shared renderer helpers**

In `scripts/render_markdown.py`, add these helpers near `render_extra_diagram`:

```python
def render_content_block_table(table):
    columns = [(column.get("key", ""), column.get("title", "")) for column in table.get("columns", [])]
    return render_fixed_table(table.get("rows", []), columns)


def render_content_block(block, support_context, title_style="heading4"):
    title = escape_heading_label(block.get("title", ""))
    if title_style == "bold":
        heading = f"**{title}**"
    else:
        heading = f"#### {title}"
    block_type = block.get("block_type")
    if block_type == "text":
        body = render_paragraph(block.get("text", ""))
    elif block_type == "diagram":
        body = render_mermaid_block(block.get("diagram", {}))
    elif block_type == "table":
        body = render_content_block_table(block.get("table", {}))
    else:
        raise RenderError(f"unsupported content block type: {block_type}")

    rendered = "\n\n".join(part for part in [heading, body] if part)
    support = render_node_support(block, support_context)
    if support:
        rendered = f"{rendered}\n\n支持数据（{title}）\n\n{support}"
    return rendered


def render_content_blocks(blocks, support_context, title_style="heading4"):
    return "\n\n".join(
        render_content_block(block, support_context, title_style=title_style)
        for block in blocks or []
    )
```

Update `render_internal_mechanism` to replace the existing per-text-block rendering with:

```python
for detail_number, row in enumerate(index_rows, start=1):
    detail = detail_by_id.get(row.get("mechanism_id"), {})
    parts.append(
        f"###### 4.{chapter_index}.6.{detail_number} {escape_heading_label(row.get('mechanism_name', ''))}"
    )
    rendered_blocks = render_content_blocks(detail.get("blocks", []), support_context, title_style="bold")
    if rendered_blocks:
        parts.append(rendered_blocks)
```

Stop calling the old `render_mechanism_text_block` helper after the shared helper is in place. If cleanup of unused code is desired, do it as a normal patch edit and do not run any file deletion command.

Replace `render_chapter_9` with:

```python
def render_chapter_9(document, support_context):
    risks = document.get("risks", [])
    assumptions = document.get("assumptions", [])
    low_confidence_items = collect_low_confidence_items(document)
    structure_issues = document.get("structure_issues_and_suggestions", {})

    parts = [
        chapter_heading(9, "结构问题与改进建议"),
        "### 9.1 风险清单",
    ]

    if risks:
        risk_parts = [render_fixed_table(risks, RISK_COLUMNS)]
        support = render_collection_support(
            risks,
            support_context,
            id_key="id",
            label_key="description",
            target_type="risk",
        )
        if support:
            risk_parts.append(support)
        parts.append("\n\n".join(risk_parts))
    else:
        parts.append("无风险清单。")

    parts.append("### 9.2 假设清单")
    if assumptions:
        assumption_parts = [render_fixed_table(assumptions, ASSUMPTION_COLUMNS)]
        support = render_collection_support(
            assumptions,
            support_context,
            id_key="id",
            label_key="description",
            target_type="assumption",
        )
        if support:
            assumption_parts.append(support)
        parts.append("\n\n".join(assumption_parts))
    else:
        parts.append("无假设清单。")

    parts.append("### 9.3 低置信度项目")
    if low_confidence_items:
        parts.append(render_fixed_table(low_confidence_items, LOW_CONFIDENCE_COLUMNS))
    else:
        parts.append("无低置信度项目。")

    parts.append("### 9.4 结构问题与改进建议")
    if isinstance(structure_issues, dict):
        summary = render_paragraph(structure_issues.get("summary", ""))
        if summary:
            parts.append(summary)
        rendered_blocks = render_content_blocks(structure_issues.get("blocks", []), support_context)
        if rendered_blocks:
            parts.append(rendered_blocks)
        if not summary and not rendered_blocks:
            parts.append(render_paragraph(structure_issues.get("not_applicable_reason", ""), empty_text="未识别到明确的结构问题与改进建议。"))
    else:
        raise RenderError("structure_issues_and_suggestions must use the V2 Phase 3 object shape")

    return "\n\n".join(part for part in parts if part != "")
```

- [ ] **Step 4: Run renderer tests**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_v2_phase3_content_blocks.Phase3RenderingTests tests.test_render_markdown.ChapterNineRenderingTests tests.test_render_markdown.ChapterOneToFourRenderingTests -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/render_markdown.py tests/test_v2_phase3_content_blocks.py tests/test_render_markdown.py
git commit -m "feat: render v2 phase 3 content blocks"
```

---

### Task 5: Migrate Existing Tests, Examples, And Documentation

**Files:**
- Modify: `tests/test_v2_phase2_module_model.py`
- Modify: `tests/test_validate_dsl.py`
- Modify: `tests/test_validate_dsl_semantics.py`
- Modify: `tests/test_phase7_e2e.py`
- Modify: `tests/test_validate_mermaid.py`
- Modify: `examples/minimal-from-code.dsl.json`
- Modify: `examples/minimal-from-requirements.dsl.json`
- Modify: `references/dsl-spec.md`
- Modify: `references/document-structure.md`
- Modify: `references/review-checklist.md`
- Modify: `SKILL.md`

- [ ] **Step 1: Run broader tests to expose migration failures**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_v2_phase2_module_model tests.test_validate_dsl tests.test_validate_dsl_semantics tests.test_render_markdown tests.test_phase7_e2e tests.test_validate_mermaid -v
```

Expected: FAIL in tests that still assume Chapter 9 is a string, Chapter 4 blocks are text-only, or docs/examples describe the Phase 2 DSL shape.

- [ ] **Step 2: Update examples to Phase 3 Chapter 9 object shape**

In both `examples/minimal-from-code.dsl.json` and `examples/minimal-from-requirements.dsl.json`, replace the top-level string with an object using this shape:

```json
"structure_issues_and_suggestions": {
  "summary": "当前结构内容由上游准备，create-structure-md 负责校验并渲染为 Markdown。",
  "blocks": [
    {
      "block_id": "ISSUE-TEXT-001",
      "block_type": "text",
      "title": "输入完整性依赖",
      "text": "如果 DSL 缺少某个模块、流程或依赖信息，渲染器不会从仓库源码中推理补齐。",
      "confidence": "observed",
      "evidence_refs": [],
      "traceability_refs": [],
      "source_snippet_refs": []
    }
  ],
  "not_applicable_reason": ""
}
```

Use the existing wording in each example where it is more specific, but keep the same object keys and at least one text block.

- [ ] **Step 3: Update semantic tests for Chapter 9 Markdown safety**

In `tests/test_validate_dsl_semantics.py`, replace tests that mutate `document["structure_issues_and_suggestions"]` as a raw string. The new unsafe Markdown test should mutate the summary and text block separately:

```python
def test_chapter_nine_summary_and_text_blocks_reject_markdown_structure(self):
    cases = [
        ("summary", lambda document, value: document["structure_issues_and_suggestions"].__setitem__("summary", value)),
        (
            "text",
            lambda document, value: document["structure_issues_and_suggestions"]["blocks"][0].__setitem__("text", value),
        ),
    ]
    for label, apply_value in cases:
        with self.subTest(label=label):
            with tempfile.TemporaryDirectory() as tmpdir:
                document = valid_document()
                apply_value(document, "# 伪造标题")
                path = write_json(tmpdir, f"unsafe-chapter9-{label}.dsl.json", document)
                completed = run_validator(path)
            self.assertEqual(1, completed.returncode)
            self.assertIn("unsafe Markdown structure is not allowed", completed.stderr)
```

Keep the "reports once" assertion by checking that a single unsafe value in one field produces one error for that field.

- [ ] **Step 4: Update renderer tests for Chapter 9**

In `tests/test_render_markdown.py`, ensure `ChapterNineRenderingTests` expects:

```python
self.assertIn("### 9.1 风险清单", markdown)
self.assertIn("### 9.2 假设清单", markdown)
self.assertIn("### 9.3 低置信度项目", markdown)
self.assertIn("### 9.4 结构问题与改进建议", markdown)
```

Replace assertions that require these old unnumbered headings:

```python
"### 风险"
"### 假设"
"### 低置信度项"
```

- [ ] **Step 5: Update references and skill documentation**

Update `references/dsl-spec.md` to include:

```markdown
## Reusable Content Blocks

V2 Phase 3 content block sections use `blocks[]` with `block_type` values `text`, `diagram`, and `table`.
Each non-empty content-block section must include at least one text block. Block-level `evidence_refs`,
`traceability_refs`, and `source_snippet_refs` are valid metadata and are hidden by default in rendered Markdown.

Content-block tables attach support data to the block as a whole. Their rows must use declared column keys only and
must not include `evidence_refs`, `traceability_refs`, or `source_snippet_refs`.
```

Update `references/document-structure.md` to include:

```markdown
## Chapter 9 Order

Chapter 9 renders in this fixed order:

1. `9.1 风险清单`
2. `9.2 假设清单`
3. `9.3 低置信度项目`
4. `9.4 结构问题与改进建议`

Section 9.4 renders `structure_issues_and_suggestions.summary` before the shared content blocks.
```

Update `references/review-checklist.md` to include:

```markdown
- Confirm Chapter 4 mechanism details and Chapter 9 structure issues use the same content-block behavior.
- Confirm every non-empty content-block section includes at least one text block.
- Confirm content-block table rows do not carry support refs.
- Confirm Chapter 9 renders risks, assumptions, low-confidence items, then structure issues.
```

Update `SKILL.md` so the input-readiness checklist says `structure_issues_and_suggestions` is a Phase 3 object with `summary`, `blocks`, and `not_applicable_reason`, not a free-form Markdown string.

- [ ] **Step 6: Run migrated test group**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_v2_phase2_module_model tests.test_validate_dsl tests.test_validate_dsl_semantics tests.test_render_markdown tests.test_phase7_e2e tests.test_validate_mermaid -v
```

Expected: PASS except strict Mermaid tests may still fail in this sandbox with Puppeteer/Chromium launch errors. If only those failures remain, record the exact failure in the implementation handoff and run the non-strict targeted commands.

- [ ] **Step 7: Commit**

```bash
git add tests/test_v2_phase2_module_model.py tests/test_validate_dsl.py tests/test_validate_dsl_semantics.py tests/test_phase7_e2e.py tests/test_validate_mermaid.py examples/minimal-from-code.dsl.json examples/minimal-from-requirements.dsl.json references/dsl-spec.md references/document-structure.md references/review-checklist.md SKILL.md
git commit -m "docs: document v2 phase 3 content blocks"
```

---

### Task 6: Final Regression, Static Rendering, And Boundary Guards

**Files:**
- Verify only: all changed files
- Verify only: `scripts/validate_mermaid.py`
- Verify only: `references/mermaid-rules.md`
- Verify only: `requirements.txt`

- [ ] **Step 1: Run Phase 3 targeted tests**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_v2_phase3_content_blocks -v
```

Expected: PASS.

- [ ] **Step 2: Run schema, validator, and renderer tests**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_validate_dsl tests.test_validate_dsl_semantics tests.test_render_markdown tests.test_v2_phase2_module_model -v
```

Expected: PASS.

- [ ] **Step 3: Validate examples**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python scripts/validate_dsl.py examples/minimal-from-code.dsl.json
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python scripts/validate_dsl.py examples/minimal-from-requirements.dsl.json
```

Expected: both commands print `Validation succeeded`.

- [ ] **Step 4: Render examples into temporary output directories**

Run:

```bash
CODE_DIR="$(mktemp -d /tmp/create-structure-md-phase3-code.XXXXXX)"
REQ_DIR="$(mktemp -d /tmp/create-structure-md-phase3-requirements.XXXXXX)"
printf '%s\n' "$CODE_DIR" > /tmp/create-structure-md-phase3-code-dir.txt
printf '%s\n' "$REQ_DIR" > /tmp/create-structure-md-phase3-requirements-dir.txt
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python scripts/render_markdown.py examples/minimal-from-code.dsl.json --output-dir "$CODE_DIR"
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python scripts/render_markdown.py examples/minimal-from-requirements.dsl.json --output-dir "$REQ_DIR"
```

Expected: both commands write Markdown files and do not report errors. The `mktemp -d` directories make the step repeat-safe without deleting prior outputs.

- [ ] **Step 5: Run Markdown static Mermaid validation on rendered outputs**

Run:

```bash
CODE_DIR="$(cat /tmp/create-structure-md-phase3-code-dir.txt)"
REQ_DIR="$(cat /tmp/create-structure-md-phase3-requirements-dir.txt)"
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python scripts/validate_mermaid.py --from-markdown "$CODE_DIR/create-structure-md_STRUCTURE_DESIGN.md" --static
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python scripts/validate_mermaid.py --from-markdown "$REQ_DIR/requirements-note-example_STRUCTURE_DESIGN.md" --static
```

Expected: both commands pass static validation.

- [ ] **Step 6: Run full suite**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest discover -s tests -v
```

Expected: PASS in an environment where strict Mermaid CLI can launch Chromium. In the current sandbox, known strict Mermaid e2e failures may remain:

```text
Failed to launch the browser process
sandbox_host_linux.cc
Operation not permitted
```

If those are the only failures, record them as environment failures and include the passing targeted commands in the final handoff.

- [ ] **Step 7: Verify Mermaid boundary files are untouched**

Run:

```bash
git diff --exit-code -- scripts/validate_mermaid.py references/mermaid-rules.md
```

Expected: no output and exit code 0.

- [ ] **Step 8: Verify runtime dependencies are unchanged**

Run:

```bash
git diff --exit-code -- requirements.txt
```

Expected: no output and exit code 0.

- [ ] **Step 9: Commit final verification adjustments**

If Task 6 required test/doc fixes, commit them:

```bash
git add tests/test_v2_phase3_content_blocks.py tests/test_v2_phase2_module_model.py tests/test_validate_dsl.py tests/test_validate_dsl_semantics.py tests/test_render_markdown.py tests/test_phase7_e2e.py tests/test_validate_mermaid.py scripts/v2_phase3.py scripts/validate_dsl.py scripts/render_markdown.py schemas/structure-design.schema.json tests/fixtures/valid-v2-foundation.dsl.json examples/minimal-from-code.dsl.json examples/minimal-from-requirements.dsl.json references/dsl-spec.md references/document-structure.md references/review-checklist.md SKILL.md
git commit -m "test: verify v2 phase 3 content blocks"
```

---

## Self-Review

- Spec coverage: The plan covers shared schema, shared semantic helper, shared renderer helper, Chapter 4 mechanism detail blocks, Chapter 9 structure issues object, hidden/inline support behavior, table row restrictions, diagram/table global IDs, Chapter 9 order, examples, docs, and boundary guards.
- Placeholder scan: No placeholder markers or deferred-work language remain. Code steps include concrete snippets and exact commands.
- Type consistency: The plan uses `block_id`, `block_type`, `title`, `confidence`, `evidence_refs`, `traceability_refs`, `source_snippet_refs`, `diagram`, `table`, `summary`, `blocks`, and `not_applicable_reason` consistently across schema, validator, renderer, fixture, and tests.
- Known risk: `contentBlockBase` with `allOf` and closed child schemas is verbose. If implementation prefers simpler closed per-type schemas without the base, keep the resulting accepted/rejected shapes identical to the tests.
