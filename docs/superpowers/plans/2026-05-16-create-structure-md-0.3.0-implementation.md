# create-structure-md 0.3.0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the incompatible 0.3.0 create-structure-md mainline from the committed redesign spec, with layered manifest input, fixed eight-chapter rendering, package validation, a Mermaid official tooling gate, repo-understand workflow documentation, examples, and tests.

**Architecture:** Rebuild the active skill from clean root-level files while treating `docs/superpowers/history/V1` and `docs/superpowers/history/V2` as read-only reference material. The validator loads `structure.manifest.json`, resolves only manifest-owned child JSON files, validates each file with 0.3.0 schemas, then runs package-level semantic rules before rendering. The renderer consumes the validated package model and emits one Chinese Markdown document with human-readable labels and hidden internal IDs.

**Tech Stack:** Python 3 standard library, `jsonschema`, `unittest`, Mermaid official parser/CLI tooling such as `mermaid.parse` or `mmdc`, root-level skill files, JSON Schema Draft 2020-12.

---

## Scope Check

This spec spans schema, validation, rendering, documentation, and examples, but those pieces are not independent products. They are one working pipeline: manifest package in, validated Markdown out. Keep one integrated plan and commit after each working slice.

Do not run deletion commands. The workspace instruction is: when cleanup needs deletion, provide the command for the user to run. This plan creates and modifies active 0.3.0 files only; it reads historical files as references and does not remove them.

Use this Python for local verification:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest discover -s tests -v
```

Each task commits its own passing slice. When `git add` or `git commit` needs sandbox escalation, request it explicitly.

---

## File Structure

- Create: `SKILL.md`
  - Active 0.3.0 skill instructions. States the repo-understand handoff, layered manifest package input, fixed eight chapters, and non-goals.
- Create: `requirements.txt`
  - Runtime dependency list. Keep only `jsonschema`.
- Create: `references/dsl-spec.md`
  - Human reference for the 0.3.0 manifest and child JSON contracts.
- Create: `references/document-structure.md`
  - Rendering contract for the fixed Chinese eight-chapter document.
- Create: `references/mermaid-rules.md`
  - Mermaid official tooling gate rules and source-parser prohibition.
- Create: `references/repo-understand-workflow.md`
  - Workflow contract for using repo-understand before building DSL content, especially for Chapter 6 mechanism deep dives.
- Create: `references/review-checklist.md`
  - Final review checklist for validation, rendering, Mermaid, and content boundaries.
- Create: `schemas/v0.3.0/structure.manifest.schema.json`
  - JSON Schema for the pure path-directory manifest.
- Create: `schemas/v0.3.0/chapter.schema.json`
  - JSON Schema definitions for all child chapter JSON shapes and shared named objects.
- Create: `scripts/build_v030_chapter_schema.py`
  - Deterministic builder for the full 0.3.0 chapter schema, kept so schema changes stay reviewable.
- Create: `scripts/v030_types.py`
  - Shared issue/result data classes and JSON path formatting.
- Create: `scripts/v030_paths.py`
  - Lexical POSIX path validation and safe manifest path resolution.
- Create: `scripts/v030_package.py`
  - Manifest loading, direct child file loading, mechanism key inference, package model.
- Create: `scripts/v030_schema.py`
  - Schema validation dispatcher for manifest, single-path chapters, and mechanism files.
- Create: `scripts/v030_semantics.py`
  - Package-level semantic validation: references, ID uniqueness, empty mechanisms, SourceRef repository checks.
- Create: `scripts/v030_mermaid.py`
  - Diagram collection, Mermaid official parser invocation, and narrow project policy checks.
- Create: `scripts/v030_renderer.py`
  - Markdown rendering functions for the eight fixed chapters.
- Create: `scripts/validate_structure.py`
  - CLI for package validation.
- Create: `scripts/render_markdown.py`
  - CLI for validation plus Markdown rendering.
- Create: `tests/helpers_v030.py`
  - Test fixture builder for temporary 0.3.0 DSL packages.
- Create: `tests/__init__.py`
  - Keeps `python -m unittest tests.test_*` imports bound to this repository's test package.
- Create: `tests/test_v030_scaffold.py`
  - Active-file scaffold and version-boundary tests.
- Create: `tests/test_v030_manifest.py`
  - Manifest shape, path, direct-child, and mechanism-key tests.
- Create: `tests/test_v030_chapter_schema.py`
  - Chapter schema tests for each fixed chapter and mechanism files.
- Create: `tests/test_v030_semantics.py`
  - Cross-file reference, ID uniqueness, SourceRef, and empty-mechanism tests.
- Create: `tests/test_v030_mermaid.py`
  - Mermaid official tooling integration contract tests.
- Create: `tests/test_v030_renderer.py`
  - Markdown renderer tests for chapter order, ID hiding, Chapter 6, and output path behavior.
- Create: `tests/test_v030_docs.py`
  - Skill/reference documentation signpost tests.
- Create: `tests/test_v030_e2e.py`
  - Example package validation and rendering tests.
- Create: `examples/minimal-c-library/structure.manifest.json`
  - Accepted package with one mechanism.
- Create: `examples/minimal-c-library/chapters/*.json`
  - Child JSON files for the accepted package.
- Create: `examples/no-mechanisms/structure.manifest.json`
  - Accepted package with empty `key_mechanisms`.
- Create: `examples/no-mechanisms/chapters/*.json`
  - Child JSON files proving empty Chapter 6 behavior and Chapter 8 gap recording.

Historical files under `docs/superpowers/history` are verify-only references. Do not modify them in this implementation plan.

---

### Task 1: Active 0.3.0 Scaffold And Version Boundary

**Files:**
- Create: `requirements.txt`
- Create: `scripts/v030_types.py`
- Create: `scripts/v030_paths.py`
- Create: `scripts/validate_structure.py`
- Create: `tests/__init__.py`
- Create: `tests/test_v030_scaffold.py`

- [ ] **Step 1: Write the failing scaffold tests**

Create `tests/test_v030_scaffold.py`:

```python
import json
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable


class V030ScaffoldTests(unittest.TestCase):
    def test_active_root_files_exist(self):
        expected = [
            "requirements.txt",
            "scripts/v030_types.py",
            "scripts/v030_paths.py",
            "scripts/validate_structure.py",
        ]
        for relative_path in expected:
            with self.subTest(path=relative_path):
                self.assertTrue((ROOT / relative_path).is_file())

    def test_requirements_contains_jsonschema_only(self):
        lines = [
            line.strip()
            for line in (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]
        self.assertEqual(["jsonschema"], lines)

    def test_manifest_payload_must_not_carry_dsl_version(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest = Path(tmpdir) / "structure.manifest.json"
            manifest.write_text(
                json.dumps(
                    {
                        "dsl_version": "0.2.0",
                        "document": "chapters/01-document.json",
                        "repository_overview": "chapters/02-repository-overview.json",
                        "directory_map": "chapters/03-directory-map.json",
                        "module_layers": "chapters/04-module-layers.json",
                        "repository_mainline": "chapters/05-repository-mainline.json",
                        "key_mechanisms": [],
                        "integration_boundaries": "chapters/07-integration-boundaries.json",
                        "risks_validation": "chapters/08-risks-validation.json",
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            completed = subprocess.run(
                [PYTHON, str(ROOT / "scripts/validate_structure.py"), str(manifest)],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(2, completed.returncode)
        self.assertIn("structure.manifest.json must not contain dsl_version", completed.stderr)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the scaffold tests and verify they fail**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_v030_scaffold -v
```

Expected: FAIL because the active 0.3.0 files do not exist.

- [ ] **Step 3: Create the minimal scaffold**

Create `requirements.txt`:

```text
jsonschema
```

Create `tests/__init__.py` as an empty file.

Create `scripts/v030_types.py`:

```python
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ValidationIssue:
    level: str
    code: str
    json_path: str
    message: str

    def format(self) -> str:
        return f"{self.level}: {self.code}: {self.json_path}: {self.message}"


@dataclass
class ValidationResult:
    errors: list[ValidationIssue] = field(default_factory=list)
    warnings: list[ValidationIssue] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    def error(self, code: str, json_path: str, message: str) -> None:
        self.errors.append(ValidationIssue("ERROR", code, json_path, message))

    def warn(self, code: str, json_path: str, message: str) -> None:
        self.warnings.append(ValidationIssue("WARNING", code, json_path, message))

    def extend(self, other: "ValidationResult") -> None:
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)


def json_path(parts) -> str:
    path = "$"
    for part in parts:
        if isinstance(part, int):
            path += f"[{part}]"
        else:
            path += f".{part}"
    return path
```

Create `scripts/v030_paths.py`:

```python
from pathlib import Path


def is_normalized_relative_posix(value: str, *, require_json: bool = False) -> bool:
    if not isinstance(value, str) or not value:
        return False
    if value.startswith("/") or "\\" in value:
        return False
    parts = value.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        return False
    if require_json and not value.endswith(".json"):
        return False
    return True


def resolve_manifest_child(root_dir: Path, manifest_path: str) -> Path:
    if not is_normalized_relative_posix(manifest_path, require_json=True):
        raise ValueError(f"invalid manifest path: {manifest_path}")
    root = root_dir.resolve()
    target = (root_dir / manifest_path).resolve()
    if target != root and root not in target.parents:
        raise ValueError(f"manifest path escapes package root: {manifest_path}")
    return target
```

Create `scripts/validate_structure.py`:

```python
#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate create-structure-md 0.3.0 manifest package.")
    parser.add_argument("manifest", help="Path to structure.manifest.json")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as errors.")
    parser.add_argument("--repo-root", help="Optional repository root for SourceRef existence checks.")
    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    manifest_path = Path(args.manifest)
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"file not found: {manifest_path}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print(f"invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}", file=sys.stderr)
        return 2
    if "dsl_version" in manifest:
        print("ERROR: $.dsl_version: structure.manifest.json must not contain dsl_version", file=sys.stderr)
        return 2
    print("Validation succeeded")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run the scaffold tests and verify they pass**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_v030_scaffold -v
```

Expected: PASS.

- [ ] **Step 5: Commit the scaffold**

Run:

```bash
git add requirements.txt scripts/v030_types.py scripts/v030_paths.py scripts/validate_structure.py tests/__init__.py tests/test_v030_scaffold.py
git commit -m "feat: scaffold create-structure-md 0.3.0"
```

---

### Task 2: Manifest Package Loader

**Files:**
- Create: `schemas/v0.3.0/structure.manifest.schema.json`
- Create: `scripts/v030_package.py`
- Create: `tests/helpers_v030.py`
- Create: `tests/test_v030_manifest.py`
- Modify: `scripts/validate_structure.py`

- [ ] **Step 1: Write the failing manifest tests**

Create `tests/helpers_v030.py`:

```python
import json
from pathlib import Path


FIXED_MANIFEST = {
    "document": "chapters/01-document.json",
    "repository_overview": "chapters/02-repository-overview.json",
    "directory_map": "chapters/03-directory-map.json",
    "module_layers": "chapters/04-module-layers.json",
    "repository_mainline": "chapters/05-repository-mainline.json",
    "key_mechanisms": ["chapters/06-key-mechanisms/persistence.json"],
    "integration_boundaries": "chapters/07-integration-boundaries.json",
    "risks_validation": "chapters/08-risks-validation.json",
}


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def write_manifest_only_package(tmpdir: str, manifest=None) -> Path:
    root = Path(tmpdir)
    manifest_value = dict(FIXED_MANIFEST if manifest is None else manifest)
    write_json(root / "structure.manifest.json", manifest_value)
    for value in manifest_value.values():
        paths = value if isinstance(value, list) else [value]
        for child in paths:
            write_json(root / child, {})
    return root / "structure.manifest.json"
```

Create `tests/test_v030_manifest.py`:

```python
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.helpers_v030 import FIXED_MANIFEST, write_manifest_only_package

from jsonschema import Draft202012Validator

from scripts.v030_package import infer_mechanism_key, load_manifest_package, manifest_shape_errors


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable


class V030ManifestTests(unittest.TestCase):
    def test_loads_fixed_manifest_and_infers_mechanism_keys(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = write_manifest_only_package(tmpdir)
            package = load_manifest_package(manifest_path)
        self.assertEqual("structure.manifest.json", package.manifest_path.name)
        self.assertEqual(["persistence"], [mechanism.key for mechanism in package.mechanisms])
        self.assertEqual(set(FIXED_MANIFEST.keys()), set(package.manifest.keys()))

    def test_manifest_rejects_extra_metadata_fields(self):
        manifest = dict(FIXED_MANIFEST)
        manifest["title"] = "EasyFlash"
        errors = manifest_shape_errors(manifest)
        self.assertTrue(any("must contain exactly the fixed chapter keys" in issue.message for issue in errors))

    def test_manifest_schema_rejects_wrong_root_type(self):
        schema = json.loads((ROOT / "schemas/v0.3.0/structure.manifest.schema.json").read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        errors = list(Draft202012Validator(schema).iter_errors([]))
        self.assertTrue(errors)

    def test_manifest_cli_reports_wrong_root_type_without_traceback(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = Path(tmpdir) / "structure.manifest.json"
            manifest_path.write_text("[]", encoding="utf-8")
            completed = subprocess.run(
                [PYTHON, str(ROOT / "scripts/validate_structure.py"), str(manifest_path)],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(2, completed.returncode)
        self.assertIn("manifest root must be an object", completed.stderr)
        self.assertNotIn("Traceback", completed.stderr)

    def test_manifest_rejects_aggregate_key_mechanisms_file(self):
        manifest = dict(FIXED_MANIFEST)
        manifest["key_mechanisms"] = ["chapters/06-key-mechanisms.json"]
        errors = manifest_shape_errors(manifest)
        self.assertTrue(any("chapters/06-key-mechanisms.json is forbidden" in issue.message for issue in errors))

    def test_manifest_path_must_be_relative_posix_json(self):
        bad_values = [
            "/chapters/01-document.json",
            "chapters\\\\01-document.json",
            "chapters//01-document.json",
            "chapters/../01-document.json",
            "chapters/01-document.md",
        ]
        for bad_value in bad_values:
            with self.subTest(value=bad_value):
                manifest = dict(FIXED_MANIFEST)
                manifest["document"] = bad_value
                errors = manifest_shape_errors(manifest)
                self.assertTrue(errors)

    def test_manifest_paths_must_be_unique(self):
        manifest = dict(FIXED_MANIFEST)
        manifest["repository_overview"] = manifest["document"]
        errors = manifest_shape_errors(manifest)
        self.assertTrue(any("Manifest paths must be unique" in issue.message for issue in errors))

    def test_mechanism_key_comes_from_file_stem(self):
        self.assertEqual("storage-flow", infer_mechanism_key("chapters/06-key-mechanisms/storage-flow.json"))

    def test_invalid_mechanism_key_is_rejected(self):
        manifest = dict(FIXED_MANIFEST)
        manifest["key_mechanisms"] = ["chapters/06-key-mechanisms/Storage.json"]
        errors = manifest_shape_errors(manifest)
        self.assertTrue(any("invalid mechanism key" in issue.message for issue in errors))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the manifest tests and verify they fail**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_v030_manifest -v
```

Expected: FAIL because `scripts/v030_package.py` and the manifest schema do not exist.

- [ ] **Step 3: Implement the manifest package loader**

Create `schemas/v0.3.0/structure.manifest.schema.json` with:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://create-structure-md.local/schemas/v0.3.0/structure.manifest.schema.json",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "document",
    "repository_overview",
    "directory_map",
    "module_layers",
    "repository_mainline",
    "key_mechanisms",
    "integration_boundaries",
    "risks_validation"
  ],
  "properties": {
    "document": { "$ref": "#/$defs/manifestPath" },
    "repository_overview": { "$ref": "#/$defs/manifestPath" },
    "directory_map": { "$ref": "#/$defs/manifestPath" },
    "module_layers": { "$ref": "#/$defs/manifestPath" },
    "repository_mainline": { "$ref": "#/$defs/manifestPath" },
    "key_mechanisms": {
      "type": "array",
      "items": { "$ref": "#/$defs/manifestPath" }
    },
    "integration_boundaries": { "$ref": "#/$defs/manifestPath" },
    "risks_validation": { "$ref": "#/$defs/manifestPath" }
  },
  "$defs": {
    "manifestPath": {
      "type": "string",
      "minLength": 1,
      "pattern": "^(?!/)(?!.*\\\\\\\\)(?!.*(?:^|/)\\\\.\\\\.?/)(?!.*//)[A-Za-z0-9._/-]+\\\\.json$"
    }
  }
}
```

Create `scripts/v030_package.py`:

```python
import json
import re
from dataclasses import dataclass
from pathlib import Path

