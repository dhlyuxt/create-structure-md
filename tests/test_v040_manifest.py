import json
import sys
import tempfile
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.v040_package import load_manifest_package, manifest_shape_errors
from tests.helpers_v040 import FIXED_MANIFEST, MAIN_FLOW_DETAIL, write_json, write_valid_package


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

        main_flow_overview = package.chapters["main_flow_overview"]["main_flow_overview"]
        self.assertIn("flow_table", main_flow_overview)
        self.assertEqual("初始化主线", main_flow_overview["flow_table"]["rows"][0]["flow"])
        self.assertEqual("example_init", main_flow_overview["flow_table"]["rows"][0]["entry"])
        main_flow_detail = package.main_flow_details[0].data
        self.assertEqual("初始化主线", main_flow_detail["title"])
        self.assertIn("purpose", main_flow_detail)
        self.assertEqual("example_init", main_flow_detail["entry"]["name"])
        self.assertIn("blocks", main_flow_detail)
        self.assertNotIn("steps", main_flow_detail)
        self.assertIn("extra_subsections", main_flow_detail)

        module_overview = package.chapters["module_overview"]["module_overview"]
        self.assertIn("module_table", module_overview)
        self.assertEqual("存储模块", module_overview["module_table"]["rows"][0]["module"])
        module_detail = package.module_details[0].data
        self.assertEqual("存储模块", module_detail["name"])
        for key in ["location", "purpose", "blocks", "extra_subsections"]:
            self.assertIn(key, module_detail)
        self.assertEqual(["保存初始化结果", "提供追加写入机制"], module_detail["responsibilities"])
        self.assertEqual("追加写入", module_detail["mechanisms"][0]["title"])
        self.assertIn("blocks", module_detail["mechanisms"][0])
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

    def test_valid_package_fixture_writes_all_manifest_detail_files(self):
        original_main_flow_details = FIXED_MANIFEST["main_flow_details"]
        original_module_details = FIXED_MANIFEST["module_details"]
        try:
            FIXED_MANIFEST["main_flow_details"] = [
                *original_main_flow_details,
                "chapters/04-main-flow-details/retry-flow.json",
            ]
            FIXED_MANIFEST["module_details"] = [
                *original_module_details,
                "chapters/05-module-details/cache.json",
            ]
            with tempfile.TemporaryDirectory() as tmpdir:
                write_valid_package(tmpdir)
                root = Path(tmpdir)

                for relative_path in FIXED_MANIFEST["main_flow_details"]:
                    self.assertTrue((root / relative_path).is_file(), relative_path)
                for relative_path in FIXED_MANIFEST["module_details"]:
                    self.assertTrue((root / relative_path).is_file(), relative_path)
        finally:
            FIXED_MANIFEST["main_flow_details"] = original_main_flow_details
            FIXED_MANIFEST["module_details"] = original_module_details

    def test_loads_static_chapters_in_fixed_manifest_order_when_json_order_is_reversed(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = write_valid_package(tmpdir)
            reversed_manifest = dict(reversed(list(FIXED_MANIFEST.items())))
            manifest_path.write_text(
                json.dumps(reversed_manifest, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            package = load_manifest_package(manifest_path)

        self.assertEqual(
            [
                "document",
                "overview",
                "quick_start",
                "architecture_overview",
                "main_flow_overview",
                "module_overview",
            ],
            list(package.chapters.keys()),
        )
        self.assertEqual(["init-flow"], [detail.key for detail in package.main_flow_details])
        self.assertEqual(["storage"], [detail.key for detail in package.module_details])

    def test_loads_upgraded_manifest_with_detail_lists(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            package = load_manifest_package(write_valid_package(tmpdir))

        self.assertEqual(set(FIXED_MANIFEST.keys()), set(package.manifest.keys()))
        self.assertEqual(
            {
                "document",
                "overview",
                "quick_start",
                "architecture_overview",
                "main_flow_overview",
                "module_overview",
            },
            set(package.chapters.keys()),
        )
        self.assertIn("flow_table", package.chapters["main_flow_overview"]["main_flow_overview"])
        self.assertIn("module_table", package.chapters["module_overview"]["module_overview"])
        self.assertEqual(["init-flow"], [detail.key for detail in package.main_flow_details])
        self.assertEqual(["storage"], [detail.key for detail in package.module_details])
        self.assertEqual("初始化主线", package.main_flow_details[0].data["title"])
        self.assertEqual("example_init", package.main_flow_details[0].data["entry"]["name"])
        self.assertEqual("存储模块", package.module_details[0].data["name"])
        self.assertEqual(["保存初始化结果", "提供追加写入机制"], package.module_details[0].data["responsibilities"])

    def test_rejects_old_active_v040_aggregate_manifest(self):
        old_manifest = {
            "document": "chapters/00-document.json",
            "overview": "chapters/01-overview.json",
            "quick_start": "chapters/02-quick-start.json",
            "architecture_overview": "chapters/03-architecture-overview.json",
            "main_flows": "chapters/04-main-flows.json",
            "module_details": "chapters/05-module-details.json",
        }

        issues = manifest_shape_errors(old_manifest)

        self.assertHasIssue(
            issues,
            code="manifest.keys",
            path="$",
            message="active 0.4.0 manifest must use main_flow_overview",
        )

    def test_rejects_empty_detail_arrays(self):
        for key in ["main_flow_details", "module_details"]:
            with self.subTest(key=key):
                manifest = dict(FIXED_MANIFEST)
                manifest[key] = []
                issues = manifest_shape_errors(manifest)
                self.assertHasIssue(
                    issues,
                    code="manifest.detail_array",
                    path=f"$.{key}",
                    message="must be a non-empty array",
                )

    def test_rejects_forbidden_aggregate_detail_paths(self):
        cases = [
            ("main_flow_details", ["chapters/04-main-flows.json"]),
            ("module_details", ["chapters/05-module-details.json"]),
        ]
        for key, value in cases:
            with self.subTest(key=key):
                manifest = dict(FIXED_MANIFEST)
                manifest[key] = value
                issues = manifest_shape_errors(manifest)
                self.assertHasIssue(
                    issues,
                    code="manifest.forbidden_path",
                    path=f"$.{key}[0]",
                    message="old aggregate path is invalid",
                )

    def test_rejects_invalid_detail_stems(self):
        manifest = dict(FIXED_MANIFEST)
        manifest["main_flow_details"] = ["chapters/04-main-flow-details/Bad-Key.json"]

        issues = manifest_shape_errors(manifest)

        self.assertHasIssue(
            issues,
            code="manifest.detail_key",
            path="$.main_flow_details[0]",
            message="file stem must match",
        )

    def test_rejects_duplicate_manifest_paths(self):
        manifest = dict(FIXED_MANIFEST)
        manifest["module_details"] = ["chapters/04-main-flow-details/init-flow.json"]

        issues = manifest_shape_errors(manifest)

        self.assertHasIssue(
            issues,
            code="manifest.path_duplicate",
            path="$",
            message="manifest paths must be unique",
        )

    def test_rejects_unsafe_manifest_paths(self):
        cases = [
            ("main_flow_details", ["/tmp/init-flow.json"]),
            ("main_flow_details", ["chapters/../init-flow.json"]),
            ("main_flow_details", ["chapters\\init-flow.json"]),
            ("main_flow_details", ["chapters//init-flow.json"]),
            ("main_flow_details", ["chapters/04-main-flow-details/init-flow.txt"]),
        ]
        for key, value in cases:
            with self.subTest(value=value):
                manifest = dict(FIXED_MANIFEST)
                manifest[key] = value
                issues = manifest_shape_errors(manifest)
                self.assertHasIssue(
                    issues,
                    code="manifest.path",
                    path=f"$.{key}[0]",
                    message="relative POSIX .json path",
                )

    def test_load_rejects_detail_path_that_resolves_outside_package_root(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            package_root = Path(tmpdir) / "package"
            outside_root = Path(tmpdir) / "outside"
            manifest_path = write_valid_package(package_root)
            outside_root.mkdir()
            escaped = outside_root / "escaped.json"
            escaped.write_text(
                json.dumps(MAIN_FLOW_DETAIL, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            (package_root / "chapters/04-main-flow-details/escaped.json").symlink_to(escaped)
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["main_flow_details"] = ["chapters/04-main-flow-details/escaped.json"]
            write_json(manifest_path, manifest)

            with self.assertRaisesRegex(ValueError, "resolves outside package root"):
                load_manifest_package(manifest_path)

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
