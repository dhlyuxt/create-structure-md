# Phase 5 Markdown Renderer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement `scripts/render_markdown.py` so a validated create-structure-md DSL file renders one safe, deterministic, module- or system-specific Markdown structure design document.

**Architecture:** Replace the Phase 1 renderer stub with one standard-library Python renderer that separates CLI/input handling, safe output writing, Markdown escaping primitives, fixed table/diagram helpers, chapter renderers, and chapter 9 risk/assumption/low-confidence summaries. The renderer assumes `validate_dsl.py` already accepted the DSL, but still performs defensive JSON, output filename, Markdown fence, and overwrite checks. Rendered Markdown must pass `scripts/validate_mermaid.py --from-markdown ... --static`.

**Tech Stack:** Python 3 standard library only: `argparse`, `copy`, `dataclasses`, `datetime`, `html`, `json`, `re`, `shutil`, `sys`, `pathlib`, `typing`, `unittest`, `unittest.mock`, `subprocess`, and `tempfile`; existing `jsonschema` remains the only runtime dependency through `validate_dsl.py`.

---

## File Structure

- Modify: `scripts/render_markdown.py`
  - Owns CLI, JSON loading, defensive output filename validation, safe output writing, Markdown escaping, table rendering, Mermaid fence rendering, fixed chapter rendering, chapter 9 risk/assumption/low-confidence summaries, and process exit codes.
  - Exit codes: `0` for render success, `1` for safe-output/render validation failure after valid CLI input, `2` for CLI misuse, missing/unreadable input, invalid JSON, missing `document.output_file`, or unsafe output filename.
  - Output contract: success messages go to stdout; errors go to stderr; the script writes exactly one Markdown file under `--output-dir`.
- Modify: `tests/test_render_markdown.py`
  - Keep existing reference signpost tests.
  - Add renderer unit, helper, CLI, output-safety, chapter, and integration tests using `unittest`.
- Modify: `tests/test_validate_dsl.py`
  - Remove `scripts/render_markdown.py` from Phase 1 stub expectations once Task 1 makes the renderer real.
- Verify only unless Task 7 reference tests fail: `references/document-structure.md`
  - Should describe the fixed 9-chapter rendered structure, output filename policy, no-overwrite policy, Mermaid post-render validation, and fixed visible table columns.
- Verify only unless Task 7 reference tests fail: `references/review-checklist.md`
  - Should remind reviewers to check output path, overwrite/backup behavior, generated-at fill, fixed section numbering, and post-render Mermaid static validation.
- Verify only: `scripts/validate_mermaid.py`
  - Use the existing `--from-markdown --static` mode for post-render validation. Do not duplicate Mermaid static validation inside `render_markdown.py`.
- Verify only: `scripts/validate_dsl.py`
  - Keep schema and semantic validation there. Renderer only performs defensive checks and deterministic rendering.
- Verify only: `tests/fixtures/valid-phase2.dsl.json`
  - Must render successfully and pass rendered Markdown Mermaid static validation.
- Verify only: `examples/minimal-from-code.dsl.json`
  - Must render successfully and pass rendered Markdown Mermaid static validation.
- Verify only: `examples/minimal-from-requirements.dsl.json`
  - Must render successfully and pass rendered Markdown Mermaid static validation.

Implementation constraints from the workspace instructions:

- Do not run deletion commands such as `rm`, `rmdir`, `git clean`, `git reset --hard`, checkout-discard commands, worktree removal, or branch deletion. If cleanup is needed, give the command to the user instead of executing it.
- Do not modify code, tests, specs, examples, or references while writing this plan. During implementation, modify only the files listed by each task.
- Do not add Python dependencies.
- Use the agent Python for test commands:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest discover -s tests -v
```

---

### Task 1: CLI, JSON Loading, Filename Validation, And First Real Write

**Files:**
- Modify: `tests/test_render_markdown.py`
- Modify: `tests/test_validate_dsl.py`
- Modify: `scripts/render_markdown.py`

- [ ] **Step 1: Write failing CLI and filename tests**

Append these imports near the top of `tests/test_render_markdown.py`:

```python
import contextlib
import importlib.util
import io
import json
import subprocess
import sys
import tempfile
from copy import deepcopy
from pathlib import Path
from unittest import mock
```

Keep the existing `ROOT` constant and append these constants/helpers after it:

```python
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
```

Append this test class:

```python
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
```

In `tests/test_validate_dsl.py`, replace `SCRIPT_CASES` with an empty list because Phase 5 makes the final stub real:

```python
SCRIPT_CASES = []
```

- [ ] **Step 2: Run tests to verify RED**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_render_markdown.RendererCliAndFilenameTests tests.test_validate_dsl.ScriptStubTests -v
```

Expected RED:

