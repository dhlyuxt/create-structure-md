#!/usr/bin/env python3
import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


SUPPORTED_TYPES = {"flowchart", "graph", "sequenceDiagram", "classDiagram", "stateDiagram-v2"}
TYPE_PREFIXES = {
    "flowchart": re.compile(r"^flowchart(?=\s|$)"),
    "graph": re.compile(r"^graph(?=\s|$)"),
    "sequenceDiagram": re.compile(r"^sequenceDiagram(?=\s|$)"),
    "classDiagram": re.compile(r"^classDiagram(?=\s|$)"),
    "stateDiagram-v2": re.compile(r"^stateDiagram-v2(?=\s|$)"),
}
OPENING_FENCE_RE = re.compile(r"^ {0,3}(```+|~~~+)[ \t]*(.*?)[ \t]*$")
CLOSING_FENCE_RE = re.compile(r"^ {0,3}(```+|~~~+)[ \t]*$")
KNOWN_UNSUPPORTED_MARKDOWN_TYPES = {
    "erDiagram",
    "journey",
    "gantt",
    "pie",
    "gitGraph",
    "mindmap",
    "timeline",
    "quadrantChart",
    "requirementDiagram",
    "C4Context",
    "C4Container",
    "C4Component",
    "C4Dynamic",
    "sankey-beta",
    "xychart-beta",
    "block-beta",
    "packet-beta",
    "architecture-beta",
}
DOT_PATTERNS = [
    re.compile(r"(?im)^\s*digraph\b"),
    re.compile(r"(?im)^\s*(?:strict\s+)?graph\b.*\{"),
    re.compile(r"(?im)^\s*rankdir\s*="),
    re.compile(
        r'(?m)^\s*(?:[A-Za-z_][\w.-]*|"[^"\n]+")\s*'
        r'(?:->(?!>)|--(?![-\>]))\s*'
        r'(?:[A-Za-z_][\w.-]*|"[^"\n]+")'
        r'(?:\s+\[[^\]\n]*\])?\s*;?\s*$'
    ),
]
DOT_SYNTAX_HINT = "Use Mermaid syntax only; final Graphviz, DOT, SVG, PNG, and image export are out of scope"
SAFE_FILENAME_RE = re.compile(r"[^A-Za-z0-9_.-]+")
ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class MermaidIssue:
    level: str
    location: str
    message: str
    hint: str = ""

    def format(self):
        suffix = f" Hint: {self.hint}" if self.hint else ""
        return f"{self.level}: {self.location}: {self.message}.{suffix}"


@dataclass(frozen=True)
class MermaidDiagram:
    diagram_id: str
    source: str
    diagram_type: str = ""
    json_path: str = ""
    markdown_block_index: Optional[int] = None
    line_start: Optional[int] = None

    def label(self):
        if self.json_path:
            return f"{self.json_path} ({self.diagram_id})"
        return f"Mermaid block {self.markdown_block_index} line {self.line_start}"


@dataclass
class MermaidReport:
    errors: List[MermaidIssue] = field(default_factory=list)

    def error(self, location, message, hint=""):
        self.errors.append(MermaidIssue("ERROR", location, message, hint))


def build_parser():
    parser = argparse.ArgumentParser(description="Validate create-structure-md Mermaid diagrams.")
    source_group = parser.add_mutually_exclusive_group()
    source_group.add_argument("--from-dsl", dest="dsl_file", help="Path to structure DSL JSON.")
    source_group.add_argument("--from-markdown", dest="markdown_file", help="Path to rendered Markdown.")
    parser.add_argument("--strict", action="store_true", help="Validate with local Mermaid CLI tooling.")
    parser.add_argument("--static", action="store_true", help="Run deterministic static checks only.")
    parser.add_argument("--work-dir", help="Directory for strict-mode validation artifacts.")
    parser.add_argument("--check-env", action="store_true", help="Report local Mermaid validation tooling status.")
    return parser


def effective_mode(args):
    return "static" if args.static else "strict"


def validate_args(args, parser):
    if args.strict and args.static:
        parser.error("--strict and --static are mutually exclusive")
    if args.check_env and (args.dsl_file or args.markdown_file or args.strict or args.static or args.work_dir):
        parser.error("--check-env must be used by itself")
    if not args.check_env and not (args.dsl_file or args.markdown_file):
        parser.error("one of --from-dsl, --from-markdown, or --check-env is required")
    if args.work_dir and effective_mode(args) != "strict":
        parser.error("--work-dir is valid only in strict mode")


