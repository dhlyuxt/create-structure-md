# create-structure-md 0.4.0 Detail List Upgrade Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the active create-structure-md 0.4.0 aggregate Chapter 4 and Chapter 5 contract with manifest-listed main-flow and module detail files that can be authored and reviewed independently.

**Architecture:** Keep active version naming at `0.4.0`, but make this a breaking contract upgrade. The package loader becomes responsible for upgraded manifest routing, safe detail path validation, inferred detail keys, and ordered detail loading; schema, semantic validation, Mermaid traversal, rendering, examples, and CLIs consume that upgraded package model. `SKILL.md` and references become the orchestration contract: the main agent owns package-level files and overview synthesis, while separate subagents own each Chapter 4 and Chapter 5 detail file.

**Tech Stack:** Python standard library, `jsonschema`, existing Mermaid CLI validation wrapper, Markdown reference files, `unittest`.

---

## User Constraints

- Do not run deletion commands. If obsolete files should be removed, print exact commands for the user to run.
- Documentation-only changes use review, not TDD.
- Code, schema, and example-package changes use TDD.
- Keep historical 0.3.0 dispatch working from `docs/superpowers/history/V3/`.
- Do not preserve compatibility with the old active 0.4.0 six-field aggregate manifest.

## Source Spec

Implement this spec:

- `docs/superpowers/specs/2026-05-27-create-structure-md-v040-detail-list-upgrade-design.md`

The upgraded active 0.4.0 manifest has exactly these eight top-level fields:

```json
{
  "document": "chapters/00-document.json",
  "overview": "chapters/01-overview.json",
  "quick_start": "chapters/02-quick-start.json",
  "architecture_overview": "chapters/03-architecture-overview.json",
  "main_flow_overview": "chapters/04-main-flow-overview.json",
  "main_flow_details": [
    "chapters/04-main-flow-details/init-flow.json"
  ],
  "module_overview": "chapters/05-module-overview.json",
  "module_details": [
    "chapters/05-module-details/storage.json"
  ]
}
```

Forbidden old active 0.4.0 aggregate paths:

- `chapters/04-main-flows.json`
- `chapters/05-module-details.json` as a single aggregate file

## File Structure

Modify:

- `SKILL.md`: create-interface-md-style orchestration for create-structure-md.
- `references/dsl-spec.md`: upgraded active 0.4.0 package, overview, and detail contract.
- `references/dsl-authoring-guide.md`: authoring rules for table overviews and one-detail-per-subagent files.
- `references/document-structure.md`: rendered section order and overview/detail placement.
- `references/review-checklist.md`: review gates for subagent-owned detail files.
- `references/mermaid-rules.md`: keep Mermaid guidance aligned with detail-file traversal.
- `scripts/v040_package.py`: upgraded manifest model, detail path validation, safe loading, key inference.
- `scripts/build_v040_chapter_schema.py`: schema builder for upgraded overview and detail shapes.
- `schemas/v0.4.0/structure.manifest.schema.json`: eight-field manifest schema.
- `schemas/v0.4.0/chapter.schema.json`: generated schema for static chapters, overviews, and details.
- `scripts/v040_schema.py`: schema validation over static chapter files and detail arrays.
- `scripts/v040_semantics.py`: overview-detail consistency, process metadata, warnings, and location checks.
- `scripts/v040_mermaid.py`: Mermaid traversal over static chapters and detail arrays.
- `scripts/v040_renderer.py`: fixed overview table rendering and detail rendering in manifest order.
- `scripts/validate_structure.py`: upgraded manifest dispatch and old aggregate migration error.
- `scripts/render_markdown.py`: render upgraded packages after validation.
- `tests/helpers_v040.py`: upgraded fixture writer.
- `tests/test_v040_manifest.py`: manifest and loader tests.
- `tests/test_v040_chapter_schema.py`: schema tests.
- `tests/test_v040_semantics.py`: semantic tests.
- `tests/test_v040_mermaid.py`: Mermaid traversal tests.
- `tests/test_v040_renderer.py`: renderer tests.
- `tests/test_v040_cli.py`: root CLI and single-detail validator tests.
- `tests/test_v040_docs.py`: reference/skill contract checks, updated after docs review.
- `tests/test_v040_e2e.py`: upgraded minimal package validation and render.
- `examples/minimal-reader-guide/structure.manifest.json`: upgraded manifest.
- `examples/minimal-reader-guide/chapters/04-main-flow-overview.json`: new Chapter 4 overview file.
- `examples/minimal-reader-guide/chapters/04-main-flow-details/init-flow.json`: new main-flow detail file.
- `examples/minimal-reader-guide/chapters/05-module-overview.json`: new Chapter 5 overview file.
- `examples/minimal-reader-guide/chapters/05-module-details/storage.json`: new module detail file.

Create:

- `scripts/validate_flow_detail.py`: validate one assigned main-flow detail file in package context.
- `scripts/validate_module_detail.py`: validate one assigned module detail file in package context.

Do not delete automatically:

- `examples/minimal-reader-guide/chapters/04-main-flows.json`
- `examples/minimal-reader-guide/chapters/05-module-details.json`

At final cleanup, print these commands for the user:

```bash
rm examples/minimal-reader-guide/chapters/04-main-flows.json
rm examples/minimal-reader-guide/chapters/05-module-details.json
```

## Task 1: Documentation Contract And Skill Workflow

**Nature:** Documentation-only. Review only; do not use TDD.

**Files:**

- Modify: `SKILL.md`
- Modify: `references/dsl-spec.md`
- Modify: `references/dsl-authoring-guide.md`
- Modify: `references/document-structure.md`
- Modify: `references/review-checklist.md`
- Modify: `references/mermaid-rules.md`

- [ ] **Step 1: Rewrite `SKILL.md` around main-agent orchestration**

Use these top-level sections:

```markdown
---
name: create-structure-md
description: Use when rendering, validating, or authoring a human-first repository reader guide from a create-structure-md 0.4.0 manifest package.
---

# create-structure-md

## Boundary
## Required Reading
## Input Shape
## Step-by-Step Workflow
## Main Agent Responsibilities
## Subagent Roles
## Acceptance Rules
## Rejection Rules
## Validate And Render
## References
```

Required content:

- State that `structure.manifest.json` and referenced child JSON files are authoritative.
- State that rendered Markdown is generated output.
- State that process records, subagent reports, command transcripts, rejected drafts, and scan logs stay outside JSON.
- State that the main agent owns package orchestration, dispatch briefs, contract loading, planning dispatch, ownership freeze dispatch, manifest creation, overview synthesis, validation, rendering, and final review.
- State that the main agent does not directly author substantive Chapter 4 or Chapter 5 detail prose.
- Require one authoring subagent per file under `chapters/04-main-flow-details/<flow-key>.json`.
- Require one authoring subagent per file under `chapters/05-module-details/<module-key>.json`.
- Require a separate adversarial review subagent for every accepted detail file.
- State that reviewers may modify only their assigned detail file.
- State that `main_flow_overview` and `module_overview` are synthesized after all detail files pass review.
- Use validation commands:

```bash
python scripts/validate_structure.py <package>/structure.manifest.json --strict
python scripts/validate_flow_detail.py <package>/chapters/04-main-flow-details/<flow-key>.json --package-root <package>
python scripts/validate_module_detail.py <package>/chapters/05-module-details/<module-key>.json --package-root <package>
python scripts/render_markdown.py <package>/structure.manifest.json
```

- [ ] **Step 2: Update `references/dsl-spec.md`**

Required sections:

```markdown
# create-structure-md 0.4.0 DSL 规范

## Package Shape
## Document Metadata
## Shared Blocks
## Overview
## Quick Start
## Architecture Overview
## Main Flow Overview
## Main Flow Detail
## Module Overview
## Module Detail
## Extra Subsections
## Validation Rules
```

Include JSON examples for:

- upgraded eight-field manifest
- `chapters/04-main-flow-overview.json`
- one `chapters/04-main-flow-details/<flow-key>.json`
- `chapters/05-module-overview.json`
- one `chapters/05-module-details/<module-key>.json`

State these constraints exactly:

- `main_flow_details` and `module_details` are non-empty arrays.
- detail keys are inferred from file stems.
- detail JSON does not repeat the inferred key.
- detail file stems match `^[a-z0-9][a-z0-9_-]*$`.
- overview rows match detail arrays in count and order.
- `main_flow_overview` and `module_overview` do not contain `blocks` or `extra_subsections`.
- neither overview file contains detail prose, Mermaid, code, examples, or process metadata.

- [ ] **Step 3: Update `references/dsl-authoring-guide.md`**

Required authoring guidance:

- The guide starts from reader questions rather than directory enumeration.
- Main-flow detail files describe reader-facing behavior paths, not call-chain dumps.
- Module detail files describe responsibility units, not source-file listings.
- Main-flow authoring subagents write exactly one assigned flow detail file.
- Module authoring subagents write exactly one assigned module detail file.
- `main_flow_overview` and `module_overview` are written only after details pass review.
- Overview tables are fixed table artifacts and must link to detail headings through `anchor`.
- Shared blocks remain `text`, `unordered_list`, `ordered_list`, `table`, `mermaid`, and `code`.
- List block `items` values are string arrays.
- Extra subsections use `key`, `title`, and `blocks`.

- [ ] **Step 4: Update rendered-structure and review references**

In `references/document-structure.md`, state this order:

```markdown
# <repository_name> 结构说明

## 入门
### 概述
### 快速开始

## 深入解析
### 架构概述
### 主线流程
#### <main_flow_details[].title>
### 模块详解
#### <module_details[].name>
##### <module_details[].mechanisms[].title>
```

In `references/review-checklist.md`, require checks for:

- upgraded eight-field manifest
- one-detail-per-subagent ownership
- separate adversarial detail review
- fixed overview table shape
- overview rows matching details
- old aggregate path rejection
- process metadata absence
- Mermaid readability
- module responsibility-unit fit
- main-flow behavior-path fit

In `references/mermaid-rules.md`, state that Mermaid blocks can appear in detail files and shared-block static chapters, but not in `main_flow_overview` or `module_overview`.

- [ ] **Step 5: Review documentation changes**

Run these review commands:

```bash
rg -n "main_flows|chapters/04-main-flows.json|intro_blocks|modules\\[\\]|module_details\\.modules|generated_module_object" SKILL.md references
rg -n "main_flow_overview|main_flow_details|module_overview|module_details|validate_flow_detail|validate_module_detail" SKILL.md references
```

Expected:

- The first command prints only historical mentions that are explicitly labeled as rejected old active 0.4.0 shape.
- The second command prints the upgraded contract and commands in `SKILL.md` and references.

- [ ] **Step 6: Commit documentation**

```bash
git add SKILL.md references/dsl-spec.md references/dsl-authoring-guide.md references/document-structure.md references/review-checklist.md references/mermaid-rules.md
git commit -m "docs: document v040 detail-list workflow"
```

## Task 2: Manifest Loader And Detail Package Model

**Nature:** Code and tests. Use TDD.

**Files:**

- Modify: `tests/helpers_v040.py`
- Modify: `tests/test_v040_manifest.py`
- Modify: `scripts/v040_package.py`
- Modify: `schemas/v0.4.0/structure.manifest.schema.json`

- [ ] **Step 1: Update fixture constants and write failing manifest tests**

In `tests/helpers_v040.py`, replace `FIXED_MANIFEST` with:

```python
FIXED_MANIFEST = {
    "document": "chapters/00-document.json",
    "overview": "chapters/01-overview.json",
    "quick_start": "chapters/02-quick-start.json",
    "architecture_overview": "chapters/03-architecture-overview.json",
    "main_flow_overview": "chapters/04-main-flow-overview.json",
    "main_flow_details": ["chapters/04-main-flow-details/init-flow.json"],
    "module_overview": "chapters/05-module-overview.json",
    "module_details": ["chapters/05-module-details/storage.json"],
}
```

Add these fixture objects:

```python
MAIN_FLOW_OVERVIEW = {
    "main_flow_overview": {
        "intro": "本章按读者最常遇到的行为路径说明仓库如何工作。",
        "flow_table": {
            "rows": [
                {
                    "flow": "初始化主线",
                    "purpose": "准备示例仓库能力并写入初始状态。",
                    "entry": "example_init",
                    "location": "src/api/init.py",
                    "anchor": "初始化主线",
                }
            ]
        },
    }
}

MAIN_FLOW_DETAIL = {
    "title": "初始化主线",
    "purpose": "准备示例仓库能力并写入初始状态。",
    "reader_goal": "读者想知道调用初始化入口后仓库内部发生什么。",
    "entry": {"name": "example_init", "location": "src/api/init.py"},
    "blocks": [{"type": "text", "content": "初始化入口协调读取配置和追加写入。"}],
    "extra_subsections": [],
}

MODULE_OVERVIEW = {
    "module_overview": {
        "intro": "本章按责任单元说明仓库的关键模块。",
        "module_table": {
            "rows": [
                {
                    "module": "存储模块",
                    "purpose": "保存初始化流程产生的示例状态。",
                    "location": "src/storage.py",
                    "anchor": "存储模块",
                }
            ]
        },
    }
}

MODULE_DETAIL = {
    "name": "存储模块",
    "location": "src/storage.py",
    "purpose": "保存初始化流程产生的示例状态。",
    "responsibilities": ["保存初始化结果", "提供追加写入机制"],
    "blocks": [{"type": "text", "content": "存储模块负责把初始化结果持久化到本地状态。"}],
    "mechanisms": [
        {
            "title": "追加写入",
            "blocks": [{"type": "text", "content": "追加写入保留已有记录并写入新的初始化结果。"}],
        }
    ],
    "extra_subsections": [],
}
```

Update `write_valid_package()` so it writes static chapters, both overview files, and all detail files from the manifest arrays.

In `tests/test_v040_manifest.py`, replace old aggregate expectations with:

```python
def test_loads_upgraded_manifest_with_detail_lists(self):
    with tempfile.TemporaryDirectory() as tmpdir:
        package = load_manifest_package(write_valid_package(tmpdir))

    self.assertEqual(set(FIXED_MANIFEST.keys()), set(package.manifest.keys()))
    self.assertEqual(["init-flow"], [detail.key for detail in package.main_flow_details])
    self.assertEqual(["storage"], [detail.key for detail in package.module_details])
    self.assertEqual("初始化主线", package.main_flow_details[0].data["title"])
    self.assertEqual("存储模块", package.module_details[0].data["name"])

def test_rejects_old_active_v040_aggregate_manifest(self):
    old_manifest = {
        "document": "chapters/00-document.json",
        "overview": "chapters/01-overview.json",
        "quick_start": "chapters/02-quick-start.json",
        "architecture_overview": "chapters/03-architecture-overview.json",
        "main_flows": "chapters/04-main-flows.json",
        "module_details": "chapters/05-module-details.json",
    }

    issues = manifest_shape_errors(old_manifest)

    self.assertHasIssue(
        issues,
        code="manifest.keys",
        path="$",
        message="active 0.4.0 manifest must use main_flow_overview",
    )

def test_rejects_empty_detail_arrays(self):
    for key in ["main_flow_details", "module_details"]:
        with self.subTest(key=key):
            manifest = dict(FIXED_MANIFEST)
            manifest[key] = []
            issues = manifest_shape_errors(manifest)
            self.assertHasIssue(
                issues,
                code="manifest.detail_array",
                path=f"$.{key}",
                message="must be a non-empty array",
            )

def test_rejects_forbidden_aggregate_detail_paths(self):
    cases = [
        ("main_flow_details", ["chapters/04-main-flows.json"]),
        ("module_details", ["chapters/05-module-details.json"]),
    ]
    for key, value in cases:
        with self.subTest(key=key):
            manifest = dict(FIXED_MANIFEST)
            manifest[key] = value
            issues = manifest_shape_errors(manifest)
            self.assertHasIssue(
                issues,
                code="manifest.forbidden_path",
                path=f"$.{key}[0]",
                message="old aggregate path is invalid",
            )

def test_rejects_invalid_detail_stems(self):
    manifest = dict(FIXED_MANIFEST)
    manifest["main_flow_details"] = ["chapters/04-main-flow-details/Bad-Key.json"]

    issues = manifest_shape_errors(manifest)

    self.assertHasIssue(
        issues,
        code="manifest.detail_key",
        path="$.main_flow_details[0]",
        message="file stem must match",
    )

def test_rejects_duplicate_manifest_paths(self):
    manifest = dict(FIXED_MANIFEST)
    manifest["module_details"] = ["chapters/04-main-flow-details/init-flow.json"]

    issues = manifest_shape_errors(manifest)

    self.assertHasIssue(
        issues,
        code="manifest.path_duplicate",
        path="$",
        message="manifest paths must be unique",
    )

def test_rejects_unsafe_manifest_paths(self):
    cases = [
        ("main_flow_details", ["/tmp/init-flow.json"]),
        ("main_flow_details", ["chapters/../init-flow.json"]),
        ("main_flow_details", ["chapters\\\\init-flow.json"]),
        ("main_flow_details", ["chapters//init-flow.json"]),
        ("main_flow_details", ["chapters/04-main-flow-details/init-flow.txt"]),
    ]
    for key, value in cases:
        with self.subTest(value=value):
            manifest = dict(FIXED_MANIFEST)
            manifest[key] = value
            issues = manifest_shape_errors(manifest)
            self.assertHasIssue(
                issues,
                code="manifest.path",
                path=f"$.{key}[0]",
                message="relative POSIX .json path",
            )
```

- [ ] **Step 2: Run manifest tests and confirm failure**

```bash
python -m unittest tests.test_v040_manifest -v
```

Expected: FAIL because `ManifestPackage` has no `main_flow_details` or `module_details`, old aggregate keys are still accepted, and new manifest keys are rejected.

- [ ] **Step 3: Implement the upgraded package model**

In `scripts/v040_package.py`, add imports:

```python
import re
from pathlib import Path, PurePosixPath
```

Replace `FIXED_MANIFEST` with:

```python
STATIC_MANIFEST = {
    "document": "chapters/00-document.json",
    "overview": "chapters/01-overview.json",
    "quick_start": "chapters/02-quick-start.json",
    "architecture_overview": "chapters/03-architecture-overview.json",
    "main_flow_overview": "chapters/04-main-flow-overview.json",
    "module_overview": "chapters/05-module-overview.json",
}

DETAIL_MANIFEST_KEYS = ("main_flow_details", "module_details")

FORBIDDEN_AGGREGATE_PATHS = {
    "chapters/04-main-flows.json",
    "chapters/05-module-details.json",
}

DETAIL_KEY_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
```

