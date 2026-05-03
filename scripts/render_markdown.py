#!/usr/bin/env python3
import argparse
import html
import json
import re
import shutil
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


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

CONTROL_CHARACTER_RE = re.compile(r"[\x00-\x1f\x7f-\x9f]")
SAFE_FENCE_INFO_RE = re.compile(r"^[A-Za-z0-9_+.-]+$")

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

CONFIGURATION_ITEM_COLUMNS = [
    ("config_name", "配置项"),
    ("source", "来源"),
    ("used_by", "使用方"),
    ("purpose", "用途"),
    ("notes", "备注"),
]

STRUCTURAL_DATA_ARTIFACT_COLUMNS = [
    ("artifact_name", "数据/产物"),
    ("artifact_type", "类型"),
    ("owner", "归属"),
    ("producer", "生产方"),
    ("consumer", "消费方"),
    ("notes", "备注"),
]

DEPENDENCY_COLUMNS = [
    ("dependency_name", "依赖项"),
    ("dependency_type", "类型"),
    ("used_by", "使用方"),
    ("purpose", "用途"),
    ("notes", "备注"),
]

COLLABORATION_COLUMNS = [
    ("scenario", "场景"),
    ("initiator_module_id", "发起模块"),
    ("participant_module_ids", "参与模块"),
    ("collaboration_method", "协作方式"),
    ("description", "描述"),
]

FLOW_INDEX_COLUMNS = [
    ("flow_name", "流程"),
    ("trigger_condition", "触发条件"),
    ("participant_module_ids", "参与模块"),
    ("participant_runtime_unit_ids", "参与运行单元"),
    ("main_steps", "主要步骤"),
    ("output_result", "输出结果"),
    ("notes", "备注"),
]

FLOW_STEP_COLUMNS = [
    ("order", "序号"),
    ("actor", "执行方"),
    ("description", "说明"),
    ("input", "输入"),
    ("output", "输出"),
    ("related_module_ids", "关联模块"),
    ("related_runtime_unit_ids", "关联运行单元"),
]

FLOW_BRANCH_COLUMNS = [
    ("condition", "条件"),
    ("handling", "处理方式"),
    ("related_module_ids", "关联模块"),
    ("related_runtime_unit_ids", "关联运行单元"),
]

RISK_COLUMNS = [
    ("description", "风险"),
    ("impact", "影响"),
    ("mitigation", "缓解措施"),
    ("confidence", "置信度"),
]

ASSUMPTION_COLUMNS = [
    ("description", "假设"),
    ("rationale", "依据"),
    ("validation_suggestion", "验证建议"),
    ("confidence", "置信度"),
]

LOW_CONFIDENCE_COLUMNS = [
    ("path", "路径"),
    ("label", "项目"),
    ("confidence", "置信度"),
]

LOW_CONFIDENCE_LABEL_KEYS = [
    "module_name",
    "name",
    "capability_name",
    "unit_name",
    "config_name",
    "artifact_name",
    "dependency_name",
    "scenario",
    "flow_name",
    "description",
    "condition",
    "summary",
]


class RenderError(Exception):
    exit_code = 1


class InputError(RenderError):
    exit_code = 2


def escape_fence_markers(value):
    return value.replace("```", "`&#96;&#96;").replace("~~~", "~&#126;&#126;")


def escape_html(value):
    return html.escape(value, quote=False)


def stringify_markdown_value(value):
    if value is None:
        return ""
    if isinstance(value, list):
        return "、".join(str(item) for item in value)
    return str(value)


def escape_table_cell(value):
    escaped = escape_html(stringify_markdown_value(value))
    escaped = "".join(escape_markdown_heading_line(line) for line in escaped.splitlines(keepends=True))
    escaped = escaped.replace("|", "\\|")
    escaped = escaped.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "<br>")
    return escape_fence_markers(escaped)


def escape_plain_text(value):
    escaped = escape_fence_markers(escape_html(stringify_markdown_value(value)))
    lines = escaped.splitlines(keepends=True)
    return "".join(escape_plain_text_line(line) for line in lines)


