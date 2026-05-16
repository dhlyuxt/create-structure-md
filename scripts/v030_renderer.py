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
    _bullet(lines, f"文档版本：{document['version']}")
    _bullet(lines, f"状态：{document['status']}")
    _bullet(lines, f"语言：{document['language']}")
    _bullet(lines, f"生成时间：{document['generated_at']}")
    _bullet(lines, f"仓库：{repository['name']}（{repository['root_display_path']}）")
    _bullet(lines, f"仓库类型：{repository['kind']}")
    _bullet(lines, f"主要语言：{_join(repository['primary_languages'])}")
    _line(lines)
    _line(lines, "### 范围")
    for item in scope["included"]:
        _bullet(lines, f"包含 {item['area']}：{item['description']}")
    for item in scope["excluded"]:
        _bullet(lines, f"不包含 {item['area']}：{item['reason']}")
    _line(lines)
    _line(lines, "### 可信度")
    _bullet(lines, f"{confidence['level']}：{confidence['summary']}")
    for gap in confidence["validation_gaps"]:
        _bullet(lines, f"验证缺口：{gap}")
    _line(lines)


def _chapter2(lines: list[str], chapter: dict) -> None:
    overview = chapter["overview"]
    route = chapter["reading_route"]
    orientation = chapter["reader_orientation"]
    _line(lines, "## 2. 仓库概述与阅读路线")
    _line(lines)
    _line(lines, overview["summary"])
    _line(lines)
    _bullet(lines, f"问题域：{overview['problem_domain']}")
    _bullet(lines, f"仓库目标：{overview['repository_purpose']}")
    _bullet(lines, f"目标读者：{_join(overview['target_readers'])}")
    _line(lines)
    _line(lines, "### 核心能力")
    for capability in chapter["core_capabilities"]:
        entry_points = _source_refs(capability.get("entry_points", []))
        _bullet(lines, f"{capability['name']}：{capability['description']}")
        _bullet(lines, f"入口：{entry_points}")
        _bullet(lines, capability.get("notes", ""))
    _line(lines)
    _line(lines, "### 阅读路线")
    _line(lines, route["summary"])
    for step in route["steps"]:
        files = _join(f"{item['path']}（{item['reason']}）" for item in step["recommended_files"])
        _numbered(lines, step["order"], f"{step['title']}：{step['why_read_this']} 推荐阅读 {files}。目标收获：{step['expected_takeaway']}")
    _line(lines)
    _bullet(lines, f"先读：{_join(orientation['read_first'])}")
    _bullet(lines, f"后读：{_join(orientation['read_later'])}")
    _bullet(lines, f"可暂跳过：{_join(orientation['can_skip_initially'])}")
    _line(lines)


def _chapter3(lines: list[str], chapter: dict) -> None:
    _line(lines, "## 3. 目录地图")
    _line(lines)
    _line(lines, chapter["summary"])
    _line(lines)
    _line(lines, "### 目录分组")
    for group in chapter["directory_groups"]:
        _bullet(lines, f"{group['name']}：{group['responsibility']} 路径：{_join(group['paths'])}。阅读时机：{group['read_when']} {group.get('notes', '')}")
    _line(lines)
    _line(lines, "### 重要文件")
    for item in chapter["important_files"]:
        _bullet(lines, f"{item['path']}：{item['role']}。{item['why_it_matters']}")
    _line(lines)
    relationships = chapter["directory_relationships"]
    _line(lines, relationships["summary"])
    if "diagram" in relationships:
        _line(lines)
        _diagram(lines, relationships["diagram"])
    for note in chapter["boundary_notes"]:
        _bullet(lines, f"{note['area']}：{note['note']}")
    _line(lines)