Add the detail dataclass:

```python
@dataclass(frozen=True)
class DetailFile:
    kind: str
    key: str
    relative_path: str
    path: Path
    data: dict
```

Update `ManifestPackage`:

```python
@dataclass(frozen=True)
class ManifestPackage:
    root_dir: Path
    manifest_path: Path
    manifest: dict
    chapters: dict
    main_flow_details: list[DetailFile]
    module_details: list[DetailFile]
```

Add path validation helpers:

```python
def _validate_manifest_path(value, path, issues):
    if not isinstance(value, str):
        issues.append(ValidationIssue("manifest.path", path, "manifest path must be a string"))
        return None
    if (
        Path(value).is_absolute()
        or "\\" in value
        or "//" in value
        or not value.endswith(".json")
        or "." in PurePosixPath(value).parts
        or ".." in PurePosixPath(value).parts
    ):
        issues.append(
            ValidationIssue(
                "manifest.path",
                path,
                "manifest path must be a relative POSIX .json path without '.', '..', backslashes, or duplicate slashes",
            )
        )
        return None
    if value in FORBIDDEN_AGGREGATE_PATHS:
        issues.append(
            ValidationIssue(
                "manifest.forbidden_path",
                path,
                f"old aggregate path is invalid in active 0.4.0: {value}",
            )
        )
        return None
    return value

def _detail_key(value):
    stem = PurePosixPath(value).stem
    if not DETAIL_KEY_RE.fullmatch(stem):
        return None
    return stem
```

In `manifest_shape_errors()`:

- Require `set(manifest.keys()) == set(STATIC_MANIFEST) | {"main_flow_details", "module_details"}`.
- Produce `manifest.keys` with a message containing `active 0.4.0 manifest must use main_flow_overview, main_flow_details, module_overview, and module_details`.
- Require static paths to equal `STATIC_MANIFEST`.
- Require detail arrays to be non-empty lists.
- Run `_validate_manifest_path()` for every manifest path.
- Reject duplicate relative paths with `manifest.path_duplicate`.
- Reject invalid detail stems with `manifest.detail_key`.

In `load_manifest_package()`, load static chapters into `chapters`, then load detail arrays:

```python
main_flow_details = _load_detail_files(root_dir, manifest, "main_flow_details")
module_details = _load_detail_files(root_dir, manifest, "module_details")
return ManifestPackage(root_dir, manifest_path, manifest, chapters, main_flow_details, module_details)
```

Add `_load_detail_files()`:

```python
def _load_detail_files(root_dir: Path, manifest: dict, kind: str) -> list[DetailFile]:
    details = []
    for relative_path in manifest[kind]:
        details.append(
            DetailFile(
                kind=kind,
                key=PurePosixPath(relative_path).stem,
                relative_path=relative_path,
                path=root_dir / relative_path,
                data=_read_json_file(root_dir / relative_path, relative_path),
            )
        )
    return details
```

- [ ] **Step 4: Update manifest schema**

Replace `schemas/v0.4.0/structure.manifest.schema.json` with an executable eight-field schema:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://create-structure-md.local/schemas/v0.4.0/structure.manifest.schema.json",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "document",
    "overview",
    "quick_start",
    "architecture_overview",
    "main_flow_overview",
    "main_flow_details",
    "module_overview",
    "module_details"
  ],
  "properties": {
    "document": {"const": "chapters/00-document.json"},
    "overview": {"const": "chapters/01-overview.json"},
    "quick_start": {"const": "chapters/02-quick-start.json"},
    "architecture_overview": {"const": "chapters/03-architecture-overview.json"},
    "main_flow_overview": {"const": "chapters/04-main-flow-overview.json"},
    "main_flow_details": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "string",
        "pattern": "^chapters/04-main-flow-details/[a-z0-9][a-z0-9_-]*\\.json$",
        "not": {"const": "chapters/04-main-flows.json"}
      }
    },
    "module_overview": {"const": "chapters/05-module-overview.json"},
    "module_details": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "string",
        "pattern": "^chapters/05-module-details/[a-z0-9][a-z0-9_-]*\\.json$",
        "not": {"const": "chapters/05-module-details.json"}
      }
    }
  }
}
```

- [ ] **Step 5: Run manifest tests and confirm pass**

```bash
python -m unittest tests.test_v040_manifest -v
```

Expected: PASS.

- [ ] **Step 6: Commit manifest model**

```bash
git add tests/helpers_v040.py tests/test_v040_manifest.py scripts/v040_package.py schemas/v0.4.0/structure.manifest.schema.json
git commit -m "feat: load v040 detail-list manifests"
```

## Task 3: Schema Validation For Overview And Detail Files

**Nature:** Code, schema, and tests. Use TDD.

**Files:**

- Modify: `tests/test_v040_chapter_schema.py`
- Modify: `scripts/build_v040_chapter_schema.py`
- Modify: `scripts/v040_schema.py`
- Modify: `schemas/v0.4.0/chapter.schema.json`

- [ ] **Step 1: Write failing schema tests**

Add these tests to `tests/test_v040_chapter_schema.py`:

```python
def test_main_flow_overview_accepts_fixed_table_only(self):
    self.assertValid(self.validate_package())

def test_main_flow_overview_rejects_blocks_and_extra_subsections(self):
    def mutate(root):
        data = _read(root / "chapters/04-main-flow-overview.json")
        data["main_flow_overview"]["blocks"] = [{"type": "text", "content": "detail prose"}]
        data["main_flow_overview"]["extra_subsections"] = []
        write_json(root / "chapters/04-main-flow-overview.json", data)

    result = self.validate_package(mutate)
    self.assertInvalidAt(result, "$.main_flow_overview")

def test_module_overview_rejects_mechanisms_and_detail_blocks(self):
    def mutate(root):
        data = _read(root / "chapters/05-module-overview.json")
        data["module_overview"]["mechanisms"] = []
        data["module_overview"]["blocks"] = [{"type": "text", "content": "detail prose"}]
        write_json(root / "chapters/05-module-overview.json", data)

    result = self.validate_package(mutate)
    self.assertInvalidAt(result, "$.module_overview")

def test_main_flow_detail_requires_reader_goal_and_extra_subsections(self):
    def mutate(root):
        data = _read(root / "chapters/04-main-flow-details/init-flow.json")
        del data["reader_goal"]
        del data["extra_subsections"]
        write_json(root / "chapters/04-main-flow-details/init-flow.json", data)

    result = self.validate_package(mutate)
    self.assertInvalidAt(result, "$.main_flow_details[0]")

def test_main_flow_detail_rejects_top_level_chapter(self):
    def mutate(root):
        data = _read(root / "chapters/04-main-flow-details/init-flow.json")
        data["chapter"] = "主线流程"
        write_json(root / "chapters/04-main-flow-details/init-flow.json", data)

    result = self.validate_package(mutate)
    self.assertInvalidAt(result, "$.main_flow_details[0]")

def test_module_detail_requires_responsibilities(self):
    def mutate(root):
        data = _read(root / "chapters/05-module-details/storage.json")
        data["responsibilities"] = []
        write_json(root / "chapters/05-module-details/storage.json", data)

    result = self.validate_package(mutate)
    self.assertInvalidAt(result, "$.module_details[0].responsibilities")

def test_module_detail_rejects_top_level_chapter(self):
    def mutate(root):
        data = _read(root / "chapters/05-module-details/storage.json")
        data["chapter"] = "模块详解"
        write_json(root / "chapters/05-module-details/storage.json", data)

    result = self.validate_package(mutate)
    self.assertInvalidAt(result, "$.module_details[0]")
```

- [ ] **Step 2: Run schema tests and confirm failure**

```bash
python -m unittest tests.test_v040_chapter_schema -v
```

Expected: FAIL because old schema definitions expect `main_flows` and aggregate `module_details.modules`.

- [ ] **Step 3: Update schema builder**

In `scripts/build_v040_chapter_schema.py`, remove old `MainFlowsChapter` and aggregate `ModuleDetailsChapter`. Add:

```python
def maybe_string():
    return {"type": "string"}

defs["OverviewIntro"] = string()

defs["MainFlowOverviewRow"] = obj(
    ["flow", "purpose", "entry", "location", "anchor"],
    {
        "flow": string(),
        "purpose": string(),
        "entry": string(),
        "location": maybe_string(),
        "anchor": string(),
    },
)
defs["MainFlowOverviewChapter"] = obj(
    ["main_flow_overview"],
    {
        "main_flow_overview": obj(
            ["flow_table"],
            {
                "intro": ref("OverviewIntro"),
                "flow_table": obj(["rows"], {"rows": array(ref("MainFlowOverviewRow"), min_items=1)}),
            },
        )
    },
)

defs["MainFlowDetail"] = obj(
    ["title", "purpose", "reader_goal", "entry", "blocks", "extra_subsections"],
    {
        "title": string(),
        "purpose": string(),
        "reader_goal": string(),
        "entry": ref("MainFlowEntry"),
        "blocks": block_array(),
        "extra_subsections": extra_subsections(),
    },
)

defs["ModuleOverviewRow"] = obj(
    ["module", "purpose", "location", "anchor"],
    {
        "module": string(),
        "purpose": string(),
        "location": string(),
        "anchor": string(),
    },
)
defs["ModuleOverviewChapter"] = obj(
    ["module_overview"],
    {
        "module_overview": obj(
            ["module_table"],
            {
                "intro": ref("OverviewIntro"),
                "module_table": obj(["rows"], {"rows": array(ref("ModuleOverviewRow"), min_items=1)}),
            },
        )
    },
)