def escape_markdown_heading_line(line):
    newline = ""
    content = line
    if content.endswith("\r\n"):
        content = content[:-2]
        newline = "\r\n"
    elif content.endswith("\n"):
        content = content[:-1]
        newline = "\n"
    elif content.endswith("\r"):
        content = content[:-1]
        newline = "\r"

    if re.match(r"^ {0,3}#{1,6}(?:\s+|$)", content) or re.match(r"^ {0,3}(=+|-+)\s*$", content):
        content = "\\" + content
    return content + newline


def escape_plain_text_line(line):
    content = escape_markdown_heading_line(line)
    if "|" in content:
        content = content.replace("|", "\\|")
    return content


def render_fixed_table(rows, columns):
    headers = [escape_table_cell(title) for _, title in columns]
    rendered_rows = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for row in rows:
        cells = [escape_table_cell(row.get(field_key, "")) for field_key, _ in columns]
        rendered_rows.append("| " + " | ".join(cells) + " |")
    return "\n".join(rendered_rows)


def render_fixed_table_or_empty(rows, columns, empty_text):
    if not rows:
        return empty_text
    return render_fixed_table(rows, columns)


def row_display_label(row, id_key, label_key):
    row_id = re.sub(r"\s+", " ", stringify_markdown_value(row.get(id_key, ""))).strip()
    label = re.sub(r"\s+", " ", stringify_markdown_value(row.get(label_key, ""))).strip()
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


def build_module_display_names(document):
    rows = document.get("architecture_views", {}).get("module_intro", {}).get("rows", [])
    return {row.get("module_id"): row.get("module_name", "") for row in rows}


def build_runtime_unit_display_names(document):
    rows = document.get("runtime_view", {}).get("runtime_units", {}).get("rows", [])
    return {row.get("unit_id"): row.get("unit_name", "") for row in rows}


def display_names_for_refs(refs, display_names, reference_type):
    if refs is None:
        return ""
    if isinstance(refs, list):
        return [display_name_for_ref(ref, display_names, reference_type) for ref in refs]
    return display_name_for_ref(refs, display_names, reference_type)


def display_name_for_ref(ref, display_names, reference_type):
    if ref in display_names and display_names[ref] != "":
        return display_names[ref]
    raise RenderError(f"missing display name for {reference_type} reference")


def render_reference_summary(label, refs, display_names, reference_type):
    names = display_names_for_refs(refs, display_names, reference_type)
    rendered_names = stringify_markdown_value(names)
    if rendered_names == "":
        return ""
    return f"{label}：{escape_plain_text(rendered_names)}"


def rows_with_display_refs(rows, module_display_names, runtime_unit_display_names):
    mapped_rows = []
    for row in rows or []:
        mapped_row = dict(row)
        for key in ("related_module_ids", "participant_module_ids"):
            if key in mapped_row:
                mapped_row[key] = display_names_for_refs(mapped_row[key], module_display_names, "module")
        for key in ("related_runtime_unit_ids", "participant_runtime_unit_ids"):
            if key in mapped_row:
                mapped_row[key] = display_names_for_refs(
                    mapped_row[key], runtime_unit_display_names, "runtime unit"
                )
        if "initiator_module_id" in mapped_row:
            mapped_row["initiator_module_id"] = display_names_for_refs(
                mapped_row["initiator_module_id"], module_display_names, "module"
            )
        mapped_rows.append(mapped_row)
    return mapped_rows


def render_extra_table(table):
    columns = table.get("columns", [])
    rows = table.get("rows", [])
    declared_columns = [(column.get("key", ""), column.get("title", "")) for column in columns]
    title = escape_heading_label(table.get("title", ""))
    return f"#### {title}\n\n{render_fixed_table(rows, declared_columns)}"


def render_extra_diagram(diagram):
    title = escape_heading_label(diagram.get("title", ""))
    untitled_diagram = dict(diagram)
    untitled_diagram["title"] = ""
    return f"#### {title}\n\n{render_mermaid_block(untitled_diagram)}"