```text
FAIL: test_missing_positional_dsl_file_is_cli_error
FAIL: test_missing_dsl_path_fails_without_output
FAIL: test_invalid_json_fails_without_output
FAIL: test_missing_document_output_file_fails_defensively
FAIL: test_unsafe_output_filename_fails_defensively
FAIL: test_generic_only_output_filename_fails_defensively
FAIL: test_output_filename_must_include_documented_object_token
FAIL: test_spaces_are_written_exactly_without_silent_rename
FAIL: test_output_filename_policy_matches_validate_dsl_semantics
```

`tests.test_validate_dsl.ScriptStubTests` should pass after `SCRIPT_CASES = []`.

- [ ] **Step 3: Implement the CLI, defensive filename checks, and a minimal real renderer path**

Replace the Phase 1 stub in `scripts/render_markdown.py` with these public functions and behavior:

```python
class RenderError(Exception):
    exit_code = 1


class InputError(RenderError):
    exit_code = 2


def build_parser():
    parser = argparse.ArgumentParser(description="Render create-structure-md DSL JSON to Markdown.")
    parser.add_argument("dsl_file", help="Path to structure DSL JSON.")
    parser.add_argument("--output-dir", default=".", help="Directory for the generated Markdown file.")
    output_group = parser.add_mutually_exclusive_group()
    output_group.add_argument("--overwrite", action="store_true", help="Replace an existing output file.")
    output_group.add_argument("--backup", action="store_true", help="Back up an existing output file before writing.")
    return parser
```

Implementation details:

- `load_json_file(path)` must raise `InputError("file not found: ...")` for a missing file and `InputError("invalid JSON in ...")` for invalid JSON.
- `validate_output_filename(document)` must read `document["document"]["output_file"]` and raise `InputError` when it is missing, not a string, empty, does not end with `.md`, contains `/`, contains `\`, contains `..`, contains control characters `\x00-\x1f` or `\x7f-\x9f`, or is generic-only.
- Generic-only detection should use the same defensive policy as `validate_dsl.py`: reject exact names `STRUCTURE_DESIGN.md`, `structure_design.md`, `structure-design.md`, `structuredesign.md`, `design.md`, `软件结构设计说明书.md`, and reject stems whose normalized tokens are all generic tokens such as `software`, `structure`, `design`, `document`, `doc`, `system`, `module`, `软件`, `结构`, `设计`, `说明书`.
- Module- or system-specific detection should reuse the Phase 3 idea from `validate_dsl.py`: collect non-generic tokens from `document.project_name`, `architecture_views.module_intro.rows[].module_id`, `architecture_views.module_intro.rows[].module_name`, `module_design.modules[].module_id`, and `module_design.modules[].name`; reject filenames whose normalized stem contains none of those concrete documented-object tokens.
- Keep renderer filename acceptance/rejection in parity with `validate_dsl.py` for the table-driven cases in `test_output_filename_policy_matches_validate_dsl_semantics`. Renderer errors may use renderer-specific wording, but accept/reject decisions must match the validator.
- Spaces in `document.output_file` are accepted; do not normalize or rename.
- `resolve_output_path(output_dir, output_file)` must return `Path(output_dir) / output_file`, after confirming the output directory exists and is a directory.
- `render_markdown(document)` may initially return a minimal valid string containing `# 软件结构设计说明书\n`; later tasks expand it.
- `write_output(output_path, markdown, overwrite=False, backup=False)` may initially write when the path does not exist. Task 2 fills in existing-file behavior.
- `main(argv=None)` must parse args, load the DSL, validate the filename, render, write, print `Markdown rendered: <path>` to stdout, and return `0`.
- On `InputError`, print `ERROR: <message>` to stderr and return `2`.
- On `RenderError`, print `ERROR: <message>` to stderr and return `1`.

- [ ] **Step 4: Run tests to verify GREEN**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_render_markdown.RendererCliAndFilenameTests tests.test_validate_dsl.ScriptStubTests -v
```

Expected GREEN:

```text
Ran 11 tests
OK
```

- [ ] **Step 5: Commit**

```bash
git add scripts/render_markdown.py tests/test_render_markdown.py tests/test_validate_dsl.py
git commit -m "feat: add renderer cli and filename validation"
```

---

### Task 2: Safe Output Handling With No Overwrite, Overwrite, Backup, And Backup Collision Failure

**Files:**
- Modify: `tests/test_render_markdown.py`
- Modify: `scripts/render_markdown.py`

- [ ] **Step 1: Write failing output safety tests**

Append this test class to `tests/test_render_markdown.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify RED**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_render_markdown.RendererOutputSafetyTests -v
```

Expected RED:

```text
FAIL: test_default_render_refuses_to_overwrite_existing_output
FAIL: test_overwrite_replaces_existing_output_without_creating_backup
FAIL: test_backup_preserves_existing_output_before_writing_new_output
FAIL: test_backup_fails_when_timestamped_backup_path_already_exists
```

`test_overwrite_and_backup_are_mutually_exclusive` may already pass because Task 1 uses an argparse mutually exclusive group.

- [ ] **Step 3: Implement safe output writing**

Implement these functions in `scripts/render_markdown.py`:

```python
def backup_timestamp():
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def backup_path_for(output_path):
    return output_path.with_name(f"{output_path.name}.bak-{backup_timestamp()}")