def check_environment():
    node_path = shutil.which("node")
    mmdc_path = shutil.which("mmdc")
    lines = [
        f"node: found at {node_path}" if node_path else "node: missing",
        f"mmdc: found at {mmdc_path}" if mmdc_path else "mmdc: missing",
    ]
    if mmdc_path:
        completed = subprocess.run(["mmdc", "--version"], text=True, capture_output=True, check=False)
        version = completed.stdout.strip() or completed.stderr.strip() or "version unavailable"
        lines.append(f"mermaid-cli: {version}")
    return node_path is not None and mmdc_path is not None, lines


def print_report(report):
    for issue in report.errors:
        print(issue.format(), file=sys.stderr)


def merge_reports(*reports):
    merged = MermaidReport()
    for report in reports:
        if report:
            merged.errors.extend(report.errors)
    return merged


def json_path(*parts):
    path = "$"
    for part in parts:
        if isinstance(part, int):
            path += f"[{part}]"
        else:
            path += f".{part}"
    return path


def is_diagram_object(value):
    return isinstance(value, dict) and {"id", "kind", "diagram_type", "source"}.issubset(value)


def first_meaningful_line(source):
    for line in source.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("%%"):
            return stripped
    return ""


def find_dot_syntax(source):
    findings = []
    for line_number, line in enumerate(source.splitlines(), start=1):
        for pattern in DOT_PATTERNS:
            if pattern.search(line):
                findings.append((line_number, line.strip()))
                break
    return findings


def report_dot_syntax(report, location, source):
    findings = find_dot_syntax(source)
    for line_number, line in findings:
        report.error(
            location,
            f"Graphviz/DOT syntax is not supported at line {line_number}: {line}",
            DOT_SYNTAX_HINT,
        )
    return bool(findings)


def infer_type_from_source(source):
    first_line = first_meaningful_line(source)
    for diagram_type, pattern in TYPE_PREFIXES.items():
        if pattern.search(first_line):
            return diagram_type
    return ""


def first_meaningful_token(source):
    first_line = first_meaningful_line(source)
    if not first_line:
        return ""
    return first_line.split(None, 1)[0]


def infer_markdown_diagram_type(source):
    inferred_type = infer_type_from_source(source)
    if inferred_type:
        return inferred_type
    token = first_meaningful_token(source)
    if token in KNOWN_UNSUPPORTED_MARKDOWN_TYPES:
        return token
    return ""


def markdown_info_language(info_string):
    if not info_string:
        return ""
    return info_string.split(None, 1)[0]


def is_closing_fence(line, opening_marker):
    match = CLOSING_FENCE_RE.match(line)
    return (
        match is not None
        and match.group(1)[0] == opening_marker[0]
        and len(match.group(1)) >= len(opening_marker)
    )


def append_diagram(diagrams, value, path):
    if not is_diagram_object(value):
        return
    source = value["source"]
    if not isinstance(source, str) or not source.strip():
        return
    diagrams.append(
        MermaidDiagram(
            diagram_id=str(value["id"]),
            source=source,
            diagram_type=str(value["diagram_type"]),
            json_path=path,
        )
    )


def append_diagram_array(diagrams, values, path):
    if not isinstance(values, list):
        return
    for index, value in enumerate(values):
        append_diagram(diagrams, value, f"{path}[{index}]")


def object_section(parent, name, path):
    if name not in parent:
        return {}
    value = parent[name]
    if not isinstance(value, dict):
        raise ValueError(f"{path} must be an object")
    return value