def render_extras(extra_tables, extra_diagrams, empty_text="无补充内容。"):
    parts = []
    for table in extra_tables or []:
        parts.append(render_extra_table(table))
    for diagram in extra_diagrams or []:
        parts.append(render_extra_diagram(diagram))
    if not parts:
        return empty_text
    return "\n\n".join(parts)


def render_mermaid_block(diagram, empty_text=None):
    source = ""
    if diagram:
        source = str(diagram.get("source") or "")
    if source == "":
        return empty_text or ""
    if "```" in source or "~~~" in source:
        raise RenderError("Mermaid source must not contain fenced code markers")

    parts = []
    title = diagram.get("title") if diagram else ""
    description = diagram.get("description") if diagram else ""
    if title:
        parts.append(escape_plain_text(title))
    if description:
        parts.append(escape_plain_text(description))
    parts.append(f"```mermaid\n{source}\n```")
    return "\n\n".join(parts)


def longest_backtick_run(content):
    runs = re.findall(r"`+", content)
    if not runs:
        return 0
    return max(len(run) for run in runs)


def render_source_snippet(snippet):
    content = str(snippet.get("content") or "")
    fence = "`" * max(3, longest_backtick_run(content) + 1)
    language = safe_fence_info_string(snippet.get("language", ""))
    path = escape_plain_text(snippet.get("path", "")).strip()
    line_start = escape_plain_text(snippet.get("line_start", "")).strip()
    line_end = escape_plain_text(snippet.get("line_end", "")).strip()
    purpose = escape_plain_text(snippet.get("purpose", "")).strip()

    details = []
    if path:
        if line_start or line_end:
            details.append(f"Source: {path}:{line_start}-{line_end}")
        else:
            details.append(f"Source: {path}")
    if purpose:
        details.append(f"Purpose: {purpose}")

    details.append(f"{fence}{language}\n{content}\n{fence}")
    return "\n\n".join(details)


def safe_fence_info_string(value):
    language = stringify_markdown_value(value).strip()
    if SAFE_FENCE_INFO_RE.fullmatch(language):
        return language
    return ""


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


def collapse_support_line(value):
    return re.sub(r"\s+", " ", stringify_markdown_value(value)).strip()


def render_support_lines(lines):
    rendered = []
    for line in lines:
        escaped = escape_plain_text(collapse_support_line(line)).strip()
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


def generated_at_value():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def chapter_heading(number, title):
    return f"## {number}. {title}"


def subchapter_heading(chapter_number, section_number, title):
    return f"### {chapter_number}.{section_number} {title}"


def nested_heading(chapter_number, section_number, nested_number, title):
    return f"#### {chapter_number}.{section_number}.{nested_number} {title}"


def escape_heading_label(value):
    escaped = escape_plain_text(value)
    return re.sub(r"\s+", " ", escaped).strip()


def render_paragraph(value, empty_text=""):
    text = stringify_markdown_value(value)
    if text == "":
        return empty_text
    return escape_plain_text(text)


def render_bullets(items):
    bullets = []
    for item in items or []:
        text = escape_plain_text(item).strip()
        if text:
            bullets.append(f"- {text}")
    return "\n".join(bullets)


def render_chapter_1(document):
    metadata = document["document"]
    rows = []
    for key, value in metadata.items():
        rendered_value = generated_at_value() if key == "generated_at" and value == "" else value
        rows.append({"field": key, "value": rendered_value})
    return "\n\n".join(
        [
            chapter_heading(1, "文档信息"),
            render_fixed_table(rows, [("field", "字段"), ("value", "值")]),
        ]
    )


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


