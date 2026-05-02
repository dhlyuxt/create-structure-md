# create-structure-md Phase 1 Skill Scaffold Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the installable `create-structure-md` skill skeleton and execution contract without implementing DSL validation, Mermaid validation, or Markdown rendering behavior.

**Architecture:** The repository root is the skill root, so `SKILL.md`, `requirements.txt`, `references/`, `schemas/`, `scripts/`, `examples/`, and `tests/` live directly under the current workspace. Phase 1 uses `unittest` to lock down the scaffold, skill metadata, runtime dependency boundary, CLI stub honesty, and reference signposts. Python scripts expose minimal CLIs that exit with a clear phase-1 message instead of claiming validation or rendering success.

**Tech Stack:** Python 3, standard-library `unittest`, standard-library `argparse`, `jsonschema` as the only runtime dependency.

---

## File Structure

- Create: `SKILL.md`
  - Owns Codex skill metadata, scope boundary, input readiness contract, workflow order, output rules, and reference pointers.
- Create: `requirements.txt`
  - Declares runtime dependencies only; contains `jsonschema`.
- Create: `references/dsl-spec.md`
  - Signpost for DSL purpose, top-level fields, chapter fields, and support data.
- Create: `references/document-structure.md`
  - Signpost for the fixed 9-chapter output and output filename policy.
- Create: `references/mermaid-rules.md`
  - Signpost for supported MVP Mermaid types, strict/static validation distinction, and Mermaid-only boundary.
- Create: `references/review-checklist.md`
  - Signpost for reviewing final output path, fixed chapters, Mermaid validation, and no repo-analysis behavior.
- Create: `schemas/structure-design.schema.json`
  - Minimal parseable JSON Schema scaffold only.
- Create: `scripts/validate_dsl.py`
  - Minimal CLI stub that reports DSL validation is unavailable in Phase 1 and exits non-zero.
- Create: `scripts/validate_mermaid.py`
  - Minimal CLI stub that accepts intended Phase 1 flags, reports Mermaid validation is unavailable in Phase 1, and exits non-zero.
- Create: `scripts/render_markdown.py`
  - Minimal CLI stub that accepts intended Phase 1 flags, reports Markdown rendering is unavailable in Phase 1, and exits non-zero.
- Create: `examples/minimal-from-code.dsl.json`
  - Parseable empty JSON scaffold for later example content.
- Create: `examples/minimal-from-requirements.dsl.json`
  - Parseable empty JSON scaffold for later example content.
- Create: `tests/test_validate_dsl.py`
  - Covers required layout, runtime dependency boundary, parseable JSON scaffolds, and script stub honesty.
- Create: `tests/test_validate_mermaid.py`
  - Covers `SKILL.md` front matter, input readiness contract, workflow order, strict/static rule, output rules, temp directory rules, and no repo-analysis boundary.
- Create: `tests/test_render_markdown.py`
  - Covers reference signpost headings and boundary language.

Implementation constraint from the workspace instructions: do not run deletion commands such as `rm`, `rmdir`, `git clean`, `git reset --hard`, or checkout commands that discard files. If cleanup is needed, provide the command for the user to run.

---

### Task 1: Scaffold Layout And Runtime Dependency Test

**Files:**
- Create: `tests/test_validate_dsl.py`
- Create: `tests/test_validate_mermaid.py`
- Create: `tests/test_render_markdown.py`
- Create: `SKILL.md`
- Create: `requirements.txt`
- Create: `references/dsl-spec.md`
- Create: `references/document-structure.md`
- Create: `references/mermaid-rules.md`
- Create: `references/review-checklist.md`
- Create: `schemas/structure-design.schema.json`
- Create: `scripts/validate_dsl.py`
- Create: `scripts/validate_mermaid.py`
- Create: `scripts/render_markdown.py`
- Create: `examples/minimal-from-code.dsl.json`
- Create: `examples/minimal-from-requirements.dsl.json`

- [ ] **Step 1: Write the failing scaffold test**

Create `tests/test_validate_dsl.py`:

```python
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
```

Create empty test modules so `unittest discover` has the required files:

`tests/test_validate_mermaid.py`

```python
import unittest


if __name__ == "__main__":
    unittest.main()
```

`tests/test_render_markdown.py`

