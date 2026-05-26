# create-structure-md Reader Guide Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the incompatible 0.4.0 reader-guide workflow for create-structure-md, replacing the rendered content model with `入门` and `深入解析` while preserving historical 0.3.0 files in place.

**Architecture:** Add focused 0.4.0 modules, schemas, examples, and tests beside the existing 0.3.0 implementation. Update the public validator and renderer CLIs to dispatch by manifest shape so old 0.3.0 packages still work during the transition, while `SKILL.md` and references document only the new reader-guide workflow.

**Tech Stack:** Python standard library, `jsonschema`, Mermaid CLI integration already used by 0.3.0, Markdown reference files, `unittest`.

---

## User Constraints

- Do not run deletion commands. If generated caches or obsolete files need cleanup, print the exact commands for the user to run.
- Text-only tasks do not use TDD. For those tasks, edit the Markdown files and run focused text checks.
- Code tasks use TDD: write failing tests first, run them to confirm the intended failure, implement the smallest code change, then run the tests again.
- Do not revert unrelated worktree changes. Read files before touching them and keep edits scoped.
- Historical 0.3.0 files may remain. Prefer adding 0.4.0 modules and version dispatch over destructive replacement.

## File Structure

Create:

- `docs/superpowers/plans/2026-05-26-create-structure-md-reader-guide-implementation.md`: this implementation plan.
- `references/dsl-authoring-guide.md`: canonical guidance for agents writing or reviewing the 0.4.0 DSL.
- `schemas/v0.4.0/structure.manifest.schema.json`: 0.4.0 manifest schema with the fixed six manifest keys.
- `schemas/v0.4.0/chapter.schema.json`: generated 0.4.0 child JSON schema.
- `scripts/build_v040_chapter_schema.py`: schema builder for shared block definitions and all 0.4.0 child documents.
- `scripts/v040_package.py`: manifest shape checks and package loader for fixed 0.4.0 paths.
- `scripts/v040_schema.py`: schema validation wrapper for 0.4.0 packages.
- `scripts/v040_semantics.py`: semantic checks that cannot be expressed cleanly in JSON Schema.
- `scripts/v040_mermaid.py`: Mermaid diagram extraction and validation for free content blocks.
- `scripts/v040_renderer.py`: Markdown renderer for the two-part reader guide.
- `tests/helpers_v040.py`: package fixtures for 0.4.0 tests.
- `tests/test_v040_manifest.py`: manifest shape and loader tests.
- `tests/test_v040_chapter_schema.py`: block and section schema tests.
- `tests/test_v040_semantics.py`: semantic reader-guide checks.
- `tests/test_v040_mermaid.py`: Mermaid block checks.
- `tests/test_v040_renderer.py`: renderer output and section-order tests.
- `tests/test_v040_docs.py`: reference and skill contract tests.
- `tests/test_v040_e2e.py`: validate-render CLI tests for a sample 0.4.0 package.
- `examples/minimal-reader-guide/structure.manifest.json`: sample 0.4.0 manifest.
- `examples/minimal-reader-guide/chapters/00-document.json`: sample document metadata.
- `examples/minimal-reader-guide/chapters/01-overview.json`: sample overview chapter.
- `examples/minimal-reader-guide/chapters/02-quick-start.json`: sample quick-start chapter.
- `examples/minimal-reader-guide/chapters/03-architecture-overview.json`: sample architecture chapter.
- `examples/minimal-reader-guide/chapters/04-main-flows.json`: sample main-flows chapter.
- `examples/minimal-reader-guide/chapters/05-module-details.json`: sample module-details chapter.

Modify:

- `SKILL.md`: rewrite from a 0.3.0 render wrapper into the 0.4.0 orchestration workflow.
- `references/dsl-spec.md`: replace the old eight-chapter contract with the 0.4.0 reader-guide DSL.
- `references/document-structure.md`: document the rendered two-part section order.
- `references/review-checklist.md`: align review criteria with reader-guide quality.
- `references/mermaid-rules.md`: keep only rules that apply to free Mermaid blocks, if the current file names 0.3.0-only chapter locations.
- `scripts/render_markdown.py`: dispatch to 0.3.0 or 0.4.0 implementation based on manifest keys.
- `scripts/validate_structure.py`: dispatch to 0.3.0 or 0.4.0 implementation based on manifest keys.

## Shared 0.4.0 Data Model

The new manifest keys are exactly:

```python
V040_MANIFEST_KEYS = {
    "document",
    "overview",
    "quick_start",
    "architecture_overview",
    "main_flows",
    "module_details",
}
```

The fixed manifest paths are:

```json
{
  "document": "chapters/00-document.json",
  "overview": "chapters/01-overview.json",
  "quick_start": "chapters/02-quick-start.json",
  "architecture_overview": "chapters/03-architecture-overview.json",
  "main_flows": "chapters/04-main-flows.json",
  "module_details": "chapters/05-module-details.json"
}
```

The renderer owns these visible headings:

```markdown
# <repository_name> 结构说明

## 入门
### 概述
#### 当前仓库介绍
#### 解决的问题
#### 主要功能
#### 核心组件
### 快速开始
#### 使用场景
#### 准备工作
#### 第一次运行/接入
#### 最小示例
#### 预期结果

## 深入解析
### 架构概述
#### 架构总览
#### 软件分层
#### 模块划分
#### 目录角色
### 主线流程
### 模块详解
```

Each module under `module_details.modules[]` renders as its own fourth-level subsection below `### 模块详解`. Mechanisms render inside their owning module as fifth-level subsections.

## Task 1: Rewrite Skill And References

**Nature:** Text-only. Do not use TDD for this task.

**Files:**

- Modify: `SKILL.md`
- Create: `references/dsl-authoring-guide.md`
- Modify: `references/dsl-spec.md`
- Modify: `references/document-structure.md`
- Modify: `references/review-checklist.md`
- Modify: `references/mermaid-rules.md`