def render_chapter_3(document, support_context):
    architecture = document["architecture_views"]
    parts = [
        chapter_heading(3, "架构视图"),
        subchapter_heading(3, 1, "架构概述"),
        render_paragraph(architecture.get("summary", "")),
        subchapter_heading(3, 2, "各模块介绍"),
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
        ),
        subchapter_heading(3, 3, "模块关系图"),
        render_mermaid_block(architecture.get("module_relationship_diagram", {}), empty_text="无模块关系图。"),
        subchapter_heading(3, 4, "补充架构图表"),
        render_extras(architecture.get("extra_tables", []), architecture.get("extra_diagrams", [])),
    ]
    return "\n\n".join(part for part in parts if part != "")


def module_designs_by_id(document):
    modules = document.get("module_design", {}).get("modules", [])
    return {module.get("module_id"): module for module in modules}


def ordered_module_designs(document):
    designs_by_id = module_designs_by_id(document)
    ordered = []
    seen_ids = set()
    for row in document.get("architecture_views", {}).get("module_intro", {}).get("rows", []):
        module_id = row.get("module_id")
        module = designs_by_id.get(module_id)
        if module is not None:
            ordered.append(module)
            seen_ids.add(module_id)
    for module in document.get("module_design", {}).get("modules", []):
        module_id = module.get("module_id")
        if module_id not in seen_ids:
            ordered.append(module)
    return ordered


def render_external_capability_summary(summary):
    parts = [render_paragraph(summary.get("description", ""))]
    consumers = render_bullets(summary.get("consumers", []))
    if consumers:
        parts.append("使用方：\n" + consumers)
    interface_style = render_paragraph(summary.get("interface_style", ""))
    if interface_style:
        parts.append(f"接口风格：{interface_style}")
    boundary_notes = render_bullets(summary.get("boundary_notes", []))
    if boundary_notes:
        parts.append("边界说明：\n" + boundary_notes)
    return "\n\n".join(part for part in parts if part != "")


def render_internal_structure(internal_structure):
    diagram = internal_structure.get("diagram", {})
    rendered_diagram = render_mermaid_block(diagram)
    if rendered_diagram:
        return rendered_diagram
    parts = [
        render_paragraph(internal_structure.get("textual_structure", "")),
        render_paragraph(internal_structure.get("not_applicable_reason", "")),
    ]
    return "\n\n".join(part for part in parts if part != "")


def render_module_supplement(module):
    details = module.get("external_capability_details", {})
    parts = []
    details_extras = render_extras(details.get("extra_tables", []), details.get("extra_diagrams", []), empty_text="")
    if details_extras:
        parts.append(details_extras)
    module_extras = render_extras(module.get("extra_tables", []), module.get("extra_diagrams", []), empty_text="")
    if module_extras:
        parts.append(module_extras)
    notes = render_bullets(module.get("notes", []))
    if notes:
        parts.append(notes)
    if not parts:
        return "无补充内容。"
    return "\n\n".join(parts)


def render_module_design_section(module, index):
    details = module.get("external_capability_details", {})
    provided = details.get("provided_capabilities", {})
    parts = [
        subchapter_heading(4, index, escape_heading_label(module.get("name", ""))),
        nested_heading(4, index, 1, "模块概述"),
        render_paragraph(module.get("summary", "")),
        nested_heading(4, index, 2, "模块职责"),
        render_bullets(module.get("responsibilities", [])),
        nested_heading(4, index, 3, "对外能力说明"),
        render_external_capability_summary(module.get("external_capability_summary", {})),
        nested_heading(4, index, 4, "对外接口需求清单"),
        render_fixed_table(
            provided.get("rows", []),
            [
                ("capability_name", "能力名称"),
                ("interface_style", "接口风格"),
                ("description", "描述"),
                ("inputs", "输入"),
                ("outputs", "输出"),
                ("notes", "备注"),
            ],
        ),
        nested_heading(4, index, 5, "模块内部结构关系图"),
        render_internal_structure(module.get("internal_structure", {})),
        nested_heading(4, index, 6, "补充说明"),
        render_module_supplement(module),
    ]
    return "\n\n".join(part for part in parts if part != "")


