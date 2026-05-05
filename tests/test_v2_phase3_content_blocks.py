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