defs["ModuleDetail"] = obj(
    ["name", "location", "purpose", "responsibilities", "blocks", "mechanisms", "extra_subsections"],
    {
        "name": string(),
        "location": string(),
        "purpose": string(),
        "responsibilities": array(string(), min_items=1),
        "blocks": block_array(),
        "mechanisms": array(ref("Mechanism")),
        "extra_subsections": extra_subsections(),
    },
)
```

Keep the existing `DocumentChapter`, `OverviewChapter`, `QuickStartChapter`, `ArchitectureOverviewChapter`, shared `Block`, `ExtraSubsection`, `MainFlowEntry`, and `Mechanism` definitions.

- [ ] **Step 4: Regenerate chapter schema**

```bash
python scripts/build_v040_chapter_schema.py
```

Expected stdout contains:

```text
wrote /home/hyx/create-structure-md/schemas/v0.4.0/chapter.schema.json
```

- [ ] **Step 5: Update schema validation routing**

In `scripts/v040_schema.py`, replace old key routing with:

```python
STATIC_CHAPTER_DEF_BY_KEY = {
    "document": "DocumentChapter",
    "overview": "OverviewChapter",
    "quick_start": "QuickStartChapter",
    "architecture_overview": "ArchitectureOverviewChapter",
    "main_flow_overview": "MainFlowOverviewChapter",
    "module_overview": "ModuleOverviewChapter",
}

DETAIL_DEF_BY_KIND = {
    "main_flow_details": "MainFlowDetail",
    "module_details": "ModuleDetail",
}
```

Update `schema_validation_result()`:

```python
def schema_validation_result(package: ManifestPackage) -> ValidationResult:
    result = ValidationResult()
    for key, def_name in STATIC_CHAPTER_DEF_BY_KEY.items():
        _validate_value(result, def_name, package.chapters[key], f"$.{key}")
    for index, detail in enumerate(package.main_flow_details):
        _validate_value(result, "MainFlowDetail", detail.data, f"$.main_flow_details[{index}]")
    for index, detail in enumerate(package.module_details):
        _validate_value(result, "ModuleDetail", detail.data, f"$.module_details[{index}]")
    return result

def _validate_value(result, def_name, value, path_prefix):
    validator = validator_for(def_name)
    errors = sorted(validator.iter_errors(value), key=lambda error: list(error.path))
    for error in errors:
        result.error("schema", _schema_error_path(path_prefix, error.path), error.message)
```

Update `_schema_error_path()` so it accepts a full path prefix:

```python
def _schema_error_path(path_prefix: str, path) -> str:
    if not path:
        return path_prefix
    return path_prefix + _json_path(path)[1:]
```

- [ ] **Step 6: Run schema tests and confirm pass**

```bash
python -m unittest tests.test_v040_chapter_schema -v
```

Expected: PASS.

- [ ] **Step 7: Commit schema work**

```bash
git add tests/test_v040_chapter_schema.py scripts/build_v040_chapter_schema.py scripts/v040_schema.py schemas/v0.4.0/chapter.schema.json
git commit -m "feat: validate v040 overview and detail files"
```

## Task 4: Minimal Example Package Migration

**Nature:** Example package and tests. Use TDD.

**Files:**

- Modify: `tests/test_v040_e2e.py`
- Modify: `examples/minimal-reader-guide/structure.manifest.json`
- Create: `examples/minimal-reader-guide/chapters/04-main-flow-overview.json`
- Create: `examples/minimal-reader-guide/chapters/04-main-flow-details/init-flow.json`
- Create: `examples/minimal-reader-guide/chapters/05-module-overview.json`
- Create: `examples/minimal-reader-guide/chapters/05-module-details/storage.json`

- [ ] **Step 1: Write failing e2e assertions for upgraded example shape**

In `tests/test_v040_e2e.py`, add:

```python
def test_example_manifest_uses_detail_list_shape(self):
    manifest = json.loads(EXAMPLE_MANIFEST.read_text(encoding="utf-8"))

    self.assertEqual(
        {
            "document",
            "overview",
            "quick_start",
            "architecture_overview",
            "main_flow_overview",
            "main_flow_details",
            "module_overview",
            "module_details",
        },
        set(manifest),
    )
    self.assertEqual(["chapters/04-main-flow-details/init-flow.json"], manifest["main_flow_details"])
    self.assertEqual(["chapters/05-module-details/storage.json"], manifest["module_details"])
    self.assertNotIn("main_flows", manifest)
```

Add `import json` at the top of the file.

- [ ] **Step 2: Run e2e tests and confirm failure**

```bash
python -m unittest tests.test_v040_e2e -v
```

Expected: FAIL because the checked-in example still uses `main_flows` and the old aggregate module file.

- [ ] **Step 3: Migrate `examples/minimal-reader-guide/structure.manifest.json`**

Use:

```json
{
  "document": "chapters/00-document.json",
  "overview": "chapters/01-overview.json",
  "quick_start": "chapters/02-quick-start.json",
  "architecture_overview": "chapters/03-architecture-overview.json",
  "main_flow_overview": "chapters/04-main-flow-overview.json",
  "main_flow_details": [
    "chapters/04-main-flow-details/init-flow.json"
  ],
  "module_overview": "chapters/05-module-overview.json",
  "module_details": [
    "chapters/05-module-details/storage.json"
  ]
}
```

- [ ] **Step 4: Add main-flow overview example**

Create `examples/minimal-reader-guide/chapters/04-main-flow-overview.json`:

```json
{
  "main_flow_overview": {
    "intro": "本章按读者最常遇到的行为路径说明仓库如何工作。",
    "flow_table": {
      "rows": [
        {
          "flow": "初始化主线",
          "purpose": "准备示例仓库能力并写入初始状态。",
          "entry": "example_init",
          "location": "src/api/init.py",
          "anchor": "初始化主线"
        }
      ]
    }
  }
}
```

- [ ] **Step 5: Add main-flow detail example**

Create `examples/minimal-reader-guide/chapters/04-main-flow-details/init-flow.json`:

```json
{
  "title": "初始化主线",
  "purpose": "准备示例仓库能力并写入初始状态。",
  "reader_goal": "读者想知道调用初始化入口后仓库内部发生什么。",
  "entry": {
    "name": "example_init",
    "location": "src/api/init.py"
  },
  "blocks": [
    {
      "type": "text",
      "content": "初始化入口协调读取配置和追加写入。"
    }
  ],
  "extra_subsections": []
}
```

- [ ] **Step 6: Add module overview example**

Create `examples/minimal-reader-guide/chapters/05-module-overview.json`:

```json
{
  "module_overview": {
    "intro": "本章按责任单元说明仓库的关键模块。",
    "module_table": {
      "rows": [
        {
          "module": "存储模块",
          "purpose": "保存初始化流程产生的示例状态。",
          "location": "src/storage.py",
          "anchor": "存储模块"
        }
      ]
    }
  }
}
```

- [ ] **Step 7: Add module detail example**

Create `examples/minimal-reader-guide/chapters/05-module-details/storage.json`:

```json
{
  "name": "存储模块",
  "location": "src/storage.py",
  "purpose": "保存初始化流程产生的示例状态。",
  "responsibilities": [
    "保存初始化结果",
    "提供追加写入机制"
  ],
  "blocks": [
    {
      "type": "text",
      "content": "存储模块负责把初始化结果持久化到本地状态。"
    }
  ],
  "mechanisms": [
    {
      "title": "追加写入",
      "blocks": [
        {
          "type": "text",
          "content": "追加写入保留已有记录并写入新的初始化结果。"
        }
      ]
    }
  ],
  "extra_subsections": []
}
```

- [ ] **Step 8: Run e2e tests and confirm pass**

```bash
python -m unittest tests.test_v040_e2e -v
```

Expected: PASS.

- [ ] **Step 9: Commit example migration**

```bash
git add tests/test_v040_e2e.py examples/minimal-reader-guide/structure.manifest.json examples/minimal-reader-guide/chapters/04-main-flow-overview.json examples/minimal-reader-guide/chapters/04-main-flow-details/init-flow.json examples/minimal-reader-guide/chapters/05-module-overview.json examples/minimal-reader-guide/chapters/05-module-details/storage.json
git commit -m "test: migrate minimal reader guide to detail lists"
```

## Task 5: Renderer Overview Tables And Detail Ordering

**Nature:** Code and tests. Use TDD.

**Files:**

- Modify: `tests/test_v040_renderer.py`
- Modify: `scripts/v040_renderer.py`

- [ ] **Step 1: Write failing renderer tests**

In `tests/test_v040_renderer.py`, replace old aggregate flow and module assertions with:

```python
def test_main_flow_overview_table_links_to_detail_heading(self):
    markdown = self.render_package()
    self.assertIn("| 主线 | 目的 | 入口 | 位置 |", markdown)
    self.assertIn(
        "| [初始化主线](#初始化主线) | 准备示例仓库能力并写入初始状态。 | `example_init` | src/api/init.py |",
        markdown,
    )
    self.assertLess(markdown.index("| 主线 | 目的 | 入口 | 位置 |"), markdown.index("#### 初始化主线"))