def render_chapter_4(document):
    module_design = document["module_design"]
    parts = [
        chapter_heading(4, "模块设计"),
        render_paragraph(module_design.get("summary", "")),
    ]
    for index, module in enumerate(ordered_module_designs(document), start=1):
        parts.append(render_module_design_section(module, index))
    return "\n\n".join(part for part in parts if part != "")


def render_chapter_5(document, module_display_names, support_context):
    runtime = document["runtime_view"]
    runtime_unit_rows = rows_with_display_refs(
        runtime.get("runtime_units", {}).get("rows", []),
        module_display_names,
        {},
    )
    parts = [
        chapter_heading(5, "运行时视图"),
        subchapter_heading(5, 1, "运行时概述"),
        render_paragraph(runtime.get("summary", "")),
        subchapter_heading(5, 2, "运行单元说明"),
        render_fixed_table_with_support(
            runtime_unit_rows,
            RUNTIME_UNIT_COLUMNS,
            support_context,
            id_key="unit_id",
            label_key="unit_name",
            target_type="runtime_unit",
        ),
        subchapter_heading(5, 3, "运行时流程图"),
        render_mermaid_block(runtime.get("runtime_flow_diagram", {})),
        subchapter_heading(5, 4, "运行时序图（推荐）"),
        render_mermaid_block(runtime.get("runtime_sequence_diagram", {}), empty_text="未提供运行时序图。"),
        subchapter_heading(5, 5, "补充运行时图表"),
        render_extras(runtime.get("extra_tables", []), runtime.get("extra_diagrams", [])),
    ]
    return "\n\n".join(part for part in parts if part != "")


def render_chapter_6(document, support_context):
    configuration = document["configuration_data_dependencies"]
    parts = [
        chapter_heading(6, "配置、数据与依赖关系"),
    ]
    summary = render_paragraph(configuration.get("summary", ""))
    if summary:
        parts.append(summary)
    parts.extend(
        [
            subchapter_heading(6, 1, "配置项说明"),
            render_fixed_table_or_empty_with_support(
                configuration.get("configuration_items", {}).get("rows", []),
                CONFIGURATION_ITEM_COLUMNS,
                "不适用。",
                support_context,
                id_key="config_id",
                label_key="config_name",
                target_type="configuration_item",
            ),
            subchapter_heading(6, 2, "关键结构数据与产物"),
            render_fixed_table_or_empty_with_support(
                configuration.get("structural_data_artifacts", {}).get("rows", []),
                STRUCTURAL_DATA_ARTIFACT_COLUMNS,
                "未识别到需要在结构设计阶段单独说明的关键结构数据或产物。",
                support_context,
                id_key="artifact_id",
                label_key="artifact_name",
                target_type="structural_data_artifact",
            ),
            subchapter_heading(6, 3, "依赖项说明"),
            render_fixed_table_or_empty_with_support(
                configuration.get("dependencies", {}).get("rows", []),
                DEPENDENCY_COLUMNS,
                "未识别到需要在结构设计阶段单独说明的外部依赖项。",
                support_context,
                id_key="dependency_id",
                label_key="dependency_name",
                target_type="dependency",
            ),
            subchapter_heading(6, 4, "补充图表"),
            render_extras(configuration.get("extra_tables", []), configuration.get("extra_diagrams", [])),
        ]
    )
    return "\n\n".join(part for part in parts if part != "")


def render_chapter_7(document, module_display_names, support_context):
    collaboration = document["cross_module_collaboration"]
    collaboration_rows = rows_with_display_refs(
        collaboration.get("collaboration_scenarios", {}).get("rows", []),
        module_display_names,
        {},
    )
    parts = [
        chapter_heading(7, "跨模块协作关系"),
        subchapter_heading(7, 1, "协作关系概述"),
        render_paragraph(collaboration.get("summary", "")),
        subchapter_heading(7, 2, "跨模块协作说明"),
        render_fixed_table_or_empty_with_support(
            collaboration_rows,
            COLLABORATION_COLUMNS,
            "本系统当前仅识别到一个结构模块，暂无跨模块协作关系。",
            support_context,
            id_key="collaboration_id",
            label_key="scenario",
            target_type="collaboration_scenario",
        ),
        subchapter_heading(7, 3, "跨模块协作关系图"),
        render_mermaid_block(
            collaboration.get("collaboration_relationship_diagram", {}),
            empty_text="未提供跨模块协作关系图。",
        ),
        subchapter_heading(7, 4, "补充协作图表"),
        render_extras(collaboration.get("extra_tables", []), collaboration.get("extra_diagrams", [])),
    ]
    return "\n\n".join(part for part in parts if part != "")