```python
import unittest


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the scaffold test to verify it fails**

Run:

```bash
python -m unittest tests.test_validate_dsl -v
```

Expected: FAIL with missing path assertions such as `Missing file: SKILL.md` or `Missing directory: references`.

- [ ] **Step 3: Create the minimum scaffold files**

Run:

```bash
mkdir -p references schemas scripts examples tests
```

Create `requirements.txt`:

```text
jsonschema
```

Create `SKILL.md`:

```markdown
---
name: create-structure-md
description: Phase 1 scaffold for create-structure-md.
---

# create-structure-md

Phase 1 scaffold.
```

Create `schemas/structure-design.schema.json`:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "create-structure-md Phase 1 Scaffold Schema",
  "type": "object"
}
```

Create `examples/minimal-from-code.dsl.json`:

```json
{}
```

Create `examples/minimal-from-requirements.dsl.json`:

```json
{}
```

Create these files as empty scaffold files; later tasks replace them with tested content:

```text
references/dsl-spec.md
references/document-structure.md
references/mermaid-rules.md
references/review-checklist.md
scripts/validate_dsl.py
scripts/validate_mermaid.py
scripts/render_markdown.py
```

- [ ] **Step 4: Run the scaffold test to verify it passes**

Run:

```bash
python -m unittest tests.test_validate_dsl -v
```

Expected: PASS. The output should report `OK`.

- [ ] **Step 5: Commit**

Run:

```bash
git add SKILL.md requirements.txt references schemas scripts examples tests
git commit -m "test: add create-structure-md scaffold layout"
```

Expected: commit succeeds with the scaffold files staged.

---

### Task 2: SKILL.md Contract

**Files:**
- Modify: `tests/test_validate_mermaid.py`
- Modify: `SKILL.md`

- [ ] **Step 1: Write the failing SKILL.md contract test**

Replace `tests/test_validate_mermaid.py` with:

```python
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "SKILL.md"

EXPECTED_DESCRIPTION = (
    "Use when the user asks Codex to generate a single module-specific software "
    "structure design document, such as <documented-object-name>_STRUCTURE_DESIGN.md, "
    "from already-prepared structured design content using the create-structure-md "
    "DSL and Mermaid diagrams. Do not use for repo analysis, requirements inference, "
    "multi-document generation, Word/PDF output, or image export."
)

REQUIRED_INPUTS = [
    "module list and stable module IDs",
    "module responsibilities",
    "module relationships",
    "module-level external capabilities or interface requirements",
    "module internal structure information",
    "runtime units and runtime flow",
    "configuration, structural data/artifact, and dependency information when applicable",
    "cross-module collaboration scenarios when more than one module is identified",
    "key flows and one diagram concept per key flow",
    "confidence values and support-data references where the schema requires or allows them",
    "evidence references or source snippets when available and safe to disclose",
]

WORKFLOW_ORDER = [
    "Create a temporary work directory.",
    "Write one complete DSL JSON file",
    "python scripts/validate_dsl.py structure.dsl.json",
    "python scripts/validate_mermaid.py --from-dsl structure.dsl.json --strict",
    "python scripts/render_markdown.py structure.dsl.json --output-dir",
    "python scripts/validate_mermaid.py --from-markdown <output-file> --static",
    "references/review-checklist.md",
    "Report the output path",
]


class SkillMetadataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = SKILL.read_text(encoding="utf-8")
        cls.front_matter = cls.text.split("---", 2)[1]

    def test_yaml_front_matter_matches_contract(self):
        self.assertTrue(self.text.startswith("---\n"))
        self.assertIn("name: create-structure-md", self.front_matter)
        self.assertIn(f"description: {EXPECTED_DESCRIPTION}", self.front_matter)

    def test_description_contains_required_trigger_terms(self):
        for term in [
            "software structure design document",
            "STRUCTURE_DESIGN.md",
            "DSL",
            "Mermaid",
        ]:
            with self.subTest(term=term):
                self.assertIn(term, self.front_matter)

    def test_description_excludes_out_of_scope_work(self):
        for term in [
            "repo analysis",
            "requirements inference",
            "multi-document generation",
            "Word/PDF output",
            "image export",
        ]:
            with self.subTest(term=term):
                self.assertIn(term, self.front_matter)


class SkillBodyContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = SKILL.read_text(encoding="utf-8")

    def test_input_readiness_contract_lists_required_inputs(self):
        for phrase in REQUIRED_INPUTS:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.text)
        self.assertIn("If any required input is missing", self.text)
        self.assertIn("outside this skill", self.text)

    def test_workflow_appears_in_required_order(self):
        positions = []
        for phrase in WORKFLOW_ORDER:
            with self.subTest(phrase=phrase):
                positions.append(self.text.index(phrase))
        self.assertEqual(sorted(positions), positions)

    def test_mermaid_strict_and_static_acceptance_rule_is_visible(self):
        self.assertIn("Strict Mermaid validation is the default", self.text)
        self.assertIn("Static-only Mermaid validation is allowed only when strict tooling is unavailable", self.text)
        self.assertIn("the user explicitly accepts that limitation for the current run", self.text)

    def test_output_and_temporary_directory_rules_are_visible(self):
        for phrase in [
            "Final output is one Markdown file named by document.output_file",
            "target repository root",
            "current working directory",
            "<documented-object-name>_STRUCTURE_DESIGN.md",
            "Generic-only filenames are forbidden",
            "STRUCTURE_DESIGN.md",
            "structure_design.md",
            "design.md",
            "软件结构设计说明书.md",
            "must end with .md",
            "must not contain path separators",
            "must not contain ..",
            "must not contain control characters",
            "Spaces in the output filename should already be normalized to _",
            ".codex-tmp/create-structure-md-<run-id>/",
            "/tmp/create-structure-md-<run-id>",
            "Temporary files in the skill working directory are not automatically deleted",
            "give the cleanup command to the user instead of deleting files",
            "Codex must not edit .gitignore automatically unless the user asks it to",
        ]:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.text)

    def test_body_keeps_skill_out_of_repository_analysis(self):
        self.assertIn("This skill does not analyze repositories", self.text)
        self.assertIn("Do not run repository analysis tools as part of this skill", self.text)
        self.assertIn("Create one module- or system-specific Markdown file", self.text)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the SKILL.md contract test to verify it fails**

Run:

```bash
python -m unittest tests.test_validate_mermaid -v
```

Expected: FAIL because `SKILL.md` still contains only the temporary scaffold text.

- [ ] **Step 3: Replace SKILL.md with the Phase 1 contract**

Replace `SKILL.md` with:

```markdown
---
name: create-structure-md
description: Use when the user asks Codex to generate a single module-specific software structure design document, such as <documented-object-name>_STRUCTURE_DESIGN.md, from already-prepared structured design content using the create-structure-md DSL and Mermaid diagrams. Do not use for repo analysis, requirements inference, multi-document generation, Word/PDF output, or image export.
---

# create-structure-md

Create one module- or system-specific Markdown file from already-prepared structured design content. The final file is a software structure design document rendered from the create-structure-md DSL with Mermaid diagrams.

## Boundary

This skill does not analyze repositories, infer requirements, generate multiple documents, produce Word/PDF files, or export images. Codex performs project or requirement understanding before invoking this skill. Do not run repository analysis tools as part of this skill.

## Input Readiness

Before creating DSL JSON, Codex must already have enough information to populate required sections without fabrication:

- module list and stable module IDs
- module responsibilities
- module relationships
- module-level external capabilities or interface requirements
- module internal structure information
- runtime units and runtime flow
- configuration, structural data/artifact, and dependency information when applicable
- cross-module collaboration scenarios when more than one module is identified
- key flows and one diagram concept per key flow
- confidence values and support-data references where the schema requires or allows them
- evidence references or source snippets when available and safe to disclose

If any required input is missing, stop and perform project or requirement understanding outside this skill before creating DSL JSON.

## Workflow

1. Create a temporary work directory.
2. Write one complete DSL JSON file, optionally after smaller staged JSON files.
3. Run `python scripts/validate_dsl.py structure.dsl.json`.
4. Run `python scripts/validate_mermaid.py --from-dsl structure.dsl.json --strict`.
5. Render the document with `python scripts/render_markdown.py structure.dsl.json --output-dir ...`.
6. Run `python scripts/validate_mermaid.py --from-markdown <output-file> --static`.
7. Review the generated document with `references/review-checklist.md`.
8. Report the output path, temporary work directory, assumptions, low-confidence items, and any static-only Mermaid acceptance.

