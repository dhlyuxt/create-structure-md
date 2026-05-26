from scripts.v030_package import ManifestPackage


EMPTY_MECHANISMS_SENTENCE = "本次分析未选择可深读的关键机制。"


def _line(lines: list[str], text: str = "") -> None:
    lines.append(text)


def _join(values) -> str:
    return "、".join(str(value) for value in values if value)


def _sentence(text: str) -> str:
    if text.endswith(("。", "！", "？", ".", "!", "?")):
        return text
    return f"{text}。"


def _source_ref(source_ref: dict) -> str:
    if not source_ref:
        return ""
    path = source_ref.get("path", "")
    symbol = source_ref.get("symbol")
    return f"{path}::{symbol}" if symbol else path


def _source_refs(source_refs: list[dict]) -> str:
    return _join(_source_ref(source_ref) for source_ref in source_refs)


def _with_parenthesized_source(text: str, source_ref: dict | None) -> str:
    source = _source_ref(source_ref or {})
    return f"{text}（{source}）" if source else text


def _table_cell(value) -> str:
    if value is None:
        return "-"
    text = str(value).strip()
    if not text:
        return "-"
    return text.replace("|", "\\|").replace("\n", "<br>")


def _table(lines: list[str], headers: list[str], rows: list[list]) -> None:
    if not rows:
        return
    _line(lines, "| " + " | ".join(_table_cell(header) for header in headers) + " |")
    _line(lines, "| " + " | ".join("---" for _ in headers) + " |")
    for row in rows:
        _line(lines, "| " + " | ".join(_table_cell(value) for value in row) + " |")
    _line(lines)


def _list_cell(values) -> str:
    return "<br>".join(str(value) for value in values if value) or "-"


def _source_refs_cell(source_refs: list[dict]) -> str:
    return _list_cell(_source_ref(source_ref) for source_ref in source_refs)


def _location_text(location: dict) -> str:
    return _with_parenthesized_source(location["description"], location.get("source_ref"))


def _location_summary(location: dict) -> str:
    if not location:
        return "-"
    kind = location.get("kind")
    if kind == "manifest_path":
        return location.get("path", "-")
    if kind == "chapter":
        return location.get("chapter", "-")
    if location.get("path"):
        return _source_ref(location)
    return kind or "-"


def _bullet(lines: list[str], text: str) -> None:
    if text:
        _line(lines, f"- {text}")


def _numbered(lines: list[str], index: int, text: str) -> None:
    if text:
        _line(lines, f"{index}. {text}")


def _diagram(lines: list[str], diagram: dict, *, level: int = 3) -> None:
    _line(lines, f"{'#' * level} {diagram['title']}")
    _line(lines)
    _line(lines, diagram["description"])
    _line(lines)
    _line(lines, "```mermaid")
    _line(lines, diagram["source"])
    _line(lines, "```")
    _line(lines)


def _module_name_map(package: ManifestPackage) -> dict[str, str]:
    modules = package.chapters["module_layers"]["modules"]
    return {module["module_id"]: module["name"] for module in modules}


def _mechanism_name_map(package: ManifestPackage) -> dict[str, str]:
    return {mechanism.key: mechanism.data["section"]["title"] for mechanism in package.mechanisms}


def _module_names(module_refs: list[str], names: dict[str, str]) -> str:
    return _join(names.get(module_ref, module_ref) for module_ref in module_refs)


def _mechanism_names(mechanism_refs: list[str], names: dict[str, str]) -> str:
    return _join(names.get(mechanism_ref, mechanism_ref) for mechanism_ref in mechanism_refs)


def _chapter1(lines: list[str], chapter: dict) -> None:
    document = chapter["document"]
    repository = chapter["repository"]
    scope = chapter["scope"]
    confidence = chapter["confidence"]
    _line(lines, "## 1. 文档说明")
    _line(lines)
    _table(
        lines,
        ["字段", "值"],
        [
            ["文档版本", document["version"]],
            ["状态", document["status"]],
            ["语言", document["language"]],
            ["生成时间", document["generated_at"]],
            ["仓库", f"{repository['name']}（{repository['root_display_path']}）"],
            ["仓库类型", repository["kind"]],
            ["主要语言", _join(repository["primary_languages"])],
        ],
    )
    _line(lines, "### 范围")
    _table(
        lines,
        ["类型", "范围", "说明"],
        [["包含", item["area"], item["description"]] for item in scope["included"]]
        + [["不包含", item["area"], item["reason"]] for item in scope["excluded"]],
    )
    _line(lines, "### 可信度")
    _table(
        lines,
        ["项目", "内容"],
        [
            ["级别", confidence["level"]],
            ["摘要", confidence["summary"]],
            ["验证缺口", _list_cell(confidence["validation_gaps"])],
        ],
    )


