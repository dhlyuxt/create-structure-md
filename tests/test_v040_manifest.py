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


def find_blocks(value, block_type):
    blocks = []
    if isinstance(value, dict):
        if value.get("type") == block_type:
            blocks.append(value)
        for child in value.values():
            blocks.extend(find_blocks(child, block_type))
    elif isinstance(value, list):
        for child in value:
            blocks.extend(find_blocks(child, block_type))
    return blocks


class V040ManifestTests(unittest.TestCase):
    def load_manifest_schema(self):
        schema = json.loads(
            (ROOT / "schemas/v0.4.0/structure.manifest.schema.json").read_text(encoding="utf-8")
        )
        Draft202012Validator.check_schema(schema)
        return schema

    def assertHasIssue(self, issues, *, code, path, message):
        self.assertTrue(
            any(
                issue.code == code and issue.path == path and message in issue.message
                for issue in issues
            ),
            [issue.format() for issue in issues],
        )

    def test_loads_fixed_manifest(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = write_valid_package(tmpdir)
            package = load_manifest_package(manifest_path)
        self.assertEqual("structure.manifest.json", package.manifest_path.name)
        self.assertEqual(set(FIXED_MANIFEST.keys()), set(package.manifest.keys()))
        self.assertEqual("示例仓库", package.chapters["document"]["document"]["repository_name"])

    def test_valid_package_fixture_uses_supported_v040_shapes(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            package = load_manifest_package(write_valid_package(tmpdir))

        document = package.chapters["document"]["document"]
        self.assertEqual("示例仓库", document["repository_name"])
        self.assertEqual("Example_STRUCTURE_DESIGN.md", document["output_file"])
        self.assertIn("summary", document)

        overview = package.chapters["overview"]["overview"]
        self.assertEqual("text", overview["repository_intro"]["blocks"][0]["type"])
        self.assertIn("content", overview["repository_intro"]["blocks"][0])
        self.assertIn("blocks", overview["problems_solved"])
        self.assertEqual("unordered_list", overview["main_capabilities"]["blocks"][0]["type"])
        self.assertEqual(
            [{"component": "公共 API", "role": "对外提供仓库能力入口", "location": "src/api"}],
            overview["core_components"]["component_table"]["rows"],
        )
        self.assertEqual(
            "公共 API 是最小调用入口。",
            overview["core_components"]["blocks"][0]["content"],
        )
        self.assertIn("extra_subsections", overview)

        quick_start = package.chapters["quick_start"]["quick_start"]
        for key in ["usage_scenarios", "setup", "minimal_example", "expected_result"]:
            self.assertIn("blocks", quick_start[key])
        self.assertEqual("初始化仓库能力", quick_start["first_run"]["steps"][0]["title"])
        self.assertEqual("调用初始化入口。", quick_start["first_run"]["steps"][0]["blocks"][0]["content"])
        self.assertIn("blocks", quick_start["first_run"])
        self.assertIn("extra_subsections", quick_start)

        architecture = package.chapters["architecture_overview"]["architecture_overview"]
        self.assertIn("blocks", architecture["architecture_summary"])
        self.assertEqual(
            [{"layer": "接口层", "role": "接收调用并转换为应用命令。", "location": "src/api"}],
            architecture["layers"]["layer_table"]["rows"],
        )
        self.assertIn("blocks", architecture["layers"])
        self.assertEqual(
            [{"module": "reader", "role": "读取输入并构建领域对象。", "layer": "接口层", "location": "src/reader.py"}],
            architecture["module_map"]["module_table"]["rows"],
        )
        for key in ["module_map", "repository_layout"]:
            self.assertIn("blocks", architecture[key])
        self.assertIn("extra_subsections", architecture)

        main_flows = package.chapters["main_flows"]["main_flows"]
        self.assertIn("blocks", main_flows["flow_overview"])
        self.assertEqual("初始化主线", main_flows["flows"][0]["title"])
        self.assertIn("purpose", main_flows["flows"][0])
        self.assertEqual("example_init", main_flows["flows"][0]["entry"]["name"])
        self.assertIn("blocks", main_flows["flows"][0])
        self.assertNotIn("steps", main_flows["flows"][0])
        self.assertIn("extra_subsections", main_flows)

        module_details = package.chapters["module_details"]["module_details"]
        self.assertEqual([], module_details["intro_blocks"])
        module = module_details["modules"][0]
        self.assertEqual("存储模块", module["name"])
        for key in ["location", "purpose", "blocks", "extra_subsections"]:
            self.assertIn(key, module)
        self.assertEqual("追加写入", module["mechanisms"][0]["title"])
        self.assertIn("blocks", module["mechanisms"][0])
        self.assertIn("extra_subsections", module_details)
        self.assertEqual([], find_blocks(package.chapters, "mermaid"))

    def test_valid_package_fixture_adds_one_mermaid_block_on_request(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            package = load_manifest_package(write_valid_package(tmpdir, include_mermaid=True))
        mermaid_blocks = find_blocks(package.chapters, "mermaid")
        self.assertEqual(1, len(mermaid_blocks))
        self.assertEqual(
            {"type", "title", "diagram_type", "source"},
            set(mermaid_blocks[0].keys()),
        )

    def test_loads_chapters_in_fixed_manifest_order_when_json_order_is_reversed(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = write_valid_package(tmpdir)
            reversed_manifest = dict(reversed(list(FIXED_MANIFEST.items())))
            manifest_path.write_text(
                json.dumps(reversed_manifest, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            package = load_manifest_package(manifest_path)
        self.assertEqual(list(FIXED_MANIFEST.keys()), list(package.chapters.keys()))

    def test_manifest_rejects_extra_metadata(self):
        manifest = dict(FIXED_MANIFEST)
        manifest["dsl_version"] = "0.4.0"
        issues = manifest_shape_errors(manifest)
        self.assertHasIssue(
            issues,
            code="manifest.dsl_version",
            path="$.dsl_version",
            message="must not contain dsl_version",
        )

    def test_manifest_rejects_wrong_keys(self):
        manifest = dict(FIXED_MANIFEST)
        manifest["repository_overview"] = manifest.pop("overview")
        issues = manifest_shape_errors(manifest)
        self.assertHasIssue(
            issues,
            code="manifest.keys",
            path="$",
            message="0.4.0 manifest keys",
        )

    def test_manifest_paths_must_match_fixed_values(self):
        manifest = dict(FIXED_MANIFEST)
        manifest["overview"] = "chapters/overview.json"
        issues = manifest_shape_errors(manifest)
        self.assertHasIssue(
            issues,
            code="manifest.path",
            path="$.overview",
            message="must equal chapters/01-overview.json",
        )

    def test_manifest_schema_accepts_fixed_manifest(self):
        schema = self.load_manifest_schema()
        errors = list(Draft202012Validator(schema).iter_errors(FIXED_MANIFEST))
        self.assertEqual([], errors)

    def test_manifest_schema_rejects_wrong_const_path(self):
        schema = self.load_manifest_schema()
        manifest = dict(FIXED_MANIFEST)
        manifest["overview"] = "chapters/overview.json"
        errors = list(Draft202012Validator(schema).iter_errors(manifest))
        self.assertTrue(errors)

    def test_manifest_schema_rejects_additional_property(self):
        schema = self.load_manifest_schema()
        manifest = dict(FIXED_MANIFEST)
        manifest["dsl_version"] = "0.4.0"
        errors = list(Draft202012Validator(schema).iter_errors(manifest))
        self.assertTrue(errors)

    def test_manifest_schema_rejects_wrong_root_type(self):
        schema = self.load_manifest_schema()
        errors = list(Draft202012Validator(schema).iter_errors([]))
        self.assertTrue(errors)


if __name__ == "__main__":
    unittest.main()