from jsonschema import Draft202012Validator

from scripts.v030_paths import is_normalized_relative_posix, resolve_manifest_child
from scripts.v030_types import ValidationIssue


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_SCHEMA_PATH = ROOT / "schemas/v0.3.0/structure.manifest.schema.json"
FIXED_MANIFEST_KEYS = [
    "document",
    "repository_overview",
    "directory_map",
    "module_layers",
    "repository_mainline",
    "key_mechanisms",
    "integration_boundaries",
    "risks_validation",
]
SINGLE_CHAPTER_KEYS = [key for key in FIXED_MANIFEST_KEYS if key != "key_mechanisms"]
MECHANISM_KEY_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
FORBIDDEN_MECHANISM_AGGREGATE = "chapters/06-key-mechanisms.json"


@dataclass(frozen=True)
class MechanismFile:
    key: str
    manifest_path: str
    filesystem_path: Path
    data: dict


@dataclass(frozen=True)
class ManifestPackage:
    manifest_path: Path
    root_dir: Path
    manifest: dict
    chapters: dict[str, dict]
    chapter_files: dict[str, Path]
    mechanisms: list[MechanismFile]

    @property
    def declared_paths(self) -> set[str]:
        paths = set()
        for key in SINGLE_CHAPTER_KEYS:
            paths.add(self.manifest[key])
        paths.update(self.manifest["key_mechanisms"])
        return paths


def infer_mechanism_key(manifest_path: str) -> str:
    return Path(manifest_path).name.removesuffix(".json")


def manifest_schema_errors(manifest) -> list[ValidationIssue]:
    schema = json.loads(MANIFEST_SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    return [
        ValidationIssue("ERROR", "manifest.schema", "$", error.message)
        for error in sorted(validator.iter_errors(manifest), key=lambda item: list(item.path))
    ]


def manifest_shape_errors(manifest) -> list[ValidationIssue]:
    errors: list[ValidationIssue] = []
    if not isinstance(manifest, dict):
        return [ValidationIssue("ERROR", "manifest.root", "$", "manifest root must be an object")]
    errors.extend(manifest_schema_errors(manifest))
    if set(manifest.keys()) != set(FIXED_MANIFEST_KEYS):
        errors.append(ValidationIssue("ERROR", "manifest.fixed_keys", "$", "structure.manifest.json must contain exactly the fixed chapter keys"))
    paths: list[str] = []
    for key in SINGLE_CHAPTER_KEYS:
        value = manifest.get(key)
        if not is_normalized_relative_posix(value, require_json=True):
            errors.append(ValidationIssue("ERROR", "manifest.path", f"$.{key}", "manifest path must be a normalized relative POSIX .json path"))
        else:
            paths.append(value)
    mechanisms = manifest.get("key_mechanisms")
    if not isinstance(mechanisms, list):
        errors.append(ValidationIssue("ERROR", "manifest.key_mechanisms", "$.key_mechanisms", "key_mechanisms must be an array of manifest paths"))
        mechanisms = []
    seen_keys: set[str] = set()
    for index, value in enumerate(mechanisms):
        if value == FORBIDDEN_MECHANISM_AGGREGATE:
            errors.append(ValidationIssue("ERROR", "manifest.no_aggregate_chapter6", f"$.key_mechanisms[{index}]", "chapters/06-key-mechanisms.json is forbidden"))
            continue
        if not is_normalized_relative_posix(value, require_json=True):
            errors.append(ValidationIssue("ERROR", "manifest.path", f"$.key_mechanisms[{index}]", "manifest path must be a normalized relative POSIX .json path"))
            continue
        key = infer_mechanism_key(value)
        if not MECHANISM_KEY_RE.match(key):
            errors.append(ValidationIssue("ERROR", "manifest.mechanism_key", f"$.key_mechanisms[{index}]", f"invalid mechanism key: {key}"))
        if key in seen_keys:
            errors.append(ValidationIssue("ERROR", "manifest.mechanism_key_unique", f"$.key_mechanisms[{index}]", f"duplicate mechanism key: {key}"))
        seen_keys.add(key)
        paths.append(value)
    if len(paths) != len(set(paths)):
        errors.append(ValidationIssue("ERROR", "manifest.path_unique", "$", "Manifest paths must be unique"))
    return errors


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON at {path}:{exc.lineno}:{exc.colno}: {exc.msg}") from exc


def load_manifest_package(manifest_path: Path | str) -> ManifestPackage:
    manifest_path = Path(manifest_path)
    manifest = load_json(manifest_path)
    errors = manifest_shape_errors(manifest)
    if errors:
        raise ValueError(errors[0].format())
    root_dir = manifest_path.parent
    chapters: dict[str, dict] = {}
    chapter_files: dict[str, Path] = {}
    for key in SINGLE_CHAPTER_KEYS:
        child_path = resolve_manifest_child(root_dir, manifest[key])
        chapters[key] = load_json(child_path)
        chapter_files[key] = child_path
    mechanisms: list[MechanismFile] = []
    for value in manifest["key_mechanisms"]:
        child_path = resolve_manifest_child(root_dir, value)
        mechanisms.append(MechanismFile(infer_mechanism_key(value), value, child_path, load_json(child_path)))
    return ManifestPackage(manifest_path, root_dir, manifest, chapters, chapter_files, mechanisms)
```

- [ ] **Step 4: Wire the CLI through the package loader**

Modify `scripts/validate_structure.py` so `main()` imports `load_manifest_package` and prints loader errors:

```python
from scripts.v030_package import load_manifest_package, manifest_shape_errors


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    manifest_path = Path(args.manifest)
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"file not found: {manifest_path}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print(f"invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}", file=sys.stderr)
        return 2
    if "dsl_version" in manifest:
        print("ERROR: $.dsl_version: structure.manifest.json must not contain dsl_version", file=sys.stderr)
        return 2
    errors = manifest_shape_errors(manifest)
    if errors:
        for issue in errors:
            print(issue.format(), file=sys.stderr)
        return 2
    try:
        load_manifest_package(manifest_path)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print("Validation succeeded")
    return 0
```

- [ ] **Step 5: Run scaffold and manifest tests**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_v030_scaffold tests.test_v030_manifest -v
```

Expected: PASS.

- [ ] **Step 6: Commit the manifest loader**

Run:

```bash
git add schemas/v0.3.0/structure.manifest.schema.json scripts/v030_package.py scripts/validate_structure.py tests/helpers_v030.py tests/test_v030_manifest.py
git commit -m "feat: load 0.3.0 manifest packages"
```

---

### Task 3: Chapter JSON Schema Validation

**Files:**
- Create: `schemas/v0.3.0/chapter.schema.json`
- Create: `scripts/build_v030_chapter_schema.py`
- Create: `scripts/v030_schema.py`
- Create: `tests/test_v030_chapter_schema.py`
- Modify: `tests/helpers_v030.py`
- Modify: `scripts/validate_structure.py`

- [ ] **Step 1: Extend fixture helpers with a complete minimal package**

Add these functions to `tests/helpers_v030.py`:

```python
def minimal_document_chapter():
    return {
        "chapter": {"key": "document", "title": "文档说明"},
        "document": {
            "title": "示例仓库结构说明",
            "version": "0.1",
            "status": "draft",
            "language": "zh-CN",
            "generated_at": "2026-05-16T00:00:00+08:00",
            "output_file": "Example_STRUCTURE_DESIGN.md",
        },
        "repository": {
            "name": "example",
            "root_display_path": "example",
            "kind": "c_library",
            "primary_languages": ["C"],
        },
        "scope": {
            "included": [{"area": "library", "description": "核心库代码。"}],
            "excluded": [{"area": "hardware", "reason": "未连接目标硬件。"}],
        },
        "confidence": {
            "level": "medium",
            "summary": "基于静态阅读。",
            "validation_gaps": ["未执行目标板验证。"],
        },
    }


def minimal_repository_overview_chapter():
    return {
        "chapter": {"key": "repository_overview", "title": "仓库概述与阅读路线"},
        "overview": {
            "summary": "这是一个 C 库示例。",
            "problem_domain": "嵌入式持久化。",
            "repository_purpose": "提供可移植的存储能力。",
            "target_readers": ["首次阅读仓库的工程师"],
        },
        "core_capabilities": [
            {
                "name": "持久化读写",
                "description": "封装底层存储访问。",
                "entry_points": [{"path": "src/storage.c", "symbol": "storage_init"}],
                "notes": "入口由应用调用。",
            }
        ],
        "reading_route": {
            "summary": "先读公共头文件，再读核心实现。",
            "steps": [
                {
                    "order": 1,
                    "title": "公共接口",
                    "why_read_this": "先理解调用面。",
                    "recommended_files": [{"path": "include/storage.h", "reason": "声明主要接口。"}],
                    "expected_takeaway": "知道应用如何进入库。",
                }
            ],
        },
        "reader_orientation": {
            "read_first": ["include/storage.h"],
            "read_later": ["src/storage.c"],
            "can_skip_initially": ["docs/"],
        },
    }


def minimal_directory_map_chapter():
    return {
        "chapter": {"key": "directory_map", "title": "目录地图"},
        "summary": "目录按公共接口、核心实现、示例分组。",
        "directory_groups": [
            {
                "name": "公共头文件",
                "role": "public_headers",
                "paths": ["include"],
                "responsibility": "暴露应用集成接口。",
                "read_when": "开始集成前。",
                "notes": "保持小而稳定。",
            }
        ],
        "important_files": [
            {
                "path": "include/storage.h",
                "role": "公共接口",
                "why_it_matters": "定义应用调用面。",
                "related_chapters": ["repository_overview", "module_layers"],
            }
        ],
        "directory_relationships": {"summary": "应用通过公共头文件进入核心实现。"},
        "boundary_notes": [{"area": "demo", "note": "示例代码不是库的一部分。"}],
    }


def minimal_module_layers_chapter():
    return {
        "chapter": {"key": "module_layers", "title": "系统分层与模块职责"},
        "summary": "系统分为接口层和核心层。",
        "layers": [
            {
                "layer_id": "api",
                "name": "接口层",
                "role": "接收应用调用。",
                "responsibilities": ["稳定入口"],
                "paths": ["include"],
                "notes": "不拥有存储细节。",
            },
            {
                "layer_id": "core",
                "name": "核心层",
                "role": "实现持久化流程。",
                "responsibilities": ["调度读写"],
                "paths": ["src"],
                "notes": "依赖平台适配。",
            },
        ],
        "modules": [
            {
                "module_id": "storage_api",
                "name": "存储接口",
                "layer_id": "api",
                "purpose": "提供应用入口。",
                "source_paths": ["include/storage.h"],
                "owns": ["接口契约"],
                "consumes": ["应用请求"],
                "produces": ["核心调用"],
                "does_not_own": ["平台驱动"],
                "collaborates_with": [{"module_ref": "storage_core", "relationship": "调用核心实现。"}],
                "read_when": "理解集成入口时。",
                "notes": "只描述职责，不列函数原型。",
            },
            {
                "module_id": "storage_core",
                "name": "存储核心",
                "layer_id": "core",
                "purpose": "组织持久化读写。",
                "source_paths": ["src/storage.c"],
                "owns": ["读写流程"],
                "consumes": ["接口层调用"],
                "produces": ["平台适配调用"],
                "does_not_own": ["具体硬件"],
                "collaborates_with": [],
                "read_when": "理解主线行为时。",
                "notes": "机制细节放在第六章。",
            },
        ],
        "boundary_notes": [{"topic": "API 细节", "note": "不在本章展开参数和返回值。"}],
    }


def minimal_repository_mainline_chapter():
    return {
        "chapter": {"key": "repository_mainline", "title": "仓库主线"},
        "summary": "主线展示应用初始化到存储就绪的路径。",
        "mainline_overview_diagram": {
            "id": "mainline_overview",
            "title": "初始化主线",
            "diagram_type": "flowchart",
            "description": "应用进入库并完成核心初始化。",
            "source": "flowchart TD\n  app[应用] --> api[存储接口]\n  api --> core[存储核心]",
        },
        "mainlines": [
            {
                "mainline_id": "init",
                "name": "初始化",
                "purpose": "让存储能力可用。",
                "entry": {
                    "kind": "api",
                    "name": "storage_init",
                    "description": "应用初始化入口。",
                    "source_ref": {"path": "include/storage.h", "symbol": "storage_init"},
                },
                "steps": [
                    {
                        "order": 1,
                        "step": "应用调用公共入口。",
                        "module_refs": ["storage_api"],
                        "source_refs": [{"path": "include/storage.h", "symbol": "storage_init"}],
                        "effect": "进入库边界。",
                    },
                    {
                        "order": 2,
                        "step": "核心层准备运行状态。",
                        "module_refs": ["storage_core"],
                        "source_refs": [{"path": "src/storage.c", "symbol": "storage_init"}],
                        "effect": "存储核心可处理请求。",
                    },
                ],
                "result": "初始化完成。",
                "notes": "这是阅读主线，不是调用序列参考。",
            }
        ],
        "cross_mainline_notes": [{"topic": "移植", "note": "平台驱动由第七章说明。"}],
    }


def minimal_mechanism_chapter():
    return {
        "section": {"title": "持久化写入机制"},
        "why_it_matters": "这是理解仓库行为的核心机制。",
        "reader_prerequisites": ["先读仓库主线。"],
        "related_modules": ["storage_core"],
        "source_focus": [{"source_ref": {"path": "src/storage.c", "symbol": "storage_write"}, "reason": "写入流程入口。"}],
        "mechanism_overview": "核心层接收写入请求并交给平台适配完成。",
        "flow": [
            {
                "order": 1,
                "step": "检查写入请求。",
                "source_refs": [{"path": "src/storage.c", "symbol": "storage_write"}],
                "state_or_data": "写入缓冲区。",
                "notes": "这里只讲机制，不列 API 表。",
            }
        ],
        "key_states_or_data": [
            {
                "name": "写入缓冲区",
                "kind": "runtime_value",
                "description": "调用方传入的数据。",
                "source_refs": [{"path": "src/storage.c", "symbol": "storage_write"}],
            }
        ],
        "common_misunderstandings": [{"misunderstanding": "核心层直接访问硬件。", "correction": "硬件访问属于平台适配。"}],
        "validation_gaps": ["未在真实硬件上验证写入时序。"],
        "confidence": "medium",
    }


def minimal_integration_boundaries_chapter():
    return {
        "chapter": {"key": "integration_boundaries", "title": "配置、移植与集成边界"},
        "summary": "集成者需要提供平台驱动。",
        "required_configuration": [
            {
                "name": "存储大小",
                "kind": "macro",
                "location": {"description": "配置头文件", "source_ref": {"path": "include/storage_cfg.h"}},
                "purpose": "定义可用存储空间。",
                "required_when": "启用库时。",
                "notes": "示例值不代表生产配置。",
            }
        ],
        "required_adaptations": [
            {
                "name": "底层写入",
                "kind": "port_function",
                "location": {"description": "平台适配文件", "source_ref": {"path": "port/storage_port.c", "symbol": "storage_port_write"}},
                "responsibility": "把数据写入硬件。",
                "caller_or_consumer": "存储核心。",
                "failure_if_missing": "写入请求无法完成。",
            }
        ],
        "integration_paths": [
            {
                "name": "应用集成",
                "scenario": "应用初始化存储库。",
                "recommended_entry": {"description": "调用公共初始化接口。", "source_ref": {"path": "include/storage.h", "symbol": "storage_init"}},
                "steps": ["配置宏", "实现平台函数", "调用初始化入口"],
                "reference_examples": ["examples/basic"],
                "notes": "示例路径可不存在于最小测试仓库。",
            }
        ],
        "external_dependencies": [{"name": "Flash 驱动", "kind": "hardware", "used_by": "平台适配", "integration_role": "提供擦写能力。", "notes": "由平台工程提供。"}],
        "out_of_scope_responsibilities": [{"topic": "硬件寿命评估", "owner": "application", "reason": "依赖产品场景。"}],
    }


def minimal_risks_validation_chapter():
    return {
        "chapter": {"key": "risks_validation", "title": "风险、假设与验证缺口"},
        "summary": "主要缺口来自静态分析。",
        "risks": [
            {
                "risk_id": "static_only",
                "description": "未执行目标硬件验证。",
                "impact": "时序问题可能遗漏。",
                "mitigation": "在目标板运行集成测试。",
                "related_modules": ["storage_core"],
                "related_mechanisms": ["persistence"],
                "confidence": "medium",
            }
        ],
        "assumptions": [
            {
                "assumption_id": "caller_initializes_once",
                "description": "应用按预期只初始化一次。",
                "rationale": "静态阅读未发现重复初始化保护。",
                "validation_suggestion": "补充重复初始化测试。",
                "confidence": "low",
            }
        ],
        "validation_gaps": [
            {
                "gap_id": "target_board",
                "gap_type": "missing_runtime_validation",
                "description": "未运行目标板测试。",
                "why_it_matters": "硬件行为影响持久化可靠性。",
                "suggested_validation": "在目标板执行写入回读。",
                "related_chapters": ["key_mechanisms"],
                "confidence": "medium",
            }
        ],
        "low_confidence_items": [
            {
                "item_id": "port_behavior",
                "location": {"kind": "chapter", "chapter": "integration_boundaries"},
                "description": "平台适配行为来自接口推断。",
                "reason": "没有目标平台实现。",
                "needed_evidence": "具体平台代码。",
            }
        ],
    }


def write_valid_package(
    tmpdir: str,
    *,
    key_mechanisms=True,
    repository_name="example",
    document_title="示例仓库结构说明",
    output_file="Example_STRUCTURE_DESIGN.md",
) -> Path:
    root = Path(tmpdir)
    manifest = dict(FIXED_MANIFEST)
    if not key_mechanisms:
        manifest["key_mechanisms"] = []
    write_json(root / "structure.manifest.json", manifest)
    document = minimal_document_chapter()
    document["document"]["title"] = document_title
    document["document"]["output_file"] = output_file
    document["repository"]["name"] = repository_name
    document["repository"]["root_display_path"] = repository_name
    write_json(root / manifest["document"], document)
    write_json(root / manifest["repository_overview"], minimal_repository_overview_chapter())
    write_json(root / manifest["directory_map"], minimal_directory_map_chapter())
    write_json(root / manifest["module_layers"], minimal_module_layers_chapter())
    write_json(root / manifest["repository_mainline"], minimal_repository_mainline_chapter())
    if key_mechanisms:
        write_json(root / manifest["key_mechanisms"][0], minimal_mechanism_chapter())
    integration = manifest["integration_boundaries"]
    risks = minimal_risks_validation_chapter()
    if not key_mechanisms:
        risks["risks"][0]["related_mechanisms"] = []
        risks["validation_gaps"].append(
            {
                "gap_id": "no_mechanisms",
                "gap_type": "no_key_mechanisms_selected",
                "description": "本次分析未选择关键机制。",
                "why_it_matters": "第六章为空需要显式说明。",
                "suggested_validation": "重新评估候选机制。",
                "related_chapters": ["key_mechanisms"],
                "confidence": "medium",
            }
        )
    write_json(root / integration, minimal_integration_boundaries_chapter())
    write_json(root / manifest["risks_validation"], risks)
    return root / "structure.manifest.json"
```

- [ ] **Step 2: Write the failing chapter schema tests**

Create `tests/test_v030_chapter_schema.py`:

```python
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.helpers_v030 import write_valid_package

from scripts.v030_package import load_manifest_package
from scripts.v030_schema import schema_validation_result


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable


class V030ChapterSchemaTests(unittest.TestCase):
    def test_complete_minimal_package_passes_schema_validation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            package = load_manifest_package(write_valid_package(tmpdir))
            result = schema_validation_result(package)
        self.assertTrue(result.ok, [issue.format() for issue in result.errors])

    def test_single_path_chapter_key_must_match_manifest_property(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = write_valid_package(tmpdir)
            package = load_manifest_package(manifest_path)
            package.chapters["document"]["chapter"]["key"] = "directory_map"
            result = schema_validation_result(package)
        self.assertFalse(result.ok)
        self.assertTrue(any("chapter.key must match manifest property" in issue.message for issue in result.errors))

    def test_mechanism_file_must_not_have_chapter_header(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = write_valid_package(tmpdir)
            package = load_manifest_package(manifest_path)
            package.mechanisms[0].data["chapter"] = {"key": "key_mechanisms", "title": "关键机制深读"}
            result = schema_validation_result(package)
        self.assertFalse(result.ok)
        self.assertTrue(any("Mechanism JSON files must not contain chapter" in issue.message for issue in result.errors))

    def test_document_language_is_zh_cn_only(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = write_valid_package(tmpdir)
            package = load_manifest_package(manifest_path)
            package.chapters["document"]["document"]["language"] = "en-US"
            result = schema_validation_result(package)
        self.assertFalse(result.ok)
        self.assertTrue(any("zh-CN" in issue.message for issue in result.errors))

    def test_fixed_chapter_title_must_match_contract(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = write_valid_package(tmpdir)
            package = load_manifest_package(manifest_path)
            package.chapters["repository_overview"]["chapter"]["title"] = "仓库简介"
            result = schema_validation_result(package)
        self.assertFalse(result.ok)
        self.assertTrue(any("仓库概述与阅读路线" in issue.message for issue in result.errors))

    def test_extra_fields_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = write_valid_package(tmpdir)
            package = load_manifest_package(manifest_path)
            package.chapters["module_layers"]["modules"][0]["public_interfaces"] = []
            result = schema_validation_result(package)
        self.assertFalse(result.ok)
        self.assertTrue(any("Additional properties are not allowed" in issue.message for issue in result.errors))

    def test_path_segments_must_not_be_dot_or_dotdot(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = write_valid_package(tmpdir)
            package = load_manifest_package(manifest_path)
            package.chapters["directory_map"]["directory_groups"][0]["paths"] = ["src/."]
            result = schema_validation_result(package)
        self.assertFalse(result.ok)

        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = write_valid_package(tmpdir)
            package = load_manifest_package(manifest_path)
            package.chapters["directory_map"]["directory_groups"][0]["paths"] = ["src/.."]
            result = schema_validation_result(package)
        self.assertFalse(result.ok)

    def test_mainline_diagram_type_constraints_are_contextual(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = write_valid_package(tmpdir)
            package = load_manifest_package(manifest_path)
            package.chapters["repository_mainline"]["mainline_overview_diagram"]["diagram_type"] = "sequenceDiagram"
            result = schema_validation_result(package)
        self.assertFalse(result.ok)

    def test_cli_schema_error_does_not_fall_through_to_semantic_traceback(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = write_valid_package(tmpdir)
            module_layers = Path(tmpdir) / "chapters/04-module-layers.json"
            data = json.loads(module_layers.read_text(encoding="utf-8"))
            del data["modules"]
            module_layers.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            completed = subprocess.run(
                [PYTHON, str(ROOT / "scripts/validate_structure.py"), str(manifest_path)],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(2, completed.returncode)
        self.assertIn("modules", completed.stderr)
        self.assertNotIn("Traceback", completed.stderr)

        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = write_valid_package(tmpdir)
            package = load_manifest_package(manifest_path)
            package.chapters["repository_mainline"]["mainlines"][0]["detail_diagram"] = {
                "id": "bad_detail",
                "title": "状态细节",
                "diagram_type": "stateDiagram-v2",
                "description": "不允许的主线细节图类型。",
                "source": "stateDiagram-v2\n  [*] --> Ready",
            }
            result = schema_validation_result(package)
        self.assertFalse(result.ok)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run the chapter schema tests and verify they fail**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_v030_chapter_schema -v
```

Expected: FAIL because `scripts/v030_schema.py` and `schemas/v0.3.0/chapter.schema.json` do not exist.

- [ ] **Step 4: Implement schema validation**

Create `scripts/v030_schema.py`:

```python
import json
from pathlib import Path

from jsonschema import Draft202012Validator

from scripts.v030_package import SINGLE_CHAPTER_KEYS, ManifestPackage
from scripts.v030_types import ValidationResult, json_path


ROOT = Path(__file__).resolve().parents[1]
CHAPTER_SCHEMA_PATH = ROOT / "schemas/v0.3.0/chapter.schema.json"


def load_chapter_schema() -> dict:
    return json.loads(CHAPTER_SCHEMA_PATH.read_text(encoding="utf-8"))


def validator_for(def_name: str) -> Draft202012Validator:
    schema = load_chapter_schema()
    selected = {
        "$schema": schema["$schema"],
        "$defs": schema["$defs"],
        "$ref": f"#/$defs/{def_name}",
    }
    Draft202012Validator.check_schema(selected)
    return Draft202012Validator(selected)


CHAPTER_DEF_BY_KEY = {
    "document": "DocumentChapter",
    "repository_overview": "RepositoryOverviewChapter",
    "directory_map": "DirectoryMapChapter",
    "module_layers": "ModuleLayersChapter",
    "repository_mainline": "RepositoryMainlineChapter",
    "integration_boundaries": "IntegrationBoundariesChapter",
    "risks_validation": "RisksValidationChapter",
}


def append_schema_errors(result: ValidationResult, def_name: str, value, prefix: str) -> None:
    errors = sorted(validator_for(def_name).iter_errors(value), key=lambda error: list(error.path))
    for error in errors:
        result.error("schema", f"{prefix}{json_path(error.path)[1:]}", error.message)


def schema_validation_result(package: ManifestPackage) -> ValidationResult:
    result = ValidationResult()
    for key in SINGLE_CHAPTER_KEYS:
        data = package.chapters[key]
        append_schema_errors(result, CHAPTER_DEF_BY_KEY[key], data, f"$.{key}")
        chapter = data.get("chapter", {})
        if chapter.get("key") != key:
            result.error("chapter.key", f"$.{key}.chapter.key", "chapter.key must match manifest property")
    for index, mechanism in enumerate(package.mechanisms):
        append_schema_errors(result, "MechanismChapter", mechanism.data, f"$.key_mechanisms[{index}]")
        if "chapter" in mechanism.data:
            result.error("mechanism.chapter", f"$.key_mechanisms[{index}].chapter", "Mechanism JSON files must not contain chapter")
    return result
```

Create `scripts/build_v030_chapter_schema.py` with the complete schema builder below, then run it to write `schemas/v0.3.0/chapter.schema.json`. Do not hand-write a partial schema and do not leave chapter definitions to be inferred from prose during implementation.