- [ ] **Step 1: Rewrite `SKILL.md` as a 0.4.0 orchestration workflow**

Use these top-level sections:

```markdown
---
name: create-structure-md
description: Render, validate, and quality-review one human-first repository reader guide from a prepared create-structure-md 0.4.0 manifest package.
---

# create-structure-md

## Boundary
## Required Reading
## Input Shape
## Workflow
## Subagent Roles
## Acceptance Rules
## Rejection Rules
## Validate And Render
## References
```

Required content:

- State that authoritative deliverables are `structure.manifest.json` plus child JSON files.
- State that rendered Markdown is generated from accepted DSL content.
- State that repository understanding, subagent reports, command transcripts, rejected drafts, and process logs stay outside the DSL.
- State that the main agent owns package orchestration, cross-section consistency, validation, rendering, and final review.
- State that subagents may draft bounded analysis or one module object, but their reports are not renderable deliverables.
- Link required reading in this order:
  `references/dsl-spec.md`, `references/dsl-authoring-guide.md`, `references/document-structure.md`, `references/review-checklist.md`.
- Include the nine-step workflow from the approved spec:
  confirm inputs, read contract, capture dispatch brief, plan repository content, review and freeze outline, draft bounded content, run adversarial review, accept or reject DSL, validate/render/review.
- Include concise subagent output contracts for repository planning, structure review, module-detail authoring, and adversarial review.
- In `Validate And Render`, use:

```bash
python scripts/validate_structure.py <package>/structure.manifest.json --strict
python scripts/render_markdown.py <package>/structure.manifest.json
```

- [ ] **Step 2: Create `references/dsl-authoring-guide.md`**

Use exactly these headings:

```markdown
# create-structure-md DSL 编写指南

## 总原则
## 内容块使用规则
## 概述怎么写
## 快速开始怎么写
## 架构概述怎么写
## 主线流程怎么写
## 模块详解怎么写
## 不要写什么
## 写完检查
```

Required guidance:

- Explain that the guide starts from reader questions, not from directory enumeration.
- Explain block selection:
  text for narrative, unordered lists for parallel facts, ordered lists for ordered actions, tables for compact comparison, Mermaid for relationships or flow, code for minimal concrete usage.
- State that list blocks use `items: string[]` only and do not support `details`.
- State that fixed subsections do not carry `key` or `title`.
- State that only extra subsections carry `key`, `title`, and `blocks`.
- State that `core_components` begins with one `component_table`, then optional free blocks.
- State that `first_run.steps[]` is ordered by array position and each step contains free blocks.
- State that `main_flows.flows[]` has no `steps`; explain flows through free blocks.
- State that mechanisms live inside module objects.
- Include concrete rejection guidance for file-list dumps, call-chain dumps, API-reference drift, process metadata, and unsupported block shapes.

- [ ] **Step 3: Replace `references/dsl-spec.md` with the 0.4.0 contract**

Required sections:

```markdown
# create-structure-md 0.4.0 DSL 规范

## Package Shape
## Document Metadata
## Shared Blocks
## Overview
## Quick Start
## Architecture Overview
## Main Flows
## Module Details
## Extra Subsections
## Validation Rules
```

Include JSON examples for every child file. The document metadata object must be:

```json
{
  "document": {
    "repository_name": "示例仓库",
    "output_file": "Example_STRUCTURE_DESIGN.md",
    "summary": "一个用于演示 create-structure-md 0.4.0 的最小仓库说明。"
  }
}
```

- [ ] **Step 4: Replace `references/document-structure.md`**

Document only the visible rendered structure from this plan. Explicitly say:

- `## 入门` contains `### 概述` and `### 快速开始`.
- `## 深入解析` contains `### 架构概述`, `### 主线流程`, and `### 模块详解`.
- Fixed subsection titles are owned by the renderer.
- Extra subsections render after fixed content in array order.
- Module subsections are generated from `module_details.modules[]`.

- [ ] **Step 5: Replace `references/review-checklist.md`**

Use checklist items grouped by:

```markdown
# create-structure-md Review Checklist

## Contract
## 入门
## 深入解析
## Blocks
## Subagent Hygiene
## Final Render
```

The checklist must reject:

- overview that contains setup steps or module mechanisms;
- quick start that becomes a platform encyclopedia;
- architecture overview that explains module internals;
- main flows that become function-by-function call graphs;
- module details that become file-by-file listings or API reference pages;
- JSON containing subagent names, command transcripts, raw scan logs, or rejected drafts.

- [ ] **Step 6: Adjust `references/mermaid-rules.md` only where it names old chapter slots**

Keep existing Mermaid quality rules that still apply:

- prefer `flowchart` over legacy `graph`;
- human-readable labels;
- no internal IDs in visible labels;
- diagrams explain relationships or behavior paths.

Remove references to fixed 0.3.0 chapter fields such as `directory_relationships.diagram`, `layer_diagram`, `mainline.detail_diagram`, and mechanism root diagrams.

- [ ] **Step 7: Run text checks**

Run:

```bash
rg -n "0\\.4\\.0|入门|深入解析|dsl-authoring-guide|repository planning|module-detail authoring" SKILL.md references
```

Expected:

- Matches appear in `SKILL.md`.
- Matches appear in `references/dsl-authoring-guide.md`.
- Matches appear in `references/dsl-spec.md`.
- No reference file claims the active skill is 0.3.0.

Run:

```bash
git diff --check -- SKILL.md references/dsl-authoring-guide.md references/dsl-spec.md references/document-structure.md references/review-checklist.md references/mermaid-rules.md
```

Expected:

- No whitespace errors.

- [ ] **Step 8: Commit text-only contract work**

Run:

```bash
git add SKILL.md references/dsl-authoring-guide.md references/dsl-spec.md references/document-structure.md references/review-checklist.md references/mermaid-rules.md
git commit -m "docs: document reader guide workflow"
```