def test_module_overview_table_links_to_detail_heading(self):
    markdown = self.render_package()
    self.assertIn("| 模块 | 职责 | 位置 |", markdown)
    self.assertIn(
        "| [存储模块](#存储模块) | 保存初始化流程产生的示例状态。 | src/storage.py |",
        markdown,
    )
    self.assertLess(markdown.index("| 模块 | 职责 | 位置 |"), markdown.index("#### 存储模块"))

def test_detail_files_render_in_manifest_order(self):
    def mutate(root):
        manifest = _read(root / "structure.manifest.json")
        manifest["main_flow_details"].append("chapters/04-main-flow-details/render-flow.json")
        manifest["module_details"].append("chapters/05-module-details/render.json")
        write_json(root / "structure.manifest.json", manifest)
        write_json(
            root / "chapters/04-main-flow-details/render-flow.json",
            {
                "title": "渲染主线",
                "purpose": "渲染结构文档。",
                "reader_goal": "读者想知道验证通过后如何生成 Markdown。",
                "entry": {"name": "render_markdown", "location": "scripts/render_markdown.py"},
                "blocks": [{"type": "text", "content": "渲染入口读取已验证包并输出 Markdown。"}],
                "extra_subsections": [],
            },
        )
        flow_overview = _read(root / "chapters/04-main-flow-overview.json")
        flow_overview["main_flow_overview"]["flow_table"]["rows"].append(
            {
                "flow": "渲染主线",
                "purpose": "渲染结构文档。",
                "entry": "render_markdown",
                "location": "scripts/render_markdown.py",
                "anchor": "渲染主线",
            }
        )
        write_json(root / "chapters/04-main-flow-overview.json", flow_overview)
        write_json(
            root / "chapters/05-module-details/render.json",
            {
                "name": "渲染模块",
                "location": "scripts/v040_renderer.py",
                "purpose": "把结构包转换为 Markdown。",
                "responsibilities": ["渲染固定章节", "渲染详情文件"],
                "blocks": [{"type": "text", "content": "渲染模块按 manifest 顺序输出内容。"}],
                "mechanisms": [],
                "extra_subsections": [],
            },
        )
        module_overview = _read(root / "chapters/05-module-overview.json")
        module_overview["module_overview"]["module_table"]["rows"].append(
            {
                "module": "渲染模块",
                "purpose": "把结构包转换为 Markdown。",
                "location": "scripts/v040_renderer.py",
                "anchor": "渲染模块",
            }
        )
        write_json(root / "chapters/05-module-overview.json", module_overview)

    markdown = self.render_package(mutate)

    self.assertLess(markdown.index("#### 初始化主线"), markdown.index("#### 渲染主线"))
    self.assertLess(markdown.index("#### 存储模块"), markdown.index("#### 渲染模块"))
```

- [ ] **Step 2: Run renderer tests and confirm failure**

```bash
python -m unittest tests.test_v040_renderer -v
```

Expected: FAIL because renderer still reads `package.chapters["main_flows"]` and aggregate `module_details`.

- [ ] **Step 3: Update renderer chapter access**

In `scripts/v040_renderer.py`, replace:

```python
main_flows = package.chapters["main_flows"]["main_flows"]
module_details = package.chapters["module_details"]["module_details"]
```

with:

```python
main_flow_overview = package.chapters["main_flow_overview"]["main_flow_overview"]
module_overview = package.chapters["module_overview"]["module_overview"]
```

- [ ] **Step 4: Render Chapter 4 overview and details**

Replace the old Chapter 4 block with:

```python
renderer.heading(3, "主线流程")
if main_flow_overview.get("intro"):
    renderer.paragraph(main_flow_overview["intro"])
renderer.linked_fixed_table(
    ["主线", "目的", "入口", "位置"],
    main_flow_overview["flow_table"].get("rows", []),
    label_key="flow",
    anchor_key="anchor",
    value_keys=["purpose", "entry", "location"],
    code_keys={"entry"},
)
for detail in package.main_flow_details:
    flow = detail.data
    renderer.heading(4, flow["title"])
    renderer.paragraph(f'目的：{flow["purpose"]}')
    renderer.paragraph(f'读者目标：{flow["reader_goal"]}')
    renderer.paragraph(f'入口：`{flow["entry"]["name"]}`')
    if flow["entry"].get("location"):
        renderer.paragraph(f'位置：{flow["entry"]["location"]}')
    renderer.blocks(flow.get("blocks", []), 5)
    renderer.extra_subsections(5, flow["extra_subsections"])
```

- [ ] **Step 5: Render Chapter 5 overview and details**

Replace the old Chapter 5 block with:

```python
renderer.heading(3, "模块详解")
if module_overview.get("intro"):
    renderer.paragraph(module_overview["intro"])
renderer.linked_fixed_table(
    ["模块", "职责", "位置"],
    module_overview["module_table"].get("rows", []),
    label_key="module",
    anchor_key="anchor",
    value_keys=["purpose", "location"],
)
for detail in package.module_details:
    module = detail.data
    renderer.heading(4, module["name"])
    renderer.paragraph(f'位置：{module["location"]}')
    renderer.paragraph(f'职责：{module["purpose"]}')
    renderer.heading(5, "责任")
    renderer.unordered_list(module["responsibilities"])
    renderer.blocks(module.get("blocks", []), 5)
    for mechanism in module.get("mechanisms", []):
        renderer.heading(5, mechanism["title"])
        renderer.blocks(mechanism.get("blocks", []), 6)
    renderer.extra_subsections(5, module["extra_subsections"])
```

- [ ] **Step 6: Add renderer helpers**

Add to `_MarkdownRenderer`:

```python
def unordered_list(self, items):
    self._parts.append("\n".join(f"- {item}" for item in items))

def linked_fixed_table(self, columns, rows, *, label_key, anchor_key, value_keys, code_keys=None):
    code_keys = set(code_keys or ())
    rendered_rows = []
    for row in rows:
        label = _markdown_link(row[label_key], row[anchor_key])
        rendered = [label]
        for key in value_keys:
            value = row[key]
            if key in code_keys:
                value = f"`{value}`"
            rendered.append(value)
        rendered_rows.append(rendered)
    self.table(columns, rendered_rows)
```

Add module-level helper:

```python
def _markdown_link(label, anchor):
    href = "#" + str(anchor).strip().replace(" ", "-")
    return f"[{label}]({href})"
```

Keep `_escape_table_cell()` unchanged so table pipes and newlines remain safe.

- [ ] **Step 7: Run renderer tests and confirm pass**

```bash
python -m unittest tests.test_v040_renderer -v
```

Expected: PASS.

- [ ] **Step 8: Commit renderer work**

```bash
git add tests/test_v040_renderer.py scripts/v040_renderer.py
git commit -m "feat: render v040 overview tables and details"
```

## Task 6: Semantic Checks And Mermaid Traversal

**Nature:** Code and tests. Use TDD.

**Files:**

- Modify: `tests/test_v040_semantics.py`
- Modify: `tests/test_v040_mermaid.py`
- Modify: `scripts/v040_semantics.py`
- Modify: `scripts/v040_mermaid.py`

- [ ] **Step 1: Write failing semantic tests**

Add to `tests/test_v040_semantics.py`:

```python
def test_errors_when_flow_overview_rows_do_not_match_details(self):
    def mutate(root):
        data = _read(root / "chapters/04-main-flow-overview.json")
        data["main_flow_overview"]["flow_table"]["rows"][0]["flow"] = "错误主线"
        write_json(root / "chapters/04-main-flow-overview.json", data)

    result = self.validate(mutate)

    self.assertErrorCode(result, "semantics.main_flow_overview.mismatch")

def test_errors_when_module_overview_rows_do_not_match_details(self):
    def mutate(root):
        data = _read(root / "chapters/05-module-overview.json")
        data["module_overview"]["module_table"]["rows"][0]["anchor"] = "错误模块"
        write_json(root / "chapters/05-module-overview.json", data)

    result = self.validate(mutate)

    self.assertErrorCode(result, "semantics.module_overview.mismatch")

def test_warns_when_more_than_three_main_flow_detail_files_are_selected(self):
    def mutate(root):
        manifest = _read(root / "structure.manifest.json")
        rows = _read(root / "chapters/04-main-flow-overview.json")
        for index in range(1, 4):
            path = f"chapters/04-main-flow-details/flow-{index}.json"
            manifest["main_flow_details"].append(path)
            title = f"主线 {index}"
            write_json(
                root / path,
                {
                    "title": title,
                    "purpose": f"说明主线 {index}。",
                    "reader_goal": f"读者想理解主线 {index}。",
                    "entry": {"name": f"flow_{index}", "location": f"src/flow_{index}.py"},
                    "blocks": [],
                    "extra_subsections": [],
                },
            )
            rows["main_flow_overview"]["flow_table"]["rows"].append(
                {
                    "flow": title,
                    "purpose": f"说明主线 {index}。",
                    "entry": f"flow_{index}",
                    "location": f"src/flow_{index}.py",
                    "anchor": title,
                }
            )
        write_json(root / "structure.manifest.json", manifest)
        write_json(root / "chapters/04-main-flow-overview.json", rows)

    result = self.validate(mutate)

    self.assertWarningPath(result, "semantics.main_flows.too_many", "$.main_flow_details")
