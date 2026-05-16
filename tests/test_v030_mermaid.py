import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.helpers_v030 import write_valid_package

from scripts.v030_mermaid import mermaid_validation_result
from scripts.v030_package import load_manifest_package


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable


class V030MermaidTests(unittest.TestCase):
    def test_diagram_type_must_match_first_source_token(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            package = load_manifest_package(write_valid_package(tmpdir))
            package.chapters["repository_mainline"]["mainline_overview_diagram"]["source"] = "sequenceDiagram\n  A->>B: hi"
            result = mermaid_validation_result(package)
        self.assertFalse(result.ok)
        self.assertTrue(any("diagram_type does not match Mermaid declaration" in issue.message for issue in result.errors))

    def test_legacy_graph_declaration_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            package = load_manifest_package(write_valid_package(tmpdir))
            package.chapters["repository_mainline"]["mainline_overview_diagram"]["source"] = "graph TD\n  a[开始] --> b[结束]"
            result = mermaid_validation_result(package)
        self.assertFalse(result.ok)
        self.assertTrue(any("Legacy graph declarations are not supported" in issue.message for issue in result.errors))

    def test_visible_labels_must_not_leak_old_internal_ids(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            package = load_manifest_package(write_valid_package(tmpdir))
            package.chapters["repository_mainline"]["mainline_overview_diagram"]["source"] = "flowchart TD\n  a[MOD-CORE] --> b[结束]"
            result = mermaid_validation_result(package)
        self.assertFalse(result.ok)
        self.assertTrue(any("visible Mermaid label leaks internal ID" in issue.message for issue in result.errors))

    def test_internal_node_ids_are_allowed_when_labels_are_human_readable(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            package = load_manifest_package(write_valid_package(tmpdir))
            package.chapters["repository_mainline"]["mainline_overview_diagram"]["source"] = "flowchart TD\n  mod_core[存储核心] --> platform_port[平台适配]"
            result = mermaid_validation_result(package)
        self.assertTrue(result.ok, [issue.format() for issue in result.errors])

    def test_state_diagram_warns_when_visible_label_syntax_is_not_covered(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            package = load_manifest_package(write_valid_package(tmpdir))
            package.mechanisms[0].data["diagram"] = {
                "id": "mechanism_state",
                "title": "机制状态",
                "diagram_type": "stateDiagram-v2",
                "description": "状态流转。",
                "source": "stateDiagram-v2\n  [*] --> Ready\n  Ready: 存储就绪",
            }
            result = mermaid_validation_result(package)
        self.assertTrue(result.ok, [issue.format() for issue in result.errors])
        self.assertTrue(any("Unsupported visible-label syntax" in issue.message for issue in result.warnings))

    def test_mixed_supported_and_unsupported_label_syntax_warns(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            package = load_manifest_package(write_valid_package(tmpdir))
            package.chapters["repository_mainline"]["mainline_overview_diagram"]["source"] = "flowchart TD\n  a[应用] --> b[核心]\n  b -- 失败路径 --> c[错误处理]"
            result = mermaid_validation_result(package)
        self.assertTrue(result.ok, [issue.format() for issue in result.errors])
        self.assertTrue(any("Unsupported visible-label syntax" in issue.message for issue in result.warnings))

    def test_strict_cli_promotes_mermaid_warnings_to_errors(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest = write_valid_package(tmpdir)
            package = load_manifest_package(manifest)
            package.mechanisms[0].data["diagram"] = {
                "id": "mechanism_state",
                "title": "机制状态",
                "diagram_type": "stateDiagram-v2",
                "description": "状态流转。",
                "source": "stateDiagram-v2\n  [*] --> Ready\n  Ready: 存储就绪",
            }
            package.mechanisms[0].filesystem_path.write_text(json.dumps(package.mechanisms[0].data, ensure_ascii=False, indent=2), encoding="utf-8")
            completed = subprocess.run(
                [PYTHON, str(ROOT / "scripts/validate_structure.py"), str(manifest), "--strict"],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(2, completed.returncode)
        self.assertIn("strict mode treats validation warnings as errors", completed.stderr)


if __name__ == "__main__":
    unittest.main()
