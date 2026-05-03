#!/usr/bin/env python3
import argparse
import html
import json
import re
import shutil
import sys
from datetime import datetime
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
SAFE_FENCE_INFO_RE = re.compile(r"^[A-Za-z0-9_+.-]+$")


class RenderError(Exception):
    exit_code = 1


class InputError(RenderError):
    exit_code = 2


def escape_fence_markers(value):
    return value.replace("```", "`&#96;&#96;").replace("~~~", "~&#126;&#126;")


def escape_html(value):
    return html.escape(value, quote=False)


def stringify_markdown_value(value):
    if value is None:
        return ""
    if isinstance(value, list):
        return "、".join(str(item) for item in value)
    return str(value)


def escape_table_cell(value):
    escaped = escape_html(stringify_markdown_value(value))
    escaped = escaped.replace("|", "\\|")
    escaped = escaped.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "<br>")
    return escape_fence_markers(escaped)


def escape_plain_text(value):
    escaped = escape_fence_markers(escape_html(stringify_markdown_value(value)))
    lines = escaped.splitlines(keepends=True)
    return "".join(escape_plain_text_line(line) for line in lines)


def escape_plain_text_line(line):
    newline = ""
    content = line
    if content.endswith("\r\n"):
        content = content[:-2]
        newline = "\r\n"
    elif content.endswith("\n"):
        content = content[:-1]
        newline = "\n"
    elif content.endswith("\r"):
        content = content[:-1]
        newline = "\r"

    if re.match(r"^ {0,3}#{1,6}\s+", content) or re.match(r"^ {0,3}(=+|-+)\s*$", content):
        content = "\\" + content
    if "|" in content:
        content = content.replace("|", "\\|")
    return content + newline


def render_fixed_table(rows, columns):
    headers = [escape_table_cell(title) for _, title in columns]
    rendered_rows = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for row in rows:
        cells = [escape_table_cell(row.get(field_key, "")) for field_key, _ in columns]
        rendered_rows.append("| " + " | ".join(cells) + " |")
    return "\n".join(rendered_rows)


def render_extra_table(table):
    columns = table.get("columns", [])
    rows = table.get("rows", [])
    declared_columns = [(column.get("key", ""), column.get("title", "")) for column in columns]
    title = escape_plain_text(table.get("title", ""))
    return f"#### {title}\n\n{render_fixed_table(rows, declared_columns)}"


def render_mermaid_block(diagram, empty_text=None):
    source = ""
    if diagram:
        source = str(diagram.get("source") or "")
    if source == "":
        return empty_text or ""
    if "```" in source or "~~~" in source:
        raise RenderError("Mermaid source must not contain fenced code markers")

    parts = []
    title = diagram.get("title") if diagram else ""
    description = diagram.get("description") if diagram else ""
    if title:
        parts.append(escape_plain_text(title))
    if description:
        parts.append(escape_plain_text(description))
    parts.append(f"```mermaid\n{source}\n```")
    return "\n\n".join(parts)


def longest_backtick_run(content):
    runs = re.findall(r"`+", content)
    if not runs:
        return 0
    return max(len(run) for run in runs)


def render_source_snippet(snippet):
    content = str(snippet.get("content") or "")
    fence = "`" * max(3, longest_backtick_run(content) + 1)
    language = safe_fence_info_string(snippet.get("language", ""))
    path = escape_plain_text(snippet.get("path", "")).strip()
    line_start = escape_plain_text(snippet.get("line_start", "")).strip()
    line_end = escape_plain_text(snippet.get("line_end", "")).strip()
    purpose = escape_plain_text(snippet.get("purpose", "")).strip()

    details = []
    if path:
        if line_start or line_end:
            details.append(f"Source: {path}:{line_start}-{line_end}")
        else:
            details.append(f"Source: {path}")
    if purpose:
        details.append(f"Purpose: {purpose}")

    details.append(f"{fence}{language}\n{content}\n{fence}")
    return "\n\n".join(details)


def safe_fence_info_string(value):
    language = stringify_markdown_value(value).strip()
    if SAFE_FENCE_INFO_RE.fullmatch(language):
        return language
    return ""


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
    except OSError as exc:
        raise InputError(f"unable to read {path}: {exc}")
    except UnicodeDecodeError as exc:
        raise InputError(f"unable to read {path}: {exc}")
    except json.JSONDecodeError as exc:
        raise InputError(f"invalid JSON in {path}: line {exc.lineno}, column {exc.colno}: {exc.msg}")


def normalized_name_tokens(value):
    if not isinstance(value, str):
        raise TypeError("filename context values must be strings")
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

    try:
        concrete_tokens = documented_object_tokens(document)
    except (KeyError, TypeError) as exc:
        raise InputError(f"DSL shape is missing required filename context: {exc}")
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


def backup_timestamp():
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def backup_path_for(output_path):
    output_path = Path(output_path)
    return output_path.with_name(f"{output_path.name}.bak-{backup_timestamp()}")


def copy_backup_file(output_path, backup_path):
    output_path = Path(output_path)
    backup_path = Path(backup_path)
    try:
        backup_bytes = output_path.read_bytes()
        with backup_path.open("xb") as destination:
            destination.write(backup_bytes)
        shutil.copystat(output_path, backup_path)
    except FileExistsError:
        raise RenderError(f"backup path already exists: {backup_path}; retry later")
    except OSError as exc:
        raise RenderError(f"failed to write backup path {backup_path}: {exc}")


def write_markdown_file(output_path, markdown, exclusive=False):
    try:
        if exclusive:
            with output_path.open("x", encoding="utf-8") as output_file:
                output_file.write(markdown)
        else:
            output_path.write_text(markdown, encoding="utf-8")
    except FileExistsError:
        raise RenderError(f"output file already exists: {output_path}; use --overwrite or --backup")
    except OSError as exc:
        raise RenderError(f"failed to write output file {output_path}: {exc}")


def write_output(output_path, markdown, overwrite=False, backup=False):
    output_path = Path(output_path)
    backup_path = None

    if output_path.exists() and not overwrite and not backup:
        raise RenderError(f"output file already exists: {output_path}; use --overwrite or --backup")

    if output_path.exists() and backup:
        backup_path = backup_path_for(output_path)
        if backup_path.exists():
            raise RenderError(f"backup path already exists: {backup_path}; retry later")
        copy_backup_file(output_path, backup_path)

    write_markdown_file(output_path, markdown, exclusive=not overwrite and not backup)
    return backup_path


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        document = load_json_file(args.dsl_file)
        output_file = validate_output_filename(document)
        output_path = resolve_output_path(args.output_dir, output_file)
        markdown = render_markdown(document)
        backup_path = write_output(output_path, markdown, overwrite=args.overwrite, backup=args.backup)
    except InputError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return exc.exit_code
    except RenderError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return exc.exit_code

    if backup_path is not None:
        print(f"Backup written: {backup_path}")
    print(f"Markdown rendered: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
