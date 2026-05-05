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
    def assert_markdown_contains(self, markdown, fragment):
        self.assertNotEqual(-1, markdown.find(fragment), f"Missing markdown fragment: {fragment}")

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

    def test_chapter_4_renders_content_blocks_through_shared_visible_contract(self):
        renderer = load_renderer_module()
        document = valid_document()
        document["structure_issues_and_suggestions"] = "Legacy Chapter 9 placeholder."
        markdown = renderer.render_markdown(document)

        self.assert_markdown_contains(markdown, "DSL 校验管线说明")
        self.assert_markdown_contains(markdown, 'A["DSL JSON"] --> B["Version gate"]')
        self.assert_markdown_contains(markdown, "DSL 校验管线图")
        self.assert_markdown_contains(markdown, "| 阶段 | 说明 |")

    def test_chapter_9_renders_content_blocks_through_shared_visible_contract(self):
        renderer = load_renderer_module()
        markdown = renderer.render_markdown(valid_document())

        self.assert_markdown_contains(markdown, "### 9.1 风险清单")
        self.assert_markdown_contains(markdown, "### 9.2 假设清单")
        self.assert_markdown_contains(markdown, "### 9.3 低置信度项目")
        self.assert_markdown_contains(markdown, "### 9.4 结构问题与改进建议")
        self.assert_markdown_contains(markdown, "结构问题概览")
        self.assert_markdown_contains(markdown, 'A["Prepared DSL"] --> B["Validation"]')
        self.assert_markdown_contains(markdown, "结构问题关系图")
        self.assert_markdown_contains(markdown, "| 问题 | 改进方向 |")

    def test_chapter_9_sections_render_in_fixed_order(self):
        renderer = load_renderer_module()
        markdown = renderer.render_markdown(valid_document())
        headings = [
            "### 9.1 风险清单",
            "### 9.2 假设清单",
            "### 9.3 低置信度项目",
            "### 9.4 结构问题与改进建议",
        ]
        positions = []
        for heading in headings:
            with self.subTest(heading=heading):
                position = markdown.find(heading)
                self.assertNotEqual(-1, position, f"Missing Chapter 9 heading: {heading}")
                positions.append(position)
        self.assertEqual(sorted(positions), positions)


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