```

Update `write_output(output_path, markdown, overwrite=False, backup=False)`:

- If `output_path.exists()` and neither `overwrite` nor `backup` is true, raise `RenderError("output file already exists: ...; use --overwrite or --backup")`.
- If `overwrite` is true, write the new Markdown directly and do not create a backup.
- If `backup` is true:
  - Compute `<output_file>.bak-YYYYMMDD_HHMMSS` with `backup_timestamp()`.
  - If the backup path exists, raise `RenderError("backup path already exists: ...; retry later")`.
  - Preserve the old output with `shutil.copy2(output_path, backup_path)`.
  - Write the new Markdown to the original output path.
  - Return the backup path so `main()` can print `Backup written: <path>` before or after `Markdown rendered: <path>`.
- If the output path does not exist, write the Markdown and return no backup path.

Do not use shell deletion commands in tests or implementation. Python `TemporaryDirectory()` cleanup is acceptable because the test framework owns that temp scope.

- [ ] **Step 4: Run tests to verify GREEN**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_render_markdown.RendererOutputSafetyTests -v
```

Expected GREEN:

```text
Ran 5 tests
OK
```

- [ ] **Step 5: Commit**

```bash
git add scripts/render_markdown.py tests/test_render_markdown.py
git commit -m "feat: add safe renderer output handling"
```

---

### Task 3: Markdown Escaping, Tables, Mermaid Blocks, And Safe Source Fences

**Files:**
- Modify: `tests/test_render_markdown.py`
- Modify: `scripts/render_markdown.py`

- [ ] **Step 1: Write failing helper tests**

Append this test class to `tests/test_render_markdown.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify RED**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_render_markdown.MarkdownPrimitiveTests -v
```

Expected RED includes missing helpers such as:

```text
AttributeError: module 'render_markdown_under_test' has no attribute 'escape_table_cell'
AttributeError: module 'render_markdown_under_test' has no attribute 'render_mermaid_block'
AttributeError: module 'render_markdown_under_test' has no attribute 'render_source_snippet'
```

- [ ] **Step 3: Implement Markdown primitives**

Add these helpers to `scripts/render_markdown.py`:

- `escape_fence_markers(value)`: replace ` ``` ` with `` `&#96;&#96; `` and `~~~` with `~&#126;&#126;`.
- `escape_html(value)`: use `html.escape(value, quote=False)`.
- `escape_table_cell(value)`:
  - Convert `None` to `""`.
  - Convert lists to `、`.joined strings after string conversion.
  - Escape raw HTML with `html.escape(..., quote=False)`.
  - Replace `|` with `\|`.
  - Replace `\r\n`, `\r`, and `\n` with `<br>`.
  - Break fenced code markers with `escape_fence_markers`.
- `escape_plain_text(value)`:
  - Convert `None` to `""`.
  - Preserve ordinary prose, inline backticks, and newlines.
  - Escape raw HTML with `html.escape(..., quote=False)`.
  - Escape `|` characters on table-like lines so plain text such as `| fake | table |` cannot become a Markdown table.
  - Break fenced code markers with `escape_fence_markers`.
  - Prefix leading Markdown heading markers with a backslash for each line matching `^ {0,3}#{1,6}\s+`.
  - Neutralize Setext heading and thematic-break underline lines by escaping plain-text lines matching `^ {0,3}(=+|-+)\s*$`, for example by prefixing `\` so `Injected heading\n---` and `Injected heading\n===` cannot become headings or horizontal rules. Ordinary prose lines must remain unchanged.
- `render_fixed_table(rows, columns)`:
  - `columns` is a list of `(field_key, visible_title)` tuples.
  - Render the visible header row and separator row.
  - Render one row per input row using only the declared field keys.
  - Do not expose IDs, confidence, `evidence_refs`, `traceability_refs`, or `source_snippet_refs` unless a caller deliberately passes them in `columns`.
  - If `rows` is empty, callers handle empty-state text before calling this function.
- `render_extra_table(table)`:
  - Render `#### <escaped title>`.
  - Use `columns[].title` as headers and `columns[].key` for row values.
  - Hide `id`, `evidence_refs`, and any metadata fields.
