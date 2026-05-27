import argparse
import json
import subprocess
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

V030_KEYS = {
    "document",
    "repository_overview",
    "directory_map",
    "module_layers",
    "repository_mainline",
    "key_mechanisms",
    "integration_boundaries",
    "risks_validation",
}
V040_KEYS = {
    "document",
    "overview",
    "quick_start",
    "architecture_overview",
    "main_flow_overview",
    "main_flow_details",
    "module_overview",
    "module_details",
}
OLD_ACTIVE_V040_KEYS = {
    "document",
    "overview",
    "quick_start",
    "architecture_overview",
    "main_flows",
    "module_details",
}
V030_SCRIPT_DIR = ROOT / "docs/superpowers/history/V3/scripts"


def main(argv=None):
    raw_argv = list(sys.argv[1:] if argv is None else argv)
    parser = argparse.ArgumentParser(description="Validate a structure package.")
    parser.add_argument("manifest", help="Path to structure.manifest.json")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as failures")
    parser.add_argument("--repo-root", help="Repository root for source-location checks")
    args = parser.parse_args(argv)

    dispatch_code = dispatch_manifest_cli(
        "validate_structure.py",
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

    print("Validation succeeded")
    return 0


def validate_package(manifest_path, *, repo_root=None):
    errors = []
    warnings = []

    manifest = _read_manifest_json(manifest_path, errors)
    if errors:
        return errors, warnings

    version, dispatch_errors = manifest_dispatch_result(manifest)
    errors.extend(dispatch_errors)
    if errors:
        return errors, warnings
    if version == "0.3.0":
        errors.append(
            ValidationIssue(
                "manifest.version",
                "$",
                "0.3.0 packages are handled by CLI manifest-shape dispatch",
            )
        )
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


def detect_manifest_version(manifest):
    if not isinstance(manifest, dict):
        return "unknown"
    keys = set(manifest.keys())
    if keys == V030_KEYS:
        return "0.3.0"
    if keys == V040_KEYS:
        return "0.4.0"
    if keys == OLD_ACTIVE_V040_KEYS:
        return "old-active-0.4.0"
    return "unknown"


def manifest_dispatch_result(manifest):
    if isinstance(manifest, dict) and "dsl_version" in manifest:
        return "unknown", [
            ValidationIssue(
                "manifest.dsl_version",
                "$.dsl_version",
                "structure.manifest.json must not contain dsl_version",
            )
        ]

    version = detect_manifest_version(manifest)
    if version == "old-active-0.4.0":
        return version, [
            ValidationIssue(
                "manifest.v040_migration",
                "$",
                "breaking active 0.4.0 migration required: replace main_flows/module_details aggregate files with main_flow_overview, main_flow_details, module_overview, and module_details",
            )
        ]
    if version == "unknown":
        return version, [_unknown_manifest_shape_issue(manifest)]
    return version, []


def dispatch_manifest_cli(script_name, argv, manifest_path):
    manifest_errors = []
    manifest = _read_manifest_json(manifest_path, manifest_errors)
    if manifest_errors:
        _print_issues(manifest_errors, sys.stderr)
        return 2

    version, dispatch_errors = manifest_dispatch_result(manifest)
    if dispatch_errors:
        _print_issues(dispatch_errors, sys.stderr)
        return 2
    if version == "0.3.0":
        return _run_v030_cli(script_name, argv)
    return None


def _unknown_manifest_shape_issue(manifest):
    received = "<non-object>"
    if isinstance(manifest, dict):
        received = ", ".join(sorted(manifest.keys())) or "<empty>"
    return ValidationIssue(
        "manifest.keys",
        "$",
        (
            "manifest keys must match an accepted 0.3.0 or 0.4.0 package shape; "
            f"received keys: {received}; "
            f"0.3.0 keys: {', '.join(sorted(V030_KEYS))}; "
            f"0.4.0 keys: {', '.join(sorted(V040_KEYS))}"
        ),
    )


def _run_v030_cli(script_name, argv):
    script = V030_SCRIPT_DIR / script_name
    try:
        process = subprocess.run(
            [sys.executable, "-B", str(script), *[str(item) for item in argv]],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except OSError as exc:
        _print_issues(
            [
                ValidationIssue(
                    "legacy_cli.run",
                    "$",
                    f"0.3.0 CLI could not be executed: {script}: {exc}",
                )
            ],
            sys.stderr,
        )
        return 2

    if process.stdout:
        print(process.stdout, end="")
    if process.stderr:
        print(process.stderr, end="", file=sys.stderr)
    return process.returncode


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