```python
#!/usr/bin/env python3
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "schemas/v0.3.0/chapter.schema.json"


def ref(name):
    return {"$ref": f"#/$defs/{name}"}


def string():
    return {"type": "string", "minLength": 1}


def const(value):
    return {"const": value}


def enum(*values):
    return {"type": "string", "enum": list(values)}


def integer():
    return {"type": "integer", "minimum": 1}


def array(item, *, min_items=None, max_items=None):
    schema = {"type": "array", "items": item}
    if min_items is not None:
        schema["minItems"] = min_items
    if max_items is not None:
        schema["maxItems"] = max_items
    return schema


def obj(required, properties):
    return {
        "type": "object",
        "additionalProperties": False,
        "required": required,
        "properties": properties,
    }


def chapter_header(key, title):
    return obj(["key", "title"], {"key": const(key), "title": const(title)})


defs = {
    "Confidence": enum("high", "medium", "low"),
    "ChapterKey": enum(
        "document",
        "repository_overview",
        "directory_map",
        "module_layers",
        "repository_mainline",
        "key_mechanisms",
        "integration_boundaries",
        "risks_validation",
    ),
    "Id": {"type": "string", "pattern": "^[a-z0-9][a-z0-9_-]*$"},
    "Path": {"type": "string", "minLength": 1, "pattern": "^(?!/)(?!.*\\\\\\\\)(?!.*(?:^|/)(?:\\.|\\.\\.)(?:/|$))(?!.*//).+$"},
    "SourceRef": obj(["path"], {"path": ref("Path"), "symbol": string()}),
    "Diagram": obj(
        ["id", "title", "diagram_type", "description", "source"],
        {
            "id": ref("Id"),
            "title": string(),
            "diagram_type": enum("flowchart", "sequenceDiagram", "stateDiagram-v2"),
            "description": string(),
            "source": string(),
        },
    ),
    "FlowchartDiagram": obj(
        ["id", "title", "diagram_type", "description", "source"],
        {
            "id": ref("Id"),
            "title": string(),
            "diagram_type": const("flowchart"),
            "description": string(),
            "source": string(),
        },
    ),
    "MainlineDetailDiagram": obj(
        ["id", "title", "diagram_type", "description", "source"],
        {
            "id": ref("Id"),
            "title": string(),
            "diagram_type": enum("flowchart", "sequenceDiagram"),
            "description": string(),
            "source": string(),
        },
    ),
    "DocumentInfo": obj(
        ["title", "version", "status", "language", "generated_at", "output_file"],
        {
            "title": string(),
            "version": string(),
            "status": enum("draft", "reviewed", "final"),
            "language": const("zh-CN"),
            "generated_at": string(),
            "output_file": string(),
        },
    ),
    "RepositoryInfo": obj(
        ["name", "root_display_path", "kind", "primary_languages"],
        {
            "name": string(),
            "root_display_path": string(),
            "kind": enum("c_library", "c_application", "firmware", "mixed", "other"),
            "primary_languages": array(string(), min_items=1),
        },
    ),
    "ScopeIncluded": obj(["area", "description"], {"area": string(), "description": string()}),
    "ScopeExcluded": obj(["area", "reason"], {"area": string(), "reason": string()}),
    "Scope": obj(["included", "excluded"], {"included": array(ref("ScopeIncluded")), "excluded": array(ref("ScopeExcluded"))}),
    "ConfidenceSummary": obj(
        ["level", "summary", "validation_gaps"],
        {"level": ref("Confidence"), "summary": string(), "validation_gaps": array(string())},
    ),
    "RepositoryOverview": obj(
        ["summary", "problem_domain", "repository_purpose", "target_readers"],
        {
            "summary": string(),
            "problem_domain": string(),
            "repository_purpose": string(),
            "target_readers": array(string(), min_items=1),
        },
    ),
    "RecommendedFile": obj(["path", "reason"], {"path": ref("Path"), "reason": string()}),
    "ReadingStep": obj(
        ["order", "title", "why_read_this", "recommended_files", "expected_takeaway"],
        {
            "order": integer(),
            "title": string(),
            "why_read_this": string(),
            "recommended_files": array(ref("RecommendedFile")),
            "expected_takeaway": string(),
        },
    ),
    "ReaderOrientation": obj(
        ["read_first", "read_later", "can_skip_initially"],
        {"read_first": array(string()), "read_later": array(string()), "can_skip_initially": array(string())},
    ),
    "CoreCapability": obj(
        ["name", "description", "entry_points", "notes"],
        {"name": string(), "description": string(), "entry_points": array(ref("SourceRef")), "notes": string()},
    ),
    "DirectoryGroup": obj(
        ["name", "role", "paths", "responsibility", "read_when", "notes"],
        {
            "name": string(),
            "role": enum("main_source", "public_headers", "platform_port", "plugin", "demo", "docs", "tests", "third_party", "build", "generated", "other"),
            "paths": array(ref("Path"), min_items=1),
            "responsibility": string(),
            "read_when": string(),
            "notes": string(),
        },
    ),
    "ImportantFile": obj(
        ["path", "role", "why_it_matters", "related_chapters"],
        {"path": ref("Path"), "role": string(), "why_it_matters": string(), "related_chapters": array(ref("ChapterKey"))},
    ),
    "RelationshipDiagram": obj(["summary"], {"summary": string(), "diagram": ref("Diagram")}),
    "AreaBoundaryNote": obj(["area", "note"], {"area": string(), "note": string()}),
    "TopicBoundaryNote": obj(["topic", "note"], {"topic": string(), "note": string()}),
    "Layer": obj(
        ["layer_id", "name", "role", "responsibilities", "paths", "notes"],
        {"layer_id": ref("Id"), "name": string(), "role": string(), "responsibilities": array(string()), "paths": array(ref("Path"), min_items=1), "notes": string()},
    ),
    "ModuleCollaboration": obj(["module_ref", "relationship"], {"module_ref": ref("Id"), "relationship": string()}),
    "Module": obj(
        ["module_id", "name", "layer_id", "purpose", "source_paths", "owns", "consumes", "produces", "does_not_own", "collaborates_with", "read_when", "notes"],
        {
            "module_id": ref("Id"),
            "name": string(),
            "layer_id": ref("Id"),
            "purpose": string(),
            "source_paths": array(ref("Path"), min_items=1),
            "owns": array(string()),
            "consumes": array(string()),
            "produces": array(string()),
            "does_not_own": array(string()),
            "collaborates_with": array(ref("ModuleCollaboration")),
            "read_when": string(),
            "notes": string(),
        },
    ),
    "MainlineEntry": obj(
        ["kind", "name", "description"],
        {"kind": enum("api", "command", "build_target", "startup", "user_action", "external_event", "other"), "name": string(), "description": string(), "source_ref": ref("SourceRef")},
    ),
    "MainlineStep": obj(
        ["order", "step", "source_refs", "effect"],
        {"order": integer(), "step": string(), "module_refs": array(ref("Id")), "source_refs": array(ref("SourceRef")), "effect": string()},
    ),
    "Mainline": obj(
        ["mainline_id", "name", "purpose", "entry", "steps", "result", "notes"],
        {
            "mainline_id": ref("Id"),
            "name": string(),
            "purpose": string(),
            "entry": ref("MainlineEntry"),
            "steps": array(ref("MainlineStep"), min_items=1),
            "result": string(),
            "detail_diagram": ref("MainlineDetailDiagram"),
            "notes": string(),
        },
    ),
    "MechanismSection": obj(["title"], {"title": string()}),
    "SourceFocus": obj(["source_ref", "reason"], {"source_ref": ref("SourceRef"), "reason": string()}),
    "MechanismStep": obj(
        ["order", "step", "source_refs", "state_or_data", "notes"],
        {"order": integer(), "step": string(), "source_refs": array(ref("SourceRef")), "state_or_data": string(), "notes": string()},
    ),
    "StateOrData": obj(
        ["name", "kind", "description", "source_refs"],
        {
            "name": string(),
            "kind": enum("state", "struct", "enum", "macro", "storage_layout", "runtime_value", "artifact", "other"),
            "description": string(),
            "source_refs": array(ref("SourceRef")),
        },
    ),
    "CommonMisunderstanding": obj(["misunderstanding", "correction"], {"misunderstanding": string(), "correction": string()}),
    "ConfigurationLocation": obj(["description"], {"description": string(), "source_ref": ref("SourceRef"), "external_name": string()}),
    "RequiredConfiguration": obj(
        ["name", "kind", "location", "purpose", "required_when", "notes"],
        {
            "name": string(),
            "kind": enum("macro", "config_file", "build_option", "environment", "runtime_setting", "other"),
            "location": ref("ConfigurationLocation"),
            "purpose": string(),
            "required_when": string(),
            "notes": string(),
        },
    ),
    "AdaptationLocation": obj(["description"], {"description": string(), "source_ref": ref("SourceRef"), "external_name": string()}),
    "RequiredAdaptation": obj(
        ["name", "kind", "location", "responsibility", "caller_or_consumer", "failure_if_missing"],
        {
            "name": string(),
            "kind": enum("port_function", "platform_hook", "driver_binding", "memory_hook", "logging_hook", "other"),
            "location": ref("AdaptationLocation"),
            "responsibility": string(),
            "caller_or_consumer": string(),
            "failure_if_missing": string(),
        },
    ),
    "IntegrationEntry": obj(["description"], {"description": string(), "source_ref": ref("SourceRef"), "external_name": string(), "command": string()}),
    "IntegrationPath": obj(
        ["name", "scenario", "recommended_entry", "steps", "reference_examples", "notes"],
        {"name": string(), "scenario": string(), "recommended_entry": ref("IntegrationEntry"), "steps": array(string(), min_items=1), "reference_examples": array(ref("Path")), "notes": string()},
    ),
    "ExternalDependency": obj(
        ["name", "kind", "used_by", "integration_role", "notes"],
        {"name": string(), "kind": enum("library", "hardware", "toolchain", "os", "protocol", "service", "other"), "used_by": string(), "integration_role": string(), "notes": string()},
    ),
    "OutOfScopeResponsibility": obj(
        ["topic", "owner", "reason"],
        {"topic": string(), "owner": enum("caller", "platform", "application", "build_system", "deployment", "unknown"), "reason": string()},
    ),
    "Risk": obj(
        ["risk_id", "description", "impact", "mitigation", "related_modules", "related_mechanisms", "confidence"],
        {"risk_id": ref("Id"), "description": string(), "impact": string(), "mitigation": string(), "related_modules": array(ref("Id")), "related_mechanisms": array(ref("Id")), "confidence": ref("Confidence")},
    ),
    "Assumption": obj(
        ["assumption_id", "description", "rationale", "validation_suggestion", "confidence"],
        {"assumption_id": ref("Id"), "description": string(), "rationale": string(), "validation_suggestion": string(), "confidence": ref("Confidence")},
    ),
    "ValidationGap": obj(
        ["gap_id", "gap_type", "description", "why_it_matters", "suggested_validation", "related_chapters", "confidence"],
        {
            "gap_id": ref("Id"),
            "gap_type": enum("analysis_gap", "missing_build_validation", "missing_runtime_validation", "uncertain_behavior", "no_key_mechanisms_selected", "other"),
            "description": string(),
            "why_it_matters": string(),
            "suggested_validation": string(),
            "related_chapters": array(ref("ChapterKey")),
            "confidence": ref("Confidence"),
        },
    ),
    "LowConfidenceLocation": {
        "oneOf": [
            obj(["kind", "chapter"], {"kind": const("chapter"), "chapter": ref("ChapterKey")}),
            obj(["kind", "path"], {"kind": const("manifest_path"), "path": ref("Path")}),
        ]
    },
    "LowConfidenceItem": obj(
        ["item_id", "location", "description", "reason", "needed_evidence"],
        {"item_id": ref("Id"), "location": ref("LowConfidenceLocation"), "description": string(), "reason": string(), "needed_evidence": string()},
    ),
}

defs["DocumentChapter"] = obj(
    ["chapter", "document", "repository", "scope", "confidence"],
    {"chapter": chapter_header("document", "文档说明"), "document": ref("DocumentInfo"), "repository": ref("RepositoryInfo"), "scope": ref("Scope"), "confidence": ref("ConfidenceSummary")},
)
defs["RepositoryOverviewChapter"] = obj(
    ["chapter", "overview", "core_capabilities", "reading_route", "reader_orientation"],
    {
        "chapter": chapter_header("repository_overview", "仓库概述与阅读路线"),
        "overview": ref("RepositoryOverview"),
        "core_capabilities": array(ref("CoreCapability"), min_items=1),
        "reading_route": obj(["summary", "steps"], {"summary": string(), "steps": array(ref("ReadingStep"), min_items=1)}),
        "reader_orientation": ref("ReaderOrientation"),
    },
)
defs["DirectoryMapChapter"] = obj(
    ["chapter", "summary", "directory_groups", "important_files", "directory_relationships", "boundary_notes"],
    {
        "chapter": chapter_header("directory_map", "目录地图"),
        "summary": string(),
        "directory_groups": array(ref("DirectoryGroup"), min_items=1),
        "important_files": array(ref("ImportantFile")),
        "directory_relationships": ref("RelationshipDiagram"),
        "boundary_notes": array(ref("AreaBoundaryNote")),
    },
)
defs["ModuleLayersChapter"] = obj(
    ["chapter", "summary", "layers", "modules", "boundary_notes"],
    {
        "chapter": chapter_header("module_layers", "系统分层与模块职责"),
        "summary": string(),
        "layers": array(ref("Layer"), min_items=1),
        "modules": array(ref("Module"), min_items=1),
        "boundary_notes": array(ref("TopicBoundaryNote")),
        "layer_diagram": ref("Diagram"),
    },
)
defs["RepositoryMainlineChapter"] = obj(
    ["chapter", "summary", "mainline_overview_diagram", "mainlines", "cross_mainline_notes"],
    {
        "chapter": chapter_header("repository_mainline", "仓库主线"),
        "summary": string(),
        "mainline_overview_diagram": ref("FlowchartDiagram"),
        "mainlines": array(ref("Mainline"), min_items=1, max_items=3),
        "cross_mainline_notes": array(ref("TopicBoundaryNote")),
    },
)
defs["MechanismChapter"] = obj(
    ["section", "why_it_matters", "reader_prerequisites", "related_modules", "source_focus", "mechanism_overview", "flow", "key_states_or_data", "common_misunderstandings", "validation_gaps", "confidence"],
    {
        "section": ref("MechanismSection"),
        "why_it_matters": string(),
        "reader_prerequisites": array(string()),
        "related_modules": array(ref("Id")),
        "source_focus": array(ref("SourceFocus"), min_items=1),
        "mechanism_overview": string(),
        "flow": array(ref("MechanismStep"), min_items=1),
        "key_states_or_data": array(ref("StateOrData")),
        "common_misunderstandings": array(ref("CommonMisunderstanding")),
        "validation_gaps": array(string()),
        "confidence": ref("Confidence"),
        "diagram": ref("Diagram"),
    },
)
defs["IntegrationBoundariesChapter"] = obj(
    ["chapter", "summary", "required_configuration", "required_adaptations", "integration_paths", "external_dependencies", "out_of_scope_responsibilities"],
    {
        "chapter": chapter_header("integration_boundaries", "配置、移植与集成边界"),
        "summary": string(),
        "required_configuration": array(ref("RequiredConfiguration")),
        "required_adaptations": array(ref("RequiredAdaptation")),
        "integration_paths": array(ref("IntegrationPath")),
        "external_dependencies": array(ref("ExternalDependency")),
        "out_of_scope_responsibilities": array(ref("OutOfScopeResponsibility")),
    },
)
defs["RisksValidationChapter"] = obj(
    ["chapter", "summary", "risks", "assumptions", "validation_gaps", "low_confidence_items"],
    {
        "chapter": chapter_header("risks_validation", "风险、假设与验证缺口"),
        "summary": string(),
        "risks": array(ref("Risk")),
        "assumptions": array(ref("Assumption")),
        "validation_gaps": array(ref("ValidationGap")),
        "low_confidence_items": array(ref("LowConfidenceItem")),
    },
)

schema = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://create-structure-md.local/schemas/v0.3.0/chapter.schema.json",
    "$defs": defs,
}

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(schema, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
```

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python scripts/build_v030_chapter_schema.py
```

Expected: `schemas/v0.3.0/chapter.schema.json` exists and contains all chapter definitions named in `CHAPTER_DEF_BY_KEY` plus `MechanismChapter`.

- [ ] **Step 5: Replace the validation CLI with the manifest-plus-schema version**

Replace `scripts/validate_structure.py` with this complete content:

```python
#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path

