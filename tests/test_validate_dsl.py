import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_DIRECTORIES = [
    "references",
    "schemas",
    "scripts",
    "examples",
    "tests",
]

REQUIRED_FILES = [
    "SKILL.md",
    "requirements.txt",
    "references/dsl-spec.md",
    "references/document-structure.md",
    "references/mermaid-rules.md",
    "references/review-checklist.md",
    "schemas/structure-design.schema.json",
    "scripts/validate_dsl.py",
    "scripts/validate_mermaid.py",
    "scripts/render_markdown.py",
    "examples/minimal-from-code.dsl.json",
    "examples/minimal-from-requirements.dsl.json",
    "tests/test_validate_dsl.py",
    "tests/test_validate_mermaid.py",
    "tests/test_render_markdown.py",
]

JSON_SCAFFOLD_FILES = [
    "schemas/structure-design.schema.json",
    "examples/minimal-from-code.dsl.json",
    "examples/minimal-from-requirements.dsl.json",
]


class ScaffoldLayoutTests(unittest.TestCase):
    def test_required_directories_exist(self):
        for relative_path in REQUIRED_DIRECTORIES:
            path = ROOT / relative_path
            with self.subTest(path=relative_path):
                self.assertTrue(path.is_dir(), f"Missing directory: {relative_path}")

    def test_required_files_exist(self):
        for relative_path in REQUIRED_FILES:
            path = ROOT / relative_path
            with self.subTest(path=relative_path):
                self.assertTrue(path.is_file(), f"Missing file: {relative_path}")

    def test_json_scaffold_files_are_parseable(self):
        for relative_path in JSON_SCAFFOLD_FILES:
            path = ROOT / relative_path
            with self.subTest(path=relative_path):
                json.loads(path.read_text(encoding="utf-8"))


class DependencyContractTests(unittest.TestCase):
    def test_requirements_contains_runtime_dependency_only(self):
        requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8")
        dependency_lines = [
            line.strip()
            for line in requirements.splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]
        self.assertEqual(["jsonschema"], dependency_lines)
        self.assertNotIn("pytest", requirements)
        self.assertNotIn("requirements-dev", requirements)


if __name__ == "__main__":
    unittest.main()