def flows_by_id(key_flows):
    return {flow.get("flow_id"): flow for flow in key_flows.get("flows", [])}


def render_key_flow_overview(flow, module_display_names, runtime_unit_display_names):
    parts = [
        render_paragraph(flow.get("overview", "")),
        render_reference_summary("关联模块", flow.get("related_module_ids", []), module_display_names, "module"),
        render_reference_summary(
            "关联运行单元", flow.get("related_runtime_unit_ids", []), runtime_unit_display_names, "runtime unit"
        ),
    ]
    return "\n\n".join(part for part in parts if part != "")


def render_key_flow_section(flow, section_number, module_display_names, runtime_unit_display_names):
    step_rows = rows_with_display_refs(
        sorted(flow.get("steps", []), key=lambda step: step.get("order", 0)),
        module_display_names,
        runtime_unit_display_names,
    )
    branch_rows = rows_with_display_refs(
        flow.get("branches_or_exceptions", []),
        module_display_names,
        runtime_unit_display_names,
    )
    parts = [
        subchapter_heading(8, section_number, escape_heading_label(flow.get("name", ""))),
        nested_heading(8, section_number, 1, "流程概述"),
        render_key_flow_overview(flow, module_display_names, runtime_unit_display_names),
        nested_heading(8, section_number, 2, "步骤说明"),
        render_fixed_table(step_rows, FLOW_STEP_COLUMNS),
        nested_heading(8, section_number, 3, "异常/分支说明"),
        render_fixed_table_or_empty(branch_rows, FLOW_BRANCH_COLUMNS, "未识别到异常或分支说明。"),
        nested_heading(8, section_number, 4, "流程图"),
        render_mermaid_block(flow.get("diagram", {})),
    ]
    return "\n\n".join(part for part in parts if part != "")


def render_chapter_8(document, module_display_names, runtime_unit_display_names):
    key_flows = document["key_flows"]
    flow_index_rows = rows_with_display_refs(
        key_flows.get("flow_index", {}).get("rows", []),
        module_display_names,
        runtime_unit_display_names,
    )
    parts = [
        chapter_heading(8, "关键流程"),
        subchapter_heading(8, 1, "关键流程概述"),
        render_paragraph(key_flows.get("summary", "")),
    ]
    extras = render_extras(key_flows.get("extra_tables", []), key_flows.get("extra_diagrams", []), empty_text="")
    if extras:
        parts.append(extras)
    parts.extend(
        [
            subchapter_heading(8, 2, "关键流程清单"),
            render_fixed_table(flow_index_rows, FLOW_INDEX_COLUMNS),
        ]
    )

    detail_by_id = flows_by_id(key_flows)
    for section_number, flow_row in enumerate(key_flows.get("flow_index", {}).get("rows", []), start=3):
        flow = detail_by_id.get(flow_row.get("flow_id"))
        if flow is not None:
            parts.append(render_key_flow_section(flow, section_number, module_display_names, runtime_unit_display_names))
    return "\n\n".join(part for part in parts if part != "")


def low_confidence_item_label(item):
    for key in LOW_CONFIDENCE_LABEL_KEYS:
        value = stringify_markdown_value(item.get(key, "")).strip()
        if value:
            return value
    item_id = stringify_markdown_value(item.get("id", "")).strip()
    if item_id:
        return item_id
    return "未命名项目"


