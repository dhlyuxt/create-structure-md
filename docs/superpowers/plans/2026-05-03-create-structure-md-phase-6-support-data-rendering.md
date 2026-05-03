# Phase 6 Support Data Rendering Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete Phase 6 support-data rendering and validation polish so evidence, traceability, source snippets, risks, assumptions, extra tables, extra diagrams, and Chapter 6/7 empty states render safely and deterministically without creating support-data appendices.

**Architecture:** Extend the existing standard-library renderer with a small support-data layer that builds evidence, traceability, and snippet indexes once, then attaches compact support blocks near supported nodes and fixed table rows. Keep schema shape enforcement in `schemas/structure-design.schema.json`, semantic warnings/errors in `scripts/validate_dsl.py`, and deterministic Markdown output in `scripts/render_markdown.py`; renderer support blocks must never add table columns or put snippets inside table cells.

**Tech Stack:** Python 3 standard library only: `argparse`, `dataclasses`, `html`, `json`, `re`, `shutil`, `sys`, `datetime`, `pathlib`, `unittest`, `unittest.mock`, `subprocess`, `tempfile`, and existing `jsonschema` through `validate_dsl.py`. Do not add Python dependencies.

---

## File Structure

- Modify: `scripts/render_markdown.py`
  - Add support-data indexing helpers for `evidence`, `traceability`, and `source_snippets`.
  - Add compact support-note renderers for evidence, traceability, and source snippets.
  - Add table support-block helpers that render after fixed and extra tables, grouped by stable row ID or fallback display label.
  - Thread support rendering through chapter 2 core capabilities, chapters 3, 4, 5, 6, 7, 8, and chapter 9 risk/assumption sections.
  - Include `id` as a rendered field in chapter 9 risk and assumption tables.
  - Preserve existing output-safety behavior, fixed heading order, fixed visible table columns, Mermaid fence behavior, and Markdown escaping.
- Modify: `scripts/validate_dsl.py`
  - Keep existing support-data checks and add only missing Phase 6 semantic gaps: explicit traceability-backlink coverage for all targetable nodes, source snippet reference coverage, extra table/diagram rules, and documentation-oriented warning/error text where current tests reveal gaps.
- Modify: `schemas/structure-design.schema.json`
  - Keep the DSL shape stable. Only adjust schema if tests expose a Phase 6 gap, such as extra table column title non-empty or extra diagram full-object requirements already intended by the spec.
- Modify: `tests/test_render_markdown.py`
  - Add renderer unit and integration tests for support-data placement, de-duplication, snippet fence safety, Chapter 9 support refs, extra table evidence, extra diagrams, and Chapter 6/7 empty states.
- Modify: `tests/test_validate_dsl.py`
  - Add schema-shape tests only for Phase 6 schema gaps that are not already covered.
- Modify: `tests/test_validate_dsl_semantics.py`
  - Add validator semantic tests for remaining Phase 6 warnings/errors. This file already owns CLI semantic behavior for unreferenced evidence, traceability targets/backlinks, source snippet references, extra table keys, and low-confidence warnings.
- Modify: `references/dsl-spec.md`
  - Document support-data rendering semantics, authoritative traceability target binding, snippet safety, and extra table/diagram constraints.
- Modify: `references/document-structure.md`
  - Document where support notes render in the fixed nine-chapter output and state that support data does not create standalone appendices.
- Modify: `references/review-checklist.md`
  - Add Phase 6 review checks for support data, snippet safety, traceability de-duplication, and empty-state wording.
- Modify: `tests/fixtures/valid-phase2.dsl.json`
  - Keep this fixture valid and lightweight. Add support data only if an integration test intentionally needs one canonical fixture; prefer test-local mutations in unit tests.

Implementation constraints:

- Do not run deletion commands such as `rm`, `rmdir`, `git clean`, `git reset --hard`, checkout-discard commands, worktree removal, or branch deletion. If cleanup is needed, give the command to the user instead of executing it.
- Do not add Python dependencies.
- Use the agent Python for all commands:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest discover -s tests -v
```

- Stay inside Phase 6 scope: support-data rendering, related validation, reference docs, and focused tests. Do not add Phase 7 end-to-end acceptance workflows, packaging changes, release docs, broad skill documentation rewrites, or commits beyond the task-specific implementation commits listed below.

---

### Task 1: Support-Data Indexes And Compact Rendering Primitives

**Files:**
- Modify: `tests/test_render_markdown.py`
- Modify: `scripts/render_markdown.py`

- [ ] **Step 1: Write failing tests for support-data indexes, de-duplication, and compact strings**

Append this test class after `MarkdownPrimitiveTests` in `tests/test_render_markdown.py`:

```python
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
        context = module.build_support_context(document)

        rendered = module.render_node_support(node, context, target_type="module", target_id="MOD-SKILL")

        self.assertEqual(1, rendered.count("依据：EV-001（入口脚本，scripts/render_markdown.py:1）"))
        self.assertEqual(1, rendered.count("关联来源：REQ-001（覆盖模块生成能力。）"))
        self.assertIn("Source: scripts/render_markdown.py:10-12", rendered)
        self.assertIn("Purpose: 展示入口。", rendered)
        self.assertIn("```python\ndef main():\n    return 0\n```", rendered)
        self.assertNotIn("很长描述不应内联", rendered)

    def test_render_node_support_returns_empty_string_when_no_support_exists(self):
        module = load_renderer_module()
        context = module.build_support_context(valid_document())
        rendered = module.render_node_support({}, context, target_type="module", target_id="MOD-SKILL")
        self.assertEqual("", rendered)
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_render_markdown.SupportDataPrimitiveTests -v
```

Expected: fail with errors such as:

```text
AttributeError: module 'render_markdown_under_test' has no attribute 'build_support_context'
```

- [ ] **Step 3: Add support-data primitives**

In `scripts/render_markdown.py`, add this import near the other imports:

```python
from dataclasses import dataclass, field
```

Add these helpers after `safe_fence_info_string`:

```python
@dataclass
class SupportContext:
    evidence_by_id: dict = field(default_factory=dict)
    traceability_by_id: dict = field(default_factory=dict)
    traceability_by_target: dict = field(default_factory=dict)
    snippets_by_id: dict = field(default_factory=dict)