- `render_mermaid_block(diagram, empty_text=None)`:
  - If `diagram` is missing or `source` is empty, return `empty_text` when provided.
  - If `source` contains ` ``` ` or `~~~`, raise `RenderError`.
  - Render optional `diagram["title"]` and `diagram["description"]` as escaped plain text before the fence when non-empty.
  - Render exactly:

```markdown
```mermaid
<raw source>
```
```

- `longest_backtick_run(content)` and `render_source_snippet(snippet)`:
  - Choose a backtick fence length longer than any backtick run in the source snippet content, with at least three backticks.
  - Render the snippet path/line/purpose as plain text, then a fenced code block with the safe fence length.
  - This helper is a safe primitive only in Phase 5. Do not insert evidence, traceability, or source snippets into normal chapters in this phase; broad support-data rendering is Phase 6.

- [ ] **Step 4: Run tests to verify GREEN**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_render_markdown.MarkdownPrimitiveTests -v
```

Expected GREEN:

```text
Ran 8 tests
OK
```

- [ ] **Step 5: Commit**

```bash
git add scripts/render_markdown.py tests/test_render_markdown.py
git commit -m "feat: add markdown rendering primitives"
```

---

### Task 4: Render Chapters 1-4 With Fixed Numbering, Generated-At Fill, Fixed Tables, And Module Ordering

**Files:**
- Modify: `tests/test_render_markdown.py`
- Modify: `scripts/render_markdown.py`

- [ ] **Step 1: Write failing tests for chapters 1-4**

Append these helper functions to `tests/test_render_markdown.py`:

```python
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
```

Append this test class:

```python
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
        document["module_design"]["modules"] = [second_design, document["module_design"]["modules"][0]]

        markdown = module.render_markdown(document)
        assert_in_order(self, markdown, ["### 4.1 技能文档生成模块", "### 4.2 第二模块"])

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
        self.assertIn("单模块示例中使用文字结构说明即可。", section)
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
```

- [ ] **Step 2: Run tests to verify RED**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_render_markdown.ChapterOneToFourRenderingTests -v
```

Expected RED:

```text
FAIL: test_chapters_1_to_4_have_fixed_headings_and_generated_at_fill_without_mutation
FAIL: test_chapter_2_renders_summary_purpose_core_capabilities_and_notes
FAIL: test_chapter_3_module_intro_table_uses_fixed_visible_columns_only
FAIL: test_chapter_4_modules_follow_chapter_3_order
FAIL: test_chapter_4_provided_capabilities_table_uses_fixed_visible_columns_only
FAIL: test_chapter_4_empty_internal_diagram_renders_textual_structure_without_mermaid_block
FAIL: test_architecture_extras_render_tables_and_diagrams_without_empty_state
```

- [ ] **Step 3: Implement chapters 1-4**

Implementation details:

- Define heading helpers:
  - Chapter heading: `## N. 标题`
  - Subchapter heading: `### N.x 标题`
  - Nested subsection heading: `#### N.x.y 标题`
- Define `generated_at_value()` as `datetime.now().astimezone().isoformat(timespec="seconds")`.
- Chapter 1:
  - Render `document` as a compact two-column metadata table with visible headers `字段` and `值`.
  - If `document.generated_at` is empty, render `generated_at_value()` without mutating the input object.
- Chapter 2:
  - Render `system_overview.summary` and `system_overview.purpose` as escaped plain text.
  - Render `system_overview.core_capabilities` as a fixed visible table with headers `能力` and `描述`, using row fields `name` and `description`.
  - Hide `capability_id` and `confidence` from the visible table.
  - Render `system_overview.notes` as a bullet list when present.
- Chapter 3:
  - `3.1 架构概述`: `architecture_views.summary`.
  - `3.2 各模块介绍`: fixed visible columns:

```python
MODULE_INTRO_COLUMNS = [
    ("module_name", "模块名称"),
    ("responsibility", "职责"),
    ("inputs", "输入"),
    ("outputs", "输出"),
    ("notes", "备注"),
]
```

  - `3.3 模块关系图`: `render_mermaid_block(architecture_views["module_relationship_diagram"])`.
  - `3.4 补充架构图表`: render extra tables and extra diagrams; when both arrays are empty, render `无补充内容。`.
  - Implement one shared helper such as `render_extras(extra_tables, extra_diagrams, empty_text="无补充内容。")` and use it for every extras location in chapters 3, 4, 5, 6, 7, and 8. The architecture extras test is the representative wiring test; the helper must not be chapter-specific.
- Chapter 4:
  - Render `module_design.summary` immediately below `## 4. 模块设计`.
  - Build chapter 3 module order from `architecture_views.module_intro.rows[].module_id`.
  - Render one module subsection per module ID in that order.
  - `4.x.1 模块概述`: module summary.
  - `4.x.2 模块职责`: bullet list of `responsibilities`.
  - `4.x.3 对外能力说明`: `external_capability_summary.description`, consumers, interface style, and boundary notes.
  - `4.x.4 对外接口需求清单`: fixed visible columns:

```python
PROVIDED_CAPABILITY_COLUMNS = [
    ("capability_name", "能力名称"),
    ("interface_style", "接口风格"),
    ("description", "描述"),
    ("inputs", "输入"),
    ("outputs", "输出"),
    ("notes", "备注"),
]
```

  - `4.x.5 模块内部结构关系图`: render Mermaid diagram when source is non-empty; otherwise render `internal_structure.textual_structure` and `internal_structure.not_applicable_reason` when present, with no empty Mermaid fence.
  - `4.x.6 补充说明`: render `external_capability_details.extra_tables`, `external_capability_details.extra_diagrams`, module-level `extra_tables`, module-level `extra_diagrams`, and notes; if all are empty, render `无补充内容。`.

- [ ] **Step 4: Run tests to verify GREEN**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_render_markdown.ChapterOneToFourRenderingTests -v
```

Expected GREEN:

```text
Ran 7 tests
OK
```

- [ ] **Step 5: Commit**

```bash
git add scripts/render_markdown.py tests/test_render_markdown.py
git commit -m "feat: render markdown chapters one through four"
```

---

### Task 5: Render Chapters 5-8 With Optional Empty States, Fixed Tables, And Flow Ordering

**Files:**
- Modify: `tests/test_render_markdown.py`
- Modify: `scripts/render_markdown.py`

- [ ] **Step 1: Write failing tests for chapters 5-8**

Append this test class to `tests/test_render_markdown.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify RED**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_render_markdown.ChapterFiveToEightRenderingTests -v
```

Expected RED:

```text
FAIL: test_chapters_5_to_8_have_fixed_headings_even_when_optional_content_is_absent
FAIL: test_runtime_units_table_uses_fixed_visible_columns_only
FAIL: test_optional_runtime_sequence_diagram_renders_empty_state_without_mermaid_block
FAIL: test_chapter_6_empty_tables_render_fixed_empty_states
FAIL: test_chapter_6_tables_use_fixed_visible_columns_only
FAIL: test_single_module_collaboration_renders_fixed_empty_states
FAIL: test_collaboration_and_flow_index_tables_use_fixed_columns_and_display_names
FAIL: test_key_flow_extras_render_between_overview_and_index_without_new_numbering
FAIL: test_key_flow_details_follow_flow_index_order_and_steps_follow_step_order
FAIL: test_key_flow_step_and_branch_tables_use_fixed_columns_display_names_and_empty_state
```

- [ ] **Step 3: Implement chapters 5-8**

Implementation details:

- Build display lookup maps before rendering chapters:
  - Module display names: `architecture_views.module_intro.rows[].module_id` to `module_name`.
  - Runtime unit display names: `runtime_view.runtime_units.rows[].unit_id` to `unit_name`.
  - Use these maps for visible module/runtime reference columns. Raw reference IDs such as `MOD-SKILL` and `RUN-GENERATE` must not appear in normal tables unless they are part of prose supplied by the DSL.
- Chapter 5:
  - `5.1 运行时概述`: `runtime_view.summary`.
  - `5.2 运行单元说明`: fixed visible columns:

```python
RUNTIME_UNIT_COLUMNS = [
    ("unit_name", "运行单元"),
    ("unit_type", "类型"),
    ("entrypoint", "入口"),
    ("entrypoint_not_applicable_reason", "入口不适用原因"),
    ("responsibility", "职责"),
    ("related_module_ids", "关联模块"),
    ("external_environment_reason", "外部环境原因"),
    ("notes", "备注"),
]
```

  - Render `related_module_ids` through the module display-name map.
  - `5.3 运行时流程图`: required Mermaid block from `runtime_flow_diagram`.
  - `5.4 运行时序图（推荐）`: optional `runtime_sequence_diagram`; if missing or empty, render `未提供运行时序图。`.
  - `5.5 补充运行时图表`: extras or `无补充内容。`.
- Chapter 6:
  - Render `configuration_data_dependencies.summary` below the chapter heading only when non-empty.
  - `6.1 配置项说明`: fixed columns `配置项, 来源, 使用方, 用途, 备注`; empty rows render `不适用。`.
  - `6.2 关键结构数据与产物`: fixed columns `数据/产物, 类型, 归属, 生产方, 消费方, 备注`; empty rows render `未识别到需要在结构设计阶段单独说明的关键结构数据或产物。`.
  - `6.3 依赖项说明`: fixed columns `依赖项, 类型, 使用方, 用途, 备注`; empty rows render `未识别到需要在结构设计阶段单独说明的外部依赖项。`.
  - `6.4 补充图表`: extras or `无补充内容。`.
- Chapter 7:
  - Always render `7.1` through `7.4`.
  - `7.1 协作关系概述`: render summary when non-empty; when empty, leave the section body empty rather than inventing prose.
  - `7.2 跨模块协作说明`: collaboration table with fixed columns `场景, 发起模块, 参与模块, 协作方式, 描述`; if rows are empty, render `本系统当前仅识别到一个结构模块，暂无跨模块协作关系。`.
  - Render `initiator_module_id` and `participant_module_ids` through the module display-name map.
  - `7.3 跨模块协作关系图`: render Mermaid when source exists; otherwise render `未提供跨模块协作关系图。`.
  - `7.4 补充协作图表`: extras or `无补充内容。`.
- Chapter 8:
  - `8.1 关键流程概述`: `key_flows.summary`.
  - Render `key_flows.extra_tables` and `key_flows.extra_diagrams` immediately after `8.1 关键流程概述` and before `8.2 关键流程清单`, without adding a new numbered subsection. The Phase 5 full outline has no Chapter 8 supplement subsection, so when these arrays are empty render nothing here rather than `无补充内容。`.
  - `8.2 关键流程清单`: fixed visible columns:

```python
FLOW_INDEX_COLUMNS = [
    ("flow_name", "流程"),
    ("trigger_condition", "触发条件"),
    ("participant_module_ids", "参与模块"),
    ("participant_runtime_unit_ids", "参与运行单元"),
    ("main_steps", "主要步骤"),
    ("output_result", "输出结果"),
    ("notes", "备注"),
]
```

  - Render participant module IDs through the module display-name map and participant runtime unit IDs through the runtime unit display-name map.
  - Detail subsections follow `key_flows.flow_index.rows[]` order. Look up detail objects by `flow_id`.
  - `8.x.1 流程概述`: render `overview`, related modules, and related runtime units.
  - `8.x.2 步骤说明`: render a fixed table ordered by `steps[].order`, with visible columns `序号, 执行方, 说明, 输入, 输出, 关联模块, 关联运行单元`; render related module/runtime references through display-name maps.
  - `8.x.3 异常/分支说明`: render fixed table columns `条件, 处理方式, 关联模块, 关联运行单元`; render related module/runtime references through display-name maps; empty rows render `未识别到异常或分支说明。`.
  - `8.x.4 流程图`: required Mermaid block from `flow.diagram`.

- [ ] **Step 4: Run tests to verify GREEN**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_render_markdown.ChapterFiveToEightRenderingTests -v
```

