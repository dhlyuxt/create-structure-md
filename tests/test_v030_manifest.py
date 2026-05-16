import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.helpers_v030 import FIXED_MANIFEST, write_json, write_manifest_only_package

from jsonschema import Draft202012Validator

from scripts.v030_package import infer_mechanism_key, load_manifest_package, manifest_shape_errors


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable


class V030ManifestTests(unittest.TestCase):
    def test_loads_fixed_manifest_and_infers_mechanism_keys(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = write_manifest_only_package(tmpdir)
            package = load_manifest_package(manifest_path)
        self.assertEqual("structure.manifest.json", package.manifest_path.name)
        self.assertEqual(["persistence"], [mechanism.key for mechanism in package.mechanisms])
        self.assertEqual(set(FIXED_MANIFEST.keys()), set(package.manifest.keys()))

    def test_manifest_rejects_extra_metadata_fields(self):
        manifest = dict(FIXED_MANIFEST)
        manifest["title"] = "EasyFlash"
        errors = manifest_shape_errors(manifest)
        self.assertTrue(any("must contain exactly the fixed chapter keys" in issue.message for issue in errors))

    def test_manifest_schema_rejects_wrong_root_type(self):
        schema = json.loads((ROOT / "schemas/v0.3.0/structure.manifest.schema.json").read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        errors = list(Draft202012Validator(schema).iter_errors([]))
        self.assertTrue(errors)

    def test_manifest_cli_reports_wrong_root_type_without_traceback(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = Path(tmpdir) / "structure.manifest.json"
            manifest_path.write_text("[]", encoding="utf-8")
            completed = subprocess.run(
                [PYTHON, str(ROOT / "scripts/validate_structure.py"), str(manifest_path)],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(2, completed.returncode)
        self.assertIn("manifest root must be an object", completed.stderr)
        self.assertNotIn("Traceback", completed.stderr)

    def test_manifest_cli_reports_child_directory_without_traceback(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            manifest = dict(FIXED_MANIFEST)
            write_json(root / "structure.manifest.json", manifest)
            for key, value in manifest.items():
                paths = value if isinstance(value, list) else [value]
                for child in paths:
                    child_path = root / child
                    if key == "document":
                        child_path.mkdir(parents=True, exist_ok=True)
                    else:
                        write_json(child_path, {})
            completed = subprocess.run(
                [PYTHON, str(ROOT / "scripts/validate_structure.py"), str(root / "structure.manifest.json")],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(2, completed.returncode)
        self.assertNotIn("Traceback", completed.stderr)

    def test_manifest_cli_reports_manifest_directory_without_traceback(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = Path(tmpdir) / "structure.manifest.json"
            manifest_path.mkdir()
            completed = subprocess.run(
                [PYTHON, str(ROOT / "scripts/validate_structure.py"), str(manifest_path)],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(2, completed.returncode)
        self.assertNotIn("Traceback", completed.stderr)

    def test_manifest_rejects_aggregate_key_mechanisms_file(self):
        manifest = dict(FIXED_MANIFEST)
        manifest["key_mechanisms"] = ["chapters/06-key-mechanisms.json"]
        errors = manifest_shape_errors(manifest)
        self.assertTrue(any("chapters/06-key-mechanisms.json is forbidden" in issue.message for issue in errors))

    def test_manifest_path_must_be_relative_posix_json(self):
        bad_values = [
            "/chapters/01-document.json",
            "chapters\\\\01-document.json",
            "chapters//01-document.json",
            "chapters/../01-document.json",
            "chapters/01-document.md",
        ]
        for bad_value in bad_values:
            with self.subTest(value=bad_value):
                manifest = dict(FIXED_MANIFEST)
                manifest["document"] = bad_value
                errors = manifest_shape_errors(manifest)
                self.assertTrue(errors)

    def test_manifest_paths_must_be_unique(self):
        manifest = dict(FIXED_MANIFEST)
        manifest["repository_overview"] = manifest["document"]
        errors = manifest_shape_errors(manifest)
        self.assertTrue(any("Manifest paths must be unique" in issue.message for issue in errors))

    def test_mechanism_key_comes_from_file_stem(self):
        self.assertEqual("storage-flow", infer_mechanism_key("chapters/06-key-mechanisms/storage-flow.json"))

    def test_invalid_mechanism_key_is_rejected(self):
        manifest = dict(FIXED_MANIFEST)
        manifest["key_mechanisms"] = ["chapters/06-key-mechanisms/Storage.json"]
        errors = manifest_shape_errors(manifest)
        self.assertTrue(any("invalid mechanism key" in issue.message for issue in errors))


if __name__ == "__main__":
    unittest.main()
