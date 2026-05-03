import contextlib
import importlib.util
import io
import json
import subprocess
import sys
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
RENDERER = ROOT / "scripts/render_markdown.py"
VALIDATOR = ROOT / "scripts/validate_mermaid.py"
FIXTURE = ROOT / "tests/fixtures/valid-phase2.dsl.json"
PYTHON = sys.executable


def load_renderer_module():
    spec = importlib.util.spec_from_file_location("render_markdown_under_test", RENDERER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def call_main(module, argv):
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        code = module.main(argv)
    return code, stdout.getvalue(), stderr.getvalue()


def valid_document():
    return deepcopy(json.loads(FIXTURE.read_text(encoding="utf-8")))


def write_json(tmpdir, name, document):
    path = Path(tmpdir) / name
    path.write_text(json.dumps(document, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def run_validate_dsl(path):
    return subprocess.run(
        [PYTHON, str(ROOT / "scripts/validate_dsl.py"), str(path)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

REFERENCE_EXPECTATIONS = {
    "references/dsl-spec.md": [
        "# create-structure-md DSL Spec",
        "## DSL Purpose",
        "## Top-Level Fields",
        "## Chapter Fields",
        "## Support Data",
        "does not analyze repositories",
    ],
    "references/document-structure.md": [
        "# create-structure-md Document Structure",
        "## Fixed 9-Chapter Markdown Outline",
        "## Output Filename Policy",
        "module- or system-specific",
        "Generic-only filenames are forbidden",
    ],
    "references/mermaid-rules.md": [
        "# create-structure-md Mermaid Rules",
        "## Supported MVP Diagram Types",
        "## Strict And Static Validation",
        "## No Graphviz",
        "Mermaid code blocks",
    ],
    "references/review-checklist.md": [
        "# create-structure-md Review Checklist",
        "## Final Output Path",
        "## Fixed Chapters",
        "## Mermaid Validation",
        "## No Repo Analysis",
        "single Markdown file",
    ],
}


class ReferenceSignpostTests(unittest.TestCase):
    def test_reference_files_contain_required_signposts(self):
        for relative_path, expected_phrases in REFERENCE_EXPECTATIONS.items():
            text = (ROOT / relative_path).read_text(encoding="utf-8")
            with self.subTest(path=relative_path):
                for phrase in expected_phrases:
                    self.assertIn(phrase, text)


class RendererCliAndFilenameTests(unittest.TestCase):
    def test_missing_positional_dsl_file_is_cli_error(self):
        completed = subprocess.run(
            [PYTHON, str(RENDERER), "--output-dir", "."],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(2, completed.returncode)
        self.assertIn("dsl_file", completed.stderr)

    def test_missing_dsl_path_fails_without_output(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            completed = subprocess.run(
                [PYTHON, str(RENDERER), str(Path(tmpdir) / "missing.dsl.json"), "--output-dir", tmpdir],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(2, completed.returncode)
            self.assertIn("file not found", completed.stderr)
            self.assertEqual([], list(Path(tmpdir).glob("*.md")))

    def test_invalid_json_fails_without_output(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            bad_json = Path(tmpdir) / "bad.dsl.json"
            bad_json.write_text("{not json", encoding="utf-8")
            completed = subprocess.run(
                [PYTHON, str(RENDERER), str(bad_json), "--output-dir", tmpdir],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(2, completed.returncode)
            self.assertIn("invalid JSON", completed.stderr)
            self.assertEqual([], list(Path(tmpdir).glob("*.md")))

    def test_missing_document_output_file_fails_defensively(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            del document["document"]["output_file"]
            dsl_path = write_json(tmpdir, "missing-output-file.dsl.json", document)
            completed = subprocess.run(
                [PYTHON, str(RENDERER), str(dsl_path), "--output-dir", tmpdir],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(2, completed.returncode)
            self.assertIn("document.output_file", completed.stderr)
            self.assertEqual([], list(Path(tmpdir).glob("*.md")))

    def test_unsafe_output_filename_fails_defensively(self):
        unsafe_names = [
            "create-structure-md_STRUCTURE_DESIGN.txt",
            "nested/create-structure-md_STRUCTURE_DESIGN.md",
            "nested\\create-structure-md_STRUCTURE_DESIGN.md",
            "../create-structure-md_STRUCTURE_DESIGN.md",
            "bad\u0001name.md",
        ]
        for output_file in unsafe_names:
            with tempfile.TemporaryDirectory() as tmpdir:
                document = valid_document()
                document["document"]["output_file"] = output_file
                dsl_path = write_json(tmpdir, "unsafe-output.dsl.json", document)
                completed = subprocess.run(
                    [PYTHON, str(RENDERER), str(dsl_path), "--output-dir", tmpdir],
                    cwd=ROOT,
                    text=True,
                    capture_output=True,
                    check=False,
                )
                with self.subTest(output_file=output_file):
                    self.assertEqual(2, completed.returncode)
                    self.assertIn("document.output_file", completed.stderr)
                    self.assertEqual([], list(Path(tmpdir).glob("*.md")))

    def test_generic_only_output_filename_fails_defensively(self):
        for output_file in ["STRUCTURE_DESIGN.md", "structure_design.md", "design.md", "软件结构设计说明书.md"]:
            with tempfile.TemporaryDirectory() as tmpdir:
                document = valid_document()
                document["document"]["output_file"] = output_file
                dsl_path = write_json(tmpdir, "generic-output.dsl.json", document)
                completed = subprocess.run(
                    [PYTHON, str(RENDERER), str(dsl_path), "--output-dir", tmpdir],
                    cwd=ROOT,
                    text=True,
                    capture_output=True,
                    check=False,
                )
                with self.subTest(output_file=output_file):
                    self.assertEqual(2, completed.returncode)
                    self.assertIn("generic-only output filename", completed.stderr)
                    self.assertEqual([], list(Path(tmpdir).glob("*.md")))

    def test_output_filename_must_include_documented_object_token(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            document["document"]["output_file"] = "unrelated_SCOPE_STRUCTURE_DESIGN.md"
            dsl_path = write_json(tmpdir, "unrelated-output.dsl.json", document)
            completed = subprocess.run(
                [PYTHON, str(RENDERER), str(dsl_path), "--output-dir", tmpdir],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(2, completed.returncode)
            self.assertIn("documented object name", completed.stderr)
            self.assertEqual([], list(Path(tmpdir).glob("*.md")))

    def test_malformed_json_shape_fails_as_input_error_without_traceback(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            del document["architecture_views"]
            dsl_path = write_json(tmpdir, "malformed-shape.dsl.json", document)
            completed = subprocess.run(
                [PYTHON, str(RENDERER), str(dsl_path), "--output-dir", tmpdir],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(2, completed.returncode)
            self.assertIn("ERROR:", completed.stderr)
            self.assertIn("DSL shape", completed.stderr)
            self.assertNotIn("Traceback", completed.stderr)
            self.assertEqual([], list(Path(tmpdir).glob("*.md")))

    def test_write_oserror_fails_as_render_error_without_traceback(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            output_file = document["document"]["output_file"]
            (Path(tmpdir) / output_file).mkdir()
            dsl_path = write_json(tmpdir, "write-failure.dsl.json", document)
            completed = subprocess.run(
                [PYTHON, str(RENDERER), str(dsl_path), "--output-dir", tmpdir, "--overwrite"],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(1, completed.returncode)
            self.assertIn("ERROR:", completed.stderr)
            self.assertIn("failed to write", completed.stderr)
            self.assertNotIn("Traceback", completed.stderr)

    def test_spaces_are_written_exactly_without_silent_rename(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            document["document"]["output_file"] = "create structure md_STRUCTURE_DESIGN.md"
            dsl_path = write_json(tmpdir, "spaces-output.dsl.json", document)
            completed = subprocess.run(
                [PYTHON, str(RENDERER), str(dsl_path), "--output-dir", tmpdir],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(0, completed.returncode, completed.stderr)
            self.assertTrue((Path(tmpdir) / "create structure md_STRUCTURE_DESIGN.md").is_file())
            self.assertFalse((Path(tmpdir) / "create_structure_md_STRUCTURE_DESIGN.md").exists())

    def test_output_filename_policy_matches_validate_dsl_semantics(self):
        cases = [
            ("STRUCTURE_DESIGN.md", False, "generic-only output filename"),
            ("structure_design.md", False, "generic-only output filename"),
            ("structure-design.md", False, "generic-only output filename"),
            ("structuredesign.md", False, "generic-only output filename"),
            ("design.md", False, "generic-only output filename"),
            ("软件结构设计说明书.md", False, "generic-only output filename"),
            ("Structure_Design.md", False, "generic-only output filename"),
            ("software_system_design.md", False, "generic-only output filename"),
            ("unrelated_SCOPE_STRUCTURE_DESIGN.md", False, "documented object name"),
            ("nested/create-structure-md_STRUCTURE_DESIGN.md", False, "document.output_file"),
            ("nested\\create-structure-md_STRUCTURE_DESIGN.md", False, "document.output_file"),
            ("../create-structure-md_STRUCTURE_DESIGN.md", False, "document.output_file"),
            ("bad\u0001name.md", False, "document.output_file"),
            ("create structure md_STRUCTURE_DESIGN.md", True, ""),
            ("CREATE-STRUCTURE-MD_STRUCTURE_DESIGN.md", True, ""),
        ]
        for output_file, should_accept, renderer_error in cases:
            with tempfile.TemporaryDirectory() as tmpdir:
                document = valid_document()
                document["document"]["output_file"] = output_file
                dsl_path = write_json(tmpdir, "filename-policy.dsl.json", document)

                dsl_result = run_validate_dsl(dsl_path)
                renderer_result = subprocess.run(
                    [PYTHON, str(RENDERER), str(dsl_path), "--output-dir", tmpdir],
                    cwd=ROOT,
                    text=True,
                    capture_output=True,
                    check=False,
                )

                with self.subTest(output_file=output_file):
                    self.assertEqual(should_accept, dsl_result.returncode == 0, dsl_result.stderr)
                    self.assertEqual(should_accept, renderer_result.returncode == 0, renderer_result.stderr)
                    if should_accept:
                        self.assertTrue((Path(tmpdir) / output_file).is_file())
                    else:
                        self.assertIn(renderer_error, renderer_result.stderr)


if __name__ == "__main__":
    unittest.main()
