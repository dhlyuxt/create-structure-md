import sys
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.v040_package import load_manifest_package
from scripts.v040_mermaid import mermaid_validation_result
from tests.helpers_v040 import write_valid_package


class V040MermaidTests(unittest.TestCase):
    def validate(self, *, include_mermaid=False):
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = write_valid_package(tmpdir, include_mermaid=include_mermaid)
            package = load_manifest_package(manifest_path)
            return mermaid_validation_result(package)

    @mock.patch("scripts.v040_mermaid.subprocess.run")
    @mock.patch("scripts.v040_mermaid._locate_mermaid_cli")
    def test_package_without_mermaid_does_not_require_cli(
        self, locate_mermaid_cli, subprocess_run
    ):
        result = self.validate()

        self.assertEqual([], [issue.format() for issue in result.errors])
        self.assertEqual([], [issue.format() for issue in result.warnings])
        locate_mermaid_cli.assert_not_called()
        subprocess_run.assert_not_called()

    @mock.patch("scripts.v040_mermaid.subprocess.run")
    @mock.patch("scripts.v040_mermaid._locate_mermaid_cli", return_value="/usr/bin/mmdc")
    def test_mermaid_block_invokes_cli_with_input_and_output(
        self, locate_mermaid_cli, subprocess_run
    ):
        def render_svg(command, **kwargs):
            output_path = command[command.index("-o") + 1]
            Path(output_path).write_text("<svg></svg>", encoding="utf-8")
            return mock.Mock(returncode=0, stderr="")

        subprocess_run.side_effect = render_svg

        result = self.validate(include_mermaid=True)

        self.assertEqual([], [issue.format() for issue in result.errors])
        locate_mermaid_cli.assert_called_once_with()
        subprocess_run.assert_called_once()
        command = subprocess_run.call_args.args[0]
        self.assertEqual("/usr/bin/mmdc", command[0])
        self.assertIn("-i", command)
        self.assertIn("-o", command)
        self.assertEqual(30, subprocess_run.call_args.kwargs["timeout"])

    @mock.patch("scripts.v040_mermaid.subprocess.run")
    @mock.patch("scripts.v040_mermaid._locate_mermaid_cli", return_value=None)
    def test_missing_mermaid_cli_is_an_error_and_does_not_call_subprocess(
        self, locate_mermaid_cli, subprocess_run
    ):
        result = self.validate(include_mermaid=True)

        self.assertTrue(result.errors, "expected missing CLI error")
        self.assertTrue(
            any(issue.code == "mermaid.cli_missing" for issue in result.errors),
            [issue.format() for issue in result.errors],
        )
        locate_mermaid_cli.assert_called_once_with()
        subprocess_run.assert_not_called()

    @mock.patch("scripts.v040_mermaid.subprocess.run")
    @mock.patch("scripts.v040_mermaid._locate_mermaid_cli", return_value="/usr/bin/mmdc")
    def test_non_zero_cli_exit_is_an_error_including_stderr(
        self, locate_mermaid_cli, subprocess_run
    ):
        subprocess_run.return_value = mock.Mock(returncode=1, stderr="Parse error")

        result = self.validate(include_mermaid=True)

        self.assertTrue(
            any(
                issue.code == "mermaid.render_failed"
                and "Parse error" in issue.message
                for issue in result.errors
            ),
            [issue.format() for issue in result.errors],
        )

    @mock.patch("scripts.v040_mermaid.subprocess.run")
    @mock.patch("scripts.v040_mermaid._locate_mermaid_cli", return_value="/usr/bin/mmdc")
    def test_zero_exit_without_svg_output_file_is_an_error(
        self, locate_mermaid_cli, subprocess_run
    ):
        subprocess_run.return_value = mock.Mock(returncode=0, stderr="")

        result = self.validate(include_mermaid=True)

        self.assertTrue(
            any(issue.code == "mermaid.svg_missing" for issue in result.errors),
            [issue.format() for issue in result.errors],
        )

    @mock.patch("scripts.v040_mermaid.subprocess.run")
    @mock.patch("scripts.v040_mermaid._locate_mermaid_cli", return_value="/usr/bin/mmdc")
    def test_cli_os_error_is_reported_with_block_path(
        self, locate_mermaid_cli, subprocess_run
    ):
        subprocess_run.side_effect = OSError("permission denied")

        result = self.validate(include_mermaid=True)

        self.assertTrue(
            any(
                issue.code == "mermaid.cli_error"
                and "$.overview.overview.repository_intro.blocks[1]" in issue.message
                and "permission denied" in issue.message
                for issue in result.errors
            ),
            [issue.format() for issue in result.errors],
        )

    @mock.patch("scripts.v040_mermaid.subprocess.run")
    @mock.patch("scripts.v040_mermaid._locate_mermaid_cli", return_value="/usr/bin/mmdc")
    def test_cli_timeout_is_reported_with_block_path(
        self, locate_mermaid_cli, subprocess_run
    ):
        subprocess_run.side_effect = subprocess.TimeoutExpired(
            cmd=["mmdc"], timeout=30
        )

        result = self.validate(include_mermaid=True)

        self.assertTrue(
            any(
                issue.code == "mermaid.timeout"
                and "$.overview.overview.repository_intro.blocks[1]" in issue.message
                and "30" in issue.message
                for issue in result.errors
            ),
            [issue.format() for issue in result.errors],
        )


if __name__ == "__main__":
    unittest.main()