Expected:

- Commit succeeds.

## Task 2: Add 0.4.0 Manifest Loader

**Nature:** Code. Use TDD.

**Files:**

- Create: `tests/helpers_v040.py`
- Create: `tests/test_v040_manifest.py`
- Create: `scripts/v040_package.py`
- Create: `schemas/v0.4.0/structure.manifest.schema.json`

- [ ] **Step 1: Write fixture helpers**

Create `tests/helpers_v040.py` with concrete helpers and a complete valid fixture. The fixture should use only supported 0.4.0 keys and should include one block of every shared block type across the package.

Key constants:

```python
FIXED_MANIFEST = {
    "document": "chapters/00-document.json",
    "overview": "chapters/01-overview.json",
    "quick_start": "chapters/02-quick-start.json",
    "architecture_overview": "chapters/03-architecture-overview.json",
    "main_flows": "chapters/04-main-flows.json",
    "module_details": "chapters/05-module-details.json",
}
```

Helper functions:

```python
def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_valid_package(root):
    root = Path(root)
    write_json(root / "structure.manifest.json", FIXED_MANIFEST)
    write_json(root / FIXED_MANIFEST["document"], DOCUMENT)
    write_json(root / FIXED_MANIFEST["overview"], OVERVIEW)
    write_json(root / FIXED_MANIFEST["quick_start"], QUICK_START)
    write_json(root / FIXED_MANIFEST["architecture_overview"], ARCHITECTURE_OVERVIEW)
    write_json(root / FIXED_MANIFEST["main_flows"], MAIN_FLOWS)
    write_json(root / FIXED_MANIFEST["module_details"], MODULE_DETAILS)
    return root / "structure.manifest.json"
```

Fixture content must include:

- `DOCUMENT["document"]["repository_name"] == "示例仓库"`
- `DOCUMENT["document"]["output_file"] == "Example_STRUCTURE_DESIGN.md"`
- one overview component row: `{"component": "公共 API", "role": "提供调用入口。", "location": "include/example.h"}`
- one quick-start step titled `初始化仓库能力`
- one layer row, one module row, one main flow, and one module with one mechanism.

- [ ] **Step 2: Write failing manifest tests**

Create `tests/test_v040_manifest.py` with tests for:

```python
class V040ManifestTests(unittest.TestCase):
    def test_loads_fixed_manifest(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = write_valid_package(tmpdir)
            package = load_manifest_package(manifest_path)
        self.assertEqual("structure.manifest.json", package.manifest_path.name)
        self.assertEqual(set(FIXED_MANIFEST.keys()), set(package.manifest.keys()))
        self.assertEqual("示例仓库", package.chapters["document"]["document"]["repository_name"])

    def test_manifest_rejects_030_keys(self):
        manifest = dict(FIXED_MANIFEST)
        manifest["repository_overview"] = manifest.pop("overview")
        issues = manifest_shape_errors(manifest)
        self.assertTrue(any("0.4.0 manifest keys" in issue.message for issue in issues))

    def test_manifest_rejects_dsl_version(self):
        manifest = dict(FIXED_MANIFEST)
        manifest["dsl_version"] = "0.4.0"
        issues = manifest_shape_errors(manifest)
        self.assertTrue(any("must not contain dsl_version" in issue.message for issue in issues))

    def test_manifest_paths_must_be_exact_fixed_values(self):
        manifest = dict(FIXED_MANIFEST)
        manifest["overview"] = "chapters/overview.json"
        issues = manifest_shape_errors(manifest)
        self.assertTrue(any("must equal chapters/01-overview.json" in issue.message for issue in issues))

    def test_manifest_schema_rejects_wrong_root_type(self):
        schema = json.loads((ROOT / "schemas/v0.4.0/structure.manifest.schema.json").read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        errors = list(Draft202012Validator(schema).iter_errors([]))
        self.assertTrue(errors)
```

Imports:

```python
from scripts.v040_package import load_manifest_package, manifest_shape_errors
from tests.helpers_v040 import FIXED_MANIFEST, write_valid_package
```

- [ ] **Step 3: Run manifest tests to confirm failure**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.test_v040_manifest -v
```

Expected:

- Fails because `scripts.v040_package` or `schemas/v0.4.0/structure.manifest.schema.json` does not exist.

- [ ] **Step 4: Implement `schemas/v0.4.0/structure.manifest.schema.json`**

Schema contract:

- root type object;
- exactly the six fixed properties;
- no additional properties;
- every property is a string with the exact fixed path value;
- no `dsl_version`.

Use JSON Schema `const` for each value:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://example.local/create-structure-md/v0.4.0/structure.manifest.schema.json",
  "title": "create-structure-md 0.4.0 manifest",
  "type": "object",
  "required": [
    "document",
    "overview",
    "quick_start",
    "architecture_overview",
    "main_flows",
    "module_details"
  ],
  "additionalProperties": false,
  "properties": {
    "document": { "const": "chapters/00-document.json" },
    "overview": { "const": "chapters/01-overview.json" },
    "quick_start": { "const": "chapters/02-quick-start.json" },
    "architecture_overview": { "const": "chapters/03-architecture-overview.json" },
    "main_flows": { "const": "chapters/04-main-flows.json" },
    "module_details": { "const": "chapters/05-module-details.json" }
  }
}
```

- [ ] **Step 5: Implement `scripts/v040_package.py`**

Implementation shape:

```python
from dataclasses import dataclass
import json
from pathlib import Path


FIXED_MANIFEST = {
    "document": "chapters/00-document.json",
    "overview": "chapters/01-overview.json",
    "quick_start": "chapters/02-quick-start.json",
    "architecture_overview": "chapters/03-architecture-overview.json",
    "main_flows": "chapters/04-main-flows.json",
    "module_details": "chapters/05-module-details.json",
}


@dataclass(frozen=True)
class ValidationIssue:
    path: str
    message: str
    severity: str = "ERROR"

    def format(self) -> str:
        return f"{self.severity}: {self.path}: {self.message}"


@dataclass(frozen=True)
class ManifestPackage:
    root_dir: Path
    manifest_path: Path
    manifest: dict
    chapters: dict


def manifest_shape_errors(manifest):
    issues = []
    if not isinstance(manifest, dict):
        return [ValidationIssue("$", "manifest root must be an object")]
    if "dsl_version" in manifest:
        issues.append(ValidationIssue("$.dsl_version", "structure.manifest.json must not contain dsl_version"))
    if set(manifest.keys()) != set(FIXED_MANIFEST.keys()):
        issues.append(ValidationIssue("$", "manifest must contain exactly the 0.4.0 manifest keys"))
    for key, expected in FIXED_MANIFEST.items():
        if key in manifest and manifest[key] != expected:
            issues.append(ValidationIssue(f"$.{key}", f"must equal {expected}"))
    return issues


def _read_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"file not found: {path}") from exc
    except IsADirectoryError as exc:
        raise ValueError(f"expected JSON file but found directory: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON at {path}:{exc.lineno}:{exc.colno}: {exc.msg}") from exc


def load_manifest_package(manifest_path):
    manifest_path = Path(manifest_path)
    manifest = _read_json(manifest_path)
    issues = manifest_shape_errors(manifest)
    if issues:
        raise ValueError("\n".join(issue.format() for issue in issues))
    root_dir = manifest_path.parent
    chapters = {}
    for key, rel_path in FIXED_MANIFEST.items():
        chapters[key] = _read_json(root_dir / rel_path)
    return ManifestPackage(root_dir=root_dir, manifest_path=manifest_path, manifest=manifest, chapters=chapters)
```

- [ ] **Step 6: Run manifest tests**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.test_v040_manifest -v
```

Expected:

- All tests in `tests.test_v040_manifest` pass.

- [ ] **Step 7: Commit manifest foundation**

Run:

```bash
git add tests/helpers_v040.py tests/test_v040_manifest.py scripts/v040_package.py schemas/v0.4.0/structure.manifest.schema.json
git commit -m "feat: add reader guide manifest loader"
```

Expected:

- Commit succeeds.

## Task 3: Add 0.4.0 Chapter Schema And Schema Validator

**Nature:** Code. Use TDD.

**Files:**

- Create: `tests/test_v040_chapter_schema.py`
- Create: `scripts/build_v040_chapter_schema.py`
- Create: `schemas/v0.4.0/chapter.schema.json`
- Create: `scripts/v040_schema.py`

- [ ] **Step 1: Write failing schema tests**

Create `tests/test_v040_chapter_schema.py` with tests for:

```python
class V040ChapterSchemaTests(unittest.TestCase):
    def load_schema(self):
        schema_path = ROOT / "schemas/v0.4.0/chapter.schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        return schema

    def validate_package(self, mutator=None):
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = write_valid_package(tmpdir)
            if mutator:
                mutator(Path(tmpdir))
            package = load_manifest_package(manifest_path)
            return schema_validation_result(package)

    def test_valid_fixture_passes_schema(self):
        result = self.validate_package()
        self.assertFalse(result.errors)

    def test_rejects_unknown_block_type(self):
        def mutate(root):
            path = root / FIXED_MANIFEST["overview"]
            data = json.loads(path.read_text(encoding="utf-8"))
            data["overview"]["repository_intro"]["blocks"].append({"type": "details", "content": "bad"})
            write_json(path, data)
        result = self.validate_package(mutate)
        self.assertTrue(any("details" in issue.message for issue in result.errors))

    def test_list_items_are_strings(self):
        def mutate(root):
            path = root / FIXED_MANIFEST["overview"]
            data = json.loads(path.read_text(encoding="utf-8"))
            data["overview"]["main_capabilities"]["blocks"] = [
                {"type": "unordered_list", "items": [{"text": "bad"}]}
            ]
            write_json(path, data)
        result = self.validate_package(mutate)
        self.assertTrue(any("is not of type 'string'" in issue.message for issue in result.errors))

    def test_core_component_rows_have_semantic_fields_only(self):
        def mutate(root):
            path = root / FIXED_MANIFEST["overview"]
            data = json.loads(path.read_text(encoding="utf-8"))
            data["overview"]["core_components"]["component_table"]["rows"][0]["notes"] = "bad"
            write_json(path, data)
        result = self.validate_package(mutate)
        self.assertTrue(any("Additional properties are not allowed" in issue.message for issue in result.errors))

    def test_first_run_steps_are_required(self):
        def mutate(root):
            path = root / FIXED_MANIFEST["quick_start"]
            data = json.loads(path.read_text(encoding="utf-8"))
            data["quick_start"]["first_run"]["steps"] = []
            write_json(path, data)
        result = self.validate_package(mutate)
        self.assertTrue(any("$.quick_start.first_run.steps" in issue.path for issue in result.errors))

    def test_main_flows_are_required(self):
        def mutate(root):
            path = root / FIXED_MANIFEST["main_flows"]
            data = json.loads(path.read_text(encoding="utf-8"))
            data["main_flows"]["flows"] = []
            write_json(path, data)
        result = self.validate_package(mutate)
        self.assertTrue(any("$.main_flows.flows" in issue.path for issue in result.errors))

    def test_module_details_are_required(self):
        def mutate(root):
            path = root / FIXED_MANIFEST["module_details"]
            data = json.loads(path.read_text(encoding="utf-8"))
            data["module_details"]["modules"] = []
            write_json(path, data)
        result = self.validate_package(mutate)
        self.assertTrue(any("$.module_details.modules" in issue.path for issue in result.errors))
```

- [ ] **Step 2: Run schema tests to confirm failure**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.test_v040_chapter_schema -v
```

