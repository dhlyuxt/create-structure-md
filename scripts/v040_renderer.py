import re


def render_markdown(package) -> str:
    document = package.chapters["document"]["document"]
    overview = package.chapters["overview"]["overview"]
    quick_start = package.chapters["quick_start"]["quick_start"]
    architecture = package.chapters["architecture_overview"]["architecture_overview"]
    main_flow_overview = package.chapters["main_flow_overview"]["main_flow_overview"]
    module_overview = package.chapters["module_overview"]["module_overview"]

    renderer = _MarkdownRenderer()
    renderer.heading(1, f'{document["repository_name"]} 结构说明')

    renderer.heading(2, "入门")
    renderer.heading(3, "概述")
    renderer.section(4, "当前仓库介绍", overview["repository_intro"])
    renderer.section(4, "解决的问题", overview["problems_solved"])
    renderer.section(4, "主要功能", overview["main_capabilities"])
    renderer.heading(4, "核心组件")
    renderer.fixed_table(
        ["组件", "作用", "位置"],
        overview["core_components"]["component_table"].get("rows", []),
        ["component", "role", "location"],
    )
    renderer.blocks(overview["core_components"].get("blocks", []), 5)
    renderer.extra_subsections(4, overview["extra_subsections"])

    renderer.heading(3, "快速开始")
    renderer.section(4, "使用场景", quick_start["usage_scenarios"])
    renderer.section(4, "准备工作", quick_start["setup"])
    renderer.heading(4, "第一次运行/接入")
    renderer.blocks(quick_start["first_run"].get("blocks", []), 5)
    for index, step in enumerate(quick_start["first_run"]["steps"], start=1):
        renderer.heading(5, f'{index}. {step["title"]}')
        renderer.blocks(step.get("blocks", []), 6)
    renderer.section(4, "最小示例", quick_start["minimal_example"])
    renderer.section(4, "预期结果", quick_start["expected_result"])
    renderer.extra_subsections(4, quick_start["extra_subsections"])

    renderer.heading(2, "深入解析")
    renderer.heading(3, "架构概述")
    renderer.section(4, "架构总览", architecture["architecture_summary"])
    renderer.heading(4, "软件分层")
    renderer.fixed_table(
        ["层", "作用", "位置"],
        architecture["layers"]["layer_table"].get("rows", []),
        ["layer", "role", "location"],
    )
    renderer.blocks(architecture["layers"].get("blocks", []), 5)
    renderer.heading(4, "模块划分")
    renderer.fixed_table(
        ["模块", "作用", "所在层", "位置"],
        architecture["module_map"]["module_table"].get("rows", []),
        ["module", "role", "layer", "location"],
    )
    renderer.blocks(architecture["module_map"].get("blocks", []), 5)
    renderer.section(4, "目录角色", architecture["repository_layout"])
    renderer.extra_subsections(4, architecture["extra_subsections"])

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

    return renderer.render()


class _MarkdownRenderer:
    def __init__(self):
        self._parts = []

    def render(self):
        return "\n\n".join(self._parts).rstrip() + "\n"

    def heading(self, level, title):
        self._parts.append(f'{"#" * level} {title}')

    def paragraph(self, content):
        self._parts.append(str(content))

    def unordered_list(self, items):
        self._parts.append("\n".join(f"- {item}" for item in items))

    def section(self, level, title, section):
        self.heading(level, title)
        self.blocks(section.get("blocks", []), level + 1)

    def blocks(self, blocks, title_level):
        for block in blocks:
            self.block(block, title_level)

    def block(self, block, title_level):
        block_type = block["type"]
        if block_type == "text":
            self.paragraph(block["content"])
        elif block_type == "unordered_list":
            self._parts.append("\n".join(f"- {item}" for item in block["items"]))
        elif block_type == "ordered_list":
            self._parts.append("\n".join(f"1. {item}" for item in block["items"]))
        elif block_type == "table":
            self.table(block["columns"], block.get("rows", []))
        elif block_type == "code":
            if block.get("title"):
                self.heading(title_level, block["title"])
            self._parts.append(_fenced_code(block["language"], block["content"]))
        elif block_type == "mermaid":
            if block.get("title"):
                self.heading(title_level, block["title"])
            self._parts.append(_fenced_code("mermaid", block["source"]))

    def table(self, columns, rows):
        escaped_columns = [_escape_table_cell(column) for column in columns]
        lines = [
            "| " + " | ".join(escaped_columns) + " |",
            "| " + " | ".join("---" for _ in columns) + " |",
        ]
        for row in rows:
            escaped_row = [_escape_table_cell(cell) for cell in row]
            lines.append("| " + " | ".join(escaped_row) + " |")
        self._parts.append("\n".join(lines))

    def fixed_table(self, columns, rows, keys):
        rendered_rows = [[row[key] for key in keys] for row in rows]
        self.table(columns, rendered_rows)

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

    def extra_subsections(self, level, subsections):
        for subsection in subsections:
            self.heading(level, subsection["title"])
            self.blocks(subsection.get("blocks", []), level + 1)


def _fenced_code(language, content):
    fence = "`" * _safe_backtick_fence_length(content)
    return f"{fence}{language}\n{content}\n{fence}"


def _safe_backtick_fence_length(content):
    runs = [len(match.group(0)) for match in re.finditer(r"`+", content)]
    return max(3, max(runs, default=0) + 1)


def _markdown_link(label, anchor):
    href = "#" + str(anchor).strip().replace(" ", "-")
    return f"[{label}]({href})"


def _escape_table_cell(value):
    text = str(value).replace("\r\n", " ").replace("\r", " ").replace("\n", " ")
    return text.replace("|", r"\|")
