import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
EXAMPLES = [
    ROOT / "examples/minimal-c-library/structure.manifest.json",
    ROOT / "examples/no-mechanisms/structure.manifest.json",
]


class V030EndToEndAcceptanceTests(unittest.TestCase):
    def test_examples_validate_in_strict_mode(self):
        for manifest in EXAMPLES:
            with self.subTest(manifest=manifest):
                completed = subprocess.run(
                    [PYTHON, str(ROOT / "scripts/validate_structure.py"), str(manifest), "--strict"],
                    cwd=ROOT,
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual("", completed.stderr)
                self.assertEqual(0, completed.returncode)
                self.assertIn("Validation succeeded", completed.stdout)

    def test_examples_render_without_visible_legacy_internal_ids(self):
        hidden_tokens = ["MOD-", "RUN-", "FLOW-", "MER-"]
        for manifest in EXAMPLES:
            with self.subTest(manifest=manifest):
                with tempfile.TemporaryDirectory() as tmpdir:
                    output = Path(tmpdir) / "rendered.md"
                    completed = subprocess.run(
                        [
                            PYTHON,
                            str(ROOT / "scripts/render_markdown.py"),
                            str(manifest),
                            "--output",
                            str(output),
                            "--strict",
                        ],
                        cwd=ROOT,
                        text=True,
                        capture_output=True,
                        check=False,
                    )
                    self.assertEqual("", completed.stderr)
                    self.assertEqual(0, completed.returncode)
                    markdown = output.read_text(encoding="utf-8")
                for token in hidden_tokens:
                    self.assertNotIn(token, markdown)
                self.assertIn("## 8. 风险、假设与验证缺口", markdown)


if __name__ == "__main__":
    unittest.main()