from scripts.v030_package import load_manifest_package, manifest_shape_errors
from scripts.v030_schema import schema_validation_result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate create-structure-md 0.3.0 manifest package.")
    parser.add_argument("manifest", help="Path to structure.manifest.json")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as errors.")
    parser.add_argument("--repo-root", help="Optional repository root for SourceRef existence checks.")
    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    manifest_path = Path(args.manifest)
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"file not found: {manifest_path}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print(f"invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}", file=sys.stderr)
        return 2
    if isinstance(manifest, dict) and "dsl_version" in manifest:
        print("ERROR: $.dsl_version: structure.manifest.json must not contain dsl_version", file=sys.stderr)
        return 2
    shape_errors = manifest_shape_errors(manifest)
    if shape_errors:
        for issue in shape_errors:
            print(issue.format(), file=sys.stderr)
        return 2
    try:
        package = load_manifest_package(manifest_path)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    schema_result = schema_validation_result(package)
    if schema_result.errors:
        for issue in schema_result.errors:
            print(issue.format(), file=sys.stderr)
        return 2
    print("Validation succeeded")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 6: Run scaffold, manifest, and chapter schema tests**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_v030_scaffold tests.test_v030_manifest tests.test_v030_chapter_schema -v
```

Expected: PASS.

- [ ] **Step 7: Commit chapter schema validation**

Run:

```bash
git add schemas/v0.3.0/chapter.schema.json scripts/build_v030_chapter_schema.py scripts/v030_schema.py scripts/validate_structure.py tests/helpers_v030.py tests/test_v030_chapter_schema.py
git commit -m "feat: validate 0.3.0 chapter schemas"
```

---

### Task 4: Package-Level Semantic Validation

**Files:**
- Create: `scripts/v030_semantics.py`
- Create: `tests/test_v030_semantics.py`
- Modify: `scripts/validate_structure.py`

- [ ] **Step 1: Write the failing semantic tests**

Create `tests/test_v030_semantics.py`:

```python
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
```

- [ ] **Step 2: Run semantic tests and verify they fail**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_v030_semantics -v
```

Expected: FAIL because `scripts/v030_semantics.py` does not exist.

- [ ] **Step 3: Implement semantic validation**

Create `scripts/v030_semantics.py`:

```python
from pathlib import Path

from scripts.v030_package import ManifestPackage
from scripts.v030_types import ValidationResult


def collect_diagrams(value, path="$"):
    if isinstance(value, dict):
        if {"id", "title", "diagram_type", "description", "source"}.issubset(value):
            yield path, value
        for key, child in value.items():
            yield from collect_diagrams(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from collect_diagrams(child, f"{path}[{index}]")


def walk_source_refs(value, path="$"):
    if isinstance(value, dict):
        if "path" in value and set(value.keys()).issubset({"path", "symbol"}):
            yield path, value
        for key, child in value.items():
            yield from walk_source_refs(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from walk_source_refs(child, f"{path}[{index}]")


def check_unique(result: ValidationResult, collection, id_field: str, label: str, path: str) -> None:
    seen: dict[str, int] = {}
    for index, item in enumerate(collection):
        value = item[id_field]
        if value in seen:
            result.error(f"semantic.{label}_unique", f"{path}[{index}].{id_field}", f"duplicate {label}: {value}")
        else:
            seen[value] = index


def check_ordered(result: ValidationResult, collection, path: str) -> None:
    orders = [item["order"] for item in collection]
    expected = list(range(1, len(collection) + 1))
    if orders != expected:
        result.error("semantic.order", path, f"order values must start at 1 without gaps: expected {expected}, got {orders}")


def semantic_validation_result(package: ManifestPackage, repo_root: Path | None = None) -> ValidationResult:
    result = ValidationResult()
    module_layers = package.chapters["module_layers"]
    risks_chapter = package.chapters["risks_validation"]

    check_unique(result, module_layers["layers"], "layer_id", "layer-id", "$.module_layers.layers")
    check_unique(result, module_layers["modules"], "module_id", "module-id", "$.module_layers.modules")
    check_unique(result, package.chapters["repository_mainline"]["mainlines"], "mainline_id", "mainline-id", "$.repository_mainline.mainlines")
    check_unique(result, risks_chapter["risks"], "risk_id", "risk-id", "$.risks_validation.risks")
    check_unique(result, risks_chapter["assumptions"], "assumption_id", "assumption-id", "$.risks_validation.assumptions")
    check_unique(result, risks_chapter["validation_gaps"], "gap_id", "gap-id", "$.risks_validation.validation_gaps")
    check_unique(result, risks_chapter["low_confidence_items"], "item_id", "item-id", "$.risks_validation.low_confidence_items")
    check_ordered(result, package.chapters["repository_overview"]["reading_route"]["steps"], "$.repository_overview.reading_route.steps")

    module_ids = {module["module_id"] for module in module_layers["modules"]}
    layer_ids = {layer["layer_id"] for layer in module_layers["layers"]}
    mechanism_keys = {mechanism.key for mechanism in package.mechanisms}

    for module_index, module in enumerate(module_layers["modules"]):
        if module["layer_id"] not in layer_ids:
            result.error("semantic.layer_ref", f"$.module_layers.modules[{module_index}].layer_id", f"layer-id does not resolve: {module['layer_id']}")
        for collab_index, collab in enumerate(module.get("collaborates_with", [])):
            if collab["module_ref"] not in module_ids:
                result.error("semantic.module_ref", f"$.module_layers.modules[{module_index}].collaborates_with[{collab_index}].module_ref", f"module-id does not resolve: {collab['module_ref']}")

    for mainline_index, mainline in enumerate(package.chapters["repository_mainline"]["mainlines"]):
        check_ordered(result, mainline["steps"], f"$.repository_mainline.mainlines[{mainline_index}].steps")
        for step_index, step in enumerate(mainline["steps"]):
            for ref_index, module_ref in enumerate(step.get("module_refs", [])):
                if module_ref not in module_ids:
                    result.error("semantic.module_ref", f"$.repository_mainline.mainlines[{mainline_index}].steps[{step_index}].module_refs[{ref_index}]", f"module-id does not resolve: {module_ref}")

    for mechanism_index, mechanism in enumerate(package.mechanisms):
        check_ordered(result, mechanism.data["flow"], f"$.key_mechanisms[{mechanism_index}].flow")
        for ref_index, module_ref in enumerate(mechanism.data.get("related_modules", [])):
            if module_ref not in module_ids:
                result.error("semantic.module_ref", f"$.key_mechanisms[{mechanism_index}].related_modules[{ref_index}]", f"module-id does not resolve: {module_ref}")

    for risk_index, risk in enumerate(risks_chapter["risks"]):
        for ref_index, module_ref in enumerate(risk["related_modules"]):
            if module_ref not in module_ids:
                result.error("semantic.module_ref", f"$.risks_validation.risks[{risk_index}].related_modules[{ref_index}]", f"module-id does not resolve: {module_ref}")
        for ref_index, mechanism_key in enumerate(risk["related_mechanisms"]):
            if mechanism_key not in mechanism_keys:
                result.error("semantic.mechanism_ref", f"$.risks_validation.risks[{risk_index}].related_mechanisms[{ref_index}]", f"mechanism-key does not resolve: {mechanism_key}")

    diagram_ids: dict[str, str] = {}
    for key, chapter in package.chapters.items():
        for path, diagram in collect_diagrams(chapter, f"$.{key}"):
            diagram_id = diagram["id"]
            if diagram_id in diagram_ids:
                result.error("semantic.diagram_id_unique", path + ".id", f"duplicate diagram-id: {diagram_id}")
            diagram_ids[diagram_id] = path
    for index, mechanism in enumerate(package.mechanisms):
        for path, diagram in collect_diagrams(mechanism.data, f"$.key_mechanisms[{index}]"):
            diagram_id = diagram["id"]
            if diagram_id in diagram_ids:
                result.error("semantic.diagram_id_unique", path + ".id", f"duplicate diagram-id: {diagram_id}")
            diagram_ids[diagram_id] = path

    if not package.mechanisms:
        gaps = risks_chapter["validation_gaps"]
        has_required_gap = any(
            gap["gap_type"] == "no_key_mechanisms_selected" and "key_mechanisms" in gap["related_chapters"]
            for gap in gaps
        )
        if not has_required_gap:
            result.error("semantic.empty_mechanisms_gap", "$.risks_validation.validation_gaps", "empty key_mechanisms requires a no_key_mechanisms_selected validation gap related to key_mechanisms")

    for item_index, item in enumerate(risks_chapter["low_confidence_items"]):
        location = item["location"]
        if location["kind"] == "manifest_path" and location["path"] not in package.declared_paths:
            result.error(
                "semantic.diagnostic_manifest_path",
                f"$.risks_validation.low_confidence_items[{item_index}].location.path",
                f"diagnostic manifest path does not resolve to a manifest child: {location['path']}",
            )

    if repo_root is not None:
        repo_root = Path(repo_root)
        for key, chapter in package.chapters.items():
            for path, source_ref in walk_source_refs(chapter, f"$.{key}"):
                source_path = repo_root / source_ref["path"]
                if not source_path.exists():
                    result.error("semantic.source_ref_path", path + ".path", f"SourceRef.path does not exist: {source_ref['path']}")
                elif "symbol" in source_ref and not source_path.is_file():
                    result.error("semantic.source_ref_file", path + ".path", f"SourceRef.symbol requires path to identify a source file: {source_ref['path']}")
        for index, mechanism in enumerate(package.mechanisms):
            for path, source_ref in walk_source_refs(mechanism.data, f"$.key_mechanisms[{index}]"):
                source_path = repo_root / source_ref["path"]
                if not source_path.exists():
                    result.error("semantic.source_ref_path", path + ".path", f"SourceRef.path does not exist: {source_ref['path']}")
                elif "symbol" in source_ref and not source_path.is_file():
                    result.error("semantic.source_ref_file", path + ".path", f"SourceRef.symbol requires path to identify a source file: {source_ref['path']}")

    return result
```

- [ ] **Step 4: Replace the validation CLI with the schema-plus-semantic version**

Replace `scripts/validate_structure.py` with this complete content so the CLI has one clear loading and reporting path:

```python
#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path

from scripts.v030_package import load_manifest_package, manifest_shape_errors
from scripts.v030_schema import schema_validation_result
from scripts.v030_semantics import semantic_validation_result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate create-structure-md 0.3.0 manifest package.")
    parser.add_argument("manifest", help="Path to structure.manifest.json")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as errors.")
    parser.add_argument("--repo-root", help="Optional repository root for SourceRef existence checks.")
    return parser


def print_result(result, *, strict: bool) -> int:
    for issue in result.warnings:
        print(issue.format(), file=sys.stderr)
    if result.errors or (strict and result.warnings):
        for issue in result.errors:
            print(issue.format(), file=sys.stderr)
        return 2
    return 0


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    manifest_path = Path(args.manifest)
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"file not found: {manifest_path}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print(f"invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}", file=sys.stderr)
        return 2
    if isinstance(manifest, dict) and "dsl_version" in manifest:
        print("ERROR: $.dsl_version: structure.manifest.json must not contain dsl_version", file=sys.stderr)
        return 2
    shape_errors = manifest_shape_errors(manifest)
    if shape_errors:
        for issue in shape_errors:
            print(issue.format(), file=sys.stderr)
        return 2
    try:
        package = load_manifest_package(manifest_path)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    schema_code = print_result(schema_validation_result(package), strict=args.strict)
    if schema_code:
        return schema_code
    semantic_code = print_result(
        semantic_validation_result(package, repo_root=Path(args.repo_root) if args.repo_root else None),
        strict=args.strict,
    )
    if semantic_code:
        return semantic_code
    print("Validation succeeded")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 5: Run semantic tests plus previous tests**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_v030_scaffold tests.test_v030_manifest tests.test_v030_chapter_schema tests.test_v030_semantics -v
```

Expected: PASS.

- [ ] **Step 6: Commit semantic validation**

Run:

```bash
git add scripts/v030_semantics.py scripts/validate_structure.py tests/test_v030_semantics.py
git commit -m "feat: validate 0.3.0 package semantics"
```

---

### Task 5: Mermaid Tooling Gate

**Files:**
- Create: `scripts/v030_mermaid.py`
- Create: `tests/test_v030_mermaid.py`
- Create: `references/mermaid-rules.md`
- Modify only if needed: `scripts/validate_structure.py`

- [ ] **Step 1: Remove the old Mermaid source-inspection design**

Do not implement Mermaid syntax with regexes, token splitting, local grammar rules, edge parsing, node parsing, bracket-label extraction, sequence alias parsing, or source-level visible-label parsing. Do not infer rendered labels by parsing Mermaid source. Do not keep a compatibility layer for a custom source-inspection approach.

Keep only:

- a thin Python integration layer that calls official Mermaid tooling and converts tool results to `ValidationResult` diagnostics
- path discovery for Node and Mermaid packages
- JSON serialization/deserialization for the tool process
- Mermaid result-name normalization, such as `flowchart-v2` to `flowchart` and `sequence` to `sequenceDiagram`
- first non-comment, non-empty declaration word extraction only for the project policy that rejects legacy `graph`