def build_support_context(document):
    context = SupportContext()
    context.evidence_by_id = {item.get("id"): item for item in document.get("evidence", [])}
    context.traceability_by_id = {item.get("id"): item for item in document.get("traceability", [])}
    context.snippets_by_id = {item.get("id"): item for item in document.get("source_snippets", [])}
    for item in document.get("traceability", []):
        target = (item.get("target_type"), item.get("target_id"))
        context.traceability_by_target.setdefault(target, []).append(item)
    return context


def unique_existing_items(refs, items_by_id):
    seen = set()
    items = []
    for ref in refs or []:
        if ref in seen:
            continue
        item = items_by_id.get(ref)
        if item is not None:
            items.append(item)
            seen.add(ref)
    return items


def evidence_label(evidence):
    title = stringify_markdown_value(evidence.get("title", "")).strip()
    location = stringify_markdown_value(evidence.get("location", "")).strip()
    details = [part for part in [title, location] if part]
    if details:
        return f"{evidence.get('id')}（{'，'.join(details)}）"
    return stringify_markdown_value(evidence.get("id", ""))


def traceability_label(trace):
    source = stringify_markdown_value(trace.get("source_external_id", "")).strip()
    description = stringify_markdown_value(trace.get("description", "")).strip()
    if description:
        return f"{source}（{description}）"
    return source


def render_support_lines(lines):
    rendered = []
    for line in lines:
        escaped = escape_plain_text(line).strip()
        if escaped:
            rendered.append(f"- {escaped}")
    return "\n".join(rendered)


def render_node_support(node, context, target_type=None, target_id=None):
    lines = []
    for evidence in unique_existing_items(node.get("evidence_refs", []), context.evidence_by_id):
        lines.append(f"依据：{evidence_label(evidence)}")

    trace_items = []
    seen_trace_ids = set()
    for trace in context.traceability_by_target.get((target_type, target_id), []):
        trace_id = trace.get("id")
        if trace_id not in seen_trace_ids:
            trace_items.append(trace)
            seen_trace_ids.add(trace_id)
    for trace in unique_existing_items(node.get("traceability_refs", []), context.traceability_by_id):
        trace_id = trace.get("id")
        if trace_id not in seen_trace_ids:
            trace_items.append(trace)
            seen_trace_ids.add(trace_id)
    for trace in trace_items:
        lines.append(f"关联来源：{traceability_label(trace)}")

    parts = []
    support_lines = render_support_lines(lines)
    if support_lines:
        parts.append(support_lines)
    for snippet in unique_existing_items(node.get("source_snippet_refs", []), context.snippets_by_id):
        parts.append(render_source_snippet(snippet))
    return "\n\n".join(parts)
```

- [ ] **Step 4: Run primitive tests to verify they pass**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_render_markdown.SupportDataPrimitiveTests -v
```

Expected:

```text
Ran 3 tests
OK
```

- [ ] **Step 5: Run existing renderer tests for regression**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_render_markdown -v
```

Expected: all existing and new renderer tests pass.

- [ ] **Step 6: Commit**

```bash
git status --short
git diff -- tests/test_render_markdown.py scripts/render_markdown.py
git add tests/test_render_markdown.py scripts/render_markdown.py
git diff --cached --stat
git diff --cached -- tests/test_render_markdown.py scripts/render_markdown.py
git status --short
# Confirm only tests/test_render_markdown.py and scripts/render_markdown.py are staged for this task.
git commit -m "feat: add support data rendering primitives"
```

---

### Task 2: Fixed Table Row Support Placement

**Files:**
- Modify: `tests/test_render_markdown.py`
- Modify: `scripts/render_markdown.py`

- [ ] **Step 1: Write failing table-placement tests**

Append this class after `SupportDataPrimitiveTests`:

```python
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

        markdown = module.render_markdown(document)
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
            {"id": "TR-DEP", "source_external_id": "REQ-DEP", "source_type": "requirement", "target_type": "dependency", "target_id": "DEP-001", "description": ""},
        ]
        document["source_snippets"] = [
            {"id": "SNIP-COL", "path": "src/collab.py", "line_start": 4, "line_end": 5, "language": "python", "purpose": "协作证据。", "content": "collaborate()", "confidence": "observed"},
        ]

        markdown = module.render_markdown(document)
        chapter_6 = section_between(markdown, "## 6. 配置、数据与依赖关系", "## 7. 跨模块协作关系")
        chapter_7 = section_between(markdown, "## 7. 跨模块协作关系", "## 8. 关键流程")

        self.assertIn("支持数据（CFG-001 / 输出目录）", chapter_6)
        self.assertIn("依据：EV-CFG（配置证据）", chapter_6)
        self.assertIn("支持数据（DEP-001 / jsonschema）", chapter_6)
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

        markdown = module.render_markdown(document)
        chapter_2 = section_between(markdown, "## 2. 系统概览", "## 3. 架构视图")
        chapter_5 = section_between(markdown, "### 5.2 运行单元说明", "### 5.3 运行时流程图")

        self.assertIn("支持数据（CAP-001 / 结构设计文档生成）", chapter_2)
        self.assertIn("关联来源：REQ-CAP-AUTH（核心能力需求。）", chapter_2)
        self.assertIn("支持数据（RUN-GENERATE / 文档生成命令序列）", chapter_5)
        self.assertIn("关联来源：REQ-RUN-AUTH（运行单元需求。）", chapter_5)
        self.assertNotIn("| REQ-CAP-AUTH |", chapter_2)
        self.assertNotIn("| REQ-RUN-AUTH |", chapter_5)
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_render_markdown.SupportDataTablePlacementTests -v
```

Expected: fail because `render_markdown()` does not yet render row support blocks after fixed tables and `render_chapter_2()` is not support-aware yet.

- [ ] **Step 3: Add fixed table support helpers**

In `scripts/render_markdown.py`, add these helpers after `render_fixed_table_or_empty`:

```python
def row_display_label(row, id_key, label_key):
    row_id = stringify_markdown_value(row.get(id_key, "")).strip()
    label = stringify_markdown_value(row.get(label_key, "")).strip()
    if row_id and label:
        return f"{row_id} / {label}"
    return row_id or label


def render_table_support(rows, context, *, id_key, label_key, target_type=None):
    parts = []
    for row in rows or []:
        row_id = stringify_markdown_value(row.get(id_key, "")).strip()
        label = row_display_label(row, id_key, label_key)
        support = render_node_support(row, context, target_type=target_type, target_id=row_id)
        if support:
            parts.append(f"支持数据（{escape_plain_text(label).strip()}）\n\n{support}")
    return "\n\n".join(parts)