def extract_diagrams_from_dsl(document):
    if not isinstance(document, dict):
        raise ValueError("DSL root must be an object")
    diagrams = []
    architecture_views = object_section(document, "architecture_views", "$.architecture_views")
    append_diagram(
        diagrams,
        architecture_views.get("module_relationship_diagram"),
        json_path("architecture_views", "module_relationship_diagram"),
    )
    append_diagram_array(
        diagrams,
        architecture_views.get("extra_diagrams"),
        json_path("architecture_views", "extra_diagrams"),
    )

    module_design = object_section(document, "module_design", "$.module_design")
    modules = module_design.get("modules", [])
    if isinstance(modules, list):
        for module_index, module in enumerate(modules):
            if not isinstance(module, dict):
                continue
            append_diagram(
                diagrams,
                module.get("internal_structure", {}).get("diagram")
                if isinstance(module.get("internal_structure"), dict)
                else None,
                json_path("module_design", "modules", module_index, "internal_structure", "diagram"),
            )
            external_details = module.get("external_capability_details", {})
            append_diagram_array(
                diagrams,
                external_details.get("extra_diagrams") if isinstance(external_details, dict) else None,
                json_path(
                    "module_design",
                    "modules",
                    module_index,
                    "external_capability_details",
                    "extra_diagrams",
                ),
            )
            append_diagram_array(
                diagrams,
                module.get("extra_diagrams"),
                json_path("module_design", "modules", module_index, "extra_diagrams"),
            )

    runtime_view = object_section(document, "runtime_view", "$.runtime_view")
    append_diagram(
        diagrams,
        runtime_view.get("runtime_flow_diagram"),
        json_path("runtime_view", "runtime_flow_diagram"),
    )
    append_diagram(
        diagrams,
        runtime_view.get("runtime_sequence_diagram"),
        json_path("runtime_view", "runtime_sequence_diagram"),
    )
    append_diagram_array(
        diagrams,
        runtime_view.get("extra_diagrams"),
        json_path("runtime_view", "extra_diagrams"),
    )

    configuration = object_section(
        document,
        "configuration_data_dependencies",
        "$.configuration_data_dependencies",
    )
    append_diagram_array(
        diagrams,
        configuration.get("extra_diagrams"),
        json_path("configuration_data_dependencies", "extra_diagrams"),
    )

    collaboration = object_section(
        document,
        "cross_module_collaboration",
        "$.cross_module_collaboration",
    )
    append_diagram(
        diagrams,
        collaboration.get("collaboration_relationship_diagram"),
        json_path("cross_module_collaboration", "collaboration_relationship_diagram"),
    )
    append_diagram_array(
        diagrams,
        collaboration.get("extra_diagrams"),
        json_path("cross_module_collaboration", "extra_diagrams"),
    )

    key_flows = object_section(document, "key_flows", "$.key_flows")
    flows = key_flows.get("flows", [])
    if isinstance(flows, list):
        for flow_index, flow in enumerate(flows):
            if isinstance(flow, dict):
                append_diagram(
                    diagrams,
                    flow.get("diagram"),
                    json_path("key_flows", "flows", flow_index, "diagram"),
                )
    append_diagram_array(
        diagrams,
        key_flows.get("extra_diagrams"),
        json_path("key_flows", "extra_diagrams"),
    )
    return diagrams


def append_markdown_diagram(diagrams, block_index, line_start, body_lines):
    source = "\n".join(body_lines)
    diagrams.append(
        MermaidDiagram(
            diagram_id=f"markdown-block-{block_index}",
            source=source,
            diagram_type=infer_markdown_diagram_type(source),
            markdown_block_index=block_index,
            line_start=line_start,
        )
    )


def extract_diagrams_from_markdown(markdown_text):
    diagrams = []
    report = MermaidReport()
    in_fence = False
    fence_marker = ""
    fence_start_line = 0
    fence_is_mermaid = False
    mermaid_block_index = 0
    body_lines = []

    for line_number, line in enumerate(markdown_text.splitlines(), start=1):
        if not in_fence:
            match = OPENING_FENCE_RE.match(line)
            if not match:
                continue
            fence_marker = match.group(1)
            fence_start_line = line_number
            language = markdown_info_language(match.group(2))
            fence_is_mermaid = language.lower() == "mermaid"
            body_lines = []
            in_fence = True
            if fence_is_mermaid:
                mermaid_block_index += 1
            continue

        if is_closing_fence(line, fence_marker):
            if fence_is_mermaid:
                append_markdown_diagram(
                    diagrams,
                    mermaid_block_index,
                    fence_start_line,
                    body_lines,
                )
            in_fence = False
            fence_marker = ""
            fence_start_line = 0
            fence_is_mermaid = False
            body_lines = []
            continue

        if fence_is_mermaid:
            body_lines.append(line)

    if in_fence:
        message = f"unbalanced fenced code block starting at line {fence_start_line}"
        if fence_is_mermaid:
            append_markdown_diagram(
                diagrams,
                mermaid_block_index,
                fence_start_line,
                body_lines,
            )
            report.error(f"Mermaid block {mermaid_block_index} line {fence_start_line}", message)
        else:
            report.error(f"Markdown line {fence_start_line}", message)

    return diagrams, report


def validate_static(diagrams, source_kind):
    report = MermaidReport()
    seen_ids = {}
    for diagram in diagrams:
        location = diagram.label()
        if source_kind == "markdown":
            if not diagram.source.strip():
                report.error(location, "Mermaid block body must be non-empty")
                continue
            if report_dot_syntax(report, location, diagram.source):
                continue
            inferred_type = infer_type_from_source(diagram.source)
            if inferred_type:
                continue
            if diagram.diagram_type:
                report.error(location, f"unsupported Mermaid diagram type {diagram.diagram_type}")
            else:
                report.error(location, "could not infer supported Mermaid diagram type")
            continue

        if not diagram.source.strip():
            report.error(location, "source must be non-empty")
            continue
        if diagram.diagram_type not in SUPPORTED_TYPES:
            report.error(location, f"unsupported diagram_type {diagram.diagram_type}")
        if source_kind == "dsl" and "```" in diagram.source:
            report.error(location, "DSL Mermaid source must not include Markdown code fences")
        has_dot_syntax = report_dot_syntax(report, location, diagram.source)
        if not has_dot_syntax:
            inferred_type = infer_type_from_source(diagram.source)
            if not inferred_type:
                report.error(
                    location,
                    "first meaningful line does not start with a supported Mermaid diagram type",
                )
            elif diagram.diagram_type in SUPPORTED_TYPES and inferred_type != diagram.diagram_type:
                report.error(
                    location,
                    f"first meaningful line starts with {inferred_type} but diagram_type is {diagram.diagram_type}",
                )
        if source_kind == "dsl":
            if diagram.diagram_id in seen_ids:
                report.error(
                    location,
                    f"duplicate diagram id {diagram.diagram_id}; first seen at {seen_ids[diagram.diagram_id]}",
                )
            else:
                seen_ids[diagram.diagram_id] = diagram.json_path
    return report


