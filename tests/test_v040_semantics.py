import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.v040_package import load_manifest_package
from scripts.v040_semantics import semantic_validation_result
from tests.helpers_v040 import write_json, write_valid_package


class V040SemanticTests(unittest.TestCase):
    def validate(self, mutator=None, *, include_mermaid=False):
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = write_valid_package(tmpdir, include_mermaid=include_mermaid)
            if mutator:
                mutator(Path(tmpdir))
            package = load_manifest_package(manifest_path)
            return semantic_validation_result(package)

    def test_valid_fixture_has_no_semantic_errors(self):
        result = self.validate()

        self.assertEqual([], [issue.format() for issue in result.errors])

    def test_errors_when_flow_overview_rows_do_not_match_details(self):
        def mutate(root):
            data = _read(root / "chapters/04-main-flow-overview.json")
            data["main_flow_overview"]["flow_table"]["rows"][0]["flow"] = "错误主线"
            write_json(root / "chapters/04-main-flow-overview.json", data)

        result = self.validate(mutate)

        self.assertErrorCode(result, "semantics.main_flow_overview.mismatch")

    def test_errors_when_module_overview_rows_do_not_match_details(self):
        def mutate(root):
            data = _read(root / "chapters/05-module-overview.json")
            data["module_overview"]["module_table"]["rows"][0]["anchor"] = "错误模块"
            write_json(root / "chapters/05-module-overview.json", data)

        result = self.validate(mutate)

        self.assertErrorCode(result, "semantics.module_overview.mismatch")

    def test_malformed_overview_or_detail_shapes_do_not_raise_semantic_validation(self):
        cases = [
            (
                "missing flow table",
                "chapters/04-main-flow-overview.json",
                lambda data: data["main_flow_overview"].pop("flow_table"),
            ),
            (
                "missing module table",
                "chapters/05-module-overview.json",
                lambda data: data["module_overview"].pop("module_table"),
            ),
            (
                "missing flow title",
                "chapters/04-main-flow-details/init-flow.json",
                lambda data: data.pop("title"),
            ),
        ]
        for label, relative_path, mutate_data in cases:
            with self.subTest(label=label):
                def mutate(root, relative_path=relative_path, mutate_data=mutate_data):
                    data = _read(root / relative_path)
                    mutate_data(data)
                    write_json(root / relative_path, data)

                result = self.validate(mutate)

                self.assertIsNotNone(result)

    def test_warns_when_more_than_three_main_flow_detail_files_are_selected(self):
        def mutate(root):
            manifest = _read(root / "structure.manifest.json")
            rows = _read(root / "chapters/04-main-flow-overview.json")
            for index in range(1, 4):
                path = f"chapters/04-main-flow-details/flow-{index}.json"
                manifest["main_flow_details"].append(path)
                title = f"主线 {index}"
                write_json(
                    root / path,
                    {
                        "title": title,
                        "purpose": f"说明主线 {index}。",
                        "reader_goal": f"读者想理解主线 {index}。",
                        "entry": {"name": f"flow_{index}", "location": f"src/flow_{index}.py"},
                        "blocks": [],
                        "extra_subsections": [],
                    },
                )
                rows["main_flow_overview"]["flow_table"]["rows"].append(
                    {
                        "flow": title,
                        "purpose": f"说明主线 {index}。",
                        "entry": f"flow_{index}",
                        "location": f"src/flow_{index}.py",
                        "anchor": title,
                    }
                )
            write_json(root / "structure.manifest.json", manifest)
            write_json(root / "chapters/04-main-flow-overview.json", rows)

        result = self.validate(mutate)

        self.assertWarningPath(
            result,
            "semantics.main_" "flows.too_many",
            "$.main_flow_details",
        )

    def test_warns_when_module_entry_looks_like_file_only_listing(self):
        def mutate(root):
            data = _read(root / "chapters/05-module-details/storage.json")
            data.update(
                {
                    "name": "src/storage.py",
                    "purpose": "src/storage.py",
                    "blocks": [],
                    "mechanisms": [],
                }
            )
            write_json(root / "chapters/05-module-details/storage.json", data)

        result = self.validate(mutate)

        self.assertWarningCode(result, "semantics.module.file_only")
        self.assertWarningPath(
            result,
            "semantics.module.file_only",
            "$.module_details[0]",
        )

    def test_warns_when_file_named_module_has_file_only_purpose_with_blocks(self):
        def mutate(root):
            data = _read(root / "chapters/05-module-details/storage.json")
            data.update(
                {
                    "name": "storage.py",
                    "purpose": "这个文件包含初始化函数。",
                    "blocks": [{"type": "text", "content": "有额外说明。"}],
                    "mechanisms": [
                        {
                            "title": "初始化",
                            "blocks": [{"type": "text", "content": "初始化细节。"}],
                        }
                    ],
                }
            )
            write_json(root / "chapters/05-module-details/storage.json", data)

        result = self.validate(mutate)

        self.assertWarningCode(result, "semantics.module.file_only")

    def test_errors_when_process_metadata_appears_in_text_content(self):
        def mutate(root):
            data = _read(root / "chapters/01-overview.json")
            data["overview"]["repository_intro"]["blocks"][0][
                "content"
            ] = "subagent report: implementation notes"
            write_json(root / "chapters/01-overview.json", data)

        result = self.validate(mutate)

        self.assertErrorCode(result, "semantics.process_metadata")

    def test_errors_when_process_metadata_appears_in_extra_subsection_title(self):
        def mutate(root):
            data = _read(root / "chapters/01-overview.json")
            data["overview"]["extra_subsections"].append(
                {
                    "key": "execution_notes",
                    "title": "执行记录",
                    "blocks": [{"type": "text", "content": "reader-facing note"}],
                }
            )
            write_json(root / "chapters/01-overview.json", data)

        result = self.validate(mutate)

        self.assertErrorCode(result, "semantics.process_metadata")

    def test_errors_when_process_metadata_appears_in_rendered_fields(self):
        def mutate(root):
            document = _read(root / "chapters/00-document.json")
            document["document"]["summary"] = "raw scan log should not ship"
            write_json(root / "chapters/00-document.json", document)

            quick_start = _read(root / "chapters/02-quick-start.json")
            quick_start["quick_start"]["setup"]["blocks"].append(
                {
                    "type": "code",
                    "title": "repo-understand log",
                    "language": "bash",
                    "content": "python -m example.init",
                }
            )
            quick_start["quick_start"]["first_run"]["steps"][0][
                "title"
            ] = "执行记录"
            write_json(root / "chapters/02-quick-start.json", quick_start)

            main_flow = _read(root / "chapters/04-main-flow-details/init-flow.json")
            main_flow["purpose"] = "command transcript should not appear"
            write_json(root / "chapters/04-main-flow-details/init-flow.json", main_flow)

            module_detail = _read(root / "chapters/05-module-details/storage.json")
            module_detail["purpose"] = "subagent report should not appear"
            module_detail["mechanisms"][0]["title"] = "rejected draft"
            write_json(root / "chapters/05-module-details/storage.json", module_detail)

        result = self.validate(mutate)

        error_paths = {
            issue.path
            for issue in result.errors
            if issue.code == "semantics.process_metadata"
        }
        self.assertTrue(
            {
                "$.document.document.summary",
                "$.quick_start.quick_start.setup.blocks[1].title",
                "$.quick_start.quick_start.first_run.steps[0].title",
                "$.main_flow_details[0].purpose",
                "$.module_details[0].purpose",
                "$.module_details[0].mechanisms[0].title",
            }.issubset(error_paths),
            [issue.format() for issue in result.errors],
        )

    def test_warns_when_mermaid_block_source_uses_legacy_graph(self):
        def mutate(root):
            data = _read(root / "chapters/01-overview.json")
            data["overview"]["repository_intro"]["blocks"][-1][
                "source"
            ] = "graph LR\n  app[应用] --> api[公共 API]"
            write_json(root / "chapters/01-overview.json", data)

        result = self.validate(mutate, include_mermaid=True)

        self.assertWarningCode(result, "semantics.mermaid.legacy_graph")

    def test_warns_when_mermaid_visible_labels_expose_internal_ids(self):
        def mutate(root):
            data = _read(root / "chapters/01-overview.json")
            data["overview"]["repository_intro"]["blocks"][-1][
                "source"
            ] = "flowchart LR\n  api_node[api_node] --> ui[用户界面]"
            write_json(root / "chapters/01-overview.json", data)

        result = self.validate(mutate, include_mermaid=True)

        self.assertWarningCode(result, "semantics.mermaid.internal_label")

    def test_warns_when_mermaid_visible_label_is_snake_or_kebab_case(self):
        cases = [
            ("flowchart LR\n  api[storage_core] --> ui[用户界面]", "storage_core"),
            ("flowchart LR\n  api[init-flow] --> ui[用户界面]", "init-flow"),
        ]
        for source, label in cases:
            with self.subTest(label=label):
                def mutate(root, source=source):
                    data = _read(root / "chapters/01-overview.json")
                    data["overview"]["repository_intro"]["blocks"][-1][
                        "source"
                    ] = source
                    write_json(root / "chapters/01-overview.json", data)

                result = self.validate(mutate, include_mermaid=True)

                self.assertWarningCode(result, "semantics.mermaid.internal_label")

    def test_warns_when_source_like_locations_are_missing_under_repo_root(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = write_valid_package(tmpdir)
            package = load_manifest_package(manifest_path)

            result = semantic_validation_result(package, repo_root=tmpdir)

        missing_location_paths = {
            issue.path
            for issue in result.warnings
            if issue.code == "semantics.location.missing"
        }
        self.assertEqual(
            {
                "$.overview.overview.core_components.component_table.rows[0].location",
                "$.architecture_overview.architecture_overview.layers.layer_table.rows[0].location",
                "$.architecture_overview.architecture_overview.module_map.module_table.rows[0].location",
                "$.main_flow_overview.main_flow_overview.flow_table.rows[0].location",
                "$.main_flow_details[0].entry.location",
                "$.module_overview.module_overview.module_table.rows[0].location",
                "$.module_details[0].location",
            },
            missing_location_paths,
        )

    def assertErrorCode(self, result, code):
        self.assertTrue(
            any(issue.code == code for issue in result.errors),
            [issue.format() for issue in result.errors],
        )

    def assertWarningCode(self, result, code):
        self.assertTrue(
            any(issue.code == code for issue in result.warnings),
            [issue.format() for issue in result.warnings],
        )

    def assertWarningPath(self, result, code, path):
        self.assertTrue(
            any(
                issue.code == code and issue.path == path
                for issue in result.warnings
            ),
            [issue.format() for issue in result.warnings],
        )


def _read(path):
    return json.loads(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
