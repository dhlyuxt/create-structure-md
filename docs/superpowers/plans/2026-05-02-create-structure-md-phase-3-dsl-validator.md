# Phase 3 DSL Validator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement `scripts/validate_dsl.py` semantic validation so schema-valid create-structure-md DSL files are checked for document readiness before rendering.

**Architecture:** Keep Phase 3 in one small internal library inside `scripts/validate_dsl.py`: parsing and JSON Schema validation run first, then a pure semantic validator returns collected errors, warnings, and low-confidence items. Unit tests import pure functions for focused behavior and use subprocess tests for the public CLI contract. Semantic validation accumulates all semantic errors after schema success, while invalid JSON or schema failures stop immediately.

**Tech Stack:** Python 3, standard-library `argparse`, `dataclasses`, `json`, `re`, `pathlib`, `unittest`, and existing `jsonschema`; no new runtime or test dependencies.

---

## File Structure

- Modify: `scripts/validate_dsl.py`
  - Replace the Phase 1 stub with a complete CLI plus pure semantic validation helpers.
  - Owns `ValidationIssue`, `ValidationReport`, schema loading, JSON loading, schema-first validation, semantic context/indexing, chapter rules, reference checks, source snippet checks, Markdown safety checks, low-confidence collection, and output formatting.
- Create: `tests/test_validate_dsl_semantics.py`
  - Focused Phase 3 unit tests for semantic rules. This avoids making existing Phase 1/2 schema tests unwieldy while still keeping all validator tests under `tests/`.
- Modify: `tests/test_validate_dsl.py`
  - Update the old Phase 1 script-stub assertions so they expect the real CLI behavior, and keep Phase 2 schema tests intact.
- Verify only: `schemas/structure-design.schema.json`
  - Phase 3 uses this schema as-is. Do not move reference validation into schema.
- Verify only: `tests/fixtures/valid-phase2.dsl.json`
  - Used as the semantic test base fixture.
- Verify only: `examples/minimal-from-code.dsl.json`
  - Must pass semantic CLI validation.
- Verify only: `examples/minimal-from-requirements.dsl.json`
  - Must pass semantic CLI validation.
- Verify only: `requirements.txt`
  - Must remain runtime-only with `jsonschema`; do not add dependencies.

Implementation constraint from the workspace instructions: do not run deletion commands such as `rm`, `rmdir`, `git clean`, `git reset --hard`, or checkout commands that discard files. If cleanup is needed, provide the command for the user to run.

Use the agent Python for every test command:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest discover -s tests -v
```

---

### Task 1: CLI Contract And Schema-First Stop Policy

**Files:**
- Create: `tests/test_validate_dsl_semantics.py`
- Modify: `tests/test_validate_dsl.py`
- Modify: `scripts/validate_dsl.py`

- [ ] **Step 1: Write failing CLI and schema-first tests**

Create `tests/test_validate_dsl_semantics.py` with the shared helpers and first tests:

```python
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

```

In `tests/test_validate_dsl.py`, replace `SCRIPT_CASES` with separate cases for the still-stubbed scripts:

```python
SCRIPT_CASES = [
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
```

Add this test class to `tests/test_validate_dsl.py`:

```python
class ValidateDslCliTests(unittest.TestCase):
    def test_validate_dsl_cli_accepts_valid_fixture(self):
        completed = subprocess.run(
            [sys.executable, str(ROOT / "scripts/validate_dsl.py"), str(ROOT / "tests/fixtures/valid-phase2.dsl.json")],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertIn("Validation succeeded", completed.stdout)
        self.assertEqual("", completed.stderr)
```

- [ ] **Step 2: Run CLI tests to verify RED**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_validate_dsl_semantics.CliAndSchemaFirstTests tests.test_validate_dsl.ValidateDslCliTests -v
```

Expected RED output:

```text
FAIL: test_invalid_json_exits_two_before_semantic_validation
AssertionError: 'invalid JSON' not found
FAIL: test_missing_file_exits_two_and_uses_stderr
AssertionError: 'file not found' not found
FAIL: test_schema_failure_exits_two_before_semantic_validation
AssertionError: '$.document.status' not found
FAIL: test_valid_fixture_exits_zero_and_prints_success_to_stdout
AssertionError: 0 != 2
FAIL: test_validate_dsl_cli_accepts_valid_fixture
AssertionError: 0 != 2
```

- [ ] **Step 3: Replace the stub with CLI and validation scaffolding**

Replace `scripts/validate_dsl.py` with definitions matching these names and responsibilities:

```python
#!/usr/bin/env python3
import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas/structure-design.schema.json"


@dataclass(frozen=True)
class ValidationIssue:
    level: str
    path: str
    message: str
    hint: str = ""

    def format(self):
        suffix = f" Hint: {self.hint}" if self.hint else ""
        return f"{self.level}: {self.path}: {self.message}.{suffix}"


@dataclass
class ValidationReport:
    errors: list[ValidationIssue] = field(default_factory=list)
    warnings: list[ValidationIssue] = field(default_factory=list)

    def error(self, path, message, hint=""):
        self.errors.append(ValidationIssue("ERROR", path, message, hint))

    def warn(self, path, message, hint=""):
        self.warnings.append(ValidationIssue("WARNING", path, message, hint))


def build_parser():
    parser = argparse.ArgumentParser(description="Validate create-structure-md DSL JSON.")
    parser.add_argument("dsl_file", help="Path to structure DSL JSON.")
    parser.add_argument(
        "--allow-long-snippets",
        action="store_true",
        help="Warn instead of fail for source snippets longer than 50 lines.",
    )
    return parser


def json_path(parts):
    path = "$"
    for part in parts:
        if isinstance(part, int):
            path += f"[{part}]"
        else:
            path += f".{part}"
    return path


def load_json_file(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ValueError(f"file not found: {path}")
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}")


def load_schema():
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def schema_errors(document):
    validator = Draft202012Validator(load_schema())
    return sorted(validator.iter_errors(document), key=lambda error: list(error.path))


def format_schema_error(error):
    return ValidationIssue(
        "ERROR",
        json_path(error.path),
        f"schema validation failed: {error.message}",
        "Fix the DSL shape before semantic validation runs",
    )


def validate_semantics(document, *, allow_long_snippets=False):
    report = ValidationReport()
    validate_document_fields(document, report)
    context = ValidationContext(document, report)
    context.build()
    run_semantic_checks(document, context, allow_long_snippets=allow_long_snippets)
    return report


def run_semantic_checks(document, context, *, allow_long_snippets):
    check_chapter_rules(document, context)
    check_source_snippets(document, context, allow_long_snippets=allow_long_snippets)
    check_markdown_safety(document, context)
    collect_low_confidence(document, context)


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    path = Path(args.dsl_file)

    try:
        document = load_json_file(path)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    schema_failure = schema_errors(document)
    if schema_failure:
        print(format_schema_error(schema_failure[0]).format(), file=sys.stderr)
        return 2

    report = validate_semantics(document, allow_long_snippets=args.allow_long_snippets)
    if report.errors:
        for issue in report.errors:
            print(issue.format(), file=sys.stderr)
        for issue in report.warnings:
            print(issue.format(), file=sys.stderr)
        return 1

    for issue in report.warnings:
        print(issue.format())
    print("Validation succeeded")
    return 0


```

In this task, also add no-op definitions so the script imports and the valid fixture can pass while subsequent tasks add rules. In the replacement file, paste this block immediately after `format_schema_error()` and before `validate_semantics()`. Do not paste it after `main()`. The final `if __name__ == "__main__": raise SystemExit(main())` guard must remain at the bottom of the file after every function and class definition.

```python
class ValidationContext:
    def __init__(self, document, report):
        self.document = document
        self.report = report

    def build(self):
        pass


def validate_document_fields(document, report):
    pass


def check_chapter_rules(document, context):
    pass


def check_source_snippets(document, context, *, allow_long_snippets):
    pass


def check_markdown_safety(document, context):
    pass


def collect_low_confidence(document, context):
    pass
```

Then add the script entrypoint at the very end of `scripts/validate_dsl.py`:

```python
if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run CLI tests to verify GREEN**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_validate_dsl_semantics.CliAndSchemaFirstTests tests.test_validate_dsl.ValidateDslCliTests -v
```

Expected GREEN output:

```text
Ran 5 tests
OK
```

- [ ] **Step 5: Commit**

```bash
git add scripts/validate_dsl.py tests/test_validate_dsl.py tests/test_validate_dsl_semantics.py
git commit -m "feat: add dsl validator cli contract"
```

---

### Task 2: Document Output, Warning Output, And Generated-At Policy

**Files:**
- Modify: `tests/test_validate_dsl_semantics.py`
- Modify: `scripts/validate_dsl.py`

- [ ] **Step 1: Write failing document validation tests**

Append to `tests/test_validate_dsl_semantics.py`:

```python
class DocumentValidationTests(unittest.TestCase):
    def test_generic_output_filename_fails(self):
        for output_file in [
            "STRUCTURE_DESIGN.md",
            "structure_design.md",
            "design.md",
            "软件结构设计说明书.md",
            "software_STRUCTURE_DESIGN.md",
            "structure_STRUCTURE_DESIGN.md",
            "design_STRUCTURE_DESIGN.md",
        ]:
            with tempfile.TemporaryDirectory() as tmpdir:
                document = valid_document()
                document["document"]["output_file"] = output_file
                path = write_json(tmpdir, "generic.dsl.json", document)
                completed = run_validator(path)
            with self.subTest(output_file=output_file):
                self.assertEqual(1, completed.returncode)
                self.assertIn("$.document.output_file", completed.stderr)
                self.assertIn("generic-only output filename", completed.stderr)

    def test_concrete_output_filename_tied_to_documented_object_passes(self):
        for output_file in [
            "create-structure-md_STRUCTURE_DESIGN.md",
            "MOD-SKILL_STRUCTURE_DESIGN.md",
            "技能文档生成模块_STRUCTURE_DESIGN.md",
            "system_create-structure-md_STRUCTURE_DESIGN.md",
            "module_MOD-SKILL_STRUCTURE_DESIGN.md",
        ]:
            with tempfile.TemporaryDirectory() as tmpdir:
                document = valid_document()
                document["document"]["output_file"] = output_file
                path = write_json(tmpdir, "concrete.dsl.json", document)
                completed = run_validator(path)
            with self.subTest(output_file=output_file):
                self.assertEqual(0, completed.returncode, completed.stderr)
                self.assertIn("Validation succeeded", completed.stdout)

    def test_output_filename_without_concrete_documented_object_fails(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            document["document"]["output_file"] = "unrelated_SCOPE_STRUCTURE_DESIGN.md"
            path = write_json(tmpdir, "unrelated.dsl.json", document)
            completed = run_validator(path)
        self.assertEqual(1, completed.returncode)
        self.assertIn("$.document.output_file", completed.stderr)
        self.assertIn("must include a concrete documented object name", completed.stderr)

    def test_output_filename_with_spaces_warns_but_passes(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            document["document"]["output_file"] = "create structure md_STRUCTURE_DESIGN.md"
            path = write_json(tmpdir, "spaces.dsl.json", document)
            completed = run_validator(path)
        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertIn("WARNING", completed.stdout)
        self.assertIn("$.document.output_file", completed.stdout)
        self.assertIn("contains spaces", completed.stdout)
        self.assertIn("Validation succeeded", completed.stdout)

    def test_generated_at_loose_format_warns(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            document["document"]["generated_at"] = "May second"
            path = write_json(tmpdir, "generated-at.dsl.json", document)
            completed = run_validator(path)
        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertIn("$.document.generated_at", completed.stdout)
        self.assertIn("should use ISO-8601", completed.stdout)

    def test_empty_document_title_stops_at_schema_validation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            document["document"]["title"] = ""
            path = write_json(tmpdir, "empty-title.dsl.json", document)
            completed = run_validator(path)
        self.assertEqual(2, completed.returncode)
        self.assertIn("$.document.title", completed.stderr)
        self.assertIn("schema validation failed", completed.stderr)
        self.assertNotIn("semantic validation failed", completed.stderr)
```

- [ ] **Step 2: Run document tests to verify RED**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_validate_dsl_semantics.DocumentValidationTests -v
```

Expected RED output:

```text
FAIL: test_generic_output_filename_fails
AssertionError: 1 != 0
FAIL: test_output_filename_without_concrete_documented_object_fails
AssertionError: 1 != 0
FAIL: test_output_filename_with_spaces_warns_but_passes
AssertionError: 'WARNING' not found
```

- [ ] **Step 3: Implement document validation**

Add these constants and replace `validate_document_fields`:

```python
GENERIC_OUTPUT_NAMES = {
    "structure_design.md",
    "structure-design.md",
    "structuredesign.md",
    "design.md",
    "软件结构设计说明书.md",
}

GENERIC_OUTPUT_TOKENS = {
    "software",
    "structure",
    "design",
    "document",
    "doc",
    "system",
    "module",
    "软件",
    "结构",
    "设计",
    "说明书",
}

DOCUMENT_REQUIRED_TEXT_FIELDS = [
    "title",
    "project_name",
    "document_version",
    "status",
    "language",
    "source_type",
    "output_file",
]

ISO8601_LOCAL_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:[+-]\d{2}:\d{2}|Z)?$"
)


