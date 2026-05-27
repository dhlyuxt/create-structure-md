import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
EXAMPLE_MANIFEST = ROOT / "examples/minimal-reader-guide/structure.manifest.json"


class V040E2ETests(unittest.TestCase):
    def test_example_package_validates_in_strict_mode_without_repo_root(self):
        completed = subprocess.run(
            [
                PYTHON,
                str(ROOT / "scripts/validate_structure.py"),
                str(EXAMPLE_MANIFEST),
                "--strict",
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertIn("Validation succeeded", completed.stdout)

    def test_example_package_renders_markdown(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "rendered.md"
            completed = subprocess.run(
                [
                    PYTHON,
                    str(ROOT / "scripts/render_markdown.py"),
                    str(EXAMPLE_MANIFEST),
                    "--output",
                    str(output),
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(0, completed.returncode, completed.stderr)
            markdown = output.read_text(encoding="utf-8")

        self.assertIn("## 入门", markdown)
        self.assertIn("### 快速开始", markdown)
        self.assertIn("### 模块详解", markdown)


if __name__ == "__main__":
    unittest.main()
