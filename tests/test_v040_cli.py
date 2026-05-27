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
from tests.helpers_v040 import write_valid_package


class V040CliTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