```

Update existing process metadata and file-only tests so paths use:

```python
"$.main_flow_details[0].purpose"
"$.module_details[0].purpose"
"$.module_details[0].mechanisms[0].title"
"$.module_details[0]"
```

- [ ] **Step 2: Write failing Mermaid traversal tests**

In `tests/test_v040_mermaid.py`, add or replace traversal assertions with:

```python
def test_traverses_mermaid_blocks_in_main_flow_details(self):
    with tempfile.TemporaryDirectory() as tmpdir:
        manifest = write_valid_package(tmpdir)
        data = _read(Path(tmpdir) / "chapters/04-main-flow-details/init-flow.json")
        data["blocks"].append(
            {
                "type": "mermaid",
                "title": "初始化流程",
                "diagram_type": "flowchart",
                "source": "flowchart LR\n  api[API] --> storage[存储]",
            }
        )
        write_json(Path(tmpdir) / "chapters/04-main-flow-details/init-flow.json", data)
        package = load_manifest_package(manifest)

        with mock.patch("scripts.v040_mermaid._locate_mermaid_cli", return_value=None):
            result = mermaid_validation_result(package)

    self.assertEqual("mermaid.cli_missing", result.errors[0].code)

def test_mermaid_error_path_mentions_detail_index(self):
    with tempfile.TemporaryDirectory() as tmpdir:
        manifest = write_valid_package(tmpdir)
        data = _read(Path(tmpdir) / "chapters/05-module-details/storage.json")
        data["blocks"].append(
            {
                "type": "mermaid",
                "title": "模块关系",
                "diagram_type": "flowchart",
                "source": "flowchart LR\n  A --> B",
            }
        )
        write_json(Path(tmpdir) / "chapters/05-module-details/storage.json", data)
        package = load_manifest_package(manifest)

        with mock.patch("scripts.v040_mermaid._locate_mermaid_cli", return_value="/bin/false"):
            result = mermaid_validation_result(package)

    self.assertTrue(
        any("$.module_details[0].blocks[1]" in issue.path for issue in result.errors),
        [issue.format() for issue in result.errors],
    )
```

- [ ] **Step 3: Run semantic and Mermaid tests and confirm failure**

```bash
python -m unittest tests.test_v040_semantics tests.test_v040_mermaid -v
```

Expected: FAIL because validators still walk aggregate Chapter 4 and Chapter 5 shapes.

- [ ] **Step 4: Implement overview consistency checks**

In `scripts/v040_semantics.py`, add:

```python
def _check_main_flow_overview(package, result):
    rows = package.chapters["main_flow_overview"]["main_flow_overview"]["flow_table"]["rows"]
    details = package.main_flow_details
    if len(rows) != len(details):
        result.error(
            "semantics.main_flow_overview.count",
            "$.main_flow_overview.main_flow_overview.flow_table.rows",
            "main-flow overview row count must match main_flow_details",
        )
        return
    for index, (row, detail) in enumerate(zip(rows, details)):
        flow = detail.data
        expected = {
            "flow": flow["title"],
            "purpose": flow["purpose"],
            "entry": flow["entry"]["name"],
            "location": flow["entry"].get("location", ""),
            "anchor": flow["title"],
        }
        actual = {key: row.get(key, "") for key in expected}
        if actual != expected:
            result.error(
                "semantics.main_flow_overview.mismatch",
                f"$.main_flow_overview.main_flow_overview.flow_table.rows[{index}]",
                f"main-flow overview row must match main_flow_details[{index}] metadata",
            )

def _check_module_overview(package, result):
    rows = package.chapters["module_overview"]["module_overview"]["module_table"]["rows"]
    details = package.module_details
    if len(rows) != len(details):
        result.error(
            "semantics.module_overview.count",
            "$.module_overview.module_overview.module_table.rows",
            "module overview row count must match module_details",
        )
        return
    for index, (row, detail) in enumerate(zip(rows, details)):
        module = detail.data
        expected = {
            "module": module["name"],
            "purpose": module["purpose"],
            "location": module["location"],
            "anchor": module["name"],
        }
        actual = {key: row.get(key, "") for key in expected}
        if actual != expected:
            result.error(
                "semantics.module_overview.mismatch",
                f"$.module_overview.module_overview.module_table.rows[{index}]",
                f"module overview row must match module_details[{index}] metadata",
            )
```

Call both functions from `semantic_validation_result()`.

- [ ] **Step 5: Update semantic walkers**

Replace aggregate walkers with:

```python
def _check_main_flow_count(package, result):
    if len(package.main_flow_details) > 3:
        result.warning(
            "semantics.main_flows.too_many",
            "$.main_flow_details",
            "reader guide should select at most three main flows",
        )

def _check_modules(package, result):
    for index, detail in enumerate(package.module_details):
        module = detail.data
        name = str(module.get("name", ""))
        purpose = str(module.get("purpose", ""))
        blocks = module.get("blocks", [])
        mechanisms = module.get("mechanisms", [])
        if _is_file_only_module(name, purpose, blocks, mechanisms):
            result.warning(
                "semantics.module.file_only",
                f"$.module_details[{index}]",
                "module entry looks like a file-only listing instead of a responsibility unit",
            )

def _iter_payloads(package):
    for chapter_key, chapter in package.chapters.items():
        yield f"$.{chapter_key}", chapter
    for index, detail in enumerate(package.main_flow_details):
        yield f"$.main_flow_details[{index}]", detail.data
    for index, detail in enumerate(package.module_details):
        yield f"$.module_details[{index}]", detail.data
```

Use `_iter_payloads()` in process metadata, Mermaid readability, and location checks.

- [ ] **Step 6: Add single-detail semantic helper**

In `scripts/v040_semantics.py`, add:

```python
def detail_semantic_validation_result(kind: str, index: int, data: dict) -> ValidationResult:
    result = ValidationResult()
    base_path = f"$.{kind}[{index}]"
    _check_process_metadata_value(data, base_path, result)
    _check_mermaid_readability_value(data, base_path, result)
    if kind == "module_details":
        name = str(data.get("name", ""))
        purpose = str(data.get("purpose", ""))
        blocks = data.get("blocks", [])
        mechanisms = data.get("mechanisms", [])
        if _is_file_only_module(name, purpose, blocks, mechanisms):
            result.warning(
                "semantics.module.file_only",
                base_path,
                "module entry looks like a file-only listing instead of a responsibility unit",
            )
    return result
```

Split the existing package-level helpers so package and single-detail validation share the same checks:

```python
def _check_process_metadata(package, result):
    for base_path, payload in _iter_payloads(package):
        _check_process_metadata_value(payload, base_path, result)

def _check_process_metadata_value(payload, base_path, result):
    for path, value in _walk(payload, base_path):
        if not isinstance(value, str):
            continue
        term = _process_metadata_term(value)
        if term:
            result.error(
                "semantics.process_metadata",
                path,
                f"reader-facing content must not include process metadata term: {term}",
            )

def _check_mermaid_readability(package, result):
    for base_path, payload in _iter_payloads(package):
        _check_mermaid_readability_value(payload, base_path, result)

def _check_mermaid_readability_value(payload, base_path, result):
    for path, block in _iter_mermaid_blocks_from_payload(payload, base_path):
        source = block.get("source", "")
        if re.match(r"^\s*graph\b", source):
            result.warning(
                "semantics.mermaid.legacy_graph",
                f"{path}.source",
                "Mermaid source should use flowchart instead of legacy graph syntax",
            )
        internal_label = _internal_visible_label(source)
        if internal_label:
            result.warning(
                "semantics.mermaid.internal_label",
                f"{path}.source",
                f"Mermaid visible label exposes internal id: {internal_label}",
            )

def _iter_mermaid_blocks_from_payload(payload, base_path):
    for path, value in _walk(payload, base_path):
        if isinstance(value, dict) and value.get("type") == "mermaid":
            yield path, value
```

- [ ] **Step 7: Update Mermaid traversal**

In `scripts/v040_mermaid.py`, replace `_iter_mermaid_blocks()` with:

```python
def _iter_mermaid_blocks(package):
    for base_path, payload in _iter_payloads(package):
        for path, value in _walk(payload, base_path):
            if isinstance(value, dict) and value.get("type") == "mermaid":
                yield path, value

def _iter_payloads(package):
    for chapter_key, chapter in package.chapters.items():
        yield f"$.{chapter_key}", chapter
    for index, detail in enumerate(package.main_flow_details):
        yield f"$.main_flow_details[{index}]", detail.data
    for index, detail in enumerate(package.module_details):
        yield f"$.module_details[{index}]", detail.data
```

- [ ] **Step 8: Add single-detail Mermaid helper**

In `scripts/v040_mermaid.py`, add:

```python
def mermaid_detail_validation_result(kind: str, index: int, data: dict) -> ValidationResult:
    result = ValidationResult()
    blocks = list(_iter_mermaid_blocks_from_payload(data, f"$.{kind}[{index}]"))
    if not blocks:
        return result

    mmdc = _locate_mermaid_cli()
    if mmdc is None:
        result.error(
            "mermaid.cli_missing",
            f"$.{kind}[{index}]",
            "Mermaid blocks require the mmdc CLI for strict rendering validation",
        )
        return result

    for path, block in blocks:
        _validate_mermaid_block(mmdc, path, block, result)
    return result

def _iter_mermaid_blocks_from_payload(payload, base_path):
    for path, value in _walk(payload, base_path):
        if isinstance(value, dict) and value.get("type") == "mermaid":
            yield path, value
