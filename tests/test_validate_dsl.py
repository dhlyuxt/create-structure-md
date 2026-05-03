import json
import subprocess
import sys
import unittest
from copy import deepcopy
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_DIRECTORIES = [
    "references",
    "schemas",
    "scripts",
    "examples",
    "tests",
]

REQUIRED_FILES = [
    "SKILL.md",
    "requirements.txt",
    "references/dsl-spec.md",
    "references/document-structure.md",
    "references/mermaid-rules.md",
    "references/review-checklist.md",
    "schemas/structure-design.schema.json",
    "scripts/validate_dsl.py",
    "scripts/validate_mermaid.py",
    "scripts/render_markdown.py",
    "examples/minimal-from-code.dsl.json",
    "examples/minimal-from-requirements.dsl.json",
    "tests/test_validate_dsl.py",
    "tests/test_validate_mermaid.py",
    "tests/test_render_markdown.py",
]

JSON_SCAFFOLD_FILES = [
    "schemas/structure-design.schema.json",
    "examples/minimal-from-code.dsl.json",
    "examples/minimal-from-requirements.dsl.json",
]

SCRIPT_CASES = []

SCHEMA_PATH = ROOT / "schemas/structure-design.schema.json"
EXAMPLE_PATHS = [
    ROOT / "examples/minimal-from-code.dsl.json",
    ROOT / "examples/minimal-from-requirements.dsl.json",
]

TOP_LEVEL_FIELDS = [
    "dsl_version",
    "document",
    "system_overview",
    "architecture_views",
    "module_design",
    "runtime_view",
    "configuration_data_dependencies",
    "cross_module_collaboration",
    "key_flows",
    "structure_issues_and_suggestions",
    "evidence",
    "traceability",
    "risks",
    "assumptions",
    "source_snippets",
]


def load_json(relative_path):
    return json.loads((ROOT / relative_path).read_text(encoding="utf-8"))


def load_schema():
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def validator():
    schema = load_schema()
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def validator_for_def(def_name):
    schema = load_schema()
    def_schema = {
        "$schema": schema["$schema"],
        "$defs": schema["$defs"],
        "$ref": f"#/$defs/{def_name}",
    }
    Draft202012Validator.check_schema(def_schema)
    return Draft202012Validator(def_schema)


def valid_example():
    return deepcopy(load_json("tests/fixtures/valid-phase2.dsl.json"))


def validation_errors(document):
    errors = sorted(validator().iter_errors(document), key=lambda error: list(error.path))
    return errors


def matching_errors(errors, expected_fragment=None, expected_validator=None, expected_path=None):
    matches = []
    for error in errors:
        if expected_fragment is not None and expected_fragment not in error.message:
            if not (expected_fragment == "does not match" and error.validator == "not"):
                continue
        if expected_validator is not None and error.validator != expected_validator:
            continue
        if expected_path is not None and list(error.path) != expected_path:
            continue
        matches.append(error)
    return matches


def assert_invalid(testcase, document, expected_fragment=None, *, expected_validator=None, expected_path=None):
    errors = validation_errors(document)
    testcase.assertTrue(errors, "Expected schema validation to fail")
    if expected_fragment is not None or expected_validator is not None or expected_path is not None:
        testcase.assertTrue(
            matching_errors(errors, expected_fragment, expected_validator, expected_path),
            "Expected one error to match all requested criteria; got "
            f"{[(error.message, error.validator, list(error.path)) for error in errors]}",
        )


def assert_invalid_def(testcase, def_name, value, expected_fragment=None, *, expected_validator=None, expected_path=None):
    errors = sorted(validator_for_def(def_name).iter_errors(value), key=lambda error: list(error.path))
    testcase.assertTrue(errors, f"Expected #/$defs/{def_name} validation to fail")
    if expected_fragment is not None or expected_validator is not None or expected_path is not None:
        testcase.assertTrue(
            matching_errors(errors, expected_fragment, expected_validator, expected_path),
            "Expected one error to match all requested criteria; got "
            f"{[(error.message, error.validator, list(error.path)) for error in errors]}",
        )


