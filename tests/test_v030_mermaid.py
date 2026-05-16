import contextlib
import io
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tests.helpers_v030 import write_valid_package

from scripts import v030_mermaid
from scripts import validate_structure
from scripts.v030_mermaid import mermaid_validation_result
from scripts.v030_package import load_manifest_package
from scripts.v030_types import ValidationResult


ROOT = Path(__file__).resolve().parents[1]


def valid_package_with_source(source: str, diagram_type: str = "flowchart"):
    tmpdir = tempfile.TemporaryDirectory()
    manifest = write_valid_package(tmpdir.name)
    package = load_manifest_package(manifest)
    diagram = package.chapters["repository_mainline"]["mainline_overview_diagram"]
    diagram["diagram_type"] = diagram_type
    diagram["source"] = source
    return tmpdir, package


def completed_tool(payload, returncode=0, stderr=""):
    return subprocess.CompletedProcess(
        args=["node"],
        returncode=returncode,
        stdout=json.dumps(payload),
        stderr=stderr,
    )


class V030MermaidToolingTests(unittest.TestCase):
    def run_with_tool_result(self, package, payload, returncode=0, stderr=""):
        with mock.patch("scripts.v030_mermaid._locate_node", return_value=Path("/tool/node")):
            with mock.patch("scripts.v030_mermaid._locate_mermaid_module", return_value=Path("/tool/mermaid.esm.mjs")):
                with mock.patch("scripts.v030_mermaid.subprocess.run", return_value=completed_tool(payload, returncode, stderr)):
                    return mermaid_validation_result(package)

    def test_valid_flowchart_succeeds_when_tool_reports_flowchart_v2(self):
        tmpdir, package = valid_package_with_source("flowchart TD\n  a[Start] --> b[Done]")
        with tmpdir:
            result = self.run_with_tool_result(package, {"ok": True, "diagramType": "flowchart-v2"})
        self.assertTrue(result.ok, [issue.format() for issue in result.errors])
        self.assertFalse(result.warnings, [issue.format() for issue in result.warnings])

    def test_valid_flowchart_succeeds_when_tool_reports_flowchart(self):
        tmpdir, package = valid_package_with_source("flowchart TD\n  a[Start] --> b[Done]")
        with tmpdir:
            result = self.run_with_tool_result(package, {"ok": True, "diagramType": "flowchart"})
        self.assertTrue(result.ok, [issue.format() for issue in result.errors])

    def test_invalid_mermaid_syntax_returns_syntax_error(self):
        tmpdir, package = valid_package_with_source("flowchart TD\n  a -->")
        with tmpdir:
            result = self.run_with_tool_result(package, {"ok": False, "error": "Parse error"})
        self.assertFalse(result.ok)
        self.assertTrue(any(issue.code == "mermaid.syntax" for issue in result.errors), [issue.format() for issue in result.errors])

    def test_dsl_type_mismatch_returns_diagram_type_error(self):
        tmpdir, package = valid_package_with_source("sequenceDiagram\n  A->>B: hi", diagram_type="flowchart")
        with tmpdir:
            result = self.run_with_tool_result(package, {"ok": True, "diagramType": "sequence"})
        self.assertFalse(result.ok)
        self.assertTrue(any(issue.code == "mermaid.diagram_type" for issue in result.errors), [issue.format() for issue in result.errors])

    def test_legacy_graph_declaration_is_rejected_before_tooling(self):
        tmpdir, package = valid_package_with_source("%% comment\ngraph TD\n  a --> b")
        with tmpdir:
            with mock.patch("scripts.v030_mermaid.subprocess.run") as run:
                result = mermaid_validation_result(package)
        self.assertFalse(result.ok)
        self.assertTrue(any(issue.code == "mermaid.legacy_graph" for issue in result.errors), [issue.format() for issue in result.errors])
        run.assert_not_called()

    def test_missing_node_returns_tooling_error(self):
        tmpdir, package = valid_package_with_source("flowchart TD\n  a --> b")
        with tmpdir:
            with mock.patch("scripts.v030_mermaid._locate_node", return_value=None):
                result = mermaid_validation_result(package)
        self.assertFalse(result.ok)
        self.assertTrue(any(issue.code == "mermaid.tooling" for issue in result.errors), [issue.format() for issue in result.errors])

    def test_missing_mermaid_package_returns_tooling_error(self):
        tmpdir, package = valid_package_with_source("flowchart TD\n  a --> b")
        with tmpdir:
            with mock.patch("scripts.v030_mermaid._locate_node", return_value=Path("/tool/node")):
                with mock.patch("scripts.v030_mermaid._locate_mermaid_module", return_value=None):
                    result = mermaid_validation_result(package)
        self.assertFalse(result.ok)
        self.assertTrue(any(issue.code == "mermaid.tooling" for issue in result.errors), [issue.format() for issue in result.errors])

    def test_failed_tool_invocation_returns_tooling_error(self):
        tmpdir, package = valid_package_with_source("flowchart TD\n  a --> b")
        with tmpdir:
            result = self.run_with_tool_result(package, {"ok": True}, returncode=1, stderr="node failed")
        self.assertFalse(result.ok)
        self.assertTrue(any(issue.code == "mermaid.tooling" for issue in result.errors), [issue.format() for issue in result.errors])

    def test_tool_warnings_are_returned_as_validation_warnings(self):
        tmpdir, package = valid_package_with_source("flowchart TD\n  a --> b")
        with tmpdir:
            result = self.run_with_tool_result(package, {"ok": True, "diagramType": "flowchart", "warnings": ["tool warning"]})
        self.assertTrue(result.ok, [issue.format() for issue in result.errors])
        self.assertTrue(any(issue.code == "mermaid.warning" for issue in result.warnings), [issue.format() for issue in result.warnings])

    def test_mermaid_module_discovery_uses_mmdc_package_layout(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            mmdc = root / "bin" / "mmdc"
            module = root / "node_modules" / "@mermaid-js" / "mermaid-cli" / "node_modules" / "mermaid" / "dist" / "mermaid.esm.mjs"
            mmdc.parent.mkdir(parents=True)
            module.parent.mkdir(parents=True)
            mmdc.write_text("", encoding="utf-8")
            module.write_text("", encoding="utf-8")
            with mock.patch.dict(os.environ, {"MERMAID_ESM_PATH": "", "MERMAID_PACKAGE_PATH": ""}, clear=False):
                with mock.patch("scripts.v030_mermaid.shutil.which", return_value=str(mmdc)):
                    self.assertEqual(module, v030_mermaid._locate_mermaid_module())

    def test_strict_cli_promotes_mermaid_warnings_to_errors(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest = write_valid_package(tmpdir)
            warning_result = ValidationResult()
            warning_result.warn("mermaid.warning", "$.repository_mainline.mainline_overview_diagram.source", "tool warning")
            with mock.patch("scripts.validate_structure.mermaid_validation_result", return_value=warning_result):
                stderr = io.StringIO()
                with contextlib.redirect_stderr(stderr):
                    code = validate_structure.main([str(manifest), "--strict"])
        self.assertEqual(2, code)
        self.assertIn("strict mode treats validation warnings as errors", stderr.getvalue())

    def test_integration_with_installed_mermaid_toolchain_when_available(self):
        if not (Path("/home/hyx/.local/bin/node").exists() and Path("/home/hyx/.local/bin/mmdc").exists()):
            self.skipTest("local Mermaid toolchain is not installed")
        tmpdir, package = valid_package_with_source("flowchart TD\n  a[Start] --> b[Done]")
        with tmpdir:
            env = {
                **os.environ,
                "MERMAID_NODE_PATH": "/home/hyx/.local/bin/node",
            }
            with mock.patch.dict(os.environ, env, clear=False):
                result = mermaid_validation_result(package)
        self.assertTrue(result.ok, [issue.format() for issue in result.errors])


if __name__ == "__main__":
    unittest.main()