def _chapter2(lines: list[str], chapter: dict) -> None:
    overview = chapter["overview"]
    route = chapter["reading_route"]
    orientation = chapter["reader_orientation"]
    _line(lines, "## 2. 仓库概述与阅读路线")
    _line(lines)
    _line(lines, overview["summary"])
    _line(lines)
    _table(
        lines,
        ["项目", "内容"],
        [
            ["问题域", overview["problem_domain"]],
            ["仓库目标", overview["repository_purpose"]],
            ["目标读者", _list_cell(overview["target_readers"])],
        ],
    )
    _line(lines, "### 核心能力")
    _table(
        lines,
        ["能力", "描述", "入口", "备注"],
        [
            [
                capability["name"],
                capability["description"],
                _source_refs_cell(capability.get("entry_points", [])),
                capability.get("notes", ""),
            ]
            for capability in chapter["core_capabilities"]
        ],
    )
    _line(lines, "### 阅读路线")
    _line(lines, route["summary"])
    _line(lines)
    _table(
        lines,
        ["顺序", "主题", "为什么读", "推荐文件", "目标收获"],
        [
            [
                step["order"],
                step["title"],
                step["why_read_this"],
                _list_cell(f"{item['path']}（{item['reason']}）" for item in step["recommended_files"]),
                step["expected_takeaway"],
            ]
            for step in route["steps"]
        ],
    )
    _table(
        lines,
        ["阅读顺序", "内容"],
        [
            ["先读", _list_cell(orientation["read_first"])],
            ["后读", _list_cell(orientation["read_later"])],
            ["可暂跳过", _list_cell(orientation["can_skip_initially"])],
        ],
    )


def _chapter3(lines: list[str], chapter: dict) -> None:
    _line(lines, "## 3. 目录地图")
    _line(lines)
    _line(lines, chapter["summary"])
    _line(lines)
    _line(lines, "### 目录分组")
    _table(
        lines,
        ["分组", "职责", "路径", "阅读时机", "备注"],
        [
            [group["name"], group["responsibility"], _list_cell(group["paths"]), group["read_when"], group.get("notes", "")]
            for group in chapter["directory_groups"]
        ],
    )
    _line(lines, "### 重要文件")
    _table(
        lines,
        ["文件", "角色", "重要性"],
        [[item["path"], item["role"], item["why_it_matters"]] for item in chapter["important_files"]],
    )
    relationships = chapter["directory_relationships"]
    _line(lines, relationships["summary"])
    if "diagram" in relationships:
        _line(lines)
        _diagram(lines, relationships["diagram"])
    else:
        _line(lines)
    if chapter["boundary_notes"]:
        _line(lines, "### 边界说明")
        _table(lines, ["区域", "说明"], [[note["area"], note["note"]] for note in chapter["boundary_notes"]])


def _chapter4(lines: list[str], chapter: dict, module_names: dict[str, str]) -> None:
    _line(lines, "## 4. 系统分层与模块职责")
    _line(lines)
    _line(lines, chapter["summary"])
    _line(lines)
    if "layer_diagram" in chapter:
        _diagram(lines, chapter["layer_diagram"])
    _line(lines, "### 分层")
    _table(
        lines,
        ["层", "角色", "职责", "路径", "备注"],
        [
            [layer["name"], layer["role"], _list_cell(layer["responsibilities"]), _list_cell(layer["paths"]), layer.get("notes", "")]
            for layer in chapter["layers"]
        ],
    )
    _line(lines, "### 模块职责")
    layer_names = {layer["layer_id"]: layer["name"] for layer in chapter["layers"]}
    _table(
        lines,
        ["层", "模块", "目的", "源码路径", "阅读时机"],
        [
            [
                layer_names.get(module["layer_id"], "其他模块"),
                module["name"],
                module["purpose"],
                _list_cell(module["source_paths"]),
                module["read_when"],
            ]
            for module in chapter["modules"]
        ],
    )
    for module in chapter["modules"]:
        _line(lines, f"#### {module['name']}")
        _line(lines)
        _table(
            lines,
            ["项目", "内容"],
            [
                ["所在层", layer_names.get(module["layer_id"], "其他模块")],
                ["负责", _list_cell(module["owns"])],
                ["消费", _list_cell(module["consumes"])],
                ["产出", _list_cell(module["produces"])],
                ["不负责", _list_cell(module["does_not_own"])],
                ["备注", module.get("notes", "")],
            ],
        )
        if module.get("collaborates_with"):
            _line(lines, "##### 协作")
            _table(
                lines,
                ["协作模块", "关系"],
                [
                    [module_names.get(item["module_ref"], item["module_ref"]), item["relationship"]]
                    for item in module.get("collaborates_with", [])
                ],
            )
    if chapter["boundary_notes"]:
        _line(lines, "### 边界说明")
        _table(lines, ["主题", "说明"], [[note["topic"], note["note"]] for note in chapter["boundary_notes"]])


