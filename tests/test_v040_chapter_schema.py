import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.v040_package import load_manifest_package
from scripts.v040_schema import schema_validation_result
from tests.helpers_v040 import write_json, write_valid_package


class V040ChapterSchemaTests(unittest.TestCase):
    def validate_package(self, mutator=None):
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = write_valid_package(tmpdir)
            if mutator:
                mutator(Path(tmpdir))
            package = load_manifest_package(manifest_path)
            return schema_validation_result(package)

    def assertValid(self, result):
        self.assertEqual([], [issue.format() for issue in result.errors])
        self.assertEqual([], [issue.format() for issue in result.warnings])

    def assertInvalidAt(self, result, path):
        self.assertTrue(
            any(issue.path == path for issue in result.errors),
            [issue.format() for issue in result.errors],
        )
        self.assertEqual([], [issue.format() for issue in result.warnings])

    def test_valid_fixture_passes_schema(self):
        self.assertValid(self.validate_package())

    def test_document_summary_is_optional(self):
        def mutate(root):
            data = _read(root / "chapters/00-document.json")
            del data["document"]["summary"]
            write_json(root / "chapters/00-document.json", data)

        self.assertValid(self.validate_package(mutate))

    def test_unknown_block_type_details_is_rejected(self):
        def mutate(root):
            data = _read(root / "chapters/01-overview.json")
            data["overview"]["repository_intro"]["blocks"][0] = {"type": "details"}
            write_json(root / "chapters/01-overview.json", data)

        result = self.validate_package(mutate)
        self.assertInvalidAt(result, "$.overview.repository_intro.blocks[0]")

    def test_list_block_items_must_be_strings(self):
        def mutate(root):
            data = _read(root / "chapters/01-overview.json")
            data["overview"]["main_capabilities"]["blocks"][0]["items"][1] = 42
            write_json(root / "chapters/01-overview.json", data)

        result = self.validate_package(mutate)
        self.assertInvalidAt(result, "$.overview.main_capabilities.blocks[0]")

    def test_quick_start_first_run_steps_is_required_and_non_empty(self):
        def mutate_missing(root):
            data = _read(root / "chapters/02-quick-start.json")
            del data["quick_start"]["first_run"]["steps"]
            write_json(root / "chapters/02-quick-start.json", data)

        def mutate_empty(root):
            data = _read(root / "chapters/02-quick-start.json")
            data["quick_start"]["first_run"]["steps"] = []
            write_json(root / "chapters/02-quick-start.json", data)

        self.assertInvalidAt(
            self.validate_package(mutate_missing),
            "$.quick_start.first_run",
        )
        self.assertInvalidAt(
            self.validate_package(mutate_empty),
            "$.quick_start.first_run.steps",
        )

    def test_main_flows_flows_is_required_and_non_empty(self):
        def mutate_missing(root):
            data = _read(root / "chapters/04-main-flows.json")
            del data["main_flows"]["flows"]
            write_json(root / "chapters/04-main-flows.json", data)

        def mutate_empty(root):
            data = _read(root / "chapters/04-main-flows.json")
            data["main_flows"]["flows"] = []
            write_json(root / "chapters/04-main-flows.json", data)

        self.assertInvalidAt(self.validate_package(mutate_missing), "$.main_flows")
        self.assertInvalidAt(self.validate_package(mutate_empty), "$.main_flows.flows")

    def test_module_details_modules_is_required_and_non_empty(self):
        def mutate_missing(root):
            data = _read(root / "chapters/05-module-details.json")
            del data["module_details"]["modules"]
            write_json(root / "chapters/05-module-details.json", data)

        def mutate_empty(root):
            data = _read(root / "chapters/05-module-details.json")
            data["module_details"]["modules"] = []
            write_json(root / "chapters/05-module-details.json", data)

        self.assertInvalidAt(
            self.validate_package(mutate_missing),
            "$.module_details",
        )
        self.assertInvalidAt(
            self.validate_package(mutate_empty),
            "$.module_details.modules",
        )

    def test_overview_core_components_component_table_is_required(self):
        def mutate(root):
            data = _read(root / "chapters/01-overview.json")
            del data["overview"]["core_components"]["component_table"]
            write_json(root / "chapters/01-overview.json", data)

        self.assertInvalidAt(self.validate_package(mutate), "$.overview.core_components")

    def test_architecture_layers_layer_table_is_required(self):
        def mutate(root):
            data = _read(root / "chapters/03-architecture-overview.json")
            del data["architecture_overview"]["layers"]["layer_table"]
            write_json(root / "chapters/03-architecture-overview.json", data)

        self.assertInvalidAt(
            self.validate_package(mutate),
            "$.architecture_overview.layers",
        )

    def test_architecture_module_map_module_table_is_required(self):
        def mutate(root):
            data = _read(root / "chapters/03-architecture-overview.json")
            del data["architecture_overview"]["module_map"]["module_table"]
            write_json(root / "chapters/03-architecture-overview.json", data)

        self.assertInvalidAt(
            self.validate_package(mutate),
            "$.architecture_overview.module_map",
        )

    def test_fixed_table_objects_reject_extra_caption_properties_individually(self):
        cases = [
            ("chapters/01-overview.json", ("overview", "core_components", "component_table")),
            ("chapters/03-architecture-overview.json", ("architecture_overview", "layers", "layer_table")),
            ("chapters/03-architecture-overview.json", ("architecture_overview", "module_map", "module_table")),
        ]
        for file_name, keys in cases:
            with self.subTest(keys=keys):
                def mutate(root, file_name=file_name, keys=keys):
                    data = _read(root / file_name)
                    table = data
                    for key in keys:
                        table = table[key]
                    table["caption"] = "not allowed"
                    write_json(root / file_name, data)

                result = self.validate_package(mutate)
                self.assertInvalidAt(result, _package_path(keys))

    def test_fixed_table_rows_reject_extra_note_properties_individually(self):
        cases = [
            (
                "chapters/01-overview.json",
                ("overview", "core_components", "component_table", "rows", 0),
            ),
            (
                "chapters/03-architecture-overview.json",
                ("architecture_overview", "layers", "layer_table", "rows", 0),
            ),
            (
                "chapters/03-architecture-overview.json",
                ("architecture_overview", "module_map", "module_table", "rows", 0),
            ),
        ]
        for file_name, keys in cases:
            with self.subTest(keys=keys):
                def mutate(root, file_name=file_name, keys=keys):
                    data = _read(root / file_name)
                    row = data
                    for key in keys:
                        row = row[key]
                    row["note"] = "not allowed"
                    write_json(root / file_name, data)

                result = self.validate_package(mutate)
                self.assertInvalidAt(result, _package_path(keys))

    def test_extra_subsection_keys_validate_lower_case_identifier_pattern_everywhere(self):
        cases = [
            ("chapters/01-overview.json", ("overview", "extra_subsections")),
            ("chapters/02-quick-start.json", ("quick_start", "extra_subsections")),
            ("chapters/03-architecture-overview.json", ("architecture_overview", "extra_subsections")),
            ("chapters/04-main-flows.json", ("main_flows", "extra_subsections")),
            ("chapters/05-module-details.json", ("module_details", "extra_subsections")),
            ("chapters/05-module-details.json", ("module_details", "modules", 0, "extra_subsections")),
        ]
        for file_name, keys in cases:
            with self.subTest(keys=keys):
                def mutate(root, file_name=file_name, keys=keys):
                    data = _read(root / file_name)
                    extra_subsections = data
                    for key in keys:
                        extra_subsections = extra_subsections[key]
                    extra_subsections.append({"key": "Bad-Key", "title": "Bad", "blocks": []})
                    write_json(root / file_name, data)

                result = self.validate_package(mutate)
                self.assertInvalidAt(result, _package_path(keys) + "[0].key")

    def test_module_details_intro_blocks_accepts_shared_blocks(self):
        def mutate(root):
            data = _read(root / "chapters/05-module-details.json")
            data["module_details"]["intro_blocks"] = [
                {"type": "text", "content": "intro"},
                {"type": "ordered_list", "items": ["one"]},
                {"type": "table", "columns": ["a"], "rows": [["b"]]},
                {
                    "type": "mermaid",
                    "title": "Intro flow",
                    "diagram_type": "flowchart",
                    "source": "flowchart LR\nA-->B",
                },
                {"type": "code", "language": "python", "content": "print('ok')"},
            ]
            write_json(root / "chapters/05-module-details.json", data)

        self.assertValid(self.validate_package(mutate))

    def test_mermaid_block_title_is_required(self):
        def mutate(root):
            data = _read(root / "chapters/05-module-details.json")
            data["module_details"]["intro_blocks"] = [
                {"type": "mermaid", "diagram_type": "flowchart", "source": "flowchart LR\nA-->B"}
            ]
            write_json(root / "chapters/05-module-details.json", data)

        result = self.validate_package(mutate)
        self.assertInvalidAt(result, "$.module_details.intro_blocks[0]")

    def test_module_details_intro_blocks_rejects_unknown_block_types(self):
        def mutate(root):
            data = _read(root / "chapters/05-module-details.json")
            data["module_details"]["intro_blocks"] = [{"type": "details"}]
            write_json(root / "chapters/05-module-details.json", data)

        result = self.validate_package(mutate)
        self.assertInvalidAt(result, "$.module_details.intro_blocks[0]")

    def test_code_block_title_is_optional(self):
        self.assertValid(self.validate_package())

    def test_main_flow_entry_location_is_optional(self):
        def mutate(root):
            data = _read(root / "chapters/04-main-flows.json")
            del data["main_flows"]["flows"][0]["entry"]["location"]
            write_json(root / "chapters/04-main-flows.json", data)

        self.assertValid(self.validate_package(mutate))


def _read(path):
    import json

    return json.loads(path.read_text(encoding="utf-8"))


def _package_path(keys):
    parts = []
    for key in keys:
        if isinstance(key, int):
            parts[-1] += f"[{key}]"
        else:
            parts.append(str(key))
    return "$." + ".".join(parts)


if __name__ == "__main__":
    unittest.main()