def is_blank(value):
    return not isinstance(value, str) or value.strip() == ""


def normalized_name_tokens(value):
    normalized = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]+", " ", value.casefold())
    return [token for token in normalized.split() if token]


def documented_object_tokens(document):
    doc = document["document"]
    tokens = set(normalized_name_tokens(doc.get("project_name", "")))
    for row in document["architecture_views"]["module_intro"]["rows"]:
        tokens.update(normalized_name_tokens(row["module_id"]))
        tokens.update(normalized_name_tokens(row["module_name"]))
    for module in document["module_design"]["modules"]:
        tokens.update(normalized_name_tokens(module["module_id"]))
        tokens.update(normalized_name_tokens(module["name"]))
    return {token for token in tokens if token not in GENERIC_OUTPUT_TOKENS and len(token) >= 2}


def validate_document_fields(document, report):
    doc = document.get("document", {})
    for field_name in DOCUMENT_REQUIRED_TEXT_FIELDS:
        if is_blank(doc.get(field_name)):
            report.error(
                f"$.document.{field_name}",
                "must be non-empty",
                "Revise the DSL content instead of fabricating filler",
            )

    output_file = doc.get("output_file", "")
    folded = output_file.casefold()
    output_tokens = normalized_name_tokens(Path(output_file).stem)
    concrete_tokens = documented_object_tokens(document)
    contains_concrete_token = any(token in output_tokens for token in concrete_tokens)
    generic_only = bool(output_tokens) and all(token in GENERIC_OUTPUT_TOKENS for token in output_tokens)
    if folded in GENERIC_OUTPUT_NAMES or generic_only:
        report.error(
            "$.document.output_file",
            "generic-only output filename is not allowed",
            "Use a concrete module, subsystem, system, package, or tool name",
        )
    elif not contains_concrete_token:
        report.error(
            "$.document.output_file",
            "must include a concrete documented object name",
            "Use document.project_name, a module ID, a module name, or another documented object name",
        )
    if " " in output_file:
        report.warn(
            "$.document.output_file",
            "contains spaces",
            "Normalize spaces to '_' before writing the final DSL when possible",
        )

    generated_at = doc.get("generated_at", "")
    if generated_at and not ISO8601_LOCAL_RE.match(generated_at):
        report.warn(
            "$.document.generated_at",
            "should use ISO-8601 local datetime with timezone when available",
            "Example: 2026-05-02T10:30:00+08:00",
        )
```

- [ ] **Step 4: Run document tests to verify GREEN**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_validate_dsl_semantics.DocumentValidationTests -v
```

Expected GREEN output:

```text
Ran 6 tests
OK
```

- [ ] **Step 5: Commit**

```bash
git add scripts/validate_dsl.py tests/test_validate_dsl_semantics.py
git commit -m "feat: validate dsl document output metadata"
```

---

### Task 3: ID Registry, Prefixes, Duplicates, And Registered Reference Fields

**Files:**
- Modify: `tests/test_validate_dsl_semantics.py`
- Modify: `scripts/validate_dsl.py`

- [ ] **Step 1: Write failing ID and reference tests**

Append to `tests/test_validate_dsl_semantics.py`:

```python
class IdAndReferenceValidationTests(unittest.TestCase):
    def test_semantic_failure_exits_one_after_schema_success(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            document["architecture_views"]["module_intro"]["rows"][0]["module_id"] = "BAD-MODULE"
            path = write_json(tmpdir, "semantic-fail.dsl.json", document)
            completed = run_validator(path)
        self.assertEqual(1, completed.returncode)
        self.assertEqual("", completed.stdout)
        self.assertIn("ERROR", completed.stderr)
        self.assertIn("$.architecture_views.module_intro.rows[0].module_id", completed.stderr)
        self.assertIn("must start with MOD-", completed.stderr)

    def test_invalid_id_prefix_fails_without_requiring_numeric_suffix(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            document["architecture_views"]["module_intro"]["rows"][0]["module_id"] = "MODULE-SKILL"
            document["module_design"]["modules"][0]["module_id"] = "MODULE-SKILL"
            document["runtime_view"]["runtime_units"]["rows"][0]["related_module_ids"] = ["MODULE-SKILL"]
            document["key_flows"]["flow_index"]["rows"][0]["participant_module_ids"] = ["MODULE-SKILL"]
            document["key_flows"]["flows"][0]["related_module_ids"] = ["MODULE-SKILL"]
            document["key_flows"]["flows"][0]["steps"][0]["related_module_ids"] = ["MODULE-SKILL"]
            path = write_json(tmpdir, "bad-prefix.dsl.json", document)
            completed = run_validator(path)
        self.assertEqual(1, completed.returncode)
        self.assertIn("$.architecture_views.module_intro.rows[0].module_id", completed.stderr)
        self.assertIn("must start with MOD-", completed.stderr)

    def test_duplicate_defining_ids_fail(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            document["evidence"] = [
                {"id": "EV-DUP", "kind": "source", "title": "A", "location": "a", "description": "a", "confidence": "observed"},
                {"id": "EV-DUP", "kind": "note", "title": "B", "location": "b", "description": "b", "confidence": "observed"},
            ]
            path = write_json(tmpdir, "duplicate.dsl.json", document)
            completed = run_validator(path)
        self.assertEqual(1, completed.returncode)
        self.assertIn("$.evidence[1].id", completed.stderr)
        self.assertIn("duplicate ID", completed.stderr)

    def test_non_numeric_suffix_id_passes_when_unique(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            document["architecture_views"]["module_intro"]["rows"][0]["module_id"] = "MOD-RENDER-ALPHA"
            document["module_design"]["modules"][0]["module_id"] = "MOD-RENDER-ALPHA"
            document["runtime_view"]["runtime_units"]["rows"][0]["related_module_ids"] = ["MOD-RENDER-ALPHA"]
            document["key_flows"]["flow_index"]["rows"][0]["participant_module_ids"] = ["MOD-RENDER-ALPHA"]
            document["key_flows"]["flows"][0]["related_module_ids"] = ["MOD-RENDER-ALPHA"]
            document["key_flows"]["flows"][0]["steps"][0]["related_module_ids"] = ["MOD-RENDER-ALPHA"]
            path = write_json(tmpdir, "non-numeric.dsl.json", document)
            completed = run_validator(path)
        self.assertEqual(0, completed.returncode, completed.stderr)

    def test_matching_flow_index_and_detail_ids_are_not_duplicate_ids(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            document["key_flows"]["flow_index"]["rows"][0]["flow_id"] = "FLOW-GENERATE"
            document["key_flows"]["flows"][0]["flow_id"] = "FLOW-GENERATE"
            path = write_json(tmpdir, "paired-flow.dsl.json", document)
            completed = run_validator(path)
        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertNotIn("duplicate ID FLOW-GENERATE", completed.stderr)

    def test_invalid_support_references_fail(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            document["architecture_views"]["module_intro"]["rows"][0]["evidence_refs"] = ["EV-MISSING"]
            path = write_json(tmpdir, "bad-ref.dsl.json", document)
            completed = run_validator(path)
        self.assertEqual(1, completed.returncode)
        self.assertIn("$.architecture_views.module_intro.rows[0].evidence_refs[0]", completed.stderr)
        self.assertIn("references unknown evidence ID EV-MISSING", completed.stderr)

    def test_unregistered_id_field_fails(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            document["architecture_views"]["extra_tables"] = [
                {
                    "id": "TBL-ARCH-EXTRA",
                    "title": "补充表",
                    "columns": [{"key": "owner_module_id", "title": "归属模块"}],
                    "rows": [{"owner_module_id": "MOD-SKILL"}],
                }
            ]
            path = write_json(tmpdir, "unregistered-id.dsl.json", document)
            completed = run_validator(path)
        self.assertEqual(1, completed.returncode)
        self.assertIn("$.architecture_views.extra_tables[0].rows[0].owner_module_id", completed.stderr)
        self.assertIn("unregistered reference-like field", completed.stderr)

    def test_registered_reference_names_fail_when_used_at_unregistered_paths(self):
        for field_name in ["module_id", "target_id", "related_module_ids"]:
            with tempfile.TemporaryDirectory() as tmpdir:
                document = valid_document()
                document["architecture_views"]["extra_tables"] = [
                    {
                        "id": "TBL-ARCH-EXTRA",
                        "title": "补充表",
                        "columns": [{"key": field_name, "title": "非法引用字段"}],
                        "rows": [{field_name: "MOD-SKILL"}],
                    }
                ]
                path = write_json(tmpdir, "path-sensitive-id.dsl.json", document)
                completed = run_validator(path)
            with self.subTest(field_name=field_name):
                self.assertEqual(1, completed.returncode)
                self.assertIn(f"$.architecture_views.extra_tables[0].rows[0].{field_name}", completed.stderr)
                self.assertIn("unregistered reference-like field", completed.stderr)

    def test_traceability_source_external_id_is_allowed_at_traceability_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            document["traceability"] = [{
                "id": "TR-MODULE",
                "source_external_id": "REQ-1",
                "source_type": "requirement",
                "target_type": "module",
                "target_id": "MOD-SKILL",
                "description": "需求映射到模块。",
            }]
            path = write_json(tmpdir, "source-external.dsl.json", document)
            completed = run_validator(path)
        self.assertEqual(0, completed.returncode, completed.stderr)
```

- [ ] **Step 2: Run ID tests to verify RED**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_validate_dsl_semantics.IdAndReferenceValidationTests -v
```

Expected RED output:

```text
FAIL: test_semantic_failure_exits_one_after_schema_success
AssertionError: 1 != 0
FAIL: test_invalid_id_prefix_fails_without_requiring_numeric_suffix
AssertionError: 1 != 0
FAIL: test_duplicate_defining_ids_fail
AssertionError: 1 != 0
FAIL: test_invalid_support_references_fail
AssertionError: 1 != 0
FAIL: test_unregistered_id_field_fails
AssertionError: 1 != 0
```

- [ ] **Step 3: Implement semantic context and ID registration**

Replace `ValidationContext` with this data structure and methods:

```python
PREFIX_BY_KIND = {
    "module": "MOD-",
    "core_capability": "CAP-",
    "provided_capability": "CAP-",
    "runtime_unit": "RUN-",
    "configuration_item": "CFG-",
    "data_artifact": "DATA-",
    "dependency": "DEP-",
    "collaboration": "COL-",
    "flow": "FLOW-",
    "flow_step": "STEP-",
    "flow_branch": "BR-",
    "diagram": "MER-",
    "extra_table": "TBL-",
    "evidence": "EV-",
    "traceability": "TR-",
    "risk": "RISK-",
    "assumption": "ASM-",
    "source_snippet": "SNIP-",
}

SUPPORT_REF_FIELDS = {
    "evidence_refs": "evidence",
    "traceability_refs": "traceability",
    "source_snippet_refs": "source_snippet",
}