Expected GREEN:

```text
Ran 10 tests
OK
```

- [ ] **Step 5: Commit**

```bash
git add scripts/render_markdown.py tests/test_render_markdown.py
git commit -m "feat: render markdown chapters five through eight"
```

---

### Task 6: Chapter 9 Free-Form Text, Risks, Assumptions, Low-Confidence Items, And Safe Owned Headings

**Files:**
- Modify: `tests/test_render_markdown.py`
- Modify: `scripts/render_markdown.py`

- [ ] **Step 1: Write failing chapter 9 tests**

Append this test class to `tests/test_render_markdown.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify RED**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_render_markdown.ChapterNineRenderingTests -v
```

Expected RED:

```text
FAIL: test_chapter_9_empty_state_appears_only_when_all_sources_are_empty
FAIL: test_free_form_chapter_9_text_is_escaped_and_cannot_create_headings
FAIL: test_risks_and_assumptions_render_under_owned_headings_without_empty_state
FAIL: test_low_confidence_items_are_collected_from_whitelisted_design_items
FAIL: test_metadata_stays_hidden_from_normal_chapters_but_can_appear_in_chapter_9_summary
```

- [ ] **Step 3: Implement chapter 9 and low-confidence collection**

Implementation details:

- Chapter heading: `## 9. 结构问题与改进建议`.
- Render `structure_issues_and_suggestions` first when non-empty through `escape_plain_text()`. Do not allow it to create headings.
- Render `### 风险` when `risks` is non-empty. Use a fixed table with visible columns `风险, 影响, 缓解措施, 置信度`.
- Render `### 假设` when `assumptions` is non-empty. Use a fixed table with visible columns `假设, 依据, 验证建议, 置信度`.
- Collect unknown-confidence items from the same whitelist used by `validate_dsl.py`:
  - `architecture_views.module_intro.rows`
  - `module_design.modules`
  - `module_design.modules[].external_capability_details.provided_capabilities.rows`
  - `runtime_view.runtime_units.rows`
  - `configuration_data_dependencies.configuration_items.rows`
  - `configuration_data_dependencies.structural_data_artifacts.rows`
  - `configuration_data_dependencies.dependencies.rows`
  - `cross_module_collaboration.collaboration_scenarios.rows`
  - `key_flows.flows`
  - `key_flows.flows[].steps`
  - `key_flows.flows[].branches_or_exceptions`
- Render `### 低置信度项` when collected items are non-empty. Include a stable JSON path, a short item label, and the confidence value. This chapter 9 summary may show IDs/metadata while normal chapter tables keep them hidden.
- Render `未识别到明确的结构问题与改进建议。` only when free-form text, risks, assumptions, and low-confidence items are all empty.
- Phase 5 only renders chapter 9 risks, assumptions, and low-confidence summaries. Evidence, traceability, and source snippets must not be inserted into normal chapters in Phase 5. Keep `render_source_snippet()` from Task 3 as a safe primitive/no-op hook for future Phase 6 support-data rendering.

