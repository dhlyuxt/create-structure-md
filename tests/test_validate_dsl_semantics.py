import json
import subprocess
import sys
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts/validate_dsl.py"
FIXTURE = ROOT / "tests/fixtures/valid-phase2.dsl.json"
PYTHON = sys.executable


def valid_document():
    return deepcopy(json.loads(FIXTURE.read_text(encoding="utf-8")))


def write_json(tmpdir, name, document):
    path = Path(tmpdir) / name
    path.write_text(json.dumps(document, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def run_validator(path, *args):
    return subprocess.run(
        [PYTHON, str(VALIDATOR), str(path), *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


class CliAndSchemaFirstTests(unittest.TestCase):
    def test_valid_fixture_exits_zero_and_prints_success_to_stdout(self):
        completed = run_validator(FIXTURE)
        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertIn("Validation succeeded", completed.stdout)
        self.assertEqual("", completed.stderr)

    def test_missing_file_exits_two_and_uses_stderr(self):
        completed = run_validator(ROOT / "missing.dsl.json")
        self.assertEqual(2, completed.returncode)
        self.assertEqual("", completed.stdout)
        self.assertIn("ERROR", completed.stderr)
        self.assertIn("file not found", completed.stderr)

    def test_invalid_json_exits_two_before_semantic_validation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "broken.dsl.json"
            path.write_text("{ not json", encoding="utf-8")
            completed = run_validator(path)
        self.assertEqual(2, completed.returncode)
        self.assertEqual("", completed.stdout)
        self.assertIn("ERROR", completed.stderr)
        self.assertIn("invalid JSON", completed.stderr)
        self.assertNotIn("semantic", completed.stderr)

    def test_schema_failure_exits_two_before_semantic_validation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            document["document"]["status"] = "almost-final"
            path = write_json(tmpdir, "schema-fail.dsl.json", document)
            completed = run_validator(path)
        self.assertEqual(2, completed.returncode)
        self.assertEqual("", completed.stdout)
        self.assertIn("ERROR", completed.stderr)
        self.assertIn("$.document.status", completed.stderr)
        self.assertIn("schema validation failed", completed.stderr)
        self.assertNotIn("semantic validation failed", completed.stderr)


class DocumentValidationTests(unittest.TestCase):
    def test_generic_output_filename_fails(self):
        for output_file in [
            "STRUCTURE_DESIGN.md",
            "structure_design.md",
            "design.md",
            "软件结构设计说明书.md",
            "software_STRUCTURE_DESIGN.md",
            "structure_STRUCTURE_DESIGN.md",
            "design_STRUCTURE_DESIGN.md",
        ]:
            with tempfile.TemporaryDirectory() as tmpdir:
                document = valid_document()
                document["document"]["output_file"] = output_file
                path = write_json(tmpdir, "generic.dsl.json", document)
                completed = run_validator(path)
            with self.subTest(output_file=output_file):
                self.assertEqual(1, completed.returncode)
                self.assertIn("$.document.output_file", completed.stderr)
                self.assertIn("generic-only output filename", completed.stderr)

    def test_concrete_output_filename_tied_to_documented_object_passes(self):
        for output_file in [
            "create-structure-md_STRUCTURE_DESIGN.md",
            "MOD-SKILL_STRUCTURE_DESIGN.md",
            "技能文档生成模块_STRUCTURE_DESIGN.md",
            "system_create-structure-md_STRUCTURE_DESIGN.md",
            "module_MOD-SKILL_STRUCTURE_DESIGN.md",
        ]:
            with tempfile.TemporaryDirectory() as tmpdir:
                document = valid_document()
                document["document"]["output_file"] = output_file
                path = write_json(tmpdir, "concrete.dsl.json", document)
                completed = run_validator(path)
            with self.subTest(output_file=output_file):
                self.assertEqual(0, completed.returncode, completed.stderr)
                self.assertIn("Validation succeeded", completed.stdout)

    def test_output_filename_without_concrete_documented_object_fails(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            document["document"]["output_file"] = "unrelated_SCOPE_STRUCTURE_DESIGN.md"
            path = write_json(tmpdir, "unrelated.dsl.json", document)
            completed = run_validator(path)
        self.assertEqual(1, completed.returncode)
        self.assertIn("$.document.output_file", completed.stderr)
        self.assertIn("must include a concrete documented object name", completed.stderr)

    def test_output_filename_with_spaces_warns_but_passes(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            document["document"]["output_file"] = "create structure md_STRUCTURE_DESIGN.md"
            path = write_json(tmpdir, "spaces.dsl.json", document)
            completed = run_validator(path)
        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertIn("WARNING", completed.stdout)
        self.assertIn("$.document.output_file", completed.stdout)
        self.assertIn("contains spaces", completed.stdout)
        self.assertIn("Validation succeeded", completed.stdout)

    def test_generated_at_loose_format_warns(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            document["document"]["generated_at"] = "May second"
            path = write_json(tmpdir, "generated-at.dsl.json", document)
            completed = run_validator(path)
        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertIn("$.document.generated_at", completed.stdout)
        self.assertIn("should use ISO-8601", completed.stdout)

    def test_empty_document_title_stops_at_schema_validation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            document["document"]["title"] = ""
            path = write_json(tmpdir, "empty-title.dsl.json", document)
            completed = run_validator(path)
        self.assertEqual(2, completed.returncode)
        self.assertIn("$.document.title", completed.stderr)
        self.assertIn("schema validation failed", completed.stderr)
        self.assertNotIn("semantic validation failed", completed.stderr)


class IdAndReferenceValidationTests(unittest.TestCase):
    def test_semantic_failure_exits_one_after_schema_success(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            document["architecture_views"]["module_intro"]["rows"][0]["module_id"] = "BAD-MODULE"
            path = write_json(tmpdir, "semantic-fail.dsl.json", document)
            completed = run_validator(path)
        self.assertEqual(1, completed.returncode)
        self.assertEqual("", completed.stdout)
        self.assertIn("ERROR", completed.stderr)
        self.assertIn("$.architecture_views.module_intro.rows[0].module_id", completed.stderr)
        self.assertIn("must start with MOD-", completed.stderr)

    def test_invalid_id_prefix_fails_without_requiring_numeric_suffix(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            document["architecture_views"]["module_intro"]["rows"][0]["module_id"] = "MODULE-SKILL"
            document["module_design"]["modules"][0]["module_id"] = "MODULE-SKILL"
            document["runtime_view"]["runtime_units"]["rows"][0]["related_module_ids"] = ["MODULE-SKILL"]
            document["key_flows"]["flow_index"]["rows"][0]["participant_module_ids"] = ["MODULE-SKILL"]
            document["key_flows"]["flows"][0]["related_module_ids"] = ["MODULE-SKILL"]
            document["key_flows"]["flows"][0]["steps"][0]["related_module_ids"] = ["MODULE-SKILL"]
            path = write_json(tmpdir, "bad-prefix.dsl.json", document)
            completed = run_validator(path)
        self.assertEqual(1, completed.returncode)
        self.assertIn("$.architecture_views.module_intro.rows[0].module_id", completed.stderr)
        self.assertIn("must start with MOD-", completed.stderr)

    def test_duplicate_defining_ids_fail(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            document["evidence"] = [
                {"id": "EV-DUP", "kind": "source", "title": "A", "location": "a", "description": "a", "confidence": "observed"},
                {"id": "EV-DUP", "kind": "note", "title": "B", "location": "b", "description": "b", "confidence": "observed"},
            ]
            path = write_json(tmpdir, "duplicate.dsl.json", document)
            completed = run_validator(path)
        self.assertEqual(1, completed.returncode)
        self.assertIn("$.evidence[1].id", completed.stderr)
        self.assertIn("duplicate ID", completed.stderr)

    def test_non_numeric_suffix_id_passes_when_unique(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            document["architecture_views"]["module_intro"]["rows"][0]["module_id"] = "MOD-RENDER-ALPHA"
            document["module_design"]["modules"][0]["module_id"] = "MOD-RENDER-ALPHA"
            document["runtime_view"]["runtime_units"]["rows"][0]["related_module_ids"] = ["MOD-RENDER-ALPHA"]
            document["cross_module_collaboration"]["collaboration_scenarios"]["rows"][0]["initiator_module_id"] = "MOD-RENDER-ALPHA"
            document["cross_module_collaboration"]["collaboration_scenarios"]["rows"][0]["participant_module_ids"] = ["MOD-RENDER-ALPHA"]
            document["key_flows"]["flow_index"]["rows"][0]["participant_module_ids"] = ["MOD-RENDER-ALPHA"]
            document["key_flows"]["flows"][0]["related_module_ids"] = ["MOD-RENDER-ALPHA"]
            document["key_flows"]["flows"][0]["steps"][0]["related_module_ids"] = ["MOD-RENDER-ALPHA"]
            document["key_flows"]["flows"][0]["branches_or_exceptions"][0]["related_module_ids"] = ["MOD-RENDER-ALPHA"]
            path = write_json(tmpdir, "non-numeric.dsl.json", document)
            completed = run_validator(path)
        self.assertEqual(0, completed.returncode, completed.stderr)

    def test_matching_flow_index_and_detail_ids_are_not_duplicate_ids(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            document["key_flows"]["flow_index"]["rows"][0]["flow_id"] = "FLOW-GENERATE"
            document["key_flows"]["flows"][0]["flow_id"] = "FLOW-GENERATE"
            path = write_json(tmpdir, "paired-flow.dsl.json", document)
            completed = run_validator(path)
        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertNotIn("duplicate ID FLOW-GENERATE", completed.stderr)

    def test_invalid_support_references_fail(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            document["architecture_views"]["module_intro"]["rows"][0]["evidence_refs"] = ["EV-MISSING"]
            path = write_json(tmpdir, "bad-ref.dsl.json", document)
            completed = run_validator(path)
        self.assertEqual(1, completed.returncode)
        self.assertIn("$.architecture_views.module_intro.rows[0].evidence_refs[0]", completed.stderr)
        self.assertIn("references unknown evidence ID EV-MISSING", completed.stderr)

    def test_registered_module_reference_must_resolve(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            document["runtime_view"]["runtime_units"]["rows"][0]["related_module_ids"] = ["MOD-MISSING"]
            path = write_json(tmpdir, "missing-module-ref.dsl.json", document)
            completed = run_validator(path)
        self.assertEqual(1, completed.returncode)
        self.assertIn("$.runtime_view.runtime_units.rows[0].related_module_ids[0]", completed.stderr)
        self.assertIn("references unknown module ID MOD-MISSING", completed.stderr)

    def test_module_design_module_id_must_reference_module_intro(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            document["module_design"]["modules"][0]["module_id"] = "MOD-MISSING"
            path = write_json(tmpdir, "missing-module-design-ref.dsl.json", document)
            completed = run_validator(path)
        self.assertEqual(1, completed.returncode)
        self.assertIn("$.module_design.modules[0].module_id", completed.stderr)
        self.assertIn("references unknown module ID MOD-MISSING", completed.stderr)

    def test_registered_runtime_unit_reference_must_resolve(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            document["key_flows"]["flow_index"]["rows"][0]["participant_runtime_unit_ids"] = ["RUN-MISSING"]
            path = write_json(tmpdir, "missing-runtime-ref.dsl.json", document)
            completed = run_validator(path)
        self.assertEqual(1, completed.returncode)
        self.assertIn("$.key_flows.flow_index.rows[0].participant_runtime_unit_ids[0]", completed.stderr)
        self.assertIn("references unknown runtime unit ID RUN-MISSING", completed.stderr)

    def test_extra_table_row_diagram_like_columns_are_plain_data(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            document["architecture_views"]["extra_tables"] = [
                {
                    "id": "TBL-ARCH-DIAGRAM-LIKE",
                    "title": "补充表",
                    "columns": [
                        {"key": "id", "title": "ID"},
                        {"key": "kind", "title": "类型"},
                        {"key": "diagram_type", "title": "图类型"},
                        {"key": "source", "title": "来源"},
                    ],
                    "rows": [
                        {
                            "id": "plain-row",
                            "kind": "note",
                            "diagram_type": "free text",
                            "source": "not a Mermaid diagram",
                        }
                    ],
                }
            ]
            path = write_json(tmpdir, "diagram-like-extra-row.dsl.json", document)
            completed = run_validator(path)
        self.assertEqual(0, completed.returncode, completed.stderr)

    def test_unregistered_id_field_fails(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            document["architecture_views"]["extra_tables"] = [
                {
                    "id": "TBL-ARCH-EXTRA",
                    "title": "补充表",
                    "columns": [{"key": "owner_module_id", "title": "归属模块"}],
                    "rows": [{"owner_module_id": "MOD-SKILL"}],
                }
            ]
            path = write_json(tmpdir, "unregistered-id.dsl.json", document)
            completed = run_validator(path)
        self.assertEqual(1, completed.returncode)
        self.assertIn("$.architecture_views.extra_tables[0].rows[0].owner_module_id", completed.stderr)
        self.assertIn("unregistered reference-like field", completed.stderr)

    def test_registered_reference_names_fail_when_used_at_unregistered_paths(self):
        for field_name in ["module_id", "target_id", "related_module_ids"]:
            with tempfile.TemporaryDirectory() as tmpdir:
                document = valid_document()
                document["architecture_views"]["extra_tables"] = [
                    {
                        "id": "TBL-ARCH-EXTRA",
                        "title": "补充表",
                        "columns": [{"key": field_name, "title": "非法引用字段"}],
                        "rows": [{field_name: "MOD-SKILL"}],
                    }
                ]
                path = write_json(tmpdir, "path-sensitive-id.dsl.json", document)
                completed = run_validator(path)
            with self.subTest(field_name=field_name):
                self.assertEqual(1, completed.returncode)
                self.assertIn(f"$.architecture_views.extra_tables[0].rows[0].{field_name}", completed.stderr)
                self.assertIn("unregistered reference-like field", completed.stderr)

    def test_traceability_source_external_id_is_allowed_at_traceability_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            document["traceability"] = [{
                "id": "TR-MODULE",
                "source_external_id": "REQ-1",
                "source_type": "requirement",
                "target_type": "module",
                "target_id": "MOD-SKILL",
                "description": "需求映射到模块。",
            }]
            path = write_json(tmpdir, "source-external.dsl.json", document)
            completed = run_validator(path)
        self.assertEqual(0, completed.returncode, completed.stderr)