class ValidationContext:
    def __init__(self, document, report):
        self.document = document
        self.report = report
        self.ids_by_kind = {kind: {} for kind in PREFIX_BY_KIND}
        self.id_owner = {}
        self.flow_index_ids = []
        self.flow_index_paths = {}
        self.traceability_targets = {}

    def build(self):
        self._register_all_ids()
        self._check_support_refs(self.document)
        self._check_unregistered_id_fields(self.document)

    def register(self, kind, value, path):
        prefix = PREFIX_BY_KIND[kind]
        if not isinstance(value, str) or not value.startswith(prefix):
            self.report.error(path, f"ID must start with {prefix}", "Use the documented prefix; numeric suffixes are optional")
            return
        if value in self.id_owner:
            first_kind, first_path = self.id_owner[value]
            self.report.error(path, f"duplicate ID {value}", f"First defined as {first_kind} at {first_path}")
            return
        self.ids_by_kind[kind][value] = path
        self.id_owner[value] = (kind, path)

    def require_ref(self, kind, value, path, label=None):
        if value not in self.ids_by_kind[kind]:
            name = label or kind.replace("_", " ")
            self.report.error(path, f"references unknown {name} ID {value}", "Define the target ID or correct the reference")

    def register_flow_index_id(self, value, path):
        prefix = PREFIX_BY_KIND["flow"]
        if not isinstance(value, str) or not value.startswith(prefix):
            self.report.error(path, f"ID must start with {prefix}", "Use the documented prefix; numeric suffixes are optional")
            return
        if value in self.flow_index_paths:
            self.report.error(path, f"duplicate flow index ID {value}", f"First defined at {self.flow_index_paths[value]}")
            return
        self.flow_index_ids.append(value)
        self.flow_index_paths[value] = path
```

Add `_register_all_ids` as a method on `ValidationContext` with the same indentation level as `register()` and `require_ref()`. In the real file, indent this whole code block by four spaces under `class ValidationContext`; it is shown flush-left here only for Markdown readability. It registers these exact defining fields:

```python
def _register_all_ids(self):
    doc = self.document
    for i, row in enumerate(doc["architecture_views"]["module_intro"]["rows"]):
        self.register("module", row["module_id"], f"$.architecture_views.module_intro.rows[{i}].module_id")
    for i, item in enumerate(doc["system_overview"]["core_capabilities"]):
        self.register("core_capability", item["capability_id"], f"$.system_overview.core_capabilities[{i}].capability_id")
    for m_i, module in enumerate(doc["module_design"]["modules"]):
        for c_i, row in enumerate(module["external_capability_details"]["provided_capabilities"]["rows"]):
            self.register("provided_capability", row["capability_id"], f"$.module_design.modules[{m_i}].external_capability_details.provided_capabilities.rows[{c_i}].capability_id")
    for i, row in enumerate(doc["runtime_view"]["runtime_units"]["rows"]):
        self.register("runtime_unit", row["unit_id"], f"$.runtime_view.runtime_units.rows[{i}].unit_id")
    for i, row in enumerate(doc["configuration_data_dependencies"]["configuration_items"]["rows"]):
        self.register("configuration_item", row["config_id"], f"$.configuration_data_dependencies.configuration_items.rows[{i}].config_id")
    for i, row in enumerate(doc["configuration_data_dependencies"]["structural_data_artifacts"]["rows"]):
        self.register("data_artifact", row["artifact_id"], f"$.configuration_data_dependencies.structural_data_artifacts.rows[{i}].artifact_id")
    for i, row in enumerate(doc["configuration_data_dependencies"]["dependencies"]["rows"]):
        self.register("dependency", row["dependency_id"], f"$.configuration_data_dependencies.dependencies.rows[{i}].dependency_id")
    for i, row in enumerate(doc["cross_module_collaboration"]["collaboration_scenarios"]["rows"]):
        self.register("collaboration", row["collaboration_id"], f"$.cross_module_collaboration.collaboration_scenarios.rows[{i}].collaboration_id")
    for i, row in enumerate(doc["key_flows"]["flow_index"]["rows"]):
        self.register_flow_index_id(row["flow_id"], f"$.key_flows.flow_index.rows[{i}].flow_id")
    for f_i, flow in enumerate(doc["key_flows"]["flows"]):
        self.register("flow", flow["flow_id"], f"$.key_flows.flows[{f_i}].flow_id")
        for s_i, step in enumerate(flow["steps"]):
            self.register("flow_step", step["step_id"], f"$.key_flows.flows[{f_i}].steps[{s_i}].step_id")
        for b_i, branch in enumerate(flow["branches_or_exceptions"]):
            self.register("flow_branch", branch["branch_id"], f"$.key_flows.flows[{f_i}].branches_or_exceptions[{b_i}].branch_id")
    for kind, collection_name in [("evidence", "evidence"), ("traceability", "traceability"), ("risk", "risks"), ("assumption", "assumptions"), ("source_snippet", "source_snippets")]:
        for i, item in enumerate(doc[collection_name]):
            self.register(kind, item["id"], f"$.{collection_name}[{i}].id")