def render_fixed_table_with_support(rows, columns, context, *, id_key, label_key, target_type=None):
    table = render_fixed_table(rows, columns)
    support = render_table_support(rows, context, id_key=id_key, label_key=label_key, target_type=target_type)
    if support:
        return f"{table}\n\n{support}"
    return table


def render_fixed_table_or_empty_with_support(rows, columns, empty_text, context, *, id_key, label_key, target_type=None):
    if not rows:
        return empty_text
    return render_fixed_table_with_support(
        rows,
        columns,
        context,
        id_key=id_key,
        label_key=label_key,
        target_type=target_type,
    )
```

- [ ] **Step 4: Thread table support into fixed row tables**

Change chapter renderers to accept `support_context` where needed. Start with chapter 2 core capabilities so authoritative `traceability[]` targets for `core_capability` have a visible attachment point even when the node has no local backlink:

```python
def render_chapter_2(document, support_context):
    overview = document["system_overview"]
    parts = [
        chapter_heading(2, "系统概览"),
        render_paragraph(overview.get("summary", "")),
        render_paragraph(overview.get("purpose", "")),
        render_fixed_table_with_support(
            overview.get("core_capabilities", []),
            [("name", "能力"), ("description", "描述")],
            support_context,
            id_key="capability_id",
            label_key="name",
            target_type="core_capability",
        ),
    ]
    notes = render_bullets(overview.get("notes", []))
    if notes:
        parts.append(notes)
    return "\n\n".join(part for part in parts if part != "")
```

Then update chapter 3 module intro:

```python
def render_chapter_3(document, support_context):
    ...
    render_fixed_table_with_support(
        architecture.get("module_intro", {}).get("rows", []),
        [
            ("module_name", "模块名称"),
            ("responsibility", "职责"),
            ("inputs", "输入"),
            ("outputs", "输出"),
            ("notes", "备注"),
        ],
        support_context,
        id_key="module_id",
        label_key="module_name",
        target_type="module",
    )
```

Apply the same pattern to:

```python
render_chapter_5(..., support_context)
render_fixed_table_with_support(runtime_unit_rows, RUNTIME_UNIT_COLUMNS, support_context, id_key="unit_id", label_key="unit_name", target_type="runtime_unit")

render_chapter_6(..., support_context)
render_fixed_table_or_empty_with_support(configuration_items_rows, CONFIGURATION_ITEM_COLUMNS, "不适用。", support_context, id_key="config_id", label_key="config_name", target_type="configuration_item")
render_fixed_table_or_empty_with_support(structural_data_rows, STRUCTURAL_DATA_ARTIFACT_COLUMNS, "未识别到需要在结构设计阶段单独说明的关键结构数据或产物。", support_context, id_key="artifact_id", label_key="artifact_name", target_type="data_artifact")
render_fixed_table_or_empty_with_support(dependency_rows, DEPENDENCY_COLUMNS, "未识别到需要在结构设计阶段单独说明的外部依赖项。", support_context, id_key="dependency_id", label_key="dependency_name", target_type="dependency")

render_chapter_7(..., support_context)
render_fixed_table_or_empty_with_support(collaboration_rows, COLLABORATION_COLUMNS, "本系统当前仅识别到一个结构模块，暂无跨模块协作关系。", support_context, id_key="collaboration_id", label_key="scenario", target_type="collaboration")
```

Update `render_markdown()` to build and pass the context:

```python
def render_markdown(document):
    module_display_names = build_module_display_names(document)
    runtime_unit_display_names = build_runtime_unit_display_names(document)
    support_context = build_support_context(document)
    parts = [
        "# 软件结构设计说明书",
        render_chapter_1(document),
        render_chapter_2(document, support_context),
        render_chapter_3(document, support_context),
        render_chapter_4(document),
        render_chapter_5(document, module_display_names, support_context),
        render_chapter_6(document, support_context),
        render_chapter_7(document, module_display_names, support_context),
        render_chapter_8(document, module_display_names, runtime_unit_display_names),
        render_chapter_9(document),
    ]
    return "\n\n".join(parts) + "\n"
```

Do not change `render_chapter_4`, `render_chapter_8`, or `render_chapter_9` signatures in Task 2. Task 2 ends with support-aware chapters 2, 3, 5, 6, and 7 only, so the full `tests.test_render_markdown` suite can pass without transient `TypeError` from calling functions whose signatures are updated in later tasks.

- [ ] **Step 5: Run table placement tests and regression tests**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_render_markdown.SupportDataPrimitiveTests tests.test_render_markdown.SupportDataTablePlacementTests -v
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_render_markdown -v
```

Expected:

```text
OK
```

- [ ] **Step 6: Commit**

```bash
git status --short
git diff -- tests/test_render_markdown.py scripts/render_markdown.py
git add tests/test_render_markdown.py scripts/render_markdown.py
git diff --cached --stat
git diff --cached -- tests/test_render_markdown.py scripts/render_markdown.py
git status --short
# Confirm only tests/test_render_markdown.py and scripts/render_markdown.py are staged for this task.
git commit -m "feat: render support data after fixed tables"
```

---

### Task 3: Node-Level Support Placement For Modules, Capabilities, Flows, Steps, And Branches

**Files:**
- Modify: `tests/test_render_markdown.py`
- Modify: `scripts/render_markdown.py`

- [ ] **Step 1: Write failing node-level support tests**

Append this class after `SupportDataTablePlacementTests`:

```python
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

        markdown = module.render_markdown(document)
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

        markdown = module.render_markdown(document)
        flow_section = section_from(markdown, "### 8.3 生成结构设计文档")

        self.assertIn("依据：EV-FLOW（流程来源，workflow）", flow_section)
        self.assertIn("支持数据（STEP-GENERATE-001 / 准备结构化 DSL JSON。）", flow_section)
        self.assertIn("关联来源：REQ-STEP", flow_section)
        self.assertEqual([], flow["steps"][0]["traceability_refs"])
        self.assertIn("支持数据（BR-GENERATE-001 / DSL 校验失败）", flow_section)
        self.assertIn("Source: scripts/validate_dsl.py:20-22", flow_section)
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_render_markdown.NodeLevelSupportPlacementTests -v
```

Expected: fail because module design sections, provided capability rows, flow nodes, steps, and branches do not render support notes yet.

- [ ] **Step 3: Render module and capability support**

In `render_module_design_section`, after the module summary paragraph, insert module support:

```python
module_support = render_node_support(
    module,
    support_context,
    target_type="module",
    target_id=module.get("module_id", ""),
)
```

Then include `module_support` directly after `render_paragraph(module.get("summary", ""))` in the `parts` list.

Change the provided capabilities table call to:

```python
render_fixed_table_with_support(
    provided.get("rows", []),
    [
        ("capability_name", "能力名称"),
        ("interface_style", "接口风格"),
        ("description", "描述"),
        ("inputs", "输入"),
        ("outputs", "输出"),
        ("notes", "备注"),
    ],
    support_context,
    id_key="capability_id",
    label_key="capability_name",
    target_type="provided_capability",
)
```

Update signatures:

```python
def render_module_design_section(module, index, support_context):
def render_chapter_4(document, support_context):
```

Ensure `render_chapter_4` calls:

```python
parts.append(render_module_design_section(module, index, support_context))
```

- [ ] **Step 4: Render flow, step, and branch support**

Change `render_key_flow_overview`:

```python
def render_key_flow_overview(flow, module_display_names, runtime_unit_display_names, support_context):
    parts = [
        render_paragraph(flow.get("overview", "")),
        render_node_support(flow, support_context, target_type="flow", target_id=flow.get("flow_id", "")),
        render_reference_summary("关联模块", flow.get("related_module_ids", []), module_display_names, "module"),
        render_reference_summary(
            "关联运行单元", flow.get("related_runtime_unit_ids", []), runtime_unit_display_names, "runtime unit"
        ),
    ]
    return "\n\n".join(part for part in parts if part != "")
```

In `render_key_flow_section`, use support-aware table rendering:

```python
render_fixed_table_with_support(
    step_rows,
    FLOW_STEP_COLUMNS,
    support_context,
    id_key="step_id",
    label_key="description",
    target_type="flow_step",
)
```

For branches:

```python
render_fixed_table_or_empty_with_support(
    branch_rows,
    FLOW_BRANCH_COLUMNS,
    "未识别到异常或分支说明。",
    support_context,
    id_key="branch_id",
    label_key="condition",
    target_type="flow_branch",
)
```

Update signatures:

```python
def render_key_flow_section(flow, section_number, module_display_names, runtime_unit_display_names, support_context):
def render_chapter_8(document, module_display_names, runtime_unit_display_names, support_context):
```

Update only the chapter 4 and chapter 8 calls in `render_markdown()` now that Task 3 changed those signatures:

```python
def render_markdown(document):
    module_display_names = build_module_display_names(document)
    runtime_unit_display_names = build_runtime_unit_display_names(document)
    support_context = build_support_context(document)
    parts = [
        "# 软件结构设计说明书",
        render_chapter_1(document),
        render_chapter_2(document, support_context),
        render_chapter_3(document, support_context),
        render_chapter_4(document, support_context),
        render_chapter_5(document, module_display_names, support_context),
        render_chapter_6(document, support_context),
        render_chapter_7(document, module_display_names, support_context),
        render_chapter_8(document, module_display_names, runtime_unit_display_names, support_context),
        render_chapter_9(document),
    ]
    return "\n\n".join(parts) + "\n"
```

- [ ] **Step 5: Run node support and full renderer tests**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_render_markdown.NodeLevelSupportPlacementTests -v
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_render_markdown -v
```

Expected:

```text
OK
```

- [ ] **Step 6: Commit**

```bash
git status --short
git diff -- tests/test_render_markdown.py scripts/render_markdown.py
git add tests/test_render_markdown.py scripts/render_markdown.py
git diff --cached --stat
git diff --cached -- tests/test_render_markdown.py scripts/render_markdown.py
git status --short
# Confirm only tests/test_render_markdown.py and scripts/render_markdown.py are staged for this task.
git commit -m "feat: render node-level support data"
```

---

### Task 4: Chapter 9 Risks, Assumptions, Support Refs, And Low-Confidence Polish

**Files:**
- Modify: `tests/test_render_markdown.py`
- Modify: `scripts/render_markdown.py`

- [ ] **Step 1: Write failing Chapter 9 support tests**

Append these tests to `ChapterNineRenderingTests`:

```python
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

        markdown = module.render_markdown(document)
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_render_markdown.ChapterNineRenderingTests -v
```

Expected: fail because risk and assumption support refs are not rendered and the existing chapter 9 risk/assumption tables do not include the required ID field.

- [ ] **Step 3: Add required ID columns and render support blocks under Chapter 9 tables**

Update the chapter 9 column constants so Phase 6's required rendered fields include ID:

```python
RISK_COLUMNS = [
    ("id", "ID"),
    ("description", "风险"),
    ("impact", "影响"),
    ("mitigation", "缓解措施"),
    ("confidence", "置信度"),
]

ASSUMPTION_COLUMNS = [
    ("id", "ID"),
    ("description", "假设"),
    ("rationale", "依据"),
    ("validation_suggestion", "验证建议"),
    ("confidence", "置信度"),
]
```

Add a helper near `render_chapter_9`:

```python
def render_collection_support(items, context, *, id_key, label_key, target_type):
    return render_table_support(items, context, id_key=id_key, label_key=label_key, target_type=target_type)
```

Change `render_chapter_9` signature and internals:

```python
def render_chapter_9(document, support_context):
    parts = [chapter_heading(9, "结构问题与改进建议")]
    free_form_text = stringify_markdown_value(document.get("structure_issues_and_suggestions", "")).strip()
    risks = document.get("risks", [])
    assumptions = document.get("assumptions", [])
    low_confidence_items = collect_low_confidence_items(document)

    if free_form_text:
        parts.append(escape_plain_text(free_form_text))
    if risks:
        parts.extend(["### 风险", render_fixed_table(risks, RISK_COLUMNS)])
        risk_support = render_collection_support(
            risks,
            support_context,
            id_key="id",
            label_key="description",
            target_type="risk",
        )
        if risk_support:
            parts.append(risk_support)
    if assumptions:
        parts.extend(["### 假设", render_fixed_table(assumptions, ASSUMPTION_COLUMNS)])
        assumption_support = render_collection_support(
            assumptions,
            support_context,
            id_key="id",
            label_key="description",
            target_type="assumption",
        )
        if assumption_support:
            parts.append(assumption_support)
    if low_confidence_items:
        parts.extend(["### 低置信度项", render_fixed_table(low_confidence_items, LOW_CONFIDENCE_COLUMNS)])
    if len(parts) == 1:
        parts.append("未识别到明确的结构问题与改进建议。")

    return "\n\n".join(parts)
