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
FIXTURE = ROOT / "tests/fixtures/valid-v2-foundation.dsl.json"
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


def document_with_support_refs():
    document = valid_document()
    document["architecture_views"]["module_intro"]["rows"][0]["evidence_refs"] = ["EV-001"]
    document["architecture_views"]["module_intro"]["rows"][0]["traceability_refs"] = ["TR-001"]
    document["architecture_views"]["module_intro"]["rows"][0]["source_snippet_refs"] = ["SNIP-001"]
    document["evidence"] = [
        {"id": "EV-001", "kind": "source", "title": "模块表证据", "location": "schema", "description": "不内联。", "confidence": "observed"},
    ]
    document["traceability"] = [
        {"id": "TR-001", "source_external_id": "REQ-MODULE", "source_type": "requirement", "target_type": "module", "target_id": "MOD-SKILL", "description": "模块追踪。"},
    ]
    document["source_snippets"] = [
        {"id": "SNIP-001", "path": "scripts/render_markdown.py", "line_start": 2, "line_end": 3, "language": "python", "purpose": "表格行证据。", "content": "print('row support')", "confidence": "observed"},
    ]
    return document


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


class EvidenceModeRenderingTests(unittest.TestCase):
    def test_render_markdown_defaults_to_hidden_evidence_mode(self):
        module = load_renderer_module()
        markdown = module.render_markdown(document_with_support_refs())
        self.assertIn("技能文档生成模块", markdown)
        self.assertNotIn("支持数据", markdown)
        self.assertNotIn("EV-001", markdown)
        self.assertNotIn("REQ-MODULE", markdown)
        self.assertNotIn("Source: scripts/render_markdown.py:2-3", markdown)

    def test_render_markdown_inline_evidence_mode_preserves_support_blocks(self):
        module = load_renderer_module()
        markdown = module.render_markdown(document_with_support_refs(), evidence_mode="inline")
        self.assertIn("支持数据（MOD-SKILL / 技能文档生成模块）", markdown)
        self.assertIn("依据：EV-001（模块表证据，schema）", markdown)
        self.assertIn("关联来源：REQ-MODULE（模块追踪。）", markdown)
        self.assertIn("Source: scripts/render_markdown.py:2-3", markdown)

    def test_hidden_support_context_suppresses_generic_node_support_refs(self):
        module = load_renderer_module()
        document = document_with_support_refs()
        context = module.build_support_context(document, evidence_mode="hidden")
        node = {"evidence_refs": ["EV-001"], "traceability_refs": ["TR-001"], "source_snippet_refs": ["SNIP-001"]}
        self.assertEqual("", module.render_node_support(node, context, target_type="module", target_id="MOD-SKILL"))

    def test_cli_defaults_to_hidden_and_can_opt_into_inline(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            document = document_with_support_refs()
            dsl_path = write_json(tmpdir, "support.dsl.json", document)
            hidden = subprocess.run(
                [PYTHON, str(RENDERER), str(dsl_path), "--output-dir", tmpdir],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(0, hidden.returncode, hidden.stderr)
            output_path = Path(tmpdir) / document["document"]["output_file"]
            hidden_text = output_path.read_text(encoding="utf-8")
            self.assertNotIn("支持数据", hidden_text)

        with tempfile.TemporaryDirectory() as tmpdir:
            document = document_with_support_refs()
            dsl_path = write_json(tmpdir, "support.dsl.json", document)
            inline = subprocess.run(
                [PYTHON, str(RENDERER), str(dsl_path), "--output-dir", tmpdir, "--evidence-mode", "inline"],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(0, inline.returncode, inline.stderr)
            output_path = Path(tmpdir) / document["document"]["output_file"]
            inline_text = output_path.read_text(encoding="utf-8")
            self.assertIn("支持数据", inline_text)

    def test_cli_rejects_appendix_evidence_mode(self):
        completed = subprocess.run(
            [PYTHON, str(RENDERER), str(FIXTURE), "--evidence-mode", "appendix"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(2, completed.returncode)
        self.assertIn("invalid choice", completed.stderr)
        self.assertIn("appendix", completed.stderr)


class RendererNotApplicableFailFastTests(unittest.TestCase):
    def test_renderer_fails_fast_when_v2_mapped_section_has_content_and_reason(self):
        module = load_renderer_module()
        document = valid_document()
        document["module_design"]["modules"][0]["dependencies"] = {
            "rows": [{"dependency_id": "MDEP-ONE"}],
            "not_applicable_reason": "不适用。",
        }
        with self.assertRaisesRegex(module.RenderError, "not_applicable_reason conflict"):
            module.render_markdown(document)

    def test_renderer_fails_fast_when_extra_table_ids_are_duplicate(self):
        module = load_renderer_module()
        document = valid_document()
        document["architecture_views"]["extra_tables"] = [
            {"id": "TBL-DUP", "title": "A", "columns": [{"key": "name", "title": "名称"}], "rows": [{"name": "一"}]},
            {"id": "TBL-DUP", "title": "B", "columns": [{"key": "name", "title": "名称"}], "rows": [{"name": "二"}]},
        ]
        with self.assertRaisesRegex(module.RenderError, "duplicate table.id TBL-DUP"):
            module.render_markdown(document)


REFERENCE_EXPECTATIONS = {
    "references/dsl-spec.md": [
        "# create-structure-md DSL Spec",
        "## DSL Purpose",
        "## DSL Top-Level Fields",
        "## Chapter Fields",
        "## Support Data",
        "does not analyze repositories",
    ],
    "references/document-structure.md": [
        "# create-structure-md Document Structure",
        "## Fixed 9-Chapter Markdown Outline",
        "## Output Filename Policy",
        "Support data renders as compact notes",
        "Extra table row evidence renders after the extra table",
        "Chapter 6 empty tables render the documented empty-state sentences",
        "module- or system-specific",
        "Generic-only filenames are forbidden",
    ],
    "references/mermaid-rules.md": [
        "# create-structure-md Mermaid Rules",
        "## Supported MVP Diagram Types",
        "## Strict/Static Validation Difference",
        "## Graphviz/DOT Rejection",
        "Mermaid code blocks",
    ],
    "references/review-checklist.md": [
        "# create-structure-md Review Checklist",
        "## Final Report",
        "## Boundary Checks",
        "## DSL Policy Checks",
        "## Mermaid Validation",
        "## Text Safety",
        "## Rendered Structure",
        "Confirm evidence notes render near the referenced design item",
        "Confirm traceability uses `target_type` and `target_id` as the authoritative binding",
        "Confirm extra table evidence renders after the table",
        "Confirm no repo analysis",
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


class RendererV2VersionTests(unittest.TestCase):
    def test_renderer_rejects_v1_before_output_filename_validation_or_rendering(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            completed = subprocess.run(
                [PYTHON, str(RENDERER), str(ROOT / "tests/fixtures/valid-phase2.dsl.json"), "--output-dir", tmpdir],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(2, completed.returncode)
            self.assertIn("V1 DSL is not supported by the V2 renderer", completed.stderr)
            self.assertEqual([], list(Path(tmpdir).glob("*.md")))

    def test_render_markdown_api_rejects_non_v2_document_before_rendering(self):
        module = load_renderer_module()
        with self.assertRaisesRegex(module.InputError, "V1 DSL is not supported by the V2 renderer"):
            module.render_markdown({"dsl_version": "0.1.0"})


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

    def test_backup_render_race_without_taken_backup_does_not_overwrite_newly_created_output(self):
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
                    [str(dsl_path), "--output-dir", tmpdir, "--backup"],
                )

            self.assertEqual(1, code)
            self.assertEqual("", stdout)
            self.assertIn("already exists", stderr)
            self.assertIn("--overwrite", stderr)
            self.assertIn("--backup", stderr)
            self.assertEqual("raced output", output_path.read_text(encoding="utf-8"))
            self.assertEqual([], list(Path(tmpdir).glob("*.bak-*")))

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

    def test_escape_plain_text_blocks_empty_atx_headings(self):
        module = load_renderer_module()
        escaped = module.escape_plain_text("#\n###\n######")
        self.assertEqual("\\#\n\\###\n\\######", escaped)
        self.assertNotIn("\n###\n", escaped)

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


class SupportDataPrimitiveTests(unittest.TestCase):
    def test_build_support_context_indexes_support_data_by_id_and_trace_target(self):
        module = load_renderer_module()
        document = valid_document()
        document["evidence"] = [
            {"id": "EV-001", "kind": "source", "title": "入口脚本", "location": "scripts/render_markdown.py:1", "description": "渲染入口。", "confidence": "observed"},
        ]
        document["traceability"] = [
            {"id": "TR-001", "source_external_id": "REQ-001", "source_type": "requirement", "target_type": "module", "target_id": "MOD-SKILL", "description": "模块需求。"},
            {"id": "TR-002", "source_external_id": "REQ-002", "source_type": "requirement", "target_type": "runtime_unit", "target_id": "RUN-GENERATE", "description": ""},
        ]
        document["source_snippets"] = [
            {"id": "SNIP-001", "path": "scripts/render_markdown.py", "line_start": 1, "line_end": 3, "language": "python", "purpose": "证明渲染入口。", "content": "def main():\n    return 0", "confidence": "observed"},
        ]

        context = module.build_support_context(document)

        self.assertEqual("入口脚本", context.evidence_by_id["EV-001"]["title"])
        self.assertEqual("SNIP-001", context.snippets_by_id["SNIP-001"]["id"])
        self.assertEqual(["TR-001"], [item["id"] for item in context.traceability_by_target[("module", "MOD-SKILL")]])
        self.assertEqual(["TR-002"], [item["id"] for item in context.traceability_by_target[("runtime_unit", "RUN-GENERATE")]])

    def test_render_node_support_combines_refs_authoritative_traceability_and_deduplicates(self):
        module = load_renderer_module()
        document = valid_document()
        document["evidence"] = [
            {"id": "EV-001", "kind": "source", "title": "入口脚本", "location": "scripts/render_markdown.py:1", "description": "很长描述不应内联。", "confidence": "observed"},
        ]
        document["traceability"] = [
            {"id": "TR-001", "source_external_id": "REQ-001", "source_type": "requirement", "target_type": "module", "target_id": "MOD-SKILL", "description": "覆盖模块生成能力。"},
        ]
        document["source_snippets"] = [
            {"id": "SNIP-001", "path": "scripts/render_markdown.py", "line_start": 10, "line_end": 12, "language": "python", "purpose": "展示入口。", "content": "def main():\n    return 0", "confidence": "observed"},
        ]
        node = {
            "evidence_refs": ["EV-001", "EV-001"],
            "traceability_refs": ["TR-001"],
            "source_snippet_refs": ["SNIP-001"],
        }
        context = module.build_support_context(document, evidence_mode="inline")

        rendered = module.render_node_support(node, context, target_type="module", target_id="MOD-SKILL")

        self.assertEqual(1, rendered.count("依据：EV-001（入口脚本，scripts/render_markdown.py:1）"))
        self.assertEqual(1, rendered.count("关联来源：REQ-001（覆盖模块生成能力。）"))
        self.assertIn("Source: scripts/render_markdown.py:10-12", rendered)
        self.assertIn("Purpose: 展示入口。", rendered)
        self.assertIn("```python\ndef main():\n    return 0\n```", rendered)
        self.assertNotIn("很长描述不应内联", rendered)

    def test_render_node_support_collapses_label_newlines_inside_bullets(self):
        module = load_renderer_module()
        document = valid_document()
        document["evidence"] = [
            {
                "id": "EV-001",
                "kind": "source",
                "title": "safe\n- injected",
                "location": "scripts/render_markdown.py:1\r\n> quote",
                "description": "not rendered",
                "confidence": "observed",
            },
        ]
        document["traceability"] = [
            {
                "id": "TR-001",
                "source_external_id": "REQ-001",
                "source_type": "requirement",
                "target_type": "module",
                "target_id": "MOD-SKILL",
                "description": "desc\n> quote\r\n- injected",
            },
        ]
        node = {
            "evidence_refs": ["EV-001"],
            "traceability_refs": ["TR-001"],
        }
        context = module.build_support_context(document, evidence_mode="inline")

        rendered = module.render_node_support(node, context, target_type="module", target_id="MOD-SKILL")

        self.assertNotIn("\n- injected", rendered)
        self.assertNotIn("\n> quote", rendered)
        self.assertIn("- 依据：EV-001（safe - injected，scripts/render_markdown.py:1 &gt; quote）", rendered)
        self.assertIn("- 关联来源：REQ-001（desc &gt; quote - injected）", rendered)

    def test_render_node_support_returns_empty_string_when_no_support_exists(self):
        module = load_renderer_module()
        context = module.build_support_context(valid_document())
        rendered = module.render_node_support({}, context, target_type="module", target_id="MOD-SKILL")
        self.assertEqual("", rendered)


class SupportDataTablePlacementTests(unittest.TestCase):
    def test_module_intro_support_renders_after_table_grouped_by_stable_row_id(self):
        module = load_renderer_module()
        document = valid_document()
        document["architecture_views"]["module_intro"]["rows"][0]["evidence_refs"] = ["EV-001"]
        document["architecture_views"]["module_intro"]["rows"][0]["traceability_refs"] = ["TR-001"]
        document["architecture_views"]["module_intro"]["rows"][0]["source_snippet_refs"] = ["SNIP-001"]
        document["evidence"] = [
            {"id": "EV-001", "kind": "source", "title": "模块表证据", "location": "schema", "description": "不内联。", "confidence": "observed"},
        ]
        document["traceability"] = [
            {"id": "TR-001", "source_external_id": "REQ-MODULE", "source_type": "requirement", "target_type": "module", "target_id": "MOD-SKILL", "description": "模块追踪。"},
        ]
        document["source_snippets"] = [
            {"id": "SNIP-001", "path": "scripts/render_markdown.py", "line_start": 1, "line_end": 2, "language": "python", "purpose": "表格行证据。", "content": "print('row support')", "confidence": "observed"},
        ]

        markdown = module.render_markdown(document, evidence_mode="inline")
        section = section_between(markdown, "### 3.2 各模块介绍", "### 3.3 模块关系图")

        self.assertIn("| 模块名称 | 职责 | 输入 | 输出 | 备注 |", section)
        self.assertIn("支持数据（MOD-SKILL / 技能文档生成模块）", section)
        self.assertIn("依据：EV-001（模块表证据，schema）", section)
        self.assertIn("关联来源：REQ-MODULE（模块追踪。）", section)
        self.assertIn("Source: scripts/render_markdown.py:1-2", section)
        table_text = section.split("支持数据（MOD-SKILL / 技能文档生成模块）", 1)[0]
        self.assertNotIn("EV-001", table_text)
        self.assertNotIn("REQ-MODULE", table_text)
        self.assertNotIn("SNIP-001", table_text)

    def test_chapter_6_and_7_table_support_renders_after_tables_not_inside_cells(self):
        module = load_renderer_module()
        document = valid_document()
        document["configuration_data_dependencies"]["configuration_items"]["rows"][0]["evidence_refs"] = ["EV-CFG"]
        document["configuration_data_dependencies"]["dependencies"]["rows"][0]["traceability_refs"] = ["TR-DEP"]
        document["cross_module_collaboration"]["collaboration_scenarios"]["rows"][0]["source_snippet_refs"] = ["SNIP-COL"]
        document["evidence"] = [
            {"id": "EV-CFG", "kind": "note", "title": "配置证据", "location": "", "description": "", "confidence": "observed"},
        ]
        document["traceability"] = [
            {"id": "TR-DEP", "source_external_id": "REQ-DEP", "source_type": "requirement", "target_type": "dependency", "target_id": "SYSDEP-JSONSCHEMA", "description": ""},
        ]
        document["source_snippets"] = [
            {"id": "SNIP-COL", "path": "src/collab.py", "line_start": 4, "line_end": 5, "language": "python", "purpose": "协作证据。", "content": "collaborate()", "confidence": "observed"},
        ]

        markdown = module.render_markdown(document, evidence_mode="inline")
        chapter_6 = section_between(markdown, "## 6. 配置、数据与依赖关系", "## 7. 跨模块协作关系")
        chapter_7 = section_between(markdown, "## 7. 跨模块协作关系", "## 8. 关键流程")

        self.assertIn("支持数据（CFG-001 / 输出目录）", chapter_6)
        self.assertIn("依据：EV-CFG（配置证据）", chapter_6)
        self.assertIn("支持数据（SYSDEP-JSONSCHEMA / jsonschema）", chapter_6)
        self.assertIn("关联来源：REQ-DEP", chapter_6)
        self.assertIn("支持数据（COL-001 / DSL 校验后渲染）", chapter_7)
        self.assertIn("Source: src/collab.py:4-5", chapter_7)
        self.assertNotIn("| EV-CFG |", chapter_6)
        self.assertNotIn("| REQ-DEP |", chapter_6)
        self.assertNotIn("| SNIP-COL |", chapter_7)

    def test_core_capability_and_runtime_authoritative_traceability_render_without_local_backlinks(self):
        module = load_renderer_module()
        document = valid_document()
        document["system_overview"]["core_capabilities"][0].pop("traceability_refs", None)
        document["runtime_view"]["runtime_units"]["rows"][0]["traceability_refs"] = []
        document["traceability"] = [
            {
                "id": "TR-CAP-AUTH",
                "source_external_id": "REQ-CAP-AUTH",
                "source_type": "requirement",
                "target_type": "core_capability",
                "target_id": "CAP-001",
                "description": "核心能力需求。",
            },
            {
                "id": "TR-RUN-AUTH",
                "source_external_id": "REQ-RUN-AUTH",
                "source_type": "requirement",
                "target_type": "runtime_unit",
                "target_id": "RUN-GENERATE",
                "description": "运行单元需求。",
            },
        ]

        markdown = module.render_markdown(document, evidence_mode="inline")
        chapter_2 = section_between(markdown, "## 2. 系统概览", "## 3. 架构视图")
        chapter_5 = section_between(markdown, "### 5.2 运行单元说明", "### 5.3 运行时流程图")

        self.assertIn("支持数据（CAP-001 / 结构设计文档生成）", chapter_2)
        self.assertIn("关联来源：REQ-CAP-AUTH（核心能力需求。）", chapter_2)
        self.assertIn("支持数据（RUN-GENERATE / 文档生成命令序列）", chapter_5)
        self.assertIn("关联来源：REQ-RUN-AUTH（运行单元需求。）", chapter_5)
        self.assertNotIn("| REQ-CAP-AUTH |", chapter_2)
        self.assertNotIn("| REQ-RUN-AUTH |", chapter_5)

    def test_data_artifact_and_collaboration_authoritative_traceability_render_without_local_backlinks(self):
        module = load_renderer_module()
        document = valid_document()
        document["configuration_data_dependencies"]["structural_data_artifacts"]["rows"][0]["traceability_refs"] = []
        document["cross_module_collaboration"]["collaboration_scenarios"]["rows"][0]["traceability_refs"] = []
        document["traceability"] = [
            {
                "id": "TR-DATA-AUTH",
                "source_external_id": "REQ-DATA-AUTH",
                "source_type": "requirement",
                "target_type": "data_artifact",
                "target_id": "DATA-001",
                "description": "结构数据需求。",
            },
            {
                "id": "TR-COL-AUTH",
                "source_external_id": "REQ-COL-AUTH",
                "source_type": "requirement",
                "target_type": "collaboration",
                "target_id": "COL-001",
                "description": "协作需求。",
            },
        ]

        markdown = module.render_markdown(document, evidence_mode="inline")
        chapter_6 = section_between(markdown, "## 6. 配置、数据与依赖关系", "## 7. 跨模块协作关系")
        chapter_7 = section_between(markdown, "## 7. 跨模块协作关系", "## 8. 关键流程")

        self.assertIn("支持数据（DATA-001 / 结构设计 DSL）", chapter_6)
        self.assertIn("关联来源：REQ-DATA-AUTH（结构数据需求。）", chapter_6)
        self.assertIn("支持数据（COL-001 / DSL 校验后渲染）", chapter_7)
        self.assertIn("关联来源：REQ-COL-AUTH（协作需求。）", chapter_7)
        self.assertNotIn("| REQ-DATA-AUTH |", chapter_6)
        self.assertNotIn("| REQ-COL-AUTH |", chapter_7)


class NodeLevelSupportPlacementTests(unittest.TestCase):
    def test_module_design_and_provided_capability_support_render_near_nodes(self):
        module = load_renderer_module()
        document = valid_document()
        module_item = document["module_design"]["modules"][0]
        capability = module_item["external_capability_details"]["provided_capabilities"]["rows"][0]
        module_item["evidence_refs"] = ["EV-MODULE"]
        module_item["source_snippet_refs"] = ["SNIP-MODULE"]
        capability["traceability_refs"] = []
        document["evidence"] = [
            {"id": "EV-MODULE", "kind": "analysis", "title": "模块设计依据", "location": "design note", "description": "", "confidence": "observed"},
        ]
        document["traceability"] = [
            {"id": "TR-CAP", "source_external_id": "REQ-CAP", "source_type": "requirement", "target_type": "provided_capability", "target_id": "CAP-MOD-SKILL-001", "description": "能力追踪。"},
        ]
        document["source_snippets"] = [
            {"id": "SNIP-MODULE", "path": "SKILL.md", "line_start": 1, "line_end": 4, "language": "markdown", "purpose": "模块说明证据。", "content": "---\nname: create-structure-md\n---", "confidence": "observed"},
        ]

        markdown = module.render_markdown(document, evidence_mode="inline")
        module_section = section_between(markdown, "### 4.1 技能文档生成模块", "## 5. 运行时视图")

        self.assertIn("依据：EV-MODULE（模块设计依据，design note）", module_section)
        self.assertIn("Source: SKILL.md:1-4", module_section)
        self.assertIn("支持数据（CAP-MOD-SKILL-001 / 文档 DSL 处理）", module_section)
        self.assertIn("关联来源：REQ-CAP（能力追踪。）", module_section)
        self.assertEqual([], capability["traceability_refs"])
        capability_table = section_between(module_section, "#### 4.1.4 对外接口需求清单", "#### 4.1.5 模块内部结构关系图")
        self.assertNotIn("| REQ-CAP |", capability_table)

    def test_flow_detail_step_and_branch_support_render_near_flow_sections(self):
        module = load_renderer_module()
        document = valid_document()
        flow = document["key_flows"]["flows"][0]
        flow["evidence_refs"] = ["EV-FLOW"]
        flow["steps"][0]["traceability_refs"] = []
        flow["branches_or_exceptions"][0]["source_snippet_refs"] = ["SNIP-BRANCH"]
        document["evidence"] = [
            {"id": "EV-FLOW", "kind": "source", "title": "流程来源", "location": "workflow", "description": "", "confidence": "observed"},
        ]
        document["traceability"] = [
            {"id": "TR-STEP", "source_external_id": "REQ-STEP", "source_type": "requirement", "target_type": "flow_step", "target_id": "STEP-GENERATE-001", "description": ""},
        ]
        document["source_snippets"] = [
            {"id": "SNIP-BRANCH", "path": "scripts/validate_dsl.py", "line_start": 20, "line_end": 22, "language": "python", "purpose": "失败分支证据。", "content": "if errors:\n    return 1", "confidence": "observed"},
        ]

        markdown = module.render_markdown(document, evidence_mode="inline")
        flow_section = section_from(markdown, "### 8.3 生成结构设计文档")

        self.assertIn("依据：EV-FLOW（流程来源，workflow）", flow_section)
        self.assertIn("支持数据（STEP-GENERATE-001 / 准备结构化 DSL JSON。）", flow_section)
        self.assertIn("关联来源：REQ-STEP", flow_section)
        self.assertEqual([], flow["steps"][0]["traceability_refs"])
        self.assertIn("支持数据（BR-GENERATE-001 / DSL 校验失败）", flow_section)
        self.assertIn("Source: scripts/validate_dsl.py:20-22", flow_section)


def section_between(text, start_marker, end_marker):
    start = text.index(start_marker)
    end = text.index(end_marker, start)
    return text[start:end]


def section_from(text, start_marker):
    start = text.index(start_marker)
    return text[start:]


def assert_in_order(testcase, text, markers):
    positions = []
    for marker in markers:
        with testcase.subTest(marker=marker):
            positions.append(text.index(marker))
    testcase.assertEqual(sorted(positions), positions)


class ChapterOneToFourRenderingTests(unittest.TestCase):
    def test_chapters_1_to_4_have_fixed_headings_and_generated_at_fill_without_mutation(self):
        module = load_renderer_module()
        document = valid_document()
        original = deepcopy(document)

        with mock.patch.object(module, "generated_at_value", return_value="2026-05-03T12:34:56+08:00"):
            markdown = module.render_markdown(document)

        self.assertEqual(original, document)
        assert_in_order(
            self,
            markdown,
            [
                "# 软件结构设计说明书",
                "## 1. 文档信息",
                "## 2. 系统概览",
                "## 3. 架构视图",
                "### 3.1 架构概述",
                "### 3.2 各模块介绍",
                "### 3.3 模块关系图",
                "### 3.4 补充架构图表",
                "## 4. 模块设计",
                "### 4.1 技能文档生成模块",
                "#### 4.1.1 模块概述",
                "#### 4.1.2 模块职责",
                "#### 4.1.3 对外能力说明",
                "#### 4.1.4 对外接口需求清单",
                "#### 4.1.5 模块内部结构关系图",
                "#### 4.1.6 补充说明",
            ],
        )
        chapter_1 = section_between(markdown, "## 1. 文档信息", "## 2. 系统概览")
        self.assertIn("2026-05-03T12:34:56+08:00", chapter_1)
        self.assertEqual("", document["document"]["generated_at"])

    def test_chapter_2_renders_summary_purpose_core_capabilities_and_notes(self):
        module = load_renderer_module()
        document = valid_document()
        document["system_overview"]["notes"] = ["第一条概览备注", "第二条概览备注"]
        markdown = module.render_markdown(document)
        section = section_between(markdown, "## 2. 系统概览", "## 3. 架构视图")
        self.assertIn("从已准备好的结构化设计内容生成单个结构设计 Markdown 文档。", section)
        self.assertIn("提供稳定的 DSL、校验入口和渲染入口，使文档生成过程可重复。", section)
        self.assertIn("| 能力 | 描述 |", section)
        self.assertIn("结构设计文档生成", section)
        self.assertIn("把完整 DSL 内容转为固定章节的 Markdown 文档。", section)
        self.assertIn("第一条概览备注", section)
        self.assertIn("第二条概览备注", section)
        self.assertNotIn("CAP-001", section)
        self.assertNotIn("observed", section)

    def test_chapter_3_module_intro_table_uses_fixed_visible_columns_only(self):
        module = load_renderer_module()
        markdown = module.render_markdown(valid_document())
        section = section_between(markdown, "### 3.2 各模块介绍", "### 3.3 模块关系图")
        self.assertIn("| 模块名称 | 职责 | 输入 | 输出 | 备注 |", section)
        self.assertNotIn("module_id", section)
        self.assertNotIn("MOD-SKILL", section)
        self.assertNotIn("confidence", section)
        self.assertNotIn("observed", section)

    def test_chapter_4_modules_follow_chapter_3_order(self):
        module = load_renderer_module()
        document = valid_document()
        second_module = deepcopy(document["architecture_views"]["module_intro"]["rows"][0])
        second_module["module_id"] = "MOD-SECOND"
        second_module["module_name"] = "第二模块"
        second_module["responsibility"] = "第二个模块职责。"
        document["architecture_views"]["module_intro"]["rows"].append(second_module)

        second_design = deepcopy(document["module_design"]["modules"][0])
        second_design["module_id"] = "MOD-SECOND"
        second_design["name"] = "第二模块"
        second_design["summary"] = "第二模块概述。"
        second_design["internal_structure"]["diagram"]["id"] = "MER-MOD-SECOND-STRUCT"
        document["module_design"]["modules"] = [second_design, document["module_design"]["modules"][0]]

        markdown = module.render_markdown(document)
        assert_in_order(self, markdown, ["### 4.1 技能文档生成模块", "### 4.2 第二模块"])

    def test_chapter_4_module_heading_label_neutralizes_markdown_injection(self):
        module = load_renderer_module()
        document = valid_document()
        document["module_design"]["modules"][0]["name"] = "安全模块\n## 注入标题\n```html\n<div>raw</div>\n```"

        markdown = module.render_markdown(document)
        section = section_between(markdown, "## 4. 模块设计", "#### 4.1.1 模块概述")

        self.assertIn("### 4.1 安全模块", section)
        self.assertNotIn("\n## 注入标题", section)
        self.assertNotIn("```", section)
        self.assertNotIn("```html", section)
        self.assertNotIn("<div>raw</div>", section)

    def test_chapter_4_provided_capabilities_table_uses_fixed_visible_columns_only(self):
        module = load_renderer_module()
        markdown = module.render_markdown(valid_document())
        section = section_between(markdown, "#### 4.1.4 对外接口需求清单", "#### 4.1.5 模块内部结构关系图")
        self.assertIn("| 能力名称 | 接口风格 | 描述 | 输入 | 输出 | 备注 |", section)
        self.assertNotIn("capability_id", section)
        self.assertNotIn("CAP-MOD-SKILL-001", section)
        self.assertNotIn("confidence", section)

    def test_chapter_4_empty_internal_diagram_renders_textual_structure_without_mermaid_block(self):
        module = load_renderer_module()
        markdown = module.render_markdown(valid_document())
        section = section_between(markdown, "#### 4.1.5 模块内部结构关系图", "#### 4.1.6 补充说明")
        self.assertIn("schema 描述 DSL 结构", section)
        self.assertNotIn("单模块示例中使用文字结构说明即可。", section)
        self.assertNotIn("```mermaid", section)

    def test_architecture_extras_render_tables_and_diagrams_without_empty_state(self):
        module = load_renderer_module()
        document = valid_document()
        document["architecture_views"]["extra_tables"] = [
            {
                "id": "TBL-ARCH-EXTRA",
                "title": "架构补充表",
                "columns": [{"key": "item", "title": "项目"}, {"key": "note", "title": "说明"}],
                "rows": [{"item": "补充项", "note": "A|B", "evidence_refs": []}],
            }
        ]
        document["architecture_views"]["extra_diagrams"] = [
            {
                "id": "MER-ARCH-EXTRA",
                "kind": "extra",
                "title": "架构补充图",
                "diagram_type": "flowchart",
                "description": "展示补充结构。",
                "source": "flowchart TD\n  ExtraA[补充A] --> ExtraB[补充B]",
                "confidence": "observed",
            }
        ]
        markdown = module.render_markdown(document)
        section = section_between(markdown, "### 3.4 补充架构图表", "## 4. 模块设计")
        self.assertIn("#### 架构补充表", section)
        self.assertIn("| 项目 | 说明 |", section)
        self.assertIn("A\\|B", section)
        self.assertIn("#### 架构补充图", section)
        self.assertIn("```mermaid\nflowchart TD\n  ExtraA[补充A] --> ExtraB[补充B]\n```", section)
        self.assertNotIn("无补充内容。", section)


class ChapterFiveToEightRenderingTests(unittest.TestCase):
    def test_chapters_5_to_8_have_fixed_headings_even_when_optional_content_is_absent(self):
        module = load_renderer_module()
        markdown = module.render_markdown(valid_document())
        assert_in_order(
            self,
            markdown,
            [
                "## 5. 运行时视图",
                "### 5.1 运行时概述",
                "### 5.2 运行单元说明",
                "### 5.3 运行时流程图",
                "### 5.4 运行时序图（推荐）",
                "### 5.5 补充运行时图表",
                "## 6. 配置、数据与依赖关系",
                "### 6.1 配置项说明",
                "### 6.2 关键结构数据与产物",
                "### 6.3 依赖项说明",
                "### 6.4 补充图表",
                "## 7. 跨模块协作关系",
                "### 7.1 协作关系概述",
                "### 7.2 跨模块协作说明",
                "### 7.3 跨模块协作关系图",
                "### 7.4 补充协作图表",
                "## 8. 关键流程",
                "### 8.1 关键流程概述",
                "### 8.2 关键流程清单",
                "### 8.3 生成结构设计文档",
                "#### 8.3.1 流程概述",
                "#### 8.3.2 步骤说明",
                "#### 8.3.3 异常/分支说明",
                "#### 8.3.4 流程图",
            ],
        )

    def test_runtime_units_table_uses_fixed_visible_columns_only(self):
        module = load_renderer_module()
        markdown = module.render_markdown(valid_document())
        section = section_between(markdown, "### 5.2 运行单元说明", "### 5.3 运行时流程图")
        self.assertIn("| 运行单元 | 类型 | 入口 | 入口不适用原因 | 职责 | 关联模块 | 外部环境原因 | 备注 |", section)
        self.assertNotIn("unit_id", section)
        self.assertNotIn("RUN-GENERATE", section)
        self.assertNotIn("MOD-SKILL", section)
        self.assertIn("技能文档生成模块", section)
        self.assertNotIn("confidence", section)

    def test_missing_module_display_name_raises_render_error_without_leaking_raw_id(self):
        module = load_renderer_module()
        document = valid_document()
        document["runtime_view"]["runtime_units"]["rows"][0]["related_module_ids"] = ["MOD-MISSING"]

        with self.assertRaisesRegex(module.RenderError, r"missing display name for module reference"):
            module.render_markdown(document)

    def test_optional_runtime_sequence_diagram_renders_empty_state_without_mermaid_block(self):
        module = load_renderer_module()
        markdown = module.render_markdown(valid_document())
        section = section_between(markdown, "### 5.4 运行时序图（推荐）", "### 5.5 补充运行时图表")
        self.assertIn("未提供运行时序图。", section)
        self.assertNotIn("```mermaid", section)

    def test_chapter_6_empty_tables_render_fixed_empty_states(self):
        module = load_renderer_module()
        document = valid_document()
        document["configuration_data_dependencies"]["configuration_items"]["rows"] = []
        document["configuration_data_dependencies"]["structural_data_artifacts"]["rows"] = []
        document["configuration_data_dependencies"]["dependencies"]["rows"] = []
        markdown = module.render_markdown(document)
        self.assertIn("不适用。", section_between(markdown, "### 6.1 配置项说明", "### 6.2 关键结构数据与产物"))
        self.assertIn(
            "未识别到需要在结构设计阶段单独说明的关键结构数据或产物。",
            section_between(markdown, "### 6.2 关键结构数据与产物", "### 6.3 依赖项说明"),
        )
        self.assertIn(
            "未识别到需要在结构设计阶段单独说明的外部依赖项。",
            section_between(markdown, "### 6.3 依赖项说明", "### 6.4 补充图表"),
        )

    def test_chapter_6_tables_use_fixed_visible_columns_only(self):
        module = load_renderer_module()
        markdown = module.render_markdown(valid_document())
        config_section = section_between(markdown, "### 6.1 配置项说明", "### 6.2 关键结构数据与产物")
        artifact_section = section_between(markdown, "### 6.2 关键结构数据与产物", "### 6.3 依赖项说明")
        dependency_section = section_between(markdown, "### 6.3 依赖项说明", "### 6.4 补充图表")
        self.assertIn("| 配置项 | 来源 | 使用方 | 用途 | 备注 |", config_section)
        self.assertIn("| 数据/产物 | 类型 | 归属 | 生产方 | 消费方 | 备注 |", artifact_section)
        self.assertIn("| 依赖项 | 类型 | 使用方 | 用途 | 备注 |", dependency_section)
        self.assertNotIn("CFG-001", config_section)
        self.assertNotIn("DATA-001", artifact_section)
        self.assertNotIn("DEP-001", dependency_section)
        self.assertNotIn("confidence", config_section + artifact_section + dependency_section)

    def test_single_module_collaboration_renders_fixed_empty_states(self):
        module = load_renderer_module()
        document = valid_document()
        document["cross_module_collaboration"]["summary"] = ""
        document["cross_module_collaboration"]["collaboration_scenarios"]["rows"] = []
        document["cross_module_collaboration"].pop("collaboration_relationship_diagram", None)
        markdown = module.render_markdown(document)
        self.assertIn(
            "本系统当前仅识别到一个结构模块，暂无跨模块协作关系。",
            section_between(markdown, "### 7.2 跨模块协作说明", "### 7.3 跨模块协作关系图"),
        )
        self.assertIn(
            "未提供跨模块协作关系图。",
            section_between(markdown, "### 7.3 跨模块协作关系图", "### 7.4 补充协作图表"),
        )

    def test_collaboration_and_flow_index_tables_use_fixed_columns_and_display_names(self):
        module = load_renderer_module()
        markdown = module.render_markdown(valid_document())
        collaboration_section = section_between(markdown, "### 7.2 跨模块协作说明", "### 7.3 跨模块协作关系图")
        flow_index_section = section_between(markdown, "### 8.2 关键流程清单", "### 8.3 生成结构设计文档")
        self.assertIn("| 场景 | 发起模块 | 参与模块 | 协作方式 | 描述 |", collaboration_section)
        self.assertIn("| 流程 | 触发条件 | 参与模块 | 参与运行单元 | 主要步骤 | 输出结果 | 备注 |", flow_index_section)
        self.assertNotIn("COL-001", collaboration_section)
        self.assertNotIn("MOD-SKILL", collaboration_section)
        self.assertNotIn("MOD-SKILL", flow_index_section)
        self.assertNotIn("RUN-GENERATE", flow_index_section)
        self.assertIn("技能文档生成模块", collaboration_section)
        self.assertIn("技能文档生成模块", flow_index_section)
        self.assertIn("文档生成命令序列", flow_index_section)

    def test_key_flow_extras_render_between_overview_and_index_without_new_numbering(self):
        module = load_renderer_module()
        document = valid_document()
        document["key_flows"]["extra_tables"] = [
            {
                "id": "TBL-FLOW-EXTRA",
                "title": "关键流程补充表",
                "columns": [{"key": "item", "title": "项目"}, {"key": "note", "title": "说明"}],
                "rows": [{"item": "流程补充项", "note": "A|B", "evidence_refs": []}],
            }
        ]
        document["key_flows"]["extra_diagrams"] = [
            {
                "id": "MER-FLOW-EXTRA",
                "kind": "extra",
                "title": "关键流程补充图",
                "diagram_type": "flowchart",
                "description": "展示关键流程补充关系。",
                "source": "flowchart TD\n  FlowExtraA[流程补充A] --> FlowExtraB[流程补充B]",
                "confidence": "observed",
            }
        ]
        markdown = module.render_markdown(document)
        intro_to_index = section_between(markdown, "### 8.1 关键流程概述", "### 8.2 关键流程清单")
        self.assertIn("#### 关键流程补充表", intro_to_index)
        self.assertIn("| 项目 | 说明 |", intro_to_index)
        self.assertIn("A\\|B", intro_to_index)
        self.assertIn("#### 关键流程补充图", intro_to_index)
        self.assertIn("```mermaid\nflowchart TD\n  FlowExtraA[流程补充A] --> FlowExtraB[流程补充B]\n```", intro_to_index)
        self.assertNotIn("无补充内容。", intro_to_index)
        self.assertNotIn("### 8.1.1", intro_to_index)
        self.assertNotIn("### 8.2 补充", intro_to_index)

    def test_key_flow_details_follow_flow_index_order_and_steps_follow_step_order(self):
        module = load_renderer_module()
        document = valid_document()
        flow_a = deepcopy(document["key_flows"]["flows"][0])
        flow_b = deepcopy(flow_a)
        flow_a["flow_id"] = "FLOW-A"
        flow_a["name"] = "流程A"
        flow_a["diagram"]["id"] = "MER-FLOW-A"
        flow_b["flow_id"] = "FLOW-B"
        flow_b["name"] = "流程B"
        flow_b["diagram"]["id"] = "MER-FLOW-B"
        flow_b["steps"] = [
            {**deepcopy(flow_b["steps"][0]), "step_id": "STEP-B-002", "order": 2, "description": "第二步"},
            {**deepcopy(flow_b["steps"][0]), "step_id": "STEP-B-001", "order": 1, "description": "第一步"},
        ]
        document["key_flows"]["flow_index"]["rows"] = [
            {**document["key_flows"]["flow_index"]["rows"][0], "flow_id": "FLOW-B", "flow_name": "流程B"},
            {**document["key_flows"]["flow_index"]["rows"][0], "flow_id": "FLOW-A", "flow_name": "流程A"},
        ]
        document["key_flows"]["flows"] = [flow_a, flow_b]

        markdown = module.render_markdown(document)
        assert_in_order(self, markdown, ["### 8.3 流程B", "### 8.4 流程A"])
        flow_b_section = section_between(markdown, "### 8.3 流程B", "### 8.4 流程A")
        assert_in_order(self, flow_b_section, ["第一步", "第二步"])

    def test_key_flow_step_and_branch_tables_use_fixed_columns_display_names_and_empty_state(self):
        module = load_renderer_module()
        document = valid_document()
        document["key_flows"]["flows"][0]["branches_or_exceptions"] = [
            {
                "branch_id": "BR-GENERATE-RETRY",
                "condition": "校验失败",
                "handling": "停止渲染并报告问题。",
                "related_module_ids": ["MOD-SKILL"],
                "related_runtime_unit_ids": ["RUN-GENERATE"],
                "confidence": "unknown",
                "evidence_refs": [],
                "traceability_refs": [],
                "source_snippet_refs": [],
            }
        ]
        markdown = module.render_markdown(document)
        flow_section = section_from(markdown, "### 8.3 生成结构设计文档")
        steps_section = section_between(flow_section, "#### 8.3.2 步骤说明", "#### 8.3.3 异常/分支说明")
        branch_section = section_between(flow_section, "#### 8.3.3 异常/分支说明", "#### 8.3.4 流程图")

        self.assertIn("| 序号 | 执行方 | 说明 | 输入 | 输出 | 关联模块 | 关联运行单元 |", steps_section)
        self.assertIn("| 条件 | 处理方式 | 关联模块 | 关联运行单元 |", branch_section)
        self.assertNotIn("STEP-GENERATE-001", steps_section)
        self.assertNotIn("BR-GENERATE-RETRY", branch_section)
        self.assertNotIn("observed", steps_section)
        self.assertNotIn("unknown", branch_section)
        self.assertNotIn("MOD-SKILL", steps_section + branch_section)
        self.assertNotIn("RUN-GENERATE", steps_section + branch_section)
        self.assertIn("技能文档生成模块", steps_section + branch_section)
        self.assertIn("文档生成命令序列", steps_section + branch_section)

        empty_branch_document = valid_document()
        empty_branch_document["key_flows"]["flows"][0]["branches_or_exceptions"] = []
        empty_markdown = module.render_markdown(empty_branch_document)
        empty_flow_section = section_from(empty_markdown, "### 8.3 生成结构设计文档")
        empty_branch_section = section_between(empty_flow_section, "#### 8.3.3 异常/分支说明", "#### 8.3.4 流程图")
        self.assertIn("未识别到异常或分支说明。", empty_branch_section)

    def test_missing_runtime_display_name_raises_render_error_without_leaking_raw_id(self):
        module = load_renderer_module()
        document = valid_document()
        document["key_flows"]["flow_index"]["rows"][0]["participant_runtime_unit_ids"] = ["RUN-MISSING"]

        with self.assertRaisesRegex(module.RenderError, r"missing display name for runtime unit reference"):
            module.render_markdown(document)


class ChapterNineRenderingTests(unittest.TestCase):
    def test_chapter_9_empty_state_appears_only_when_all_sources_are_empty(self):
        module = load_renderer_module()
        markdown = module.render_markdown(valid_document())
        section = markdown[markdown.index("## 9. 结构问题与改进建议") :]
        self.assertIn("未识别到明确的结构问题与改进建议。", section)
        self.assertNotIn("### 风险", section)
        self.assertNotIn("### 假设", section)
        self.assertNotIn("### 低置信度项", section)

    def test_free_form_chapter_9_text_is_escaped_and_cannot_create_headings(self):
        module = load_renderer_module()
        document = valid_document()
        document["structure_issues_and_suggestions"] = "# 伪造标题\n<script>alert(1)</script>\n- 保留为普通建议"
        markdown = module.render_markdown(document)
        section = markdown[markdown.index("## 9. 结构问题与改进建议") :]
        self.assertNotIn("\n# 伪造标题", section)
        self.assertIn("\\# 伪造标题", section)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", section)
        self.assertNotIn("未识别到明确的结构问题与改进建议。", section)

    def test_risks_and_assumptions_render_under_owned_headings_without_empty_state(self):
        module = load_renderer_module()
        document = valid_document()
        document["risks"] = [
            {
                "id": "RISK-001",
                "description": "输出覆盖策略被误用。",
                "impact": "可能覆盖人工修改的文档。",
                "mitigation": "默认拒绝覆盖，显式使用 --overwrite 或 --backup。",
                "confidence": "inferred",
                "evidence_refs": [],
                "traceability_refs": [],
                "source_snippet_refs": [],
            }
        ]
        document["assumptions"] = [
            {
                "id": "ASM-001",
                "description": "调用方已先执行 DSL 校验。",
                "rationale": "Renderer 只做防御性检查。",
                "validation_suggestion": "在工作流中保留 validate_dsl.py。",
                "confidence": "unknown",
                "evidence_refs": [],
                "traceability_refs": [],
                "source_snippet_refs": [],
            }
        ]
        markdown = module.render_markdown(document)
        section = markdown[markdown.index("## 9. 结构问题与改进建议") :]
        self.assertNotIn("未识别到明确的结构问题与改进建议。", section)
        assert_in_order(self, section, ["### 风险", "输出覆盖策略被误用。", "### 假设", "调用方已先执行 DSL 校验。"])

    def test_low_confidence_items_are_collected_from_whitelisted_design_items(self):
        module = load_renderer_module()
        document = valid_document()
        document["architecture_views"]["module_intro"]["rows"][0]["confidence"] = "unknown"
        document["module_design"]["modules"][0]["external_capability_details"]["provided_capabilities"]["rows"][0]["confidence"] = "unknown"
        document["key_flows"]["flows"][0]["steps"][0]["confidence"] = "unknown"
        markdown = module.render_markdown(document)
        section = markdown[markdown.index("## 9. 结构问题与改进建议") :]
        self.assertIn("### 低置信度项", section)
        self.assertIn("$.architecture_views.module_intro.rows[0]", section)
        self.assertIn("$.module_design.modules[0].external_capability_details.provided_capabilities.rows[0]", section)
        self.assertIn("$.key_flows.flows[0].steps[0]", section)
        self.assertIn("技能文档生成模块", section)
        self.assertIn("文档 DSL 处理", section)
        self.assertIn("准备结构化 DSL JSON。", section)
        self.assertNotIn("未识别到明确的结构问题与改进建议。", section)

    def test_metadata_stays_hidden_from_normal_chapters_but_can_appear_in_chapter_9_summary(self):
        module = load_renderer_module()
        document = valid_document()
        document["architecture_views"]["module_intro"]["rows"][0]["confidence"] = "unknown"
        markdown = module.render_markdown(document)
        chapter_3_table = section_between(markdown, "### 3.2 各模块介绍", "### 3.3 模块关系图")
        chapter_9 = markdown[markdown.index("## 9. 结构问题与改进建议") :]
        self.assertNotIn("unknown", chapter_3_table)
        self.assertIn("unknown", chapter_9)

    def test_risk_and_assumption_support_refs_render_under_chapter_9_tables(self):
        module = load_renderer_module()
        document = valid_document()
        document["evidence"] = [
            {"id": "EV-RISK", "kind": "analysis", "title": "覆盖策略分析", "location": "review", "description": "", "confidence": "observed"},
            {"id": "EV-ASM", "kind": "note", "title": "工作流假设", "location": "", "description": "", "confidence": "observed"},
        ]
        document["traceability"] = [
            {"id": "TR-RISK", "source_external_id": "REQ-SAFE-WRITE", "source_type": "requirement", "target_type": "risk", "target_id": "RISK-001", "description": "覆盖风险。"},
            {"id": "TR-ASM", "source_external_id": "NOTE-VALIDATED", "source_type": "note", "target_type": "assumption", "target_id": "ASM-001", "description": ""},
        ]
        document["source_snippets"] = [
            {"id": "SNIP-RISK", "path": "scripts/render_markdown.py", "line_start": 1, "line_end": 2, "language": "python", "purpose": "风险证据。", "content": "def write_output():\n    pass", "confidence": "observed"},
        ]
        document["risks"] = [
            {"id": "RISK-001", "description": "输出覆盖策略被误用。", "impact": "可能覆盖人工修改的文档。", "mitigation": "默认拒绝覆盖。", "confidence": "inferred", "evidence_refs": ["EV-RISK"], "traceability_refs": [], "source_snippet_refs": ["SNIP-RISK"]},
        ]
        document["assumptions"] = [
            {"id": "ASM-001", "description": "调用方已先执行 DSL 校验。", "rationale": "Renderer 只做防御性检查。", "validation_suggestion": "保留 validate_dsl.py。", "confidence": "unknown", "evidence_refs": ["EV-ASM"], "traceability_refs": [], "source_snippet_refs": []},
        ]

        markdown = module.render_markdown(document, evidence_mode="inline")
        chapter_9 = markdown[markdown.index("## 9. 结构问题与改进建议") :]

        self.assertIn("### 风险", chapter_9)
        risk_section = section_between(chapter_9, "### 风险", "### 假设")
        self.assertIn("| ID | 风险 | 影响 | 缓解措施 | 置信度 |", risk_section)
        self.assertIn("| RISK-001 | 输出覆盖策略被误用。 | 可能覆盖人工修改的文档。 | 默认拒绝覆盖。 | inferred |", risk_section)
        self.assertIn("支持数据（RISK-001 / 输出覆盖策略被误用。）", chapter_9)
        self.assertIn("依据：EV-RISK（覆盖策略分析，review）", chapter_9)
        self.assertIn("关联来源：REQ-SAFE-WRITE（覆盖风险。）", chapter_9)
        self.assertEqual([], document["risks"][0]["traceability_refs"])
        self.assertIn("Source: scripts/render_markdown.py:1-2", chapter_9)
        self.assertIn("### 假设", chapter_9)
        assumption_section = section_between(chapter_9, "### 假设", "支持数据（ASM-001 / 调用方已先执行 DSL 校验。）")
        self.assertIn("| ID | 假设 | 依据 | 验证建议 | 置信度 |", assumption_section)
        self.assertIn("| ASM-001 | 调用方已先执行 DSL 校验。 | Renderer 只做防御性检查。 | 保留 validate_dsl.py。 | unknown |", assumption_section)
        self.assertIn("支持数据（ASM-001 / 调用方已先执行 DSL 校验。）", chapter_9)
        self.assertIn("依据：EV-ASM（工作流假设）", chapter_9)
        self.assertIn("关联来源：NOTE-VALIDATED", chapter_9)
        self.assertEqual([], document["assumptions"][0]["traceability_refs"])
        self.assertNotIn("未识别到明确的结构问题与改进建议。", chapter_9)

    def test_low_confidence_summary_excludes_support_data_risks_assumptions_and_diagrams(self):
        module = load_renderer_module()
        document = valid_document()
        document["architecture_views"]["module_relationship_diagram"]["confidence"] = "unknown"
        document["evidence"] = [
            {"id": "EV-UNKNOWN", "kind": "note", "title": "未知证据", "location": "", "description": "", "confidence": "unknown"},
        ]
        document["risks"] = [
            {"id": "RISK-UNKNOWN", "description": "风险置信度未知。", "impact": "", "mitigation": "", "confidence": "unknown", "evidence_refs": [], "traceability_refs": [], "source_snippet_refs": []},
        ]
        document["assumptions"] = [
            {"id": "ASM-UNKNOWN", "description": "假设置信度未知。", "rationale": "", "validation_suggestion": "", "confidence": "unknown", "evidence_refs": [], "traceability_refs": [], "source_snippet_refs": []},
        ]
        document["architecture_views"]["module_intro"]["rows"][0]["confidence"] = "unknown"

        markdown = module.render_markdown(document)
        chapter_9 = markdown[markdown.index("## 9. 结构问题与改进建议") :]

        self.assertIn("### 低置信度项", chapter_9)
        self.assertIn("$.architecture_views.module_intro.rows[0]", chapter_9)
        self.assertNotIn("$.evidence[0]", chapter_9)
        low_confidence = section_from(chapter_9, "### 低置信度项")
        self.assertNotIn("RISK-UNKNOWN", low_confidence)
        self.assertNotIn("ASM-UNKNOWN", low_confidence)
        self.assertNotIn("MER-ARCH-MODULES", chapter_9)


def collect_non_empty_mermaid_sources(document):
    sources = []

    def add_diagram(diagram):
        if isinstance(diagram, dict) and diagram.get("source", "").strip():
            sources.append(diagram["source"])

    def add_diagram_array(diagrams):
        for diagram in diagrams or []:
            add_diagram(diagram)

    architecture = document.get("architecture_views", {})
    add_diagram(architecture.get("module_relationship_diagram"))
    add_diagram_array(architecture.get("extra_diagrams"))

    module_design = document.get("module_design", {})
    for module_item in module_design.get("modules", []):
        internal_structure = module_item.get("internal_structure", {})
        add_diagram(internal_structure.get("diagram"))
        external_details = module_item.get("external_capability_details", {})
        add_diagram_array(external_details.get("extra_diagrams"))
        add_diagram_array(module_item.get("extra_diagrams"))

    runtime = document.get("runtime_view", {})
    add_diagram(runtime.get("runtime_flow_diagram"))
    add_diagram(runtime.get("runtime_sequence_diagram"))
    add_diagram_array(runtime.get("extra_diagrams"))

    configuration = document.get("configuration_data_dependencies", {})
    add_diagram_array(configuration.get("extra_diagrams"))

    collaboration = document.get("cross_module_collaboration", {})
    add_diagram(collaboration.get("collaboration_relationship_diagram"))
    add_diagram_array(collaboration.get("extra_diagrams"))

    key_flows = document.get("key_flows", {})
    for flow in key_flows.get("flows", []):
        add_diagram(flow.get("diagram"))
    add_diagram_array(key_flows.get("extra_diagrams"))
    return sources


def required_mermaid_sources(document):
    sources = [
        document["architecture_views"]["module_relationship_diagram"]["source"],
        document["runtime_view"]["runtime_flow_diagram"]["source"],
    ]
    sources.extend(flow["diagram"]["source"] for flow in document["key_flows"]["flows"])
    return sources


def load_mermaid_validator_module():
    spec = importlib.util.spec_from_file_location("validate_mermaid_for_renderer_test", VALIDATOR)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def synthetic_flowchart_source(name):
    return f"flowchart TD\n  {name}A[{name} A] --> {name}B[{name} B]"


def synthetic_diagram(diagram_id, source, diagram_type="flowchart"):
    return {
        "id": diagram_id,
        "kind": "extra",
        "title": diagram_id,
        "diagram_type": diagram_type,
        "description": f"{diagram_id} synthetic diagram.",
        "source": source,
        "confidence": "observed",
    }


class RendererIntegrationTests(unittest.TestCase):
    def render_and_validate(self, dsl_path):
        with tempfile.TemporaryDirectory() as tmpdir:
            completed = subprocess.run(
                [PYTHON, str(RENDERER), str(dsl_path), "--output-dir", tmpdir],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(0, completed.returncode, completed.stderr)
            document = json.loads(Path(dsl_path).read_text(encoding="utf-8"))
            output_path = Path(tmpdir) / document["document"]["output_file"]
            self.assertTrue(output_path.is_file())
            self.assertEqual([output_path], list(Path(tmpdir).glob("*.md")))

            markdown = output_path.read_text(encoding="utf-8")
            expected_mermaid_sources = collect_non_empty_mermaid_sources(document)
            self.assertGreater(len(expected_mermaid_sources), 0)
            self.assertEqual(len(expected_mermaid_sources), markdown.count("```mermaid"))
            for source in required_mermaid_sources(document):
                with self.subTest(required_source=source.splitlines()[0]):
                    self.assertEqual(1, markdown.count(source))

            mermaid = subprocess.run(
                [PYTHON, str(VALIDATOR), "--from-markdown", str(output_path), "--static"],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(0, mermaid.returncode, mermaid.stderr)
            self.assertIn("Mermaid validation succeeded", mermaid.stdout)
            return markdown

    def test_valid_fixture_renders_and_passes_post_render_mermaid_static_validation(self):
        markdown = self.render_and_validate(FIXTURE)
        assert_in_order(
            self,
            markdown,
            [
                "## 1. 文档信息",
                "## 2. 系统概览",
                "## 3. 架构视图",
                "## 4. 模块设计",
                "## 5. 运行时视图",
                "## 6. 配置、数据与依赖关系",
                "## 7. 跨模块协作关系",
                "## 8. 关键流程",
                "## 9. 结构问题与改进建议",
            ],
        )
        self.assertNotIn("## 10.", markdown)
        self.assertNotIn("```mermaid\n\n```", markdown)

    def test_minimal_examples_are_rejected_until_migrated_to_v2(self):
        for relative_path in [
            "examples/minimal-from-code.dsl.json",
            "examples/minimal-from-requirements.dsl.json",
        ]:
            with self.subTest(path=relative_path):
                with tempfile.TemporaryDirectory() as tmpdir:
                    completed = subprocess.run(
                        [PYTHON, str(RENDERER), str(ROOT / relative_path), "--output-dir", tmpdir],
                        cwd=ROOT,
                        text=True,
                        capture_output=True,
                        check=False,
                    )
                    self.assertEqual(2, completed.returncode)
                    self.assertIn("V1 DSL is not supported by the V2 renderer", completed.stderr)
                    self.assertEqual([], list(Path(tmpdir).glob("*.md")))

    def test_synthetic_all_known_mermaid_paths_render_inside_fences(self):
        sources = {
            "architecture module_relationship": synthetic_flowchart_source("ARCHREL"),
            "architecture extra_diagrams": synthetic_flowchart_source("ARCHEXTRA"),
            "module internal_structure.diagram": synthetic_flowchart_source("MODINTERNAL"),
            "module external_capability_details.extra_diagrams": synthetic_flowchart_source("MODEXTERNAL"),
            "module extra_diagrams": synthetic_flowchart_source("MODEXTRA"),
            "runtime_flow": synthetic_flowchart_source("RUNTIMEFLOW"),
            "runtime_sequence": "sequenceDiagram\n  participant SeqA\n  participant SeqB\n  SeqA->>SeqB: RuntimeSequence",
            "runtime extra": synthetic_flowchart_source("RUNTIMEEXTRA"),
            "configuration extra": synthetic_flowchart_source("CONFIGEXTRA"),
            "collaboration relationship": synthetic_flowchart_source("COLLABREL"),
            "collaboration extra": synthetic_flowchart_source("COLLABEXTRA"),
            "key flow diagram": synthetic_flowchart_source("KEYFLOW"),
            "key flow extra": synthetic_flowchart_source("KEYFLOWEXTRA"),
        }
        document = valid_document()
        module_item = document["module_design"]["modules"][0]
        flow = document["key_flows"]["flows"][0]

        document["architecture_views"]["module_relationship_diagram"]["source"] = sources[
            "architecture module_relationship"
        ]
        document["architecture_views"]["extra_diagrams"] = [
            synthetic_diagram("MER-SYN-ARCH-EXTRA", sources["architecture extra_diagrams"])
        ]
        module_item["internal_structure"]["diagram"]["source"] = sources["module internal_structure.diagram"]
        module_item["external_capability_details"]["extra_diagrams"] = [
            synthetic_diagram("MER-SYN-MOD-EXTERNAL", sources["module external_capability_details.extra_diagrams"])
        ]
        module_item["extra_diagrams"] = [
            synthetic_diagram("MER-SYN-MOD-EXTRA", sources["module extra_diagrams"])
        ]
        document["runtime_view"]["runtime_flow_diagram"]["source"] = sources["runtime_flow"]
        document["runtime_view"]["runtime_sequence_diagram"] = synthetic_diagram(
            "MER-SYN-RUNTIME-SEQUENCE",
            sources["runtime_sequence"],
            diagram_type="sequenceDiagram",
        )
        document["runtime_view"]["extra_diagrams"] = [
            synthetic_diagram("MER-SYN-RUNTIME-EXTRA", sources["runtime extra"])
        ]
        document["configuration_data_dependencies"]["extra_diagrams"] = [
            synthetic_diagram("MER-SYN-CONFIG-EXTRA", sources["configuration extra"])
        ]
        document["cross_module_collaboration"]["collaboration_relationship_diagram"] = synthetic_diagram(
            "MER-SYN-COLLAB-REL",
            sources["collaboration relationship"],
        )
        document["cross_module_collaboration"]["extra_diagrams"] = [
            synthetic_diagram("MER-SYN-COLLAB-EXTRA", sources["collaboration extra"])
        ]
        flow["diagram"]["source"] = sources["key flow diagram"]
        document["key_flows"]["extra_diagrams"] = [
            synthetic_diagram("MER-SYN-KEY-FLOW-EXTRA", sources["key flow extra"])
        ]

        expected_sources = list(sources.values())
        self.assertEqual(13, len(expected_sources))
        with tempfile.TemporaryDirectory() as tmpdir:
            dsl_path = write_json(tmpdir, "all-known-mermaid-paths.dsl.json", document)
            completed = subprocess.run(
                [PYTHON, str(RENDERER), str(dsl_path), "--output-dir", tmpdir],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(0, completed.returncode, completed.stderr)
            output_path = Path(tmpdir) / document["document"]["output_file"]
            markdown = output_path.read_text(encoding="utf-8")

            validator_module = load_mermaid_validator_module()
            parsed_diagrams, extraction_report = validator_module.extract_diagrams_from_markdown(markdown)
            self.assertEqual([], extraction_report.errors)
            parsed_sources = [diagram.source for diagram in parsed_diagrams]
            self.assertEqual(13, len(parsed_sources))
            self.assertCountEqual(expected_sources, parsed_sources)
            self.assertEqual(13, markdown.count("```mermaid"))

            mermaid = subprocess.run(
                [PYTHON, str(VALIDATOR), "--from-markdown", str(output_path), "--static"],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(0, mermaid.returncode, mermaid.stderr)
            self.assertIn("Mermaid validation succeeded", mermaid.stdout)

    def test_chapters_2_to_8_escape_hostile_plain_text_in_rendered_markdown(self):
        module = load_renderer_module()
        document = valid_document()
        document["system_overview"]["summary"] = "# hostile chapter 2"
        document["architecture_views"]["summary"] = "<section>hostile chapter 3</section>"
        document["module_design"]["modules"][0]["summary"] = "```python\nprint('bad')\n```"
        document["runtime_view"]["summary"] = "Injected runtime heading\n---\n| fake | table |"
        document["configuration_data_dependencies"]["configuration_items"]["rows"][0]["purpose"] = "# hostile config"
        document["cross_module_collaboration"]["collaboration_scenarios"]["rows"][0][
            "description"
        ] = "<b>hostile collaboration</b>"
        document["key_flows"]["flows"][0]["overview"] = "```bad```"

        markdown = module.render_markdown(document)
        runtime_summary = section_between(markdown, "### 5.1 运行时概述", "### 5.2 运行单元说明")

        self.assertNotIn("\n# hostile chapter 2", markdown)
        self.assertIn("\\# hostile chapter 2", markdown)
        self.assertNotIn("<section>hostile chapter 3</section>", markdown)
        self.assertIn("&lt;section&gt;hostile chapter 3&lt;/section&gt;", markdown)
        self.assertNotIn("```python", markdown)
        self.assertNotIn("```bad", markdown)
        self.assertIn("`&#96;&#96;python", markdown)
        self.assertIn("`&#96;&#96;bad", markdown)
        self.assertNotIn("\n---", runtime_summary)
        self.assertIn("\n\\---", runtime_summary)
        self.assertNotIn("\n| fake | table |", markdown)
        self.assertIn("\\| fake \\| table \\|", markdown)
        self.assertNotIn("<b>hostile collaboration</b>", markdown)
        self.assertIn("&lt;b&gt;hostile collaboration&lt;/b&gt;", markdown)
        self.assertNotIn("\n# hostile config", markdown)
        self.assertIn("\\# hostile config", markdown)

    def test_extra_table_evidence_renders_after_extra_table_using_row_display_value(self):
        module = load_renderer_module()
        document = valid_document()
        document["evidence"] = [
            {"id": "EV-EXTRA", "kind": "note", "title": "补充表证据", "location": "notes", "description": "", "confidence": "observed"},
        ]
        document["architecture_views"]["extra_tables"] = [{
            "id": "TBL-ARCH-EVIDENCE",
            "title": "架构补充依据",
            "columns": [{"key": "name", "title": "名称"}, {"key": "note", "title": "说明"}],
            "rows": [
                {"name": "补充行A", "note": "说明A", "evidence_refs": ["EV-EXTRA"]},
                {"name": "补充行B"},
            ],
        }]

        markdown = module.render_markdown(document, evidence_mode="inline")
        section = section_between(markdown, "### 3.4 补充架构图表", "## 4. 模块设计")

        self.assertIn("#### 架构补充依据", section)
        self.assertIn("| 名称 | 说明 |", section)
        self.assertIn("| 补充行B |  |", section)
        self.assertIn("支持数据（补充行A）", section)
        self.assertIn("依据：EV-EXTRA（补充表证据，notes）", section)
        self.assertNotIn("| EV-EXTRA |", section)

    def test_phase_6_support_data_render_integration_passes_mermaid_static_validation(self):
        document = valid_document()
        document["evidence"] = [
            {"id": "EV-MODULE", "kind": "source", "title": "模块证据", "location": "schema", "description": "", "confidence": "observed"},
            {"id": "EV-EXTRA", "kind": "note", "title": "补充表证据", "location": "", "description": "", "confidence": "observed"},
        ]
        document["traceability"] = [
            {"id": "TR-MODULE", "source_external_id": "REQ-MODULE", "source_type": "requirement", "target_type": "module", "target_id": "MOD-SKILL", "description": "模块追踪。"},
            {"id": "TR-STEP", "source_external_id": "REQ-STEP", "source_type": "requirement", "target_type": "flow_step", "target_id": "STEP-GENERATE-001", "description": ""},
        ]
        document["source_snippets"] = [
            {"id": "SNIP-MODULE", "path": "scripts/render_markdown.py", "line_start": 1, "line_end": 3, "language": "python", "purpose": "模块片段。", "content": "```nested```\nprint('safe fence')", "confidence": "observed"},
        ]
        document["architecture_views"]["module_intro"]["rows"][0]["evidence_refs"] = ["EV-MODULE"]
        document["module_design"]["modules"][0]["traceability_refs"] = ["TR-MODULE"]
        document["module_design"]["modules"][0]["source_snippet_refs"] = ["SNIP-MODULE"]
        document["key_flows"]["flows"][0]["steps"][0]["traceability_refs"] = []
        document["architecture_views"]["extra_tables"] = [{
            "id": "TBL-PHASE-6",
            "title": "Phase 6 补充表",
            "columns": [{"key": "name", "title": "名称"}],
            "rows": [{"name": "补充证据行", "evidence_refs": ["EV-EXTRA"]}],
        }]
        document["architecture_views"]["extra_diagrams"] = [
            synthetic_diagram("MER-PHASE-6-EXTRA", "flowchart TD\n  P6A[支持数据] --> P6B[渲染输出]")
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            dsl_path = write_json(tmpdir, "phase-6-support.dsl.json", document)
            validate = subprocess.run(
                [PYTHON, str(ROOT / "scripts/validate_dsl.py"), str(dsl_path)],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(0, validate.returncode, validate.stderr)

            render = subprocess.run(
                [PYTHON, str(RENDERER), str(dsl_path), "--output-dir", tmpdir, "--evidence-mode", "inline"],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(0, render.returncode, render.stderr)
            output_path = Path(tmpdir) / document["document"]["output_file"]
            markdown = output_path.read_text(encoding="utf-8")
            self.assertIn("依据：EV-MODULE（模块证据，schema）", markdown)
            self.assertIn("关联来源：REQ-MODULE（模块追踪。）", markdown)
            self.assertIn("支持数据（STEP-GENERATE-001 / 准备结构化 DSL JSON。）", markdown)
            self.assertIn("关联来源：REQ-STEP", markdown)
            self.assertEqual([], document["key_flows"]["flows"][0]["steps"][0]["traceability_refs"])
            self.assertIn("````python\n```nested```\nprint('safe fence')\n````", markdown)
            self.assertIn("#### Phase 6 补充表", markdown)
            self.assertIn("#### MER-PHASE-6-EXTRA", markdown)

            mermaid = subprocess.run(
                [PYTHON, str(VALIDATOR), "--from-markdown", str(output_path), "--static"],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(0, mermaid.returncode, mermaid.stderr)
            self.assertIn("Mermaid validation succeeded", mermaid.stdout)

    def test_reference_docs_describe_phase_5_renderer_contract(self):
        document_structure = (ROOT / "references/document-structure.md").read_text(encoding="utf-8")
        review_checklist = (ROOT / "references/review-checklist.md").read_text(encoding="utf-8")

        for phrase in [
            "1. 文档信息",
            "5.4 运行时序图（推荐）",
            "9. 结构问题与改进建议",
            "fixed visible table columns",
            "does not overwrite an existing output file by default",
            "`--overwrite`",
            "`--backup`",
            "validate_mermaid.py --from-markdown",
        ]:
            with self.subTest(document_structure_phrase=phrase):
                self.assertIn(phrase, document_structure)

        for phrase in [
            "generated_at",
            "`--overwrite`",
            "`--backup`",
            "validate_mermaid.py --from-markdown",
            "fixed section numbering",
            "IDs, confidence, and refs are not visible table columns",
        ]:
            with self.subTest(review_checklist_phrase=phrase):
                self.assertIn(phrase, review_checklist)


if __name__ == "__main__":
    unittest.main()