Expected:

- Fails because `scripts.v040_schema` or `schemas/v0.4.0/chapter.schema.json` does not exist.

- [ ] **Step 3: Implement `scripts/build_v040_chapter_schema.py`**

The builder should emit one schema with `$defs` for:

- `text_block`
- `unordered_list_block`
- `ordered_list_block`
- `table_block`
- `mermaid_block`
- `code_block`
- `block`
- `blocks`
- `extra_subsection`
- `block_section`

Block rules:

- every block object has `type`;
- text has `content`;
- ordered and unordered lists have `items` as non-empty string arrays;
- table has `columns: string[]` and `rows: string[][]`;
- Mermaid has `title`, `diagram_type`, and `source`;
- code has `language` and `content`, with optional `title`.

Chapter roots:

- `document` object has `repository_name`, `output_file`, optional `summary`.
- `overview` contains the four fixed sections and `extra_subsections`.
- `quick_start` contains five fixed sections and `extra_subsections`; `first_run.steps` has at least one item.
- `architecture_overview` contains four fixed sections and `extra_subsections`.
- `main_flows` contains `flow_overview`, non-empty `flows`, and `extra_subsections`.
- `module_details` contains `intro_blocks`, non-empty `modules`, and `extra_subsections`.

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python scripts/build_v040_chapter_schema.py
```

Expected:

- Writes `schemas/v0.4.0/chapter.schema.json`.

- [ ] **Step 4: Implement `scripts/v040_schema.py`**

Use the existing 0.3.0 result style where possible. Required public function:

```python
def schema_validation_result(package) -> ValidationResult:
    ...
```

The function must:

- load `schemas/v0.4.0/chapter.schema.json`;
- validate each child document independently;
- prefix diagnostics with the child key, for example `$.overview.repository_intro.blocks[0]`;
- return `ValidationResult(errors=[...], warnings=[])`;
- avoid traceback output for user-facing CLI callers by returning structured issues.

- [ ] **Step 5: Run schema tests**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.test_v040_chapter_schema -v
```

Expected:

- All schema tests pass.

- [ ] **Step 6: Commit schema work**

Run:

```bash
git add tests/test_v040_chapter_schema.py scripts/build_v040_chapter_schema.py scripts/v040_schema.py schemas/v0.4.0/chapter.schema.json
git commit -m "feat: add reader guide chapter schema"
```

Expected:

- Commit succeeds.

## Task 4: Add Semantic And Mermaid Checks

**Nature:** Code. Use TDD.

**Files:**

- Create: `tests/test_v040_semantics.py`
- Create: `tests/test_v040_mermaid.py`
- Create: `scripts/v040_semantics.py`
- Create: `scripts/v040_mermaid.py`

- [ ] **Step 1: Write failing semantic tests**

Create `tests/test_v040_semantics.py` with tests for:

```python
class V040SemanticTests(unittest.TestCase):
    def validate(self, mutator=None, strict_repo_root=None):
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = write_valid_package(tmpdir)
            if mutator:
                mutator(Path(tmpdir))
            package = load_manifest_package(manifest_path)
            return semantic_validation_result(package, repo_root=strict_repo_root)

    def test_valid_fixture_has_no_errors(self):
        result = self.validate()
        self.assertFalse(result.errors)

    def test_warns_when_more_than_three_main_flows(self):
        def mutate(root):
            path = root / FIXED_MANIFEST["main_flows"]
            data = json.loads(path.read_text(encoding="utf-8"))
            flow = data["main_flows"]["flows"][0]
            data["main_flows"]["flows"] = [dict(flow, title=f"流程{i}") for i in range(4)]
            write_json(path, data)
        result = self.validate(mutate)
        self.assertTrue(any("one to three" in issue.message for issue in result.warnings))

    def test_warns_when_module_looks_like_single_file_listing(self):
        def mutate(root):
            path = root / FIXED_MANIFEST["module_details"]
            data = json.loads(path.read_text(encoding="utf-8"))
            data["module_details"]["modules"][0]["name"] = "example.c"
            data["module_details"]["modules"][0]["purpose"] = "这个文件包含函数。"
            write_json(path, data)
        result = self.validate(mutate)
        self.assertTrue(any("responsibility unit" in issue.message for issue in result.warnings))

    def test_errors_when_process_metadata_appears(self):
        def mutate(root):
            path = root / FIXED_MANIFEST["overview"]
            data = json.loads(path.read_text(encoding="utf-8"))
            data["overview"]["extra_subsections"] = [
                {"key": "agent_report", "title": "Subagent Report", "blocks": [{"type": "text", "content": "raw command transcript"}]}
            ]
            write_json(path, data)
        result = self.validate(mutate)
        self.assertTrue(any("process metadata" in issue.message for issue in result.errors))
```

The process-metadata scan should look for lower-case terms such as `subagent report`, `command transcript`, `raw scan log`, and `rejected draft` in extra subsection titles or text block content.

- [ ] **Step 2: Write failing Mermaid tests**

Create `tests/test_v040_mermaid.py` with tests for:

```python
class V040MermaidTests(unittest.TestCase):
    def validate(self, mutator=None):
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = write_valid_package(tmpdir)
            if mutator:
                mutator(Path(tmpdir))
            package = load_manifest_package(manifest_path)
            return mermaid_validation_result(package)

    def test_valid_fixture_has_no_errors(self):
        result = self.validate()
        self.assertFalse(result.errors)

    def test_rejects_legacy_graph_keyword(self):
        def mutate(root):
            path = root / FIXED_MANIFEST["overview"]
            data = json.loads(path.read_text(encoding="utf-8"))
            data["overview"]["repository_intro"]["blocks"] = [
                {"type": "mermaid", "title": "旧图", "diagram_type": "flowchart", "source": "graph LR\n  a[应用] --> b[库]"}
            ]
            write_json(path, data)
        result = self.validate(mutate)
        self.assertTrue(any("legacy graph" in issue.message for issue in result.errors))

    def test_warns_when_label_exposes_internal_id(self):
        def mutate(root):
            path = root / FIXED_MANIFEST["main_flows"]
            data = json.loads(path.read_text(encoding="utf-8"))
            data["main_flows"]["flows"][0]["blocks"] = [
                {"type": "mermaid", "title": "内部 ID", "diagram_type": "flowchart", "source": "flowchart LR\n  api[storage_core] --> user[使用者]"}
            ]
            write_json(path, data)
        result = self.validate(mutate)
        self.assertTrue(any("internal id" in issue.message for issue in result.warnings))
```

