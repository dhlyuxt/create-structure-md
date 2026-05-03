#!/usr/bin/env python3
import argparse
import json
import re
import sys
from pathlib import Path


GENERIC_OUTPUT_NAMES = {
    "structure_design.md",
    "structure-design.md",
    "structuredesign.md",
    "design.md",
    "软件结构设计说明书.md",
}

GENERIC_OUTPUT_TOKENS = {
    "software",
    "structure",
    "design",
    "document",
    "doc",
    "system",
    "module",
    "软件",
    "结构",
    "设计",
    "说明书",
}

CONTROL_CHARACTER_RE = re.compile(r"[\x00-\x1f\x7f-\x9f]")


class RenderError(Exception):
    exit_code = 1


class InputError(RenderError):
    exit_code = 2


def build_parser():
    parser = argparse.ArgumentParser(description="Render create-structure-md DSL JSON to Markdown.")
    parser.add_argument("dsl_file", help="Path to structure DSL JSON.")
    parser.add_argument("--output-dir", default=".", help="Directory for the generated Markdown file.")
    output_group = parser.add_mutually_exclusive_group()
    output_group.add_argument("--overwrite", action="store_true", help="Replace an existing output file.")
    output_group.add_argument("--backup", action="store_true", help="Back up an existing output file before writing.")
    return parser


def load_json_file(path):
    path = Path(path)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise InputError(f"file not found: {path}")
    except json.JSONDecodeError as exc:
        raise InputError(f"invalid JSON in {path}: line {exc.lineno}, column {exc.colno}: {exc.msg}")


def normalized_name_tokens(value):
    normalized = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]+", " ", value.casefold())
    return [token for token in normalized.split() if token]


def documented_object_tokens(document):
    doc = document["document"]
    tokens = set(normalized_name_tokens(doc.get("project_name", "")))
    for row in document["architecture_views"]["module_intro"]["rows"]:
        tokens.update(normalized_name_tokens(row["module_id"]))
        tokens.update(normalized_name_tokens(row["module_name"]))
    for module in document["module_design"]["modules"]:
        tokens.update(normalized_name_tokens(module["module_id"]))
        tokens.update(normalized_name_tokens(module["name"]))
    return {token for token in tokens if token not in GENERIC_OUTPUT_TOKENS and len(token) >= 2}


def validate_output_filename(document):
    try:
        output_file = document["document"]["output_file"]
    except (KeyError, TypeError):
        raise InputError("document.output_file must be a non-empty Markdown filename")

    if not isinstance(output_file, str) or output_file.strip() == "":
        raise InputError("document.output_file must be a non-empty Markdown filename")
    if not output_file.endswith(".md"):
        raise InputError("document.output_file must end with .md")
    if "/" in output_file or "\\" in output_file or ".." in output_file:
        raise InputError("document.output_file must be a simple filename without path segments")
    if CONTROL_CHARACTER_RE.search(output_file):
        raise InputError("document.output_file must not contain control characters")

    folded = output_file.casefold()
    output_tokens = normalized_name_tokens(Path(output_file).stem)
    generic_only = bool(output_tokens) and all(token in GENERIC_OUTPUT_TOKENS for token in output_tokens)
    if folded in GENERIC_OUTPUT_NAMES or generic_only:
        raise InputError("generic-only output filename is not allowed for document.output_file")

    concrete_tokens = documented_object_tokens(document)
    contains_concrete_token = any(token in output_tokens for token in concrete_tokens)
    if not contains_concrete_token:
        raise InputError("document.output_file must include a concrete documented object name")

    return output_file


def resolve_output_path(output_dir, output_file):
    output_dir = Path(output_dir)
    if not output_dir.exists():
        raise InputError(f"output directory not found: {output_dir}")
    if not output_dir.is_dir():
        raise InputError(f"output path is not a directory: {output_dir}")
    return output_dir / output_file


def render_markdown(document):
    return "# 软件结构设计说明书\n"


def write_output(output_path, markdown, overwrite=False, backup=False):
    output_path = Path(output_path)
    if output_path.exists() and not overwrite and not backup:
        raise RenderError(f"output file already exists: {output_path}")
    if output_path.exists() and backup:
        raise RenderError("backup behavior is not implemented yet")
    output_path.write_text(markdown, encoding="utf-8")


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        document = load_json_file(args.dsl_file)
        output_file = validate_output_filename(document)
        output_path = resolve_output_path(args.output_dir, output_file)
        markdown = render_markdown(document)
        write_output(output_path, markdown, overwrite=args.overwrite, backup=args.backup)
    except InputError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return exc.exit_code
    except RenderError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return exc.exit_code

    print(f"Markdown rendered: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
