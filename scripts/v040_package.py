import json
from dataclasses import dataclass
from pathlib import Path

from scripts.v040_types import ValidationIssue


FIXED_MANIFEST = {
    "document": "chapters/00-document.json",
    "overview": "chapters/01-overview.json",
    "quick_start": "chapters/02-quick-start.json",
    "architecture_overview": "chapters/03-architecture-overview.json",
    "main_flows": "chapters/04-main-flows.json",
    "module_details": "chapters/05-module-details.json",
}


@dataclass(frozen=True)
class ManifestPackage:
    root_dir: Path
    manifest_path: Path
    manifest: dict
    chapters: dict


def manifest_shape_errors(manifest) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []

    if not isinstance(manifest, dict):
        return [
            ValidationIssue(
                code="manifest.root_type",
                path="$",
                message="0.4.0 manifest root must be an object",
            )
        ]

    if "dsl_version" in manifest:
        issues.append(
            ValidationIssue(
                code="manifest.dsl_version",
                path="$.dsl_version",
                message="0.4.0 manifest must not contain dsl_version",
            )
        )

    actual_keys = set(manifest.keys())
    expected_keys = set(FIXED_MANIFEST.keys())
    if actual_keys != expected_keys:
        expected = ", ".join(FIXED_MANIFEST.keys())
        issues.append(
            ValidationIssue(
                code="manifest.keys",
                path="$",
                message=f"0.4.0 manifest keys must exactly match: {expected}",
            )
        )

    for key, expected_path in FIXED_MANIFEST.items():
        if key not in manifest:
            continue
        if manifest[key] != expected_path:
            issues.append(
                ValidationIssue(
                    code="manifest.path",
                    path=f"$.{key}",
                    message=f"{key} must equal {expected_path}",
                )
            )

    return issues


def load_manifest_package(manifest_path) -> ManifestPackage:
    manifest_path = Path(manifest_path)
    manifest = _read_json_file(manifest_path, "manifest")

    issues = manifest_shape_errors(manifest)
    if issues:
        raise ValueError("\n".join(issue.format() for issue in issues))

    root_dir = manifest_path.parent
    chapters = {}
    for key, relative_path in FIXED_MANIFEST.items():
        chapters[key] = _read_json_file(root_dir / relative_path, key)

    return ManifestPackage(
        root_dir=root_dir,
        manifest_path=manifest_path,
        manifest=manifest,
        chapters=chapters,
    )


def _read_json_file(path: Path, label: str):
    try:
        if path.is_dir():
            raise ValueError(f"{label} JSON path is a directory: {path}")
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"{label} JSON file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"{label} JSON parse failed at line {exc.lineno}, column {exc.colno}: {path}") from exc