- [ ] **Step 3: Run semantic and Mermaid tests to confirm failure**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.test_v040_semantics tests.test_v040_mermaid -v
```

Expected:

- Fails because `scripts.v040_semantics` and `scripts.v040_mermaid` do not exist.

- [ ] **Step 4: Implement `scripts/v040_semantics.py`**

Required public function:

```python
def semantic_validation_result(package, repo_root=None) -> ValidationResult:
    ...
```

Checks:

- warn if `len(main_flows.flows) > 3`;
- warn if a module name ends with `.c`, `.h`, `.py`, `.js`, `.ts`, `.java`, `.go`, or `.rs` and its purpose uses file-only wording such as `file`, `文件`, `contains`, or `包含`;
- error if text content or extra subsection titles include process-metadata terms:
  `subagent report`, `command transcript`, `raw scan log`, `rejected draft`, `repo-understand log`, `执行记录`;
- optionally check source-like `location` strings against `repo_root` only when `repo_root` is provided, using warnings for missing paths.

- [ ] **Step 5: Implement `scripts/v040_mermaid.py`**

Required public function:

```python
def mermaid_validation_result(package) -> ValidationResult:
    ...
```

Implementation requirements:

- recursively walk all dicts/lists in all child documents;
- collect objects with `type == "mermaid"`;
- error when `source.lstrip().startswith("graph ")`;
- warn when bracket labels contain snake-case or kebab-case identifiers that look internal, for example `[storage_core]` or `[init-flow]`;
- if 0.3.0 already shells out to Mermaid CLI behind a helper, reuse the same availability behavior so missing Mermaid CLI does not break ordinary unit tests.

- [ ] **Step 6: Run semantic and Mermaid tests**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.test_v040_semantics tests.test_v040_mermaid -v
```

Expected:

- All semantic and Mermaid tests pass.

- [ ] **Step 7: Commit semantic checks**

Run:

```bash
git add tests/test_v040_semantics.py tests/test_v040_mermaid.py scripts/v040_semantics.py scripts/v040_mermaid.py
git commit -m "feat: check reader guide semantics"
```

Expected:

- Commit succeeds.

## Task 5: Add Renderer And CLI Version Dispatch

**Nature:** Code. Use TDD.

**Files:**

- Create: `tests/test_v040_renderer.py`
- Modify: `scripts/render_markdown.py`
- Modify: `scripts/validate_structure.py`
- Create: `scripts/v040_renderer.py`

- [ ] **Step 1: Write failing renderer tests**

Create `tests/test_v040_renderer.py` with tests for:

```python
EXPECTED_HEADINGS = [
    "# 示例仓库结构说明",
    "## 入门",
    "### 概述",
    "#### 当前仓库介绍",
    "#### 解决的问题",
    "#### 主要功能",
    "#### 核心组件",
    "### 快速开始",
    "#### 使用场景",
    "#### 准备工作",
    "#### 第一次运行/接入",
    "#### 最小示例",
    "#### 预期结果",
    "## 深入解析",
    "### 架构概述",
    "#### 架构总览",
    "#### 软件分层",
    "#### 模块划分",
    "#### 目录角色",
    "### 主线流程",
    "### 模块详解",
]


class V040RendererTests(unittest.TestCase):
    def render_fixture(self):
        tmpdir = tempfile.TemporaryDirectory()
        manifest = write_valid_package(tmpdir.name)
        package = load_manifest_package(manifest)
        return tmpdir, render_markdown(package)

    def test_renders_reader_guide_headings_in_order(self):
        tmpdir, markdown = self.render_fixture()
        with tmpdir:
            positions = [markdown.index(heading) for heading in EXPECTED_HEADINGS]
        self.assertEqual(sorted(positions), positions)

    def test_renders_core_component_table_before_blocks(self):
        tmpdir, markdown = self.render_fixture()
        with tmpdir:
            table_pos = markdown.index("| 组件 | 作用 | 位置 |")
            text_pos = markdown.index("公共 API 是最小调用入口。")
        self.assertLess(table_pos, text_pos)
        self.assertIn("| 公共 API | 提供调用入口。 | include/example.h |", markdown)

    def test_renders_quick_start_steps_as_ordered_blocks(self):
        tmpdir, markdown = self.render_fixture()
        with tmpdir:
            self.assertIn("##### 1. 初始化仓库能力", markdown)
            self.assertIn("调用初始化入口。", markdown)

    def test_renders_main_flow_without_step_heading(self):
        tmpdir, markdown = self.render_fixture()
        with tmpdir:
            self.assertIn("#### 初始化主线", markdown)
            self.assertIn("入口：`example_init`", markdown)
            self.assertNotIn("##### 1. ", markdown.split("### 主线流程", 1)[1].split("### 模块详解", 1)[0])

    def test_renders_module_mechanisms_inside_module(self):
        tmpdir, markdown = self.render_fixture()
        with tmpdir:
            module_pos = markdown.index("#### 存储模块")
            mechanism_pos = markdown.index("##### 追加写入")
        self.assertLess(module_pos, mechanism_pos)
```

- [ ] **Step 2: Write failing CLI dispatch tests**

Add tests to `tests/test_v040_renderer.py`:

```python
class V040CliDispatchTests(unittest.TestCase):
    def test_render_cli_writes_v040_default_output(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest = write_valid_package(tmpdir)
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                code = render_cli.main([str(manifest)])
        self.assertEqual(0, code)
        self.assertTrue((Path(tmpdir) / "Example_STRUCTURE_DESIGN.md").exists())
        self.assertIn("Document written:", stdout.getvalue())

    def test_validate_cli_accepts_v040_package(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest = write_valid_package(tmpdir)
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                code = validate_cli.main([str(manifest)])
        self.assertEqual(0, code)
        self.assertIn("Validation succeeded", stdout.getvalue())
```

Also keep a 0.3.0 regression test by importing `tests.helpers_v030.write_valid_package` and verifying both CLIs still return zero for a 0.3.0 package.

- [ ] **Step 3: Run renderer tests to confirm failure**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.test_v040_renderer -v
```

Expected:

- Fails because `scripts.v040_renderer` and CLI dispatch are absent.

- [ ] **Step 4: Implement `scripts/v040_renderer.py`**

Required public function:

```python
def render_markdown(package) -> str:
    ...
```

Renderer helpers:

- `_render_blocks(blocks, level)` renders shared blocks in order.
- `_render_table(columns, rows)` escapes pipe characters in cell strings.
- `_render_extra_subsections(extra_subsections, heading_level)` renders `title` only and never renders `key`.
- `_render_block_section(title, section, heading_level)` renders fixed section headings plus blocks.
- `_render_steps(steps)` renders quick-start steps as fifth-level headings under `#### 第一次运行/接入`.

Required block output:

- text: paragraph;
- unordered list: `- item`;
- ordered list: `1. item`, `2. item`;
- table: Markdown table using `columns` and `rows`;
- Mermaid: optional title heading at current block level, then fenced `mermaid`;
- code: optional title heading at current block level, then fenced language block.

Required fixed table output:

```markdown
| 组件 | 作用 | 位置 |
| --- | --- | --- |
```

```markdown
| 层 | 作用 | 位置 |
| --- | --- | --- |
```

```markdown
| 模块 | 作用 | 所在层 | 位置 |
| --- | --- | --- | --- |
```

Main flow rendering:

- each flow renders as `#### <title>`;
- render `purpose` as a paragraph;
- render `entry.name` as ``入口：`<name>` ``;
- if `entry.location` exists, render ``位置：`<location>` ``;
- render free blocks after the entry metadata;
- do not create step headings for main flows.

Module rendering:

- render each module as `#### <name>`;
- render `位置：` and `职责：` paragraphs;
- render module `blocks`;
- render each mechanism as `##### <title>` followed by mechanism blocks;
- render module extra subsections after mechanisms.

- [ ] **Step 5: Update CLI dispatch in `scripts/validate_structure.py`**

Add a manifest-shape detector:

```python
V030_KEYS = {
    "document",
    "repository_overview",
    "directory_map",
    "module_layers",
    "repository_mainline",
    "key_mechanisms",
    "integration_boundaries",
    "risks_validation",
}

V040_KEYS = {
    "document",
    "overview",
    "quick_start",
    "architecture_overview",
    "main_flows",
    "module_details",
}


def detect_manifest_version(manifest):
    if not isinstance(manifest, dict):
        return "unknown"
    keys = set(manifest.keys())
    if keys == V030_KEYS:
        return "0.3.0"
    if keys == V040_KEYS:
        return "0.4.0"
    return "unknown"
```

Dispatch behavior:

- keep existing 0.3.0 imports available;
- import 0.4.0 modules with aliases;
- reject `dsl_version` before dispatch;
- for unknown shape, print a clear error mentioning the accepted 0.3.0 and 0.4.0 key sets;
- run the selected package loader, schema checks, semantic checks, and Mermaid checks.

- [ ] **Step 6: Update CLI dispatch in `scripts/render_markdown.py`**

Use the same detector and selected validators as `validate_structure.py`. The default output path for 0.4.0 comes from:

```python
package.chapters["document"]["document"]["output_file"]
```

Keep the existing output-path containment check. Render with `scripts.v030_renderer.render_markdown` for 0.3.0 packages and `scripts.v040_renderer.render_markdown` for 0.4.0 packages.

