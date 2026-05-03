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


SUPPORTED_TYPES = {"flowchart", "graph", "sequenceDiagram", "classDiagram", "stateDiagram-v2"}
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
    markdown_block_index: int | None = None
    line_start: int | None = None

    def label(self):
        if self.json_path:
            return f"{self.json_path} ({self.diagram_id})"
        return f"Mermaid block {self.markdown_block_index} line {self.line_start}"


@dataclass
class MermaidReport:
    errors: list[MermaidIssue] = field(default_factory=list)

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


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    validate_args(args, parser)
    if args.check_env:
        ok, lines = check_environment()
        for line in lines:
            print(line)
        return 0 if ok else 1
    print("ERROR: validation mode requires Task 2 static extraction", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
