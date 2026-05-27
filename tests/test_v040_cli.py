import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import render_markdown as render_cli
from scripts import validate_structure as validate_cli
from tests.helpers_v040 import write_json, write_valid_package


class V040CliTests(unittest.TestCase):
    def test_validate_cli_accepts_v030_package_by_manifest_shape(self):
        manifest = (
            ROOT
            / "docs/superpowers/history/V3/examples/no-mechanisms/structure.manifest.json"
        )
        stdout = io.StringIO()

        with contextlib.redirect_stdout(stdout):
            code = validate_cli.main([str(manifest), "--strict"])

        self.assertEqual(0, code)
        self.assertIn("Validation succeeded", stdout.getvalue())

    def test_validate_cli_accepts_package_without_mermaid(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest = write_valid_package(tmpdir, include_mermaid=False)
            stdout = io.StringIO()

            with contextlib.redirect_stdout(stdout):
                code = validate_cli.main([str(manifest), "--strict"])

        self.assertEqual(0, code)
        self.assertIn("Validation succeeded", stdout.getvalue())

    def test_validate_cli_reports_missing_mermaid_cli(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest = write_valid_package(tmpdir, include_mermaid=True)
            stderr = io.StringIO()

            with mock.patch("scripts.v040_mermaid._locate_mermaid_cli", return_value=None):
                with contextlib.redirect_stderr(stderr):
                    code = validate_cli.main([str(manifest), "--strict"])

        self.assertEqual(2, code)
        self.assertIn("Mermaid CLI is required", stderr.getvalue())

    def test_validate_cli_reports_manifest_directory_without_traceback(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            stderr = io.StringIO()

            with contextlib.redirect_stderr(stderr):
                code = validate_cli.main([tmpdir, "--strict"])

        self.assertEqual(2, code)
        self.assertIn("manifest JSON could not be read", stderr.getvalue())
        self.assertNotIn("Traceback", stderr.getvalue())

    def test_validate_cli_reports_invalid_json_without_traceback(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest = Path(tmpdir) / "structure.manifest.json"
            manifest.write_text("{", encoding="utf-8")
            stderr = io.StringIO()

            with contextlib.redirect_stderr(stderr):
                code = validate_cli.main([str(manifest), "--strict"])

        self.assertEqual(2, code)
        self.assertIn("manifest JSON parse failed", stderr.getvalue())
        self.assertNotIn("Traceback", stderr.getvalue())

    def test_validate_cli_reports_unknown_shape_with_supported_versions(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest = Path(tmpdir) / "structure.manifest.json"
            write_json(manifest, {"document": "chapters/00-document.json"})
            stderr = io.StringIO()

            with contextlib.redirect_stderr(stderr):
                code = validate_cli.main([str(manifest), "--strict"])

        self.assertEqual(2, code)
        self.assertIn("0.3.0", stderr.getvalue())
        self.assertIn("0.4.0", stderr.getvalue())
        self.assertNotIn("Traceback", stderr.getvalue())

    def test_validate_cli_rejects_old_active_v040_aggregate_manifest_with_migration_message(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest = Path(tmpdir) / "structure.manifest.json"
            write_json(
                manifest,
                {
                    "document": "chapters/00-document.json",
                    "overview": "chapters/01-overview.json",
                    "quick_start": "chapters/02-quick-start.json",
                    "architecture_overview": "chapters/03-architecture-overview.json",
                    "main_flows": "chapters/04-main-flows.json",
                    "module_details": "chapters/05-module-details.json",
                },
            )
            stderr = io.StringIO()

            with contextlib.redirect_stderr(stderr):
                code = validate_cli.main([str(manifest), "--strict"])

        self.assertEqual(2, code)
        self.assertIn("breaking active 0.4.0 migration", stderr.getvalue())
        self.assertIn("main_flow_details", stderr.getvalue())

    def test_validate_cli_rejects_dsl_version_before_dispatch(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest = write_valid_package(tmpdir, include_mermaid=False)
            manifest_data = {
                "dsl_version": "0.4.0",
                "document": "chapters/00-document.json",
            }
            write_json(manifest, manifest_data)
            stderr = io.StringIO()

            with contextlib.redirect_stderr(stderr):
                code = validate_cli.main([str(manifest), "--strict"])

        self.assertEqual(2, code)
        self.assertIn("dsl_version", stderr.getvalue())
        self.assertNotIn("Traceback", stderr.getvalue())

    def test_validate_flow_detail_cli_accepts_one_assigned_file(self):
        from scripts import validate_flow_detail

        with tempfile.TemporaryDirectory() as tmpdir:
            manifest = write_valid_package(tmpdir)
            detail = Path(tmpdir) / "chapters/04-main-flow-details/init-flow.json"
            stdout = io.StringIO()

            with contextlib.redirect_stdout(stdout):
                code = validate_flow_detail.main([str(detail), "--package-root", str(Path(manifest).parent)])

        self.assertEqual(0, code)
        self.assertIn("Flow detail validation succeeded", stdout.getvalue())

    def test_validate_module_detail_cli_accepts_one_assigned_file(self):
        from scripts import validate_module_detail

        with tempfile.TemporaryDirectory() as tmpdir:
            manifest = write_valid_package(tmpdir)
            detail = Path(tmpdir) / "chapters/05-module-details/storage.json"
            stdout = io.StringIO()

            with contextlib.redirect_stdout(stdout):
                code = validate_module_detail.main([str(detail), "--package-root", str(Path(manifest).parent)])

        self.assertEqual(0, code)
        self.assertIn("Module detail validation succeeded", stdout.getvalue())

    def test_validate_flow_detail_cli_works_before_overview_files_exist(self):
        from scripts import validate_flow_detail

        with tempfile.TemporaryDirectory() as tmpdir:
            package_root = Path(tmpdir)
            write_json(
                package_root / "structure.manifest.json",
                {
                    "document": "chapters/00-document.json",
                    "overview": "chapters/01-overview.json",
                    "quick_start": "chapters/02-quick-start.json",
                    "architecture_overview": "chapters/03-architecture-overview.json",
                    "main_flow_overview": "chapters/04-main-flow-overview.json",
                    "main_flow_details": ["chapters/04-main-flow-details/init-flow.json"],
                    "module_overview": "chapters/05-module-overview.json",
                    "module_details": ["chapters/05-module-details/storage.json"],
                },
            )
            detail = package_root / "chapters/04-main-flow-details/init-flow.json"
            write_json(
                detail,
                {
                    "title": "初始化主线",
                    "purpose": "准备示例仓库能力并写入初始状态。",
                    "reader_goal": "读者想知道调用初始化入口后仓库内部发生什么。",
                    "entry": {"name": "example_init", "location": "src/api/init.py"},
                    "blocks": [],
                    "extra_subsections": [],
                },
            )
            stdout = io.StringIO()

            with contextlib.redirect_stdout(stdout):
                code = validate_flow_detail.main([str(detail), "--package-root", str(package_root)])

        self.assertEqual(0, code)
        self.assertIn("Flow detail validation succeeded", stdout.getvalue())

    def test_validate_detail_cli_rejects_file_not_listed_in_manifest(self):
        from scripts import validate_flow_detail

        with tempfile.TemporaryDirectory() as tmpdir:
            manifest = write_valid_package(tmpdir)
            detail = Path(tmpdir) / "chapters/04-main-flow-details/unlisted.json"
            write_json(
                detail,
                {
                    "title": "未列出主线",
                    "purpose": "不应被接受。",
                    "reader_goal": "读者不应看到未列出文件。",
                    "entry": {"name": "unlisted"},
                    "blocks": [],
                    "extra_subsections": [],
                },
            )
            stderr = io.StringIO()

            with contextlib.redirect_stderr(stderr):
                code = validate_flow_detail.main([str(detail), "--package-root", str(Path(manifest).parent)])

        self.assertEqual(2, code)
        self.assertIn("$.main_flow_details", stderr.getvalue())

    def test_validate_module_detail_cli_rejects_process_metadata(self):
        from scripts import validate_module_detail

        with tempfile.TemporaryDirectory() as tmpdir:
            manifest = write_valid_package(tmpdir)
            detail = Path(tmpdir) / "chapters/05-module-details/storage.json"
            data = json.loads(detail.read_text(encoding="utf-8"))
            data["purpose"] = "subagent report should not ship"
            write_json(detail, data)
            stderr = io.StringIO()

            with contextlib.redirect_stderr(stderr):
                code = validate_module_detail.main([str(detail), "--package-root", str(Path(manifest).parent)])

        self.assertEqual(2, code)
        self.assertIn("semantics.process_metadata", stderr.getvalue())

    def test_render_cli_accepts_v030_package_by_manifest_shape(self):
        manifest = (
            ROOT
            / "docs/superpowers/history/V3/examples/no-mechanisms/structure.manifest.json"
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "no-mechanisms-v030.md"
            stdout = io.StringIO()

            with contextlib.redirect_stdout(stdout):
                code = render_cli.main(
                    [str(manifest), "--output", str(output), "--strict"]
                )

            self.assertEqual(0, code)
            self.assertTrue(output.exists())
            self.assertIn("Document written:", stdout.getvalue())

    def test_render_cli_writes_default_output(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest = write_valid_package(tmpdir, include_mermaid=False)
            output = Path(tmpdir) / "Example_STRUCTURE_DESIGN.md"
            stdout = io.StringIO()

            with contextlib.redirect_stdout(stdout):
                code = render_cli.main([str(manifest)])

            self.assertEqual(0, code)
            self.assertTrue(output.exists())
            self.assertIn("Document written:", stdout.getvalue())

    def test_render_cli_reports_output_directory_without_traceback(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest = write_valid_package(tmpdir, include_mermaid=False)
            stderr = io.StringIO()

            with contextlib.redirect_stderr(stderr):
                code = render_cli.main([str(manifest), "--output", tmpdir])

        self.assertEqual(2, code)
        self.assertIn("Markdown output could not be written", stderr.getvalue())
        self.assertNotIn("Traceback", stderr.getvalue())

    def test_render_cli_rejects_unsafe_default_output_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest = write_valid_package(tmpdir, include_mermaid=False)
            document_path = Path(tmpdir) / "chapters/00-document.json"
            document = {
                "document": {
                    "repository_name": "示例仓库",
                    "output_file": "../unsafe.md",
                    "summary": "用于验证 0.4.0 reader guide package 的示例仓库。",
                }
            }
            write_json(document_path, document)
            stderr = io.StringIO()

            with contextlib.redirect_stderr(stderr):
                code = render_cli.main([str(manifest)])

        self.assertEqual(2, code)
        self.assertIn("default output_file must be relative", stderr.getvalue())

    def test_render_cli_rejects_default_output_path_that_escapes_through_symlink(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            package_root = Path(tmpdir) / "package"
            outside_root = Path(tmpdir) / "outside"
            outside_root.mkdir()
            manifest = write_valid_package(package_root, include_mermaid=False)
            (package_root / "linked-outside").symlink_to(
                outside_root,
                target_is_directory=True,
            )
            document_path = package_root / "chapters/00-document.json"
            document = {
                "document": {
                    "repository_name": "示例仓库",
                    "output_file": "linked-outside/rendered.md",
                    "summary": "用于验证 0.4.0 reader guide package 的示例仓库。",
                }
            }
            write_json(document_path, document)
            stderr = io.StringIO()

            with contextlib.redirect_stderr(stderr):
                code = render_cli.main([str(manifest)])

            self.assertEqual(2, code)
            self.assertFalse((outside_root / "rendered.md").exists())
            self.assertIn("stay within the package root", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
