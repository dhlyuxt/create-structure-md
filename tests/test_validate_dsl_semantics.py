import json
import subprocess
import sys
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts/validate_dsl.py"
FIXTURE = ROOT / "tests/fixtures/valid-phase2.dsl.json"
PYTHON = sys.executable


def valid_document():
    return deepcopy(json.loads(FIXTURE.read_text(encoding="utf-8")))


def write_json(tmpdir, name, document):
    path = Path(tmpdir) / name
    path.write_text(json.dumps(document, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def run_validator(path, *args):
    return subprocess.run(
        [PYTHON, str(VALIDATOR), str(path), *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


class CliAndSchemaFirstTests(unittest.TestCase):
    def test_valid_fixture_exits_zero_and_prints_success_to_stdout(self):
        completed = run_validator(FIXTURE)
        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertIn("Validation succeeded", completed.stdout)
        self.assertEqual("", completed.stderr)

    def test_missing_file_exits_two_and_uses_stderr(self):
        completed = run_validator(ROOT / "missing.dsl.json")
        self.assertEqual(2, completed.returncode)
        self.assertEqual("", completed.stdout)
        self.assertIn("ERROR", completed.stderr)
        self.assertIn("file not found", completed.stderr)

    def test_invalid_json_exits_two_before_semantic_validation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "broken.dsl.json"
            path.write_text("{ not json", encoding="utf-8")
            completed = run_validator(path)
        self.assertEqual(2, completed.returncode)
        self.assertEqual("", completed.stdout)
        self.assertIn("ERROR", completed.stderr)
        self.assertIn("invalid JSON", completed.stderr)
        self.assertNotIn("semantic", completed.stderr)

    def test_schema_failure_exits_two_before_semantic_validation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            document["document"]["status"] = "almost-final"
            path = write_json(tmpdir, "schema-fail.dsl.json", document)
            completed = run_validator(path)
        self.assertEqual(2, completed.returncode)
        self.assertEqual("", completed.stdout)
        self.assertIn("ERROR", completed.stderr)
        self.assertIn("$.document.status", completed.stderr)
        self.assertIn("schema validation failed", completed.stderr)
        self.assertNotIn("semantic validation failed", completed.stderr)
