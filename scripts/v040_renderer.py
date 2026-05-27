import re


def render_markdown(package) -> str:
    document = package.chapters["document"]["document"]
    overview = package.chapters["overview"]["overview"]
    quick_start = package.chapters["quick_start"]["quick_start"]
    architecture = package.chapters["architecture_overview"]["architecture_overview"]
    main_flows = package.chapters["main_flows"]["main_flows"]
    module_details = package.chapters["module_details"]["module_details"]

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
    renderer.blocks(overview["core_components"].get("blocks", []))
    renderer.extra_subsections(4, overview["extra_subsections"])

    renderer.heading(3, "快速开始")
    renderer.section(4, "使用场景", quick_start["usage_scenarios"])
    renderer.section(4, "准备工作", quick_start["setup"])
    renderer.heading(4, "第一次运行/接入")
    renderer.blocks(quick_start["first_run"].get("blocks", []))
    for index, step in enumerate(quick_start["first_run"]["steps"], start=1):
        renderer.heading(5, f'{index}. {step["title"]}')
        renderer.blocks(step.get("blocks", []))
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
    renderer.blocks(architecture["layers"].get("blocks", []))
    renderer.heading(4, "模块划分")
    renderer.fixed_table(
        ["模块", "作用", "所在层", "位置"],
        architecture["module_map"]["module_table"].get("rows", []),
        ["module", "role", "layer", "location"],
    )
    renderer.blocks(architecture["module_map"].get("blocks", []))
    renderer.section(4, "目录角色", architecture["repository_layout"])
    renderer.extra_subsections(4, architecture["extra_subsections"])

    renderer.heading(3, "主线流程")
    renderer.blocks(main_flows["flow_overview"].get("blocks", []))
    for flow in main_flows["flows"]:
        renderer.heading(4, flow["title"])
        renderer.paragraph(f'目的：{flow["purpose"]}')
        renderer.paragraph(f'入口：`{flow["entry"]["name"]}`')
        if flow["entry"].get("location"):
            renderer.paragraph(f'位置：{flow["entry"]["location"]}')
        renderer.blocks(flow.get("blocks", []))
    renderer.extra_subsections(4, main_flows["extra_subsections"])

    renderer.heading(3, "模块详解")
    renderer.blocks(module_details.get("intro_blocks", []))
    for module in module_details["modules"]:
        renderer.heading(4, module["name"])
        renderer.paragraph(f'位置：{module["location"]}')
        renderer.paragraph(f'职责：{module["purpose"]}')
        renderer.blocks(module.get("blocks", []))
        for mechanism in module.get("mechanisms", []):
            renderer.heading(5, mechanism["title"])
            renderer.blocks(mechanism.get("blocks", []))
        renderer.extra_subsections(5, module["extra_subsections"])
    renderer.extra_subsections(4, module_details["extra_subsections"])

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

    def section(self, level, title, section):
        self.heading(level, title)
        self.blocks(section.get("blocks", []))

    def blocks(self, blocks):
        for block in blocks:
            self.block(block)

    def block(self, block):
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
                self.paragraph(block["title"])
            self._parts.append(_fenced_code(block["language"], block["content"]))
        elif block_type == "mermaid":
            if block.get("title"):
                self.paragraph(block["title"])
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

    def extra_subsections(self, level, subsections):
        for subsection in subsections:
            self.heading(level, subsection["title"])
            self.blocks(subsection.get("blocks", []))


def _fenced_code(language, content):
    fence = "`" * _safe_backtick_fence_length(content)
    return f"{fence}{language}\n{content}\n{fence}"


def _safe_backtick_fence_length(content):
    runs = [len(match.group(0)) for match in re.finditer(r"`+", content)]
    return max(3, max(runs, default=0) + 1)


def _escape_table_cell(value):
    text = str(value).replace("\r\n", " ").replace("\r", " ").replace("\n", " ")
    return text.replace("|", r"\|")