- [ ] **Step 4: Run tests to verify GREEN**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_render_markdown.ChapterNineRenderingTests -v
```

Expected GREEN:

```text
Ran 5 tests
OK
```

- [ ] **Step 5: Commit**

```bash
git add scripts/render_markdown.py tests/test_render_markdown.py
git commit -m "feat: render markdown chapter nine support sections"
```

---

### Task 7: End-To-End Rendering, Post-Render Mermaid Validation, Examples, And Reference Checklist Refresh

**Files:**
- Modify: `tests/test_render_markdown.py`
- Modify if reference tests fail: `references/document-structure.md`
- Modify if reference tests fail: `references/review-checklist.md`
- Modify if integration tests fail: `scripts/render_markdown.py`
- Verify only: `scripts/validate_mermaid.py`
- Verify only: `examples/minimal-from-code.dsl.json`
- Verify only: `examples/minimal-from-requirements.dsl.json`
- Verify only: `tests/fixtures/valid-phase2.dsl.json`

- [ ] **Step 1: Write failing or partially failing integration/reference tests**

Append these helpers and this test class to `tests/test_render_markdown.py`:

```python
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

    def test_minimal_examples_render_and_pass_post_render_mermaid_static_validation(self):
        for relative_path in [
            "examples/minimal-from-code.dsl.json",
            "examples/minimal-from-requirements.dsl.json",
        ]:
            with self.subTest(path=relative_path):
                markdown = self.render_and_validate(ROOT / relative_path)
                self.assertIn("## 9. 结构问题与改进建议", markdown)

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

        document["architecture_views"]["module_relationship_diagram"]["source"] = sources["architecture module_relationship"]
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
        document["cross_module_collaboration"]["collaboration_scenarios"]["rows"][0]["description"] = "<b>hostile collaboration</b>"
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
```

- [ ] **Step 2: Run integration tests to verify RED or doc-only RED**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_render_markdown.RendererIntegrationTests -v
```

Expected result before final integration fixes:

```text
FAIL: test_valid_fixture_renders_and_passes_post_render_mermaid_static_validation
FAIL: test_minimal_examples_render_and_pass_post_render_mermaid_static_validation
FAIL: test_synthetic_all_known_mermaid_paths_render_inside_fences
FAIL: test_chapters_2_to_8_escape_hostile_plain_text_in_rendered_markdown
FAIL: test_reference_docs_describe_phase_5_renderer_contract
```

If renderer integration already passes from prior tasks, the reference docs test may still fail because the current references are shorter than the Phase 5 renderer contract.

- [ ] **Step 3: Finish renderer integration and refresh references only where the test proves staleness**

Renderer integration details:

- Ensure `render_markdown(document)` renders all nine chapters in fixed order for every valid fixture and example.
- Ensure the rendered Markdown contains exactly one ` ```mermaid ` opening fence for every non-empty Mermaid source extracted by the integration test helper. This protects against false success when `validate_mermaid.py --from-markdown --static` sees zero blocks.
- Ensure the synthetic all-known-paths test renders all 13 DSL Mermaid path categories inside Mermaid fences by comparing the expected source multiset against `validate_mermaid.py` module `extract_diagrams_from_markdown()` parsed block bodies: architecture module relationship, architecture extras, module internal structure, module external capability extras, module extras, runtime flow, runtime sequence, runtime extras, configuration extras, collaboration relationship, collaboration extras, key flow diagrams, and key flow extras.
- Ensure required diagram sources from `architecture_views.module_relationship_diagram`, `runtime_view.runtime_flow_diagram`, and every `key_flows.flows[].diagram` appear exactly once in the rendered output before running the Markdown Mermaid validator.
- Ensure every required Mermaid source is fenced exactly once with ` ```mermaid ` and a closing ` ``` `.
- Ensure empty optional diagrams render text only and no Mermaid block.
- Ensure all normal text flows through `escape_plain_text()` and all table cells through `escape_table_cell()`.
- Ensure hostile plain text in chapters 2-8 cannot create extra ATX headings, Setext headings, thematic breaks, raw HTML blocks, fenced code blocks, or table rows.
- Ensure no generated Markdown contains empty Mermaid fences.
- Ensure CLI writes exactly one Markdown file in the requested output directory.

Reference doc updates when the reference test is RED:

- In `references/document-structure.md`, add the fixed Chinese outline with subchapter numbers from the Phase 5 spec, the safe output policy, backup naming format `<output_file>.bak-YYYYMMDD_HHMMSS`, post-render `validate_mermaid.py --from-markdown <output-file> --static`, fixed visible table columns, and the rule that IDs/confidence/refs are hidden except for chapter 9 risks, assumptions, and low-confidence summaries.
- In `references/review-checklist.md`, add review bullets for:
  - `document.output_file` is the exact generated filename.
  - Existing output default refusal, `--overwrite`, and `--backup`.
  - `generated_at` is filled in rendered output without mutating the DSL.
  - Fixed section numbering does not shift when optional content is absent.
  - Rendered Mermaid passes `validate_mermaid.py --from-markdown <output-file> --static`.
  - IDs, confidence, and refs are not visible table columns except in chapter 9 risks, assumptions, and low-confidence summaries.

- [ ] **Step 4: Run targeted integration tests to verify GREEN**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_render_markdown.RendererIntegrationTests -v
```

