import contextlib
import io
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