def collect_low_confidence_items(document):
    items = []

    def add_item(path, item):
        if item.get("confidence") == "unknown":
            items.append(
                {
                    "path": path,
                    "label": low_confidence_item_label(item),
                    "confidence": item.get("confidence", ""),
                }
            )

    for index, row in enumerate(document.get("architecture_views", {}).get("module_intro", {}).get("rows", [])):
        add_item(f"$.architecture_views.module_intro.rows[{index}]", row)

    for module_index, module in enumerate(document.get("module_design", {}).get("modules", [])):
        add_item(f"$.module_design.modules[{module_index}]", module)
        capability_rows = (
            module.get("external_capability_details", {}).get("provided_capabilities", {}).get("rows", [])
        )
        for row_index, row in enumerate(capability_rows):
            add_item(
                "$.module_design.modules"
                f"[{module_index}].external_capability_details.provided_capabilities.rows[{row_index}]",
                row,
            )

    for index, row in enumerate(document.get("runtime_view", {}).get("runtime_units", {}).get("rows", [])):
        add_item(f"$.runtime_view.runtime_units.rows[{index}]", row)

    configuration = document.get("configuration_data_dependencies", {})
    for collection_name in ("configuration_items", "structural_data_artifacts", "dependencies"):
        for index, row in enumerate(configuration.get(collection_name, {}).get("rows", [])):
            add_item(f"$.configuration_data_dependencies.{collection_name}.rows[{index}]", row)

    collaboration = document.get("cross_module_collaboration", {})
    for index, row in enumerate(collaboration.get("collaboration_scenarios", {}).get("rows", [])):
        add_item(f"$.cross_module_collaboration.collaboration_scenarios.rows[{index}]", row)

    for flow_index, flow in enumerate(document.get("key_flows", {}).get("flows", [])):
        add_item(f"$.key_flows.flows[{flow_index}]", flow)
        for step_index, step in enumerate(flow.get("steps", [])):
            add_item(f"$.key_flows.flows[{flow_index}].steps[{step_index}]", step)
        for branch_index, branch in enumerate(flow.get("branches_or_exceptions", [])):
            add_item(f"$.key_flows.flows[{flow_index}].branches_or_exceptions[{branch_index}]", branch)

    return items


def render_chapter_9(document):
    parts = [chapter_heading(9, "结构问题与改进建议")]
    free_form_text = stringify_markdown_value(document.get("structure_issues_and_suggestions", "")).strip()
    risks = document.get("risks", [])
    assumptions = document.get("assumptions", [])
    low_confidence_items = collect_low_confidence_items(document)

    if free_form_text:
        parts.append(escape_plain_text(free_form_text))
    if risks:
        parts.extend(["### 风险", render_fixed_table(risks, RISK_COLUMNS)])
    if assumptions:
        parts.extend(["### 假设", render_fixed_table(assumptions, ASSUMPTION_COLUMNS)])
    if low_confidence_items:
        parts.extend(["### 低置信度项", render_fixed_table(low_confidence_items, LOW_CONFIDENCE_COLUMNS)])
    if len(parts) == 1:
        parts.append("未识别到明确的结构问题与改进建议。")

    return "\n\n".join(parts)


def build_parser():
    parser = argparse.ArgumentParser(description="Render create-structure-md DSL JSON to Markdown.")
    parser.add_argument("dsl_file", help="Path to structure DSL JSON.")
    parser.add_argument("--output-dir", default=".", help="Directory for the generated Markdown file.")
    output_group = parser.add_mutually_exclusive_group()
    output_group.add_argument("--overwrite", action="store_true", help="Replace an existing output file.")
    output_group.add_argument("--backup", action="store_true", help="Back up an existing output file before writing.")
    return parser


def load_json_file(path):
    path = Path(path)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise InputError(f"file not found: {path}")
    except OSError as exc:
        raise InputError(f"unable to read {path}: {exc}")
    except UnicodeDecodeError as exc:
        raise InputError(f"unable to read {path}: {exc}")
    except json.JSONDecodeError as exc:
        raise InputError(f"invalid JSON in {path}: line {exc.lineno}, column {exc.colno}: {exc.msg}")