Strict Mermaid validation is the default. Static-only Mermaid validation is allowed only when strict tooling is unavailable and the user explicitly accepts that limitation for the current run.

## Output And Temporary Files

Final output is one Markdown file named by document.output_file. If the user provides an output directory, write document.output_file there. Otherwise write document.output_file to the target repository root, or to the current working directory when no target repository root is known.

The output file must be module- or system-specific, normally <documented-object-name>_STRUCTURE_DESIGN.md. Generic-only filenames are forbidden, including STRUCTURE_DESIGN.md, structure_design.md, design.md, and 软件结构设计说明书.md. The output filename must end with .md, must not contain path separators, must not contain .., and must not contain control characters. Spaces in the output filename should already be normalized to _ before writing document.output_file.

Preferred temporary work directory: <workspace>/.codex-tmp/create-structure-md-<run-id>/. Fallback temporary work directory: /tmp/create-structure-md-<run-id>. Temporary files in the skill working directory are not automatically deleted. If cleanup is needed, give the cleanup command to the user instead of deleting files.

The workspace .gitignore should include .codex-tmp/ unless the user intentionally versions temporary artifacts. Codex must not edit .gitignore automatically unless the user asks it to.

## References

- `references/dsl-spec.md`
- `references/document-structure.md`
- `references/mermaid-rules.md`
- `references/review-checklist.md`
```

- [ ] **Step 4: Run the SKILL.md contract test to verify it passes**

Run:

```bash
python -m unittest tests.test_validate_mermaid -v
```

Expected: PASS. The output should report `OK`.

- [ ] **Step 5: Commit**

Run:

```bash
git add SKILL.md tests/test_validate_mermaid.py
git commit -m "feat: define create-structure-md skill contract"
```

Expected: commit succeeds with `SKILL.md` and the SKILL contract tests staged.

---

### Task 3: Script CLI Stubs

**Files:**
- Modify: `tests/test_validate_dsl.py`
- Modify: `scripts/validate_dsl.py`
- Modify: `scripts/validate_mermaid.py`
- Modify: `scripts/render_markdown.py`

- [ ] **Step 1: Write the failing script stub tests**

Replace `tests/test_validate_dsl.py` with:

```python
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
```

- [ ] **Step 2: Run the script stub tests to verify they fail**

Run:

```bash
python -m unittest tests.test_validate_dsl -v
```

Expected: FAIL because the script files are still empty and return `0` instead of `2`.

- [ ] **Step 3: Implement honest CLI stubs**

Replace `scripts/validate_dsl.py` with:

```python
#!/usr/bin/env python3
import argparse
import sys


MESSAGE = "DSL validation is not implemented in Phase 1 of create-structure-md."


def build_parser():
    parser = argparse.ArgumentParser(
        description="Phase 1 scaffold for create-structure-md DSL validation."
    )
    parser.add_argument("dsl_file", nargs="?", help="Path to structure DSL JSON.")
    return parser


