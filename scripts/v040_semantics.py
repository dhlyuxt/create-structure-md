import re
from pathlib import Path

from scripts.v040_types import ValidationResult


PROCESS_METADATA_TERMS = (
    "subagent report",
    "command transcript",
    "raw scan log",
    "rejected draft",
    "repo-understand log",
    "执行记录",
)

INTERNAL_VISIBLE_LABEL_RE = re.compile(
    r"^[A-Za-z][A-Za-z0-9]*(?:[_-][A-Za-z0-9]+)+$"
)
MERMAID_BRACKET_LABEL_RE = re.compile(r"\[\s*([^\]\n]+?)\s*\]")
SOURCE_FILE_NAME_RE = re.compile(r"\.(?:c|h|py|js|ts|java|go|rs)$", re.IGNORECASE)
FILE_ONLY_TERMS = ("file", "contains", "文件", "包含")


def semantic_validation_result(package, repo_root=None) -> ValidationResult:
    result = ValidationResult()

    _check_main_flow_overview(package, result)
    _check_module_overview(package, result)
    _check_main_flow_count(package, result)
    _check_modules(package, result)
    _check_process_metadata(package, result)
    _check_mermaid_readability(package, result)
    if repo_root is not None:
        _check_locations(package, Path(repo_root), result)

    return result


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


def _check_main_flow_overview(package, result):
    rows = package.chapters["main_flow_overview"]["main_flow_overview"]["flow_table"][
        "rows"
    ]
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


def _check_locations(package, repo_root, result):
    for base_path, payload in _iter_payloads(package):
        for path, value in _walk(payload, base_path):
            if not path.endswith(".location"):
                continue
            if not isinstance(value, str) or not _looks_source_like(value):
                continue
            candidate = repo_root / value
            if not candidate.exists():
                result.warning(
                    "semantics.location.missing",
                    path,
                    f"source-like location does not exist under repo root: {value}",
                )


def _iter_payloads(package):
    for chapter_key, chapter in package.chapters.items():
        yield f"$.{chapter_key}", chapter
    for index, detail in enumerate(package.main_flow_details):
        yield f"$.main_flow_details[{index}]", detail.data
    for index, detail in enumerate(package.module_details):
        yield f"$.module_details[{index}]", detail.data


def _iter_mermaid_blocks_from_payload(payload, base_path):
    for path, value in _walk(payload, base_path):
        if isinstance(value, dict) and value.get("type") == "mermaid":
            yield path, value


def _walk(value, path):
    yield path, value
    if isinstance(value, dict):
        for key, child in value.items():
            yield from _walk(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _walk(child, f"{path}[{index}]")


def _process_metadata_term(value):
    lower_value = value.casefold()
    for term in PROCESS_METADATA_TERMS:
        if term.casefold() in lower_value:
            return term
    return None


def _is_file_only_module(name, purpose, blocks, mechanisms):
    if _looks_source_file_name(name) and _has_file_only_wording(purpose):
        return True
    return (_looks_source_like(name) or _looks_source_like(purpose)) and not (
        blocks or mechanisms
    )


def _looks_source_file_name(value):
    return bool(SOURCE_FILE_NAME_RE.search(value.strip()))


def _has_file_only_wording(value):
    lower_value = value.casefold()
    return any(term.casefold() in lower_value for term in FILE_ONLY_TERMS)


def _internal_visible_label(source):
    for match in MERMAID_BRACKET_LABEL_RE.finditer(source):
        label = match.group(1).strip()
        if INTERNAL_VISIBLE_LABEL_RE.fullmatch(label):
            return label
    return None


def _looks_source_like(value):
    text = value.strip()
    if not text:
        return False
    if text.startswith(("http://", "https://")):
        return False
    if "/" in text or "\\" in text:
        return True
    return bool(re.search(r"\.[A-Za-z0-9]{1,8}$", text))