```

Add diagram and extra table registration by walking all objects:

```python
def walk(value, path="$"):
    yield path, value
    if isinstance(value, dict):
        for key, child in value.items():
            yield from walk(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from walk(child, f"{path}[{index}]")


def is_diagram_object(value):
    return isinstance(value, dict) and {"id", "kind", "diagram_type", "source"}.issubset(value)


def is_extra_table_object(value):
    return isinstance(value, dict) and {"id", "title", "columns", "rows"}.issubset(value)
```

Call these from `_register_all_ids` after support data registration:

```python
for path, value in walk(doc):
    if is_diagram_object(value):
        self.register("diagram", value["id"], f"{path}.id")
    elif is_extra_table_object(value):
        self.register("extra_table", value["id"], f"{path}.id")
```

- [ ] **Step 4: Implement support reference and unregistered `_id` checks**

Add `_check_support_refs` and `_check_unregistered_id_fields` as methods on `ValidationContext`, with the same indentation level as `_register_all_ids`. In the real file, indent this whole code block by four spaces under `class ValidationContext`:

```python
def _check_support_refs(self, value, path="$"):
    if isinstance(value, dict):
        for field_name, target_kind in SUPPORT_REF_FIELDS.items():
            refs = value.get(field_name)
            if isinstance(refs, list):
                for i, ref in enumerate(refs):
                    self.require_ref(target_kind, ref, f"{path}.{field_name}[{i}]", target_kind.replace("_", " "))
        for key, child in value.items():
            self._check_support_refs(child, f"{path}.{key}")
    elif isinstance(value, list):
        for i, child in enumerate(value):
            self._check_support_refs(child, f"{path}[{i}]")


def _check_unregistered_id_fields(self, value, path="$"):
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if (key.endswith("_id") or key.endswith("_ids")) and not is_registered_reference_field(child_path, key):
                self.report.error(f"{path}.{key}", "unregistered reference-like field", "Add the field to the schema and validator registry before using it")
            self._check_unregistered_id_fields(child, child_path)
    elif isinstance(value, list):
        for i, child in enumerate(value):
            self._check_unregistered_id_fields(child, f"{path}[{i}]")
```

Add this path-aware helper above `_check_unregistered_id_fields`:

```python
REGISTERED_REFERENCE_PATHS = [
    re.compile(r"^\$\.architecture_views\.module_intro\.rows\[\d+\]\.module_id$"),
    re.compile(r"^\$\.system_overview\.core_capabilities\[\d+\]\.capability_id$"),
    re.compile(r"^\$\.module_design\.modules\[\d+\]\.module_id$"),
    re.compile(r"^\$\.module_design\.modules\[\d+\]\.external_capability_details\.provided_capabilities\.rows\[\d+\]\.capability_id$"),
    re.compile(r"^\$\.runtime_view\.runtime_units\.rows\[\d+\]\.(unit_id|related_module_ids)$"),
    re.compile(r"^\$\.configuration_data_dependencies\.configuration_items\.rows\[\d+\]\.config_id$"),
    re.compile(r"^\$\.configuration_data_dependencies\.structural_data_artifacts\.rows\[\d+\]\.artifact_id$"),
    re.compile(r"^\$\.configuration_data_dependencies\.dependencies\.rows\[\d+\]\.dependency_id$"),
    re.compile(r"^\$\.cross_module_collaboration\.collaboration_scenarios\.rows\[\d+\]\.(collaboration_id|initiator_module_id|participant_module_ids)$"),
    re.compile(r"^\$\.key_flows\.flow_index\.rows\[\d+\]\.(flow_id|participant_module_ids|participant_runtime_unit_ids)$"),
    re.compile(r"^\$\.key_flows\.flows\[\d+\]\.(flow_id|related_module_ids|related_runtime_unit_ids)$"),
    re.compile(r"^\$\.key_flows\.flows\[\d+\]\.steps\[\d+\]\.(step_id|related_module_ids|related_runtime_unit_ids)$"),
    re.compile(r"^\$\.key_flows\.flows\[\d+\]\.branches_or_exceptions\[\d+\]\.(branch_id|related_module_ids|related_runtime_unit_ids)$"),
    re.compile(r"^\$\.traceability\[\d+\]\.(id|source_external_id|target_id)$"),
    re.compile(r"^\$\.(evidence|risks|assumptions|source_snippets)\[\d+\]\.id$"),
    re.compile(r"^\$.*\.(?:extra_tables\[\d+\]|extra_diagrams\[\d+\]|.*diagram)\.id$"),
]


def is_registered_reference_field(path, field_name):
    if field_name in SUPPORT_REF_FIELDS:
        return True
    return any(pattern.match(path) for pattern in REGISTERED_REFERENCE_PATHS)
```

- [ ] **Step 5: Run ID tests to verify GREEN**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_validate_dsl_semantics.IdAndReferenceValidationTests -v
```

Expected GREEN output:

```text
Ran 9 tests
OK
```

- [ ] **Step 6: Commit**

```bash
git add scripts/validate_dsl.py tests/test_validate_dsl_semantics.py
git commit -m "feat: validate dsl ids and support references"
```

---

### Task 4: Chapter 2 Through 6 Semantic Rules

**Files:**
- Modify: `tests/test_validate_dsl_semantics.py`
- Modify: `scripts/validate_dsl.py`

- [ ] **Step 1: Write failing chapter 2-6 tests**

Append to `tests/test_validate_dsl_semantics.py`:

```python
class ChapterTwoThroughSixTests(unittest.TestCase):
    def test_chapter_three_module_rows_must_be_non_empty_and_diagram_mentions_warn(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            document["architecture_views"]["module_intro"]["rows"] = []
            path = write_json(tmpdir, "no-modules.dsl.json", document)
            completed = run_validator(path)
        self.assertEqual(1, completed.returncode)
        self.assertIn("$.architecture_views.module_intro.rows", completed.stderr)
        self.assertIn("must contain at least one module", completed.stderr)

        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            document["architecture_views"]["module_relationship_diagram"]["source"] = "flowchart TD\n  A --> B"
            path = write_json(tmpdir, "diagram-warn.dsl.json", document)
            completed = run_validator(path)
        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertIn("WARNING", completed.stdout)
        self.assertIn("does not mention module MOD-SKILL", completed.stdout)

    def test_chapter_four_modules_match_chapter_three_one_to_one(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            document["module_design"]["modules"][0]["module_id"] = "MOD-OTHER"
            path = write_json(tmpdir, "module-mismatch.dsl.json", document)
            completed = run_validator(path)
        self.assertEqual(1, completed.returncode)
        self.assertIn("$.module_design.modules", completed.stderr)
        self.assertIn("must match chapter 3 modules one-to-one", completed.stderr)

    def test_internal_structure_requires_diagram_source_or_text(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            internal = document["module_design"]["modules"][0]["internal_structure"]
            internal["diagram"]["source"] = ""
            internal["textual_structure"] = ""
            internal["not_applicable_reason"] = "使用文字说明"
            path = write_json(tmpdir, "internal-empty.dsl.json", document)
            completed = run_validator(path)
        self.assertEqual(1, completed.returncode)
        self.assertIn("$.module_design.modules[0].internal_structure", completed.stderr)
        self.assertIn("requires diagram source or textual_structure", completed.stderr)

    def test_runtime_entrypoint_and_related_modules_empty_reasons(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            unit = document["runtime_view"]["runtime_units"]["rows"][0]
            unit["entrypoint"] = ""
            unit["entrypoint_not_applicable_reason"] = ""
            unit["related_module_ids"] = []
            unit["external_environment_reason"] = ""
            path = write_json(tmpdir, "runtime-reasons.dsl.json", document)
            completed = run_validator(path)
        self.assertEqual(1, completed.returncode)
        self.assertIn("$.runtime_view.runtime_units.rows[0].entrypoint_not_applicable_reason", completed.stderr)
        self.assertIn("$.runtime_view.runtime_units.rows[0].external_environment_reason", completed.stderr)

    def test_required_diagrams_and_optional_extra_diagrams_need_source(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            document["runtime_view"]["runtime_flow_diagram"]["source"] = ""
            document["architecture_views"]["extra_diagrams"] = [
                {
                    "id": "MER-ARCH-EMPTY",
                    "kind": "extra",
                    "title": "空图",
                    "diagram_type": "flowchart",
                    "description": "补充图",
                    "source": "",
                    "confidence": "observed",
                }
            ]
            path = write_json(tmpdir, "diagrams-empty.dsl.json", document)
            completed = run_validator(path)
        self.assertEqual(1, completed.returncode)
        self.assertIn("$.runtime_view.runtime_flow_diagram.source", completed.stderr)
        self.assertIn("$.architecture_views.extra_diagrams[0].source", completed.stderr)

    def test_runtime_sequence_diagram_must_use_sequence_diagram_when_present(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            document["runtime_view"]["runtime_sequence_diagram"] = {
                "id": "MER-RUNTIME-SEQ",
                "kind": "runtime_sequence",
                "title": "运行时序列图",
                "diagram_type": "flowchart",
                "description": "错误类型",
                "source": "flowchart TD\n  A --> B",
                "confidence": "observed",
            }
            path = write_json(tmpdir, "runtime-sequence.dsl.json", document)
            completed = run_validator(path)
        self.assertEqual(1, completed.returncode)
        self.assertIn("$.runtime_view.runtime_sequence_diagram.source", completed.stderr)
        self.assertIn("must use sequenceDiagram", completed.stderr)
```

- [ ] **Step 2: Run chapter 2-6 tests to verify RED**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_validate_dsl_semantics.ChapterTwoThroughSixTests -v
```

Expected RED output:

```text
FAIL: test_chapter_three_module_rows_must_be_non_empty_and_diagram_mentions_warn
AssertionError: 1 != 0
FAIL: test_chapter_four_modules_match_chapter_three_one_to_one
AssertionError: 1 != 0
```

- [ ] **Step 3: Implement chapter 2-6 rules**

Replace `check_chapter_rules` with a dispatcher:

```python
def check_chapter_rules(document, context):
    check_chapter_2(document, context)
    check_chapter_3(document, context)
    check_chapter_4(document, context)
    check_chapter_5(document, context)
    check_chapter_6(document, context)
    check_chapter_7(document, context)
    check_chapter_8(document, context)
    check_chapter_9(document, context)
    check_all_extra_diagrams(document, context)
```

Add these helpers and functions:

```python
def require_non_empty(report, path, value, label):
    if is_blank(value):
        report.error(path, f"{label} must be non-empty", "Revise the structured design content")


def require_non_empty_list(report, path, value, label):
    if not isinstance(value, list) or len(value) == 0:
        report.error(path, f"{label} must contain at least one item", "Provide real content or use the documented empty representation only when allowed")


def diagram_source_required(report, path, diagram, label):
    if is_blank(diagram.get("source", "")):
        report.error(f"{path}.source", f"{label} source must be non-empty", "Mermaid syntax is checked by validate_mermaid.py; this validator only requires content")


def check_chapter_2(document, context):
    overview = document["system_overview"]
    require_non_empty(context.report, "$.system_overview.summary", overview["summary"], "chapter 2 summary")
    require_non_empty(context.report, "$.system_overview.purpose", overview["purpose"], "chapter 2 purpose")
    for i, capability in enumerate(overview["core_capabilities"]):
        base = f"$.system_overview.core_capabilities[{i}]"
        require_non_empty(context.report, f"{base}.capability_id", capability["capability_id"], "core capability ID")
        require_non_empty(context.report, f"{base}.name", capability["name"], "core capability name")
        require_non_empty(context.report, f"{base}.description", capability["description"], "core capability description")


def check_chapter_3(document, context):
    arch = document["architecture_views"]
    require_non_empty(context.report, "$.architecture_views.summary", arch["summary"], "chapter 3 summary")
    rows = arch["module_intro"]["rows"]
    if not rows:
        context.report.error("$.architecture_views.module_intro.rows", "must contain at least one module", "Chapter 3 defines canonical module IDs")
    diagram_source_required(context.report, "$.architecture_views.module_relationship_diagram", arch["module_relationship_diagram"], "module relationship diagram")
    source = arch["module_relationship_diagram"].get("source", "")
    for i, row in enumerate(rows):
        base = f"$.architecture_views.module_intro.rows[{i}]"
        for field_name in ["module_id", "module_name", "responsibility"]:
            require_non_empty(context.report, f"{base}.{field_name}", row[field_name], field_name)
        if row["module_id"] not in source and row["module_name"] not in source:
            context.report.warn(f"{base}.module_id", f"module relationship diagram does not mention module {row['module_id']} or {row['module_name']}", "Mention the module ID or name in the diagram source")


def check_chapter_4(document, context):
    module_ids = [row["module_id"] for row in document["architecture_views"]["module_intro"]["rows"]]
    design_modules = document["module_design"]["modules"]
    design_ids = [item["module_id"] for item in design_modules]
    require_non_empty(context.report, "$.module_design.summary", document["module_design"]["summary"], "chapter 4 summary")
    if sorted(module_ids) != sorted(design_ids) or len(module_ids) != len(design_ids):
        context.report.error("$.module_design.modules", "must match chapter 3 modules one-to-one", "Create exactly one module design entry for each chapter 3 module")
    for i, module in enumerate(design_modules):
        base = f"$.module_design.modules[{i}]"
        context.require_ref("module", module["module_id"], f"{base}.module_id", "module")
        require_non_empty_list(context.report, f"{base}.responsibilities", module["responsibilities"], "module responsibilities")
        require_non_empty(context.report, f"{base}.external_capability_summary.description", module["external_capability_summary"]["description"], "external capability summary description")
        rows = module["external_capability_details"]["provided_capabilities"]["rows"]
        require_non_empty_list(context.report, f"{base}.external_capability_details.provided_capabilities.rows", rows, "provided capability rows")
        internal = module["internal_structure"]
        if is_blank(internal["diagram"].get("source", "")) and is_blank(internal["textual_structure"]):
            context.report.error(f"{base}.internal_structure", "requires diagram source or textual_structure", "not_applicable_reason alone does not satisfy the internal structure rule")


def check_chapter_5(document, context):
    runtime = document["runtime_view"]
    require_non_empty(context.report, "$.runtime_view.summary", runtime["summary"], "chapter 5 summary")
    units = runtime["runtime_units"]["rows"]
    require_non_empty_list(context.report, "$.runtime_view.runtime_units.rows", units, "runtime units")
    for i, unit in enumerate(units):
        base = f"$.runtime_view.runtime_units.rows[{i}]"
        for ref_i, module_id in enumerate(unit["related_module_ids"]):
            context.require_ref("module", module_id, f"{base}.related_module_ids[{ref_i}]", "module")
        if is_blank(unit["entrypoint"]):
            require_non_empty(context.report, f"{base}.entrypoint_not_applicable_reason", unit["entrypoint_not_applicable_reason"], "entrypoint_not_applicable_reason")
        if not unit["related_module_ids"]:
            require_non_empty(context.report, f"{base}.external_environment_reason", unit["external_environment_reason"], "external_environment_reason")
    diagram_source_required(context.report, "$.runtime_view.runtime_flow_diagram", runtime["runtime_flow_diagram"], "runtime flow diagram")
    sequence = runtime.get("runtime_sequence_diagram")
    if sequence and not is_blank(sequence.get("source", "")) and not sequence["source"].lstrip().startswith("sequenceDiagram"):
        context.report.error("$.runtime_view.runtime_sequence_diagram.source", "must use sequenceDiagram", "Mermaid syntax remains the responsibility of validate_mermaid.py")


def check_chapter_6(document, context):
    for table_name, id_field, required_fields in [
        ("configuration_items", "config_id", ["config_id", "config_name", "purpose"]),
        ("structural_data_artifacts", "artifact_id", ["artifact_id", "artifact_name", "artifact_type", "owner"]),
        ("dependencies", "dependency_id", ["dependency_id", "dependency_name", "dependency_type", "purpose"]),
    ]:
        for i, row in enumerate(document["configuration_data_dependencies"][table_name]["rows"]):
            base = f"$.configuration_data_dependencies.{table_name}.rows[{i}]"
            for field_name in required_fields:
                require_non_empty(context.report, f"{base}.{field_name}", row[field_name], field_name)
```

Keep temporary no-op implementations for `check_chapter_7`, `check_chapter_8`, `check_chapter_9`, and `check_all_extra_diagrams` for this task; Tasks 5 and 8 replace these definitions:

```python
def check_chapter_7(document, context):
    pass


def check_chapter_8(document, context):
    pass


def check_chapter_9(document, context):
    pass


def check_all_extra_diagrams(document, context):
    for path, value in walk(document):
        if path.endswith(".extra_diagrams") and isinstance(value, list):
            for i, diagram in enumerate(value):
                diagram_source_required(context.report, f"{path}[{i}]", diagram, "extra diagram")
```

- [ ] **Step 4: Run chapter 2-6 tests to verify GREEN**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_validate_dsl_semantics.ChapterTwoThroughSixTests -v
```

Expected GREEN output:

```text
Ran 6 tests
OK
```

- [ ] **Step 5: Commit**

```bash
git add scripts/validate_dsl.py tests/test_validate_dsl_semantics.py
git commit -m "feat: validate dsl chapters two through six"
```

---

### Task 5: Chapter 7 And Chapter 8 Flow Semantics

**Files:**
- Modify: `tests/test_validate_dsl_semantics.py`
- Modify: `scripts/validate_dsl.py`

- [ ] **Step 1: Write failing chapter 7 and 8 tests**

Append to `tests/test_validate_dsl_semantics.py`:

```python
class ChapterSevenAndEightTests(unittest.TestCase):
    def make_two_module_document(self):
        document = valid_document()
        document["architecture_views"]["module_intro"]["rows"].append({
            "module_id": "MOD-RENDER",
            "module_name": "渲染模块",
            "responsibility": "生成 Markdown。",
            "inputs": "DSL",
            "outputs": "Markdown",
            "notes": "",
            "confidence": "observed",
            "evidence_refs": [],
            "traceability_refs": [],
            "source_snippet_refs": [],
        })
        second = deepcopy(document["module_design"]["modules"][0])
        second["module_id"] = "MOD-RENDER"
        second["name"] = "渲染模块"
        second["external_capability_details"]["provided_capabilities"]["rows"][0]["capability_id"] = "CAP-RENDER"
        second["internal_structure"]["diagram"]["id"] = "MER-MOD-RENDER-STRUCT"
        document["module_design"]["modules"].append(second)
        document["architecture_views"]["module_relationship_diagram"]["source"] += "\n  MOD-SKILL --> MOD-RENDER"
        return document

    def test_single_module_chapter_7_allows_empty_collaboration(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            document["cross_module_collaboration"]["summary"] = ""
            document["cross_module_collaboration"]["collaboration_scenarios"]["rows"] = []
            document["cross_module_collaboration"].pop("collaboration_relationship_diagram", None)
            path = write_json(tmpdir, "single-module.dsl.json", document)
            completed = run_validator(path)
        self.assertEqual(0, completed.returncode, completed.stderr)

    def test_single_module_chapter_7_allows_empty_full_diagram_object(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            document["cross_module_collaboration"]["summary"] = ""
            document["cross_module_collaboration"]["collaboration_scenarios"]["rows"] = []
            document["cross_module_collaboration"]["collaboration_relationship_diagram"] = {
                "id": "MER-COLLAB-EMPTY",
                "kind": "collaboration_relationship",
                "title": "空协作图",
                "diagram_type": "flowchart",
                "description": "单模块模式允许协作图为空。",
                "source": "",
                "confidence": "observed",
            }
            path = write_json(tmpdir, "single-empty-diagram.dsl.json", document)
            completed = run_validator(path)
        self.assertEqual(0, completed.returncode, completed.stderr)

    def test_multi_module_chapter_7_requires_summary_rows_and_diagram(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            document = self.make_two_module_document()
            document["cross_module_collaboration"]["summary"] = ""
            document["cross_module_collaboration"]["collaboration_scenarios"]["rows"] = []
            document["cross_module_collaboration"].pop("collaboration_relationship_diagram", None)
            path = write_json(tmpdir, "multi-empty.dsl.json", document)
            completed = run_validator(path)
        self.assertEqual(1, completed.returncode)
        self.assertIn("$.cross_module_collaboration.summary", completed.stderr)
        self.assertIn("$.cross_module_collaboration.collaboration_scenarios.rows", completed.stderr)
        self.assertIn("$.cross_module_collaboration.collaboration_relationship_diagram", completed.stderr)

    def test_single_module_chapter_7_validates_provided_content(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            document["cross_module_collaboration"]["collaboration_scenarios"]["rows"] = [{
                "collaboration_id": "COL-BAD-REF",
                "scenario": "可选协作内容",
                "initiator_module_id": "MOD-MISSING",
                "participant_module_ids": ["MOD-SKILL"],
                "collaboration_method": "调用",
                "description": "单模块模式中提供的内容仍需校验引用。",
                "confidence": "observed",
                "evidence_refs": [],
                "traceability_refs": [],
                "source_snippet_refs": [],
            }]
            path = write_json(tmpdir, "single-invalid-collab.dsl.json", document)
            completed = run_validator(path)
        self.assertEqual(1, completed.returncode)
        self.assertIn("$.cross_module_collaboration.collaboration_scenarios.rows[0].initiator_module_id", completed.stderr)
        self.assertNotIn("$.cross_module_collaboration.collaboration_relationship_diagram.source", completed.stderr)

    def test_multi_module_collaboration_must_involve_two_distinct_modules(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            document = self.make_two_module_document()
            document["cross_module_collaboration"]["summary"] = "模块协作。"
            document["cross_module_collaboration"]["collaboration_scenarios"]["rows"] = [{
                "collaboration_id": "COL-ONE",
                "scenario": "单模块自调用",
                "initiator_module_id": "MOD-SKILL",
                "participant_module_ids": ["MOD-SKILL"],
                "collaboration_method": "调用",
                "description": "只有一个模块。",
                "confidence": "observed",
                "evidence_refs": [],
                "traceability_refs": [],
                "source_snippet_refs": [],
            }]
            document["cross_module_collaboration"]["collaboration_relationship_diagram"] = {
                "id": "MER-COLLAB-TWO",
                "kind": "collaboration_relationship",
                "title": "协作图",
                "diagram_type": "flowchart",
                "description": "协作",
                "source": "flowchart TD\n  MOD-SKILL --> MOD-RENDER",
                "confidence": "observed",
            }
            path = write_json(tmpdir, "collab-one.dsl.json", document)
            completed = run_validator(path)
        self.assertEqual(1, completed.returncode)
        self.assertIn("$.cross_module_collaboration.collaboration_scenarios.rows[0]", completed.stderr)
        self.assertIn("at least two distinct modules", completed.stderr)

    def test_flow_index_and_detail_must_match_one_to_one(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            document["key_flows"]["flows"][0]["flow_id"] = "FLOW-DETAIL-ONLY"
            path = write_json(tmpdir, "flow-mismatch.dsl.json", document)
            completed = run_validator(path)
        self.assertEqual(1, completed.returncode)
        self.assertIn("$.key_flows", completed.stderr)
        self.assertIn("flow_index rows and flow details must match one-to-one", completed.stderr)

    def test_flow_participants_and_steps_have_reference_and_uniqueness_rules(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            document["key_flows"]["flow_index"]["rows"][0]["participant_module_ids"] = []
            document["key_flows"]["flow_index"]["rows"][0]["participant_runtime_unit_ids"] = []
            document["key_flows"]["flows"][0]["steps"].append(deepcopy(document["key_flows"]["flows"][0]["steps"][0]))
            document["key_flows"]["flows"][0]["steps"][1]["order"] = 1
            document["key_flows"]["flows"][0]["branches_or_exceptions"] = [
                {
                    "branch_id": "BR-DUP",
                    "condition": "条件 A",
                    "handling": "处理 A",
                    "related_module_ids": ["MOD-SKILL"],
                    "related_runtime_unit_ids": ["RUN-GENERATE"],
                    "confidence": "observed",
                    "evidence_refs": [],
                    "traceability_refs": [],
                    "source_snippet_refs": [],
                },
                {
                    "branch_id": "BR-DUP",
                    "condition": "条件 B",
                    "handling": "处理 B",
                    "related_module_ids": ["MOD-SKILL"],
                    "related_runtime_unit_ids": ["RUN-GENERATE"],
                    "confidence": "observed",
                    "evidence_refs": [],
                    "traceability_refs": [],
                    "source_snippet_refs": [],
                },
            ]
            path = write_json(tmpdir, "flow-rules.dsl.json", document)
            completed = run_validator(path)
        self.assertEqual(1, completed.returncode)
        self.assertIn("$.key_flows.flow_index.rows[0]", completed.stderr)
        self.assertIn("must have at least one participant", completed.stderr)
        self.assertIn("duplicate ID", completed.stderr)
        self.assertIn("step order values must be unique", completed.stderr)
```

- [ ] **Step 2: Run chapter 7-8 tests to verify RED**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_validate_dsl_semantics.ChapterSevenAndEightTests -v
```

Expected RED output:

```text
FAIL: test_multi_module_chapter_7_requires_summary_rows_and_diagram
AssertionError: 1 != 0
FAIL: test_flow_index_and_detail_must_match_one_to_one
AssertionError: 1 != 0
```

- [ ] **Step 3: Implement chapter 7 collaboration rules**

Replace `check_chapter_7`:

```python
def check_chapter_7(document, context):
    module_count = len(document["architecture_views"]["module_intro"]["rows"])
    chapter = document["cross_module_collaboration"]
    rows = chapter["collaboration_scenarios"]["rows"]
    diagram = chapter.get("collaboration_relationship_diagram")

    if module_count >= 2:
        require_non_empty(context.report, "$.cross_module_collaboration.summary", chapter["summary"], "chapter 7 summary")
        require_non_empty_list(context.report, "$.cross_module_collaboration.collaboration_scenarios.rows", rows, "collaboration rows")
        if not diagram:
            context.report.error("$.cross_module_collaboration.collaboration_relationship_diagram", "multi-module mode requires a collaboration diagram", "Add a diagram object with non-empty Mermaid source")

    if module_count >= 2 and diagram:
        diagram_source_required(context.report, "$.cross_module_collaboration.collaboration_relationship_diagram", diagram, "collaboration relationship diagram")

    for i, row in enumerate(rows):
        base = f"$.cross_module_collaboration.collaboration_scenarios.rows[{i}]"
        context.require_ref("module", row["initiator_module_id"], f"{base}.initiator_module_id", "module")
        participants = set(row["participant_module_ids"])
        for ref_i, module_id in enumerate(row["participant_module_ids"]):
            context.require_ref("module", module_id, f"{base}.participant_module_ids[{ref_i}]", "module")
        distinct_modules = participants | {row["initiator_module_id"]}
        if module_count >= 2 and len(distinct_modules) < 2:
            context.report.error(base, "collaboration must involve at least two distinct modules", "For single-module scopes leave chapter 7 empty instead")
```

- [ ] **Step 4: Implement chapter 8 flow matching and participant rules**

Replace `check_chapter_8`:

```python
def check_chapter_8(document, context):
    key_flows = document["key_flows"]
    require_non_empty(context.report, "$.key_flows.summary", key_flows["summary"], "chapter 8 summary")
    index_rows = key_flows["flow_index"]["rows"]
    flows = key_flows["flows"]
    require_non_empty_list(context.report, "$.key_flows.flow_index.rows", index_rows, "flow index rows")

    index_ids = context.flow_index_ids
    detail_ids = [flow["flow_id"] for flow in flows]
    if sorted(index_ids) != sorted(detail_ids) or len(index_ids) != len(detail_ids):
        context.report.error("$.key_flows", "flow_index rows and flow details must match one-to-one", "Use the same FLOW-* IDs in both collections")

    for i, row in enumerate(index_rows):
        base = f"$.key_flows.flow_index.rows[{i}]"
        if not row["participant_module_ids"] and not row["participant_runtime_unit_ids"]:
            context.report.error(base, "flow index row must have at least one participant", "Use participant_module_ids or participant_runtime_unit_ids")
        for ref_i, module_id in enumerate(row["participant_module_ids"]):
            context.require_ref("module", module_id, f"{base}.participant_module_ids[{ref_i}]", "module")
        for ref_i, unit_id in enumerate(row["participant_runtime_unit_ids"]):
            context.require_ref("runtime_unit", unit_id, f"{base}.participant_runtime_unit_ids[{ref_i}]", "runtime unit")

    for f_i, flow in enumerate(flows):
        base = f"$.key_flows.flows[{f_i}]"
        require_non_empty_list(context.report, f"{base}.steps", flow["steps"], "flow steps")
        diagram_source_required(context.report, f"{base}.diagram", flow["diagram"], "key flow diagram")
        for ref_i, module_id in enumerate(flow["related_module_ids"]):
            context.require_ref("module", module_id, f"{base}.related_module_ids[{ref_i}]", "module")
        for ref_i, unit_id in enumerate(flow["related_runtime_unit_ids"]):
            context.require_ref("runtime_unit", unit_id, f"{base}.related_runtime_unit_ids[{ref_i}]", "runtime unit")
        seen_orders = set()
        for s_i, step in enumerate(flow["steps"]):
            step_base = f"{base}.steps[{s_i}]"
            if step["order"] in seen_orders:
                context.report.error(f"{step_base}.order", "step order values must be unique within one flow", "Renumber this flow's steps")
            seen_orders.add(step["order"])
            for ref_i, module_id in enumerate(step["related_module_ids"]):
                context.require_ref("module", module_id, f"{step_base}.related_module_ids[{ref_i}]", "module")
            for ref_i, unit_id in enumerate(step["related_runtime_unit_ids"]):
                context.require_ref("runtime_unit", unit_id, f"{step_base}.related_runtime_unit_ids[{ref_i}]", "runtime unit")
        for b_i, branch in enumerate(flow["branches_or_exceptions"]):
            branch_base = f"{base}.branches_or_exceptions[{b_i}]"
            for ref_i, module_id in enumerate(branch["related_module_ids"]):
                context.require_ref("module", module_id, f"{branch_base}.related_module_ids[{ref_i}]", "module")
            for ref_i, unit_id in enumerate(branch["related_runtime_unit_ids"]):
                context.require_ref("runtime_unit", unit_id, f"{branch_base}.related_runtime_unit_ids[{ref_i}]", "runtime unit")
```

- [ ] **Step 5: Run chapter 7-8 tests to verify GREEN**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_validate_dsl_semantics.ChapterSevenAndEightTests -v
```

Expected GREEN output:

```text
Ran 7 tests
OK
```

- [ ] **Step 6: Commit**

```bash
git add scripts/validate_dsl.py tests/test_validate_dsl_semantics.py
git commit -m "feat: validate collaboration and key flow semantics"
```

---

### Task 6: Extra Tables And Traceability Targets

**Files:**
- Modify: `tests/test_validate_dsl_semantics.py`
- Modify: `scripts/validate_dsl.py`

- [ ] **Step 1: Write failing extra table and traceability tests**

Append to `tests/test_validate_dsl_semantics.py`:

```python
class ExtraTableAndTraceabilityTests(unittest.TestCase):
    def test_extra_table_rows_reject_unknown_keys_but_allow_missing_declared_keys(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            document["architecture_views"]["extra_tables"] = [{
                "id": "TBL-ARCH-001",
                "title": "补充表",
                "columns": [{"key": "name", "title": "名称"}, {"key": "role", "title": "角色"}],
                "rows": [{"name": "A", "extra": "B", "evidence_refs": []}],
            }]
            path = write_json(tmpdir, "extra-table.dsl.json", document)
            completed = run_validator(path)
        self.assertEqual(1, completed.returncode)
        self.assertIn("$.architecture_views.extra_tables[0].rows[0]", completed.stderr)
        self.assertIn("row contains keys outside declared columns", completed.stderr)

        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            document["architecture_views"]["extra_tables"] = [{
                "id": "TBL-ARCH-002",
                "title": "补充表",
                "columns": [{"key": "name", "title": "名称"}, {"key": "role", "title": "角色"}],
                "rows": [{"name": "A"}],
            }]
            path = write_json(tmpdir, "extra-table-missing-ok.dsl.json", document)
            completed = run_validator(path)
        self.assertEqual(0, completed.returncode, completed.stderr)

    def test_extra_table_duplicate_column_keys_fail(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            document["architecture_views"]["extra_tables"] = [{
                "id": "TBL-ARCH-DUP",
                "title": "补充表",
                "columns": [{"key": "name", "title": "名称"}, {"key": "name", "title": "重复名称"}],
                "rows": [{"name": "A"}],
            }]
            path = write_json(tmpdir, "extra-table-duplicate.dsl.json", document)
            completed = run_validator(path)
        self.assertEqual(1, completed.returncode)
        self.assertIn("$.architecture_views.extra_tables[0].columns[1].key", completed.stderr)
        self.assertIn("duplicate extra table column key", completed.stderr)

    def test_traceability_target_id_must_resolve_by_target_type(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            document["traceability"] = [{
                "id": "TR-MISSING",
                "source_external_id": "REQ-1",
                "source_type": "requirement",
                "target_type": "module",
                "target_id": "MOD-MISSING",
                "description": "错误映射",
            }]
            path = write_json(tmpdir, "trace-missing.dsl.json", document)
            completed = run_validator(path)
        self.assertEqual(1, completed.returncode)
        self.assertIn("$.traceability[0].target_id", completed.stderr)
        self.assertIn("does not resolve for target_type module", completed.stderr)

    def test_local_traceability_backlink_must_target_current_node(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            document["traceability"] = [{
                "id": "TR-MODULE",
                "source_external_id": "REQ-1",
                "source_type": "requirement",
                "target_type": "module",
                "target_id": "MOD-SKILL",
                "description": "模块追踪",
            }]
            document["runtime_view"]["runtime_units"]["rows"][0]["traceability_refs"] = ["TR-MODULE"]
            path = write_json(tmpdir, "trace-backlink.dsl.json", document)
            completed = run_validator(path)
        self.assertEqual(1, completed.returncode)
        self.assertIn("$.runtime_view.runtime_units.rows[0].traceability_refs[0]", completed.stderr)
        self.assertIn("targets module MOD-SKILL instead of runtime_unit", completed.stderr)

    def test_valid_local_traceability_backlink_passes(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            document["traceability"] = [{
                "id": "TR-RUNTIME",
                "source_external_id": "REQ-2",
                "source_type": "requirement",
                "target_type": "runtime_unit",
                "target_id": "RUN-GENERATE",
                "description": "运行单元追踪",
            }]
            document["runtime_view"]["runtime_units"]["rows"][0]["traceability_refs"] = ["TR-RUNTIME"]
            path = write_json(tmpdir, "trace-valid-backlink.dsl.json", document)
            completed = run_validator(path)
        self.assertEqual(0, completed.returncode, completed.stderr)

    def test_traceability_flow_branch_target_resolves(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            document["key_flows"]["flows"][0]["branches_or_exceptions"] = [{
                "branch_id": "BR-GENERATE-001",
                "condition": "DSL 校验失败",
                "handling": "停止渲染并报告结构问题。",
                "related_module_ids": ["MOD-SKILL"],
                "related_runtime_unit_ids": ["RUN-GENERATE"],
                "confidence": "observed",
                "evidence_refs": [],
                "traceability_refs": ["TR-BRANCH"],
                "source_snippet_refs": [],
            }]
            document["traceability"] = [{
                "id": "TR-BRANCH",
                "source_external_id": "REQ-BRANCH",
                "source_type": "requirement",
                "target_type": "flow_branch",
                "target_id": "BR-GENERATE-001",
                "description": "分支追踪",
            }]
            path = write_json(tmpdir, "trace-flow-branch.dsl.json", document)
            completed = run_validator(path)
        self.assertEqual(0, completed.returncode, completed.stderr)

    def test_unreferenced_evidence_warns(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            document["evidence"] = [{
                "id": "EV-UNUSED",
                "kind": "note",
                "title": "未使用证据",
                "location": "notes",
                "description": "没有被引用。",
                "confidence": "observed",
            }]
            path = write_json(tmpdir, "unused-evidence.dsl.json", document)
            completed = run_validator(path)
        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertIn("WARNING", completed.stdout)
        self.assertIn("$.evidence[0].id", completed.stdout)
        self.assertIn("unreferenced evidence", completed.stdout)
```

- [ ] **Step 2: Run extra table and traceability tests to verify RED**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_validate_dsl_semantics.ExtraTableAndTraceabilityTests -v
```

Expected RED output:

```text
FAIL: test_extra_table_rows_reject_unknown_keys_but_allow_missing_declared_keys
AssertionError: 1 != 0
FAIL: test_traceability_target_id_must_resolve_by_target_type
AssertionError: 1 != 0
```

- [ ] **Step 3: Implement extra table column-key validation**

Add to `run_semantic_checks` before source snippet checks:

```python
check_extra_tables(document, context)
check_traceability(document, context)
```

Add:

```python
def check_extra_tables(document, context):
    for path, value in walk(document):
        if not is_extra_table_object(value):
            continue
        column_keys = [column["key"] for column in value["columns"]]
        seen_column_keys = set()
        for i, key in enumerate(column_keys):
            if key in seen_column_keys:
                context.report.error(
                    f"{path}.columns[{i}].key",
                    f"duplicate extra table column key {key}",
                    "Each extra table column key must be unique",
                )
            seen_column_keys.add(key)
        allowed_keys = set(column_keys) | {"evidence_refs"}
        for i, row in enumerate(value["rows"]):
            row_keys = set(row)
            unknown_keys = row_keys - allowed_keys
            if unknown_keys:
                context.report.error(
                    f"{path}.rows[{i}]",
                    "row contains keys outside declared columns",
                    f"Remove unknown keys: {', '.join(sorted(unknown_keys))}",
                )
```

- [ ] **Step 4: Implement traceability target validation and backlinks**

Add target mapping and functions:

```python
TRACEABILITY_TARGET_KIND = {
    "module": "module",
    "core_capability": "core_capability",
    "provided_capability": "provided_capability",
    "runtime_unit": "runtime_unit",
    "flow": "flow",
    "flow_step": "flow_step",
    "flow_branch": "flow_branch",
    "collaboration": "collaboration",
    "configuration_item": "configuration_item",
    "data_artifact": "data_artifact",
    "dependency": "dependency",
    "risk": "risk",
    "assumption": "assumption",
    "source_snippet": "source_snippet",
}


def check_traceability(document, context):
    for i, trace in enumerate(document["traceability"]):
        target_type = trace["target_type"]
        target_id = trace["target_id"]
        kind = TRACEABILITY_TARGET_KIND[target_type]
        if target_id not in context.ids_by_kind[kind]:
            context.report.error(
                f"$.traceability[{i}].target_id",
                f"does not resolve for target_type {target_type}",
                "Use an ID defined by the target mapping in the Phase 3 spec",
            )
        context.traceability_targets[trace["id"]] = (target_type, target_id)
    check_traceability_backlinks(document, context)


def current_traceability_target(path, value):
    if not isinstance(value, dict):
        return None
    if "module_id" in value:
        return ("module", value["module_id"])
    if "capability_id" in value and ".system_overview.core_capabilities" in path:
        return ("core_capability", value["capability_id"])
    if "capability_id" in value and ".provided_capabilities.rows" in path:
        return ("provided_capability", value["capability_id"])
    if "unit_id" in value:
        return ("runtime_unit", value["unit_id"])
    if "collaboration_id" in value:
        return ("collaboration", value["collaboration_id"])
    if "config_id" in value:
        return ("configuration_item", value["config_id"])
    if "artifact_id" in value:
        return ("data_artifact", value["artifact_id"])
    if "dependency_id" in value:
        return ("dependency", value["dependency_id"])
    if "flow_id" in value and ".key_flows.flows" in path:
        return ("flow", value["flow_id"])
    if "step_id" in value:
        return ("flow_step", value["step_id"])
    if "branch_id" in value:
        return ("flow_branch", value["branch_id"])
    if path.startswith("$.risks["):
        return ("risk", value.get("id"))
    if path.startswith("$.assumptions["):
        return ("assumption", value.get("id"))
    return None


def check_traceability_backlinks(document, context):
    for path, value in walk(document):
        if not isinstance(value, dict) or "traceability_refs" not in value:
            continue
        current = current_traceability_target(path, value)
        if current is None:
            continue
        for i, trace_id in enumerate(value["traceability_refs"]):
            target = context.traceability_targets.get(trace_id)
            if target and target != current:
                context.report.error(
                    f"{path}.traceability_refs[{i}]",
                    f"traceability {trace_id} targets {target[0]} {target[1]} instead of {current[0]} {current[1]}",
                    "Local backlinks must point to traceability items for the current node",
                )
```

Extend `_check_support_refs` to warn for unused evidence after all semantic checks. Add this function and call it from `run_semantic_checks` after traceability:

```python
def check_unreferenced_evidence(document, context):
    referenced = set()
    for _path, value in walk(document):
        if isinstance(value, dict):
            referenced.update(value.get("evidence_refs", []))
    for i, evidence in enumerate(document["evidence"]):
        if evidence["id"] not in referenced:
            context.report.warn("$.evidence[%d].id" % i, f"unreferenced evidence {evidence['id']}", "Remove it from the DSL or cite it from an evidence_refs field")
```

- [ ] **Step 5: Run extra table and traceability tests to verify GREEN**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_validate_dsl_semantics.ExtraTableAndTraceabilityTests -v
```

Expected GREEN output:

```text
Ran 7 tests
OK
```

- [ ] **Step 6: Commit**

```bash
git add scripts/validate_dsl.py tests/test_validate_dsl_semantics.py
git commit -m "feat: validate extra tables and traceability"
```

---

### Task 7: Source Snippet Validation

**Files:**
- Modify: `tests/test_validate_dsl_semantics.py`
- Modify: `scripts/validate_dsl.py`

- [ ] **Step 1: Write failing source snippet tests**

Append to `tests/test_validate_dsl_semantics.py`:

```python
class SourceSnippetValidationTests(unittest.TestCase):
    def test_line_range_must_be_valid(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            document["source_snippets"] = [{
                "id": "SNIP-BAD-RANGE",
                "path": "scripts/validate_dsl.py",
                "line_start": 10,
                "line_end": 5,
                "language": "python",
                "purpose": "错误范围",
                "content": "line\n",
                "confidence": "observed",
            }]
            document["module_design"]["modules"][0]["source_snippet_refs"] = ["SNIP-BAD-RANGE"]
            path = write_json(tmpdir, "snippet-range.dsl.json", document)
            completed = run_validator(path)
        self.assertEqual(1, completed.returncode)
        self.assertIn("$.source_snippets[0].line_end", completed.stderr)
        self.assertIn("must be greater than or equal to line_start", completed.stderr)

    def test_unreferenced_source_snippet_fails(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            document["source_snippets"] = [{
                "id": "SNIP-UNUSED",
                "path": "scripts/validate_dsl.py",
                "line_start": 1,
                "line_end": 1,
                "language": "python",
                "purpose": "未引用",
                "content": "print('x')\n",
                "confidence": "observed",
            }]
            path = write_json(tmpdir, "snippet-unused.dsl.json", document)
            completed = run_validator(path)
        self.assertEqual(1, completed.returncode)
        self.assertIn("$.source_snippets[0].id", completed.stderr)
        self.assertIn("unreferenced source snippet", completed.stderr)

    def test_snippet_longer_than_twenty_warns_and_longer_than_fifty_fails_by_default(self):
        content_25 = "\n".join(f"line {i}" for i in range(25))
        content_55 = "\n".join(f"line {i}" for i in range(55))
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            document["source_snippets"] = [{
                "id": "SNIP-LONG-WARN",
                "path": "a.py",
                "line_start": 1,
                "line_end": 25,
                "language": "python",
                "purpose": "稍长片段",
                "content": content_25,
                "confidence": "observed",
            }]
            document["module_design"]["modules"][0]["source_snippet_refs"] = ["SNIP-LONG-WARN"]
            path = write_json(tmpdir, "snippet-25.dsl.json", document)
            completed = run_validator(path)
        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertIn("WARNING", completed.stdout)
        self.assertIn("longer than 20 lines", completed.stdout)

        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            document["source_snippets"] = [{
                "id": "SNIP-LONG-FAIL",
                "path": "a.py",
                "line_start": 1,
                "line_end": 55,
                "language": "python",
                "purpose": "过长片段",
                "content": content_55,
                "confidence": "observed",
            }]
            document["module_design"]["modules"][0]["source_snippet_refs"] = ["SNIP-LONG-FAIL"]
            path = write_json(tmpdir, "snippet-55.dsl.json", document)
            completed = run_validator(path)
        self.assertEqual(1, completed.returncode)
        self.assertIn("longer than 50 lines", completed.stderr)

        completed = run_validator(path, "--allow-long-snippets")
        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertIn("longer than 50 lines", completed.stdout)

    def test_secret_and_personal_data_patterns_fail(self):
        cases = [
            "AWS_SECRET_ACCESS_KEY=AKIAIOSFODNN7EXAMPLE",
            "password = \"super-secret\"",
            "-----BEGIN PRIVATE KEY-----",
            "email: person@example.com",
            "phone: 13800138000",
        ]
        for content in cases:
            with tempfile.TemporaryDirectory() as tmpdir:
                document = valid_document()
                document["source_snippets"] = [{
                    "id": "SNIP-SECRET",
                    "path": "secret.txt",
                    "line_start": 1,
                    "line_end": 1,
                    "language": "text",
                    "purpose": "敏感内容",
                    "content": content,
                    "confidence": "observed",
                }]
                document["module_design"]["modules"][0]["source_snippet_refs"] = ["SNIP-SECRET"]
                path = write_json(tmpdir, "snippet-secret.dsl.json", document)
                completed = run_validator(path)
            with self.subTest(content=content):
                self.assertEqual(1, completed.returncode)
                self.assertIn("$.source_snippets[0].content", completed.stderr)
                self.assertIn("high-risk secret or personal data pattern", completed.stderr)
```

- [ ] **Step 2: Run source snippet tests to verify RED**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_validate_dsl_semantics.SourceSnippetValidationTests -v
```

Expected RED output:

```text
FAIL: test_line_range_must_be_valid
AssertionError: 1 != 0
FAIL: test_unreferenced_source_snippet_fails
AssertionError: 1 != 0
```

- [ ] **Step 3: Implement source snippet validation**

Replace `check_source_snippets` and add patterns:

```python
HIGH_RISK_SNIPPET_PATTERNS = [
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"(?i)(password|passwd|secret|token|api[_-]?key)\s*[:=]\s*['\"]?[^'\"\s]+"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |)?PRIVATE KEY-----"),
    re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    re.compile(r"\b1[3-9]\d{9}\b"),
]


