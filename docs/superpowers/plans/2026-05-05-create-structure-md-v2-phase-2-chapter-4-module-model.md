# create-structure-md V2 Phase 2 Chapter 4 Module Model Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the V2 Phase 2 Chapter 4 module model and Section 5.2 runtime-unit cleanup for `dsl_version: "0.2.0"`.

**Architecture:** Keep the V2 boundary from Phase 1: create-structure-md consumes prepared DSL content and does not analyze repositories. This phase replaces the V1 Chapter 4 schema, semantic checks, and renderer with seven fixed module subsections, while Section 5.2 removes V1 runtime-unit reason columns. Phase 2 adds a small `scripts/v2_phase2.py` semantic helper so Chapter 4-specific rules do not bloat the Phase 1 global-rule module.

**Tech Stack:** Python 3, standard-library `unittest`, `jsonschema` Draft 2020-12, existing renderer helpers in `scripts/render_markdown.py`, no new runtime dependencies.

---

## Scope And Constraints

- Do not add repository analysis, requirement inference, Word/PDF/image export, Mermaid gate behavior, or a V1-to-V2 migration tool.
- Do not modify `scripts/validate_mermaid.py` or `references/mermaid-rules.md`.
- Do not run deletion commands. Workspace instruction: when cleanup is needed, give the command to the user instead of executing it.
- Keep `dsl_version` fixed at `0.2.0`; V1 examples remain rejected fixtures only.
- Implement only Phase 2 content-block behavior for internal mechanism details: render `block_type: "text"` blocks in DSL order and require at least one text block per mechanism detail. Phase 3 owns the reusable block model for diagram/table/other shared content blocks.
- Existing tests that currently load `tests/fixtures/valid-v2-foundation.dsl.json` must remain green by converting that fixture to the Phase 2 DSL shape.

Use the project Python for verification:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest discover -s tests -v
```

---

## File Structure

- Create: `scripts/v2_phase2.py`
  - Owns Phase 2 semantic checks for Chapter 4 module model, interface index/detail contracts, dependency target references, typed related anchors, internal mechanism one-to-one checks, observed function/method location warnings, and Section 5.2 runtime-unit rules.
- Modify: `scripts/validate_dsl.py`
  - Imports `v2_phase2.py`, calls Phase 2 semantic checks, updates V1 Chapter 4 ID/reference/low-confidence paths, and revises Chapter 4 and Chapter 5 checks for V2.
- Modify: `scripts/render_markdown.py`
  - Replaces V1 Chapter 4 rendering with seven fixed subsections and updates Section 5.2 visible columns.
- Modify: `schemas/structure-design.schema.json`
  - Replaces V1 module-design definitions with V2 Chapter 4 definitions and removes V1 Section 5.2 runtime-unit reason fields.
- Create: `tests/test_v2_phase2_module_model.py`
  - Covers schema, semantic validation, warning behavior, rendering order, visible/hidden internal fields, and runtime-unit cleanup for Phase 2.
- Modify: `tests/test_validate_dsl.py`
  - Replaces V1 module-shape schema assertions with V2 schema assertions.
- Modify: `tests/test_validate_dsl_semantics.py`
  - Migrates semantic tests away from `external_capability_details`, `internal_structure`, and removed runtime-unit reason fields.
- Modify: `tests/test_render_markdown.py`
  - Migrates renderer tests, low-confidence tests, and expected diagram collection tests to the V2 Chapter 4 model.
- Modify: `tests/test_phase7_e2e.py`
  - Updates example-contract checks so examples are expected to use the V2 Chapter 4 model.
- Modify: `tests/test_validate_mermaid.py`
  - Updates `SKILL.md` text expectations and keeps DSL extractor tests decoupled from the converted V2 fixture. Do not add V2 `public_interfaces.interfaces[].execution_flow_diagram` extraction expectations in Phase 2.
- Modify: `tests/fixtures/valid-v2-foundation.dsl.json`
  - Converts the reusable V2 fixture to the Phase 2 module model.
- Modify: `examples/minimal-from-code.dsl.json`
  - Converts the example to the Phase 2 module model.
- Modify: `examples/minimal-from-requirements.dsl.json`
  - Converts the example to the Phase 2 module model.
- Modify: `references/dsl-spec.md`
  - Documents the V2 Chapter 4 module model, Section 5.2 runtime-unit shape, and internal-field visibility.
- Modify: `references/document-structure.md`
  - Documents the seven Chapter 4 subsections and simplified Section 5.2 table.
- Modify: `references/review-checklist.md`
  - Adds reviewer checks for the Phase 2 model.
- Modify: `SKILL.md`
  - Keeps the skill workflow aligned with the V2 Chapter 4 model and Section 5.2 runtime-unit shape while preserving the no-repository-analysis boundary.
- Verify only: `scripts/v2_foundation.py`
  - Keep global constants and gates unchanged unless a Phase 2 test proves a global hook needs an additional path.
- Verify only: `requirements.txt`
  - Must still contain only `jsonschema`.

---

## Review History

This plan is intentionally review-driven. The main agent revises this section after each adversarial sub-agent pass.

- Round 1: Revised after adversarial review. Fixes added for ID registry/reference paths, the `valid_interface_ids` TypeError in the semantic-helper sketch, migration of existing V1 tests, complete related-anchor coverage, public-interface not-applicable rendering, isolated render output directories, and `SKILL.md` updates.
- Round 2: Revised after adversarial review. Fixes added for the Phase 2 Mermaid-validator boundary, renderer low-confidence/support migration, full schema-definition details, complete anchor enum tests, repeat-safe temporary render directories, and Markdown Mermaid validation for all rendered outputs.
- Round 3: Final review found two blockers; plan now adds executable `prototype` and contract `consumers` non-empty checks, plus an explicit `git diff --exit-code` guard for Mermaid validator/rules files.

---

### Task 1: Phase 2 Test Harness And Canonical Fixture Contract

**Files:**
- Create: `tests/test_v2_phase2_module_model.py`
- Modify: `tests/fixtures/valid-v2-foundation.dsl.json`

- [ ] **Step 1: Write the failing Phase 2 harness**

Create `tests/test_v2_phase2_module_model.py` with these imports, helpers, and the first schema/renderer assertions:

```python
import contextlib
import importlib.util
import io
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


