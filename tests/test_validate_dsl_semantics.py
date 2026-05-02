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


class ChapterTwoThroughSixTests(unittest.TestCase):
    def test_chapter_three_module_rows_must_be_non_empty_and_diagram_mentions_warn(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            document["architecture_views"]["module_intro"]["rows"] = []
            path = write_json(tmpdir, "no-modules.dsl.json", document)
            completed = run_validator(path)
        self.assertEqual(1, completed.returncode)
        self.assertIn("$.architecture_views.module_intro.rows", completed.stderr)
        self.assertIn("must contain at least one module", completed.stderr)

        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            document["architecture_views"]["module_relationship_diagram"]["source"] = "flowchart TD\n  A --> B"
            path = write_json(tmpdir, "diagram-warn.dsl.json", document)
            completed = run_validator(path)
        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertIn("WARNING", completed.stdout)
        self.assertIn("does not mention module MOD-SKILL", completed.stdout)

    def test_chapter_four_modules_match_chapter_three_one_to_one(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            document["module_design"]["modules"][0]["module_id"] = "MOD-OTHER"
            path = write_json(tmpdir, "module-mismatch.dsl.json", document)
            completed = run_validator(path)
        self.assertEqual(1, completed.returncode)
        self.assertIn("$.module_design.modules", completed.stderr)
        self.assertIn("must match chapter 3 modules one-to-one", completed.stderr)

    def test_internal_structure_requires_diagram_source_or_text(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            internal = document["module_design"]["modules"][0]["internal_structure"]
            internal["diagram"]["source"] = ""
            internal["textual_structure"] = ""
            internal["not_applicable_reason"] = "使用文字说明"
            path = write_json(tmpdir, "internal-empty.dsl.json", document)
            completed = run_validator(path)
        self.assertEqual(1, completed.returncode)
        self.assertIn("$.module_design.modules[0].internal_structure", completed.stderr)
        self.assertIn("requires diagram source or textual_structure", completed.stderr)

    def test_runtime_entrypoint_and_related_modules_empty_reasons(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            unit = document["runtime_view"]["runtime_units"]["rows"][0]
            unit["entrypoint"] = ""
            unit["entrypoint_not_applicable_reason"] = ""
            unit["related_module_ids"] = []
            unit["external_environment_reason"] = ""
            path = write_json(tmpdir, "runtime-reasons.dsl.json", document)
            completed = run_validator(path)
        self.assertEqual(1, completed.returncode)
        self.assertIn("$.runtime_view.runtime_units.rows[0].entrypoint_not_applicable_reason", completed.stderr)
        self.assertIn("$.runtime_view.runtime_units.rows[0].external_environment_reason", completed.stderr)

    def test_required_diagrams_and_optional_extra_diagrams_need_source(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            document["runtime_view"]["runtime_flow_diagram"]["source"] = ""
            document["architecture_views"]["extra_diagrams"] = [
                {
                    "id": "MER-ARCH-EMPTY",
                    "kind": "extra",
                    "title": "空图",
                    "diagram_type": "flowchart",
                    "description": "补充图",
                    "source": "",
                    "confidence": "observed",
                }
            ]
            path = write_json(tmpdir, "diagrams-empty.dsl.json", document)
            completed = run_validator(path)
        self.assertEqual(1, completed.returncode)
        self.assertIn("$.runtime_view.runtime_flow_diagram.source", completed.stderr)
        self.assertIn("$.architecture_views.extra_diagrams[0].source", completed.stderr)

    def test_runtime_sequence_diagram_must_use_sequence_diagram_when_present(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            document["runtime_view"]["runtime_sequence_diagram"] = {
                "id": "MER-RUNTIME-SEQ",
                "kind": "runtime_sequence",
                "title": "运行时序列图",
                "diagram_type": "flowchart",
                "description": "错误类型",
                "source": "flowchart TD\n  A --> B",
                "confidence": "observed",
            }
            path = write_json(tmpdir, "runtime-sequence.dsl.json", document)
            completed = run_validator(path)
        self.assertEqual(1, completed.returncode)
        self.assertIn("$.runtime_view.runtime_sequence_diagram.source", completed.stderr)
        self.assertIn("must use sequenceDiagram", completed.stderr)


class ChapterSevenAndEightTests(unittest.TestCase):
    def make_two_module_document(self):
        document = valid_document()
        document["architecture_views"]["module_intro"]["rows"].append({
            "module_id": "MOD-RENDER",
            "module_name": "渲染模块",
            "responsibility": "生成 Markdown。",
            "inputs": "DSL",
            "outputs": "Markdown",
            "notes": "",
            "confidence": "observed",
            "evidence_refs": [],
            "traceability_refs": [],
            "source_snippet_refs": [],
        })
        second = deepcopy(document["module_design"]["modules"][0])
        second["module_id"] = "MOD-RENDER"
        second["name"] = "渲染模块"
        second["external_capability_details"]["provided_capabilities"]["rows"][0]["capability_id"] = "CAP-RENDER"
        second["internal_structure"]["diagram"]["id"] = "MER-MOD-RENDER-STRUCT"
        document["module_design"]["modules"].append(second)
        document["architecture_views"]["module_relationship_diagram"]["source"] += "\n  MOD-SKILL --> MOD-RENDER"
        return document

    def test_single_module_chapter_7_allows_empty_collaboration(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            document["cross_module_collaboration"]["summary"] = ""
            document["cross_module_collaboration"]["collaboration_scenarios"]["rows"] = []
            document["cross_module_collaboration"].pop("collaboration_relationship_diagram", None)
            path = write_json(tmpdir, "single-module.dsl.json", document)
            completed = run_validator(path)
        self.assertEqual(0, completed.returncode, completed.stderr)

    def test_single_module_chapter_7_allows_empty_full_diagram_object(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            document["cross_module_collaboration"]["summary"] = ""
            document["cross_module_collaboration"]["collaboration_scenarios"]["rows"] = []
            document["cross_module_collaboration"]["collaboration_relationship_diagram"] = {
                "id": "MER-COLLAB-EMPTY",
                "kind": "collaboration_relationship",
                "title": "空协作图",
                "diagram_type": "flowchart",
                "description": "单模块模式允许协作图为空。",
                "source": "",
                "confidence": "observed",
            }
            path = write_json(tmpdir, "single-empty-diagram.dsl.json", document)
            completed = run_validator(path)
        self.assertEqual(0, completed.returncode, completed.stderr)

    def test_multi_module_chapter_7_requires_summary_rows_and_diagram(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            document = self.make_two_module_document()
            document["cross_module_collaboration"]["summary"] = ""
            document["cross_module_collaboration"]["collaboration_scenarios"]["rows"] = []
            document["cross_module_collaboration"].pop("collaboration_relationship_diagram", None)
            path = write_json(tmpdir, "multi-empty.dsl.json", document)
            completed = run_validator(path)
        self.assertEqual(1, completed.returncode)
        self.assertIn("$.cross_module_collaboration.summary", completed.stderr)
        self.assertIn("$.cross_module_collaboration.collaboration_scenarios.rows", completed.stderr)
        self.assertIn("$.cross_module_collaboration.collaboration_relationship_diagram", completed.stderr)

    def test_single_module_chapter_7_validates_provided_content(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            document["cross_module_collaboration"]["collaboration_scenarios"]["rows"] = [{
                "collaboration_id": "COL-BAD-REF",
                "scenario": "可选协作内容",
                "initiator_module_id": "MOD-MISSING",
                "participant_module_ids": ["MOD-SKILL"],
                "collaboration_method": "调用",
                "description": "单模块模式中提供的内容仍需校验引用。",
                "confidence": "observed",
                "evidence_refs": [],
                "traceability_refs": [],
                "source_snippet_refs": [],
            }]
            path = write_json(tmpdir, "single-invalid-collab.dsl.json", document)
            completed = run_validator(path)
        self.assertEqual(1, completed.returncode)
        self.assertIn("$.cross_module_collaboration.collaboration_scenarios.rows[0].initiator_module_id", completed.stderr)
        self.assertNotIn("$.cross_module_collaboration.collaboration_relationship_diagram.source", completed.stderr)

    def test_multi_module_collaboration_must_involve_two_distinct_modules(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            document = self.make_two_module_document()
            document["cross_module_collaboration"]["summary"] = "模块协作。"
            document["cross_module_collaboration"]["collaboration_scenarios"]["rows"] = [{
                "collaboration_id": "COL-ONE",
                "scenario": "单模块自调用",
                "initiator_module_id": "MOD-SKILL",
                "participant_module_ids": ["MOD-SKILL"],
                "collaboration_method": "调用",
                "description": "只有一个模块。",
                "confidence": "observed",
                "evidence_refs": [],
                "traceability_refs": [],
                "source_snippet_refs": [],
            }]
            document["cross_module_collaboration"]["collaboration_relationship_diagram"] = {
                "id": "MER-COLLAB-TWO",
                "kind": "collaboration_relationship",
                "title": "协作图",
                "diagram_type": "flowchart",
                "description": "协作",
                "source": "flowchart TD\n  MOD-SKILL --> MOD-RENDER",
                "confidence": "observed",
            }
            path = write_json(tmpdir, "collab-one.dsl.json", document)
            completed = run_validator(path)
        self.assertEqual(1, completed.returncode)
        self.assertIn("$.cross_module_collaboration.collaboration_scenarios.rows[0]", completed.stderr)
        self.assertIn("at least two distinct modules", completed.stderr)

    def test_flow_index_and_detail_must_match_one_to_one(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            document["key_flows"]["flows"][0]["flow_id"] = "FLOW-DETAIL-ONLY"
            path = write_json(tmpdir, "flow-mismatch.dsl.json", document)
            completed = run_validator(path)
        self.assertEqual(1, completed.returncode)
        self.assertIn("$.key_flows", completed.stderr)
        self.assertIn("flow_index rows and flow details must match one-to-one", completed.stderr)

    def test_flow_participants_and_steps_have_reference_and_uniqueness_rules(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            document["key_flows"]["flow_index"]["rows"][0]["participant_module_ids"] = []
            document["key_flows"]["flow_index"]["rows"][0]["participant_runtime_unit_ids"] = []
            document["key_flows"]["flows"][0]["steps"].append(deepcopy(document["key_flows"]["flows"][0]["steps"][0]))
            document["key_flows"]["flows"][0]["steps"][1]["order"] = 1
            document["key_flows"]["flows"][0]["branches_or_exceptions"] = [
                {
                    "branch_id": "BR-DUP",
                    "condition": "条件 A",
                    "handling": "处理 A",
                    "related_module_ids": ["MOD-SKILL"],
                    "related_runtime_unit_ids": ["RUN-GENERATE"],
                    "confidence": "observed",
                    "evidence_refs": [],
                    "traceability_refs": [],
                    "source_snippet_refs": [],
                },
                {
                    "branch_id": "BR-DUP",
                    "condition": "条件 B",
                    "handling": "处理 B",
                    "related_module_ids": ["MOD-SKILL"],
                    "related_runtime_unit_ids": ["RUN-GENERATE"],
                    "confidence": "observed",
                    "evidence_refs": [],
                    "traceability_refs": [],
                    "source_snippet_refs": [],
                },
            ]
            path = write_json(tmpdir, "flow-rules.dsl.json", document)
            completed = run_validator(path)
        self.assertEqual(1, completed.returncode)
        self.assertIn("$.key_flows.flow_index.rows[0]", completed.stderr)
        self.assertIn("must have at least one participant", completed.stderr)
        self.assertIn("duplicate ID", completed.stderr)
        self.assertIn("step order values must be unique", completed.stderr)


class ExtraTableAndTraceabilityTests(unittest.TestCase):
    def test_extra_table_rows_reject_unknown_keys_but_allow_missing_declared_keys(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            document["architecture_views"]["extra_tables"] = [{
                "id": "TBL-ARCH-001",
                "title": "补充表",
                "columns": [{"key": "name", "title": "名称"}, {"key": "role", "title": "角色"}],
                "rows": [{"name": "A", "extra": "B", "evidence_refs": []}],
            }]
            path = write_json(tmpdir, "extra-table.dsl.json", document)
            completed = run_validator(path)
        self.assertEqual(1, completed.returncode)
        self.assertIn("$.architecture_views.extra_tables[0].rows[0]", completed.stderr)
        self.assertIn("row contains keys outside declared columns", completed.stderr)

        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            document["architecture_views"]["extra_tables"] = [{
                "id": "TBL-ARCH-002",
                "title": "补充表",
                "columns": [{"key": "name", "title": "名称"}, {"key": "role", "title": "角色"}],
                "rows": [{"name": "A"}],
            }]
            path = write_json(tmpdir, "extra-table-missing-ok.dsl.json", document)
            completed = run_validator(path)
        self.assertEqual(0, completed.returncode, completed.stderr)

    def test_extra_table_duplicate_column_keys_fail(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            document["architecture_views"]["extra_tables"] = [{
                "id": "TBL-ARCH-DUP",
                "title": "补充表",
                "columns": [{"key": "name", "title": "名称"}, {"key": "name", "title": "重复名称"}],
                "rows": [{"name": "A"}],
            }]
            path = write_json(tmpdir, "extra-table-duplicate.dsl.json", document)
            completed = run_validator(path)
        self.assertEqual(1, completed.returncode)
        self.assertIn("$.architecture_views.extra_tables[0].columns[1].key", completed.stderr)
        self.assertIn("duplicate extra table column key", completed.stderr)

    def test_extra_table_rows_can_use_object_shape_keys_as_plain_data(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            document["architecture_views"]["extra_tables"] = [{
                "id": "TBL-ARCH-SHAPE-KEYS",
                "title": "补充表",
                "columns": [
                    {"key": "id", "title": "ID"},
                    {"key": "title", "title": "标题"},
                    {"key": "columns", "title": "列"},
                    {"key": "rows", "title": "行"},
                ],
                "rows": [{
                    "id": "plain-row",
                    "title": "普通行",
                    "columns": "ordinary column data",
                    "rows": "ordinary row data",
                }],
            }]
            path = write_json(tmpdir, "extra-table-shape-keys.dsl.json", document)
            completed = run_validator(path)
        self.assertEqual(0, completed.returncode, completed.stderr)

    def test_traceability_target_id_must_resolve_by_target_type(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            document["traceability"] = [{
                "id": "TR-MISSING",
                "source_external_id": "REQ-1",
                "source_type": "requirement",
                "target_type": "module",
                "target_id": "MOD-MISSING",
                "description": "错误映射",
            }]
            path = write_json(tmpdir, "trace-missing.dsl.json", document)
            completed = run_validator(path)
        self.assertEqual(1, completed.returncode)
        self.assertIn("$.traceability[0].target_id", completed.stderr)
        self.assertIn("does not resolve for target_type module", completed.stderr)

    def test_local_traceability_backlink_must_target_current_node(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            document["traceability"] = [{
                "id": "TR-MODULE",
                "source_external_id": "REQ-1",
                "source_type": "requirement",
                "target_type": "module",
                "target_id": "MOD-SKILL",
                "description": "模块追踪",
            }]
            document["runtime_view"]["runtime_units"]["rows"][0]["traceability_refs"] = ["TR-MODULE"]
            path = write_json(tmpdir, "trace-backlink.dsl.json", document)
            completed = run_validator(path)
        self.assertEqual(1, completed.returncode)
        self.assertIn("$.runtime_view.runtime_units.rows[0].traceability_refs[0]", completed.stderr)
        self.assertIn("targets module MOD-SKILL instead of runtime_unit", completed.stderr)

    def test_valid_local_traceability_backlink_passes(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            document["traceability"] = [{
                "id": "TR-RUNTIME",
                "source_external_id": "REQ-2",
                "source_type": "requirement",
                "target_type": "runtime_unit",
                "target_id": "RUN-GENERATE",
                "description": "运行单元追踪",
            }]
            document["runtime_view"]["runtime_units"]["rows"][0]["traceability_refs"] = ["TR-RUNTIME"]
            path = write_json(tmpdir, "trace-valid-backlink.dsl.json", document)
            completed = run_validator(path)
        self.assertEqual(0, completed.returncode, completed.stderr)

    def test_traceability_flow_branch_target_resolves(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            document["key_flows"]["flows"][0]["branches_or_exceptions"] = [{
                "branch_id": "BR-GENERATE-001",
                "condition": "DSL 校验失败",
                "handling": "停止渲染并报告结构问题。",
                "related_module_ids": ["MOD-SKILL"],
                "related_runtime_unit_ids": ["RUN-GENERATE"],
                "confidence": "observed",
                "evidence_refs": [],
                "traceability_refs": ["TR-BRANCH"],
                "source_snippet_refs": [],
            }]
            document["traceability"] = [{
                "id": "TR-BRANCH",
                "source_external_id": "REQ-BRANCH",
                "source_type": "requirement",
                "target_type": "flow_branch",
                "target_id": "BR-GENERATE-001",
                "description": "分支追踪",
            }]
            path = write_json(tmpdir, "trace-flow-branch.dsl.json", document)
            completed = run_validator(path)
        self.assertEqual(0, completed.returncode, completed.stderr)

    def test_unreferenced_evidence_warns(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            document["evidence"] = [{
                "id": "EV-UNUSED",
                "kind": "note",
                "title": "未使用证据",
                "location": "notes",
                "description": "没有被引用。",
                "confidence": "observed",
            }]
            path = write_json(tmpdir, "unused-evidence.dsl.json", document)
            completed = run_validator(path)
        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertIn("WARNING", completed.stdout)
        self.assertIn("$.evidence[0].id", completed.stdout)
        self.assertIn("unreferenced evidence", completed.stdout)


class SourceSnippetValidationTests(unittest.TestCase):
    def test_line_range_must_be_valid(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            document["source_snippets"] = [{
                "id": "SNIP-BAD-RANGE",
                "path": "scripts/validate_dsl.py",
                "line_start": 10,
                "line_end": 5,
                "language": "python",
                "purpose": "错误范围",
                "content": "line\n",
                "confidence": "observed",
            }]
            document["module_design"]["modules"][0]["source_snippet_refs"] = ["SNIP-BAD-RANGE"]
            path = write_json(tmpdir, "snippet-range.dsl.json", document)
            completed = run_validator(path)
        self.assertEqual(1, completed.returncode)
        self.assertIn("$.source_snippets[0].line_end", completed.stderr)
        self.assertIn("must be greater than or equal to line_start", completed.stderr)

    def test_unreferenced_source_snippet_fails(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            document["source_snippets"] = [{
                "id": "SNIP-UNUSED",
                "path": "scripts/validate_dsl.py",
                "line_start": 1,
                "line_end": 1,
                "language": "python",
                "purpose": "未引用",
                "content": "print('x')\n",
                "confidence": "observed",
            }]
            path = write_json(tmpdir, "snippet-unused.dsl.json", document)
            completed = run_validator(path)
        self.assertEqual(1, completed.returncode)
        self.assertIn("$.source_snippets[0].id", completed.stderr)
        self.assertIn("unreferenced source snippet", completed.stderr)

    def test_snippet_longer_than_twenty_warns_and_longer_than_fifty_fails_by_default(self):
        content_25 = "\n".join(f"line {i}" for i in range(25))
        content_55 = "\n".join(f"line {i}" for i in range(55))
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            document["source_snippets"] = [{
                "id": "SNIP-LONG-WARN",
                "path": "a.py",
                "line_start": 1,
                "line_end": 25,
                "language": "python",
                "purpose": "稍长片段",
                "content": content_25,
                "confidence": "observed",
            }]
            document["module_design"]["modules"][0]["source_snippet_refs"] = ["SNIP-LONG-WARN"]
            path = write_json(tmpdir, "snippet-25.dsl.json", document)
            completed = run_validator(path)
        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertIn("WARNING", completed.stdout)
        self.assertIn("longer than 20 lines", completed.stdout)

        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            document["source_snippets"] = [{
                "id": "SNIP-LONG-FAIL",
                "path": "a.py",
                "line_start": 1,
                "line_end": 55,
                "language": "python",
                "purpose": "过长片段",
                "content": content_55,
                "confidence": "observed",
            }]
            document["module_design"]["modules"][0]["source_snippet_refs"] = ["SNIP-LONG-FAIL"]
            path = write_json(tmpdir, "snippet-55.dsl.json", document)
            completed = run_validator(path)
            allowed_completed = run_validator(path, "--allow-long-snippets")
        self.assertEqual(1, completed.returncode)
        self.assertIn("longer than 50 lines", completed.stderr)

        self.assertEqual(0, allowed_completed.returncode, allowed_completed.stderr)
        self.assertIn("longer than 50 lines", allowed_completed.stdout)

    def test_secret_and_personal_data_patterns_fail(self):
        cases = [
            "AWS_SECRET_ACCESS_KEY=AKIAIOSFODNN7EXAMPLE",
            "password = \"super-secret\"",
            "-----BEGIN PRIVATE KEY-----",
            "email: person@example.com",
            "phone: 13800138000",
        ]
        for content in cases:
            with tempfile.TemporaryDirectory() as tmpdir:
                document = valid_document()
                document["source_snippets"] = [{
                    "id": "SNIP-SECRET",
                    "path": "secret.txt",
                    "line_start": 1,
                    "line_end": 1,
                    "language": "text",
                    "purpose": "敏感内容",
                    "content": content,
                    "confidence": "observed",
                }]
                document["module_design"]["modules"][0]["source_snippet_refs"] = ["SNIP-SECRET"]
                path = write_json(tmpdir, "snippet-secret.dsl.json", document)
                completed = run_validator(path)
            with self.subTest(content=content):
                self.assertEqual(1, completed.returncode)
                self.assertIn("$.source_snippets[0].content", completed.stderr)
                self.assertIn("high-risk secret or personal data pattern", completed.stderr)


class MarkdownSafetyAndLowConfidenceTests(unittest.TestCase):
    def test_chapter_nine_rejects_headings_tables_fences_html_and_graphs(self):
        cases = [
            "# 标题",
            "| A | B |\n|---|---|",
            "```mermaid\nflowchart TD\n```",
            "```python\nprint('x')",
            "<div>raw</div>",
            "<p>raw</p>",
            "<!-- raw comment -->",
            "graph TD\n  A-->B",
        ]
        for content in cases:
            with tempfile.TemporaryDirectory() as tmpdir:
                document = valid_document()
                document["structure_issues_and_suggestions"] = content
                path = write_json(tmpdir, "chapter9.dsl.json", document)
                completed = run_validator(path)
            with self.subTest(content=content):
                self.assertEqual(1, completed.returncode)
                self.assertIn("$.structure_issues_and_suggestions", completed.stderr)
                self.assertIn("unsafe Markdown structure", completed.stderr)

    def test_chapter_nine_unsafe_content_reports_once(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            document["structure_issues_and_suggestions"] = "# 标题"
            path = write_json(tmpdir, "chapter9-once.dsl.json", document)
            completed = run_validator(path)
        self.assertEqual(1, completed.returncode)
        self.assertEqual(1, completed.stderr.count("$.structure_issues_and_suggestions"))
        self.assertEqual(1, completed.stderr.count("unsafe Markdown structure"))

    def test_design_text_rejects_prototypes_and_definition_like_lines_outside_snippets(self):
        cases = [
            ("system_overview", "summary", "int main(void);"),
            ("system_overview", "summary", "def build_plan():"),
            ("system_overview", "summary", "class Renderer:"),
            ("system_overview", "summary", "typedef struct Config Config;"),
        ]
        for section, field, value in cases:
            with tempfile.TemporaryDirectory() as tmpdir:
                document = valid_document()
                document[section][field] = value
                path = write_json(tmpdir, "prototype.dsl.json", document)
                completed = run_validator(path)
            with self.subTest(value=value):
                self.assertEqual(1, completed.returncode)
                self.assertIn(f"$.{section}.{field}", completed.stderr)
                self.assertIn("prototype/detail-design content", completed.stderr)

    def test_design_text_allows_normal_prose_with_parentheticals(self):
        cases = [
            "Use standard input (stdin)",
            "Returns rendered output (Markdown)",
        ]
        for value in cases:
            with tempfile.TemporaryDirectory() as tmpdir:
                document = valid_document()
                document["system_overview"]["summary"] = value
                path = write_json(tmpdir, "parenthetical-prose.dsl.json", document)
                completed = run_validator(path)
            with self.subTest(value=value):
                self.assertEqual(0, completed.returncode, completed.stderr)

    def test_plain_text_fields_reject_markdown_structure_outside_chapter_nine(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            document["system_overview"]["summary"] = "# 注入标题"
            path = write_json(tmpdir, "plain-markdown.dsl.json", document)
            completed = run_validator(path)
        self.assertEqual(1, completed.returncode)
        self.assertIn("$.system_overview.summary", completed.stderr)
        self.assertIn("unsafe Markdown structure", completed.stderr)

    def test_plain_text_source_fields_reject_markdown_structure(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            document["configuration_data_dependencies"]["configuration_items"]["rows"][0]["source"] = "# injected"
            path = write_json(tmpdir, "plain-source-markdown.dsl.json", document)
            completed = run_validator(path)
        self.assertEqual(1, completed.returncode)
        self.assertIn("$.configuration_data_dependencies.configuration_items.rows[0].source", completed.stderr)
        self.assertIn("unsafe Markdown structure", completed.stderr)

    def test_extra_table_nested_diagram_source_is_plain_text_linted(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            document["architecture_views"]["extra_tables"] = [{
                "id": "TBL-ARCH-DIAGRAM-SOURCE",
                "title": "嵌套图字段",
                "columns": [{"key": "diagram", "title": "图"}],
                "rows": [{"diagram": {"source": "# injected heading"}}],
            }]
            path = write_json(tmpdir, "extra-table-nested-diagram-source.dsl.json", document)
            completed = run_validator(path)
        self.assertEqual(1, completed.returncode)
        self.assertIn("$.architecture_views.extra_tables[0].rows[0].diagram.source", completed.stderr)
        self.assertIn("unsafe Markdown structure", completed.stderr)

    def test_extra_table_content_and_diagram_type_fields_are_plain_text_linted(self):
        for field_name in ["content", "diagram_type"]:
            with tempfile.TemporaryDirectory() as tmpdir:
                document = valid_document()
                document["architecture_views"]["extra_tables"] = [{
                    "id": "TBL-ARCH-EXEMPT-NAME",
                    "title": "保留字段名",
                    "columns": [{"key": field_name, "title": "字段"}],
                    "rows": [{field_name: "# injected heading"}],
                }]
                path = write_json(tmpdir, "extra-table-exempt-name.dsl.json", document)
                completed = run_validator(path)
            with self.subTest(field_name=field_name):
                self.assertEqual(1, completed.returncode)
                self.assertIn(f"$.architecture_views.extra_tables[0].rows[0].{field_name}", completed.stderr)
                self.assertIn("unsafe Markdown structure", completed.stderr)

    def test_plain_text_fields_reject_large_code_like_blocks(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            document["system_overview"]["summary"] = "\n".join([
                "if ready:",
                "    validate()",
                "    render()",
                "    report()",
                "else:",
                "    raise RuntimeError('not ready')",
            ])
            path = write_json(tmpdir, "plain-code-block.dsl.json", document)
            completed = run_validator(path)
        self.assertEqual(1, completed.returncode)
        self.assertIn("$.system_overview.summary", completed.stderr)
        self.assertIn("large code-like block", completed.stderr)

    def test_mermaid_source_rejects_fenced_markdown(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            document["architecture_views"]["module_relationship_diagram"]["source"] = "```mermaid\nflowchart TD\n  A --> B\n```"
            path = write_json(tmpdir, "fenced-mermaid.dsl.json", document)
            completed = run_validator(path)
        self.assertEqual(1, completed.returncode)
        self.assertIn("$.architecture_views.module_relationship_diagram.source", completed.stderr)
        self.assertIn("must not include Markdown fences", completed.stderr)

    def test_low_confidence_whitelist_warns_and_suggests_chapter_nine_coverage(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            document["architecture_views"]["module_intro"]["rows"][0]["confidence"] = "unknown"
            document["module_design"]["modules"][0]["external_capability_details"]["provided_capabilities"]["rows"][0]["confidence"] = "unknown"
            document["evidence"] = [{
                "id": "EV-UNKNOWN",
                "kind": "note",
                "title": "未知证据",
                "location": "note",
                "description": "support data 不应进入低置信度集合。",
                "confidence": "unknown",
            }]
            document["architecture_views"]["module_intro"]["rows"][0]["evidence_refs"] = ["EV-UNKNOWN"]
            path = write_json(tmpdir, "low-confidence.dsl.json", document)
            completed = run_validator(path)
        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertIn("WARNING", completed.stdout)
        self.assertIn("low-confidence item", completed.stdout)
        self.assertIn("$.architecture_views.module_intro.rows[0]", completed.stdout)
        self.assertIn("$.module_design.modules[0].external_capability_details.provided_capabilities.rows[0]", completed.stdout)
        self.assertNotIn("$.evidence[0]", completed.stdout)
        self.assertIn("Summarize in chapter 9", completed.stdout)

    def test_unknown_unreferenced_evidence_still_warns(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            document["evidence"] = [{
                "id": "EV-UNKNOWN",
                "kind": "note",
                "title": "未知证据",
                "location": "note",
                "description": "未知置信度证据仍然需要被引用。",
                "confidence": "unknown",
            }]
            path = write_json(tmpdir, "unknown-unreferenced-evidence.dsl.json", document)
            completed = run_validator(path)
        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertIn("WARNING", completed.stdout)
        self.assertIn("$.evidence[0].id", completed.stdout)
        self.assertIn("unreferenced evidence", completed.stdout)
