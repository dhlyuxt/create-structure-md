import json
import subprocess
import sys
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

SCRIPT_CASES = [
    (
        "scripts/validate_dsl.py",
        ["structure.dsl.json"],
        "DSL validation is not implemented in Phase 1",
    ),
    (
        "scripts/validate_mermaid.py",
        ["--from-dsl", "structure.dsl.json", "--strict"],
        "Mermaid validation is not implemented in Phase 1",
    ),
    (
        "scripts/render_markdown.py",
        ["structure.dsl.json", "--output-dir", "."],
        "Markdown rendering is not implemented in Phase 1",
    ),
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


class ScriptStubTests(unittest.TestCase):
    def test_scripts_are_python_executable_stubs(self):
        for relative_path, args, expected_message in SCRIPT_CASES:
            script_path = ROOT / relative_path
            with self.subTest(script=relative_path):
                completed = subprocess.run(
                    [sys.executable, str(script_path), *args],
                    cwd=ROOT,
                    text=True,
                    capture_output=True,
                    check=False,
                )
                combined_output = completed.stdout + completed.stderr
                self.assertEqual(2, completed.returncode)
                self.assertIn(expected_message, combined_output)

    def test_scripts_do_not_claim_success(self):
        forbidden_success_messages = [
            "Validation succeeded",
            "Mermaid validation passed",
            "Markdown rendered",
            "Document written",
        ]
        for relative_path, args, _expected_message in SCRIPT_CASES:
            script_path = ROOT / relative_path
            with self.subTest(script=relative_path):
                completed = subprocess.run(
                    [sys.executable, str(script_path), *args],
                    cwd=ROOT,
                    text=True,
                    capture_output=True,
                    check=False,
                )
                combined_output = completed.stdout + completed.stderr
                for forbidden in forbidden_success_messages:
                    self.assertNotIn(forbidden, combined_output)


if __name__ == "__main__":
    unittest.main()