- [ ] **Step 7: Run renderer and CLI tests**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.test_v040_renderer tests.test_v030_renderer tests.test_v030_manifest -v
```

Expected:

- New 0.4.0 renderer tests pass.
- Existing 0.3.0 renderer and manifest tests continue to pass.

- [ ] **Step 8: Commit renderer and dispatch**

Run:

```bash
git add tests/test_v040_renderer.py scripts/v040_renderer.py scripts/render_markdown.py scripts/validate_structure.py
git commit -m "feat: render reader guide packages"
```

Expected:

- Commit succeeds.

## Task 6: Add Example Package And End-To-End Tests

**Nature:** Code and data. Use TDD for CLI behavior; data files are created to satisfy those tests.

**Files:**

- Create: `tests/test_v040_e2e.py`
- Create: `tests/test_v040_docs.py`
- Create: `examples/minimal-reader-guide/structure.manifest.json`
- Create: `examples/minimal-reader-guide/chapters/00-document.json`
- Create: `examples/minimal-reader-guide/chapters/01-overview.json`
- Create: `examples/minimal-reader-guide/chapters/02-quick-start.json`
- Create: `examples/minimal-reader-guide/chapters/03-architecture-overview.json`
- Create: `examples/minimal-reader-guide/chapters/04-main-flows.json`
- Create: `examples/minimal-reader-guide/chapters/05-module-details.json`

- [ ] **Step 1: Write failing end-to-end tests**

Create `tests/test_v040_e2e.py`:

```python
class V040EndToEndTests(unittest.TestCase):
    def test_example_package_validates_strictly(self):
        manifest = ROOT / "examples/minimal-reader-guide/structure.manifest.json"
        completed = subprocess.run(
            [PYTHON, str(ROOT / "scripts/validate_structure.py"), str(manifest), "--strict"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertIn("Validation succeeded", completed.stdout)

    def test_example_package_renders_expected_sections(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "rendered.md"
            manifest = ROOT / "examples/minimal-reader-guide/structure.manifest.json"
            completed = subprocess.run(
                [PYTHON, str(ROOT / "scripts/render_markdown.py"), str(manifest), "--output", str(output)],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(0, completed.returncode, completed.stderr)
            markdown = output.read_text(encoding="utf-8")
        self.assertIn("## 入门", markdown)
        self.assertIn("### 快速开始", markdown)
        self.assertIn("### 模块详解", markdown)
        self.assertIn("| 组件 | 作用 | 位置 |", markdown)
```

- [ ] **Step 2: Write failing docs tests**

Create `tests/test_v040_docs.py`:

```python
class V040DocsTests(unittest.TestCase):
    def read(self, rel):
        return (ROOT / rel).read_text(encoding="utf-8")

    def test_skill_points_to_new_authoring_guide(self):
        skill = self.read("SKILL.md")
        self.assertIn("references/dsl-authoring-guide.md", skill)
        self.assertIn("0.4.0", skill)
        self.assertIn("repository_identity", skill)
        self.assertIn("generated_module_object", skill)

    def test_authoring_guide_has_required_headings(self):
        guide = self.read("references/dsl-authoring-guide.md")
        for heading in [
            "## 总原则",
            "## 内容块使用规则",
            "## 概述怎么写",
            "## 快速开始怎么写",
            "## 架构概述怎么写",
            "## 主线流程怎么写",
            "## 模块详解怎么写",
            "## 不要写什么",
            "## 写完检查",
        ]:
            self.assertIn(heading, guide)

    def test_old_eight_chapter_language_is_not_active_contract(self):
        spec = self.read("references/dsl-spec.md")
        self.assertIn("## Overview", spec)
        self.assertIn("## Module Details", spec)
        self.assertNotIn("key_mechanisms", spec)
        self.assertNotIn("risks_validation", spec)
```

- [ ] **Step 3: Run end-to-end and docs tests to confirm failure**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.test_v040_e2e tests.test_v040_docs -v
```

Expected:

- Fails because the example package and updated docs are not complete yet.

- [ ] **Step 4: Create `examples/minimal-reader-guide` package**

Use the same fixed manifest values from `tests/helpers_v040.py`.

The sample should render a small but complete guide:

- repository name: `示例仓库`;
- overview explains a C library that exposes an initialization API and a storage module;
- quick start has one or two steps;
- architecture overview has one layer row and one module row;
- main flows has one flow named `初始化主线`;
- module details has one module named `存储模块` and one mechanism named `追加写入`.

Keep prose short. Include one Mermaid block in a fixture only if `scripts/v040_mermaid.py` accepts it under strict mode.

- [ ] **Step 5: Run end-to-end and docs tests**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.test_v040_e2e tests.test_v040_docs -v
```

Expected:

- End-to-end validation passes in strict mode.
- Rendering writes the requested output file.
- Docs tests pass.

- [ ] **Step 6: Commit example and E2E coverage**

Run:

```bash
git add tests/test_v040_e2e.py tests/test_v040_docs.py examples/minimal-reader-guide
git commit -m "test: cover reader guide workflow"
```

Expected:

- Commit succeeds.

## Task 7: Final Verification

**Nature:** Verification. No deletion commands.

**Files:**

- Read: working tree status
- Read: all files touched by prior tasks

- [ ] **Step 1: Run focused 0.4.0 tests**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.test_v040_manifest tests.test_v040_chapter_schema tests.test_v040_semantics tests.test_v040_mermaid tests.test_v040_renderer tests.test_v040_docs tests.test_v040_e2e -v
```

Expected:

- All 0.4.0 tests pass.

- [ ] **Step 2: Run existing 0.3.0 regression tests**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.test_v030_manifest tests.test_v030_chapter_schema tests.test_v030_semantics tests.test_v030_mermaid tests.test_v030_renderer tests.test_v030_docs tests.test_v030_e2e tests.test_v030_scaffold -v
```

Expected:

- Existing 0.3.0 tests pass.

- [ ] **Step 3: Run the full unittest suite**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -v
```

Expected:

- Full suite passes.

- [ ] **Step 4: Check Markdown and Python whitespace**

Run:

```bash
git diff --check
```

Expected:

- No whitespace errors.

- [ ] **Step 5: Inspect worktree without deleting generated files**

Run:

```bash
git status --short
```

Expected:

- Only intended source, schema, test, example, and reference files are modified or untracked.
- If Python cache files appear, do not remove them. Tell the user the cleanup command they can run, for example:

```bash
find scripts tests -type d -name __pycache__ -prune -print
```

- [ ] **Step 6: Final commit if verification changed tracked files**

If all tasks were committed and verification did not change tracked files, skip this step. If a verification fix was made, commit only the intended files:

```bash
git add <intended-files>
git commit -m "chore: finish reader guide verification"
```

Expected:

- No unrelated dirty files are included.

## Implementation Notes

- Prefer copying result dataclasses and issue formatting style from 0.3.0 modules when it keeps CLI behavior consistent.
- Keep 0.4.0 logic in `v040_*` modules so each file has one responsibility.
- Keep dispatch functions small and deterministic. Dispatch should depend on manifest keys, not on a `dsl_version` field.
- Do not place subagent output contracts in child JSON schemas. They belong in `SKILL.md` as workflow contracts only.
- Do not include a top-level `关键机制` or `验证与风险` section anywhere in the renderer.
- Do not add `details` to list blocks.
- Do not add `key` or `title` to fixed sections.
- Do not add `steps` to main flows.