def load_text_file(path):
    try:
        return Path(path).read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"could not read file: {path}: {exc}") from exc


def load_json_file(path):
    try:
        return json.loads(load_text_file(path))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {path}: {exc}") from exc


def run_static_validation(diagrams, source_kind, extraction_report=None):
    report = merge_reports(extraction_report, validate_static(diagrams, source_kind))
    if report.errors:
        print_report(report)
        return 1
    print(f"Mermaid validation succeeded: {len(diagrams)} diagram(s) checked in static mode.")
    return 0


def safe_artifact_stem(diagram):
    raw = diagram.diagram_id or f"markdown-block-{diagram.markdown_block_index}"
    stem = SAFE_FILENAME_RE.sub("_", raw).strip("._")
    return stem or "mermaid-diagram"


def ensure_strict_tooling(report):
    node_path = shutil.which("node")
    mmdc_path = shutil.which("mmdc")
    if not node_path or not mmdc_path:
        missing = []
        if not node_path:
            missing.append("node")
        if not mmdc_path:
            missing.append("mmdc")
        report.error(
            "strict Mermaid validation",
            "Mermaid strict validation was not performed because local Mermaid CLI tooling unavailable: "
            + ", ".join(missing),
            "Install node and @mermaid-js/mermaid-cli with mmdc on PATH, or ask the user before using --static for this run",
        )
        return False
    return True


def run_strict_validation(diagrams, work_dir=None):
    report = MermaidReport()
    if not ensure_strict_tooling(report):
        return report

    if work_dir:
        root = Path(work_dir)
        root.mkdir(parents=True, exist_ok=True)
        cleanup_context = None
    else:
        cleanup_context = tempfile.TemporaryDirectory(prefix="create-structure-md-mermaid-")
        root = Path(cleanup_context.__enter__())

    try:
        for diagram in diagrams:
            stem = safe_artifact_stem(diagram)
            input_path = root / f"{stem}.mmd"
            output_path = root / f"{stem}.svg"
            input_path.write_text(diagram.source, encoding="utf-8")
            completed = subprocess.run(
                ["mmdc", "-i", str(input_path), "-o", str(output_path)],
                text=True,
                capture_output=True,
                check=False,
            )
            if completed.returncode != 0:
                detail = completed.stderr.strip() or completed.stdout.strip() or f"exit code {completed.returncode}"
                report.error(diagram.label(), f"mmdc failed: {detail}")
    finally:
        if cleanup_context is not None:
            cleanup_context.__exit__(None, None, None)

    return report


def run_strict_mode(diagrams, source_kind, extraction_report=None, work_dir=None):
    preflight_report = merge_reports(extraction_report or MermaidReport(), validate_static(diagrams, source_kind))
    if preflight_report.errors:
        print_report(preflight_report)
        return 1

    strict_report = run_strict_validation(diagrams, work_dir)
    if strict_report.errors:
        print_report(strict_report)
        return 1
    print(f"Mermaid validation succeeded: {len(diagrams)} diagram(s) checked in strict mode.")
    return 0


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    validate_args(args, parser)
    if args.check_env:
        ok, lines = check_environment()
        for line in lines:
            print(line)
        return 0 if ok else 1
    try:
        extraction_report = None
        if args.dsl_file:
            document = load_json_file(args.dsl_file)
            diagrams = extract_diagrams_from_dsl(document)
            source_kind = "dsl"
        else:
            markdown_text = load_text_file(args.markdown_file)
            diagrams, extraction_report = extract_diagrams_from_markdown(markdown_text)
            source_kind = "markdown"
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    mode = effective_mode(args)
    if mode == "static":
        return run_static_validation(diagrams, source_kind, extraction_report)
    return run_strict_mode(diagrams, source_kind, extraction_report, args.work_dir)


if __name__ == "__main__":
    raise SystemExit(main())