def content_line_count(content):
    if content == "":
        return 0
    return len(content.splitlines())


def check_source_snippets(document, context, *, allow_long_snippets):
    referenced = set()
    for _path, value in walk(document):
        if isinstance(value, dict):
            referenced.update(value.get("source_snippet_refs", []))

    for i, snippet in enumerate(document["source_snippets"]):
        base = f"$.source_snippets[{i}]"
        if snippet["line_end"] < snippet["line_start"]:
            context.report.error(f"{base}.line_end", "must be greater than or equal to line_start", "Use a positive inclusive line range")
        line_count = content_line_count(snippet["content"])
        if line_count > 50:
            if allow_long_snippets:
                context.report.warn(f"{base}.content", "source snippet is longer than 50 lines", "Keep only necessary evidence when possible")
            else:
                context.report.error(f"{base}.content", "source snippet is longer than 50 lines", "Pass --allow-long-snippets only when the long evidence is intentional")
        elif line_count > 20:
            context.report.warn(f"{base}.content", "source snippet is longer than 20 lines", "Shorter snippets are easier to review")
        if snippet["id"] not in referenced:
            context.report.error(f"{base}.id", f"unreferenced source snippet {snippet['id']}", "Reference it from source_snippet_refs or remove it from the DSL")
        for pattern in HIGH_RISK_SNIPPET_PATTERNS:
            if pattern.search(snippet["content"]):
                context.report.error(f"{base}.content", "contains high-risk secret or personal data pattern", "Redact the snippet before validation")
                break
