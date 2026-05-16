import re

from scripts.v030_semantics import collect_diagrams
from scripts.v030_types import ValidationResult


OLD_INTERNAL_ID_RE = re.compile(r"(?<![A-Za-z0-9_-])(?:MOD|RUN|FLOW|MER|STEP|CAP|CFG|DATA|COL|RISK|ASM)-[A-Za-z0-9_-]+(?![A-Za-z0-9_-])")
FLOWCHART_NODE_LABEL_RE = re.compile(
    r"(?<![\w])(?P<id>[A-Za-z0-9_.:-]+)\s*"
    r"(?:\[(?P<bracket>[^\]\n]+)\]|\((?P<paren>[^\)\n]+)\)|\{(?P<brace>[^}\n]+)\})"
)
FLOWCHART_EDGE_ENDPOINT_RE = re.compile(
    r"(?P<left>[A-Za-z0-9_.:-]+(?:\[[^\]\n]*\]|\([^\)\n]*\)|\{[^}\n]*\})?)"
    r"\s*(?:[-.=]+(?:>|x|o)|[-.=]+)\s*(?:\|[^|\n]+\|\s*)?"
    r"(?P<right>[A-Za-z0-9_.:-]+(?:\[[^\]\n]*\]|\([^\)\n]*\)|\{[^}\n]*\})?)"
)
FLOWCHART_STANDALONE_NODE_RE = re.compile(r"^\s*([A-Za-z0-9_.:-]+)\s*;?\s*$")
FLOWCHART_EDGE_LABEL_RE = re.compile(r"[-.=]+(?:>|x|o)?\s*\|([^|\n]+)\|")
FLOWCHART_SUBGRAPH_RE = re.compile(r"^\s*subgraph\s+(.+?)\s*$")
FLOWCHART_SUBGRAPH_LABEL_RE = re.compile(r"^[A-Za-z0-9_.:-]+\s*\[([^\]\n]+)\]\s*$")
SEQUENCE_ALIAS_RE = re.compile(r"^\s*(?:create\s+)?(?:participant|actor)\s+(?P<id>\S+)\s+as\s+(?P<label>.+?)\s*$")
SEQUENCE_DECLARATION_RE = re.compile(r"^\s*(?:create\s+)?(?:participant|actor)\s+(?P<label>.+?)\s*$")
SEQUENCE_MESSAGE_RE = re.compile(
    r"^\s*(?P<from>\S+)\s*(?:-{1,2}(?:>>?|x|\))|={1,2}(?:>>?|x|\)))[+-]?\s*(?P<to>\S+)\s*:\s*(?P<label>.+?)\s*$"
)
SEQUENCE_UNSUPPORTED_VISIBLE_LINE_RE = re.compile(r"^\s*(?:Note|loop|alt|opt|par|and|rect|critical|break|box)\b")
UNSUPPORTED_FLOWCHART_LABEL_LINE_RE = re.compile(r"(?:--|==|-\.)\s+[^|\n]+?\s+(?:-->|==>|\.->)")
UNSUPPORTED_FLOWCHART_NODE_SHAPE_RE = re.compile(r"^\s*[A-Za-z0-9_.:-]+\s*>\s*[^]\n]+\]\s*$")


def content_lines(source: str):
    for line in source.splitlines():
        if not line.lstrip().startswith("%%"):
            yield line


def first_mermaid_token(source: str) -> str:
    for line in content_lines(source):
        stripped = line.strip()
        if stripped:
            return stripped.split()[0]
    return ""


def unlabeled_flowchart_node_id(token: str) -> str:
    token = token.strip().rstrip(";").strip('"')
    if not token or any(marker in token for marker in "[({"):
        return ""
    if ":::" in token:
        token = token.split(":::", 1)[0]
    return token


def explicit_flowchart_labels(content: str):
    for match in FLOWCHART_NODE_LABEL_RE.finditer(content):
        node_id = match.group("id").strip().strip('"')
        label = next(match.group(name) for name in ("bracket", "paren", "brace") if match.group(name) is not None)
        label = label.strip().strip('"')
        if node_id and label:
            yield node_id, label


def visible_unlabeled_flowchart_node_ids(lines, labeled_node_ids: set[str]):
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith(("flowchart", "subgraph")) or stripped == "end":
            continue
        for match in FLOWCHART_EDGE_ENDPOINT_RE.finditer(line):
            for group in ("left", "right"):
                node_id = unlabeled_flowchart_node_id(match.group(group))
                if node_id and node_id not in labeled_node_ids:
                    yield node_id
        match = FLOWCHART_STANDALONE_NODE_RE.match(line)
        if match:
            node_id = unlabeled_flowchart_node_id(match.group(1))
            if node_id and node_id not in labeled_node_ids:
                yield node_id


def visible_flowchart_subgraph_labels(lines):
    for line in lines:
        match = FLOWCHART_SUBGRAPH_RE.match(line)
        if not match:
            continue
        title = match.group(1).strip().strip('"')
        label_match = FLOWCHART_SUBGRAPH_LABEL_RE.match(title)
        if label_match:
            title = label_match.group(1).strip().strip('"')
        if title:
            yield title


def clean_sequence_participant(value: str) -> str:
    return value.strip().lstrip("+-").strip('"')


def visible_labels(diagram_type: str, source: str):
    lines = list(content_lines(source))
    content = "\n".join(lines)
    if diagram_type == "flowchart":
        labeled_node_ids = set()
        for node_id, label in explicit_flowchart_labels(content):
            labeled_node_ids.add(node_id)
            yield label
        for match in FLOWCHART_EDGE_LABEL_RE.finditer(content):
            label = match.group(1).strip().strip('"')
            if label:
                yield label
        yield from visible_flowchart_subgraph_labels(lines)
        yield from visible_unlabeled_flowchart_node_ids(lines, labeled_node_ids)
    if diagram_type != "sequenceDiagram":
        return
    declared_participant_ids = set()
    for line in lines:
        match = SEQUENCE_ALIAS_RE.match(line)
        if match:
            participant_id = clean_sequence_participant(match.group("id"))
            label = match.group("label").strip().strip('"')
            if participant_id:
                declared_participant_ids.add(participant_id)
            if label:
                yield label
            continue
        match = SEQUENCE_DECLARATION_RE.match(line)
        if match:
            label = clean_sequence_participant(match.group("label"))
            if label:
                declared_participant_ids.add(label)
                yield label
    for line in lines:
        match = SEQUENCE_MESSAGE_RE.match(line)
        if match:
            sender = clean_sequence_participant(match.group("from"))
            receiver = clean_sequence_participant(match.group("to"))
            label = match.group("label").strip().strip('"')
            for participant in (sender, receiver):
                if participant and participant not in declared_participant_ids:
                    yield participant
            if label:
                yield label


def has_unsupported_visible_label_syntax(diagram_type: str, source: str) -> bool:
    if diagram_type == "stateDiagram-v2":
        return True
    if diagram_type == "flowchart":
        return any(
            UNSUPPORTED_FLOWCHART_LABEL_LINE_RE.search(line) or UNSUPPORTED_FLOWCHART_NODE_SHAPE_RE.search(line)
            for line in content_lines(source)
        )
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