Expected GREEN:

```text
Ran 5 tests
OK
```

- [ ] **Step 5: Run the full test suite**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest discover -s tests -v
```

Expected GREEN:

```text
OK
```

- [ ] **Step 6: Manually run the documented render workflow on the fixture**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python scripts/validate_dsl.py tests/fixtures/valid-phase2.dsl.json
```

Expected:

```text
Validation succeeded
```

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python scripts/validate_mermaid.py --from-dsl tests/fixtures/valid-phase2.dsl.json --static
```

Expected:

```text
Mermaid validation succeeded
```

Create a fresh temporary output directory and render into it:

```bash
OUTPUT_DIR=$(/home/hyx/miniconda3/envs/agent/bin/python -c "import tempfile; print(tempfile.mkdtemp(prefix='create-structure-md-phase5-render-check-'))")
```

Expected: stdout prints nothing and the shell variable `OUTPUT_DIR` contains a new directory path under `/tmp`.

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python scripts/render_markdown.py tests/fixtures/valid-phase2.dsl.json --output-dir "$OUTPUT_DIR"
```

Expected:

```text
Markdown rendered: <OUTPUT_DIR>/create-structure-md_STRUCTURE_DESIGN.md
```

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python scripts/validate_mermaid.py --from-markdown "$OUTPUT_DIR/create-structure-md_STRUCTURE_DESIGN.md" --static
```

Expected:

```text
Mermaid validation succeeded
```

Do not delete the temporary output directory with a shell command. If cleanup is desired, report the cleanup command for the user to run.

- [ ] **Step 7: Commit**

```bash
git add scripts/render_markdown.py tests/test_render_markdown.py references/document-structure.md references/review-checklist.md
git commit -m "feat: complete renderer integration coverage"
```

If the renderer already passes and the final changes are only tests/docs, use this narrower commit command and message:

```bash
git add tests/test_render_markdown.py references/document-structure.md references/review-checklist.md
git commit -m "test: pin renderer integration coverage"
```

---

## Spec Coverage Map

- CLI contract and defensive input/output filename validation: Task 1.
- Output filename parity with `validate_dsl.py`, including generic-only names, all-generic stems, unrelated concrete tokens, spaces, path separators, `..`, control characters, and casefold concrete names: Task 1.
- Default no-overwrite, `--overwrite`, `--backup`, `%Y%m%d_%H%M%S`, and backup collision failure: Task 2.
- Markdown escaping for table cells, plain text, fences, raw HTML, pipes, newlines, Setext headings/thematic breaks, and renderer wiring across hostile chapter 2-8 fields: Tasks 3 and 7.
- Mermaid block rendering, optional empty diagram text, rendered Mermaid block count, required source presence, 13 known DSL Mermaid path categories parsed from fenced block bodies, and post-render static validation: Tasks 3 and 7.
- Fixed 9-chapter structure and stable numbering across absent optional content: Tasks 4, 5, and 7.
- Fixed visible table columns and hidden metadata except chapter 9 risk/assumption/low-confidence summaries: Tasks 3, 4, 5, and 6.
- Chapter 1 `generated_at` fill without DSL mutation: Task 4.
- Chapter 2-8 rendering rules, extras wiring including key flow extras placed between `8.1` and `8.2` without new numbering, module ordering by chapter 3 order, key flow ordering by flow index, and step/branch table behavior: Tasks 4 and 5.
- Chapter 9 free-form issues, risks, assumptions, low-confidence items, empty-state behavior, and safe owned headings: Task 6.
- Integration tests on valid fixture and minimal examples with rendered Markdown Mermaid validation: Task 7.
- Reference checklist/document structure refresh only when tests show visible staleness: Task 7.

## Intentional Out Of Scope

- Strict Mermaid CLI validation remains Phase 4 behavior and workflow policy; Phase 5 only requires post-render static validation.
- Advanced evidence, traceability, and source-snippet placement is completed in Phase 6. Phase 5 provides a safe source-snippet primitive only and renders chapter 9 risks, assumptions, and low-confidence summaries.
- The renderer does not replace `validate_dsl.py` semantic validation. It performs defensive checks needed to avoid unsafe output and malformed Markdown.