```

- [ ] **Step 9: Run semantic and Mermaid tests and confirm pass**

```bash
python -m unittest tests.test_v040_semantics tests.test_v040_mermaid -v
```

Expected: PASS.

- [ ] **Step 10: Commit semantic and Mermaid work**

```bash
git add tests/test_v040_semantics.py tests/test_v040_mermaid.py scripts/v040_semantics.py scripts/v040_mermaid.py
git commit -m "feat: validate v040 detail semantics"
```

## Task 7: Root CLIs And Single-Detail Validators

**Nature:** Code and tests. Use TDD.

**Files:**

- Modify: `tests/test_v040_cli.py`
- Modify: `scripts/validate_structure.py`
- Modify: `scripts/render_markdown.py`
- Create: `scripts/validate_flow_detail.py`
- Create: `scripts/validate_module_detail.py`

- [ ] **Step 1: Write failing CLI tests**

In `tests/test_v040_cli.py`, add:

```python
def test_validate_cli_rejects_old_active_v040_aggregate_manifest_with_migration_message(self):
    with tempfile.TemporaryDirectory() as tmpdir:
        manifest = Path(tmpdir) / "structure.manifest.json"
        write_json(
            manifest,
            {
                "document": "chapters/00-document.json",
                "overview": "chapters/01-overview.json",
                "quick_start": "chapters/02-quick-start.json",
                "architecture_overview": "chapters/03-architecture-overview.json",
                "main_flows": "chapters/04-main-flows.json",
                "module_details": "chapters/05-module-details.json",
            },
        )
        stderr = io.StringIO()

        with contextlib.redirect_stderr(stderr):
            code = validate_cli.main([str(manifest), "--strict"])

    self.assertEqual(2, code)
    self.assertIn("breaking active 0.4.0 migration", stderr.getvalue())
    self.assertIn("main_flow_details", stderr.getvalue())

def test_validate_flow_detail_cli_accepts_one_assigned_file(self):
    from scripts import validate_flow_detail

    with tempfile.TemporaryDirectory() as tmpdir:
        manifest = write_valid_package(tmpdir)
        detail = Path(tmpdir) / "chapters/04-main-flow-details/init-flow.json"
        stdout = io.StringIO()

        with contextlib.redirect_stdout(stdout):
            code = validate_flow_detail.main([str(detail), "--package-root", str(Path(manifest).parent)])

    self.assertEqual(0, code)
    self.assertIn("Flow detail validation succeeded", stdout.getvalue())

def test_validate_module_detail_cli_accepts_one_assigned_file(self):
    from scripts import validate_module_detail

    with tempfile.TemporaryDirectory() as tmpdir:
        manifest = write_valid_package(tmpdir)
        detail = Path(tmpdir) / "chapters/05-module-details/storage.json"
        stdout = io.StringIO()

        with contextlib.redirect_stdout(stdout):
            code = validate_module_detail.main([str(detail), "--package-root", str(Path(manifest).parent)])

    self.assertEqual(0, code)
    self.assertIn("Module detail validation succeeded", stdout.getvalue())

def test_validate_flow_detail_cli_works_before_overview_files_exist(self):
    from scripts import validate_flow_detail

    with tempfile.TemporaryDirectory() as tmpdir:
        package_root = Path(tmpdir)
        write_json(
            package_root / "structure.manifest.json",
            {
                "document": "chapters/00-document.json",
                "overview": "chapters/01-overview.json",
                "quick_start": "chapters/02-quick-start.json",
                "architecture_overview": "chapters/03-architecture-overview.json",
                "main_flow_overview": "chapters/04-main-flow-overview.json",
                "main_flow_details": ["chapters/04-main-flow-details/init-flow.json"],
                "module_overview": "chapters/05-module-overview.json",
                "module_details": ["chapters/05-module-details/storage.json"],
            },
        )
        detail = package_root / "chapters/04-main-flow-details/init-flow.json"
        write_json(
            detail,
            {
                "title": "初始化主线",
                "purpose": "准备示例仓库能力并写入初始状态。",
                "reader_goal": "读者想知道调用初始化入口后仓库内部发生什么。",
                "entry": {"name": "example_init", "location": "src/api/init.py"},
                "blocks": [],
                "extra_subsections": [],
            },
        )
        stdout = io.StringIO()

        with contextlib.redirect_stdout(stdout):
            code = validate_flow_detail.main([str(detail), "--package-root", str(package_root)])

    self.assertEqual(0, code)
    self.assertIn("Flow detail validation succeeded", stdout.getvalue())

def test_validate_detail_cli_rejects_file_not_listed_in_manifest(self):
    from scripts import validate_flow_detail

    with tempfile.TemporaryDirectory() as tmpdir:
        manifest = write_valid_package(tmpdir)
        detail = Path(tmpdir) / "chapters/04-main-flow-details/unlisted.json"
        write_json(
            detail,
            {
                "title": "未列出主线",
                "purpose": "不应被接受。",
                "reader_goal": "读者不应看到未列出文件。",
                "entry": {"name": "unlisted"},
                "blocks": [],
                "extra_subsections": [],
            },
        )
        stderr = io.StringIO()

        with contextlib.redirect_stderr(stderr):
            code = validate_flow_detail.main([str(detail), "--package-root", str(Path(manifest).parent)])

    self.assertEqual(2, code)
    self.assertIn("$.main_flow_details", stderr.getvalue())

def test_validate_module_detail_cli_rejects_process_metadata(self):
    from scripts import validate_module_detail

    with tempfile.TemporaryDirectory() as tmpdir:
        manifest = write_valid_package(tmpdir)
        detail = Path(tmpdir) / "chapters/05-module-details/storage.json"
        data = json.loads(detail.read_text(encoding="utf-8"))
        data["purpose"] = "subagent report should not ship"
        write_json(detail, data)
        stderr = io.StringIO()

        with contextlib.redirect_stderr(stderr):
            code = validate_module_detail.main([str(detail), "--package-root", str(Path(manifest).parent)])

    self.assertEqual(2, code)
    self.assertIn("semantics.process_metadata", stderr.getvalue())
```

Add `import json` at the top of `tests/test_v040_cli.py`.

- [ ] **Step 2: Run CLI tests and confirm failure**

```bash
python -m unittest tests.test_v040_cli -v
```

Expected: FAIL because old active 0.4.0 is reported as unknown shape and the single-detail scripts do not exist.

- [ ] **Step 3: Update manifest dispatch**

In `scripts/validate_structure.py`, replace `V040_KEYS` with:

```python
V040_KEYS = {
    "document",
    "overview",
    "quick_start",
    "architecture_overview",
    "main_flow_overview",
    "main_flow_details",
    "module_overview",
    "module_details",
}

OLD_ACTIVE_V040_KEYS = {
    "document",
    "overview",
    "quick_start",
    "architecture_overview",
    "main_flows",
    "module_details",
}
```

Update `detect_manifest_version()`:

```python
if keys == OLD_ACTIVE_V040_KEYS:
    return "old-active-0.4.0"
```

Update `manifest_dispatch_result()`:

```python
if version == "old-active-0.4.0":
    return version, [
        ValidationIssue(
            "manifest.v040_migration",
            "$",
            "breaking active 0.4.0 migration required: replace main_flows/module_details aggregate files with main_flow_overview, main_flow_details, module_overview, and module_details",
        )
    ]
```

Update `_unknown_manifest_shape_issue()` so the supported active 0.4.0 keys list includes the eight upgraded keys.

- [ ] **Step 4: Add shared detail CLI helper**

Single-detail validators are strict for subagent handoff: schema errors, semantic errors, Mermaid rendering errors, and semantic warnings all return exit code `2`.

In `scripts/validate_flow_detail.py`, implement:

```python
#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.validate_structure import _print_issues
from scripts.v040_mermaid import mermaid_detail_validation_result
from scripts.v040_package import manifest_shape_errors
from scripts.v040_schema import validator_for
from scripts.v040_semantics import detail_semantic_validation_result
from scripts.v040_types import ValidationIssue, ValidationResult


def main(argv=None):
    parser = argparse.ArgumentParser(description="Validate one v040 main-flow detail file.")
    parser.add_argument("detail", help="Path to chapters/04-main-flow-details/<flow-key>.json")
    parser.add_argument("--package-root", required=True, help="Package root containing structure.manifest.json")
    args = parser.parse_args(argv)

    errors = validate_detail(args.detail, args.package_root)
    _print_issues(errors, sys.stderr)
    if errors:
        return 2
    print("Flow detail validation succeeded")
    return 0


