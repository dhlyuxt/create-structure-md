import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.v040_mermaid import mermaid_validation_result
from scripts.v040_package import load_manifest_package, manifest_shape_errors
from scripts.v040_schema import schema_validation_result
from scripts.v040_semantics import semantic_validation_result
from scripts.v040_types import ValidationIssue


def main(argv=None):
    parser = argparse.ArgumentParser(description="Validate a 0.4.0 structure package.")
    parser.add_argument("manifest", help="Path to structure.manifest.json")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as failures")
    parser.add_argument("--repo-root", help="Repository root for source-location checks")
    args = parser.parse_args(argv)

    errors, warnings = validate_package(args.manifest, repo_root=args.repo_root)
    _print_issues(warnings, sys.stderr)
    _print_issues(errors, sys.stderr)

    if errors or (args.strict and warnings):
        return 2

    print("Validation succeeded")
    return 0


def validate_package(manifest_path, *, repo_root=None):
    errors = []
    warnings = []

    manifest = _read_manifest_json(manifest_path, errors)
    if errors:
        return errors, warnings

    errors.extend(manifest_shape_errors(manifest))
    if errors:
        return errors, warnings

    try:
        package = load_manifest_package(manifest_path)
    except ValueError as exc:
        errors.append(ValidationIssue("package.load", "$", str(exc)))
        return errors, warnings

    for result in _validation_results(package, repo_root=repo_root):
        warnings.extend(result.warnings)
        errors.extend(result.errors)

    return errors, warnings


def _read_manifest_json(manifest_path, errors):
    path = Path(manifest_path)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        errors.append(
            ValidationIssue(
                "manifest.not_found",
                "$",
                f"manifest JSON file not found: {path}",
            )
        )
    except json.JSONDecodeError as exc:
        errors.append(
            ValidationIssue(
                "manifest.json",
                "$",
                f"manifest JSON parse failed at line {exc.lineno}, column {exc.colno}: {path}",
            )
        )
    except OSError as exc:
        errors.append(
            ValidationIssue(
                "manifest.read",
                "$",
                f"manifest JSON could not be read: {path}: {exc}",
            )
        )
    return None


def _validation_results(package, *, repo_root=None):
    yield schema_validation_result(package)
    if repo_root is None:
        yield semantic_validation_result(package)
    else:
        yield semantic_validation_result(package, repo_root=repo_root)
    yield mermaid_validation_result(package)


def _print_issues(issues, stream):
    for issue in issues:
        message = issue.format()
        if issue.code == "mermaid.cli_missing":
            message = f"{message}\nMermaid CLI is required for packages with Mermaid blocks."
        print(message, file=stream)


if __name__ == "__main__":
    raise SystemExit(main())
