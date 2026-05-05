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