def validate_detail(detail_path, package_root):
    package_root = Path(package_root)
    detail_path = Path(detail_path)
    try:
        manifest = json.loads((package_root / "structure.manifest.json").read_text(encoding="utf-8"))
    except FileNotFoundError:
        return [ValidationIssue("manifest.not_found", "$", f"manifest JSON file not found: {package_root / 'structure.manifest.json'}")]
    except json.JSONDecodeError as exc:
        return [ValidationIssue("manifest.json", "$", f"manifest JSON parse failed at line {exc.lineno}, column {exc.colno}")]

    manifest_errors = manifest_shape_errors(manifest)
    if manifest_errors:
        return manifest_errors

    try:
        relative = detail_path.resolve().relative_to(package_root.resolve()).as_posix()
    except ValueError:
        return [ValidationIssue("detail.path", "$.main_flow_details", "detail file must stay inside package root")]

    details = manifest["main_flow_details"]
    if relative not in details:
        return [ValidationIssue("detail.unlisted", "$.main_flow_details", f"detail file is not listed in manifest: {relative}")]

    index = details.index(relative)
    try:
        data = json.loads(detail_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return [ValidationIssue("detail.not_found", f"$.main_flow_details[{index}]", f"detail JSON file not found: {detail_path}")]
    except json.JSONDecodeError as exc:
        return [ValidationIssue("detail.json", f"$.main_flow_details[{index}]", f"detail JSON parse failed at line {exc.lineno}, column {exc.colno}")]

    result = ValidationResult()
    validator = validator_for("MainFlowDetail")
    for error in sorted(validator.iter_errors(data), key=lambda item: list(item.path)):
        result.error("schema", f"$.main_flow_details[{index}]", error.message)
    semantic_result = detail_semantic_validation_result("main_flow_details", index, data)
    mermaid_result = mermaid_detail_validation_result("main_flow_details", index, data)
    result.errors.extend(semantic_result.errors)
    result.errors.extend(mermaid_result.errors)
    result.warnings.extend(semantic_result.warnings)
    result.warnings.extend(mermaid_result.warnings)
    if result.warnings:
        result.errors.extend(result.warnings)
    return result.errors


if __name__ == "__main__":
    raise SystemExit(main())
```

Create `scripts/validate_module_detail.py`:

```python
#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.validate_structure import _print_issues
from scripts.v040_mermaid import mermaid_detail_validation_result
from scripts.v040_package import manifest_shape_errors
from scripts.v040_schema import validator_for
from scripts.v040_semantics import detail_semantic_validation_result
from scripts.v040_types import ValidationIssue, ValidationResult


def main(argv=None):
    parser = argparse.ArgumentParser(description="Validate one v040 module detail file.")
    parser.add_argument("detail", help="Path to chapters/05-module-details/<module-key>.json")
    parser.add_argument("--package-root", required=True, help="Package root containing structure.manifest.json")
    args = parser.parse_args(argv)

    errors = validate_detail(args.detail, args.package_root)
    _print_issues(errors, sys.stderr)
    if errors:
        return 2
    print("Module detail validation succeeded")
    return 0


def validate_detail(detail_path, package_root):
    package_root = Path(package_root)
    detail_path = Path(detail_path)
    try:
        manifest = json.loads((package_root / "structure.manifest.json").read_text(encoding="utf-8"))
    except FileNotFoundError:
        return [ValidationIssue("manifest.not_found", "$", f"manifest JSON file not found: {package_root / 'structure.manifest.json'}")]
    except json.JSONDecodeError as exc:
        return [ValidationIssue("manifest.json", "$", f"manifest JSON parse failed at line {exc.lineno}, column {exc.colno}")]

    manifest_errors = manifest_shape_errors(manifest)
    if manifest_errors:
        return manifest_errors

    try:
        relative = detail_path.resolve().relative_to(package_root.resolve()).as_posix()
    except ValueError:
        return [ValidationIssue("detail.path", "$.module_details", "detail file must stay inside package root")]

    details = manifest["module_details"]
    if relative not in details:
        return [ValidationIssue("detail.unlisted", "$.module_details", f"detail file is not listed in manifest: {relative}")]

    index = details.index(relative)
    try:
        data = json.loads(detail_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return [ValidationIssue("detail.not_found", f"$.module_details[{index}]", f"detail JSON file not found: {detail_path}")]
    except json.JSONDecodeError as exc:
        return [ValidationIssue("detail.json", f"$.module_details[{index}]", f"detail JSON parse failed at line {exc.lineno}, column {exc.colno}")]

    result = ValidationResult()
    validator = validator_for("ModuleDetail")
    for error in sorted(validator.iter_errors(data), key=lambda item: list(item.path)):
        result.error("schema", f"$.module_details[{index}]", error.message)
    semantic_result = detail_semantic_validation_result("module_details", index, data)
    mermaid_result = mermaid_detail_validation_result("module_details", index, data)
    result.errors.extend(semantic_result.errors)
    result.errors.extend(mermaid_result.errors)
    result.warnings.extend(semantic_result.warnings)
    result.warnings.extend(mermaid_result.warnings)
    if result.warnings:
        result.errors.extend(result.warnings)
    return result.errors


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 5: Run CLI tests and confirm pass**

```bash
python -m unittest tests.test_v040_cli -v
```

Expected: PASS.

- [ ] **Step 6: Commit CLI work**

```bash
git add tests/test_v040_cli.py scripts/validate_structure.py scripts/render_markdown.py scripts/validate_flow_detail.py scripts/validate_module_detail.py
git commit -m "feat: add v040 detail validation CLIs"
```

## Task 8: Documentation Regression Checks And Final Verification

**Nature:** Mixed. Update tests with TDD only where test code changes are needed; review documentation directly.

**Files:**

- Modify: `tests/test_v040_docs.py`
- Inspect: all files changed in Tasks 1-7.

- [ ] **Step 1: Write failing docs contract tests**

Update `tests/test_v040_docs.py` expected strings:

```python
def test_skill_mentions_detail_list_workflow_and_roles(self):
    content = (ROOT / "SKILL.md").read_text(encoding="utf-8")

    for expected in [
        "main_flow_overview",
        "main_flow_details",
        "module_overview",
        "module_details",
        "validate_flow_detail.py",
        "validate_module_detail.py",
        "accepted_main_flows",
        "accepted_modules",
        "review_decision: accept | changes_applied | reject_detail | split_required",
    ]:
        self.assertIn(expected, content)

def test_references_describe_fixed_overview_tables(self):
    spec = (ROOT / "references/dsl-spec.md").read_text(encoding="utf-8")
    authoring = (ROOT / "references/dsl-authoring-guide.md").read_text(encoding="utf-8")

    for expected in [
        "main_flow_overview",
        "flow_table",
        "module_overview",
        "module_table",
        "overview rows match detail arrays",
        "chapters/04-main-flows.json",
        "chapters/05-module-details.json",
        "old aggregate path",
    ]:
        self.assertIn(expected, spec + authoring)
```

- [ ] **Step 2: Run docs tests and confirm failure if references are incomplete**

```bash
python -m unittest tests.test_v040_docs -v
```

Expected: FAIL if documentation from Task 1 missed any required upgraded terms; PASS if Task 1 already covered them.

- [ ] **Step 3: Fix docs or tests to match the approved spec**

If tests fail because documentation lacks an approved term, update the relevant Markdown file. If tests fail because a string expectation is stricter than the approved wording, adjust the test to assert the approved concept using the actual wording from the Markdown.

- [ ] **Step 4: Run focused docs checks again**

```bash
python -m unittest tests.test_v040_docs -v
```

Expected: PASS.

- [ ] **Step 5: Run full verification**

```bash
python -m unittest tests.test_v040_manifest tests.test_v040_chapter_schema tests.test_v040_semantics tests.test_v040_mermaid tests.test_v040_renderer tests.test_v040_cli tests.test_v040_docs tests.test_v040_e2e -v
python scripts/validate_structure.py examples/minimal-reader-guide/structure.manifest.json --strict
python scripts/render_markdown.py examples/minimal-reader-guide/structure.manifest.json --output /tmp/minimal-reader-guide-v040.md
```

Expected:

- All `unittest` modules pass.
- Validation prints `Validation succeeded`.
- Render command prints `Document written: /tmp/minimal-reader-guide-v040.md`.

- [ ] **Step 6: Review generated Markdown**

Run:

```bash
sed -n '1,220p' /tmp/minimal-reader-guide-v040.md
```

Expected Markdown contains, in order:

```markdown
### 主线流程
| 主线 | 目的 | 入口 | 位置 |
#### 初始化主线
### 模块详解
| 模块 | 职责 | 位置 |
#### 存储模块
##### 责任
##### 追加写入
```

- [ ] **Step 7: Print cleanup commands for the user**

Do not run these commands. Print them for the user:

```bash
rm examples/minimal-reader-guide/chapters/04-main-flows.json
rm examples/minimal-reader-guide/chapters/05-module-details.json
```

- [ ] **Step 8: Commit final verification updates**

```bash
git add tests/test_v040_docs.py SKILL.md references/dsl-spec.md references/dsl-authoring-guide.md references/document-structure.md references/review-checklist.md references/mermaid-rules.md
git commit -m "test: cover v040 detail-list docs"
```

## Final Acceptance Checklist

- [ ] `SKILL.md` follows create-interface-md-style orchestration.
- [ ] Active 0.4.0 manifest is the upgraded eight-field shape.
- [ ] Old active 0.4.0 aggregate shape is rejected with a migration message.
- [ ] Each Chapter 4 main-flow detail file is independently authorable and reviewable.
- [ ] Each Chapter 5 module detail file is independently authorable and reviewable.
- [ ] `main_flow_overview` and `module_overview` render as fixed tables.
- [ ] Overview rows match detail arrays in count and order.
- [ ] Detail keys are inferred from safe file stems.
- [ ] Single-detail validation CLIs work for subagent handoff.
- [ ] Process metadata is rejected from JSON strings.
- [ ] Mermaid traversal includes all detail files.
- [ ] Minimal example validates and renders.
- [ ] Historical 0.3.0 dispatch still works.
- [ ] Documentation-only changes were reviewed.
- [ ] Code, schema, and example-package changes followed TDD.
