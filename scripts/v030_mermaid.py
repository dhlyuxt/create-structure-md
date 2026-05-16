import re

from scripts.v030_semantics import collect_diagrams
from scripts.v030_types import ValidationResult


OLD_INTERNAL_ID_RE = re.compile(r"\b(?:MOD|RUN|FLOW|MER|STEP|CAP|CFG|DATA|COL|RISK|ASM)-[A-Za-z0-9_-]+\b")
FLOWCHART_NODE_LABEL_RE = re.compile(r"(?<![\w])[\w.:-]+\s*(?:\[([^\]\n]+)\]|\(([^\)\n]+)\)|\{([^}\n]+)\})")
FLOWCHART_EDGE_LABEL_RE = re.compile(r"-->\|([^|]+)\|")
SEQUENCE_ALIAS_RE = re.compile(r"^\s*(?:participant|actor)\s+\S+\s+as\s+(.+?)\s*$")
SEQUENCE_MESSAGE_RE = re.compile(r"^\s*\S+\s*(?:-{1,2}(?:>>?|x|\))|={1,2}(?:>>?|x|\)))[+-]?\s*\S+\s*:\s*(.+?)\s*$")
SEQUENCE_UNSUPPORTED_VISIBLE_LINE_RE = re.compile(r"^\s*(?:Note|loop|alt|opt|par|and|rect|critical|break)\b")
UNSUPPORTED_FLOWCHART_LABEL_LINE_RE = re.compile(r"--\s+[^-|>][^-|>]+?\s+-->")


def content_lines(source: str):
    for line in source.splitlines():
        if not line.lstrip().startswith("%%"):
            yield line


def first_mermaid_token(source: str) -> str:
    for line in source.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped.split()[0]
    return ""


def visible_labels(diagram_type: str, source: str):
    lines = list(content_lines(source))
    content = "\n".join(lines)
    if diagram_type == "flowchart":
        for match in FLOWCHART_NODE_LABEL_RE.finditer(content):
            label = next(group for group in match.groups() if group is not None).strip().strip('"')
            if label:
                yield label
        for match in FLOWCHART_EDGE_LABEL_RE.finditer(content):
            label = match.group(1).strip().strip('"')
            if label:
                yield label
    if diagram_type != "sequenceDiagram":
        return
    for line in lines:
        match = SEQUENCE_ALIAS_RE.match(line)
        if match:
            label = match.group(1).strip().strip('"')
            if label:
                yield label
        match = SEQUENCE_MESSAGE_RE.match(line)
        if not match:
            continue
        label = match.group(1).strip().strip('"')
        if label:
            yield label


def has_unsupported_visible_label_syntax(diagram_type: str, source: str) -> bool:
    if diagram_type == "stateDiagram-v2":
        return True
    if diagram_type == "flowchart":
        return any(UNSUPPORTED_FLOWCHART_LABEL_LINE_RE.search(line) for line in content_lines(source))
    if diagram_type == "sequenceDiagram":
        return any(SEQUENCE_UNSUPPORTED_VISIBLE_LINE_RE.search(line) for line in content_lines(source))
    return False


def mermaid_validation_result(package) -> ValidationResult:
    result = ValidationResult()
    all_diagrams = []
    for key, chapter in package.chapters.items():
        all_diagrams.extend(collect_diagrams(chapter, f"$.{key}"))
    for index, mechanism in enumerate(package.mechanisms):
        all_diagrams.extend(collect_diagrams(mechanism.data, f"$.key_mechanisms[{index}]"))

    for path, diagram in all_diagrams:
        token = first_mermaid_token(diagram["source"])
        if token == "graph":
            result.error("mermaid.legacy_graph", path + ".source", "Legacy graph declarations are not supported in 0.3.0; use flowchart")
        elif token != diagram["diagram_type"]:
            result.error("mermaid.declaration", path + ".source", f"diagram_type does not match Mermaid declaration: {diagram['diagram_type']} != {token}")
        if has_unsupported_visible_label_syntax(diagram["diagram_type"], diagram["source"]):
            result.warn("mermaid.label_coverage", path + ".source", f"Unsupported visible-label syntax for {diagram['diagram_type']}; readability check is partial")
        checked_any_label = False
        for label in visible_labels(diagram["diagram_type"], diagram["source"]):
            checked_any_label = True
            if OLD_INTERNAL_ID_RE.search(label):
                result.error("mermaid.visible_id", path + ".source", f"visible Mermaid label leaks internal ID: {label}")
        if not checked_any_label:
            result.warn("mermaid.label_coverage", path + ".source", "No supported visible-label syntax found; readability check inspected declaration only")
    return result