def main(argv=None):
    parser = build_parser()
    parser.parse_args(argv)
    print(MESSAGE, file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
```

Replace `scripts/validate_mermaid.py` with:

```python
#!/usr/bin/env python3
import argparse
import sys


MESSAGE = "Mermaid validation is not implemented in Phase 1 of create-structure-md."


def build_parser():
    parser = argparse.ArgumentParser(
        description="Phase 1 scaffold for create-structure-md Mermaid validation."
    )
    source_group = parser.add_mutually_exclusive_group()
    source_group.add_argument("--from-dsl", dest="dsl_file", help="Path to structure DSL JSON.")
    source_group.add_argument("--from-markdown", dest="markdown_file", help="Path to rendered Markdown.")
    parser.add_argument("--strict", action="store_true", help="Reserved for strict Mermaid validation.")
    parser.add_argument("--static", action="store_true", help="Reserved for static Markdown Mermaid checks.")
    return parser


def main(argv=None):
    parser = build_parser()
    parser.parse_args(argv)
    print(MESSAGE, file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
```

Replace `scripts/render_markdown.py` with:

```python
#!/usr/bin/env python3
import argparse
import sys


MESSAGE = "Markdown rendering is not implemented in Phase 1 of create-structure-md."


def build_parser():
    parser = argparse.ArgumentParser(
        description="Phase 1 scaffold for create-structure-md Markdown rendering."
    )
    parser.add_argument("dsl_file", nargs="?", help="Path to structure DSL JSON.")
    parser.add_argument("--output-dir", default=".", help="Directory for the generated Markdown file.")
    output_group = parser.add_mutually_exclusive_group()
    output_group.add_argument("--overwrite", action="store_true", help="Reserved for replacing existing output.")
    output_group.add_argument("--backup", action="store_true", help="Reserved for backup-before-write behavior.")
    return parser


def main(argv=None):
    parser = build_parser()
    parser.parse_args(argv)
    print(MESSAGE, file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run the script stub tests to verify they pass**

Run:

```bash
python -m unittest tests.test_validate_dsl -v
```

Expected: PASS. The output should report `OK`.

- [ ] **Step 5: Commit**

Run:

```bash
git add scripts/validate_dsl.py scripts/validate_mermaid.py scripts/render_markdown.py tests/test_validate_dsl.py
git commit -m "feat: add phase 1 script stubs"
```

Expected: commit succeeds with script stubs and script tests staged.

---

### Task 4: Reference Signposts

**Files:**
- Modify: `tests/test_render_markdown.py`
- Modify: `references/dsl-spec.md`
- Modify: `references/document-structure.md`
- Modify: `references/mermaid-rules.md`
- Modify: `references/review-checklist.md`

- [ ] **Step 1: Write the failing reference signpost tests**

Replace `tests/test_render_markdown.py` with:

```python
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

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


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the reference tests to verify they fail**

Run:

```bash
python -m unittest tests.test_render_markdown -v
```

Expected: FAIL because the reference files are still empty.

- [ ] **Step 3: Add concise reference signposts**

Replace `references/dsl-spec.md` with:

```markdown
# create-structure-md DSL Spec

## DSL Purpose

The DSL records document-ready structure design content prepared by Codex outside this skill. It does not analyze repositories, infer requirements, or decide what a target system means.

## Top-Level Fields

Later phases define the full schema for `dsl_version`, `document`, fixed chapter objects, `evidence`, `traceability`, `risks`, `assumptions`, and `source_snippets`.

## Chapter Fields

The DSL is organized around the fixed 9-chapter Markdown output: document metadata, system overview, architecture views, module design, runtime view, configuration/data/dependencies, cross-module collaboration, key flows, and structure issues or suggestions.

## Support Data

Support data supplies confidence, evidence, traceability, source snippets, risks, and assumptions for design items. Support data helps render stronger documentation but does not create standalone Markdown chapters.
```

Replace `references/document-structure.md` with:

```markdown
# create-structure-md Document Structure

## Fixed 9-Chapter Markdown Outline

The rendered document uses exactly nine chapters:

1. Document metadata
2. System overview
3. Architecture views
4. Module design
5. Runtime view
6. Configuration, structural data, and dependencies
7. Cross-module collaboration
8. Key flows
9. Structure issues and suggestions

## Output Filename Policy

The output is one module- or system-specific Markdown file named by `document.output_file`, normally `<documented-object-name>_STRUCTURE_DESIGN.md`. Generic-only filenames are forbidden, including `STRUCTURE_DESIGN.md`, `structure_design.md`, `design.md`, and `软件结构设计说明书.md`.
```

Replace `references/mermaid-rules.md` with:

```markdown
# create-structure-md Mermaid Rules

## Supported MVP Diagram Types

The MVP supports Mermaid diagram sources for `flowchart`, `graph`, `sequenceDiagram`, `classDiagram`, and `stateDiagram-v2`.

## Strict And Static Validation

Strict validation checks Mermaid sources before rendering whenever strict tooling is available. Static validation checks rendered Markdown Mermaid code blocks for fence shape and non-empty sources when strict tooling is unavailable and the user explicitly accepts that limitation.

## No Graphviz

Final diagrams are Markdown Mermaid code blocks. Graphviz, DOT files, SVG files, PNG files, and image export are outside this skill.
```

Replace `references/review-checklist.md` with:

```markdown
# create-structure-md Review Checklist

## Final Output Path

- Confirm the result is a single Markdown file.
- Confirm the filename comes from `document.output_file`.
- Confirm the filename is module- or system-specific.

## Fixed Chapters

- Confirm the rendered document uses the fixed 9-chapter structure.
- Confirm optional empty sections use the documented empty-state wording.

## Mermaid Validation

- Confirm DSL Mermaid sources passed strict validation, or record the user's explicit acceptance of static-only validation.
- Confirm rendered Markdown contains Mermaid fences only where Mermaid sources exist.

## No Repo Analysis

- Confirm this skill only rendered prepared design content.
- Confirm repository analysis, requirement inference, and multi-document generation were handled outside this skill.
```

- [ ] **Step 4: Run the reference tests to verify they pass**

Run:

```bash
python -m unittest tests.test_render_markdown -v
```

Expected: PASS. The output should report `OK`.

- [ ] **Step 5: Commit**

Run:

```bash
git add references/dsl-spec.md references/document-structure.md references/mermaid-rules.md references/review-checklist.md tests/test_render_markdown.py
git commit -m "docs: add phase 1 reference signposts"
```

Expected: commit succeeds with reference docs and tests staged.

---

### Task 5: Phase 1 Acceptance Sweep

**Files:**
- Verify: `SKILL.md`
- Verify: `requirements.txt`
- Verify: `references/`
- Verify: `schemas/`
- Verify: `scripts/`
- Verify: `examples/`
- Verify: `tests/`

- [ ] **Step 1: Run the full unittest suite**

Run:

```bash
python -m unittest discover -s tests -v
```

Expected: PASS. The output should report `OK` and include tests from all three required test modules.

- [ ] **Step 2: Confirm no third-party test dependency was introduced**

Run:

```bash
python - <<'PY'
from pathlib import Path
requirements = Path("requirements.txt").read_text(encoding="utf-8")
assert requirements.strip().splitlines() == ["jsonschema"], requirements
assert not Path("requirements-dev.txt").exists()
print("runtime dependency boundary ok")
PY
```

Expected: prints `runtime dependency boundary ok`.

- [ ] **Step 3: Confirm scripts are honest non-success stubs**

Run:

```bash
python scripts/validate_dsl.py structure.dsl.json
```

Expected: exits with code `2` and prints `DSL validation is not implemented in Phase 1 of create-structure-md.`

Run:

```bash
python scripts/validate_mermaid.py --from-dsl structure.dsl.json --strict
```

Expected: exits with code `2` and prints `Mermaid validation is not implemented in Phase 1 of create-structure-md.`

Run:

```bash
python scripts/render_markdown.py structure.dsl.json --output-dir .
```

Expected: exits with code `2` and prints `Markdown rendering is not implemented in Phase 1 of create-structure-md.`

- [ ] **Step 4: Inspect changed files**

Run:

```bash
git status --short
```

Expected after the previous task commits: no output. If files are still modified, inspect them and commit only Phase 1 scaffold changes.

- [ ] **Step 5: Final commit if Step 4 found uncommitted Phase 1 verification adjustments**

Run only if Step 4 shows intentional Phase 1 changes:

```bash
git add SKILL.md requirements.txt references schemas scripts examples tests
git commit -m "chore: finalize phase 1 skill scaffold"
```

Expected: commit succeeds, then `git status --short` shows no output.

---

## Self-Review Checklist

- Spec coverage:
  - Skill directory layout: Task 1.
  - `SKILL.md` YAML front matter and body contract: Task 2.
  - Runtime dependency declaration: Task 1 and Task 5.
  - Standard-library `unittest` harness: Tasks 1 through 4.
  - Script CLI stubs without false success: Task 3 and Task 5.
  - Reference signposts: Task 4.
  - Input readiness contract: Task 2.
  - Strict Mermaid workflow and static-only acceptance rule: Task 2.
  - Output filename and temporary directory rules: Task 2.
  - No repository-analysis behavior: Task 2 and Task 4.
- Boundary check:
  - JSON Schema completeness is not implemented.
  - DSL semantic validation is not implemented.
  - Mermaid validation is not implemented.
  - Markdown rendering is not implemented.
  - End-to-end example correctness is not required in this phase.
- Deletion constraint:
  - The plan contains no deletion step.
  - Cleanup, if ever needed, is reported to the user as a command for user execution.
