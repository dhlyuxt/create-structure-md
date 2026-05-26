import json
import sys
import tempfile
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.v040_package import load_manifest_package, manifest_shape_errors
from tests.helpers_v040 import FIXED_MANIFEST, write_valid_package


class V040ManifestTests(unittest.TestCase):
    def test_loads_fixed_manifest(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = write_valid_package(tmpdir)
            package = load_manifest_package(manifest_path)
        self.assertEqual("structure.manifest.json", package.manifest_path.name)
        self.assertEqual(set(FIXED_MANIFEST.keys()), set(package.manifest.keys()))
        self.assertEqual("示例仓库", package.chapters["document"]["document"]["repository_name"])

    def test_manifest_rejects_extra_metadata(self):
        manifest = dict(FIXED_MANIFEST)
        manifest["dsl_version"] = "0.4.0"
        issues = manifest_shape_errors(manifest)
        self.assertTrue(any("must not contain dsl_version" in issue.message for issue in issues))

    def test_manifest_rejects_wrong_keys(self):
        manifest = dict(FIXED_MANIFEST)
        manifest["repository_overview"] = manifest.pop("overview")
        issues = manifest_shape_errors(manifest)
        self.assertTrue(any("0.4.0 manifest keys" in issue.message for issue in issues))

    def test_manifest_paths_must_match_fixed_values(self):
        manifest = dict(FIXED_MANIFEST)
        manifest["overview"] = "chapters/overview.json"
        issues = manifest_shape_errors(manifest)
        self.assertTrue(
            any("must equal chapters/01-overview.json" in issue.message for issue in issues)
        )

    def test_manifest_schema_rejects_wrong_root_type(self):
        schema = json.loads(
            (ROOT / "schemas/v0.4.0/structure.manifest.schema.json").read_text(encoding="utf-8")
        )
        Draft202012Validator.check_schema(schema)
        errors = list(Draft202012Validator(schema).iter_errors([]))
        self.assertTrue(errors)


if __name__ == "__main__":
    unittest.main()
