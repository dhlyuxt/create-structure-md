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

    def test_directory_dsl_path_fails_as_input_error_without_traceback(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            dsl_dir = Path(tmpdir) / "directory.dsl.json"
            dsl_dir.mkdir()
            completed = subprocess.run(
                [PYTHON, str(RENDERER), str(dsl_dir), "--output-dir", tmpdir],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(2, completed.returncode)
            self.assertIn("ERROR:", completed.stderr)
            self.assertIn("unable to read", completed.stderr)
            self.assertNotIn("Traceback", completed.stderr)
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

    def test_non_string_filename_context_fails_as_input_error_without_traceback(self):
        cases = [
            ("document.project_name", lambda document: document["document"].__setitem__("project_name", 123)),
            (
                "architecture_views.module_intro.rows[0].module_id",
                lambda document: document["architecture_views"]["module_intro"]["rows"][0].__setitem__("module_id", 123),
            ),
            (
                "architecture_views.module_intro.rows[0].module_name",
                lambda document: document["architecture_views"]["module_intro"]["rows"][0].__setitem__("module_name", 123),
            ),
            (
                "module_design.modules[0].name",
                lambda document: document["module_design"]["modules"][0].__setitem__("name", 123),
            ),
        ]
        for field_name, mutate in cases:
            with tempfile.TemporaryDirectory() as tmpdir:
                document = valid_document()
                mutate(document)
                dsl_path = write_json(tmpdir, "non-string-context.dsl.json", document)
                completed = subprocess.run(
                    [PYTHON, str(RENDERER), str(dsl_path), "--output-dir", tmpdir],
                    cwd=ROOT,
                    text=True,
                    capture_output=True,
                    check=False,
                )
                with self.subTest(field_name=field_name):
                    self.assertEqual(2, completed.returncode)
                    self.assertIn("ERROR:", completed.stderr)
                    self.assertIn("filename context", completed.stderr)
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

    def test_existing_output_policy_refuses_to_overwrite_by_default(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            output_file = document["document"]["output_file"]
            output_path = Path(tmpdir) / output_file
            output_path.write_text("old content", encoding="utf-8")
            dsl_path = write_json(tmpdir, "existing-output.dsl.json", document)
            completed = subprocess.run(
                [PYTHON, str(RENDERER), str(dsl_path), "--output-dir", tmpdir],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(1, completed.returncode)
            self.assertIn("already exists", completed.stderr)
            self.assertEqual("old content", output_path.read_text(encoding="utf-8"))

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


class RendererOutputSafetyTests(unittest.TestCase):
    def test_default_render_refuses_to_overwrite_existing_output(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            dsl_path = write_json(tmpdir, "structure.dsl.json", document)
            output_path = Path(tmpdir) / document["document"]["output_file"]
            output_path.write_text("existing content", encoding="utf-8")

            completed = subprocess.run(
                [PYTHON, str(RENDERER), str(dsl_path), "--output-dir", tmpdir],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(1, completed.returncode)
            self.assertIn("already exists", completed.stderr)
            self.assertIn("--overwrite", completed.stderr)
            self.assertIn("--backup", completed.stderr)
            self.assertEqual("existing content", output_path.read_text(encoding="utf-8"))

    def test_default_render_race_does_not_overwrite_newly_created_output(self):
        module = load_renderer_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            dsl_path = write_json(tmpdir, "structure.dsl.json", document)
            output_path = Path(tmpdir) / document["document"]["output_file"]
            output_path.write_text("raced output", encoding="utf-8")

            real_exists = Path.exists

            def stale_output_exists(path):
                if path == output_path:
                    return False
                return real_exists(path)

            with mock.patch.object(module.Path, "exists", stale_output_exists):
                code, stdout, stderr = call_main(
                    module,
                    [str(dsl_path), "--output-dir", tmpdir],
                )

            self.assertEqual(1, code)
            self.assertEqual("", stdout)
            self.assertIn("already exists", stderr)
            self.assertIn("--overwrite", stderr)
            self.assertIn("--backup", stderr)
            self.assertEqual("raced output", output_path.read_text(encoding="utf-8"))

    def test_overwrite_replaces_existing_output_without_creating_backup(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            dsl_path = write_json(tmpdir, "structure.dsl.json", document)
            output_path = Path(tmpdir) / document["document"]["output_file"]
            output_path.write_text("existing content", encoding="utf-8")

            completed = subprocess.run(
                [PYTHON, str(RENDERER), str(dsl_path), "--output-dir", tmpdir, "--overwrite"],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(0, completed.returncode, completed.stderr)
            self.assertNotEqual("existing content", output_path.read_text(encoding="utf-8"))
            self.assertEqual([], list(Path(tmpdir).glob("*.bak-*")))

    def test_backup_preserves_existing_output_before_writing_new_output(self):
        module = load_renderer_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            dsl_path = write_json(tmpdir, "structure.dsl.json", document)
            output_path = Path(tmpdir) / document["document"]["output_file"]
            output_path.write_text("existing content", encoding="utf-8")

            with mock.patch.object(module, "backup_timestamp", return_value="20260503_123456"):
                code, stdout, stderr = call_main(
                    module,
                    [str(dsl_path), "--output-dir", tmpdir, "--backup"],
                )

            backup_path = Path(tmpdir) / "create-structure-md_STRUCTURE_DESIGN.md.bak-20260503_123456"
            self.assertEqual(0, code, stderr)
            self.assertIn("Backup written:", stdout)
            self.assertEqual("existing content", backup_path.read_text(encoding="utf-8"))
            self.assertNotEqual("existing content", output_path.read_text(encoding="utf-8"))

    def test_backup_fails_when_timestamped_backup_path_already_exists(self):
        module = load_renderer_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            dsl_path = write_json(tmpdir, "structure.dsl.json", document)
            output_path = Path(tmpdir) / document["document"]["output_file"]
            backup_path = Path(tmpdir) / "create-structure-md_STRUCTURE_DESIGN.md.bak-20260503_123456"
            output_path.write_text("existing content", encoding="utf-8")
            backup_path.write_text("old backup", encoding="utf-8")

            with mock.patch.object(module, "backup_timestamp", return_value="20260503_123456"):
                code, stdout, stderr = call_main(
                    module,
                    [str(dsl_path), "--output-dir", tmpdir, "--backup"],
                )

            self.assertEqual(1, code)
            self.assertEqual("", stdout)
            self.assertIn("backup path already exists", stderr)
            self.assertEqual("existing content", output_path.read_text(encoding="utf-8"))
            self.assertEqual("old backup", backup_path.read_text(encoding="utf-8"))

    def test_backup_race_does_not_overwrite_newly_created_backup_path(self):
        module = load_renderer_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            dsl_path = write_json(tmpdir, "structure.dsl.json", document)
            output_path = Path(tmpdir) / document["document"]["output_file"]
            backup_path = Path(tmpdir) / "create-structure-md_STRUCTURE_DESIGN.md.bak-20260503_123456"
            output_path.write_text("existing content", encoding="utf-8")
            backup_path.write_text("raced backup", encoding="utf-8")

            real_exists = Path.exists

            def stale_backup_exists(path):
                if path == backup_path:
                    return False
                return real_exists(path)

            with (
                mock.patch.object(module, "backup_timestamp", return_value="20260503_123456"),
                mock.patch.object(module.Path, "exists", stale_backup_exists),
            ):
                code, stdout, stderr = call_main(
                    module,
                    [str(dsl_path), "--output-dir", tmpdir, "--backup"],
                )

            self.assertEqual(1, code)
            self.assertEqual("", stdout)
            self.assertIn("backup path already exists", stderr)
            self.assertEqual("existing content", output_path.read_text(encoding="utf-8"))
            self.assertEqual("raced backup", backup_path.read_text(encoding="utf-8"))

    def test_backup_copy_failure_preserves_existing_output(self):
        module = load_renderer_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            dsl_path = write_json(tmpdir, "structure.dsl.json", document)
            output_path = Path(tmpdir) / document["document"]["output_file"]
            output_path.write_text("existing content", encoding="utf-8")
            backup_path = Path(tmpdir) / "create-structure-md_STRUCTURE_DESIGN.md.bak-20260503_123456"

            real_read_bytes = Path.read_bytes

            def fail_reading_output(path):
                if path == output_path:
                    raise OSError("copy failed")
                return real_read_bytes(path)

            with (
                mock.patch.object(module, "backup_timestamp", return_value="20260503_123456"),
                mock.patch.object(module.Path, "read_bytes", fail_reading_output),
            ):
                code, stdout, stderr = call_main(
                    module,
                    [str(dsl_path), "--output-dir", tmpdir, "--backup"],
                )

            self.assertEqual(1, code)
            self.assertEqual("", stdout)
            self.assertIn("failed to write backup", stderr)
            self.assertEqual("existing content", output_path.read_text(encoding="utf-8"))
            self.assertFalse(backup_path.exists())

    def test_overwrite_and_backup_are_mutually_exclusive(self):
        completed = subprocess.run(
            [PYTHON, str(RENDERER), str(FIXTURE), "--output-dir", ".", "--overwrite", "--backup"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(2, completed.returncode)
        self.assertIn("not allowed with argument", completed.stderr)

class MarkdownPrimitiveTests(unittest.TestCase):
    def test_escape_table_cell_handles_pipe_newline_fence_and_html(self):
        module = load_renderer_module()
        value = "A | B\n<script>alert(1)</script>\n```mermaid\nflowchart TD\n```"
        escaped = module.escape_table_cell(value)
        self.assertIn("A \\| B", escaped)
        self.assertIn("<br>", escaped)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", escaped)
        self.assertNotIn("```", escaped)

    def test_escape_plain_text_preserves_prose_but_blocks_headings_html_and_fences(self):
        module = load_renderer_module()
        value = "# 伪造标题\nInjected heading\n---\nInjected heading 2\n===\n普通 `inline` 文本\n<div>raw</div>\n```python\nx = 1\n```"
        escaped = module.escape_plain_text(value)
        self.assertIn("\\# 伪造标题", escaped)
        self.assertNotIn("\n---", escaped)
        self.assertNotIn("\n===", escaped)
        self.assertIn("\n\\---", escaped)
        self.assertIn("\n\\===", escaped)
        self.assertIn("普通 `inline` 文本", escaped)
        self.assertIn("&lt;div&gt;raw&lt;/div&gt;", escaped)
        self.assertNotIn("```", escaped)

    def test_escape_plain_text_escapes_one_pipe_gfm_table_shape(self):
        module = load_renderer_module()
        value = "a | b\n--- | ---\nx | y"
        escaped = module.escape_plain_text(value)
        self.assertIn("a \\| b", escaped)
        self.assertIn("--- \\| ---", escaped)
        self.assertIn("x \\| y", escaped)
        self.assertNotIn("a | b\n--- | ---\nx | y", escaped)

    def test_render_fixed_table_uses_only_visible_columns_and_escapes_cells(self):
        module = load_renderer_module()
        rows = [
            {
                "module_id": "MOD-HIDDEN",
                "module_name": "渲染|模块",
                "responsibility": "第一行\n第二行",
                "inputs": "<input>",
                "outputs": "Markdown",
                "notes": "```bad```",
                "confidence": "unknown",
                "evidence_refs": ["EV-001"],
            }
        ]
        table = module.render_fixed_table(
            rows,
            [
                ("module_name", "模块名称"),
                ("responsibility", "职责"),
                ("inputs", "输入"),
                ("outputs", "输出"),
                ("notes", "备注"),
            ],
        )
        self.assertIn("| 模块名称 | 职责 | 输入 | 输出 | 备注 |", table)
        self.assertIn("渲染\\|模块", table)
        self.assertIn("第一行<br>第二行", table)
        self.assertIn("&lt;input&gt;", table)
        self.assertNotIn("MOD-HIDDEN", table)
        self.assertNotIn("unknown", table)
        self.assertNotIn("EV-001", table)
        self.assertNotIn("```bad```", table)

    def test_render_extra_table_uses_declared_columns_and_hides_evidence_refs(self):
        module = load_renderer_module()
        table = {
            "id": "TBL-EXTRA",
            "title": "补充表",
            "columns": [{"key": "name", "title": "名称"}, {"key": "note", "title": "说明"}],
            "rows": [{"name": "A", "note": "B|C", "evidence_refs": ["EV-001"]}],
        }
        rendered = module.render_extra_table(table)
        self.assertIn("#### 补充表", rendered)
        self.assertIn("| 名称 | 说明 |", rendered)
        self.assertIn("B\\|C", rendered)
        self.assertNotIn("TBL-EXTRA", rendered)
        self.assertNotIn("EV-001", rendered)

    def test_render_mermaid_block_fences_raw_source_exactly_once(self):
        module = load_renderer_module()
        diagram = {
            "id": "MER-TEST",
            "title": "测试图",
            "description": "用于测试。",
            "source": "flowchart TD\n  A --> B",
        }
        rendered = module.render_mermaid_block(diagram, empty_text="无图。")
        self.assertIn("```mermaid\nflowchart TD\n  A --> B\n```", rendered)
        self.assertEqual(1, rendered.count("```mermaid"))
        self.assertEqual(2, rendered.count("```"))

    def test_render_mermaid_block_empty_optional_diagram_uses_empty_state(self):
        module = load_renderer_module()
        diagram = {"id": "MER-EMPTY", "title": "空图", "description": "", "source": ""}
        rendered = module.render_mermaid_block(diagram, empty_text="未提供运行时序图。")
        self.assertEqual("未提供运行时序图。", rendered.strip())
        self.assertNotIn("```mermaid", rendered)

    def test_render_mermaid_block_rejects_source_that_already_contains_fences(self):
        module = load_renderer_module()
        diagram = {"id": "MER-BAD", "title": "坏图", "description": "", "source": "```mermaid\nflowchart TD\n```"}
        with self.assertRaises(module.RenderError):
            module.render_mermaid_block(diagram, empty_text="无图。")

    def test_safe_source_snippet_fence_uses_longer_fence_than_content(self):
        module = load_renderer_module()
        snippet = {
            "id": "SNIP-001",
            "path": "src/example.py",
            "line_start": 1,
            "line_end": 2,
            "language": "python",
            "purpose": "展示安全 fence。",
            "content": "```python\nprint('nested')\n```",
            "confidence": "observed",
        }
        rendered = module.render_source_snippet(snippet)
        self.assertIn("````python", rendered)
        self.assertIn("```python\nprint('nested')\n```", rendered)
        self.assertTrue(rendered.rstrip().endswith("````"))

    def test_source_snippet_omits_unsafe_language_info_string(self):
        module = load_renderer_module()
        unsafe_languages = [
            "python extra",
            "python\njavascript",
            "py`thon",
        ]
        for language in unsafe_languages:
            with self.subTest(language=language):
                snippet = {
                    "path": "src/example.py",
                    "line_start": 1,
                    "line_end": 1,
                    "language": language,
                    "purpose": "展示安全 info string。",
                    "content": "print('safe')",
                }
                rendered = module.render_source_snippet(snippet)
                self.assertIn("```\nprint('safe')\n```", rendered)
                self.assertNotIn("```python", rendered)
                self.assertNotIn("javascript", rendered)
                self.assertNotIn("py`thon", rendered)


if __name__ == "__main__":
    unittest.main()