```

Update the chapter 9 call in `render_markdown()` after changing the signature:

```python
def render_markdown(document):
    module_display_names = build_module_display_names(document)
    runtime_unit_display_names = build_runtime_unit_display_names(document)
    support_context = build_support_context(document)
    parts = [
        "# 软件结构设计说明书",
        render_chapter_1(document),
        render_chapter_2(document, support_context),
        render_chapter_3(document, support_context),
        render_chapter_4(document, support_context),
        render_chapter_5(document, module_display_names, support_context),
        render_chapter_6(document, support_context),
        render_chapter_7(document, module_display_names, support_context),
        render_chapter_8(document, module_display_names, runtime_unit_display_names, support_context),
        render_chapter_9(document, support_context),
    ]
    return "\n\n".join(parts) + "\n"
```

Keep `collect_low_confidence_items` restricted to design content only:

```python
# Do not add evidence, traceability, source_snippets, risks, assumptions, or diagrams here.
```

- [ ] **Step 4: Run Chapter 9 and full renderer tests**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_render_markdown.ChapterNineRenderingTests -v
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_render_markdown -v
```

Expected:

```text
OK
```

- [ ] **Step 5: Commit**

```bash
git status --short
git diff -- tests/test_render_markdown.py scripts/render_markdown.py
git add tests/test_render_markdown.py scripts/render_markdown.py
git diff --cached --stat
git diff --cached -- tests/test_render_markdown.py scripts/render_markdown.py
git status --short
# Confirm only tests/test_render_markdown.py and scripts/render_markdown.py are staged for this task.
git commit -m "feat: render chapter nine support refs"
```

---

### Task 5: Validator Refinements For Phase 6 Gaps

**Files:**
- Modify: `tests/test_validate_dsl.py`
- Modify: `tests/test_validate_dsl_semantics.py`
- Modify: `schemas/structure-design.schema.json`
- Modify: `scripts/validate_dsl.py`

- [ ] **Step 1: Add schema characterization/regression tests for existing Phase 6 shape rules**

Add these tests to `SchemaCommonShapeTests` in `tests/test_validate_dsl.py`:

```python
    def test_extra_table_column_key_and_title_must_be_non_empty(self):
        for field_name in ["key", "title"]:
            extra_table = {
                "id": "TBL-ARCH-001",
                "title": "补充表格",
                "columns": [{"key": "name", "title": "名称"}],
                "rows": [{"name": "示例"}],
            }
            extra_table["columns"][0][field_name] = ""
            with self.subTest(field_name=field_name):
                assert_invalid_def(
                    self,
                    "extraTable",
                    extra_table,
                    "should be non-empty",
                    expected_validator="minLength",
                    expected_path=["columns", 0, field_name],
                )

    def test_extra_diagram_empty_source_is_schema_valid_and_semantically_checked_later(self):
        document = valid_example()
        document["architecture_views"]["extra_diagrams"] = [{
            "id": "MER-ARCH-EXTRA",
            "kind": "extra",
            "title": "补充图",
            "diagram_type": "flowchart",
            "description": "补充图。",
            "source": "",
            "confidence": "observed",
        }]
        # Schema allows string shape; semantic validator owns non-empty source.
        validator().validate(document)
```

Expected: these characterization tests should pass before implementation if the current schema already matches the intended split between schema shape and semantic validation. They are regression tests, not red tests.

- [ ] **Step 2: Run schema characterization tests**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_validate_dsl.SchemaCommonShapeTests -v
```

Expected:

```text
OK
```

- [ ] **Step 3: Write a schema red test for core capability local support refs**

Add this test to `SchemaSupportDataTests` in `tests/test_validate_dsl.py`:

```python
    def test_core_capability_accepts_optional_support_refs(self):
        document = valid_example()
        document["evidence"] = [
            {"id": "EV-CAP", "kind": "note", "title": "能力证据", "location": "", "description": "", "confidence": "observed"}
        ]
        document["traceability"] = [
            {
                "id": "TR-CAP",
                "source_external_id": "REQ-CAP",
                "source_type": "requirement",
                "target_type": "core_capability",
                "target_id": "CAP-001",
                "description": "核心能力追踪。",
            }
        ]
        document["source_snippets"] = [
            {
                "id": "SNIP-CAP",
                "path": "references/dsl-spec.md",
                "line_start": 1,
                "line_end": 1,
                "language": "markdown",
                "purpose": "核心能力证据。",
                "content": "# create-structure-md DSL Spec",
                "confidence": "observed",
            }
        ]
        document["system_overview"]["core_capabilities"][0]["evidence_refs"] = ["EV-CAP"]
        document["system_overview"]["core_capabilities"][0]["traceability_refs"] = ["TR-CAP"]
        document["system_overview"]["core_capabilities"][0]["source_snippet_refs"] = ["SNIP-CAP"]

        validator().validate(document)
```

- [ ] **Step 4: Run the core capability schema red test**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_validate_dsl.SchemaSupportDataTests.test_core_capability_accepts_optional_support_refs -v
```

Expected: fail with a schema `additionalProperties` error for `system_overview.core_capabilities[0]` because current `#/$defs/capability` does not yet allow `evidence_refs`, `traceability_refs`, or `source_snippet_refs`.

- [ ] **Step 5: Update schema to allow optional support refs on core capabilities**

Extend `schemas/structure-design.schema.json` so `#/$defs/capability` allows optional support refs while keeping the existing required fields unchanged:

```json
"capability": {
  "type": "object",
  "required": ["capability_id", "name", "description", "confidence"],
  "additionalProperties": false,
  "properties": {
    "capability_id": { "$ref": "#/$defs/nonEmptyString" },
    "name": { "$ref": "#/$defs/nonEmptyString" },
    "description": { "$ref": "#/$defs/nonEmptyString" },
    "confidence": { "$ref": "#/$defs/confidence" },
    "evidence_refs": { "$ref": "#/$defs/referenceArray" },
    "traceability_refs": { "$ref": "#/$defs/referenceArray" },
    "source_snippet_refs": { "$ref": "#/$defs/referenceArray" }
  }
}
```

