#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.v030_mermaid import mermaid_validation_result
from scripts.v030_package import load_manifest_package, manifest_shape_errors
from scripts.v030_renderer import render_markdown
from scripts.v030_schema import schema_validation_result
from scripts.v030_semantics import semantic_validation_result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render create-structure-md 0.3.0 package to Markdown.")
    parser.add_argument("manifest", help="Path to structure.manifest.json")
    parser.add_argument("--output", help="Optional output Markdown path.")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as errors.")
    parser.add_argument("--repo-root", help="Optional repository root for SourceRef existence checks.")
    return parser


def print_result(result, *, strict: bool) -> int:
    for issue in result.warnings:
        print(issue.format(), file=sys.stderr)
    if result.errors or (strict and result.warnings):
        for issue in result.errors:
            print(issue.format(), file=sys.stderr)
        if strict and result.warnings:
            print("ERROR: strict mode treats validation warnings as errors", file=sys.stderr)
        return 2
    return 0


def _load_manifest_for_shape(manifest_path: Path):
    try:
        return json.loads(manifest_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"file not found: {manifest_path}", file=sys.stderr)
        return None
    except OSError as exc:
        print(f"unable to read manifest {manifest_path}: {exc.strerror or exc}", file=sys.stderr)
        return None
    except json.JSONDecodeError as exc:
        print(f"invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}", file=sys.stderr)
        return None


def _validate_package(manifest_path: Path, *, strict: bool, repo_root: Path | None):
    manifest = _load_manifest_for_shape(manifest_path)
    if manifest is None:
        return None, 2
    if isinstance(manifest, dict) and "dsl_version" in manifest:
        print("ERROR: $.dsl_version: structure.manifest.json must not contain dsl_version", file=sys.stderr)
        return None, 2
    shape_errors = manifest_shape_errors(manifest)
    if shape_errors:
        for issue in shape_errors:
            print(issue.format(), file=sys.stderr)
        return None, 2
    try:
        package = load_manifest_package(manifest_path)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return None, 2
    schema_code = print_result(schema_validation_result(package), strict=strict)
    if schema_code:
        return None, schema_code
    semantic_code = print_result(semantic_validation_result(package, repo_root=repo_root), strict=strict)
    if semantic_code:
        return None, semantic_code
    mermaid_code = print_result(mermaid_validation_result(package), strict=strict)
    if mermaid_code:
        return None, mermaid_code
    return package, 0


def _default_output_path(package) -> Path | None:
    root = package.root_dir.resolve()
    output_file = package.chapters["document"]["document"]["output_file"]
    output_path = Path(output_file)
    if output_path.is_absolute() or ".." in output_path.parts:
        print("ERROR: $.document.document.output_file: document.output_file must stay within the package root", file=sys.stderr)
        return None
    candidate = package.root_dir / output_path
    try:
        candidate.resolve().relative_to(root)
    except ValueError:
        print("ERROR: $.document.document.output_file: document.output_file must stay within the package root", file=sys.stderr)
        return None
    return candidate


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    manifest_path = Path(args.manifest)
    package, code = _validate_package(
        manifest_path,
        strict=args.strict,
        repo_root=Path(args.repo_root) if args.repo_root else None,
    )
    if code:
        return code
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = _default_output_path(package)
        if output_path is None:
            return 2
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_markdown(package), encoding="utf-8")
    print(f"Document written: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
