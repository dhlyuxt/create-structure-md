import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.validate_structure import (
    _print_issues,
    dispatch_manifest_cli,
    validate_package,
)
from scripts.v040_package import load_manifest_package
from scripts.v040_renderer import render_markdown as render_package_markdown
from scripts.v040_types import ValidationIssue


def main(argv=None):
    raw_argv = list(sys.argv[1:] if argv is None else argv)
    parser = argparse.ArgumentParser(description="Render a structure package.")
    parser.add_argument("manifest", help="Path to structure.manifest.json")
    parser.add_argument("--output", help="Output Markdown path")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as failures")
    parser.add_argument("--repo-root", help="Repository root for source-location checks")
    args = parser.parse_args(argv)

    dispatch_code = dispatch_manifest_cli(
        "render_markdown.py",
        raw_argv,
        args.manifest,
    )
    if dispatch_code is not None:
        return dispatch_code

    errors, warnings = validate_package(args.manifest, repo_root=args.repo_root)
    _print_issues(warnings, sys.stderr)
    _print_issues(errors, sys.stderr)
    if errors or (args.strict and warnings):
        return 2

    package = load_manifest_package(args.manifest)
    output_path, output_errors = _resolve_output_path(package, args.output)
    if output_errors:
        _print_issues(output_errors, sys.stderr)
        return 2

    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(render_package_markdown(package), encoding="utf-8")
    except OSError as exc:
        _print_issues(
            [
                ValidationIssue(
                    "render.write",
                    "$.output",
                    f"Markdown output could not be written: {output_path}: {exc}",
                )
            ],
            sys.stderr,
        )
        return 2

    print(f"Document written: {output_path}")
    return 0


def _resolve_output_path(package, output):
    if output:
        return Path(output), []

    default_output = package.chapters["document"]["document"]["output_file"]
    default_path = Path(default_output)
    if default_path.is_absolute() or ".." in default_path.parts:
        return default_path, [
            ValidationIssue(
                "render.output_path",
                "$.document.document.output_file",
                "default output_file must be relative and must not contain '..'",
            )
        ]

    output_path = package.root_dir / default_path
    try:
        output_path.resolve().relative_to(package.root_dir.resolve())
    except ValueError:
        return output_path, [
            ValidationIssue(
                "render.output_path",
                "$.document.document.output_file",
                "default output_file must stay within the package root",
            )
        ]

    return output_path, []


if __name__ == "__main__":
    raise SystemExit(main())
