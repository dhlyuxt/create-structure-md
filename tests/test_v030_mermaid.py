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

    def test_leading_mermaid_comments_do_not_affect_declaration_token(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            package = load_manifest_package(write_valid_package(tmpdir))
            package.chapters["repository_mainline"]["mainline_overview_diagram"]["source"] = "%% comment\nflowchart TD\n  a[应用] --> b[核心]"
            result = mermaid_validation_result(package)
        self.assertTrue(result.ok, [issue.format() for issue in result.errors])
        self.assertFalse(result.warnings, [issue.format() for issue in result.warnings])

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

    def test_visible_labels_must_not_leak_embedded_old_internal_ids(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            package = load_manifest_package(write_valid_package(tmpdir))
            package.chapters["repository_mainline"]["mainline_overview_diagram"]["source"] = "flowchart TD\n  a[存储MOD-CORE核心] --> b[结束]"
            result = mermaid_validation_result(package)
        self.assertFalse(result.ok)
        self.assertTrue(any("visible Mermaid label leaks internal ID" in issue.message for issue in result.errors))

    def test_human_readable_chinese_labels_without_old_internal_ids_are_allowed(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            package = load_manifest_package(write_valid_package(tmpdir))
            package.chapters["repository_mainline"]["mainline_overview_diagram"]["source"] = "flowchart TD\n  a[存储核心] --> b[平台适配]"
            result = mermaid_validation_result(package)
        self.assertTrue(result.ok, [issue.format() for issue in result.errors])
        self.assertFalse(result.warnings, [issue.format() for issue in result.warnings])

    def test_internal_node_ids_are_allowed_when_labels_are_human_readable(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            package = load_manifest_package(write_valid_package(tmpdir))
            package.chapters["repository_mainline"]["mainline_overview_diagram"]["source"] = "flowchart TD\n  mod_core[存储核心] --> platform_port[平台适配]"
            result = mermaid_validation_result(package)
        self.assertTrue(result.ok, [issue.format() for issue in result.errors])

    def test_sequence_message_labels_must_not_leak_old_internal_ids(self):
        sources = [
            (
                "with_aliases",
                "sequenceDiagram\n  participant api as 存储接口\n  participant core as 存储核心\n  api->>core: MOD-CORE",
            ),
            ("without_aliases", "sequenceDiagram\n  api->>core: MOD-CORE"),
        ]
        for name, source in sources:
            with self.subTest(name=name):
                with tempfile.TemporaryDirectory() as tmpdir:
                    package = load_manifest_package(write_valid_package(tmpdir))
                    diagram = package.chapters["repository_mainline"]["mainline_overview_diagram"]
                    diagram["diagram_type"] = "sequenceDiagram"
                    diagram["source"] = source
                    result = mermaid_validation_result(package)
                self.assertFalse(result.ok)
                self.assertTrue(any("visible Mermaid label leaks internal ID: MOD-CORE" in issue.message for issue in result.errors))

    def test_implicit_sequence_participants_must_not_leak_old_internal_ids(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            package = load_manifest_package(write_valid_package(tmpdir))
            diagram = package.chapters["repository_mainline"]["mainline_overview_diagram"]
            diagram["diagram_type"] = "sequenceDiagram"
            diagram["source"] = "sequenceDiagram\n  MOD-CORE->>RUN-LOAD: 写入成功"
            result = mermaid_validation_result(package)
        self.assertFalse(result.ok)
        self.assertTrue(any("visible Mermaid label leaks internal ID: MOD-CORE" in issue.message for issue in result.errors))
        self.assertTrue(any("visible Mermaid label leaks internal ID: RUN-LOAD" in issue.message for issue in result.errors))

    def test_human_readable_implicit_sequence_participants_are_allowed(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            package = load_manifest_package(write_valid_package(tmpdir))
            diagram = package.chapters["repository_mainline"]["mainline_overview_diagram"]
            diagram["diagram_type"] = "sequenceDiagram"
            diagram["source"] = "sequenceDiagram\n  应用->>核心: 写入成功"
            result = mermaid_validation_result(package)
        self.assertTrue(result.ok, [issue.format() for issue in result.errors])
        self.assertFalse(result.warnings, [issue.format() for issue in result.warnings])

    def test_unaliased_sequence_participants_must_not_leak_old_internal_ids(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            package = load_manifest_package(write_valid_package(tmpdir))
            diagram = package.chapters["repository_mainline"]["mainline_overview_diagram"]
            diagram["diagram_type"] = "sequenceDiagram"
            diagram["source"] = "sequenceDiagram\n  participant MOD-CORE"
            result = mermaid_validation_result(package)
        self.assertFalse(result.ok)
        self.assertTrue(any("visible Mermaid label leaks internal ID: MOD-CORE" in issue.message for issue in result.errors))

    def test_human_readable_unaliased_sequence_participants_pass_without_warning(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            package = load_manifest_package(write_valid_package(tmpdir))
            diagram = package.chapters["repository_mainline"]["mainline_overview_diagram"]
            diagram["diagram_type"] = "sequenceDiagram"
            diagram["source"] = "sequenceDiagram\n  participant 存储接口\n  participant 存储核心\n  存储接口->>存储核心: 写入成功"
            result = mermaid_validation_result(package)
        self.assertTrue(result.ok, [issue.format() for issue in result.errors])
        self.assertFalse(result.warnings, [issue.format() for issue in result.warnings])

    def test_flowchart_labels_with_parentheses_must_not_hide_old_internal_ids(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            package = load_manifest_package(write_valid_package(tmpdir))
            package.chapters["repository_mainline"]["mainline_overview_diagram"]["source"] = "flowchart TD\n  a[MOD-CORE (legacy)] --> b[结束]"
            result = mermaid_validation_result(package)
        self.assertFalse(result.ok)
        self.assertTrue(any("visible Mermaid label leaks internal ID: MOD-CORE" in issue.message for issue in result.errors))

    def test_mermaid_comments_are_ignored_by_visible_label_checks(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            package = load_manifest_package(write_valid_package(tmpdir))
            package.chapters["repository_mainline"]["mainline_overview_diagram"]["source"] = (
                "flowchart TD\n"
                "  %% hidden[MOD-CORE]\n"
                "  %% a -- hidden old route --> b\n"
                "  a[应用] --> b[核心]"
            )
            result = mermaid_validation_result(package)
        self.assertTrue(result.ok, [issue.format() for issue in result.errors])
        self.assertFalse(result.warnings, [issue.format() for issue in result.warnings])

    def test_unlabeled_flowchart_node_ids_are_visible_labels(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            package = load_manifest_package(write_valid_package(tmpdir))
            package.chapters["repository_mainline"]["mainline_overview_diagram"]["source"] = "flowchart TD\n  MOD-CORE --> RUN-LOAD"
            result = mermaid_validation_result(package)
        self.assertFalse(result.ok)
        self.assertTrue(any("visible Mermaid label leaks internal ID: MOD-CORE" in issue.message for issue in result.errors))
        self.assertTrue(any("visible Mermaid label leaks internal ID: RUN-LOAD" in issue.message for issue in result.errors))

    def test_labeled_old_style_flowchart_node_ids_reused_in_edges_are_allowed(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            package = load_manifest_package(write_valid_package(tmpdir))
            package.chapters["repository_mainline"]["mainline_overview_diagram"]["source"] = (
                "flowchart TD\n"
                "  MOD-CORE[存储核心]\n"
                "  RUN-LOAD[加载流程]\n"
                "  MOD-CORE --> RUN-LOAD"
            )
            result = mermaid_validation_result(package)
        self.assertTrue(result.ok, [issue.format() for issue in result.errors])
        self.assertFalse(result.warnings, [issue.format() for issue in result.warnings])

    def test_explicitly_labeled_flowchart_technical_ids_are_allowed(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            package = load_manifest_package(write_valid_package(tmpdir))
            package.chapters["repository_mainline"]["mainline_overview_diagram"]["source"] = "flowchart TD\n  mod_core[存储核心] --> run_load[加载流程]"
            result = mermaid_validation_result(package)
        self.assertTrue(result.ok, [issue.format() for issue in result.errors])
        self.assertFalse(result.warnings, [issue.format() for issue in result.warnings])

    def test_non_arrow_pipe_edge_labels_must_not_leak_old_internal_ids(self):
        sources = [
            ("line", "flowchart TD\n  a[应用] ---|MOD-CORE| b[核心]"),
            ("dotted", "flowchart TD\n  a[应用] -.->|MOD-CORE| b[核心]"),
            ("thick", "flowchart TD\n  a[应用] ==>|MOD-CORE| b[核心]"),
        ]
        for name, source in sources:
            with self.subTest(name=name):
                with tempfile.TemporaryDirectory() as tmpdir:
                    package = load_manifest_package(write_valid_package(tmpdir))
                    package.chapters["repository_mainline"]["mainline_overview_diagram"]["source"] = source
                    result = mermaid_validation_result(package)
                self.assertFalse(result.ok)
                self.assertTrue(any("visible Mermaid label leaks internal ID: MOD-CORE" in issue.message for issue in result.errors))

    def test_human_readable_non_arrow_pipe_edge_labels_are_allowed(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            package = load_manifest_package(write_valid_package(tmpdir))
            package.chapters["repository_mainline"]["mainline_overview_diagram"]["source"] = "flowchart TD\n  a[应用] ---|失败路径| b[核心]"
            result = mermaid_validation_result(package)
        self.assertTrue(result.ok, [issue.format() for issue in result.errors])
        self.assertFalse(result.warnings, [issue.format() for issue in result.warnings])

    def test_subgraph_title_must_not_leak_old_internal_ids(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            package = load_manifest_package(write_valid_package(tmpdir))
            package.chapters["repository_mainline"]["mainline_overview_diagram"]["source"] = "flowchart TD\n  subgraph MOD-CORE\n    a[应用]\n  end"
            result = mermaid_validation_result(package)
        self.assertFalse(result.ok)
        self.assertTrue(any("visible Mermaid label leaks internal ID: MOD-CORE" in issue.message for issue in result.errors))

    def test_flowchart_textual_edge_syntax_warns_when_not_fully_inspected(self):
        sources = [
            ("dotted", "flowchart TD\n  a[应用] -. 失败路径 .-> b[核心]"),
            ("thick", "flowchart TD\n  a[应用] == 失败路径 ==> b[核心]"),
            ("hyphenated", "flowchart TD\n  a[应用] -- 失败-路径 --> b[核心]"),
        ]
        for name, source in sources:
            with self.subTest(name=name):
                with tempfile.TemporaryDirectory() as tmpdir:
                    package = load_manifest_package(write_valid_package(tmpdir))
                    package.chapters["repository_mainline"]["mainline_overview_diagram"]["source"] = source
                    result = mermaid_validation_result(package)
                self.assertTrue(result.ok, [issue.format() for issue in result.errors])
                self.assertTrue(any("Unsupported visible-label syntax" in issue.message for issue in result.warnings))

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

    def test_mermaid_rules_document_checked_label_forms(self):
        rules = (ROOT / "references/mermaid-rules.md").read_text(encoding="utf-8")
        self.assertIn("flowchart edge labels", rules)
        self.assertIn("`-->|失败路径|`", rules)
        self.assertIn("sequence message labels", rules)
        self.assertIn("`api->>core: 写入成功`", rules)
        self.assertIn("unaliased sequence participant and actor names", rules)
        self.assertIn("`participant 存储接口`", rules)
        self.assertIn("unlabeled flowchart node IDs", rules)
        self.assertIn("`---|失败路径|`", rules)
        self.assertIn("simple flowchart subgraph titles", rules)
        self.assertIn("`subgraph 存储核心`", rules)
        self.assertIn("state diagrams are supported by schema but non-strict", rules)


if __name__ == "__main__":
    unittest.main()