- [ ] **Step 2: Write the failing Mermaid tooling tests**

Create `tests/test_v030_mermaid.py` with focused contract tests:

```python
import contextlib
import io
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tests.helpers_v030 import write_valid_package

from scripts import v030_mermaid
from scripts import validate_structure
from scripts.v030_mermaid import mermaid_validation_result
from scripts.v030_package import load_manifest_package
from scripts.v030_types import ValidationResult


ROOT = Path(__file__).resolve().parents[1]


def valid_package_with_source(source: str, diagram_type: str = "flowchart"):
    tmpdir = tempfile.TemporaryDirectory()
    manifest = write_valid_package(tmpdir.name)
    package = load_manifest_package(manifest)
    diagram = package.chapters["repository_mainline"]["mainline_overview_diagram"]
    diagram["diagram_type"] = diagram_type
    diagram["source"] = source
    return tmpdir, package


def completed_tool(payload, returncode=0, stderr=""):
    return subprocess.CompletedProcess(args=["node"], returncode=returncode, stdout=json.dumps(payload), stderr=stderr)


class V030MermaidToolingTests(unittest.TestCase):
    def run_with_tool_result(self, package, payload, returncode=0, stderr=""):
        with mock.patch("scripts.v030_mermaid._locate_node", return_value=Path("/tool/node")):
            with mock.patch("scripts.v030_mermaid._locate_mermaid_module", return_value=Path("/tool/mermaid.esm.mjs")):
                with mock.patch("scripts.v030_mermaid.subprocess.run", return_value=completed_tool(payload, returncode, stderr)):
                    return mermaid_validation_result(package)

    def test_valid_flowchart_succeeds_when_tool_reports_flowchart_v2(self):
        tmpdir, package = valid_package_with_source("flowchart TD\n  a[Start] --> b[Done]")
        with tmpdir:
            result = self.run_with_tool_result(package, {"ok": True, "diagramType": "flowchart-v2"})
        self.assertTrue(result.ok, [issue.format() for issue in result.errors])

    def test_invalid_mermaid_syntax_returns_syntax_error(self):
        tmpdir, package = valid_package_with_source("flowchart TD\n  a -->")
        with tmpdir:
            result = self.run_with_tool_result(package, {"ok": False, "error": "Parse error"})
        self.assertFalse(result.ok)
        self.assertTrue(any(issue.code == "mermaid.syntax" for issue in result.errors))

    def test_dsl_type_mismatch_returns_diagram_type_error(self):
        tmpdir, package = valid_package_with_source("sequenceDiagram\n  A->>B: hi", diagram_type="flowchart")
        with tmpdir:
            result = self.run_with_tool_result(package, {"ok": True, "diagramType": "sequence"})
        self.assertFalse(result.ok)
        self.assertTrue(any(issue.code == "mermaid.diagram_type" for issue in result.errors))

    def test_legacy_graph_declaration_is_rejected_before_tooling(self):
        tmpdir, package = valid_package_with_source("%% comment\ngraph TD\n  a --> b")
        with tmpdir:
            with mock.patch("scripts.v030_mermaid.subprocess.run") as run:
                result = mermaid_validation_result(package)
        self.assertFalse(result.ok)
        self.assertTrue(any(issue.code == "mermaid.legacy_graph" for issue in result.errors))
        run.assert_not_called()

    def test_missing_node_mermaid_package_or_failed_invocation_returns_tooling_error(self):
        tmpdir, package = valid_package_with_source("flowchart TD\n  a --> b")
        with tmpdir:
            with mock.patch("scripts.v030_mermaid._locate_node", return_value=None):
                result = mermaid_validation_result(package)
        self.assertFalse(result.ok)
        self.assertTrue(any(issue.code == "mermaid.tooling" for issue in result.errors))

    def test_mermaid_module_discovery_uses_mmdc_package_layout(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            mmdc = root / "bin" / "mmdc"
            module = root / "node_modules" / "@mermaid-js" / "mermaid-cli" / "node_modules" / "mermaid" / "dist" / "mermaid.esm.mjs"
            mmdc.parent.mkdir(parents=True)
            module.parent.mkdir(parents=True)
            mmdc.write_text("", encoding="utf-8")
            module.write_text("", encoding="utf-8")
            with mock.patch.dict(os.environ, {"MERMAID_ESM_PATH": "", "MERMAID_PACKAGE_PATH": ""}, clear=False):
                with mock.patch("scripts.v030_mermaid.shutil.which", return_value=str(mmdc)):
                    self.assertEqual(module, v030_mermaid._locate_mermaid_module())

    def test_strict_cli_promotes_mermaid_warnings_to_errors(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest = write_valid_package(tmpdir)
            warning_result = ValidationResult()
            warning_result.warn("mermaid.warning", "$.repository_mainline.mainline_overview_diagram.source", "tool warning")
            with mock.patch("scripts.validate_structure.mermaid_validation_result", return_value=warning_result):
                stderr = io.StringIO()
                with contextlib.redirect_stderr(stderr):
                    code = validate_structure.main([str(manifest), "--strict"])
        self.assertEqual(2, code)
        self.assertIn("strict mode treats validation warnings as errors", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run Mermaid tests and verify they fail**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_v030_mermaid -v
```

Expected: FAIL because `scripts/v030_mermaid.py` does not exist.

- [ ] **Step 4: Implement Mermaid official-tool validation**

Create `scripts/v030_mermaid.py` as a thin wrapper around official Mermaid tooling:

- collect diagrams with `collect_diagrams` from `scripts.v030_semantics`
- locate Node through an explicit environment variable first, then `PATH`
- locate Mermaid through an explicit environment variable first, then the installed `mmdc` package layout, then local `node_modules`
- call Node with Mermaid's own ESM API, preferably `mermaid.parse(source)`
- map Mermaid parse failures to `mermaid.syntax`
- map missing executable/package, non-JSON output, or failed process invocation to `mermaid.tooling`
- map official Mermaid diagram type names to DSL names, including `flowchart-v2 -> flowchart` and `sequence -> sequenceDiagram`
- reject a first non-comment declaration word of `graph` as `mermaid.legacy_graph` before invoking the tool
- return a `ValidationResult`

Forbidden helper logic:

- Mermaid edge parsing
- Mermaid node parsing
- flowchart bracket-label parsing
- sequence participant alias parsing
- state-diagram grammar recognition
- regex checks that try to decide Mermaid syntax validity
- source-level visible-label parsing

- [ ] **Step 5: Document Mermaid rules**

Create `references/mermaid-rules.md`:

```markdown
# create-structure-md 0.3.0 Mermaid Rules

## Purpose

Mermaid diagrams exist to help readers build a mental model. The project validator must not implement a second Mermaid.

## Hard Boundary

Do not add a self-authored Mermaid syntax parser, grammar recognizer, regex syntax checker, edge parser, node parser, bracket-label parser, sequence alias parser, or source-level visible-label parser.

Syntax validation is delegated to Mermaid official tooling, such as `mermaid.parse`, `mmdc`, or another official Mermaid package or CLI entry point.

## Supported DSL Types

- `flowchart`
- `sequenceDiagram`
- `stateDiagram-v2`

The validator maps Mermaid tool result names to DSL names before comparison. For example, `flowchart-v2` and `flowchart` both normalize to `flowchart`, and `sequence` normalizes to `sequenceDiagram`.

## Project Policy Checks

The validator keeps only narrow project policy checks outside Mermaid tooling:

- legacy `graph` declarations are rejected; authors must use `flowchart`
- the DSL `diagram_type` must match the Mermaid tool-reported diagram type after normalization

These checks are not a Mermaid grammar implementation.

## Visible Labels

Visible labels must be human-readable and must not expose internal IDs. In 0.3.0, the validator does not implement a source-level visible-label parser.

Future automated label gates must inspect Mermaid tooling output, such as rendered SVG text, rather than parsing Mermaid source locally.
```

- [ ] **Step 6: Confirm the validation CLI behavior**

`scripts/validate_structure.py` should continue to run schema, semantic, and Mermaid diagnostics on one path and make `--strict` promote every warning to failure. If it already does this, leave it alone.

- [ ] **Step 7: Run Mermaid and previous tests**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_v030_scaffold tests.test_v030_manifest tests.test_v030_chapter_schema tests.test_v030_semantics tests.test_v030_mermaid -v
```

Expected: PASS.

- [ ] **Step 8: Commit Mermaid validation**

Run:

```bash
git add scripts/v030_mermaid.py scripts/validate_structure.py references/mermaid-rules.md tests/test_v030_mermaid.py
git commit -m "feat: add 0.3.0 mermaid tooling gate"
```

---

### Task 6: Fixed Eight-Chapter Markdown Renderer

**Files:**
- Create: `scripts/v030_renderer.py`
- Create: `scripts/render_markdown.py`
- Create: `tests/test_v030_renderer.py`
- Create: `references/document-structure.md`

- [ ] **Step 1: Write the failing renderer tests**

Create `tests/test_v030_renderer.py`:

```python
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.helpers_v030 import write_valid_package

from scripts.v030_package import load_manifest_package
from scripts.v030_renderer import render_markdown


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable


class V030RendererTests(unittest.TestCase):
    def test_renders_fixed_eight_chapters_in_order(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            package = load_manifest_package(write_valid_package(tmpdir))
            markdown = render_markdown(package)
        expected_titles = [
            "# 示例仓库结构说明",
            "## 1. 文档说明",
            "## 2. 仓库概述与阅读路线",
            "## 3. 目录地图",
            "## 4. 系统分层与模块职责",
            "## 5. 仓库主线",
            "## 6. 关键机制深读",
            "## 7. 配置、移植与集成边界",
            "## 8. 风险、假设与验证缺口",
        ]
        positions = [markdown.index(title) for title in expected_titles]
        self.assertEqual(positions, sorted(positions))

    def test_renderer_hides_internal_reference_ids_from_visible_text(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            package = load_manifest_package(write_valid_package(tmpdir))
            markdown = render_markdown(package)
        forbidden = ["storage_api", "storage_core", "mainline_overview", "static_only", "caller_initializes_once"]
        for token in forbidden:
            with self.subTest(token=token):
                self.assertNotIn(token, markdown)
        self.assertIn("存储接口", markdown)
        self.assertIn("存储核心", markdown)

    def test_empty_key_mechanisms_renders_fixed_sentence(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            package = load_manifest_package(write_valid_package(tmpdir, key_mechanisms=False))
            markdown = render_markdown(package)
        self.assertIn("本次分析未选择可深读的关键机制。", markdown)

    def test_renderer_includes_required_chapter_6_7_8_content(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            package = load_manifest_package(write_valid_package(tmpdir))
            markdown = render_markdown(package)
        expected_fragments = [
            "先读仓库主线。",
            "相关模块：存储核心",
            "`src/storage.c` / `storage_write`：写入流程入口。",
            "核心层接收写入请求并交给平台适配完成。",
            "写入缓冲区",
            "未在真实硬件上验证写入时序。",
            "机制置信度：medium",
            "应用集成",
            "Flash 驱动",
            "硬件寿命评估",
            "相关机制：持久化写入机制",
            "相关章节：关键机制深读",
            "应用按预期只初始化一次。",
            "位置：配置、移植与集成边界",
            "平台适配行为来自接口推断。",
        ]
        for fragment in expected_fragments:
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, markdown)

    def test_renderer_includes_required_chapter_1_to_5_content(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            package = load_manifest_package(write_valid_package(tmpdir))
            package.chapters["repository_mainline"]["mainlines"][0]["detail_diagram"] = {
                "id": "init_detail",
                "title": "初始化细节图",
                "diagram_type": "flowchart",
                "description": "展示初始化细节。",
                "source": "flowchart TD\n  api[存储接口] --> core[存储核心]",
            }
            markdown = render_markdown(package)
        expected_fragments = [
            "生成时间：2026-05-16T00:00:00+08:00",
            "分析范围",
            "嵌入式持久化",
            "提供可移植的存储能力。",
            "首次阅读仓库的工程师",
            "先读：include/storage.h",
            "后读：src/storage.c",
            "可暂时跳过：docs/",
            "定义应用调用面。",
            "应用通过公共头文件进入核心实现。",
            "示例代码不是库的一部分。",
            "入口：storage_init",
            "`include/storage.h` / `storage_init`",
            "`src/storage.c` / `storage_init`",
            "初始化细节图",
            "平台驱动由第七章说明。",
            "这是阅读主线，不是调用序列参考。",
        ]
        for fragment in expected_fragments:
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, markdown)

    def test_render_cli_writes_document_output_file_by_default(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest = write_valid_package(tmpdir)
            completed = subprocess.run(
                [PYTHON, str(ROOT / "scripts/render_markdown.py"), str(manifest)],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            output = Path(tmpdir) / "Example_STRUCTURE_DESIGN.md"
            self.assertEqual(0, completed.returncode, completed.stderr)
            self.assertTrue(output.is_file())
            self.assertIn("Document written:", completed.stdout)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run renderer tests and verify they fail**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_v030_renderer -v
```

Expected: FAIL because renderer files do not exist.

- [ ] **Step 3: Implement the renderer**

Create `scripts/v030_renderer.py`:

```python
def bullet(items):
    return "\n".join(f"- {item}" for item in items)


def source_ref_text(source_ref):
    symbol = source_ref.get("symbol")
    return f"`{source_ref['path']}`" + (f" / `{symbol}`" if symbol else "")


def module_name_map(package):
    return {module["module_id"]: module["name"] for module in package.chapters["module_layers"]["modules"]}


def mechanism_title_map(package):
    return {mechanism.key: mechanism.data["section"]["title"] for mechanism in package.mechanisms}


CHAPTER_TITLE_BY_KEY = {
    "document": "文档说明",
    "repository_overview": "仓库概述与阅读路线",
    "directory_map": "目录地图",
    "module_layers": "系统分层与模块职责",
    "repository_mainline": "仓库主线",
    "key_mechanisms": "关键机制深读",
    "integration_boundaries": "配置、移植与集成边界",
    "risks_validation": "风险、假设与验证缺口",
}


def low_confidence_location_text(location):
    if location["kind"] == "chapter":
        return CHAPTER_TITLE_BY_KEY[location["chapter"]]
    return location["path"]


def render_diagram(diagram):
    return "\n".join(
        [
            f"**{diagram['title']}**",
            "",
            diagram["description"],
            "",
            "```mermaid",
            diagram["source"],
            "```",
        ]
    )


def render_markdown(package) -> str:
    document = package.chapters["document"]
    module_names = module_name_map(package)
    mechanism_titles = mechanism_title_map(package)
    lines = [f"# {document['document']['title']}", ""]

    lines.extend(["## 1. 文档说明", "", document["confidence"]["summary"], ""])
    lines.extend(
        [
            f"- 仓库：{document['repository']['name']}",
            f"- 状态：{document['document']['status']}",
            f"- 生成时间：{document['document']['generated_at']}",
            f"- 置信度：{document['confidence']['level']}",
            "",
            "### 分析范围",
            "",
        ]
    )
    for item in document["scope"]["included"]:
        lines.append(f"- 包含：{item['area']}，{item['description']}")
    for item in document["scope"]["excluded"]:
        lines.append(f"- 不包含：{item['area']}，{item['reason']}")
    lines.append("")

    overview = package.chapters["repository_overview"]
    lines.extend(["## 2. 仓库概述与阅读路线", "", overview["overview"]["summary"], ""])
    lines.extend(
        [
            f"- 问题领域：{overview['overview']['problem_domain']}",
            f"- 仓库目的：{overview['overview']['repository_purpose']}",
            f"- 目标读者：{'、'.join(overview['overview']['target_readers'])}",
            "",
        ]
    )
    lines.extend(["### 核心能力", ""])
    for capability in overview["core_capabilities"]:
        lines.extend([f"- **{capability['name']}**：{capability['description']}"])
    lines.extend(["", "### 推荐阅读路线", ""])
    for step in overview["reading_route"]["steps"]:
        files = "、".join(item["path"] for item in step["recommended_files"])
        lines.extend([f"{step['order']}. {step['title']}：{step['why_read_this']}（{files}）"])
    orientation = overview["reader_orientation"]
    lines.extend(
        [
            "",
            "### 阅读取舍",
            "",
            f"- 先读：{'、'.join(orientation['read_first'])}",
            f"- 后读：{'、'.join(orientation['read_later'])}",
            f"- 可暂时跳过：{'、'.join(orientation['can_skip_initially'])}",
        ]
    )
    lines.append("")

    directory = package.chapters["directory_map"]
    lines.extend(["## 3. 目录地图", "", directory["summary"], ""])
    for group in directory["directory_groups"]:
        lines.extend([f"- **{group['name']}**：{group['responsibility']}"])
    lines.extend(["", "### 重要文件", ""])
    for item in directory["important_files"]:
        lines.append(f"- `{item['path']}`：{item['why_it_matters']}（{item['role']}）")
    lines.extend(["", "### 目录关系", "", directory["directory_relationships"]["summary"], ""])
    if directory["directory_relationships"].get("diagram"):
        lines.extend([render_diagram(directory["directory_relationships"]["diagram"]), ""])
    lines.extend(["### 边界说明", ""])
    for item in directory["boundary_notes"]:
        lines.append(f"- {item['area']}：{item['note']}")
    lines.append("")

    layers = package.chapters["module_layers"]
    lines.extend(["## 4. 系统分层与模块职责", "", layers["summary"], ""])
    for layer in layers["layers"]:
        lines.extend([f"### {layer['name']}", "", layer["role"], ""])
        for module in [item for item in layers["modules"] if item["layer_id"] == layer["layer_id"]]:
            collaborators = "、".join(module_names[item["module_ref"]] for item in module["collaborates_with"]) or "无"
            lines.extend(
                [
                    f"#### {module['name']}",
                    "",
                    f"- 职责：{module['purpose']}",
                    f"- 位置：{'、'.join(module['source_paths'])}",
                    f"- 拥有：{'、'.join(module['owns'])}",
                    f"- 消耗：{'、'.join(module['consumes'])}",
                    f"- 产出：{'、'.join(module['produces'])}",
                    f"- 不拥有：{'、'.join(module['does_not_own'])}",
                    f"- 邻近协作：{collaborators}",
                    "",
                ]
            )

    mainline = package.chapters["repository_mainline"]
    lines.extend(["## 5. 仓库主线", "", mainline["summary"], "", render_diagram(mainline["mainline_overview_diagram"]), ""])
    for item in mainline["mainlines"]:
        lines.extend([f"### {item['name']}", "", item["purpose"], ""])
        entry_source = source_ref_text(item["entry"]["source_ref"]) if item["entry"].get("source_ref") else "无源码定位"
        lines.extend([f"- 入口：{item['entry']['name']}（{item['entry']['kind']}），{item['entry']['description']}，{entry_source}", ""])
        for step in item["steps"]:
            names = "、".join(module_names[ref] for ref in step.get("module_refs", [])) or "无直接模块"
            source_refs = "、".join(source_ref_text(ref) for ref in step["source_refs"]) or "无源码定位"
            lines.append(f"{step['order']}. {step['step']}（{names}，{source_refs}）=> {step['effect']}")
        if item.get("detail_diagram"):
            lines.extend(["", render_diagram(item["detail_diagram"])])
        lines.extend(["", f"结果：{item['result']}", f"备注：{item['notes']}", ""])
    if mainline["cross_mainline_notes"]:
        lines.extend(["### 跨主线说明", ""])
        for note in mainline["cross_mainline_notes"]:
            lines.append(f"- {note['topic']}：{note['note']}")
        lines.append("")

    lines.extend(["## 6. 关键机制深读", ""])
    if not package.mechanisms:
        lines.extend(["本次分析未选择可深读的关键机制。", ""])
    for index, mechanism in enumerate(package.mechanisms, start=1):
        data = mechanism.data
        related_modules = "、".join(module_names[module_id] for module_id in data["related_modules"]) or "无"
        lines.extend(
            [
                f"### 6.{index} {data['section']['title']}",
                "",
                data["why_it_matters"],
                "",
                f"- 相关模块：{related_modules}",
                f"- 机制置信度：{data['confidence']}",
                "",
                "#### 阅读前提",
                "",
            ]
        )
        for prerequisite in data["reader_prerequisites"]:
            lines.append(f"- {prerequisite}")
        lines.extend(["", "#### 源码焦点", ""])
        for focus in data["source_focus"]:
            lines.append(f"- {source_ref_text(focus['source_ref'])}：{focus['reason']}")
        lines.extend(["", "#### 机制概览", "", data["mechanism_overview"], ""])
        if data.get("diagram"):
            lines.extend([render_diagram(data["diagram"]), ""])
        lines.extend(["#### 核心流程", ""])
        for step in data["flow"]:
            source_refs = "、".join(source_ref_text(ref) for ref in step["source_refs"]) or "无源码定位"
            lines.append(f"{step['order']}. {step['step']}：{step['state_or_data']}（{source_refs}）。{step['notes']}")
        lines.extend(["", "#### 关键状态与数据", ""])
        for item in data["key_states_or_data"]:
            source_refs = "、".join(source_ref_text(ref) for ref in item["source_refs"]) or "无源码定位"
            lines.append(f"- {item['name']}：{item['description']}（{item['kind']}，{source_refs}）")
        lines.extend(["", "#### 常见误解", ""])
        for item in data["common_misunderstandings"]:
            lines.append(f"- {item['misunderstanding']} => {item['correction']}")
        lines.extend(["", "#### 验证缺口", ""])
        for gap in data["validation_gaps"]:
            lines.append(f"- {gap}")
        lines.append("")

    integration = package.chapters["integration_boundaries"]
    lines.extend(["## 7. 配置、移植与集成边界", "", integration["summary"], ""])
    lines.extend(["### 必要配置", ""])
    for config in integration["required_configuration"]:
        location = config["location"]["description"]
        lines.append(f"- {config['name']}：{config['purpose']}（{config['kind']}，{location}，适用条件：{config['required_when']}）。{config['notes']}")
    lines.extend(["", "### 必要移植", ""])
    for adaptation in integration["required_adaptations"]:
        location = adaptation["location"]["description"]
        lines.append(f"- {adaptation['name']}：{adaptation['responsibility']}（{adaptation['kind']}，{location}，消费者：{adaptation['caller_or_consumer']}；缺失后果：{adaptation['failure_if_missing']}）")
    lines.extend(["", "### 集成路径", ""])
    for path in integration["integration_paths"]:
        lines.append(f"- {path['name']}：{path['scenario']}。入口：{path['recommended_entry']['description']}。步骤：{'、'.join(path['steps'])}。示例：{'、'.join(path['reference_examples']) or '无'}。{path['notes']}")
    lines.extend(["", "### 外部依赖", ""])
    for dependency in integration["external_dependencies"]:
        lines.append(f"- {dependency['name']}：{dependency['integration_role']}（{dependency['kind']}，使用方：{dependency['used_by']}）。{dependency['notes']}")
    lines.extend(["", "### 边界外责任", ""])
    for responsibility in integration["out_of_scope_responsibilities"]:
        lines.append(f"- {responsibility['topic']}：由 {responsibility['owner']} 负责，因为 {responsibility['reason']}")
    lines.append("")

    risks = package.chapters["risks_validation"]
    lines.extend(["## 8. 风险、假设与验证缺口", "", risks["summary"], ""])
    lines.extend(["### 风险", ""])
    for risk in risks["risks"]:
        related = "、".join(module_names[ref] for ref in risk["related_modules"]) or "无"
        related_mechanisms = "、".join(mechanism_titles[ref] for ref in risk["related_mechanisms"]) or "无"
        lines.append(f"- {risk['description']}（相关模块：{related}，相关机制：{related_mechanisms}，置信度：{risk['confidence']}）。影响：{risk['impact']}。缓解：{risk['mitigation']}")
    lines.extend(["", "### 假设", ""])
    for assumption in risks["assumptions"]:
        lines.append(f"- {assumption['description']}（置信度：{assumption['confidence']}）。依据：{assumption['rationale']}。验证建议：{assumption['validation_suggestion']}")
    lines.extend(["", "### 验证缺口", ""])
    for gap in risks["validation_gaps"]:
        chapters = "、".join(CHAPTER_TITLE_BY_KEY[key] for key in gap["related_chapters"]) or "无"
        lines.append(f"- {gap['description']}（{gap['gap_type']}，相关章节：{chapters}，置信度：{gap['confidence']}）。原因：{gap['why_it_matters']}。建议：{gap['suggested_validation']}")
    lines.extend(["", "### 低置信项", ""])
    for item in risks["low_confidence_items"]:
        lines.append(f"- 位置：{low_confidence_location_text(item['location'])}。{item['description']}。原因：{item['reason']}。需要证据：{item['needed_evidence']}")
    lines.append("")

    return "\n".join(lines).rstrip() + "\n"
```

Create `scripts/render_markdown.py`:

```python
#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path

from scripts.v030_mermaid import mermaid_validation_result
from scripts.v030_package import load_manifest_package
from scripts.v030_renderer import render_markdown
from scripts.v030_schema import schema_validation_result
from scripts.v030_semantics import semantic_validation_result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render create-structure-md 0.3.0 Markdown.")
    parser.add_argument("manifest", help="Path to structure.manifest.json")
    parser.add_argument("--output", help="Explicit Markdown output path.")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as errors.")
    parser.add_argument("--repo-root", help="Optional repository root for SourceRef checks.")
    return parser


def validate_or_print(package, *, strict=False, repo_root=None) -> int:
    schema_result = schema_validation_result(package)
    for result in [schema_result]:
        for issue in result.warnings:
            print(issue.format(), file=sys.stderr)
        if result.errors or (strict and result.warnings):
            for issue in result.errors:
                print(issue.format(), file=sys.stderr)
            if strict and result.warnings:
                print("ERROR: strict mode treats validation warnings as errors", file=sys.stderr)
            return 2

    semantic_result = semantic_validation_result(package, repo_root=Path(repo_root) if repo_root else None)
    for result in [semantic_result]:
        for issue in result.warnings:
            print(issue.format(), file=sys.stderr)
        if result.errors or (strict and result.warnings):
            for issue in result.errors:
                print(issue.format(), file=sys.stderr)
            if strict and result.warnings:
                print("ERROR: strict mode treats validation warnings as errors", file=sys.stderr)
            return 2

    mermaid_result = mermaid_validation_result(package)
    for result in [mermaid_result]:
        for issue in result.warnings:
            print(issue.format(), file=sys.stderr)
        if result.errors or (strict and result.warnings):
            for issue in result.errors:
                print(issue.format(), file=sys.stderr)
            if strict and result.warnings:
                print("ERROR: strict mode treats validation warnings as errors", file=sys.stderr)
            return 2
    return 0


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        package = load_manifest_package(Path(args.manifest))
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    validation_code = validate_or_print(package, strict=args.strict, repo_root=args.repo_root)
    if validation_code:
        return validation_code
    markdown = render_markdown(package)
    output_path = Path(args.output) if args.output else package.root_dir / package.chapters["document"]["document"]["output_file"]
    output_path.write_text(markdown, encoding="utf-8")
    print(f"Document written: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Document the rendered structure**

Create `references/document-structure.md`:

```markdown
# create-structure-md 0.3.0 Document Structure

## Fixed Eight Chapters

1. 文档说明
2. 仓库概述与阅读路线
3. 目录地图
4. 系统分层与模块职责
5. 仓库主线
6. 关键机制深读
7. 配置、移植与集成边界
8. 风险、假设与验证缺口

The renderer uses this fixed order. Chapter JSON object property order is not semantic.

## Human-First Rendering

Visible prose and Mermaid labels use names and explanations, not internal IDs. Chapter 4 renders module and layer names. Chapter 5 renders mainline names and human-readable Mermaid labels. Chapter 6 resolves `related_modules` through Chapter 4 when a visible name is needed.

## Chapter 6 Empty State

When `structure.manifest.json` has `"key_mechanisms": []`, the renderer still emits `## 6. 关键机制深读` followed by `本次分析未选择可深读的关键机制。`
```

- [ ] **Step 5: Run renderer tests and previous tests**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_v030_scaffold tests.test_v030_manifest tests.test_v030_chapter_schema tests.test_v030_semantics tests.test_v030_mermaid tests.test_v030_renderer -v
```

Expected: PASS.

- [ ] **Step 6: Commit the renderer**

Run:

```bash
git add scripts/v030_renderer.py scripts/render_markdown.py references/document-structure.md tests/test_v030_renderer.py
git commit -m "feat: render 0.3.0 structure markdown"
```

---

### Task 7: Skill And Reference Documentation

**Files:**
- Create: `SKILL.md`
- Create: `references/dsl-spec.md`
- Create: `references/repo-understand-workflow.md`
- Create: `references/review-checklist.md`
- Create: `tests/test_v030_docs.py`

- [ ] **Step 1: Write the failing documentation tests**

Create `tests/test_v030_docs.py`:

```python
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class V030DocumentationTests(unittest.TestCase):
    def test_skill_declares_0_3_0_boundary_and_repo_understand_handoff(self):
        text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        expected = [
            "0.3.0",
            "structure.manifest.json",
            "repo-understand",
            "固定八章",
            "不要把分析过程写入 DSL",
            "不兼容 0.2.0",
        ]
        for phrase in expected:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)

    def test_reference_docs_have_required_signposts(self):
        expectations = {
            "references/dsl-spec.md": ["main JSON is a chapter directory only", "key_mechanisms", "DocumentInfo.language", "SourceRef"],
            "references/repo-understand-workflow.md": ["repo-analysis-tools", "Chapter 6", "subagent", "mechanism JSON stores accepted content"],
            "references/review-checklist.md": ["manifest contains only chapter paths", "visible Mermaid labels", "Chapter 4 is not an API reference", "Chapter 8 records validation gaps"],
        }
        for relative_path, phrases in expectations.items():
            text = (ROOT / relative_path).read_text(encoding="utf-8")
            for phrase in phrases:
                with self.subTest(path=relative_path, phrase=phrase):
                    self.assertIn(phrase, text)

    def test_reference_docs_do_not_turn_dsl_into_easyflash_specific_contract(self):
        contract_docs = [
            ROOT / "references/dsl-spec.md",
            ROOT / "references/document-structure.md",
            ROOT / "references/review-checklist.md",
        ]
        for path in contract_docs:
            text = path.read_text(encoding="utf-8")
            with self.subTest(path=path):
                self.assertNotIn("EasyFlash", text)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run documentation tests and verify they fail**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_v030_docs -v
```

Expected: FAIL because the active skill and reference docs do not exist yet.

- [ ] **Step 3: Create active skill instructions**

Create `SKILL.md`:

```markdown
---
name: create-structure-md
description: Generate one human-first repository structure Markdown document from a prepared create-structure-md 0.3.0 manifest package.
---

# create-structure-md 0.3.0

Use this skill to render one fixed-eight-chapter repository structure document from prepared DSL content.

0.3.0 is not compatible with 0.2.0. The input is `structure.manifest.json`, not `structure.dsl.json`, and JSON payloads do not carry `dsl_version`.

## Boundary

The skill renders and validates a prepared DSL package. Repository understanding happens before the DSL is finalized. For unfamiliar C repositories, use `repo-understand` to prepare structured understanding material, especially for Chapter 6 mechanism deep dives.

不要把分析过程写入 DSL. Subagent names, repo-understand command logs, and draft reasoning belong outside renderable JSON.

## Input Shape

The manifest contains only fixed chapter path references:

1. `document`
2. `repository_overview`
3. `directory_map`
4. `module_layers`
5. `repository_mainline`
6. `key_mechanisms`
7. `integration_boundaries`
8. `risks_validation`

Chapter 6 is split directly in `key_mechanisms`; there is no aggregate `chapters/06-key-mechanisms.json`.

## Workflow

1. Validate the package with `python scripts/validate_structure.py <path/to/structure.manifest.json>`.
2. Fix schema, semantic, and Mermaid diagnostics in the DSL package.
3. Render with `python scripts/render_markdown.py <path/to/structure.manifest.json>`.
4. Review the Markdown with `references/review-checklist.md`.

## Output

The renderer writes one Markdown file named by `document.output_file`, unless `--output` is supplied.
```

- [ ] **Step 4: Create DSL, repo-understand, and review references**

Create `references/dsl-spec.md` with sections:

```markdown
# create-structure-md 0.3.0 DSL Spec

## DSL Purpose

The DSL stores renderable repository-structure content. The main JSON is a chapter directory only. It does not store repository metadata, output filename, workflow instructions, analysis logs, validation policy, or DSL version metadata.

## Manifest

`structure.manifest.json` contains exactly the eight fixed keys from the 0.3.0 contract. `key_mechanisms` is an array of direct mechanism child JSON paths. `chapters/06-key-mechanisms.json` is not a valid aggregate file.

## Shared Types

`SourceRef` is a structured object with `path` and optional `symbol`. 0.3.0 does not define `path#symbol` or symbol-only references.

`DocumentInfo.language` is `zh-CN`. Other languages require a later localization profile.

## Chapter Contracts

The authoritative field contracts live in `docs/superpowers/specs/2026-05-16-create-structure-md-0.3.0-redesign.md`. The schema implementation mirrors those names and enum values.

## Chapter 6

Each mechanism file is a direct manifest child. The mechanism key is inferred from the file stem. The mechanism JSON stores accepted content, not analysis transcript text.
```

Create `references/repo-understand-workflow.md`:

```markdown
# repo-understand Workflow For create-structure-md 0.3.0

## Purpose

create-structure-md no longer pretends repository understanding is outside the product workflow. For C repositories, run repo-understand before finalizing the DSL package.

## Mechanism Deep Dives

Chapter 6 is the primary place for repo-understand depth. The main agent identifies candidate mechanisms from the overview, directory map, modules, and mainlines. A subagent may inspect each independent mechanism with repo-analysis-tools, raw source reading, and targeted call-path checks.

## Output Boundary

Subagents return structured mechanism material. The mechanism JSON stores accepted content: what matters, source focus, flow, state/data, misunderstandings, validation gaps, and confidence. It does not store subagent identity, command logs, or analysis transcript.
```

Create `references/review-checklist.md`:

```markdown
# create-structure-md 0.3.0 Review Checklist

## Manifest

- Confirm `structure.manifest.json` contains only chapter paths.
- Confirm `key_mechanisms` directly lists mechanism JSON files.
- Confirm there is no `dsl_version` in JSON payloads.

## Human-First Output

- Confirm visible Mermaid labels are readable names, not internal IDs.
- Confirm Chapter 4 is not an API reference.
- Confirm Chapter 5 includes one to three repository mainlines.
- Confirm Chapter 6 explains mechanisms rather than listing functions.
- Confirm Chapter 8 records validation gaps honestly.

## Validation

- Run `python scripts/validate_structure.py <manifest> --strict`.
- Run `python scripts/render_markdown.py <manifest>`.
- Review diagnostics before accepting the generated Markdown.
```

- [ ] **Step 5: Run documentation tests and full current suite**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_v030_scaffold tests.test_v030_manifest tests.test_v030_chapter_schema tests.test_v030_semantics tests.test_v030_mermaid tests.test_v030_renderer tests.test_v030_docs -v
```

Expected: PASS.

- [ ] **Step 6: Commit documentation**

Run:

```bash
git add SKILL.md references/dsl-spec.md references/repo-understand-workflow.md references/review-checklist.md tests/test_v030_docs.py
git commit -m "docs: document create-structure-md 0.3.0 workflow"
```

---

### Task 8: Examples And End-To-End Acceptance

**Files:**
- Create: `examples/minimal-c-library/structure.manifest.json`
- Create: `examples/minimal-c-library/chapters/01-document.json`
- Create: `examples/minimal-c-library/chapters/02-repository-overview.json`
- Create: `examples/minimal-c-library/chapters/03-directory-map.json`
- Create: `examples/minimal-c-library/chapters/04-module-layers.json`
- Create: `examples/minimal-c-library/chapters/05-repository-mainline.json`
- Create: `examples/minimal-c-library/chapters/06-key-mechanisms/persistence.json`
- Create: `examples/minimal-c-library/chapters/07-integration-boundaries.json`
- Create: `examples/minimal-c-library/chapters/08-risks-validation.json`
- Create: `examples/no-mechanisms/structure.manifest.json`
- Create: `examples/no-mechanisms/chapters/01-document.json`
- Create: `examples/no-mechanisms/chapters/02-repository-overview.json`
- Create: `examples/no-mechanisms/chapters/03-directory-map.json`
- Create: `examples/no-mechanisms/chapters/04-module-layers.json`
- Create: `examples/no-mechanisms/chapters/05-repository-mainline.json`
- Create: `examples/no-mechanisms/chapters/07-integration-boundaries.json`
- Create: `examples/no-mechanisms/chapters/08-risks-validation.json`
- Create: `tests/test_v030_e2e.py`

- [ ] **Step 1: Write the failing end-to-end tests**

Create `tests/test_v030_e2e.py`:

```python
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
EXAMPLES = [
    ROOT / "examples/minimal-c-library/structure.manifest.json",
    ROOT / "examples/no-mechanisms/structure.manifest.json",
]


class V030EndToEndTests(unittest.TestCase):
    def test_examples_validate_in_strict_mode(self):
        for manifest in EXAMPLES:
            with self.subTest(manifest=manifest):
                completed = subprocess.run(
                    [PYTHON, str(ROOT / "scripts/validate_structure.py"), str(manifest), "--strict"],
                    cwd=ROOT,
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(0, completed.returncode, completed.stderr)
                self.assertIn("Validation succeeded", completed.stdout)

    def test_examples_render_without_visible_legacy_internal_ids(self):
        forbidden = ["MOD-", "RUN-", "FLOW-", "MER-"]
        for manifest in EXAMPLES:
            with self.subTest(manifest=manifest):
                with tempfile.TemporaryDirectory() as tmpdir:
                    output = Path(tmpdir) / "rendered.md"
                    completed = subprocess.run(
                        [PYTHON, str(ROOT / "scripts/render_markdown.py"), str(manifest), "--output", str(output), "--strict"],
                        cwd=ROOT,
                        text=True,
                        capture_output=True,
                        check=False,
                    )
                    self.assertEqual(0, completed.returncode, completed.stderr)
                    markdown = output.read_text(encoding="utf-8")
                for token in forbidden:
                    self.assertNotIn(token, markdown)
                self.assertIn("## 8. 风险、假设与验证缺口", markdown)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run end-to-end tests and verify they fail**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_v030_e2e -v
```

Expected: FAIL because example packages do not exist.

- [ ] **Step 3: Create the accepted examples**

Generate the example packages with the fixture builder so the examples and schema tests share the same concrete DSL shape. This command writes committed example files and does not delete anything:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -c "from tests.helpers_v030 import write_valid_package; write_valid_package('examples/minimal-c-library', key_mechanisms=True, repository_name='minimal-c-library', document_title='minimal-c-library 结构说明', output_file='MinimalCLibrary_STRUCTURE_DESIGN.md'); write_valid_package('examples/no-mechanisms', key_mechanisms=False, repository_name='no-mechanisms', document_title='no-mechanisms 结构说明', output_file='NoMechanisms_STRUCTURE_DESIGN.md')"
```

Use stable, generic example content:

- repository name: `minimal-c-library`
- output file: `MinimalCLibrary_STRUCTURE_DESIGN.md`
- mechanism key: `persistence`
- no references to a specific real repository brand
- all visible Mermaid labels in Chinese
- no `dsl_version`
- no `chapters/06-key-mechanisms.json`

- [ ] **Step 4: Run examples through the public CLIs**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python scripts/validate_structure.py examples/minimal-c-library/structure.manifest.json --strict
```

Expected: `Validation succeeded`.

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python scripts/validate_structure.py examples/no-mechanisms/structure.manifest.json --strict
```

Expected: `Validation succeeded`.

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_v030_e2e -v
```

Expected: PASS.

- [ ] **Step 5: Commit examples and end-to-end tests**

Run:

```bash
git add examples/minimal-c-library examples/no-mechanisms tests/test_v030_e2e.py
git commit -m "test: add 0.3.0 example package acceptance"
```

---

### Task 9: Final Verification And Implementation Handoff

**Files:**
- Verify: all active 0.3.0 files
- Verify: `docs/superpowers/specs/2026-05-16-create-structure-md-0.3.0-redesign.md`
- Verify: `docs/superpowers/history`

- [ ] **Step 1: Run the full test suite**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest discover -s tests -v
```

Expected: PASS.

- [ ] **Step 2: Validate both examples in strict mode**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python scripts/validate_structure.py examples/minimal-c-library/structure.manifest.json --strict
```

Expected: `Validation succeeded`.

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python scripts/validate_structure.py examples/no-mechanisms/structure.manifest.json --strict
```

Expected: `Validation succeeded`.

- [ ] **Step 3: Render both examples to temporary output paths**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python scripts/render_markdown.py examples/minimal-c-library/structure.manifest.json --output /tmp/minimal-c-library-structure.md --strict
```

Expected: `Document written: /tmp/minimal-c-library-structure.md`.

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python scripts/render_markdown.py examples/no-mechanisms/structure.manifest.json --output /tmp/no-mechanisms-structure.md --strict
```

Expected: `Document written: /tmp/no-mechanisms-structure.md`.

- [ ] **Step 4: Confirm historical material was not modified**

Run:

```bash
git diff --exit-code -- docs/superpowers/history
```

Expected: no output and exit code 0.

- [ ] **Step 5: Inspect worktree**

Run:

```bash
git status --short
```

Expected: only active 0.3.0 files changed since the last task commit, or no output if every task commit was already made.

- [ ] **Step 6: Commit final review adjustments if needed**

If Step 5 shows final documentation or example adjustments, run:

```bash
git add SKILL.md references schemas scripts tests examples
git commit -m "chore: finalize create-structure-md 0.3.0"
```

Expected: a final cleanup commit, or no commit when the worktree is already clean.

---

## Self-Review

Spec coverage:

- Fixed eight-chapter contract is covered by Task 6 renderer tests and `references/document-structure.md`.
- Layered manifest model, fixed keys, direct Chapter 6 mechanism files, and no aggregate Chapter 6 JSON are covered by Task 2.
- No JSON payload `dsl_version` and 0.2.0 incompatibility are covered by Task 1 and Task 7.
- Chapter JSON field contracts and enum values are covered by Task 3.
- Package-level semantic rules are covered by Task 4.
- Mermaid official tooling validation, legacy `graph` rejection, and diagram type normalization are covered by Task 5.
- repo-understand workflow and Chapter 6 subagent boundary are covered by Task 7.
- Examples and end-to-end rendering are covered by Task 8.
- Historical archive non-modification and no deletion command behavior are covered by Task 9.

Red-flag scan:

- The plan contains exact file paths, commands, expected results, and code snippets for each code-bearing task.
- It does not instruct agents to delete files or directories.
- It does not modify `docs/superpowers/history`.

Type consistency:

- `module_id`, `layer_id`, `module_ref`, `module_refs`, `related_modules`, and `related_mechanisms` match the spec vocabulary.
- `key_mechanisms` is always manifest-owned and mechanism keys are inferred from file stems.
- `DocumentInfo.language` uses the literal `zh-CN`.
- Script names are consistent across tests, implementation, examples, and docs.