def normalized_name_tokens(value):
    if not isinstance(value, str):
        raise TypeError("filename context values must be strings")
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


def validate_output_filename(document):
    try:
        output_file = document["document"]["output_file"]
    except (KeyError, TypeError):
        raise InputError("document.output_file must be a non-empty Markdown filename")

    if not isinstance(output_file, str) or output_file.strip() == "":
        raise InputError("document.output_file must be a non-empty Markdown filename")
    if not output_file.endswith(".md"):
        raise InputError("document.output_file must end with .md")
    if "/" in output_file or "\\" in output_file or ".." in output_file:
        raise InputError("document.output_file must be a simple filename without path segments")
    if CONTROL_CHARACTER_RE.search(output_file):
        raise InputError("document.output_file must not contain control characters")

    folded = output_file.casefold()
    output_tokens = normalized_name_tokens(Path(output_file).stem)
    generic_only = bool(output_tokens) and all(token in GENERIC_OUTPUT_TOKENS for token in output_tokens)
    if folded in GENERIC_OUTPUT_NAMES or generic_only:
        raise InputError("generic-only output filename is not allowed for document.output_file")

    try:
        concrete_tokens = documented_object_tokens(document)
    except (KeyError, TypeError) as exc:
        raise InputError(f"DSL shape is missing required filename context: {exc}")
    contains_concrete_token = any(token in output_tokens for token in concrete_tokens)
    if not contains_concrete_token:
        raise InputError("document.output_file must include a concrete documented object name")

    return output_file


def resolve_output_path(output_dir, output_file):
    output_dir = Path(output_dir)
    if not output_dir.exists():
        raise InputError(f"output directory not found: {output_dir}")
    if not output_dir.is_dir():
        raise InputError(f"output path is not a directory: {output_dir}")
    return output_dir / output_file


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


def backup_timestamp():
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def backup_path_for(output_path):
    output_path = Path(output_path)
    return output_path.with_name(f"{output_path.name}.bak-{backup_timestamp()}")


def copy_backup_file(output_path, backup_path):
    output_path = Path(output_path)
    backup_path = Path(backup_path)
    try:
        backup_bytes = output_path.read_bytes()
        with backup_path.open("xb") as destination:
            destination.write(backup_bytes)
        shutil.copystat(output_path, backup_path)
    except FileExistsError:
        raise RenderError(f"backup path already exists: {backup_path}; retry later")
    except OSError as exc:
        raise RenderError(f"failed to write backup path {backup_path}: {exc}")


def write_markdown_file(output_path, markdown, exclusive=False):
    try:
        if exclusive:
            with output_path.open("x", encoding="utf-8") as output_file:
                output_file.write(markdown)
        else:
            output_path.write_text(markdown, encoding="utf-8")
    except FileExistsError:
        raise RenderError(f"output file already exists: {output_path}; use --overwrite or --backup")
    except OSError as exc:
        raise RenderError(f"failed to write output file {output_path}: {exc}")


def write_output(output_path, markdown, overwrite=False, backup=False):
    output_path = Path(output_path)
    backup_path = None

    if output_path.exists() and not overwrite and not backup:
        raise RenderError(f"output file already exists: {output_path}; use --overwrite or --backup")

    if output_path.exists() and backup:
        backup_path = backup_path_for(output_path)
        if backup_path.exists():
            raise RenderError(f"backup path already exists: {backup_path}; retry later")
        copy_backup_file(output_path, backup_path)

    write_markdown_file(output_path, markdown, exclusive=not overwrite and backup_path is None)
    return backup_path


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        document = load_json_file(args.dsl_file)
        output_file = validate_output_filename(document)
        output_path = resolve_output_path(args.output_dir, output_file)
        markdown = render_markdown(document)
        backup_path = write_output(output_path, markdown, overwrite=args.overwrite, backup=args.backup)
    except InputError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return exc.exit_code
    except RenderError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return exc.exit_code

    if backup_path is not None:
        print(f"Backup written: {backup_path}")
    print(f"Markdown rendered: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
