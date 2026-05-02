#!/usr/bin/env python3
import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas/structure-design.schema.json"


@dataclass(frozen=True)
class ValidationIssue:
    level: str
    path: str
    message: str
    hint: str = ""

    def format(self):
        suffix = f" Hint: {self.hint}" if self.hint else ""
        return f"{self.level}: {self.path}: {self.message}.{suffix}"


@dataclass
class ValidationReport:
    errors: list[ValidationIssue] = field(default_factory=list)
    warnings: list[ValidationIssue] = field(default_factory=list)

    def error(self, path, message, hint=""):
        self.errors.append(ValidationIssue("ERROR", path, message, hint))

    def warn(self, path, message, hint=""):
        self.warnings.append(ValidationIssue("WARNING", path, message, hint))


def build_parser():
    parser = argparse.ArgumentParser(description="Validate create-structure-md DSL JSON.")
    parser.add_argument("dsl_file", help="Path to structure DSL JSON.")
    parser.add_argument(
        "--allow-long-snippets",
        action="store_true",
        help="Warn instead of fail for source snippets longer than 50 lines.",
    )
    return parser


def json_path(parts):
    path = "$"
    for part in parts:
        if isinstance(part, int):
            path += f"[{part}]"
        else:
            path += f".{part}"
    return path


def load_json_file(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ValueError(f"file not found: {path}")
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}")


def load_schema():
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def schema_errors(document):
    validator = Draft202012Validator(load_schema())
    return sorted(validator.iter_errors(document), key=lambda error: list(error.path))


def format_schema_error(error):
    return ValidationIssue(
        "ERROR",
        json_path(error.path),
        f"schema validation failed: {error.message}",
        "Fix the DSL shape before semantic validation runs",
    )


class ValidationContext:
    def __init__(self, document, report):
        self.document = document
        self.report = report

    def build(self):
        pass


def validate_document_fields(document, report):
    pass


def check_chapter_rules(document, context):
    pass


def check_source_snippets(document, context, *, allow_long_snippets):
    pass


def check_markdown_safety(document, context):
    pass


def collect_low_confidence(document, context):
    pass


def validate_semantics(document, *, allow_long_snippets=False):
    report = ValidationReport()
    validate_document_fields(document, report)
    context = ValidationContext(document, report)
    context.build()
    run_semantic_checks(document, context, allow_long_snippets=allow_long_snippets)
    return report


def run_semantic_checks(document, context, *, allow_long_snippets):
    check_chapter_rules(document, context)
    check_source_snippets(document, context, allow_long_snippets=allow_long_snippets)
    check_markdown_safety(document, context)
    collect_low_confidence(document, context)


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    path = Path(args.dsl_file)

    try:
        document = load_json_file(path)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    schema_failure = schema_errors(document)
    if schema_failure:
        print(format_schema_error(schema_failure[0]).format(), file=sys.stderr)
        return 2

    report = validate_semantics(document, allow_long_snippets=args.allow_long_snippets)
    if report.errors:
        for issue in report.errors:
            print(issue.format(), file=sys.stderr)
        for issue in report.warnings:
            print(issue.format(), file=sys.stderr)
        return 1

    for issue in report.warnings:
        print(issue.format())
    print("Validation succeeded")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
