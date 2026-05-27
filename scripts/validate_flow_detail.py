import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.v040_mermaid import mermaid_detail_validation_result
from scripts.v040_package import manifest_shape_errors
from scripts.v040_schema import _schema_error_path, validator_for
from scripts.v040_semantics import detail_semantic_validation_result
from scripts.v040_types import ValidationIssue
from scripts.validate_structure import _print_issues


def main(argv=None):
    parser = argparse.ArgumentParser(description="Validate one main-flow detail file.")
    parser.add_argument("detail", help="Path to one main-flow detail JSON file")
    parser.add_argument(
        "--package-root",
        required=True,
        help="Path to the package root containing structure.manifest.json",
    )
    args = parser.parse_args(argv)

    return run_detail_cli(
        detail_path=args.detail,
        package_root=args.package_root,
        kind="main_flow_details",
        def_name="MainFlowDetail",
        success_message="Flow detail validation succeeded",
    )


def run_detail_cli(detail_path, package_root, *, kind, def_name, success_message):
    errors = []
    package_root = Path(package_root)
    manifest_path = package_root / "structure.manifest.json"
    manifest = _read_manifest_json(manifest_path, errors)
    if not errors:
        errors.extend(manifest_shape_errors(manifest))

    relative_path = None
    index = None
    if not errors:
        relative_path = _relative_detail_path(Path(detail_path), package_root, errors)
    if not errors:
        index = _manifest_detail_index(manifest, kind, relative_path, errors)
    if not errors:
        data = _read_detail_json(Path(detail_path), kind, index, errors)
    if not errors:
        errors.extend(_schema_issues(def_name, data, f"$.{kind}[{index}]"))
        semantic_result = detail_semantic_validation_result(kind, index, data)
        errors.extend(semantic_result.errors)
        errors.extend(semantic_result.warnings)
        mermaid_result = mermaid_detail_validation_result(kind, index, data)
        errors.extend(mermaid_result.errors)
        errors.extend(mermaid_result.warnings)

    if errors:
        _print_issues(errors, sys.stderr)
        return 2

    print(success_message)
    return 0


def _read_manifest_json(manifest_path, errors):
    try:
        return json.loads(manifest_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        errors.append(
            ValidationIssue(
                "manifest.not_found",
                "$",
                f"manifest JSON file not found: {manifest_path}",
            )
        )
    except json.JSONDecodeError as exc:
        errors.append(
            ValidationIssue(
                "manifest.json",
                "$",
                f"manifest JSON parse failed at line {exc.lineno}, column {exc.colno}: {manifest_path}",
            )
        )
    except OSError as exc:
        errors.append(
            ValidationIssue(
                "manifest.read",
                "$",
                f"manifest JSON could not be read: {manifest_path}: {exc}",
            )
        )
    return None


def _relative_detail_path(detail_path: Path, package_root: Path, errors):
    try:
        relative_path = detail_path.resolve().relative_to(package_root.resolve())
    except ValueError:
        errors.append(
            ValidationIssue(
                "detail.path",
                "$",
                "detail path must stay within the package root",
            )
        )
        return None
    return relative_path.as_posix()


def _manifest_detail_index(manifest, kind, relative_path, errors):
    try:
        return manifest[kind].index(relative_path)
    except ValueError:
        errors.append(
            ValidationIssue(
                "manifest.detail_unlisted",
                f"$.{kind}",
                f"detail file must be listed in {kind}: {relative_path}",
            )
        )
    return None


def _read_detail_json(detail_path: Path, kind: str, index: int, errors):
    issue_path = f"$.{kind}[{index}]"
    try:
        return json.loads(detail_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        errors.append(
            ValidationIssue(
                "detail.not_found",
                issue_path,
                f"detail JSON file not found: {detail_path}",
            )
        )
    except json.JSONDecodeError as exc:
        errors.append(
            ValidationIssue(
                "detail.json",
                issue_path,
                f"detail JSON parse failed at line {exc.lineno}, column {exc.colno}: {detail_path}",
            )
        )
    except OSError as exc:
        errors.append(
            ValidationIssue(
                "detail.read",
                issue_path,
                f"detail JSON could not be read: {detail_path}: {exc}",
            )
        )
    return None


def _schema_issues(def_name, data, path_prefix):
    validator = validator_for(def_name)
    schema_errors = sorted(validator.iter_errors(data), key=lambda error: list(error.path))
    return [
        ValidationIssue("schema", _schema_error_path(path_prefix, error.path), error.message)
        for error in schema_errors
    ]


if __name__ == "__main__":
    raise SystemExit(main())