def _chapter4(lines: list[str], chapter: dict, module_names: dict[str, str]) -> None:
    _line(lines, "## 4. 系统分层与模块职责")
    _line(lines)
    _line(lines, chapter["summary"])
    _line(lines)
    if "layer_diagram" in chapter:
        _diagram(lines, chapter["layer_diagram"])
    _line(lines, "### 分层")
    for layer in chapter["layers"]:
        _bullet(lines, f"{layer['name']}：{layer['role']} 职责：{_join(layer['responsibilities'])}。路径：{_join(layer['paths'])}。{layer.get('notes', '')}")
    _line(lines)
    _line(lines, "### 模块职责")
    for module in chapter["modules"]:
        collaborators = _join(f"{module_names.get(item['module_ref'], item['module_ref'])}（{item['relationship']}）" for item in module.get("collaborates_with", []))
        _bullet(lines, f"{module['name']}：{module['purpose']} 负责 {_join(module['owns'])}；消费 {_join(module['consumes'])}；产出 {_join(module['produces'])}；不负责 {_join(module['does_not_own'])}。阅读时机：{module['read_when']} {module.get('notes', '')}")
        if collaborators:
            _bullet(lines, f"协作：{collaborators}")
    _line(lines)
    for note in chapter["boundary_notes"]:
        _bullet(lines, f"{note['topic']}：{note['note']}")
    _line(lines)


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
        entry_text = _with_parenthesized_source(f"入口：{entry['name']}，{entry['description']}", entry.get("source_ref"))
        _bullet(lines, entry_text)
        for step in mainline["steps"]:
            modules = _module_names(step.get("module_refs", []), module_names)
            sources = _source_refs(step.get("source_refs", []))
            suffix = f" 模块：{modules}。" if modules else ""
            source_suffix = f" 参考：{sources}。" if sources else ""
            _numbered(lines, step["order"], f"{step['step']} 影响：{step['effect']}。{suffix}{source_suffix}")
        if "detail_diagram" in mainline:
            _line(lines)
            _diagram(lines, mainline["detail_diagram"], level=4)
        _bullet(lines, f"结果：{mainline['result']}")
        _bullet(lines, mainline.get("notes", ""))
        _line(lines)
    for note in chapter["cross_mainline_notes"]:
        _bullet(lines, f"{note['topic']}：{note['note']}")
    _line(lines)


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
        _bullet(lines, f"阅读前提：{_join(data['reader_prerequisites'])}")
        _bullet(lines, f"相关模块：{_module_names(data.get('related_modules', []), module_names)}")
        for focus in data["source_focus"]:
            _bullet(lines, f"源码焦点：{_source_ref(focus['source_ref'])}，{focus['reason']}")
        _line(lines)
        _line(lines, data["mechanism_overview"])
        _line(lines)
        if "diagram" in data:
            _diagram(lines, data["diagram"], level=4)
        _line(lines, "#### 流程")
        for step in data["flow"]:
            sources = _source_refs(step.get("source_refs", []))
            source_text = f"参考：{sources}。" if sources else ""
            _numbered(lines, step["order"], f"{step['step']} 数据/状态：{_sentence(step['state_or_data'])}{source_text}{step.get('notes', '')}")
        _line(lines)
        _line(lines, "#### 关键状态与数据")
        for item in data["key_states_or_data"]:
            sources = _source_refs(item.get("source_refs", []))
            detail = f"{item['kind']}，{sources}" if sources else item["kind"]
            _bullet(lines, f"{item['name']}：{item['description']}（{detail}）")
        _line(lines)
        _line(lines, "#### 常见误解")
        for item in data["common_misunderstandings"]:
            _bullet(lines, f"{item['misunderstanding']} 更正：{item['correction']}")
        for gap in data["validation_gaps"]:
            _bullet(lines, f"验证缺口：{gap}")
        _bullet(lines, f"可信度：{data['confidence']}")
        _line(lines)


def _chapter7(lines: list[str], chapter: dict) -> None:
    _line(lines, "## 7. 配置、移植与集成边界")
    _line(lines)
    _line(lines, chapter["summary"])
    _line(lines)
    _line(lines, "### 必需配置")
    for item in chapter["required_configuration"]:
        location = item["location"]
        location_text = _with_parenthesized_source(location["description"], location.get("source_ref"))
        _bullet(lines, f"{item['name']}：{item['purpose']}。位置：{location_text}。要求：{item['required_when']} {item.get('notes', '')}")
    _line(lines)
    _line(lines, "### 必需适配")
    for item in chapter["required_adaptations"]:
        location = item["location"]
        location_text = _with_parenthesized_source(location["description"], location.get("source_ref"))
        _bullet(lines, f"{item['name']}：{item['responsibility']}。消费者：{item['caller_or_consumer']}。位置：{location_text}。缺失影响：{item['failure_if_missing']}")
    _line(lines)
    _line(lines, "### 集成路径")
    for path in chapter["integration_paths"]:
        entry = path["recommended_entry"]
        entry_text = _with_parenthesized_source(entry["description"], entry.get("source_ref"))
        _bullet(lines, f"{path['name']}：{path['scenario']} 推荐入口：{entry_text}。步骤：{_join(path['steps'])}。示例：{_join(path['reference_examples'])}。{path.get('notes', '')}")
    _line(lines)
    _line(lines, "### 外部依赖与边界")
    for item in chapter["external_dependencies"]:
        _bullet(lines, f"{item['name']}：{item['integration_role']}。用于：{item['used_by']}。{item.get('notes', '')}")
    for item in chapter["out_of_scope_responsibilities"]:
        _bullet(lines, f"{item['topic']} 由 {item['owner']} 负责：{item['reason']}")
    _line(lines)


def _chapter8(lines: list[str], chapter: dict, module_names: dict[str, str], mechanism_names: dict[str, str]) -> None:
    _line(lines, "## 8. 风险、假设与验证缺口")
    _line(lines)
    _line(lines, chapter["summary"])
    _line(lines)
    _line(lines, "### 风险")
    for risk in chapter["risks"]:
        modules = _module_names(risk.get("related_modules", []), module_names)
        mechanisms = _mechanism_names(risk.get("related_mechanisms", []), mechanism_names)
        suffixes = []
        if modules:
            suffixes.append(f"相关模块：{modules}")
        if mechanisms:
            suffixes.append(f"相关机制：{mechanisms}")
        suffix = f"（{_join(suffixes)}）" if suffixes else ""
        _bullet(lines, f"{risk['description']}：影响 {risk['impact']}；缓解 {risk['mitigation']}；可信度 {risk['confidence']}。{suffix}")
    _line(lines)
    _line(lines, "### 假设")
    for assumption in chapter["assumptions"]:
        _bullet(lines, f"{assumption['description']}：依据 {assumption['rationale']}；验证建议 {assumption['validation_suggestion']}；可信度 {assumption['confidence']}。")
    _line(lines)
    _line(lines, "### 验证缺口")
    for gap in chapter["validation_gaps"]:
        _bullet(lines, f"{gap['description']}：{gap['why_it_matters']} 建议：{gap['suggested_validation']}。可信度 {gap['confidence']}。")
    _line(lines)
    _line(lines, "### 低可信项")
    for item in chapter["low_confidence_items"]:
        _bullet(lines, f"{item['description']}：{item['reason']} 需要证据：{item['needed_evidence']}。")
    _line(lines)


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