def _chapter5(lines: list[str], chapter: dict, module_names: dict[str, str]) -> None:
    _line(lines, "## 5. 仓库主线")
    _line(lines)
    _line(lines, chapter["summary"])
    _line(lines)
    _diagram(lines, chapter["mainline_overview_diagram"])
    for mainline_index, mainline in enumerate(chapter["mainlines"], start=1):
        _line(lines, f"### 5.{mainline_index} {mainline['name']}")
        _line(lines)
        _line(lines, mainline["purpose"])
        _line(lines)
        entry = mainline["entry"]
        _table(
            lines,
            ["项目", "名称", "类型", "描述", "参考"],
            [["入口", entry["name"], entry["kind"], entry["description"], _source_ref(entry.get("source_ref", {}))]],
        )
        _table(
            lines,
            ["序号", "步骤", "影响", "模块", "参考"],
            [
                [
                    step["order"],
                    step["step"],
                    step["effect"],
                    _module_names(step.get("module_refs", []), module_names),
                    _source_refs_cell(step.get("source_refs", [])),
                ]
                for step in mainline["steps"]
            ],
        )
        if "detail_diagram" in mainline:
            _diagram(lines, mainline["detail_diagram"], level=4)
        _table(lines, ["项目", "内容"], [["结果", mainline["result"]], ["备注", mainline.get("notes", "")]])
    if chapter["cross_mainline_notes"]:
        _line(lines, "### 跨主线说明")
        _table(lines, ["主题", "说明"], [[note["topic"], note["note"]] for note in chapter["cross_mainline_notes"]])


def _chapter6(lines: list[str], package: ManifestPackage, module_names: dict[str, str]) -> None:
    _line(lines, "## 6. 关键机制深读")
    _line(lines)
    if not package.mechanisms:
        _line(lines, EMPTY_MECHANISMS_SENTENCE)
        _line(lines)
        return
    for mechanism_index, mechanism in enumerate(package.mechanisms, start=1):
        data = mechanism.data
        _line(lines, f"### 6.{mechanism_index} {data['section']['title']}")
        _line(lines)
        _line(lines, data["why_it_matters"])
        _line(lines)
        _table(
            lines,
            ["项目", "内容"],
            [
                ["阅读前提", _list_cell(data["reader_prerequisites"])],
                ["相关模块", _module_names(data.get("related_modules", []), module_names)],
            ],
        )
        _table(
            lines,
            ["源码焦点", "关注原因"],
            [[_source_ref(focus["source_ref"]), focus["reason"]] for focus in data["source_focus"]],
        )
        _line(lines, data["mechanism_overview"])
        _line(lines)
        if "diagram" in data:
            _diagram(lines, data["diagram"], level=4)
        _line(lines, "#### 流程")
        _table(
            lines,
            ["序号", "步骤", "数据或状态", "参考", "备注"],
            [
                [
                    step["order"],
                    step["step"],
                    _sentence(step["state_or_data"]),
                    _source_refs_cell(step.get("source_refs", [])),
                    step.get("notes", ""),
                ]
                for step in data["flow"]
            ],
        )
        _line(lines, "#### 关键状态与数据")
        _table(
            lines,
            ["名称", "类型", "说明", "参考"],
            [
                [item["name"], item["kind"], item["description"], _source_refs_cell(item.get("source_refs", []))]
                for item in data["key_states_or_data"]
            ],
        )
        _line(lines, "#### 常见误解")
        _table(
            lines,
            ["误解", "更正"],
            [[item["misunderstanding"], item["correction"]] for item in data["common_misunderstandings"]],
        )
        _line(lines, "#### 验证缺口")
        _table(lines, ["验证缺口"], [[gap] for gap in data["validation_gaps"]])
        _table(lines, ["项目", "内容"], [["可信度", data["confidence"]]])