- [ ] **Step 6: Run schema tests to verify the red test is green**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_validate_dsl.SchemaCommonShapeTests tests.test_validate_dsl.SchemaSupportDataTests.test_core_capability_accepts_optional_support_refs -v
```

Expected:

```text
OK
```

- [ ] **Step 7: Write semantic red tests and semantic regression tests**

Add these tests to `ExtraTableAndTraceabilityTests` in `tests/test_validate_dsl_semantics.py`:

```python
    def test_extra_table_column_keys_reject_support_metadata_names(self):
        reserved_keys = ["evidence_refs", "traceability_refs", "source_snippet_refs", "confidence"]
        for key in reserved_keys:
            with tempfile.TemporaryDirectory() as tmpdir:
                document = valid_document()
                document["architecture_views"]["extra_tables"] = [{
                    "id": "TBL-RESERVED-KEY",
                    "title": "补充表",
                    "columns": [{"key": key, "title": "保留字段"}],
                    "rows": [{}],
                }]
                path = write_json(tmpdir, f"extra-table-reserved-{key}.dsl.json", document)
                completed = run_validator(path)
            with self.subTest(key=key):
                self.assertEqual(1, completed.returncode)
                self.assertIn("$.architecture_views.extra_tables[0].columns[0].key", completed.stderr)
                self.assertIn("reserved support metadata key", completed.stderr)

    def test_authoritative_traceability_can_target_module_without_local_backlink_regression(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            document["traceability"] = [{
                "id": "TR-MODULE-AUTH",
                "source_external_id": "REQ-AUTH",
                "source_type": "requirement",
                "target_type": "module",
                "target_id": "MOD-SKILL",
                "description": "authoritative target only",
            }]
            document["architecture_views"]["module_intro"]["rows"][0]["traceability_refs"] = []
            document["module_design"]["modules"][0]["traceability_refs"] = []
            path = write_json(tmpdir, "trace-authoritative-only.dsl.json", document)
            completed = run_validator(path)
        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertIn("Validation succeeded", completed.stdout)

    def test_local_traceability_backlinks_cover_all_targetable_nodes(self):
        def risk_node(document):
            document["risks"] = [{
                "id": "RISK-TRACE",
                "description": "可追踪风险。",
                "impact": "",
                "mitigation": "",
                "confidence": "inferred",
                "evidence_refs": [],
                "traceability_refs": [],
                "source_snippet_refs": [],
            }]
            return document["risks"][0]

        def assumption_node(document):
            document["assumptions"] = [{
                "id": "ASM-TRACE",
                "description": "可追踪假设。",
                "rationale": "",
                "validation_suggestion": "",
                "confidence": "unknown",
                "evidence_refs": [],
                "traceability_refs": [],
                "source_snippet_refs": [],
            }]
            return document["assumptions"][0]

        cases = [
            ("module", "MOD-SKILL", lambda document: document["module_design"]["modules"][0]),
            ("core_capability", "CAP-001", lambda document: document["system_overview"]["core_capabilities"][0]),
            ("provided_capability", "CAP-MOD-SKILL-001", lambda document: document["module_design"]["modules"][0]["external_capability_details"]["provided_capabilities"]["rows"][0]),
            ("runtime_unit", "RUN-GENERATE", lambda document: document["runtime_view"]["runtime_units"]["rows"][0]),
            ("configuration_item", "CFG-001", lambda document: document["configuration_data_dependencies"]["configuration_items"]["rows"][0]),
            ("data_artifact", "DATA-001", lambda document: document["configuration_data_dependencies"]["structural_data_artifacts"]["rows"][0]),
            ("dependency", "DEP-001", lambda document: document["configuration_data_dependencies"]["dependencies"]["rows"][0]),
            ("collaboration", "COL-001", lambda document: document["cross_module_collaboration"]["collaboration_scenarios"]["rows"][0]),
            ("flow", "FLOW-GENERATE", lambda document: document["key_flows"]["flows"][0]),
            ("flow_step", "STEP-GENERATE-001", lambda document: document["key_flows"]["flows"][0]["steps"][0]),
            ("flow_branch", "BR-GENERATE-001", lambda document: document["key_flows"]["flows"][0]["branches_or_exceptions"][0]),
            ("risk", "RISK-TRACE", risk_node),
            ("assumption", "ASM-TRACE", assumption_node),
        ]
        # Intentionally excludes key_flows.flow_index.rows[] because flow index rows are index-only
        # and must not carry local traceability_refs.

        for target_type, target_id, get_node in cases:
            with tempfile.TemporaryDirectory() as tmpdir:
                document = valid_document()
                document["traceability"] = [{
                    "id": "TR-VALID",
                    "source_external_id": f"REQ-{target_type}",
                    "source_type": "requirement",
                    "target_type": target_type,
                    "target_id": target_id,
                    "description": "valid local backlink",
                }]
                get_node(document)["traceability_refs"] = ["TR-VALID"]
                path = write_json(tmpdir, f"{target_type}-trace-valid.dsl.json", document)
                completed = run_validator(path)
            with self.subTest(target_type=target_type, mode="valid"):
                self.assertEqual(0, completed.returncode, completed.stderr)

            with tempfile.TemporaryDirectory() as tmpdir:
                document = valid_document()
                wrong_target_type = "runtime_unit" if target_type == "module" else "module"
                wrong_target_id = "RUN-GENERATE" if target_type == "module" else "MOD-SKILL"
                document["traceability"] = [{
                    "id": "TR-WRONG",
                    "source_external_id": f"REQ-WRONG-{target_type}",
                    "source_type": "requirement",
                    "target_type": wrong_target_type,
                    "target_id": wrong_target_id,
                    "description": "wrong local backlink",
                }]
                get_node(document)["traceability_refs"] = ["TR-WRONG"]
                path = write_json(tmpdir, f"{target_type}-trace-wrong.dsl.json", document)
                completed = run_validator(path)
            with self.subTest(target_type=target_type, mode="wrong"):
                self.assertEqual(1, completed.returncode)
                self.assertIn("traceability_refs[0]", completed.stderr)
                self.assertIn(f"instead of {target_type} {target_id}", completed.stderr)
```

Add this test to `SourceSnippetValidationTests`:

```python
    def test_source_snippet_may_be_referenced_from_fixed_table_row_and_flow_step_regression(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            document["source_snippets"] = [{
                "id": "SNIP-ROW",
                "path": "scripts/render_markdown.py",
                "line_start": 1,
                "line_end": 2,
                "language": "python",
                "purpose": "固定表格行证据",
                "content": "print('row')",
                "confidence": "observed",
            }]
            document["runtime_view"]["runtime_units"]["rows"][0]["source_snippet_refs"] = ["SNIP-ROW"]
            path = write_json(tmpdir, "snippet-row-ref.dsl.json", document)
            completed = run_validator(path)
        self.assertEqual(0, completed.returncode, completed.stderr)

        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            document["source_snippets"] = [{
                "id": "SNIP-STEP",
                "path": "scripts/render_markdown.py",
                "line_start": 3,
                "line_end": 4,
                "language": "python",
                "purpose": "流程步骤证据",
                "content": "print('step')",
                "confidence": "observed",
            }]
            document["key_flows"]["flows"][0]["steps"][0]["source_snippet_refs"] = ["SNIP-STEP"]
            path = write_json(tmpdir, "snippet-step-ref.dsl.json", document)
            completed = run_validator(path)
        self.assertEqual(0, completed.returncode, completed.stderr)
```

This step intentionally mixes one semantic red test with semantic regression tests:

- Red: `test_extra_table_column_keys_reject_support_metadata_names`.
- Expected green regressions: authoritative-only traceability without a local backlink, source snippet refs from already allowed fields, and table-driven local backlinks after Step 5's schema update.

- [ ] **Step 8: Run semantic tests and verify only the reserved-key test is red**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_validate_dsl_semantics.ExtraTableAndTraceabilityTests tests.test_validate_dsl_semantics.SourceSnippetValidationTests -v
```

Expected: fail on `test_extra_table_column_keys_reject_support_metadata_names` because `check_extra_tables()` does not yet reject reserved support metadata keys in `columns[].key`. The authoritative-only traceability regression, source snippet reference regression, and table-driven backlink coverage tests should pass after Step 5; if one fails, inspect that specific validator mapping before changing implementation.

- [ ] **Step 9: Implement reserved extra table key validation and any mapping fixes exposed by regressions**

Add a reserved-key check to `check_extra_tables()` in `scripts/validate_dsl.py`:

```python
RESERVED_EXTRA_TABLE_COLUMN_KEYS = {
    "evidence_refs",
    "traceability_refs",
    "source_snippet_refs",
    "confidence",
}
```

Then check each declared column key:

```python
        for i, key in enumerate(column_keys):
            if key in RESERVED_EXTRA_TABLE_COLUMN_KEYS:
                context.report.error(
                    f"{path}.columns[{i}].key",
                    f"reserved support metadata key {key} cannot be used as an extra table column",
                    "Use a content-specific column key and keep support metadata outside visible table cells",
                )
            if key in seen_column_keys:
                context.report.error(
                    f"{path}.columns[{i}].key",
                    f"duplicate extra table column key {key}",
                    "Each extra table column key must be unique",
                )
            seen_column_keys.add(key)
```

If the table-driven backlink regression exposes a missing target mapping, update `current_traceability_target` in `scripts/validate_dsl.py` for that specific existing DSL node type. The intended mapping includes these local backlink-capable target types and excludes index-only `key_flows.flow_index.rows[]`:

```python
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
```

This mapping intentionally does not treat `key_flows.flow_index.rows[]` as a traceability target, because those rows are index-only and must not carry local `traceability_refs`.

If risk/assumption backlink tests fail, the relevant lines from the mapping above are:

```python
    if path.startswith("$.risks["):
        return ("risk", value.get("id"))
    if path.startswith("$.assumptions["):
        return ("assumption", value.get("id"))
```

If schema tests reveal `extraTableColumn` no longer uses non-empty strings, restore this shape in `schemas/structure-design.schema.json`:

```json
"extraTableColumn": {
  "type": "object",
  "required": ["key", "title"],
  "additionalProperties": false,
  "properties": {
    "key": { "$ref": "#/$defs/nonEmptyString" },
    "title": { "$ref": "#/$defs/nonEmptyString" }
  }
}
```

If extra diagram semantic non-empty tests are missing or failing, keep `check_all_extra_diagrams` enforcing:

```python
def check_all_extra_diagrams(document, context):
    for path, value in walk(document):
        if path.endswith(".extra_diagrams") and isinstance(value, list):
            for i, diagram in enumerate(value):
                diagram_source_required(context.report, f"{path}[{i}]", diagram, "extra diagram")
```

Do not add schema fields or change DSL shapes unless a test proves the Phase 6 spec requires the change.

- [ ] **Step 10: Run validator regression suite**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_validate_dsl tests.test_validate_dsl_semantics -v
```

Expected:

```text
OK
```

- [ ] **Step 11: Commit**

```bash
git status --short
git diff -- tests/test_validate_dsl.py tests/test_validate_dsl_semantics.py schemas/structure-design.schema.json scripts/validate_dsl.py
git add tests/test_validate_dsl.py tests/test_validate_dsl_semantics.py schemas/structure-design.schema.json scripts/validate_dsl.py
git diff --cached --stat
git diff --cached -- tests/test_validate_dsl.py tests/test_validate_dsl_semantics.py schemas/structure-design.schema.json scripts/validate_dsl.py
git status --short
# Confirm only tests/test_validate_dsl.py, tests/test_validate_dsl_semantics.py, schemas/structure-design.schema.json, and scripts/validate_dsl.py are staged for this task.
git commit -m "test: lock phase six validation semantics"
```

---

### Task 6: Extra Table Evidence, Extra Diagrams, References, Fixture, And Integration Validation

**Files:**
- Modify: `tests/test_render_markdown.py`
- Modify: `references/dsl-spec.md`
- Modify: `references/document-structure.md`
- Modify: `references/review-checklist.md`
- Modify: `tests/fixtures/valid-phase2.dsl.json` only if needed by the integration test
- Modify: `scripts/render_markdown.py`

- [ ] **Step 1: Write failing extra table evidence and integration tests**

Append these tests to `RendererIntegrationTests`:

```python
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

        markdown = module.render_markdown(document)
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
                [PYTHON, str(RENDERER), str(dsl_path), "--output-dir", tmpdir],
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
```

- [ ] **Step 2: Run tests to verify failures**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_render_markdown.RendererIntegrationTests -v
```

Expected: the extra table evidence test fails until `render_extra_table` accepts support context and renders row evidence after the table.

- [ ] **Step 3: Implement extra table evidence rendering**

Change `render_extra_table`:

```python
def first_display_value(row, columns):
    for key, _title in columns:
        value = stringify_markdown_value(row.get(key, "")).strip()
        if value:
            return value
    return "未命名补充行"


def render_extra_table_support(table, context):
    columns = [(column.get("key", ""), column.get("title", "")) for column in table.get("columns", [])]
    parts = []
    for row in table.get("rows", []):
        support = render_node_support(row, context)
        if support:
            label = first_display_value(row, columns)
            parts.append(f"支持数据（{escape_plain_text(label).strip()}）\n\n{support}")
    return "\n\n".join(parts)


def render_extra_table(table, support_context=None):
    columns = table.get("columns", [])
    rows = table.get("rows", [])
    declared_columns = [(column.get("key", ""), column.get("title", "")) for column in columns]
    title = escape_heading_label(table.get("title", ""))
    rendered = f"#### {title}\n\n{render_fixed_table(rows, declared_columns)}"
    if support_context is not None:
        support = render_extra_table_support(table, support_context)
        if support:
            rendered = f"{rendered}\n\n{support}"
    return rendered
```

Change `render_extras`:

```python
def render_extras(extra_tables, extra_diagrams, empty_text="无补充内容。", support_context=None):
    parts = []
    for table in extra_tables or []:
        parts.append(render_extra_table(table, support_context=support_context))
    for diagram in extra_diagrams or []:
        parts.append(render_extra_diagram(diagram))
    if not parts:
        return empty_text
    return "\n\n".join(parts)
```

Pass `support_context` to every `render_extras(...)` call in chapters 3 through 8 and module supplement renderers.

- [ ] **Step 4: Update reference docs for Phase 6 contract**

In `references/dsl-spec.md`, replace the placeholder support section with concrete Phase 6 rules:

```markdown
## Support Data

Support data supplies confidence, evidence, traceability, source snippets, risks, and assumptions for design items. Support data helps render stronger documentation but does not create standalone Markdown chapters.

- Evidence referenced by design nodes renders near those nodes as compact `依据：EV-...` notes.
- Unreferenced evidence produces a validation warning, not a failure.
- Traceability binding is authoritative through `traceability[].target_type` and `traceability[].target_id`; local `traceability_refs` are optional backlinks and must target the current node when present.
- Duplicate traceability discovered through both authoritative target scanning and local backlinks renders once.
- Source snippets must be referenced by at least one `source_snippet_refs` field, render near the referencing node, and never render inside Markdown table cells.
- Snippet code fences are chosen so snippet content cannot break the fence.
- Extra table rows may use declared content column keys plus `evidence_refs`; extra table `columns[].key` must not use support metadata names such as `evidence_refs`, `traceability_refs`, `source_snippet_refs`, or `confidence`.
- Extra diagrams are optional by omission, must be full diagram objects when present, and must have non-empty Mermaid source.
- Risks and assumptions render under chapter 9 `风险` and `假设`, with compact support refs when present.
- Low-confidence summary excludes evidence, traceability, source snippets, risks, assumptions, and Mermaid diagrams.
```

In `references/document-structure.md`, extend `## Mermaid And Tables`:

```markdown
Support data renders as compact notes near the relevant node or immediately after the relevant table. Fixed table rows keep fixed visible columns; evidence, traceability, and source snippet refs never become table cells. Extra table row evidence renders after the extra table using the first non-empty displayed row value as the support label; support metadata names are reserved and cannot be declared as extra table columns.

Chapter 6 empty tables render the documented empty-state sentences. Chapter 7 keeps sections 7.1 through 7.4 in single-module documents and renders the fixed collaboration absence text plus no-diagram text.
```

In `references/review-checklist.md`, add a `## Support Data` section:

```markdown
## Support Data

- Confirm evidence notes render near the referenced design item or after the referenced table row.
- Confirm unreferenced evidence warnings were reviewed.
- Confirm traceability uses `target_type` and `target_id` as the authoritative binding and duplicates render once.
- Confirm source snippets are necessary, redacted, safely fenced, and not inside table cells.
- Confirm risks and assumptions render in chapter 9 with support refs when present.
- Confirm low-confidence summary excludes support data and Mermaid diagram nodes.
- Confirm extra table evidence renders after the table, support metadata names are not visible column keys, and extra diagrams render only when non-empty.
```

- [ ] **Step 5: Run docs signpost and full test suite**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_render_markdown.RendererIntegrationTests tests.test_render_markdown.ReferenceSignpostTests -v
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest discover -s tests -v
```

Expected:

```text
OK
```

- [ ] **Step 6: Manual self-check against Phase 6 spec**

Verify each Phase 6 topic has a test and implementation:

```text
evidence near modules/rows/flows: SupportDataTablePlacementTests, NodeLevelSupportPlacementTests, RendererIntegrationTests
unreferenced evidence warning: tests/test_validate_dsl_semantics.py existing warning test
traceability authoritative target attachment/conflicting backlinks/dedup: SupportDataPrimitiveTests, SupportDataTablePlacementTests.test_core_capability_and_runtime_authoritative_traceability_render_without_local_backlinks, NodeLevelSupportPlacementTests, ExtraTableAndTraceabilityTests
source snippet required refs/safe fences/not table cells: SourceSnippetValidationTests, MarkdownPrimitiveTests, SupportDataTablePlacementTests
risk/assumption/low-confidence chapter 9: ChapterNineRenderingTests, including required ID columns in risk and assumption tables
extra table evidence and reserved metadata columns: RendererIntegrationTests.test_extra_table_evidence_renders_after_extra_table_using_row_display_value, ExtraTableAndTraceabilityTests.test_extra_table_column_keys_reject_support_metadata_names
extra diagram non-empty/rendering: test_validate_dsl_semantics extra diagram checks and RendererIntegrationTests
Chapter 6/7 empty states: existing ChapterFiveToEightRenderingTests
```

- [ ] **Step 7: Commit**

```bash
git status --short
git diff -- tests/test_render_markdown.py references/dsl-spec.md references/document-structure.md references/review-checklist.md scripts/render_markdown.py tests/fixtures/valid-phase2.dsl.json
git add tests/test_render_markdown.py references/dsl-spec.md references/document-structure.md references/review-checklist.md scripts/render_markdown.py tests/fixtures/valid-phase2.dsl.json
git diff --cached --stat
git diff --cached -- tests/test_render_markdown.py references/dsl-spec.md references/document-structure.md references/review-checklist.md scripts/render_markdown.py tests/fixtures/valid-phase2.dsl.json
git status --short
# Confirm only tests/test_render_markdown.py, references/dsl-spec.md, references/document-structure.md, references/review-checklist.md, scripts/render_markdown.py, and tests/fixtures/valid-phase2.dsl.json are staged for this task.
git commit -m "feat: complete phase six support data integration"
```