def load_renderer_module():
    spec = importlib.util.spec_from_file_location(
        "render_markdown_phase2_under_test",
        ROOT / "scripts/render_markdown.py",
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_validator_module():
    spec = importlib.util.spec_from_file_location(
        "validate_dsl_phase2_under_test",
        ROOT / "scripts/validate_dsl.py",
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def schema_errors(document):
    schema = load_json(SCHEMA)
    Draft202012Validator.check_schema(schema)
    return sorted(Draft202012Validator(schema).iter_errors(document), key=lambda error: list(error.path))


def validation_stderr_for(document):
    with tempfile.TemporaryDirectory() as tmpdir:
        path = write_json(tmpdir, "case.dsl.json", document)
        completed = run_validator(path)
    return completed.returncode, completed.stderr, completed.stdout


class Phase2FixtureContractTests(unittest.TestCase):
    def test_valid_fixture_matches_phase2_schema_and_semantics(self):
        document = valid_document()
        self.assertEqual([], schema_errors(document))
        completed = run_validator(FIXTURE)
        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertIn("Validation succeeded", completed.stdout)

    def test_chapter_4_renders_seven_fixed_subsections_in_order(self):
        renderer = load_renderer_module()
        markdown = renderer.render_markdown(valid_document())
        headings = [
            "#### 4.1.1 模块定位与源码/产物范围",
            "#### 4.1.2 配置",
            "#### 4.1.3 依赖",
            "#### 4.1.4 数据对象",
            "#### 4.1.5 对外接口",
            "#### 4.1.6 实现机制说明",
            "#### 4.1.7 已知限制",
        ]
        positions = [markdown.index(heading) for heading in headings]
        self.assertEqual(sorted(positions), positions)
        self.assertNotIn("模块职责", markdown)
        self.assertNotIn("对外能力说明", markdown)
        self.assertNotIn("模块内部结构关系图", markdown)

    def test_section_5_2_renders_simplified_columns(self):
        renderer = load_renderer_module()
        markdown = renderer.render_markdown(valid_document())
        self.assertIn("| 运行单元 | 类型 | 入口 | 职责 | 关联模块 | 备注 |", markdown)
        self.assertNotIn("入口不适用原因", markdown)
        self.assertNotIn("外部环境原因", markdown)
```

- [ ] **Step 2: Run the harness to verify it fails**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_v2_phase2_module_model.Phase2FixtureContractTests -v
```

Expected: FAIL because the schema, fixture, and renderer still use the V1 Chapter 4 module shape and V1 Section 5.2 columns.

- [ ] **Step 3: Convert the canonical fixture to the Phase 2 DSL shape**

Modify `tests/fixtures/valid-v2-foundation.dsl.json` so its first `module_design.modules[0]` has this shape:

```json
{
  "module_id": "MOD-SKILL",
  "name": "技能文档生成模块",
  "module_kind": "library",
  "summary": "接收已经准备好的 DSL 内容，执行结构检查并生成文档。",
  "source_scope": {
    "summary": "覆盖 schema、校验脚本、渲染脚本、示例和参考文档组成的文档生成能力。",
    "primary_files": [
      {
        "path": "schemas/structure-design.schema.json",
        "role": "DSL 结构契约",
        "language": "json",
        "notes": ""
      },
      {
        "path": "scripts/validate_dsl.py",
        "role": "DSL 校验入口",
        "language": "python",
        "notes": ""
      },
      {
        "path": "scripts/render_markdown.py",
        "role": "Markdown 渲染入口",
        "language": "python",
        "notes": ""
      }
    ],
    "consumed_inputs": ["结构化设计 DSL JSON"],
    "owned_outputs": ["document.output_file 指定的 Markdown 文件"],
    "out_of_scope": ["不负责仓库分析", "不负责推理缺失设计内容"]
  },
  "configuration": {
    "summary": "模块级配置来自渲染和校验命令行参数。",
    "parameters": {
      "rows": [
        {
          "parameter_id": "MPARAM-SKILL-OUTPUT-DIR",
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
    "summary": "模块依赖 Python、jsonschema 和 prepared DSL 输入。",
    "rows": [
      {
        "dependency_id": "MDEP-SKILL-JSONSCHEMA",
        "name": "jsonschema",
        "dependency_type": "library",
        "usage_relation": "validates_against",
        "target_module_id": "",
        "target_data_id": "",
        "system_dependency_ref": "SYSDEP-JSONSCHEMA",
        "required_for": "执行 Draft 2020-12 JSON Schema 校验。",
        "failure_behavior": "DSL schema 校验无法执行。",
        "confidence": "observed",
        "evidence_refs": []
      }
    ],
    "not_applicable_reason": ""
  },
  "data_objects": {
    "summary": "模块读取 DSL JSON 并写出 Markdown 文件。",
    "rows": [
      {
        "data_id": "DATA-SKILL-DSL",
        "name": "结构设计 DSL",
        "data_type": "json",
        "role": "渲染输入",
        "producer": "Codex 或上游分析 skill",
        "consumer": "validate_dsl.py 和 render_markdown.py",
        "shape_or_contract": "符合 schemas/structure-design.schema.json",
        "confidence": "observed",
        "evidence_refs": []
      }
    ],
    "not_applicable_reason": ""
  },
  "public_interfaces": {
    "summary": "模块暴露校验 CLI、渲染 CLI 和 DSL 契约。",
    "interface_index": {
      "rows": [
        {
          "interface_id": "IFACE-SKILL-VALIDATE-CLI",
          "interface_name": "validate_dsl.py",
          "interface_type": "command_line",
          "description": "校验 DSL JSON 的 schema 和语义规则。"
        },
        {
          "interface_id": "IFACE-SKILL-DSL-CONTRACT",
          "interface_name": "structure-design.schema.json",
          "interface_type": "schema_contract",
          "description": "定义 V2 DSL 的 JSON Schema 契约。"
        }
      ]
    },
    "interfaces": [
      {
        "interface_id": "IFACE-SKILL-DSL-CONTRACT",
        "interface_name": "structure-design.schema.json",
        "interface_type": "schema_contract",
        "purpose": "定义结构设计 DSL 的可接受字段、枚举和对象形状。",
        "location": {
          "file_path": "schemas/structure-design.schema.json",
          "symbol": "",
          "line_start": null,
          "line_end": null
        },
        "contract": {
          "contract_scope": "覆盖 create-structure-md V2 DSL JSON 输入。",
          "contract_location": "schemas/structure-design.schema.json",
          "required_items": ["dsl_version", "document", "module_design"],
          "constraints": ["dsl_version 必须为 0.2.0"],
          "consumers": ["validate_dsl.py", "render_markdown.py"],
          "validation_behavior": "违反契约时 validate_dsl.py 返回非 0。"
        },
        "confidence": "observed",
        "evidence_refs": []
      },
      {
        "interface_id": "IFACE-SKILL-VALIDATE-CLI",
        "interface_name": "validate_dsl.py",
        "interface_type": "command_line",
        "prototype": "python3 scripts/validate_dsl.py structure.dsl.json",
        "purpose": "校验 DSL JSON 的 schema 和语义规则。",
        "location": {
          "file_path": "scripts/validate_dsl.py",
          "symbol": "main",
          "line_start": null,
          "line_end": null
        },
        "parameters": {
          "rows": [
            {
              "parameter_name": "structure.dsl.json",
              "parameter_type": "path",
              "description": "待校验的 DSL JSON 文件路径。",
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
              "description": "0 表示成功，1 表示语义错误，2 表示输入或 schema 错误。",
              "condition": "命令结束时返回。"
            }
          ],
          "not_applicable_reason": ""
        },
        "execution_flow_diagram": {
          "id": "MER-IFACE-SKILL-VALIDATE-CLI",
          "kind": "interface_execution_flow",
          "title": "validate_dsl.py 执行流程",
          "diagram_type": "flowchart",
          "description": "展示 DSL 校验流程。",
          "source": "flowchart TD\n  A[\"Load JSON\"] --> B[\"Require V2\"]\n  B --> C[\"Schema validation\"]\n  C --> D[\"Semantic checks\"]",
          "confidence": "observed"
        },
        "side_effects": ["读取 DSL 文件", "向 stdout 或 stderr 输出校验结果"],
        "error_behavior": [
          {
            "condition": "DSL 文件不存在或 JSON 无效",
            "behavior": "返回 2 并向 stderr 输出错误。"
          }
        ],
        "consumers": ["Codex", "仓库维护者"],
        "confidence": "observed",
        "evidence_refs": []
      }
    ],
    "not_applicable_reason": ""
  },
  "internal_mechanism": {
    "summary": "模块通过 schema 校验、语义检查和渲染函数分层完成文档生成。",
    "mechanism_index": {
      "rows": [
        {
          "mechanism_id": "MECH-SKILL-VALIDATION-PIPELINE",
          "mechanism_name": "DSL 校验管线",
          "purpose": "在渲染前拒绝不符合契约的 DSL 输入。",
          "input": "结构化设计 DSL JSON",
          "processing": "先检查 dsl_version，再执行 JSON Schema 和语义校验。",
          "output": "校验报告或成功结果",
          "structural_significance": "保证渲染器接收稳定的结构输入。",
          "related_anchors": [
            {
              "anchor_type": "interface_id",
              "value": "IFACE-SKILL-VALIDATE-CLI",
              "reason": ""
            },
            {
              "anchor_type": "data_id",
              "value": "DATA-SKILL-DSL",
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
        "mechanism_id": "MECH-SKILL-VALIDATION-PIPELINE",
        "blocks": [
          {
            "block_id": "BLOCK-SKILL-VALIDATION-TEXT",
            "block_type": "text",
            "title": "DSL 校验管线说明",
            "text": "校验入口先拒绝非 0.2.0 DSL，再执行 JSON Schema 检查和语义检查；只有通过校验的 DSL 才进入渲染流程。",
            "confidence": "observed",
            "evidence_refs": [],
            "traceability_refs": [],
            "source_snippet_refs": []
          }
        ]
      }
    ],
    "not_applicable_reason": ""
  },
  "known_limitations": {
    "summary": "模块仍依赖上游提供完整结构内容。",
    "rows": [
      {
        "limitation_id": "LIMIT-SKILL-NO-REPO-ANALYSIS",
        "limitation": "不会从仓库源码自动推理缺失设计内容。",
        "impact": "DSL 内容缺失时输出文档也会缺失相应结构信息。",
        "mitigation_or_next_step": "由上游分析 skill 或人工先准备完整 DSL。",
        "confidence": "observed",
        "evidence_refs": []
      }
    ],
    "not_applicable_reason": ""
  },
  "evidence_refs": [],
  "traceability_refs": [],
  "source_snippet_refs": [],
  "notes": [],
  "confidence": "observed"
}
```

Update `runtime_view.runtime_units.rows[0]` by removing `entrypoint_not_applicable_reason` and `external_environment_reason`; keep:

```json
{
  "unit_id": "RUN-GENERATE",
  "unit_name": "文档生成命令序列",
  "unit_type": "CLI workflow",
  "entrypoint": "python scripts/render_markdown.py",
  "responsibility": "在校验通过后生成 Markdown 文档。",
  "related_module_ids": ["MOD-SKILL"],
  "notes": "",
  "confidence": "observed",
  "evidence_refs": [],
  "traceability_refs": [],
  "source_snippet_refs": []
}
```

- [ ] **Step 4: Run the harness again**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_v2_phase2_module_model.Phase2FixtureContractTests -v
```

Expected: still FAIL because schema, validator, and renderer have not implemented Phase 2 yet. The fixture now represents the target contract for later tasks.

- [ ] **Step 5: Commit**

```bash
git add tests/test_v2_phase2_module_model.py tests/fixtures/valid-v2-foundation.dsl.json
git commit -m "test: define v2 phase 2 module model fixture"
```

---

### Task 2: Schema Shape For Chapter 4 And Section 5.2

**Files:**
- Modify: `tests/test_v2_phase2_module_model.py`
- Modify: `schemas/structure-design.schema.json`

- [ ] **Step 1: Add failing schema-negative tests**

Append this test class to `tests/test_v2_phase2_module_model.py`:

```python
class Phase2SchemaShapeTests(unittest.TestCase):
    def assert_schema_invalid(self, document, path_fragment):
        errors = schema_errors(document)
        self.assertTrue(errors, "Expected schema validation failure")
        rendered = "\n".join(f"{list(error.path)}: {error.message}" for error in errors)
        self.assertIn(path_fragment, rendered)

    def test_v1_chapter_4_fields_are_rejected(self):
        for field_name, value in {
            "responsibilities": ["old"],
            "external_capability_summary": {"description": "old"},
            "external_capability_details": {"provided_capabilities": {"rows": []}, "extra_tables": [], "extra_diagrams": []},
            "internal_structure": {"summary": "old"},
            "extra_tables": [],
            "extra_diagrams": [],
        }.items():
            document = valid_document()
            document["module_design"]["modules"][0][field_name] = value
            with self.subTest(field=field_name):
                self.assert_schema_invalid(document, field_name)

    def test_source_scope_rejects_primary_directories_and_not_applicable_reason(self):
        for field_name in ["primary_directories", "not_applicable_reason"]:
            document = valid_document()
            document["module_design"]["modules"][0]["source_scope"][field_name] = []
            with self.subTest(field=field_name):
                self.assert_schema_invalid(document, field_name)

    def test_contract_interface_rejects_required_fields(self):
        document = valid_document()
        interface = document["module_design"]["modules"][0]["public_interfaces"]["interfaces"][0]
        interface["contract"]["required_fields"] = ["module_id"]
        self.assert_schema_invalid(document, "required_fields")

    def test_related_anchors_reject_bare_strings(self):
        document = valid_document()
        row = document["module_design"]["modules"][0]["internal_mechanism"]["mechanism_index"]["rows"][0]
        row["related_anchors"] = ["IFACE-SKILL-VALIDATE-CLI"]
        self.assert_schema_invalid(document, "related_anchors")

    def test_runtime_unit_rejects_removed_reason_fields(self):
        for field_name in ["entrypoint_not_applicable_reason", "external_environment_reason"]:
            document = valid_document()
            document["runtime_view"]["runtime_units"]["rows"][0][field_name] = "old"
            with self.subTest(field=field_name):
                self.assert_schema_invalid(document, field_name)
```

- [ ] **Step 2: Run schema tests to verify they fail**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_v2_phase2_module_model.Phase2SchemaShapeTests -v
```

Expected: FAIL because the current schema still requires V1 module fields and V1 runtime-unit fields.

- [ ] **Step 3: Replace V1 schema definitions with Phase 2 definitions**

In `schemas/structure-design.schema.json`, replace `$defs.moduleDesignItem` with a V2 object that requires these keys:

```json
[
  "module_id",
  "name",
  "module_kind",
  "summary",
  "source_scope",
  "configuration",
  "dependencies",
  "data_objects",
  "public_interfaces",
  "internal_mechanism",
  "known_limitations",
  "evidence_refs",
  "traceability_refs",
  "source_snippet_refs",
  "notes",
  "confidence"
]
```

The `moduleDesignItem` properties must be:

```json
{
  "module_id": { "$ref": "#/$defs/nonEmptyString" },
  "name": { "$ref": "#/$defs/nonEmptyString" },
  "module_kind": { "$ref": "#/$defs/moduleKind" },
  "module_kind_reason": { "type": "string" },
  "summary": { "$ref": "#/$defs/nonEmptyString" },
  "source_scope": { "$ref": "#/$defs/moduleSourceScope" },
  "configuration": { "$ref": "#/$defs/moduleConfiguration" },
  "dependencies": { "$ref": "#/$defs/moduleDependencies" },
  "data_objects": { "$ref": "#/$defs/moduleDataObjects" },
  "public_interfaces": { "$ref": "#/$defs/publicInterfaces" },
  "internal_mechanism": { "$ref": "#/$defs/internalMechanism" },
  "known_limitations": { "$ref": "#/$defs/knownLimitations" },
  "evidence_refs": { "$ref": "#/$defs/referenceArray" },
  "traceability_refs": { "$ref": "#/$defs/referenceArray" },
  "source_snippet_refs": { "$ref": "#/$defs/referenceArray" },
  "notes": { "$ref": "#/$defs/stringArray" },
  "confidence": { "$ref": "#/$defs/confidence" }
}
```

Add these `$defs` and wire them from `moduleDesignItem`:

```json
"moduleSourceScope": {
  "type": "object",
  "required": ["summary", "primary_files", "consumed_inputs", "owned_outputs", "out_of_scope"],
  "additionalProperties": false,
  "properties": {
    "summary": { "$ref": "#/$defs/nonEmptyString" },
    "primary_files": {
      "type": "array",
      "items": { "$ref": "#/$defs/moduleSourceFile" }
    },
    "consumed_inputs": { "$ref": "#/$defs/stringArray" },
    "owned_outputs": { "$ref": "#/$defs/stringArray" },
    "out_of_scope": { "$ref": "#/$defs/stringArray" }
  }
},
"moduleSourceFile": {
  "type": "object",
  "required": ["path", "role", "language", "notes"],
  "additionalProperties": false,
  "properties": {
    "path": { "$ref": "#/$defs/nonEmptyString" },
    "role": { "$ref": "#/$defs/nonEmptyString" },
    "language": { "type": "string" },
    "notes": { "type": "string" }
  }
},
"moduleConfiguration": {
  "type": "object",
  "required": ["summary", "parameters"],
  "additionalProperties": false,
  "properties": {
    "summary": { "type": "string" },
    "parameters": { "$ref": "#/$defs/moduleParameterTable" }
  }
},
"moduleParameterTable": {
  "type": "object",
  "required": ["rows", "not_applicable_reason"],
  "additionalProperties": false,
  "properties": {
    "rows": { "type": "array", "items": { "$ref": "#/$defs/moduleParameterRow" } },
    "not_applicable_reason": { "type": "string" }
  }
},
"moduleParameterRow": {
  "type": "object",
  "required": ["parameter_id", "prototype", "value_or_default", "value_source", "meaning", "confidence", "evidence_refs"],
  "additionalProperties": false,
  "properties": {
    "parameter_id": { "$ref": "#/$defs/nonEmptyString" },
    "prototype": { "$ref": "#/$defs/nonEmptyString" },
    "value_or_default": { "type": "string" },
    "value_source": { "$ref": "#/$defs/valueSource" },
    "meaning": { "$ref": "#/$defs/nonEmptyString" },
    "confidence": { "$ref": "#/$defs/confidence" },
    "evidence_refs": { "$ref": "#/$defs/referenceArray" }
  }
}
```

Add these exact Phase 2 `$defs` entries. They are intentionally expanded here so the implementer does not have to infer shape details:

```json
"moduleDependencies": {
  "type": "object",
  "required": ["summary", "rows", "not_applicable_reason"],
  "additionalProperties": false,
  "properties": {
    "summary": { "type": "string" },
    "rows": { "type": "array", "items": { "$ref": "#/$defs/moduleDependencyRow" } },
    "not_applicable_reason": { "type": "string" }
  }
},
"moduleDependencyRow": {
  "type": "object",
  "required": ["dependency_id", "name", "dependency_type", "usage_relation", "target_module_id", "target_data_id", "system_dependency_ref", "required_for", "failure_behavior", "confidence", "evidence_refs"],
  "additionalProperties": false,
  "properties": {
    "dependency_id": { "$ref": "#/$defs/nonEmptyString" },
    "name": { "$ref": "#/$defs/nonEmptyString" },
    "dependency_type": { "$ref": "#/$defs/dependencyType" },
    "usage_relation": { "$ref": "#/$defs/usageRelation" },
    "target_module_id": { "type": "string" },
    "target_data_id": { "type": "string" },
    "system_dependency_ref": { "type": "string" },
    "required_for": { "$ref": "#/$defs/nonEmptyString" },
    "failure_behavior": { "$ref": "#/$defs/nonEmptyString" },
    "confidence": { "$ref": "#/$defs/confidence" },
    "evidence_refs": { "$ref": "#/$defs/referenceArray" }
  }
},
"moduleDataObjects": {
  "type": "object",
  "required": ["summary", "rows", "not_applicable_reason"],
  "additionalProperties": false,
  "properties": {
    "summary": { "type": "string" },
    "rows": { "type": "array", "items": { "$ref": "#/$defs/moduleDataObjectRow" } },
    "not_applicable_reason": { "type": "string" }
  }
},
"moduleDataObjectRow": {
  "type": "object",
  "required": ["data_id", "name", "data_type", "role", "producer", "consumer", "shape_or_contract", "confidence", "evidence_refs"],
  "additionalProperties": false,
  "properties": {
    "data_id": { "$ref": "#/$defs/nonEmptyString" },
    "name": { "$ref": "#/$defs/nonEmptyString" },
    "data_type": { "$ref": "#/$defs/nonEmptyString" },
    "role": { "$ref": "#/$defs/nonEmptyString" },
    "producer": { "$ref": "#/$defs/nonEmptyString" },
    "consumer": { "$ref": "#/$defs/nonEmptyString" },
    "shape_or_contract": { "$ref": "#/$defs/nonEmptyString" },
    "confidence": { "$ref": "#/$defs/confidence" },
    "evidence_refs": { "$ref": "#/$defs/referenceArray" }
  }
},
"publicInterfaces": {
  "type": "object",
  "required": ["summary", "interface_index", "interfaces", "not_applicable_reason"],
  "additionalProperties": false,
  "properties": {
    "summary": { "type": "string" },
    "interface_index": { "$ref": "#/$defs/interfaceIndexTable" },
    "interfaces": { "type": "array", "items": { "$ref": "#/$defs/interfaceDetail" } },
    "not_applicable_reason": { "type": "string" }
  }
},
"interfaceIndexTable": {
  "type": "object",
  "required": ["rows"],
  "additionalProperties": false,
  "properties": {
    "rows": { "type": "array", "items": { "$ref": "#/$defs/interfaceIndexRow" } }
  }
},
"interfaceIndexRow": {
  "type": "object",
  "required": ["interface_id", "interface_name", "interface_type", "description"],
  "additionalProperties": false,
  "properties": {
    "interface_id": { "$ref": "#/$defs/nonEmptyString" },
    "interface_name": { "$ref": "#/$defs/nonEmptyString" },
    "interface_type": { "$ref": "#/$defs/interfaceType" },
    "description": { "$ref": "#/$defs/nonEmptyString" }
  }
},
"interfaceDetail": {
  "type": "object",
  "required": ["interface_id", "interface_name", "interface_type", "purpose", "location", "confidence", "evidence_refs"],
  "additionalProperties": false,
  "properties": {
    "interface_id": { "$ref": "#/$defs/nonEmptyString" },
    "interface_name": { "$ref": "#/$defs/nonEmptyString" },
    "interface_type": { "$ref": "#/$defs/interfaceType" },
    "interface_type_reason": { "type": "string" },
    "prototype": { "$ref": "#/$defs/nonEmptyString" },
    "purpose": { "$ref": "#/$defs/nonEmptyString" },
    "location": { "$ref": "#/$defs/interfaceLocation" },
    "parameters": { "$ref": "#/$defs/interfaceParameterTable" },
    "return_values": { "$ref": "#/$defs/interfaceReturnTable" },
    "execution_flow_diagram": { "$ref": "#/$defs/diagram" },
    "side_effects": { "$ref": "#/$defs/stringArray" },
    "error_behavior": { "type": "array", "items": { "$ref": "#/$defs/interfaceErrorBehavior" } },
    "consumers": { "$ref": "#/$defs/stringArray" },
    "contract": { "$ref": "#/$defs/interfaceContract" },
    "confidence": { "$ref": "#/$defs/confidence" },
    "evidence_refs": { "$ref": "#/$defs/referenceArray" }
  },
  "oneOf": [
    {
      "properties": { "interface_type": { "enum": ["command_line", "function", "method", "library_api", "workflow"] } },
      "required": ["prototype", "parameters", "return_values", "execution_flow_diagram", "side_effects", "error_behavior", "consumers"]
    },
    {
      "properties": { "interface_type": { "enum": ["schema_contract", "dsl_contract", "document_contract", "configuration_contract", "data_contract", "test_fixture"] } },
      "required": ["contract"],
      "not": {
        "anyOf": [
          { "required": ["parameters"] },
          { "required": ["return_values"] },
          { "required": ["execution_flow_diagram"] }
        ]
      }
    },
    {
      "properties": { "interface_type": { "const": "other" } },
      "required": ["interface_type_reason"]
    }
  ]
},
"interfaceLocation": {
  "type": "object",
  "required": ["file_path"],
  "additionalProperties": false,
  "properties": {
    "file_path": { "$ref": "#/$defs/nonEmptyString" },
    "symbol": { "type": "string" },
    "line_start": { "type": ["integer", "null"], "minimum": 1 },
    "line_end": { "type": ["integer", "null"], "minimum": 1 }
  }
},
"interfaceParameterTable": {
  "type": "object",
  "required": ["rows", "not_applicable_reason"],
  "additionalProperties": false,
  "properties": {
    "rows": { "type": "array", "items": { "$ref": "#/$defs/interfaceParameterRow" } },
    "not_applicable_reason": { "type": "string" }
  }
},
"interfaceParameterRow": {
  "type": "object",
  "required": ["parameter_name", "parameter_type", "description", "direction"],
  "additionalProperties": false,
  "properties": {
    "parameter_name": { "$ref": "#/$defs/nonEmptyString" },
    "parameter_type": { "$ref": "#/$defs/nonEmptyString" },
    "description": { "$ref": "#/$defs/nonEmptyString" },
    "direction": { "$ref": "#/$defs/nonEmptyString" }
  }
},
"interfaceReturnTable": {
  "type": "object",
  "required": ["rows", "not_applicable_reason"],
  "additionalProperties": false,
  "properties": {
    "rows": { "type": "array", "items": { "$ref": "#/$defs/interfaceReturnRow" } },
    "not_applicable_reason": { "type": "string" }
  }
},
"interfaceReturnRow": {
  "type": "object",
  "required": ["return_name", "return_type", "description", "condition"],
  "additionalProperties": false,
  "properties": {
    "return_name": { "$ref": "#/$defs/nonEmptyString" },
    "return_type": { "$ref": "#/$defs/nonEmptyString" },
    "description": { "$ref": "#/$defs/nonEmptyString" },
    "condition": { "$ref": "#/$defs/nonEmptyString" }
  }
},
"interfaceErrorBehavior": {
  "type": "object",
  "required": ["condition", "behavior"],
  "additionalProperties": false,
  "properties": {
    "condition": { "$ref": "#/$defs/nonEmptyString" },
    "behavior": { "$ref": "#/$defs/nonEmptyString" }
  }
},
"interfaceContract": {
  "type": "object",
  "required": ["contract_scope", "contract_location", "required_items", "consumers", "validation_behavior"],
  "additionalProperties": false,
  "properties": {
    "contract_scope": { "$ref": "#/$defs/nonEmptyString" },
    "contract_location": { "$ref": "#/$defs/nonEmptyString" },
    "required_items": { "$ref": "#/$defs/stringArray" },
    "constraints": { "$ref": "#/$defs/stringArray" },
    "consumers": { "$ref": "#/$defs/stringArray" },
    "validation_behavior": { "$ref": "#/$defs/nonEmptyString" }
  }
},
"internalMechanism": {
  "type": "object",
  "required": ["summary", "mechanism_index", "mechanism_details", "not_applicable_reason"],
  "additionalProperties": false,
  "properties": {
    "summary": { "type": "string" },
    "mechanism_index": { "$ref": "#/$defs/mechanismIndexTable" },
    "mechanism_details": { "type": "array", "items": { "$ref": "#/$defs/mechanismDetail" } },
    "not_applicable_reason": { "type": "string" }
  }
},
"mechanismIndexTable": {
  "type": "object",
  "required": ["rows", "not_applicable_reason"],
  "additionalProperties": false,
  "properties": {
    "rows": { "type": "array", "items": { "$ref": "#/$defs/mechanismIndexRow" } },
    "not_applicable_reason": { "type": "string" }
  }
},
"mechanismIndexRow": {
  "type": "object",
  "required": ["mechanism_id", "mechanism_name", "purpose", "input", "processing", "output", "structural_significance", "related_anchors", "confidence", "evidence_refs", "traceability_refs", "source_snippet_refs"],
  "additionalProperties": false,
  "properties": {
    "mechanism_id": { "$ref": "#/$defs/nonEmptyString" },
    "mechanism_name": { "$ref": "#/$defs/nonEmptyString" },
    "purpose": { "$ref": "#/$defs/nonEmptyString" },
    "input": { "$ref": "#/$defs/nonEmptyString" },
    "processing": { "$ref": "#/$defs/nonEmptyString" },
    "output": { "$ref": "#/$defs/nonEmptyString" },
    "structural_significance": { "$ref": "#/$defs/nonEmptyString" },
    "related_anchors": { "type": "array", "items": { "$ref": "#/$defs/typedRelatedAnchor" } },
    "confidence": { "$ref": "#/$defs/confidence" },
    "evidence_refs": { "$ref": "#/$defs/referenceArray" },
    "traceability_refs": { "$ref": "#/$defs/referenceArray" },
    "source_snippet_refs": { "$ref": "#/$defs/referenceArray" }
  }
},
"typedRelatedAnchor": {
  "type": "object",
  "required": ["anchor_type", "value", "reason"],
  "additionalProperties": false,
  "properties": {
    "anchor_type": { "$ref": "#/$defs/anchorType" },
    "value": { "$ref": "#/$defs/nonEmptyString" },
    "reason": { "type": "string" }
  }
},
"mechanismDetail": {
  "type": "object",
  "required": ["mechanism_id", "blocks"],
  "additionalProperties": false,
  "properties": {
    "mechanism_id": { "$ref": "#/$defs/nonEmptyString" },
    "blocks": { "type": "array", "items": { "$ref": "#/$defs/mechanismTextBlock" } }
  }
},
"mechanismTextBlock": {
  "type": "object",
  "required": ["block_id", "block_type", "title", "text", "confidence", "evidence_refs", "traceability_refs", "source_snippet_refs"],
  "additionalProperties": false,
  "properties": {
    "block_id": { "$ref": "#/$defs/nonEmptyString" },
    "block_type": { "const": "text" },
    "title": { "type": "string" },
    "text": { "$ref": "#/$defs/nonEmptyString" },
    "confidence": { "$ref": "#/$defs/confidence" },
    "evidence_refs": { "$ref": "#/$defs/referenceArray" },
    "traceability_refs": { "$ref": "#/$defs/referenceArray" },
    "source_snippet_refs": { "$ref": "#/$defs/referenceArray" }
  }
},
"knownLimitations": {
  "type": "object",
  "required": ["summary", "rows", "not_applicable_reason"],
  "additionalProperties": false,
  "properties": {
    "summary": { "type": "string" },
    "rows": { "type": "array", "items": { "$ref": "#/$defs/knownLimitationRow" } },
    "not_applicable_reason": { "type": "string" }
  }
},
"knownLimitationRow": {
  "type": "object",
  "required": ["limitation_id", "limitation", "impact", "mitigation_or_next_step", "confidence", "evidence_refs"],
  "additionalProperties": false,
  "properties": {
    "limitation_id": { "$ref": "#/$defs/nonEmptyString" },
    "limitation": { "$ref": "#/$defs/nonEmptyString" },
    "impact": { "$ref": "#/$defs/nonEmptyString" },
    "mitigation_or_next_step": { "$ref": "#/$defs/nonEmptyString" },
    "confidence": { "$ref": "#/$defs/confidence" },
    "evidence_refs": { "$ref": "#/$defs/referenceArray" }
  }
}
```

The schema intentionally does not express every cross-field semantic rule. Keep these in `scripts/v2_phase2.py`: `module_kind: "other"` reason required, not-applicable mutual exclusion, `related_anchors[]` min-size, non-`file_path` anchor resolution, line-range anti-placeholder checks, conditional dependency target refs, and executable/contract interface one-to-one checks.

Change `$defs.runtimeUnitRow` required fields to:

```json
[
  "unit_id",
  "unit_name",
  "unit_type",
  "entrypoint",
  "responsibility",
  "related_module_ids",
  "notes",
  "confidence",
  "evidence_refs",
  "traceability_refs",
  "source_snippet_refs"
]
```

Remove `entrypoint_not_applicable_reason` and `external_environment_reason` from runtime-unit properties.

- [ ] **Step 4: Run Phase 2 schema tests**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_v2_phase2_module_model.Phase2SchemaShapeTests -v
```

Expected: PASS.

- [ ] **Step 5: Run root validator tests to expose semantic/V1 path fallout**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_validate_dsl tests.test_validate_dsl_semantics tests.test_v2_foundation_rules -v
```

Expected: FAIL in semantic checks that still traverse V1 `external_capability_details`, `internal_structure`, or runtime-unit reason fields. Those failures are fixed in Tasks 3 and 4.

- [ ] **Step 6: Commit**

```bash
git add schemas/structure-design.schema.json tests/test_v2_phase2_module_model.py
git commit -m "feat: add v2 phase 2 schema shape"
```

---

### Task 3: Phase 2 Semantic Validation

**Files:**
- Create: `scripts/v2_phase2.py`
- Modify: `scripts/validate_dsl.py`
- Modify: `tests/test_v2_phase2_module_model.py`
- Modify: `tests/test_validate_dsl.py`
- Modify: `tests/test_validate_dsl_semantics.py`

- [ ] **Step 1: Add failing semantic tests for module identity, dependencies, interfaces, mechanisms, anchors, warnings, and runtime units**

Append this test class to `tests/test_v2_phase2_module_model.py`:

```python
class Phase2SemanticValidationTests(unittest.TestCase):
    def assert_invalid(self, mutate, expected):
        document = valid_document()
        mutate(document)
        code, stderr, stdout = validation_stderr_for(document)
        self.assertEqual(1, code, stdout + stderr)
        self.assertIn(expected, stderr)

    def test_module_design_must_match_chapter_3_one_to_one(self):
        self.assert_invalid(
            lambda doc: doc["module_design"]["modules"].append(deepcopy(doc["module_design"]["modules"][0])),
            "must match chapter 3 modules one-to-one",
        )

    def test_source_scope_requires_at_least_one_scope_array_value(self):
        def mutate(doc):
            scope = doc["module_design"]["modules"][0]["source_scope"]
            scope["primary_files"] = []
            scope["consumed_inputs"] = []
            scope["owned_outputs"] = []
        self.assert_invalid(mutate, "source_scope must provide primary_files, consumed_inputs, or owned_outputs")

    def test_unknown_parameter_value_may_omit_default_but_default_source_must_not(self):
        self.assert_invalid(
            lambda doc: doc["module_design"]["modules"][0]["configuration"]["parameters"]["rows"][0].update({"value_source": "default", "value_or_default": ""}),
            "value_or_default must be non-empty unless value_source is unknown",
        )

    def test_internal_module_dependency_target_must_reference_existing_module(self):
        def mutate(doc):
            row = doc["module_design"]["modules"][0]["dependencies"]["rows"][0]
            row.update({"dependency_type": "internal_module", "target_module_id": "MOD-MISSING"})
        self.assert_invalid(mutate, "target_module_id must reference an existing module")

    def test_data_object_dependency_target_must_reference_existing_data_object(self):
        def mutate(doc):
            row = doc["module_design"]["modules"][0]["dependencies"]["rows"][0]
            row.update({"dependency_type": "data_object", "target_data_id": "DATA-MISSING"})
        self.assert_invalid(mutate, "target_data_id must reference an existing data object")

    def test_system_dependency_ref_must_reference_chapter_6_dependency(self):
        self.assert_invalid(
            lambda doc: doc["module_design"]["modules"][0]["dependencies"]["rows"][0].update({"system_dependency_ref": "SYSDEP-MISSING"}),
            "system_dependency_ref must reference a Chapter 6 dependency",
        )

    def test_interface_index_and_details_must_match(self):
        self.assert_invalid(
            lambda doc: doc["module_design"]["modules"][0]["public_interfaces"]["interfaces"].pop(),
            "interface_index rows and interface details must have matching interface_id sets",
        )

    def test_executable_interface_requires_non_empty_mermaid_source(self):
        def mutate(doc):
            iface = doc["module_design"]["modules"][0]["public_interfaces"]["interfaces"][1]
            iface["execution_flow_diagram"]["source"] = ""
        self.assert_invalid(mutate, "execution_flow_diagram.source must be non-empty")

    def test_executable_interface_requires_non_empty_prototype(self):
        self.assert_invalid(
            lambda doc: doc["module_design"]["modules"][0]["public_interfaces"]["interfaces"][1].update({"prototype": ""}),
            "prototype must be non-empty",
        )

    def test_executable_interface_requires_side_effects_and_error_behavior(self):
        for field_name, expected in [
            ("side_effects", "side_effects must contain at least one item"),
            ("error_behavior", "error_behavior must contain at least one item"),
        ]:
            def mutate(doc, field_name=field_name):
                iface = doc["module_design"]["modules"][0]["public_interfaces"]["interfaces"][1]
                iface[field_name] = []
            with self.subTest(field=field_name):
                self.assert_invalid(mutate, expected)

    def test_contract_interface_required_items_and_constraints_are_non_empty_when_present(self):
        for field_name, expected in [
            ("required_items", "contract.required_items must contain at least one item"),
            ("constraints", "contract.constraints must contain at least one item when present"),
        ]:
            def mutate(doc, field_name=field_name):
                iface = doc["module_design"]["modules"][0]["public_interfaces"]["interfaces"][0]
                iface["contract"][field_name] = []
            with self.subTest(field=field_name):
                self.assert_invalid(mutate, expected)

    def test_contract_interface_requires_consumers(self):
        def mutate(doc):
            iface = doc["module_design"]["modules"][0]["public_interfaces"]["interfaces"][0]
            iface["contract"]["consumers"] = []
        self.assert_invalid(mutate, "contract.consumers must contain at least one item")

    def test_observed_function_without_symbol_or_line_range_warns(self):
        document = valid_document()
        iface = document["module_design"]["modules"][0]["public_interfaces"]["interfaces"][1]
        iface["interface_type"] = "function"
        iface["location"]["symbol"] = ""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = write_json(tmpdir, "warn.dsl.json", document)
            completed = run_validator(path)
        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertIn("WARNING", completed.stdout)
        self.assertIn("observed function or method interface should provide symbol or line range", completed.stdout)

    def test_mechanism_index_and_details_must_match(self):
        self.assert_invalid(
            lambda doc: doc["module_design"]["modules"][0]["internal_mechanism"]["mechanism_details"].clear(),
            "mechanism_index rows and mechanism_details must have matching mechanism_id sets",
        )

    def test_duplicate_mechanism_ids_fail_within_module(self):
        def mutate(doc):
            mechanism = doc["module_design"]["modules"][0]["internal_mechanism"]
            mechanism["mechanism_index"]["rows"].append(deepcopy(mechanism["mechanism_index"]["rows"][0]))
            mechanism["mechanism_details"].append(deepcopy(mechanism["mechanism_details"][0]))
        self.assert_invalid(mutate, "duplicate mechanism_id")

    def test_mechanism_index_row_requires_related_anchor(self):
        def mutate(doc):
            row = doc["module_design"]["modules"][0]["internal_mechanism"]["mechanism_index"]["rows"][0]
            row["related_anchors"] = []
        self.assert_invalid(mutate, "related_anchors must contain at least one anchor")

    def test_related_anchor_resolution_covers_all_non_file_id_types(self):
        anchor_cases = [
            ("module_id", "MOD-MISSING"),
            ("interface_id", "IFACE-MISSING"),
            ("data_id", "DATA-MISSING"),
            ("dependency_id", "MDEP-MISSING"),
            ("parameter_id", "MPARAM-MISSING"),
            ("diagram_id", "MER-MISSING"),
            ("table_id", "TBL-MISSING"),
            ("source_snippet_id", "SNIP-MISSING"),
            ("evidence_id", "EV-MISSING"),
            ("traceability_id", "TR-MISSING"),
        ]
        for anchor_type, value in anchor_cases:
            def mutate(doc, anchor_type=anchor_type, value=value):
                anchor = doc["module_design"]["modules"][0]["internal_mechanism"]["mechanism_index"]["rows"][0]["related_anchors"][0]
                anchor.update({"anchor_type": anchor_type, "value": value})
            with self.subTest(anchor_type=anchor_type):
                self.assert_invalid(mutate, "related_anchors value must resolve")

    def test_file_path_anchor_does_not_check_filesystem(self):
        document = valid_document()
        anchor = document["module_design"]["modules"][0]["internal_mechanism"]["mechanism_index"]["rows"][0]["related_anchors"][0]
        anchor.update({"anchor_type": "file_path", "value": "missing/not-real.py", "reason": ""})
        code, stderr, stdout = validation_stderr_for(document)
        self.assertEqual(0, code, stdout + stderr)

    def test_empty_related_anchor_value_fails_schema_validation(self):
        document = valid_document()
        anchor = document["module_design"]["modules"][0]["internal_mechanism"]["mechanism_index"]["rows"][0]["related_anchors"][0]
        anchor["value"] = ""
        errors = schema_errors(document)
        rendered = "\n".join(f"{list(error.path)}: {error.message}" for error in errors)
        self.assertIn("related_anchors", rendered)

    def test_other_related_anchor_requires_reason(self):
        def mutate(doc):
            anchor = doc["module_design"]["modules"][0]["internal_mechanism"]["mechanism_index"]["rows"][0]["related_anchors"][0]
            anchor.update({"anchor_type": "other", "value": "external note", "reason": ""})
        self.assert_invalid(mutate, "reason is required when anchor_type is other")

    def test_runtime_entrypoint_not_applicable_requires_notes(self):
        def mutate(doc):
            unit = doc["runtime_view"]["runtime_units"]["rows"][0]
            unit["entrypoint"] = "不适用"
            unit["notes"] = ""
        self.assert_invalid(mutate, "entrypoint 不适用 requires non-empty notes")

    def test_runtime_entrypoint_inline_reason_is_invalid(self):
        self.assert_invalid(
            lambda doc: doc["runtime_view"]["runtime_units"]["rows"][0].update({"entrypoint": "不适用：由内部调用"}),
            "entrypoint must be exactly 不适用 without inline reason",
        )
```

- [ ] **Step 2: Run semantic tests to verify they fail**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_v2_phase2_module_model.Phase2SemanticValidationTests -v
```

Expected: FAIL because Phase 2 semantic hooks do not exist and `validate_dsl.py` still contains V1 Chapter 4 rules.

- [ ] **Step 3: Create `scripts/v2_phase2.py`**

Create the file with this structure:

```python
from dataclasses import dataclass

try:
    from v2_foundation import ANCHOR_TYPE_VALUES, EXECUTABLE_INTERFACE_TYPES, RuleViolation, as_rows, has_reason
except ModuleNotFoundError:
    from scripts.v2_foundation import ANCHOR_TYPE_VALUES, EXECUTABLE_INTERFACE_TYPES, RuleViolation, as_rows, has_reason


CONTRACT_INTERFACE_TYPES = (
    "schema_contract",
    "dsl_contract",
    "document_contract",
    "configuration_contract",
    "data_contract",
    "test_fixture",
)


@dataclass(frozen=True)
class Phase2Warning:
    path: str
    message: str


def _non_empty(value):
    return isinstance(value, str) and bool(value.strip())


def _module_ids(document):
    rows = as_rows(document.get("architecture_views", {}).get("module_intro"))
    return {row.get("module_id") for row in rows if isinstance(row, dict) and _non_empty(row.get("module_id"))}


def _chapter6_dependency_ids(document):
    rows = as_rows(document.get("configuration_data_dependencies", {}).get("dependencies"))
    return {row.get("dependency_id") for row in rows if isinstance(row, dict) and _non_empty(row.get("dependency_id"))}


def _module_data_ids(document):
    ids = set()
    for module in document.get("module_design", {}).get("modules", []) or []:
        for row in as_rows(module.get("data_objects")):
            if isinstance(row, dict) and _non_empty(row.get("data_id")):
                ids.add(row["data_id"])
    return ids


def _ids_from_collection(document, collection_name):
    return {
        item.get("id")
        for item in document.get(collection_name, []) or []
        if isinstance(item, dict) and _non_empty(item.get("id"))
    }


def _diagram_ids(document):
    ids = set()
    for path, value in _walk(document):
        if isinstance(value, dict) and {"id", "kind", "diagram_type", "source"}.issubset(value):
            ids.add(value["id"])
    return ids


def _table_ids(document):
    ids = set()
    for path, value in _walk(document):
        if isinstance(value, dict) and {"id", "title", "columns", "rows"}.issubset(value):
            ids.add(value["id"])
    return ids


def _walk(value, path="$"):
    yield path, value
    if isinstance(value, dict):
        for key, child in value.items():
            yield from _walk(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _walk(child, f"{path}[{index}]")


def _interface_ids(module):
    public = module.get("public_interfaces", {}) if isinstance(module, dict) else {}
    index_ids = [
        row.get("interface_id")
        for row in as_rows(public.get("interface_index"))
        if isinstance(row, dict) and _non_empty(row.get("interface_id"))
    ]
    detail_ids = [
        interface.get("interface_id")
        for interface in public.get("interfaces", []) or []
        if isinstance(interface, dict) and _non_empty(interface.get("interface_id"))
    ]
    return index_ids, detail_ids


def _mechanism_ids(module):
    mechanism = module.get("internal_mechanism", {}) if isinstance(module, dict) else {}
    index_ids = [
        row.get("mechanism_id")
        for row in as_rows(mechanism.get("mechanism_index"))
        if isinstance(row, dict) and _non_empty(row.get("mechanism_id"))
    ]
    detail_ids = [
        detail.get("mechanism_id")
        for detail in mechanism.get("mechanism_details", []) or []
        if isinstance(detail, dict) and _non_empty(detail.get("mechanism_id"))
    ]
    return index_ids, detail_ids


def phase2_module_model_violations(document):
    violations = []
    module_ids = _module_ids(document)
    system_dependency_ids = _chapter6_dependency_ids(document)
    data_ids = _module_data_ids(document)
    diagram_ids = _diagram_ids(document)
    table_ids = _table_ids(document)
    support_ids = {
        "source_snippet_id": _ids_from_collection(document, "source_snippets"),
        "evidence_id": _ids_from_collection(document, "evidence"),
        "traceability_id": _ids_from_collection(document, "traceability"),
    }
    modules = document.get("module_design", {}).get("modules", []) if isinstance(document, dict) else []

    design_ids = [module.get("module_id") for module in modules if isinstance(module, dict)]
    if set(design_ids) != module_ids or len(design_ids) != len(module_ids):
        violations.append(RuleViolation("$.module_design.modules", "must match chapter 3 modules one-to-one"))

    for module_index, module in enumerate(modules):
        if not isinstance(module, dict):
            continue
        base = f"$.module_design.modules[{module_index}]"
        violations.extend(_source_scope_violations(base, module))
        violations.extend(_configuration_violations(base, module))
        violations.extend(_dependency_violations(base, module, module_ids, data_ids, system_dependency_ids))
        violations.extend(_interface_violations(base, module))
        violations.extend(
            _internal_mechanism_violations(
                base,
                module,
                module_ids,
                data_ids,
                system_dependency_ids,
                diagram_ids,
                table_ids,
                support_ids,
            )
        )
        violations.extend(_runtime_anchor_violations(base, module))
    violations.extend(_runtime_unit_violations(document))
    return violations


def phase2_module_model_warnings(document):
    warnings = []
    modules = document.get("module_design", {}).get("modules", []) if isinstance(document, dict) else []
    for module_index, module in enumerate(modules):
        interfaces = module.get("public_interfaces", {}).get("interfaces", []) if isinstance(module, dict) else []
        for interface_index, interface in enumerate(interfaces):
            if not isinstance(interface, dict):
                continue
            if interface.get("confidence") != "observed" or interface.get("interface_type") not in ("function", "method"):
                continue
            location = interface.get("location", {})
            has_symbol = _non_empty(location.get("symbol"))
            has_range = location.get("line_start") is not None and location.get("line_end") is not None
            if not has_symbol and not has_range:
                warnings.append(
                    Phase2Warning(
                        f"$.module_design.modules[{module_index}].public_interfaces.interfaces[{interface_index}].location",
                        "observed function or method interface should provide symbol or line range",
                    )
                )
    return warnings
```

In the same file, implement the private helpers used above:

```python
def _source_scope_violations(base, module):
    scope = module.get("source_scope", {})
    values = [
        scope.get("primary_files", []),
        scope.get("consumed_inputs", []),
        scope.get("owned_outputs", []),
    ]
    if not any(isinstance(value, list) and len(value) > 0 for value in values):
        return [RuleViolation(f"{base}.source_scope", "source_scope must provide primary_files, consumed_inputs, or owned_outputs")]
    return []


def _configuration_violations(base, module):
    violations = []
    for row_index, row in enumerate(as_rows(module.get("configuration", {}).get("parameters"))):
        if row.get("value_source") != "unknown" and not _non_empty(row.get("value_or_default")):
            violations.append(
                RuleViolation(
                    f"{base}.configuration.parameters.rows[{row_index}].value_or_default",
                    "value_or_default must be non-empty unless value_source is unknown",
                )
            )
    return violations


def _dependency_violations(base, module, module_ids, data_ids, system_dependency_ids):
    violations = []
    for row_index, row in enumerate(as_rows(module.get("dependencies"))):
        row_path = f"{base}.dependencies.rows[{row_index}]"
        if row.get("dependency_type") == "internal_module" and row.get("target_module_id") not in module_ids:
            violations.append(RuleViolation(f"{row_path}.target_module_id", "target_module_id must reference an existing module"))
        if row.get("dependency_type") == "data_object" and row.get("target_data_id") not in data_ids:
            violations.append(RuleViolation(f"{row_path}.target_data_id", "target_data_id must reference an existing data object"))
        system_ref = row.get("system_dependency_ref")
        if _non_empty(system_ref) and system_ref not in system_dependency_ids:
            violations.append(RuleViolation(f"{row_path}.system_dependency_ref", "system_dependency_ref must reference a Chapter 6 dependency"))
        if row.get("dependency_id") == system_ref:
            violations.append(RuleViolation(f"{row_path}.system_dependency_ref", "system_dependency_ref must not reference the same dependency row"))
    return violations


def _interface_violations(base, module):
    violations = []
    index_ids, detail_ids = _interface_ids(module)
    if set(index_ids) != set(detail_ids) or len(index_ids) != len(detail_ids):
        violations.append(RuleViolation(f"{base}.public_interfaces", "interface_index rows and interface details must have matching interface_id sets"))
    detail_by_id = {
        interface.get("interface_id"): interface
        for interface in module.get("public_interfaces", {}).get("interfaces", []) or []
        if isinstance(interface, dict)
    }
    for index_id in index_ids:
        interface = detail_by_id.get(index_id)
        if not interface:
            continue
        interface_path = f"{base}.public_interfaces.interfaces[{detail_ids.index(index_id)}]"
        if interface.get("interface_type") in EXECUTABLE_INTERFACE_TYPES:
            if not _non_empty(interface.get("prototype")):
                violations.append(RuleViolation(f"{interface_path}.prototype", "prototype must be non-empty"))
            diagram = interface.get("execution_flow_diagram", {})
            if not _non_empty(diagram.get("source")):
                violations.append(RuleViolation(f"{interface_path}.execution_flow_diagram.source", "execution_flow_diagram.source must be non-empty"))
            if not interface.get("side_effects"):
                violations.append(RuleViolation(f"{interface_path}.side_effects", "side_effects must contain at least one item"))
            if not interface.get("error_behavior"):
                violations.append(RuleViolation(f"{interface_path}.error_behavior", "error_behavior must contain at least one item"))
        if interface.get("interface_type") in CONTRACT_INTERFACE_TYPES:
            contract = interface.get("contract", {})
            if "required_fields" in contract:
                violations.append(RuleViolation(f"{interface_path}.contract.required_fields", "contract.required_fields is invalid; use required_items"))
            if not contract.get("required_items"):
                violations.append(RuleViolation(f"{interface_path}.contract.required_items", "contract.required_items must contain at least one item"))
            if not contract.get("consumers"):
                violations.append(RuleViolation(f"{interface_path}.contract.consumers", "contract.consumers must contain at least one item"))
            if "constraints" in contract and not contract.get("constraints"):
                violations.append(RuleViolation(f"{interface_path}.contract.constraints", "contract.constraints must contain at least one item when present"))
    return violations


def _internal_mechanism_violations(base, module, module_ids, data_ids, system_dependency_ids, diagram_ids, table_ids, support_ids):
    violations = []
    index_ids, detail_ids = _mechanism_ids(module)
    if set(index_ids) != set(detail_ids) or len(index_ids) != len(detail_ids):
        violations.append(RuleViolation(f"{base}.internal_mechanism", "mechanism_index rows and mechanism_details must have matching mechanism_id sets"))
    if len(index_ids) != len(set(index_ids)):
        violations.append(RuleViolation(f"{base}.internal_mechanism.mechanism_index.rows", "duplicate mechanism_id"))
    for detail_index, detail in enumerate(module.get("internal_mechanism", {}).get("mechanism_details", []) or []):
        blocks = detail.get("blocks", []) if isinstance(detail, dict) else []
        if not any(isinstance(block, dict) and block.get("block_type") == "text" and _non_empty(block.get("text")) for block in blocks):
            violations.append(RuleViolation(f"{base}.internal_mechanism.mechanism_details[{detail_index}].blocks", "mechanism detail must include at least one non-empty text block"))
    interface_index_ids, interface_detail_ids = _interface_ids(module)
    valid_interface_ids = set(interface_index_ids) | set(interface_detail_ids)
    valid_dependency_ids = system_dependency_ids | {
        row.get("dependency_id")
        for row in as_rows(module.get("dependencies"))
        if isinstance(row, dict) and _non_empty(row.get("dependency_id"))
    }
    valid_parameter_ids = {
        row.get("parameter_id")
        for row in as_rows(module.get("configuration", {}).get("parameters"))
        if isinstance(row, dict) and _non_empty(row.get("parameter_id"))
    }
    anchor_targets = {
        "module_id": module_ids,
        "interface_id": valid_interface_ids,
        "data_id": data_ids,
        "dependency_id": valid_dependency_ids,
        "parameter_id": valid_parameter_ids,
        "diagram_id": diagram_ids,
        "table_id": table_ids,
        "source_snippet_id": support_ids["source_snippet_id"],
        "evidence_id": support_ids["evidence_id"],
        "traceability_id": support_ids["traceability_id"],
    }
    for row_index, row in enumerate(as_rows(module.get("internal_mechanism", {}).get("mechanism_index"))):
        if not row.get("related_anchors"):
            violations.append(
                RuleViolation(
                    f"{base}.internal_mechanism.mechanism_index.rows[{row_index}].related_anchors",
                    "related_anchors must contain at least one anchor",
                )
            )
        for anchor_index, anchor in enumerate(row.get("related_anchors", []) or []):
            anchor_path = f"{base}.internal_mechanism.mechanism_index.rows[{row_index}].related_anchors[{anchor_index}]"
            anchor_type = anchor.get("anchor_type")
            value = anchor.get("value")
            if anchor_type == "other" and not _non_empty(anchor.get("reason")):
                violations.append(RuleViolation(f"{anchor_path}.reason", "reason is required when anchor_type is other"))
            if anchor_type in anchor_targets and value not in anchor_targets[anchor_type]:
                violations.append(RuleViolation(f"{anchor_path}.value", "related_anchors value must resolve"))
    return violations


def _runtime_anchor_violations(base, module):
    return []


def _runtime_unit_violations(document):
    violations = []
    rows = as_rows(document.get("runtime_view", {}).get("runtime_units"))
    for row_index, row in enumerate(rows):
        path = f"$.runtime_view.runtime_units.rows[{row_index}]"
        entrypoint = row.get("entrypoint")
        if entrypoint == "不适用" and not _non_empty(row.get("notes")):
            violations.append(RuleViolation(f"{path}.notes", "entrypoint 不适用 requires non-empty notes"))
        if isinstance(entrypoint, str) and entrypoint.startswith("不适用："):
            violations.append(RuleViolation(f"{path}.entrypoint", "entrypoint must be exactly 不适用 without inline reason"))
    return violations
```

- [ ] **Step 4: Wire Phase 2 semantic checks into `validate_dsl.py`**

Add imports near the existing `v2_foundation` import:

```python
try:
    from v2_phase2 import phase2_module_model_violations, phase2_module_model_warnings
except ModuleNotFoundError:
    from scripts.v2_phase2 import phase2_module_model_violations, phase2_module_model_warnings
```

Add this helper:

```python
def check_v2_phase2_module_model(document, report):
    for violation in phase2_module_model_violations(document):
        report.error(violation.path, violation.message)
    for warning in phase2_module_model_warnings(document):
        report.warn(warning.path, warning.message)
```

Call it in `run_semantic_checks()` immediately after `check_v2_global_foundation_rules()`:

```python
def run_semantic_checks(document, context, *, allow_long_snippets):
    check_v2_global_foundation_rules(document, context.report)
    check_v2_phase2_module_model(document, context.report)
    check_chapter_rules(document, context)
    check_extra_tables(document, context)
    check_traceability(document, context)
    check_unreferenced_evidence(document, context)
    check_source_snippets(document, context, allow_long_snippets=allow_long_snippets)
    check_markdown_safety(document, context)
    collect_low_confidence(document, context)
```

- [ ] **Step 5: Replace V1 Chapter 4 and Section 5.2 semantic logic in `validate_dsl.py`**

Change `check_chapter_4()` so it validates V2 required chapter-level basics and leaves detailed Phase 2 contracts to `v2_phase2.py`:

```python
def check_chapter_4(document, context):
    module_ids = [row["module_id"] for row in document["architecture_views"]["module_intro"]["rows"]]
    design_modules = document["module_design"]["modules"]
    design_ids = [item["module_id"] for item in design_modules]
    require_non_empty(context.report, "$.module_design.summary", document["module_design"]["summary"], "chapter 4 summary")
    if sorted(module_ids) != sorted(design_ids) or len(module_ids) != len(design_ids):
        context.report.error("$.module_design.modules", "must match chapter 3 modules one-to-one", "Create exactly one module design entry for each chapter 3 module")
    for i, module in enumerate(design_modules):
        base = f"$.module_design.modules[{i}]"
        context.require_ref("module", module["module_id"], f"{base}.module_id", "module")
        for field_name in ["module_id", "name", "module_kind", "summary"]:
            require_non_empty(context.report, f"{base}.{field_name}", module[field_name], field_name)
        require_non_empty(context.report, f"{base}.source_scope.summary", module["source_scope"]["summary"], "source scope summary")
```

Change `check_chapter_5()` runtime-unit logic:

```python
def check_chapter_5(document, context):
    runtime = document["runtime_view"]
    require_non_empty(context.report, "$.runtime_view.summary", runtime["summary"], "chapter 5 summary")
    units = runtime["runtime_units"]["rows"]
    require_non_empty_list(context.report, "$.runtime_view.runtime_units.rows", units, "runtime units")
    for i, unit in enumerate(units):
        base = f"$.runtime_view.runtime_units.rows[{i}]"
        require_non_empty(context.report, f"{base}.entrypoint", unit["entrypoint"], "entrypoint")
        for ref_i, module_id in enumerate(unit["related_module_ids"]):
            context.require_ref("module", module_id, f"{base}.related_module_ids[{ref_i}]", "module")
    diagram_source_required(context.report, "$.runtime_view.runtime_flow_diagram", runtime["runtime_flow_diagram"], "runtime flow diagram")
    sequence = runtime.get("runtime_sequence_diagram")
    if sequence and not is_blank(sequence.get("source", "")) and not sequence["source"].lstrip().startswith("sequenceDiagram"):
        context.report.error("$.runtime_view.runtime_sequence_diagram.source", "must use sequenceDiagram", "Mermaid syntax remains the responsibility of validate_mermaid.py")
```

- [ ] **Step 6: Update ID/reference registry, diagram safety paths, and low-confidence paths away from V1 Chapter 4**

In `scripts/validate_dsl.py`, remove registration of `external_capability_details.provided_capabilities.rows[]`. Do not add `self.register("parameter", ...)`: `parameter` is not an existing `PREFIX_BY_KIND` or traceability target kind. Phase 2 `parameter_id`, `interface_id`, `data_id`, `mechanism_id`, `limitation_id`, and `block_id` uniqueness is enforced by `v2_foundation.id_scope_violations()` and `v2_phase2.py`, not by the legacy traceability registry.

Append these V2 paths to `REGISTERED_REFERENCE_PATHS` so `_check_unregistered_id_fields()` accepts the new defining-ID and conditional-reference fields:

```python
    re.compile(r"^\$\.module_design\.modules\[\d+\]\.configuration\.parameters\.rows\[\d+\]\.parameter_id$"),
    re.compile(r"^\$\.module_design\.modules\[\d+\]\.dependencies\.rows\[\d+\]\.(dependency_id|target_module_id|target_data_id)$"),
    re.compile(r"^\$\.module_design\.modules\[\d+\]\.data_objects\.rows\[\d+\]\.data_id$"),
    re.compile(r"^\$\.module_design\.modules\[\d+\]\.public_interfaces\.interface_index\.rows\[\d+\]\.interface_id$"),
    re.compile(r"^\$\.module_design\.modules\[\d+\]\.public_interfaces\.interfaces\[\d+\]\.interface_id$"),
    re.compile(r"^\$\.module_design\.modules\[\d+\]\.internal_mechanism\.mechanism_index\.rows\[\d+\]\.mechanism_id$"),
    re.compile(r"^\$\.module_design\.modules\[\d+\]\.internal_mechanism\.mechanism_details\[\d+\]\.mechanism_id$"),
    re.compile(r"^\$\.module_design\.modules\[\d+\]\.internal_mechanism\.mechanism_details\[\d+\]\.blocks\[\d+\]\.block_id$"),
    re.compile(r"^\$\.module_design\.modules\[\d+\]\.known_limitations\.rows\[\d+\]\.limitation_id$"),
```

Add module dependency IDs to the existing dependency registry so global duplicate dependency checks still cover Chapter 4 and Chapter 6:

```python
for m_i, module in enumerate(doc["module_design"]["modules"]):
    for row_i, row in enumerate(module["dependencies"]["rows"]):
        self.register(
            "dependency",
            row["dependency_id"],
            f"$.module_design.modules[{m_i}].dependencies.rows[{row_i}].dependency_id",
        )
```

Do not add `target_module_id` or `target_data_id` to `REFERENCE_FIELD_RULES`; those fields are allowed to be empty unless their `dependency_type` requires them, and `v2_phase2.py` enforces the conditional reference rule.

Update `real_diagram_field_patterns()` by removing V1 Chapter 4 paths and adding the Phase 2 executable interface flow path:

```python
        rf"^\$\.module_design\.modules\[\d+\]\.public_interfaces\.interfaces\[\d+\]\.execution_flow_diagram\.{escaped_field_name}$",
```

Replace the `LOW_CONFIDENCE_COLLECTIONS` entry for V1 provided capabilities with Phase 2 module-level rows:

```python
(
    "$.module_design.modules[{module_index}].public_interfaces.interfaces",
    lambda doc: [
        (module_index, interface_index, interface)
        for module_index, module in enumerate(doc["module_design"]["modules"])
        for interface_index, interface in enumerate(module["public_interfaces"]["interfaces"])
    ],
),
```

- [ ] **Step 7: Migrate existing validator tests away from V1 fields**

Update `tests/test_validate_dsl.py`:

- Replace `test_internal_structure_diagram_rejects_empty_object` with `test_executable_interface_diagram_rejects_empty_object`.
- In that test, mutate:

```python
document["module_design"]["modules"][0]["public_interfaces"]["interfaces"][1]["execution_flow_diagram"] = {}
```

- Assert schema failure at:

```python
expected_path=["module_design", "modules", 0, "public_interfaces", "interfaces", 1, "execution_flow_diagram"]
```

Update `tests/test_validate_dsl_semantics.py`:

- Replace `test_internal_structure_requires_diagram_source_or_text` with a Phase 2 internal-mechanism rule test that clears all text block text:

```python
document = valid_document()
blocks = document["module_design"]["modules"][0]["internal_mechanism"]["mechanism_details"][0]["blocks"]
blocks[0]["text"] = ""
```

Expected stderr contains:

```text
$.module_design.modules[0].internal_mechanism.mechanism_details[0].blocks
mechanism detail must include at least one non-empty text block
```

- Replace the old runtime reason-field semantic test with the two Phase 2 runtime tests already added to `Phase2SemanticValidationTests`: `entrypoint: "不适用"` requires non-empty `notes`, and `entrypoint` beginning with `不适用：` fails.
- Replace any `external_capability_details.provided_capabilities.rows[0]` low-confidence mutation with:

```python
document["module_design"]["modules"][0]["public_interfaces"]["interfaces"][0]["confidence"] = "unknown"
```

Expected low-confidence path:

```text
$.module_design.modules[0].public_interfaces.interfaces[0]
```

- Replace multi-module fixture setup that edits `internal_structure.diagram.id` with edits to the executable interface diagram ID:

```python
second["public_interfaces"]["interfaces"][1]["execution_flow_diagram"]["id"] = "MER-IFACE-SECOND-VALIDATE"
```

- Remove or rewrite any assertion that expects `provided_capability` traceability targets from Chapter 4; Phase 2 removed provided-capability rows as Chapter 4 inputs.

- [ ] **Step 8: Run semantic tests**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_v2_phase2_module_model.Phase2SemanticValidationTests -v
```

Expected: PASS.

- [ ] **Step 9: Run the broader validator suite**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_validate_dsl tests.test_validate_dsl_semantics tests.test_v2_foundation_rules tests.test_v2_phase2_module_model -v
```

Expected: PASS.

- [ ] **Step 10: Commit**

```bash
git add scripts/v2_phase2.py scripts/validate_dsl.py tests/test_v2_phase2_module_model.py tests/test_validate_dsl.py tests/test_validate_dsl_semantics.py
git commit -m "feat: validate v2 phase 2 module model"
```

---

### Task 4: Chapter 4 And Section 5.2 Rendering

**Files:**
- Modify: `tests/test_v2_phase2_module_model.py`
- Modify: `scripts/render_markdown.py`
- Modify: `tests/test_render_markdown.py`

- [ ] **Step 1: Add failing rendering tests for all Phase 2 visible tables and hidden internal fields**

Append this test class to `tests/test_v2_phase2_module_model.py`:

```python
class Phase2RenderingTests(unittest.TestCase):
    def markdown(self, document=None):
        renderer = load_renderer_module()
        return renderer.render_markdown(document or valid_document())

    def test_source_scope_renders_expected_parts(self):
        markdown = self.markdown()
        self.assertIn("| 文件 | 角色 | 语言 | 备注 |", markdown)
        self.assertIn("schemas/structure-design.schema.json", markdown)
        self.assertIn("结构化设计 DSL JSON", markdown)
        self.assertIn("document.output_file 指定的 Markdown 文件", markdown)
        self.assertIn("不负责仓库分析", markdown)

    def test_configuration_dependency_data_and_limit_tables_hide_internal_ids(self):
        markdown = self.markdown()
        self.assertIn("| 原型 | 当前/默认值 | 来源 | 含义 |", markdown)
        self.assertIn("| 名称 | 类型 | 关系 | 用途 | 失败行为 |", markdown)
        self.assertIn("| 名称 | 类型 | 角色 | 生产方 | 消费方 | 结构/契约 |", markdown)
        self.assertIn("| 限制 | 影响 | 缓解/后续 |", markdown)
        self.assertNotIn("MPARAM-SKILL-OUTPUT-DIR", markdown)
        self.assertNotIn("MDEP-SKILL-JSONSCHEMA", markdown)
        self.assertNotIn("DATA-SKILL-DSL", markdown)
        self.assertNotIn("LIMIT-SKILL-NO-REPO-ANALYSIS", markdown)

    def test_public_interface_details_render_in_index_order(self):
        document = valid_document()
        interfaces = document["module_design"]["modules"][0]["public_interfaces"]["interfaces"]
        interfaces.reverse()
        markdown = self.markdown(document)
        first = markdown.index("##### 4.1.5.1 validate_dsl.py")
        second = markdown.index("##### 4.1.5.2 structure-design.schema.json")
        self.assertLess(first, second)
        self.assertIn("```mermaid\nflowchart TD", markdown)
        self.assertIn("契约范围：覆盖 create-structure-md V2 DSL JSON 输入。", markdown)
        self.assertIn("必填项：dsl_version、document、module_design", markdown)

    def test_public_interfaces_not_applicable_reason_renders_when_empty(self):
        document = valid_document()
        public = document["module_design"]["modules"][0]["public_interfaces"]
        public["summary"] = ""
        public["interface_index"]["rows"] = []
        public["interfaces"] = []
        public["not_applicable_reason"] = "该模块不暴露对外接口。"
        markdown = self.markdown(document)
        self.assertIn("该模块不暴露对外接口。", markdown)

    def test_internal_mechanism_details_render_in_index_order_and_hide_anchors(self):
        markdown = self.markdown()
        self.assertIn("| 机制 | 用途 | 输入 | 处理方式 | 输出 | 结构意义 |", markdown)
        self.assertIn("###### 4.1.6.1 DSL 校验管线", markdown)
        self.assertIn("DSL 校验管线说明", markdown)
        self.assertNotIn("IFACE-SKILL-VALIDATE-CLI", markdown)
        self.assertNotIn("DATA-SKILL-DSL", markdown)
```

- [ ] **Step 2: Run rendering tests to verify they fail**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_v2_phase2_module_model.Phase2RenderingTests -v
```

Expected: FAIL because `render_markdown.py` still renders V1 Chapter 4 and old Section 5.2 columns.

- [ ] **Step 3: Update Section 5.2 columns**

In `scripts/render_markdown.py`, replace `RUNTIME_UNIT_COLUMNS` with:

```python
RUNTIME_UNIT_COLUMNS = [
    ("unit_name", "运行单元"),
    ("unit_type", "类型"),
    ("entrypoint", "入口"),
    ("responsibility", "职责"),
    ("related_module_ids", "关联模块"),
    ("notes", "备注"),
]
```

- [ ] **Step 4: Add Chapter 4 table constants**

Add these constants near the existing table column constants:

```python
SOURCE_FILE_COLUMNS = [
    ("path", "文件"),
    ("role", "角色"),
    ("language", "语言"),
    ("notes", "备注"),
]

MODULE_PARAMETER_COLUMNS = [
    ("prototype", "原型"),
    ("value_or_default", "当前/默认值"),
    ("value_source", "来源"),
    ("meaning", "含义"),
]

MODULE_DEPENDENCY_COLUMNS = [
    ("name", "名称"),
    ("dependency_type", "类型"),
    ("usage_relation", "关系"),
    ("required_for", "用途"),
    ("failure_behavior", "失败行为"),
]

MODULE_DATA_OBJECT_COLUMNS = [
    ("name", "名称"),
    ("data_type", "类型"),
    ("role", "角色"),
    ("producer", "生产方"),
    ("consumer", "消费方"),
    ("shape_or_contract", "结构/契约"),
]

INTERFACE_INDEX_COLUMNS = [
    ("interface_name", "接口名称"),
    ("description", "接口功能描述"),
    ("interface_type", "接口类型"),
]

INTERFACE_PARAMETER_COLUMNS = [
    ("parameter_name", "参数名"),
    ("parameter_type", "参数类型"),
    ("description", "参数描述"),
    ("direction", "输入/输出"),
]

INTERFACE_RETURN_COLUMNS = [
    ("return_name", "返回名"),
    ("return_type", "返回类型"),
    ("description", "描述"),
    ("condition", "条件"),
]

INTERFACE_ERROR_COLUMNS = [
    ("condition", "条件"),
    ("behavior", "行为"),
]

MECHANISM_INDEX_COLUMNS = [
    ("mechanism_name", "机制"),
    ("purpose", "用途"),
    ("input", "输入"),
    ("processing", "处理方式"),
    ("output", "输出"),
    ("structural_significance", "结构意义"),
]

KNOWN_LIMITATION_COLUMNS = [
    ("limitation", "限制"),
    ("impact", "影响"),
    ("mitigation_or_next_step", "缓解/后续"),
]
```

- [ ] **Step 5: Replace V1 Chapter 4 renderer helpers**

Replace `render_external_capability_summary()`, `render_internal_structure()`, `render_module_supplement()`, and `render_module_design_section()` with these V2 helpers:

```python
def render_not_applicable_table(section, columns, empty_text):
    rows = section.get("rows", []) if isinstance(section, dict) else []
    if rows:
        return render_fixed_table(rows, columns)
    reason = section.get("not_applicable_reason", "") if isinstance(section, dict) else ""
    if reason:
        return escape_plain_text(reason)
    return empty_text


def render_source_scope(scope):
    parts = [
        render_paragraph(scope.get("summary", "")),
        render_fixed_table_or_empty(scope.get("primary_files", []), SOURCE_FILE_COLUMNS, "无主要文件。"),
    ]
    consumed = render_bullets(scope.get("consumed_inputs", []))
    if consumed:
        parts.append("消费输入：\n" + consumed)
    outputs = render_bullets(scope.get("owned_outputs", []))
    if outputs:
        parts.append("拥有输出：\n" + outputs)
    out_of_scope = render_bullets(scope.get("out_of_scope", []))
    if out_of_scope:
        parts.append("不负责范围：\n" + out_of_scope)
    return "\n\n".join(part for part in parts if part != "")


def render_location(location):
    line_start = location.get("line_start")
    line_end = location.get("line_end")
    line_text = ""
    if line_start is not None and line_end is not None:
        line_text = f":{line_start}-{line_end}"
    symbol = location.get("symbol", "")
    symbol_text = f"#{symbol}" if symbol else ""
    return f"{location.get('file_path', '')}{symbol_text}{line_text}"


def render_executable_interface_detail(interface):
    parts = [
        f"原型：`{escape_plain_text(interface.get('prototype', '')).strip()}`",
        f"用途：{escape_plain_text(interface.get('purpose', '')).strip()}",
        f"位置：`{escape_plain_text(render_location(interface.get('location', {}))).strip()}`",
        "参数：\n" + render_not_applicable_table(interface.get("parameters", {}), INTERFACE_PARAMETER_COLUMNS, "无参数。"),
        "返回值：\n" + render_not_applicable_table(interface.get("return_values", {}), INTERFACE_RETURN_COLUMNS, "无返回值。"),
        render_mermaid_block(interface.get("execution_flow_diagram", {})),
    ]
    side_effects = render_bullets(interface.get("side_effects", []))
    if side_effects:
        parts.append("副作用：\n" + side_effects)
    if interface.get("error_behavior"):
        parts.append("错误行为：\n" + render_fixed_table(interface.get("error_behavior", []), INTERFACE_ERROR_COLUMNS))
    consumers = render_bullets(interface.get("consumers", []))
    if consumers:
        parts.append("使用方：\n" + consumers)
    return "\n\n".join(part for part in parts if part != "")


def render_contract_interface_detail(interface):
    contract = interface.get("contract", {})
    parts = [
        f"用途：{escape_plain_text(interface.get('purpose', '')).strip()}",
        f"位置：`{escape_plain_text(render_location(interface.get('location', {}))).strip()}`",
        f"契约范围：{escape_plain_text(contract.get('contract_scope', '')).strip()}",
        f"契约位置：`{escape_plain_text(contract.get('contract_location', '')).strip()}`",
        f"必填项：{escape_plain_text(contract.get('required_items', [])).strip()}",
    ]
    constraints = render_bullets(contract.get("constraints", []))
    if constraints:
        parts.append("约束：\n" + constraints)
    consumers = render_bullets(contract.get("consumers", []))
    if consumers:
        parts.append("使用方：\n" + consumers)
    parts.append(f"校验行为：{escape_plain_text(contract.get('validation_behavior', '')).strip()}")
    return "\n\n".join(part for part in parts if part != "")


def render_public_interfaces(public_interfaces, chapter_index):
    index_rows = public_interfaces.get("interface_index", {}).get("rows", [])
    details = {
        interface.get("interface_id"): interface
        for interface in public_interfaces.get("interfaces", [])
        if isinstance(interface, dict)
    }
    if not index_rows and not details:
        return escape_plain_text(public_interfaces.get("not_applicable_reason", "无对外接口。"))
    parts = [
        render_paragraph(public_interfaces.get("summary", "")),
        render_fixed_table(index_rows, INTERFACE_INDEX_COLUMNS),
    ]
    for detail_index, row in enumerate(index_rows, start=1):
        interface = details.get(row.get("interface_id"), {})
        title = escape_heading_label(row.get("interface_name", ""))
        parts.append(f"##### 4.{chapter_index}.5.{detail_index} {title}")
        if interface.get("interface_type") in ("command_line", "function", "method", "library_api", "workflow"):
            parts.append(render_executable_interface_detail(interface))
        else:
            parts.append(render_contract_interface_detail(interface))
    return "\n\n".join(part for part in parts if part != "")


def render_mechanism_text_block(block):
    title = escape_heading_label(block.get("title", ""))
    text = render_paragraph(block.get("text", ""))
    if title and text:
        return f"**{title}**\n\n{text}"
    return text


def render_internal_mechanism(internal_mechanism, chapter_index):
    index_rows = internal_mechanism.get("mechanism_index", {}).get("rows", [])
    details = {
        detail.get("mechanism_id"): detail
        for detail in internal_mechanism.get("mechanism_details", [])
        if isinstance(detail, dict)
    }
    if not index_rows:
        return escape_plain_text(internal_mechanism.get("not_applicable_reason", ""))
    parts = [
        render_paragraph(internal_mechanism.get("summary", "")),
        render_fixed_table(index_rows, MECHANISM_INDEX_COLUMNS),
    ]
    for detail_index, row in enumerate(index_rows, start=1):
        detail = details.get(row.get("mechanism_id"), {})
        title = escape_heading_label(row.get("mechanism_name", ""))
        parts.append(f"###### 4.{chapter_index}.6.{detail_index} {title}")
        for block in detail.get("blocks", []):
            if block.get("block_type") == "text":
                parts.append(render_mechanism_text_block(block))
    return "\n\n".join(part for part in parts if part != "")


def render_module_design_section(module, index, support_context):
    module_support = render_node_support(
        module,
        support_context,
        target_type="module",
        target_id=module.get("module_id", ""),
    )
    parts = [
        subchapter_heading(4, index, escape_heading_label(module.get("name", ""))),
        module_support,
        nested_heading(4, index, 1, "模块定位与源码/产物范围"),
        render_source_scope(module.get("source_scope", {})),
        nested_heading(4, index, 2, "配置"),
        render_paragraph(module.get("configuration", {}).get("summary", "")),
        render_not_applicable_table(module.get("configuration", {}).get("parameters", {}), MODULE_PARAMETER_COLUMNS, "无模块级配置。"),
        nested_heading(4, index, 3, "依赖"),
        render_paragraph(module.get("dependencies", {}).get("summary", "")),
        render_not_applicable_table(module.get("dependencies", {}), MODULE_DEPENDENCY_COLUMNS, "无模块级依赖。"),
        nested_heading(4, index, 4, "数据对象"),
        render_paragraph(module.get("data_objects", {}).get("summary", "")),
        render_not_applicable_table(module.get("data_objects", {}), MODULE_DATA_OBJECT_COLUMNS, "无模块级数据对象。"),
        nested_heading(4, index, 5, "对外接口"),
        render_public_interfaces(module.get("public_interfaces", {}), index),
        nested_heading(4, index, 6, "实现机制说明"),
        render_internal_mechanism(module.get("internal_mechanism", {}), index),
        nested_heading(4, index, 7, "已知限制"),
        render_paragraph(module.get("known_limitations", {}).get("summary", "")),
        render_not_applicable_table(module.get("known_limitations", {}), KNOWN_LIMITATION_COLUMNS, "无已知限制。"),
    ]
    return "\n\n".join(part for part in parts if part != "")
```

- [ ] **Step 6: Run rendering tests**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_v2_phase2_module_model.Phase2RenderingTests -v
```

Expected: PASS.

- [ ] **Step 7: Migrate existing renderer tests away from V1 Chapter 4 fields**

Update `tests/test_render_markdown.py`:

- Replace Chapter 4 assertions that expect headings `模块职责`, `对外能力说明`, `对外接口需求清单`, `模块内部结构关系图`, and `补充说明` with the seven V2 headings from `Phase2FixtureContractTests.test_chapter_4_renders_seven_fixed_subsections_in_order`.
- Replace mutations of:

```python
module_item["external_capability_details"]["provided_capabilities"]["rows"][0]
```

with mutations of:

```python
module_item["public_interfaces"]["interfaces"][0]
```

when the test is about low-confidence summary collection.

- Replace expected low-confidence path:

```text
$.module_design.modules[0].external_capability_details.provided_capabilities.rows[0]
```

with:

```text
$.module_design.modules[0].public_interfaces.interfaces[0]
```

- Update `render_markdown.py`'s `collect_low_confidence_items()` independently from the validator's low-confidence collection. Remove the loop over `external_capability_details.provided_capabilities.rows[]` and add a loop over public-interface details:

```python
for module_index, module in enumerate(document.get("module_design", {}).get("modules", [])):
    add_item(f"$.module_design.modules[{module_index}]", module)
    for interface_index, interface in enumerate(module.get("public_interfaces", {}).get("interfaces", [])):
        add_item(
            f"$.module_design.modules[{module_index}].public_interfaces.interfaces[{interface_index}]",
            interface,
        )
```

- Add `"interface_name"` and `"limitation"` to `LOW_CONFIDENCE_LABEL_KEYS` so Chapter 4 V2 items have readable labels in Chapter 9.
- Update support-data tests that referenced provided-capability rows. Use module-level support instead:

```python
document = valid_document()
document["module_design"]["modules"][0]["evidence_refs"] = ["EV-001"]
document["evidence"] = [
    {"id": "EV-001", "kind": "source", "title": "模块证据", "location": "schema", "description": "模块级证据。", "confidence": "observed"}
]
markdown = load_renderer_module().render_markdown(document, evidence_mode="inline")
self.assertIn("支持数据（MOD-SKILL / 技能文档生成模块）", markdown)
```

- Replace expected diagram collection from `internal_structure.diagram` and `external_capability_details.extra_diagrams` with executable public-interface diagrams:

```python
module_item["public_interfaces"]["interfaces"][1]["execution_flow_diagram"]["source"] = synthetic_flowchart_source("IFACEFLOW")
```

- Replace multi-module fixture setup that edits `second_design["internal_structure"]["diagram"]["id"]` with:

```python
second_design["public_interfaces"]["interfaces"][1]["execution_flow_diagram"]["id"] = "MER-IFACE-SECOND-FLOW"
```

- Keep renderer evidence-mode tests unchanged except for any fixture path assumptions that break after converting the canonical fixture to the V2 module model.

- [ ] **Step 8: Run renderer suite**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_render_markdown tests.test_v2_phase2_module_model -v
```

Expected: PASS.

- [ ] **Step 9: Commit**

```bash
git add scripts/render_markdown.py tests/test_v2_phase2_module_model.py tests/test_render_markdown.py
git commit -m "feat: render v2 phase 2 chapter 4"
```

---

### Task 5: Examples And Reference Documentation

**Files:**
- Modify: `examples/minimal-from-code.dsl.json`
- Modify: `examples/minimal-from-requirements.dsl.json`
- Modify: `references/dsl-spec.md`
- Modify: `references/document-structure.md`
- Modify: `references/review-checklist.md`
- Modify: `SKILL.md`
- Modify: `tests/test_v2_phase2_module_model.py`
- Modify: `tests/test_phase7_e2e.py`
- Modify: `tests/test_validate_mermaid.py`

- [ ] **Step 1: Add failing example and reference tests**

Append this test class to `tests/test_v2_phase2_module_model.py`:

```python
class Phase2ExamplesAndReferenceTests(unittest.TestCase):
    EXAMPLES = [
        ROOT / "examples/minimal-from-code.dsl.json",
        ROOT / "examples/minimal-from-requirements.dsl.json",
    ]

    def test_examples_validate_with_phase2_shape(self):
        for path in self.EXAMPLES:
            completed = run_validator(path)
            with self.subTest(path=path.name):
                self.assertEqual(0, completed.returncode, completed.stderr)

    def test_reference_docs_describe_phase2_contracts(self):
        expectations = {
            "references/dsl-spec.md": [
                "module_design.modules[]",
                "source_scope",
                "public_interfaces",
                "internal_mechanism",
                "known_limitations",
                "entrypoint_not_applicable_reason",
                "external_environment_reason",
            ],
            "references/document-structure.md": [
                "4.x.1 模块定位与源码/产物范围",
                "4.x.2 配置",
                "4.x.3 依赖",
                "4.x.4 数据对象",
                "4.x.5 对外接口",
                "4.x.6 实现机制说明",
                "4.x.7 已知限制",
                "运行单元 | 类型 | 入口 | 职责 | 关联模块 | 备注",
            ],
            "references/review-checklist.md": [
                "Chapter 4 seven fixed subsections",
                "public interface index and details",
                "Section 5.2 simplified runtime unit table",
            ],
            "SKILL.md": [
                "does not analyze repositories",
                "4.x.1 模块定位与源码/产物范围",
                "public_interfaces",
                "entrypoint: \"不适用\"",
            ],
        }
        for relative_path, phrases in expectations.items():
            text = (ROOT / relative_path).read_text(encoding="utf-8")
            for phrase in phrases:
                with self.subTest(path=relative_path, phrase=phrase):
                    self.assertIn(phrase, text)
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_v2_phase2_module_model.Phase2ExamplesAndReferenceTests -v
```

Expected: FAIL because examples and references still describe the V1 shape.

- [ ] **Step 3: Convert both examples**

For each file under `examples/`, apply the same V2 module shape used in `tests/fixtures/valid-v2-foundation.dsl.json`, with module IDs and names matching the example's Chapter 3 `module_intro.rows[]`. Preserve example-specific project names, flow names, output filenames, and Mermaid diagrams. Remove `entrypoint_not_applicable_reason` and `external_environment_reason` from runtime units.

Use this runtime-unit shape in both examples:

```json
{
  "unit_id": "RUN-GENERATE",
  "unit_name": "文档生成命令序列",
  "unit_type": "CLI workflow",
  "entrypoint": "python scripts/render_markdown.py",
  "responsibility": "在校验通过后生成 Markdown 文档。",
  "related_module_ids": ["MOD-SKILL"],
  "notes": "",
  "confidence": "observed",
  "evidence_refs": [],
  "traceability_refs": [],
  "source_snippet_refs": []
}
```

- [ ] **Step 4: Update reference docs**

In `references/dsl-spec.md`, add a Chapter 4 section that lists:

```markdown
## V2 Chapter 4 Module Model

`module_design.modules[]` uses the V2 module model for `dsl_version: "0.2.0"`.
Each module renders these fixed subsections in order:

1. `4.x.1 模块定位与源码/产物范围`
2. `4.x.2 配置`
3. `4.x.3 依赖`
4. `4.x.4 数据对象`
5. `4.x.5 对外接口`
6. `4.x.6 实现机制说明`
7. `4.x.7 已知限制`

V1 fields `internal_structure`, `external_capability_details`, `extra_diagrams`, and `extra_tables` are invalid as alternate V2 module-design inputs.
Section 5.2 no longer accepts `entrypoint_not_applicable_reason` or `external_environment_reason`.
When a runtime unit has no concrete entrypoint, set `entrypoint` to exactly `不适用` and put the explanation in `notes`.
```

In `references/document-structure.md`, add the same seven-subsection list and the visible Section 5.2 columns:

```markdown
| 运行单元 | 类型 | 入口 | 职责 | 关联模块 | 备注 |
| --- | --- | --- | --- | --- | --- |
```

In `references/review-checklist.md`, add checks:

```markdown
- Confirm Chapter 4 uses the seven fixed V2 subsections in order.
- Confirm public interface index rows and detail sections match and render in index order.
- Confirm Section 5.2 simplified runtime unit table omits V1 reason columns.
```

In `SKILL.md`, replace the old Chapter 4 guidance that lists module responsibilities or provided capabilities with V2 guidance:

```markdown
- Chapter 4 uses the V2 `module_design.modules[]` shape and renders seven fixed subsections: `4.x.1 模块定位与源码/产物范围`, `4.x.2 配置`, `4.x.3 依赖`, `4.x.4 数据对象`, `4.x.5 对外接口`, `4.x.6 实现机制说明`, and `4.x.7 已知限制`.
- Public function, method, library API, workflow, command-line, and contract interfaces belong under `public_interfaces`.
- Section 5.2 runtime units use visible columns `运行单元 | 类型 | 入口 | 职责 | 关联模块 | 备注`; if no concrete entrypoint exists, set `entrypoint: "不适用"` and put the reason in `notes`.
```

Keep the existing no-repository-analysis boundary in `SKILL.md`; do not add source-code inference instructions.

- [ ] **Step 5: Run examples and reference tests**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_v2_phase2_module_model.Phase2ExamplesAndReferenceTests -v
```

Expected: PASS.

- [ ] **Step 6: Migrate Phase 7 and Mermaid regression tests**

Update `tests/test_phase7_e2e.py`:

- Replace example-contract assertions that require `external_capability_details.provided_capabilities.rows[]` and `internal_structure` with checks for the V2 fields:

```python
for module in document["module_design"]["modules"]:
    self.assertIn("source_scope", module)
    self.assertIn("configuration", module)
    self.assertIn("dependencies", module)
    self.assertIn("data_objects", module)
    self.assertIn("public_interfaces", module)
    self.assertIn("internal_mechanism", module)
    self.assertIn("known_limitations", module)
```

- Add a runtime-unit assertion that removed fields are absent:

```python
for unit in document["runtime_view"]["runtime_units"]["rows"]:
    self.assertNotIn("entrypoint_not_applicable_reason", unit)
    self.assertNotIn("external_environment_reason", unit)
```

Update `tests/test_validate_mermaid.py` without changing `scripts/validate_mermaid.py` behavior:

- Update `REQUIRED_INPUTS` so the `SKILL.md` body contract expects V2 phrases such as `module scope`, `public interfaces`, and `internal mechanisms` instead of V1 `module-level external capabilities` and `module internal structure information`.
- Keep `DslMermaidStaticTests` scoped to the current extractor behavior. Do not add an expectation that `--from-dsl` extracts `$.module_design.modules[].public_interfaces.interfaces[].execution_flow_diagram`; Phase 4 owns Mermaid gate behavior.
- If `document_with_all_known_paths()` uses the converted V2 canonical fixture, inject the legacy extractor-only fields into the synthetic test document before asserting existing extractor paths:

```python
module = document["module_design"]["modules"][0]
module["internal_structure"] = {"diagram": self.diagram("MER-MODULE-INTERNAL")}
module["external_capability_details"] = {
    "extra_diagrams": [self.diagram("MER-MODULE-CAPABILITY-EXTRA")]
}
module["extra_diagrams"] = [self.diagram("MER-MODULE-EXTRA")]
```

This keeps the no-`validate_mermaid.py` Phase 2 boundary intact while preventing the converted V2 fixture from breaking legacy extractor tests.

- [ ] **Step 7: Run installed reference and regression tests**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_render_markdown.ReferenceSignpostTests tests.test_phase7_e2e tests.test_validate_mermaid -v
```

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add examples/minimal-from-code.dsl.json examples/minimal-from-requirements.dsl.json references/dsl-spec.md references/document-structure.md references/review-checklist.md SKILL.md tests/test_v2_phase2_module_model.py tests/test_phase7_e2e.py tests/test_validate_mermaid.py
git commit -m "docs: document v2 phase 2 module model"
```

---

### Task 6: End-To-End Verification And Regression Sweep

**Files:**
- Modify only files from earlier tasks when a verification failure points to a Phase 2 bug.

- [ ] **Step 1: Run the full unit suite**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest discover -s tests -v
```

Expected: PASS.

- [ ] **Step 2: Validate all V2 DSL examples and canonical fixture**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python scripts/validate_dsl.py tests/fixtures/valid-v2-foundation.dsl.json
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python scripts/validate_dsl.py examples/minimal-from-code.dsl.json
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python scripts/validate_dsl.py examples/minimal-from-requirements.dsl.json
```

Expected: each command prints `Validation succeeded`.

- [ ] **Step 3: Render fixture and examples to isolated preserved temporary output directories**

Run:

```bash
mkdir -p .codex-tmp
RUN_DIR=$(mktemp -d -p .codex-tmp v2-phase2-render.XXXXXX)
mkdir -p "$RUN_DIR/fixture" "$RUN_DIR/code-example" "$RUN_DIR/requirements-example"
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python scripts/render_markdown.py tests/fixtures/valid-v2-foundation.dsl.json --output-dir "$RUN_DIR/fixture"
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python scripts/render_markdown.py examples/minimal-from-code.dsl.json --output-dir "$RUN_DIR/code-example"
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python scripts/render_markdown.py examples/minimal-from-requirements.dsl.json --output-dir "$RUN_DIR/requirements-example"
```

Expected: each command exits `0`; each isolated output directory contains one Markdown output and no backup files. If a cleanup is desired after review, tell the user:

```bash
rm -r "$RUN_DIR"
```

- [ ] **Step 4: Validate Mermaid blocks from rendered Markdown**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python scripts/validate_mermaid.py --from-markdown "$RUN_DIR/fixture/create-structure-md_STRUCTURE_DESIGN.md" --static
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python scripts/validate_mermaid.py --from-markdown "$RUN_DIR/code-example/create-structure-md_STRUCTURE_DESIGN.md" --static
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python scripts/validate_mermaid.py --from-markdown "$RUN_DIR/requirements-example/requirements-note-example_STRUCTURE_DESIGN.md" --static
```

Expected: each static Markdown Mermaid validation exits `0`. Do not modify `scripts/validate_mermaid.py` or `references/mermaid-rules.md` if this fails; fix the DSL Mermaid source or renderer output.

- [ ] **Step 5: Inspect git diff**

Run:

```bash
git diff -- scripts/v2_phase2.py scripts/validate_dsl.py scripts/render_markdown.py schemas/structure-design.schema.json tests/test_v2_phase2_module_model.py tests/test_validate_dsl.py tests/test_validate_dsl_semantics.py tests/test_render_markdown.py tests/test_phase7_e2e.py tests/test_validate_mermaid.py tests/fixtures/valid-v2-foundation.dsl.json examples/minimal-from-code.dsl.json examples/minimal-from-requirements.dsl.json references/dsl-spec.md references/document-structure.md references/review-checklist.md SKILL.md
```

Expected: diff only contains Phase 2 schema, validator, renderer, fixture/example, and reference changes. No Mermaid validator/rules changes appear.

- [ ] **Step 6: Verify Mermaid validator and Mermaid rules were not modified**

Run:

```bash
git diff --exit-code -- scripts/validate_mermaid.py references/mermaid-rules.md
```

Expected: no output and exit code `0`.

- [ ] **Step 7: Commit**

```bash
git add scripts/v2_phase2.py scripts/validate_dsl.py scripts/render_markdown.py schemas/structure-design.schema.json tests/test_v2_phase2_module_model.py tests/test_validate_dsl.py tests/test_validate_dsl_semantics.py tests/test_render_markdown.py tests/test_phase7_e2e.py tests/test_validate_mermaid.py tests/fixtures/valid-v2-foundation.dsl.json examples/minimal-from-code.dsl.json examples/minimal-from-requirements.dsl.json references/dsl-spec.md references/document-structure.md references/review-checklist.md SKILL.md
git commit -m "test: verify v2 phase 2 end to end"
```

---

## Self-Review

- Spec coverage: Tasks 2-4 cover Chapter 4 seven-subsection rendering, V1 field rejection, module/Chapter 3 one-to-one matching, module kind, source scope, configuration, dependencies, data objects, public interfaces, internal mechanisms, typed anchors, known limitations, and Section 5.2 cleanup. Task 5 covers examples and docs. Task 6 covers end-to-end validation.
- Non-goals: This plan does not add repo analysis, migration tooling, Mermaid gate behavior, export formats, or Mermaid validator/rule changes.
- Phase split: Chapter 4 module-local dependencies use `system_dependency_ref` for Chapter 6 dependencies. The renderer does not deduplicate Chapter 4 and Chapter 6.
- Content blocks: Phase 2 renders internal mechanism text blocks only and leaves reusable diagram/table block expansion to Phase 3.
- Deletion policy: No task executes a deletion command; cleanup is provided as a user-run command only.