```

- [ ] **Step 4: Run source snippet tests to verify GREEN**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_validate_dsl_semantics.SourceSnippetValidationTests -v
```

Expected GREEN output:

```text
Ran 4 tests
OK
```

- [ ] **Step 5: Commit**

```bash
git add scripts/validate_dsl.py tests/test_validate_dsl_semantics.py
git commit -m "feat: validate dsl source snippets"
```

---

### Task 8: Markdown Safety, Structure Boundary, And Low-Confidence Collection

**Files:**
- Modify: `tests/test_validate_dsl_semantics.py`
- Modify: `scripts/validate_dsl.py`

- [ ] **Step 1: Write failing Markdown safety and low-confidence tests**

Append to `tests/test_validate_dsl_semantics.py`:

```python
class MarkdownSafetyAndLowConfidenceTests(unittest.TestCase):
    def test_chapter_nine_rejects_headings_tables_fences_html_and_graphs(self):
        cases = [
            "# 标题",
            "| A | B |\n|---|---|",
            "```mermaid\nflowchart TD\n```",
            "```python\nprint('x')",
            "<div>raw</div>",
            "<p>raw</p>",
            "<!-- raw comment -->",
            "graph TD\n  A-->B",
        ]
        for content in cases:
            with tempfile.TemporaryDirectory() as tmpdir:
                document = valid_document()
                document["structure_issues_and_suggestions"] = content
                path = write_json(tmpdir, "chapter9.dsl.json", document)
                completed = run_validator(path)
            with self.subTest(content=content):
                self.assertEqual(1, completed.returncode)
                self.assertIn("$.structure_issues_and_suggestions", completed.stderr)
                self.assertIn("unsafe Markdown structure", completed.stderr)

    def test_design_text_rejects_prototypes_and_definition_like_lines_outside_snippets(self):
        cases = [
            ("system_overview", "summary", "int main(void);"),
            ("system_overview", "summary", "def build_plan():"),
            ("system_overview", "summary", "class Renderer:"),
            ("system_overview", "summary", "typedef struct Config Config;"),
        ]
        for section, field, value in cases:
            with tempfile.TemporaryDirectory() as tmpdir:
                document = valid_document()
                document[section][field] = value
                path = write_json(tmpdir, "prototype.dsl.json", document)
                completed = run_validator(path)
            with self.subTest(value=value):
                self.assertEqual(1, completed.returncode)
                self.assertIn(f"$.{section}.{field}", completed.stderr)
                self.assertIn("prototype/detail-design content", completed.stderr)

    def test_plain_text_fields_reject_markdown_structure_outside_chapter_nine(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            document["system_overview"]["summary"] = "# 注入标题"
            path = write_json(tmpdir, "plain-markdown.dsl.json", document)
            completed = run_validator(path)
        self.assertEqual(1, completed.returncode)
        self.assertIn("$.system_overview.summary", completed.stderr)
        self.assertIn("unsafe Markdown structure", completed.stderr)

    def test_plain_text_fields_reject_large_code_like_blocks(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            document["system_overview"]["summary"] = "\n".join([
                "if ready:",
                "    validate()",
                "    render()",
                "    report()",
                "else:",
                "    raise RuntimeError('not ready')",
            ])
            path = write_json(tmpdir, "plain-code-block.dsl.json", document)
            completed = run_validator(path)
        self.assertEqual(1, completed.returncode)
        self.assertIn("$.system_overview.summary", completed.stderr)
        self.assertIn("large code-like block", completed.stderr)

    def test_mermaid_source_rejects_fenced_markdown(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            document["architecture_views"]["module_relationship_diagram"]["source"] = "```mermaid\nflowchart TD\n  A --> B\n```"
            path = write_json(tmpdir, "fenced-mermaid.dsl.json", document)
            completed = run_validator(path)
        self.assertEqual(1, completed.returncode)
        self.assertIn("$.architecture_views.module_relationship_diagram.source", completed.stderr)
        self.assertIn("must not include Markdown fences", completed.stderr)

    def test_low_confidence_whitelist_warns_and_suggests_chapter_nine_coverage(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            document["architecture_views"]["module_intro"]["rows"][0]["confidence"] = "unknown"
            document["module_design"]["modules"][0]["external_capability_details"]["provided_capabilities"]["rows"][0]["confidence"] = "unknown"
            document["evidence"] = [{
                "id": "EV-UNKNOWN",
                "kind": "note",
                "title": "未知证据",
                "location": "note",
                "description": "support data 不应进入低置信度集合。",
                "confidence": "unknown",
            }]
            path = write_json(tmpdir, "low-confidence.dsl.json", document)
            completed = run_validator(path)
        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertIn("WARNING", completed.stdout)
        self.assertIn("low-confidence item", completed.stdout)
        self.assertIn("$.architecture_views.module_intro.rows[0]", completed.stdout)
        self.assertIn("$.module_design.modules[0].external_capability_details.provided_capabilities.rows[0]", completed.stdout)
        self.assertNotIn("$.evidence[0]", completed.stdout)
        self.assertIn("Summarize in chapter 9", completed.stdout)
```

- [ ] **Step 2: Run Markdown safety tests to verify RED**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_validate_dsl_semantics.MarkdownSafetyAndLowConfidenceTests -v
```

Expected RED output:

```text
FAIL: test_chapter_nine_rejects_headings_tables_fences_html_and_graphs
AssertionError: 1 != 0
FAIL: test_low_confidence_whitelist_warns_and_suggests_chapter_nine_coverage
AssertionError: 'low-confidence item' not found
```

- [ ] **Step 3: Implement Markdown safety and prototype/detail-design lint**

Replace `check_markdown_safety` and add helper functions:

```python
MARKDOWN_UNSAFE_PATTERNS = [
    re.compile(r"(?m)^\s{0,3}#{1,6}\s+"),
    re.compile(r"(?m)^\s*\|.+\|\s*$"),
    re.compile(r"```"),
    re.compile(r"(?s)<!--.*?-->"),
    re.compile(r"(?is)</?[A-Za-z][A-Za-z0-9:-]*(?:\s+[^<>]*)?>"),
    re.compile(r"(?m)^\s*(?:graph|flowchart|sequenceDiagram|classDiagram|stateDiagram-v2)\b"),
]

PROTOTYPE_PATTERNS = [
    re.compile(r"(?m)^\s*[A-Za-z_][\w\s\*]+?\s+[A-Za-z_]\w*\s*\([^;{}]*\)\s*;?\s*$"),
    re.compile(r"(?m)^\s*def\s+[A-Za-z_]\w*\s*\("),
    re.compile(r"(?m)^\s*class\s+[A-Za-z_]\w*(?:\(|:|\s*$)"),
    re.compile(r"(?m)^\s*typedef\s+(?:struct|enum)\b"),
    re.compile(r"(?m)^\s*enum\s*\{"),
    re.compile(r"(?m)^\s*class\s*\{"),
]

TEXT_LINT_EXEMPT_FIELD_NAMES = {"source", "content"}

CODE_LIKE_LINE_RE = re.compile(
    r"^\s*(?:if |else:|elif |for |while |try:|except |return\b|raise\b|[A-Za-z_]\w*\(.*\)|[A-Za-z_]\w*\s*=|[{};])"
)


def has_large_code_like_block(value):
    run_length = 0
    for line in value.splitlines():
        if CODE_LIKE_LINE_RE.search(line):
            run_length += 1
            if run_length >= 5:
                return True
        elif line.strip():
            run_length = 0
    return False


def check_chapter_9(document, context):
    value = document["structure_issues_and_suggestions"]
    for pattern in MARKDOWN_UNSAFE_PATTERNS:
        if pattern.search(value):
            context.report.error(
                "$.structure_issues_and_suggestions",
                "unsafe Markdown structure is not allowed in chapter 9",
                "Use paragraphs, simple lists, emphasis, and inline code only",
            )
            return


def is_mermaid_source_path(path):
    return path.endswith(".source") and any(marker in path for marker in ["diagram", "extra_diagrams"])


def check_markdown_safety(document, context):
    for path, value in walk(document):
        if not isinstance(value, str):
            continue
        field_name = path.rsplit(".", 1)[-1]
        if is_mermaid_source_path(path) and "```" in value:
            context.report.error(path, "Mermaid source must not include Markdown fences", "Store raw Mermaid source only")
            continue
        if field_name in TEXT_LINT_EXEMPT_FIELD_NAMES or path.startswith("$.source_snippets["):
            continue
        if path == "$.structure_issues_and_suggestions":
            continue
        for pattern in MARKDOWN_UNSAFE_PATTERNS:
            if pattern.search(value):
                context.report.error(path, "unsafe Markdown structure is not allowed in plain text fields", "Keep document structure controlled by the renderer")
                break
        for pattern in PROTOTYPE_PATTERNS:
            if pattern.search(value):
                context.report.error(path, "prototype/detail-design content is outside this DSL field", "Move code evidence into source_snippets or summarize structurally")
                break
        if has_large_code_like_block(value):
            context.report.error(path, "large code-like block is outside this DSL field", "Move code evidence into source_snippets or summarize structurally")
```

- [ ] **Step 4: Implement low-confidence whitelist collection**

Replace `collect_low_confidence`:

```python
LOW_CONFIDENCE_COLLECTIONS = [
    ("$.architecture_views.module_intro.rows", lambda doc: doc["architecture_views"]["module_intro"]["rows"]),
    ("$.module_design.modules", lambda doc: doc["module_design"]["modules"]),
    (
        "$.module_design.modules[{module_index}].external_capability_details.provided_capabilities.rows",
        lambda doc: [
            (module_index, row_index, row)
            for module_index, module in enumerate(doc["module_design"]["modules"])
            for row_index, row in enumerate(module["external_capability_details"]["provided_capabilities"]["rows"])
        ],
    ),
    ("$.runtime_view.runtime_units.rows", lambda doc: doc["runtime_view"]["runtime_units"]["rows"]),
    ("$.configuration_data_dependencies.configuration_items.rows", lambda doc: doc["configuration_data_dependencies"]["configuration_items"]["rows"]),
    ("$.configuration_data_dependencies.structural_data_artifacts.rows", lambda doc: doc["configuration_data_dependencies"]["structural_data_artifacts"]["rows"]),
    ("$.configuration_data_dependencies.dependencies.rows", lambda doc: doc["configuration_data_dependencies"]["dependencies"]["rows"]),
    ("$.cross_module_collaboration.collaboration_scenarios.rows", lambda doc: doc["cross_module_collaboration"]["collaboration_scenarios"]["rows"]),
    ("$.key_flows.flows", lambda doc: doc["key_flows"]["flows"]),
]


def collect_low_confidence(document, context):
    for base_path, getter in LOW_CONFIDENCE_COLLECTIONS:
        values = getter(document)
        for i, item in enumerate(values):
            if isinstance(item, tuple):
                module_index, row_index, row = item
                path = base_path.format(module_index=module_index) + f"[{row_index}]"
                candidate = row
            else:
                path = f"{base_path}[{i}]"
                candidate = item
            if candidate.get("confidence") == "unknown":
                context.report.warn(path, "low-confidence item", "Summarize in chapter 9 when useful")
    for f_i, flow in enumerate(document["key_flows"]["flows"]):
        for s_i, step in enumerate(flow["steps"]):
            if step.get("confidence") == "unknown":
                context.report.warn(f"$.key_flows.flows[{f_i}].steps[{s_i}]", "low-confidence item", "Summarize in chapter 9 when useful")
        for b_i, branch in enumerate(flow["branches_or_exceptions"]):
            if branch.get("confidence") == "unknown":
                context.report.warn(f"$.key_flows.flows[{f_i}].branches_or_exceptions[{b_i}]", "low-confidence item", "Summarize in chapter 9 when useful")
```

- [ ] **Step 5: Run Markdown safety tests to verify GREEN**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_validate_dsl_semantics.MarkdownSafetyAndLowConfidenceTests -v
```

Expected GREEN output:

```text
Ran 6 tests
OK
```

- [ ] **Step 6: Commit**

```bash
git add scripts/validate_dsl.py tests/test_validate_dsl_semantics.py
git commit -m "feat: validate markdown safety and low confidence items"
```

---

### Task 9: Examples, Acceptance Criteria, And Full Regression

**Files:**
- Modify: `tests/test_validate_dsl_semantics.py`
- Modify: `scripts/validate_dsl.py`
- Verify only: `examples/minimal-from-code.dsl.json`
- Verify only: `examples/minimal-from-requirements.dsl.json`
- Verify only: `requirements.txt`

- [ ] **Step 1: Write final acceptance tests**

Append to `tests/test_validate_dsl_semantics.py`:

```python
class AcceptanceTests(unittest.TestCase):
    def test_examples_pass_semantic_cli_validation(self):
        for relative_path in [
            "examples/minimal-from-code.dsl.json",
            "examples/minimal-from-requirements.dsl.json",
        ]:
            completed = run_validator(ROOT / relative_path)
            with self.subTest(path=relative_path):
                self.assertEqual(0, completed.returncode, completed.stderr)
                self.assertIn("Validation succeeded", completed.stdout)

    def test_semantic_validation_accumulates_multiple_errors_after_schema_success(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            document["document"]["output_file"] = "design.md"
            document["runtime_view"]["runtime_flow_diagram"]["source"] = ""
            document["key_flows"]["flows"][0]["diagram"]["source"] = ""
            path = write_json(tmpdir, "multi-error.dsl.json", document)
            completed = run_validator(path)
        self.assertEqual(1, completed.returncode)
        self.assertGreaterEqual(completed.stderr.count("ERROR:"), 3)
        self.assertIn("$.document.output_file", completed.stderr)
        self.assertIn("$.runtime_view.runtime_flow_diagram.source", completed.stderr)
        self.assertIn("$.key_flows.flows[0].diagram.source", completed.stderr)

    def test_unsafe_output_file_path_stops_at_schema_validation(self):
        for output_file in [
            "nested/create-structure-md_STRUCTURE_DESIGN.md",
            "nested\\create-structure-md_STRUCTURE_DESIGN.md",
            "../create-structure-md_STRUCTURE_DESIGN.md",
            "bad\u0001name.md",
        ]:
            with tempfile.TemporaryDirectory() as tmpdir:
                document = valid_document()
                document["document"]["output_file"] = output_file
                path = write_json(tmpdir, "unsafe-output.dsl.json", document)
                completed = run_validator(path)
            with self.subTest(output_file=output_file):
                self.assertEqual(2, completed.returncode)
                self.assertIn("$.document.output_file", completed.stderr)
                self.assertIn("schema validation failed", completed.stderr)
                self.assertNotIn("semantic validation failed", completed.stderr)

    def test_no_new_dependencies_are_required(self):
        requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8")
        dependency_lines = [
            line.strip()
            for line in requirements.splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]
        self.assertEqual(["jsonschema"], dependency_lines)
```

- [ ] **Step 2: Run acceptance tests to verify RED or identify fixture drift**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_validate_dsl_semantics.AcceptanceTests -v
```

Expected before final cleanup if any semantic rule is incomplete:

```text
FAIL: test_examples_pass_semantic_cli_validation
AssertionError: 0 != 1
```

If the examples already pass, the expected output is:

```text
Ran 4 tests
OK
```

- [ ] **Step 3: Adjust validator implementation only for incomplete Phase 3 behavior**

If acceptance tests fail because a required Phase 3 rule is missing, update `scripts/validate_dsl.py` only. Do not loosen tests for the existing examples unless the example violates the Phase 3 spec. The implementation must still enforce:

```text
schema validation before semantic validation
fail on semantic errors with exit code 1
warn without blocking with exit code 0
all semantic errors accumulated after schema success
no Mermaid syntax validation
no renderer implementation
no network access
no dependency additions
```

- [ ] **Step 4: Run focused acceptance tests to verify GREEN**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_validate_dsl_semantics.AcceptanceTests -v
```

Expected GREEN output:

```text
Ran 4 tests
OK
```

- [ ] **Step 5: Run the complete test suite**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest discover -s tests -v
```

Expected GREEN output:

```text
OK
```

- [ ] **Step 6: Manually run the public CLI examples**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python scripts/validate_dsl.py examples/minimal-from-code.dsl.json
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python scripts/validate_dsl.py examples/minimal-from-requirements.dsl.json
```

Expected output for each command:

```text
Validation succeeded
```

- [ ] **Step 7: Commit**

```bash
git add scripts/validate_dsl.py tests/test_validate_dsl_semantics.py
git commit -m "feat: complete dsl validator acceptance coverage"
```

---

## Self-Review Checklist

- [ ] CLI contract covered: positional path, missing file, invalid JSON, schema-first stop, semantic exit code 1, success exit code 0, and `--allow-long-snippets`.
- [ ] Error/warning/stop policy covered: invalid JSON and schema stop early; semantic validation accumulates errors; warnings print visibly and do not fail.
- [ ] Document/output validation covered: required document fields, `status` and `source_type` via schema, generic filename failure, concrete documented-object filename acceptance, unsafe filename schema-first stop, spaces warning, generated_at warning.
- [ ] ID/reference validation covered: defining ID fields, prefix uniqueness, duplicate IDs, paired flow IDs, reference existence, path-sensitive unregistered `_id`/`_ids`, and no strict numeric suffix.
- [ ] Chapter-specific non-empty and diagram requiredness covered for chapters 2 through 9, including optional extra diagrams requiring source.
- [ ] Chapter 7 single-module and multi-module collaboration behavior covered, including empty single-module collaboration diagrams and validation of provided single-module rows.
- [ ] Chapter 8 flow index/detail one-to-one matching, participant refs, step order uniqueness, global step IDs, and global branch IDs covered.
- [ ] Extra table column-key matching and row field restriction covered.
- [ ] Traceability target mapping and local backlink conflict validation covered.
- [ ] Source snippet range, line-count warning/fail boundary, `--allow-long-snippets`, reference requirement, and obvious secret/personal-data failures covered.
- [ ] Markdown safety and structure boundary covered: headings, tables, Mermaid fences, unbalanced fences, generic HTML blocks/comments, raw graph definitions, large code-like blocks, and prototype/detail-design lint outside snippets.
- [ ] Low-confidence collection covered with the whitelist and chapter 9 coverage suggestion; support data is intentionally excluded.
- [ ] Acceptance criteria covered: examples pass semantic validation and error messages include JSON paths plus correction hints.
- [ ] Out-of-scope boundaries preserved: no Mermaid syntax validation, no Markdown renderer implementation, no network usage, and no dependency additions.
- [ ] Plan wording scan complete: every task includes concrete test code, exact commands, expected output, and named functions or data structures for implementation.