def _chapter7(lines: list[str], chapter: dict) -> None:
    _line(lines, "## 7. 配置、移植与集成边界")
    _line(lines)
    _line(lines, chapter["summary"])
    _line(lines)
    _line(lines, "### 必需配置")
    _table(
        lines,
        ["名称", "类型", "用途", "位置", "要求", "备注"],
        [
            [item["name"], item["kind"], item["purpose"], _location_text(item["location"]), item["required_when"], item.get("notes", "")]
            for item in chapter["required_configuration"]
        ],
    )
    _line(lines, "### 必需适配")
    _table(
        lines,
        ["名称", "类型", "职责", "消费者", "位置", "缺失影响"],
        [
            [
                item["name"],
                item["kind"],
                item["responsibility"],
                item["caller_or_consumer"],
                _location_text(item["location"]),
                item["failure_if_missing"],
            ]
            for item in chapter["required_adaptations"]
        ],
    )
    _line(lines, "### 集成路径")
    _table(
        lines,
        ["路径", "场景", "推荐入口", "步骤", "示例", "备注"],
        [
            [
                path["name"],
                path["scenario"],
                _with_parenthesized_source(path["recommended_entry"]["description"], path["recommended_entry"].get("source_ref")),
                _list_cell(path["steps"]),
                _list_cell(path["reference_examples"]),
                path.get("notes", ""),
            ]
            for path in chapter["integration_paths"]
        ],
    )
    _line(lines, "### 外部依赖与边界")
    _table(
        lines,
        ["依赖", "类型", "用于", "集成角色", "备注"],
        [
            [item["name"], item["kind"], item["used_by"], item["integration_role"], item.get("notes", "")]
            for item in chapter["external_dependencies"]
        ],
    )
    _table(
        lines,
        ["主题", "责任方", "原因"],
        [[item["topic"], item["owner"], item["reason"]] for item in chapter["out_of_scope_responsibilities"]],
    )


def _chapter8(lines: list[str], chapter: dict, module_names: dict[str, str], mechanism_names: dict[str, str]) -> None:
    _line(lines, "## 8. 风险、假设与验证缺口")
    _line(lines)
    _line(lines, chapter["summary"])
    _line(lines)
    _line(lines, "### 风险")
    _table(
        lines,
        ["风险", "影响", "缓解", "相关模块", "相关机制", "可信度"],
        [
            [
                risk["description"],
                risk["impact"],
                risk["mitigation"],
                _module_names(risk.get("related_modules", []), module_names),
                _mechanism_names(risk.get("related_mechanisms", []), mechanism_names),
                risk["confidence"],
            ]
            for risk in chapter["risks"]
        ],
    )
    _line(lines, "### 假设")
    _table(
        lines,
        ["假设", "依据", "验证建议", "可信度"],
        [
            [assumption["description"], assumption["rationale"], assumption["validation_suggestion"], assumption["confidence"]]
            for assumption in chapter["assumptions"]
        ],
    )
    _line(lines, "### 验证缺口")
    _table(
        lines,
        ["缺口", "类型", "重要性", "建议验证", "相关章节", "可信度"],
        [
            [
                gap["description"],
                gap["gap_type"],
                gap["why_it_matters"],
                gap["suggested_validation"],
                _list_cell(gap.get("related_chapters", [])),
                gap["confidence"],
            ]
            for gap in chapter["validation_gaps"]
        ],
    )
    _line(lines, "### 低可信项")
    _table(
        lines,
        ["项目", "位置", "说明", "原因", "需要证据"],
        [
            [
                item.get("item_id", ""),
                _location_summary(item.get("location", {})),
                item["description"],
                item["reason"],
                item["needed_evidence"],
            ]
            for item in chapter["low_confidence_items"]
        ],
    )


def render_markdown(package: ManifestPackage) -> str:
    """Render a validated 0.3.0 manifest package as fixed-order Markdown."""
    lines: list[str] = []
    module_names = _module_name_map(package)
    mechanism_names = _mechanism_name_map(package)
    title = package.chapters["document"]["document"]["title"]
    _line(lines, f"# {title}")
    _line(lines)
    _chapter1(lines, package.chapters["document"])
    _chapter2(lines, package.chapters["repository_overview"])
    _chapter3(lines, package.chapters["directory_map"])
    _chapter4(lines, package.chapters["module_layers"], module_names)
    _chapter5(lines, package.chapters["repository_mainline"], module_names)
    _chapter6(lines, package, module_names)
    _chapter7(lines, package.chapters["integration_boundaries"])
    _chapter8(lines, package.chapters["risks_validation"], module_names, mechanism_names)
    return "\n".join(lines).rstrip() + "\n"