class ScaffoldLayoutTests(unittest.TestCase):
    def test_required_directories_exist(self):
        for relative_path in REQUIRED_DIRECTORIES:
            path = ROOT / relative_path
            with self.subTest(path=relative_path):
                self.assertTrue(path.is_dir(), f"Missing directory: {relative_path}")

    def test_required_files_exist(self):
        for relative_path in REQUIRED_FILES:
            path = ROOT / relative_path
            with self.subTest(path=relative_path):
                self.assertTrue(path.is_file(), f"Missing file: {relative_path}")

    def test_json_scaffold_files_are_parseable(self):
        for relative_path in JSON_SCAFFOLD_FILES:
            path = ROOT / relative_path
            with self.subTest(path=relative_path):
                json.loads(path.read_text(encoding="utf-8"))


class DependencyContractTests(unittest.TestCase):
    def test_requirements_contains_runtime_dependency_only(self):
        requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8")
        dependency_lines = [
            line.strip()
            for line in requirements.splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]
        self.assertEqual(["jsonschema"], dependency_lines)
        self.assertNotIn("pytest", requirements)
        self.assertNotIn("requirements-dev", requirements)


class ScriptStubTests(unittest.TestCase):
    def test_scripts_are_python_executable_stubs(self):
        for relative_path, args, expected_message in SCRIPT_CASES:
            script_path = ROOT / relative_path
            with self.subTest(script=relative_path):
                completed = subprocess.run(
                    [sys.executable, str(script_path), *args],
                    cwd=ROOT,
                    text=True,
                    capture_output=True,
                    check=False,
                )
                combined_output = completed.stdout + completed.stderr
                self.assertEqual(2, completed.returncode)
                self.assertIn(expected_message, combined_output)

    def test_scripts_do_not_claim_success(self):
        forbidden_success_messages = [
            "Validation succeeded",
            "Mermaid validation passed",
            "Markdown rendered",
            "Document written",
        ]
        for relative_path, args, _expected_message in SCRIPT_CASES:
            script_path = ROOT / relative_path
            with self.subTest(script=relative_path):
                completed = subprocess.run(
                    [sys.executable, str(script_path), *args],
                    cwd=ROOT,
                    text=True,
                    capture_output=True,
                    check=False,
                )
                combined_output = completed.stdout + completed.stderr
                for forbidden in forbidden_success_messages:
                    self.assertNotIn(forbidden, combined_output)


