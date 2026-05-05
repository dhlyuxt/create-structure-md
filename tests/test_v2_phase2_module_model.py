import importlib.util
import json
import subprocess
import sys
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


def schema_errors(document):
    schema = load_json(SCHEMA)
    Draft202012Validator.check_schema(schema)
    return sorted(Draft202012Validator(schema).iter_errors(document), key=lambda error: list(error.path))


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
        positions = []
        for heading in headings:
            position = markdown.find(heading)
            with self.subTest(heading=heading):
                self.assertNotEqual(-1, position, f"missing Phase 2 heading: {heading}")
            positions.append(position)
        if -1 in positions:
            return
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
