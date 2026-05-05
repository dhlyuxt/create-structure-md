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


def run_validator(path):
    return subprocess.run(
        [PYTHON, str(ROOT / "scripts/validate_dsl.py"), str(path)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def write_json(tmpdir, name, document):
    path = Path(tmpdir) / name
    path.write_text(json.dumps(document, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def validation_stderr_for(document):
    with tempfile.TemporaryDirectory() as tmpdir:
        path = write_json(tmpdir, "phase2-semantic.dsl.json", document)
        return run_validator(path)


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


class Phase2SemanticValidationTests(unittest.TestCase):
    def assert_invalid(self, mutate, expected):
        document = valid_document()
        mutate(document)
        completed = validation_stderr_for(document)
        self.assertEqual(1, completed.returncode, completed.stderr or completed.stdout)
        self.assertIn(expected, completed.stderr)

    def test_module_design_must_match_chapter_3_one_to_one(self):
        self.assert_invalid(
            lambda document: document["module_design"]["modules"].append(deepcopy(document["module_design"]["modules"][0])),
            "must match chapter 3 modules one-to-one",
        )

    def test_source_scope_requires_at_least_one_scope_array_value(self):
        def mutate(document):
            scope = document["module_design"]["modules"][0]["source_scope"]
            scope["primary_files"] = []
            scope["consumed_inputs"] = []
            scope["owned_outputs"] = []

        self.assert_invalid(mutate, "source_scope must provide primary_files, consumed_inputs, or owned_outputs")

    def test_unknown_parameter_value_may_omit_default_but_default_source_must_not(self):
        def mutate(document):
            parameter = document["module_design"]["modules"][0]["configuration"]["parameters"]["rows"][0]
            parameter["value_source"] = "default"
            parameter["value_or_default"] = ""

        self.assert_invalid(mutate, "value_or_default must be non-empty unless value_source is unknown")

    def test_internal_module_dependency_target_must_reference_existing_module(self):
        def mutate(document):
            dependency = document["module_design"]["modules"][0]["dependencies"]["rows"][0]
            dependency["dependency_type"] = "internal_module"
            dependency["target_module_id"] = "MOD-MISSING"
            dependency["system_dependency_ref"] = ""

        self.assert_invalid(mutate, "target_module_id must reference an existing module")

    def test_data_object_dependency_target_must_reference_existing_data_object(self):
        def mutate(document):
            dependency = document["module_design"]["modules"][0]["dependencies"]["rows"][0]
            dependency["dependency_type"] = "data_object"
            dependency["target_data_id"] = "DATA-MISSING"
            dependency["system_dependency_ref"] = ""

        self.assert_invalid(mutate, "target_data_id must reference an existing data object")

    def test_system_dependency_ref_must_reference_chapter_6_dependency(self):
        def mutate(document):
            document["module_design"]["modules"][0]["dependencies"]["rows"][0]["system_dependency_ref"] = "SYSDEP-MISSING"

        self.assert_invalid(mutate, "system_dependency_ref must reference a Chapter 6 dependency")

    def test_interface_index_and_details_must_match(self):
        def mutate(document):
            document["module_design"]["modules"][0]["public_interfaces"]["interfaces"].pop()

        self.assert_invalid(mutate, "interface_index rows and interface details must have matching interface_id sets")

    def test_executable_interface_requires_non_empty_mermaid_source(self):
        def mutate(document):
            document["module_design"]["modules"][0]["public_interfaces"]["interfaces"][1]["execution_flow_diagram"]["source"] = ""

        self.assert_invalid(mutate, "execution_flow_diagram.source must be non-empty")

    def test_executable_interface_requires_non_empty_prototype(self):
        def mutate(document):
            document["module_design"]["modules"][0]["public_interfaces"]["interfaces"][1]["prototype"] = " "

        self.assert_invalid(mutate, "prototype must be non-empty")

    def test_executable_interface_requires_side_effects_and_error_behavior(self):
        def mutate(document):
            interface = document["module_design"]["modules"][0]["public_interfaces"]["interfaces"][1]
            interface["side_effects"] = []
            interface["error_behavior"] = []

        document = valid_document()
        mutate(document)
        completed = validation_stderr_for(document)
        self.assertEqual(1, completed.returncode, completed.stderr)
        self.assertIn("side_effects must contain at least one item", completed.stderr)
        self.assertIn("error_behavior must contain at least one item", completed.stderr)

    def test_contract_interface_required_items_and_constraints_are_non_empty_when_present(self):
        def mutate(document):
            contract = document["module_design"]["modules"][0]["public_interfaces"]["interfaces"][0]["contract"]
            contract["required_items"] = []
            contract["constraints"] = []

        document = valid_document()
        mutate(document)
        completed = validation_stderr_for(document)
        self.assertEqual(1, completed.returncode, completed.stderr)
        self.assertIn("contract.required_items must contain at least one item", completed.stderr)
        self.assertIn("contract.constraints must contain at least one item when present", completed.stderr)

    def test_contract_interface_requires_consumers(self):
        def mutate(document):
            document["module_design"]["modules"][0]["public_interfaces"]["interfaces"][0]["contract"]["consumers"] = []

        self.assert_invalid(mutate, "contract.consumers must contain at least one item")

    def test_observed_function_without_symbol_or_line_range_warns(self):
        document = valid_document()
        row = document["module_design"]["modules"][0]["public_interfaces"]["interface_index"]["rows"][1]
        interface = document["module_design"]["modules"][0]["public_interfaces"]["interfaces"][1]
        row["interface_type"] = "function"
        interface["interface_type"] = "function"
        interface["location"]["symbol"] = ""
        interface["location"]["line_start"] = None
        interface["location"]["line_end"] = None
        completed = validation_stderr_for(document)
        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertIn("observed function or method interface should provide symbol or line range", completed.stdout)

    def test_mechanism_index_and_details_must_match(self):
        def mutate(document):
            document["module_design"]["modules"][0]["internal_mechanism"]["mechanism_details"] = []

        self.assert_invalid(mutate, "mechanism_index rows and mechanism_details must have matching mechanism_id sets")

    def test_duplicate_mechanism_ids_fail_within_module(self):
        def mutate(document):
            mechanism = document["module_design"]["modules"][0]["internal_mechanism"]
            mechanism["mechanism_index"]["rows"].append(deepcopy(mechanism["mechanism_index"]["rows"][0]))
            mechanism["mechanism_details"].append(deepcopy(mechanism["mechanism_details"][0]))

        self.assert_invalid(mutate, "duplicate mechanism_id")

    def test_mechanism_index_row_requires_related_anchor(self):
        def mutate(document):
            document["module_design"]["modules"][0]["internal_mechanism"]["mechanism_index"]["rows"][0]["related_anchors"] = []

        self.assert_invalid(mutate, "related_anchors must contain at least one anchor")

    def test_related_anchor_resolution_covers_all_non_file_id_types(self):
        anchor_types = [
            "module_id",
            "interface_id",
            "data_id",
            "dependency_id",
            "parameter_id",
            "diagram_id",
            "table_id",
            "source_snippet_id",
            "evidence_id",
            "traceability_id",
        ]
        for anchor_type in anchor_types:
            with self.subTest(anchor_type=anchor_type):
                def mutate(document, anchor_type=anchor_type):
                    anchor = document["module_design"]["modules"][0]["internal_mechanism"]["mechanism_index"]["rows"][0]["related_anchors"][0]
                    anchor["anchor_type"] = anchor_type
                    anchor["value"] = f"MISSING-{anchor_type}"

                self.assert_invalid(mutate, "related_anchors value must resolve")

    def test_file_path_anchor_does_not_check_filesystem(self):
        document = valid_document()
        anchor = document["module_design"]["modules"][0]["internal_mechanism"]["mechanism_index"]["rows"][0]["related_anchors"][0]
        anchor["anchor_type"] = "file_path"
        anchor["value"] = "missing/path/that/does/not/exist.py"
        completed = validation_stderr_for(document)
        self.assertEqual(0, completed.returncode, completed.stderr)

    def test_empty_related_anchor_value_fails_schema_validation(self):
        document = valid_document()
        document["module_design"]["modules"][0]["internal_mechanism"]["mechanism_index"]["rows"][0]["related_anchors"][0]["value"] = ""
        completed = validation_stderr_for(document)
        self.assertEqual(2, completed.returncode, completed.stderr)
        self.assertIn("related_anchors", completed.stderr)

    def test_other_related_anchor_requires_reason(self):
        def mutate(document):
            anchor = document["module_design"]["modules"][0]["internal_mechanism"]["mechanism_index"]["rows"][0]["related_anchors"][0]
            anchor["anchor_type"] = "other"
            anchor["value"] = "custom-anchor"
            anchor["reason"] = ""

        self.assert_invalid(mutate, "reason is required when anchor_type is other")

    def test_runtime_entrypoint_not_applicable_requires_notes(self):
        def mutate(document):
            unit = document["runtime_view"]["runtime_units"]["rows"][0]
            unit["entrypoint"] = "不适用"
            unit["notes"] = ""

        self.assert_invalid(mutate, "entrypoint 不适用 requires non-empty notes")

    def test_runtime_entrypoint_inline_reason_is_invalid(self):
        def mutate(document):
            document["runtime_view"]["runtime_units"]["rows"][0]["entrypoint"] = "不适用：由调用方提供"

        self.assert_invalid(mutate, "entrypoint must be exactly 不适用 without inline reason")
