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

INTERNAL_LABEL_RE = re.compile(r"\b([A-Za-z][A-Za-z0-9_]*)\s*\[\s*\1\s*\]")


def semantic_validation_result(package, repo_root=None) -> ValidationResult:
    result = ValidationResult()

    _check_main_flow_count(package, result)
    _check_modules(package, result)
    _check_process_metadata(package, result)
    _check_mermaid_readability(package, result)
    if repo_root is not None:
        _check_locations(package, Path(repo_root), result)

    return result


def _check_main_flow_count(package, result):
    flows = (
        package.chapters.get("main_flows", {})
        .get("main_flows", {})
        .get("flows", [])
    )
    if len(flows) > 3:
        result.warning(
            "semantics.main_flows.too_many",
            "$.main_flows.main_flows.flows",
            "reader guide should select at most three main flows",
        )


def _check_modules(package, result):
    modules = (
        package.chapters.get("module_details", {})
        .get("module_details", {})
        .get("modules", [])
    )
    for index, module in enumerate(modules):
        name = str(module.get("name", ""))
        purpose = str(module.get("purpose", ""))
        blocks = module.get("blocks", [])
        mechanisms = module.get("mechanisms", [])
        if (_looks_source_like(name) or _looks_source_like(purpose)) and not (
            blocks or mechanisms
        ):
            result.warning(
                "semantics.module.file_only",
                f"$.module_details.module_details.modules[{index}]",
                "module entry looks like a file-only listing instead of a responsibility unit",
            )


def _check_process_metadata(package, result):
    for chapter_key, chapter in package.chapters.items():
        for path, value in _walk(chapter, f"$.{chapter_key}"):
            if not isinstance(value, str):
                continue
            if not (_is_text_content_path(path) or _is_extra_subsection_title_path(path)):
                continue
            term = _process_metadata_term(value)
            if term:
                result.error(
                    "semantics.process_metadata",
                    path,
                    f"reader-facing content must not include process metadata term: {term}",
                )


def _check_mermaid_readability(package, result):
    for path, block in _iter_mermaid_blocks(package):
        source = block.get("source", "")
        if re.match(r"^\s*graph\b", source):
            result.warning(
                "semantics.mermaid.legacy_graph",
                f"{path}.source",
                "Mermaid source should use flowchart instead of legacy graph syntax",
            )
        match = INTERNAL_LABEL_RE.search(source)
        if match:
            result.warning(
                "semantics.mermaid.internal_label",
                f"{path}.source",
                f"Mermaid visible label exposes internal id: {match.group(1)}",
            )


def _check_locations(package, repo_root, result):
    for chapter_key, chapter in package.chapters.items():
        for path, value in _walk(chapter, f"$.{chapter_key}"):
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


def _iter_mermaid_blocks(package):
    for chapter_key, chapter in package.chapters.items():
        for path, value in _walk(chapter, f"$.{chapter_key}"):
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


def _is_text_content_path(path):
    return path.endswith(".content") or ".items[" in path or ".rows[" in path


def _is_extra_subsection_title_path(path):
    return ".extra_subsections[" in path and path.endswith(".title")


def _process_metadata_term(value):
    lower_value = value.casefold()
    for term in PROCESS_METADATA_TERMS:
        if term.casefold() in lower_value:
            return term
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
