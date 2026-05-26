import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.helpers_v030 import write_valid_package

from scripts.v030_package import load_manifest_package
from scripts.v030_schema import schema_validation_result


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable


class V030ChapterSchemaTests(unittest.TestCase):
    def test_complete_minimal_package_passes_schema_validation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            package = load_manifest_package(write_valid_package(tmpdir))
            result = schema_validation_result(package)
        self.assertTrue(result.ok, [issue.format() for issue in result.errors])

    def test_single_path_chapter_key_must_match_manifest_property(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = write_valid_package(tmpdir)
            package = load_manifest_package(manifest_path)
            package.chapters["document"]["chapter"]["key"] = "directory_map"
            result = schema_validation_result(package)
        self.assertFalse(result.ok)
        self.assertTrue(any("chapter.key must match manifest property" in issue.message for issue in result.errors))

    def test_mechanism_file_must_not_have_chapter_header(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = write_valid_package(tmpdir)
            package = load_manifest_package(manifest_path)
            package.mechanisms[0].data["chapter"] = {"key": "key_mechanisms", "title": "关键机制深读"}
            result = schema_validation_result(package)
        self.assertFalse(result.ok)
        self.assertTrue(any("Mechanism JSON files must not contain chapter" in issue.message for issue in result.errors))

    def test_document_language_is_zh_cn_only(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = write_valid_package(tmpdir)
            package = load_manifest_package(manifest_path)
            package.chapters["document"]["document"]["language"] = "en-US"
            result = schema_validation_result(package)
        self.assertFalse(result.ok)
        self.assertTrue(any("zh-CN" in issue.message for issue in result.errors))

    def test_fixed_chapter_title_must_match_contract(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = write_valid_package(tmpdir)
            package = load_manifest_package(manifest_path)
            package.chapters["repository_overview"]["chapter"]["title"] = "仓库简介"
            result = schema_validation_result(package)
        self.assertFalse(result.ok)
        self.assertTrue(any("仓库概述与阅读路线" in issue.message for issue in result.errors))

    def test_extra_fields_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = write_valid_package(tmpdir)
            package = load_manifest_package(manifest_path)
            package.chapters["module_layers"]["modules"][0]["public_interfaces"] = []
            result = schema_validation_result(package)
        self.assertFalse(result.ok)
        self.assertTrue(any("Additional properties are not allowed" in issue.message for issue in result.errors))

    def test_path_segments_must_not_be_dot_or_dotdot(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = write_valid_package(tmpdir)
            package = load_manifest_package(manifest_path)
            package.chapters["directory_map"]["directory_groups"][0]["paths"] = ["src/."]
            result = schema_validation_result(package)
        self.assertFalse(result.ok)

        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = write_valid_package(tmpdir)
            package = load_manifest_package(manifest_path)
            package.chapters["directory_map"]["directory_groups"][0]["paths"] = ["src/.."]
            result = schema_validation_result(package)
        self.assertFalse(result.ok)

    def test_mainline_diagram_type_constraints_are_contextual(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = write_valid_package(tmpdir)
            package = load_manifest_package(manifest_path)
            package.chapters["repository_mainline"]["mainline_overview_diagram"]["diagram_type"] = "sequenceDiagram"
            result = schema_validation_result(package)
        self.assertFalse(result.ok)

    def test_cli_schema_error_does_not_fall_through_to_semantic_traceback(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = write_valid_package(tmpdir)
            module_layers = Path(tmpdir) / "chapters/04-module-layers.json"
            data = json.loads(module_layers.read_text(encoding="utf-8"))
            del data["modules"]
            module_layers.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            completed = subprocess.run(
                [PYTHON, str(ROOT / "scripts/validate_structure.py"), str(manifest_path)],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(2, completed.returncode)
        self.assertIn("modules", completed.stderr)
        self.assertNotIn("Traceback", completed.stderr)

    def test_cli_non_object_chapter_root_reports_schema_error_without_traceback(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = write_valid_package(tmpdir)
            document = Path(tmpdir) / "chapters/01-document.json"
            document.write_text("[]", encoding="utf-8")
            completed = subprocess.run(
                [PYTHON, str(ROOT / "scripts/validate_structure.py"), str(manifest_path)],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(2, completed.returncode)
        self.assertIn("object", completed.stderr)
        self.assertNotIn("Traceback", completed.stderr)

    def test_cli_non_object_chapter_header_reports_schema_error_without_traceback(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = write_valid_package(tmpdir)
            document = Path(tmpdir) / "chapters/01-document.json"
            data = json.loads(document.read_text(encoding="utf-8"))
            data["chapter"] = []
            document.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            completed = subprocess.run(
                [PYTHON, str(ROOT / "scripts/validate_structure.py"), str(manifest_path)],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(2, completed.returncode)
        self.assertIn("chapter", completed.stderr)
        self.assertIn("object", completed.stderr)
        self.assertNotIn("Traceback", completed.stderr)

    def test_cli_non_object_mechanism_root_reports_schema_error_without_traceback(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = write_valid_package(tmpdir)
            mechanism = Path(tmpdir) / "chapters/06-key-mechanisms/persistence.json"
            mechanism.write_text("1", encoding="utf-8")
            completed = subprocess.run(
                [PYTHON, str(ROOT / "scripts/validate_structure.py"), str(manifest_path)],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(2, completed.returncode)
        self.assertIn("object", completed.stderr)
        self.assertNotIn("Traceback", completed.stderr)

    def test_mainline_detail_diagram_rejects_state_diagram(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = write_valid_package(tmpdir)
            package = load_manifest_package(manifest_path)
            package.chapters["repository_mainline"]["mainlines"][0]["detail_diagram"] = {
                "id": "bad_detail",
                "title": "状态细节",
                "diagram_type": "stateDiagram-v2",
                "description": "不允许的主线细节图类型。",
                "source": "stateDiagram-v2\n  [*] --> Ready",
            }
            result = schema_validation_result(package)
        self.assertFalse(result.ok)
