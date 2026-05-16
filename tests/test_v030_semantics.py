import tempfile
import unittest
from pathlib import Path

from tests.helpers_v030 import write_valid_package

from scripts.v030_package import load_manifest_package
from scripts.v030_semantics import semantic_validation_result


class V030SemanticValidationTests(unittest.TestCase):
    def test_layer_and_module_references_must_resolve(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            package = load_manifest_package(write_valid_package(tmpdir))
            package.chapters["module_layers"]["modules"][0]["layer_id"] = "missing_layer"
            package.chapters["module_layers"]["modules"][0]["collaborates_with"][0]["module_ref"] = "missing_module"
            result = semantic_validation_result(package)
        messages = [issue.message for issue in result.errors]
        self.assertTrue(any("layer-id does not resolve" in message for message in messages))
        self.assertTrue(any("module-id does not resolve" in message for message in messages))

    def test_mechanism_references_must_resolve_to_manifest_file_stems(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            package = load_manifest_package(write_valid_package(tmpdir))
            package.chapters["risks_validation"]["risks"][0]["related_mechanisms"] = ["missing_mechanism"]
            result = semantic_validation_result(package)
        self.assertFalse(result.ok)
        self.assertTrue(any("mechanism-key does not resolve" in issue.message for issue in result.errors))

    def test_diagram_ids_are_unique_package_wide(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            package = load_manifest_package(write_valid_package(tmpdir))
            package.mechanisms[0].data["diagram"] = {
                "id": "mainline_overview",
                "title": "重复图",
                "diagram_type": "flowchart",
                "description": "重复 ID。",
                "source": "flowchart TD\n  a[开始] --> b[结束]",
            }
            result = semantic_validation_result(package)
        self.assertFalse(result.ok)
        self.assertTrue(any("duplicate diagram-id" in issue.message for issue in result.errors))

    def test_internal_ids_are_unique_in_their_declared_ranges(self):
        cases = [
            ("layers", lambda package: package.chapters["module_layers"]["layers"][1].__setitem__("layer_id", "api"), "duplicate layer-id"),
            ("modules", lambda package: package.chapters["module_layers"]["modules"][1].__setitem__("module_id", "storage_api"), "duplicate module-id"),
            ("mainlines", lambda package: package.chapters["repository_mainline"]["mainlines"].append(dict(package.chapters["repository_mainline"]["mainlines"][0])), "duplicate mainline-id"),
            ("risks", lambda package: package.chapters["risks_validation"]["risks"].append(dict(package.chapters["risks_validation"]["risks"][0])), "duplicate risk-id"),
            ("assumptions", lambda package: package.chapters["risks_validation"]["assumptions"].append(dict(package.chapters["risks_validation"]["assumptions"][0])), "duplicate assumption-id"),
            ("validation_gaps", lambda package: package.chapters["risks_validation"]["validation_gaps"].append(dict(package.chapters["risks_validation"]["validation_gaps"][0])), "duplicate gap-id"),
            ("low_confidence_items", lambda package: package.chapters["risks_validation"]["low_confidence_items"].append(dict(package.chapters["risks_validation"]["low_confidence_items"][0])), "duplicate item-id"),
        ]
        for name, mutate, expected in cases:
            with self.subTest(name=name):
                with tempfile.TemporaryDirectory() as tmpdir:
                    package = load_manifest_package(write_valid_package(tmpdir))
                    mutate(package)
                    result = semantic_validation_result(package)
                self.assertFalse(result.ok)
                self.assertTrue(any(expected in issue.message for issue in result.errors), [issue.format() for issue in result.errors])

    def test_empty_key_mechanisms_requires_chapter8_gap(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            package = load_manifest_package(write_valid_package(tmpdir, key_mechanisms=False))
            package.chapters["risks_validation"]["validation_gaps"] = []
            result = semantic_validation_result(package)
        self.assertFalse(result.ok)
        self.assertTrue(any("no_key_mechanisms_selected" in issue.message for issue in result.errors))

    def test_ordered_arrays_start_at_one_without_gaps(self):
        cases = [
            ("reading_route", lambda package: package.chapters["repository_overview"]["reading_route"]["steps"][0].__setitem__("order", 2)),
            ("mainline_steps", lambda package: package.chapters["repository_mainline"]["mainlines"][0]["steps"][1].__setitem__("order", 3)),
            ("mechanism_flow", lambda package: package.mechanisms[0].data["flow"][0].__setitem__("order", 2)),
        ]
        for name, mutate in cases:
            with self.subTest(name=name):
                with tempfile.TemporaryDirectory() as tmpdir:
                    package = load_manifest_package(write_valid_package(tmpdir))
                    mutate(package)
                    result = semantic_validation_result(package)
                self.assertFalse(result.ok)
                self.assertTrue(any("order values must start at 1 without gaps" in issue.message for issue in result.errors))

    def test_low_confidence_manifest_path_must_resolve_to_manifest_child(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            package = load_manifest_package(write_valid_package(tmpdir))
            package.chapters["risks_validation"]["low_confidence_items"][0]["location"] = {
                "kind": "manifest_path",
                "path": "chapters/not-declared.json",
            }
            result = semantic_validation_result(package)
        self.assertFalse(result.ok)
        self.assertTrue(any("diagnostic manifest path does not resolve" in issue.message for issue in result.errors))

    def test_source_ref_paths_resolve_when_repo_root_is_available(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            manifest_path = write_valid_package(str(root / "dsl"))
            repo_root = root / "repo"
            repo_root.mkdir()
            (repo_root / "include").mkdir()
            (repo_root / "include/storage.h").write_text("int storage_init(void);\n", encoding="utf-8")
            package = load_manifest_package(manifest_path)
            result = semantic_validation_result(package, repo_root=repo_root)
        self.assertFalse(result.ok)
        self.assertTrue(any("SourceRef.path does not exist" in issue.message for issue in result.errors))

    def test_source_ref_with_symbol_requires_file_when_repo_root_is_available(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            manifest_path = write_valid_package(str(root / "dsl"))
            repo_root = root / "repo"
            (repo_root / "include").mkdir(parents=True)
            (repo_root / "src").mkdir()
            (repo_root / "port").mkdir()
            (repo_root / "include/storage.h").write_text("int storage_init(void);\n", encoding="utf-8")
            (repo_root / "include/storage_cfg.h").write_text("#define STORAGE_SIZE 1\n", encoding="utf-8")
            (repo_root / "port/storage_port.c").write_text("int storage_port_write(void) { return 0; }\n", encoding="utf-8")
            package = load_manifest_package(manifest_path)
            package.chapters["repository_overview"]["core_capabilities"][0]["entry_points"][0] = {"path": "src", "symbol": "storage_init"}
            result = semantic_validation_result(package, repo_root=repo_root)
        self.assertFalse(result.ok)
        self.assertTrue(any("SourceRef.symbol requires path to identify a source file" in issue.message for issue in result.errors))


if __name__ == "__main__":
    unittest.main()