class ValidateDslCliTests(unittest.TestCase):
    def test_validate_dsl_cli_accepts_valid_fixture(self):
        completed = subprocess.run(
            [sys.executable, str(ROOT / "scripts/validate_dsl.py"), str(ROOT / "tests/fixtures/valid-phase2.dsl.json")],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertIn("Validation succeeded", completed.stdout)
        self.assertEqual("", completed.stderr)


class SchemaRootContractTests(unittest.TestCase):
    def test_schema_is_valid_draft_2020_12_schema(self):
        Draft202012Validator.check_schema(load_schema())

    def test_root_requires_all_top_level_fields(self):
        schema = load_schema()
        self.assertEqual("https://json-schema.org/draft/2020-12/schema", schema["$schema"])
        self.assertCountEqual(TOP_LEVEL_FIELDS, schema["required"])
        self.assertFalse(schema["additionalProperties"])

    def test_schema_defines_required_base_defs(self):
        defs = load_schema()["$defs"]
        expected_defs = {
            "nonEmptyString": {"type": "string", "minLength": 1},
            "stringArray": {"type": "array", "items": {"$ref": "#/$defs/nonEmptyString"}},
            "referenceArray": {"type": "array", "items": {"$ref": "#/$defs/nonEmptyString"}},
            "confidence": {"type": "string", "enum": ["observed", "inferred", "unknown"]},
        }
        self.assertLessEqual(expected_defs.keys(), defs.keys())

        for def_name, expected_schema in expected_defs.items():
            with self.subTest(def_name=def_name):
                self.assertEqual(expected_schema, defs[def_name])

        validator_for_def("nonEmptyString").validate("value")
        assert_invalid_def(self, "nonEmptyString", "", expected_validator="minLength", expected_path=[])

        validator_for_def("stringArray").validate(["alpha", "beta"])
        assert_invalid_def(self, "stringArray", [""], expected_validator="minLength", expected_path=[0])

        validator_for_def("referenceArray").validate(["REF-001"])
        assert_invalid_def(self, "referenceArray", [""], expected_validator="minLength", expected_path=[0])

        for value in ["observed", "inferred", "unknown"]:
            with self.subTest(confidence=value):
                validator_for_def("confidence").validate(value)
        assert_invalid_def(self, "confidence", "guessed", expected_validator="enum", expected_path=[])

    def test_fixture_passes_root_shell_validation(self):
        validator().validate(valid_example())

    def test_dsl_version_must_be_non_empty(self):
        document = valid_example()
        document["dsl_version"] = ""
        assert_invalid(
            self,
            document,
            "should be non-empty",
            expected_validator="minLength",
            expected_path=["dsl_version"],
        )

    def test_unknown_top_level_field_fails(self):
        document = valid_example()
        document["required_tables"] = []
        assert_invalid(
            self,
            document,
            "Additional properties are not allowed",
            expected_validator="additionalProperties",
            expected_path=[],
        )

    def test_validation_policy_fields_fail_at_top_level(self):
        for forbidden in ["empty_allowed", "required", "min_rows", "max_rows", "render_when_empty"]:
            document = valid_example()
            document[forbidden] = True
            with self.subTest(field=forbidden):
                assert_invalid(
                    self,
                    document,
                    "Additional properties are not allowed",
                    expected_validator="additionalProperties",
                    expected_path=[],
                )


class SchemaCommonShapeTests(unittest.TestCase):
    def test_fixture_passes_with_common_definitions(self):
        validator().validate(valid_example())

    def test_structurally_unsafe_output_filenames_fail(self):
        invalid_names = [
            "create-structure-md_STRUCTURE_DESIGN.txt",
            "nested/create-structure-md_STRUCTURE_DESIGN.md",
            "nested\\create-structure-md_STRUCTURE_DESIGN.md",
            "../create-structure-md_STRUCTURE_DESIGN.md",
            "bad..name.md",
            "bad\u0001name.md",
            "bad\u007fname.md",
            "bad\u009fname.md",
        ]
        for output_file in invalid_names:
            document = valid_example()
            document["document"]["output_file"] = output_file
            with self.subTest(output_file=output_file):
                assert_invalid(
                    self,
                    document,
                    "does not match",
                    expected_path=["document", "output_file"],
                )

    def test_empty_diagram_object_fails_when_optional_field_is_present(self):
        assert_invalid_def(
            self,
            "diagram",
            {},
            "is a required property",
            expected_validator="required",
            expected_path=[],
        )

    def test_extra_table_rows_reject_traceability_and_source_snippet_refs(self):
        for forbidden in ["traceability_refs", "source_snippet_refs"]:
            extra_table = {
                "id": "TBL-ARCH-001",
                "title": "补充表格",
                "columns": [{"key": "name", "title": "名称"}],
                "rows": [{"name": "示例", forbidden: ["TR-001"]}]
            }
            with self.subTest(field=forbidden):
                assert_invalid_def(
                    self,
                    "extraTable",
                    extra_table,
                    "should not be valid",
                    expected_validator="not",
                    expected_path=["rows", 0],
                )

    def test_extra_table_evidence_refs_must_be_reference_array(self):
        extra_table = {
            "id": "TBL-ARCH-001",
            "title": "补充表格",
            "columns": [{"key": "name", "title": "名称"}],
            "rows": [{"name": "示例", "evidence_refs": [1]}]
        }
        assert_invalid_def(
            self,
            "extraTable",
            extra_table,
            "is not of type 'string'",
            expected_validator="type",
            expected_path=["rows", 0, "evidence_refs", 0],
        )

    def test_extra_table_rows_reject_validation_policy_fields(self):
        for forbidden in ["required", "min_rows", "max_rows", "empty_allowed", "render_when_empty"]:
            extra_table = {
                "id": "TBL-ARCH-001",
                "title": "补充表格",
                "columns": [{"key": "name", "title": "名称"}],
                "rows": [{"name": "示例", forbidden: True}]
            }
            with self.subTest(field=forbidden):
                assert_invalid_def(
                    self,
                    "extraTable",
                    extra_table,
                    "should not be valid",
                    expected_validator="not",
                    expected_path=["rows", 0],
                )

    def test_extra_table_column_key_and_title_must_be_non_empty(self):
        for field_name in ["key", "title"]:
            extra_table = {
                "id": "TBL-ARCH-001",
                "title": "补充表格",
                "columns": [{"key": "name", "title": "名称"}],
                "rows": [{"name": "示例"}],
            }
            extra_table["columns"][0][field_name] = ""
            with self.subTest(field_name=field_name):
                assert_invalid_def(
                    self,
                    "extraTable",
                    extra_table,
                    "should be non-empty",
                    expected_validator="minLength",
                    expected_path=["columns", 0, field_name],
                )

    def test_extra_diagram_empty_source_is_schema_valid_and_semantically_checked_later(self):
        document = valid_example()
        document["architecture_views"]["extra_diagrams"] = [{
            "id": "MER-ARCH-EXTRA",
            "kind": "extra",
            "title": "补充图",
            "diagram_type": "flowchart",
            "description": "补充图。",
            "source": "",
            "confidence": "observed",
        }]
        # Schema allows string shape; semantic validator owns non-empty source.
        validator().validate(document)


class SchemaChapterTwoThroughFourTests(unittest.TestCase):
    def test_fixture_passes_with_chapter_two_through_four_schema(self):
        validator().validate(valid_example())

    def test_chapter_two_rejects_unknown_capability_field(self):
        document = valid_example()
        document["system_overview"]["core_capabilities"][0]["surprise_id"] = "CAP-BAD"
        assert_invalid(
            self,
            document,
            "Additional properties are not allowed",
            expected_validator="additionalProperties",
            expected_path=["system_overview", "core_capabilities", 0],
        )

    def test_module_intro_rejects_fixed_table_id_title_or_columns(self):
        for forbidden in ["id", "title", "columns"]:
            document = valid_example()
            document["architecture_views"]["module_intro"][forbidden] = forbidden
            with self.subTest(field=forbidden):
                assert_invalid(
                    self,
                    document,
                    "Additional properties are not allowed",
                    expected_validator="additionalProperties",
                    expected_path=["architecture_views", "module_intro"],
                )

    def test_module_design_module_id_is_modeled_reference_field(self):
        document = valid_example()
        document["module_design"]["modules"][0]["module_id"] = ""
        assert_invalid(
            self,
            document,
            "should be non-empty",
            expected_validator="minLength",
            expected_path=["module_design", "modules", 0, "module_id"],
        )

    def test_internal_structure_diagram_rejects_empty_object(self):
        document = valid_example()
        document["module_design"]["modules"][0]["internal_structure"]["diagram"] = {}
        assert_invalid(
            self,
            document,
            "is a required property",
            expected_validator="required",
            expected_path=["module_design", "modules", 0, "internal_structure", "diagram"],
        )


class SchemaChapterFiveThroughNineTests(unittest.TestCase):
    def test_fixture_passes_with_chapter_five_through_nine_schema(self):
        validator().validate(valid_example())

    def test_runtime_related_module_ids_are_string_arrays(self):
        document = valid_example()
        document["runtime_view"]["runtime_units"]["rows"][0]["related_module_ids"] = [1]
        assert_invalid(
            self,
            document,
            "is not of type 'string'",
            expected_validator="type",
            expected_path=["runtime_view", "runtime_units", "rows", 0, "related_module_ids", 0],
        )

    def test_collaboration_optional_diagram_allows_omission_but_rejects_empty_object(self):
        document = valid_example()
        document["cross_module_collaboration"].pop("collaboration_relationship_diagram", None)
        validator().validate(document)

        document = valid_example()
        document["cross_module_collaboration"]["collaboration_relationship_diagram"] = {}
        assert_invalid(
            self,
            document,
            "is a required property",
            expected_validator="required",
            expected_path=["cross_module_collaboration", "collaboration_relationship_diagram"],
        )

    def test_runtime_optional_sequence_diagram_rejects_empty_object(self):
        document = valid_example()
        document["runtime_view"]["runtime_sequence_diagram"] = {}
        assert_invalid(
            self,
            document,
            "is a required property",
            expected_validator="required",
            expected_path=["runtime_view", "runtime_sequence_diagram"],
        )

    def test_flow_index_rejects_common_metadata(self):
        for forbidden in ["confidence", "evidence_refs", "traceability_refs", "source_snippet_refs"]:
            document = valid_example()
            document["key_flows"]["flow_index"]["rows"][0][forbidden] = "observed"
            with self.subTest(field=forbidden):
                assert_invalid(
                    self,
                    document,
                    "Additional properties are not allowed",
                    expected_validator="additionalProperties",
                    expected_path=["key_flows", "flow_index", "rows", 0],
                )

    def test_flow_step_order_must_be_positive_integer(self):
        document = valid_example()
        document["key_flows"]["flows"][0]["steps"][0]["order"] = 0
        assert_invalid(
            self,
            document,
            "is less than the minimum",
            expected_validator="minimum",
            expected_path=["key_flows", "flows", 0, "steps", 0, "order"],
        )

    def test_chapter_six_rows_reject_unknown_id_fields(self):
        cases = [
            ("configuration_items", "unknown_id"),
            ("structural_data_artifacts", "owner_module_id"),
            ("dependencies", "dependency_ids"),
        ]
        for table_name, field_name in cases:
            document = valid_example()
            document["configuration_data_dependencies"][table_name]["rows"][0][field_name] = "BAD-001"
            with self.subTest(table=table_name, field=field_name):
                assert_invalid(
                    self,
                    document,
                    "Additional properties are not allowed",
                    expected_validator="additionalProperties",
                    expected_path=["configuration_data_dependencies", table_name, "rows", 0],
                )

    def test_collaboration_row_rejects_unknown_reference_fields(self):
        document = valid_example()
        document["cross_module_collaboration"]["collaboration_scenarios"]["rows"][0]["participant_ids"] = ["MOD-SKILL"]
        assert_invalid(
            self,
            document,
            "Additional properties are not allowed",
            expected_validator="additionalProperties",
            expected_path=["cross_module_collaboration", "collaboration_scenarios", "rows", 0],
        )

    def test_flow_branch_related_runtime_unit_ids_must_be_string_arrays(self):
        document = valid_example()
        document["key_flows"]["flows"][0]["branches_or_exceptions"][0]["related_runtime_unit_ids"] = [1]
        assert_invalid(
            self,
            document,
            "is not of type 'string'",
            expected_validator="type",
            expected_path=["key_flows", "flows", 0, "branches_or_exceptions", 0, "related_runtime_unit_ids", 0],
        )

class SchemaSupportDataTests(unittest.TestCase):
    def test_fixture_passes_with_support_data_schema(self):
        validator().validate(valid_example())

    def test_core_capability_accepts_optional_support_refs(self):
        document = valid_example()
        document["evidence"] = [
            {"id": "EV-CAP", "kind": "note", "title": "能力证据", "location": "", "description": "", "confidence": "observed"}
        ]
        document["traceability"] = [
            {
                "id": "TR-CAP",
                "source_external_id": "REQ-CAP",
                "source_type": "requirement",
                "target_type": "core_capability",
                "target_id": "CAP-001",
                "description": "核心能力追踪。",
            }
        ]
        document["source_snippets"] = [
            {
                "id": "SNIP-CAP",
                "path": "references/dsl-spec.md",
                "line_start": 1,
                "line_end": 1,
                "language": "markdown",
                "purpose": "核心能力证据。",
                "content": "# create-structure-md DSL Spec",
                "confidence": "observed",
            }
        ]
        document["system_overview"]["core_capabilities"][0]["evidence_refs"] = ["EV-CAP"]
        document["system_overview"]["core_capabilities"][0]["traceability_refs"] = ["TR-CAP"]
        document["system_overview"]["core_capabilities"][0]["source_snippet_refs"] = ["SNIP-CAP"]

        validator().validate(document)

    def test_support_data_objects_accept_valid_shapes(self):
        document = valid_example()
        document["evidence"] = [
            {
                "id": "EV-001",
                "kind": "source",
                "title": "入口脚本",
                "location": "scripts/render_markdown.py",
                "description": "渲染入口脚本。",
                "confidence": "observed"
            }
        ]
        document["traceability"] = [
            {
                "id": "TR-001",
                "source_external_id": "REQ-001",
                "source_type": "requirement",
                "target_type": "module",
                "target_id": "MOD-SKILL",
                "description": "需求映射到技能模块。"
            }
        ]
        document["risks"] = [
            {
                "id": "RISK-001",
                "description": "示例风险。",
                "impact": "影响文档完整性。",
                "mitigation": "通过校验发现。",
                "confidence": "inferred",
                "evidence_refs": ["EV-001"],
                "traceability_refs": ["TR-001"],
                "source_snippet_refs": ["SNIP-001"]
            }
        ]
        document["assumptions"] = [
            {
                "id": "ASM-001",
                "description": "示例假设。",
                "rationale": "用于验证 support data schema。",
                "validation_suggestion": "执行语义校验。",
                "confidence": "unknown",
                "evidence_refs": ["EV-001"],
                "traceability_refs": ["TR-001"],
                "source_snippet_refs": ["SNIP-001"]
            }
        ]
        document["source_snippets"] = [
            {
                "id": "SNIP-001",
                "path": "scripts/render_markdown.py",
                "line_start": 1,
                "line_end": 2,
                "language": "python",
                "purpose": "说明脚本入口。",
                "content": "#!/usr/bin/env python3\n",
                "confidence": "observed"
            }
        ]
        validator().validate(document)

    def test_support_data_objects_reject_unknown_fields(self):
        cases = [
            ("evidence", {"id": "EV-001", "kind": "source", "title": "", "location": "", "description": "", "confidence": "observed"}),
            ("traceability", {"id": "TR-001", "source_external_id": "REQ-001", "source_type": "requirement", "target_type": "module", "target_id": "MOD-001", "description": ""}),
            ("risks", {"id": "RISK-001", "description": "", "impact": "", "mitigation": "", "confidence": "inferred", "evidence_refs": [], "traceability_refs": [], "source_snippet_refs": []}),
            ("assumptions", {"id": "ASM-001", "description": "", "rationale": "", "validation_suggestion": "", "confidence": "unknown", "evidence_refs": [], "traceability_refs": [], "source_snippet_refs": []}),
            ("source_snippets", {"id": "SNIP-001", "path": "src/main.py", "line_start": 1, "line_end": 1, "language": "python", "purpose": "", "content": "print('x')", "confidence": "observed"}),
        ]
        for field, item in cases:
            document = valid_example()
            item = dict(item)
            item["unexpected"] = True
            document[field] = [item]
            with self.subTest(field=field):
                assert_invalid(
                    self,
                    document,
                    "Additional properties are not allowed",
                    expected_validator="additionalProperties",
                    expected_path=[field, 0],
                )

    def test_source_snippet_line_numbers_must_be_positive_integers(self):
        invalid_values = [
            (0, "minimum"),
            (-1, "minimum"),
            ("1", "type"),
        ]
        for field_name in ["line_start", "line_end"]:
            for value, expected_validator in invalid_values:
                document = valid_example()
                snippet = {
                    "id": "SNIP-001",
                    "path": "src/main.py",
                    "line_start": 1,
                    "line_end": 1,
                    "language": "python",
                    "purpose": "证明入口",
                    "content": "print('x')",
                    "confidence": "observed"
                }
                snippet[field_name] = value
                document["source_snippets"] = [snippet]
                with self.subTest(field=field_name, value=value):
                    assert_invalid(
                        self,
                        document,
                        expected_validator=expected_validator,
                        expected_path=["source_snippets", 0, field_name],
                    )

    def test_traceability_target_type_enum_is_enforced(self):
        document = valid_example()
        document["traceability"] = [
            {
                "id": "TR-001",
                "source_external_id": "REQ-001",
                "source_type": "requirement",
                "target_type": "unknown_target",
                "target_id": "MOD-001",
                "description": ""
            }
        ]
        assert_invalid(
            self,
            document,
            "is not one of",
            expected_validator="enum",
            expected_path=["traceability", 0, "target_type"],
        )


class SchemaExampleValidationTests(unittest.TestCase):
    def test_example_dsl_files_pass_schema_validation(self):
        schema_validator = validator()
        for path in EXAMPLE_PATHS:
            with self.subTest(path=path.name):
                schema_validator.validate(json.loads(path.read_text(encoding="utf-8")))

    def test_examples_use_concrete_output_filenames(self):
        for path in EXAMPLE_PATHS:
            document = json.loads(path.read_text(encoding="utf-8"))
            output_file = document["document"]["output_file"]
            with self.subTest(path=path.name):
                self.assertTrue(output_file.endswith("_STRUCTURE_DESIGN.md"))
                self.assertNotEqual("STRUCTURE_DESIGN.md", output_file)
                self.assertNotEqual("structure_design.md", output_file)
                self.assertNotEqual("design.md", output_file)
                self.assertNotEqual("软件结构设计说明书.md", output_file)


if __name__ == "__main__":
    unittest.main()
