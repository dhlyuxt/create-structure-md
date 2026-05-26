import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable


class V030ScaffoldTests(unittest.TestCase):
    def test_active_root_files_exist(self):
        expected = [
            "requirements.txt",
            "scripts/v030_types.py",
            "scripts/v030_paths.py",
            "scripts/validate_structure.py",
        ]
        for relative_path in expected:
            with self.subTest(path=relative_path):
                self.assertTrue((ROOT / relative_path).is_file())

    def test_requirements_contains_jsonschema_only(self):
        lines = [
            line.strip()
            for line in (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]
        self.assertEqual(["jsonschema"], lines)

    def test_manifest_payload_must_not_carry_dsl_version(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest = Path(tmpdir) / "structure.manifest.json"
            manifest.write_text(
                json.dumps(
                    {
                        "dsl_version": "0.2.0",
                        "document": "chapters/01-document.json",
                        "repository_overview": "chapters/02-repository-overview.json",
                        "directory_map": "chapters/03-directory-map.json",
                        "module_layers": "chapters/04-module-layers.json",
                        "repository_mainline": "chapters/05-repository-mainline.json",
                        "key_mechanisms": [],
                        "integration_boundaries": "chapters/07-integration-boundaries.json",
                        "risks_validation": "chapters/08-risks-validation.json",
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            completed = subprocess.run(
                [PYTHON, str(ROOT / "scripts/validate_structure.py"), str(manifest)],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(2, completed.returncode)
        self.assertIn("structure.manifest.json must not contain dsl_version", completed.stderr)


if __name__ == "__main__":
    unittest.main()
