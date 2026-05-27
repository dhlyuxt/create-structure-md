import json
import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from scripts.v040_types import ValidationIssue


STATIC_MANIFEST = {
    "document": "chapters/00-document.json",
    "overview": "chapters/01-overview.json",
    "quick_start": "chapters/02-quick-start.json",
    "architecture_overview": "chapters/03-architecture-overview.json",
    "main_flow_overview": "chapters/04-main-flow-overview.json",
    "module_overview": "chapters/05-module-overview.json",
}

DETAIL_MANIFEST_KEYS = ("main_flow_details", "module_details")

DETAIL_PREFIXES = {
    "main_flow_details": "chapters/04-main-flow-details/",
    "module_details": "chapters/05-module-details/",
}

FORBIDDEN_AGGREGATE_PATHS = {
    "chapters/04-main-flows.json",
    "chapters/05-module-details.json",
}

DETAIL_KEY_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")


@dataclass(frozen=True)
class DetailFile:
    kind: str
    key: str
    relative_path: str
    path: Path
    data: dict


@dataclass(frozen=True)
class ManifestPackage:
    root_dir: Path
    manifest_path: Path
    manifest: dict
    chapters: dict
    main_flow_details: list[DetailFile]
    module_details: list[DetailFile]


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
    expected_keys = set(STATIC_MANIFEST.keys()) | set(DETAIL_MANIFEST_KEYS)
    if actual_keys != expected_keys:
        expected = ", ".join([*STATIC_MANIFEST.keys(), *DETAIL_MANIFEST_KEYS])
        issues.append(
            ValidationIssue(
                code="manifest.keys",
                path="$",
                message=(
                    "active 0.4.0 manifest must use main_flow_overview; "
                    f"0.4.0 manifest keys must exactly match: {expected}"
                ),
            )
        )

    manifest_paths = []

    for key, expected_path in STATIC_MANIFEST.items():
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
        if isinstance(manifest[key], str):
            manifest_paths.append(manifest[key])

    for key in DETAIL_MANIFEST_KEYS:
        if key not in manifest:
            continue
        detail_paths = manifest[key]
        if not isinstance(detail_paths, list) or not detail_paths:
            issues.append(
                ValidationIssue(
                    code="manifest.detail_array",
                    path=f"$.{key}",
                    message=f"{key} must be a non-empty array",
                )
            )
            continue

        for index, relative_path in enumerate(detail_paths):
            issue_path = f"$.{key}[{index}]"
            valid_path = _validate_manifest_path(relative_path, issue_path, issues)
            if isinstance(relative_path, str):
                manifest_paths.append(relative_path)
                if relative_path not in FORBIDDEN_AGGREGATE_PATHS:
                    prefix = DETAIL_PREFIXES[key]
                    if not relative_path.startswith(prefix):
                        issues.append(
                            ValidationIssue(
                                code="manifest.detail_path",
                                path=issue_path,
                                message=f"{key} path must start with {prefix}",
                            )
                        )
                    elif valid_path and _detail_key(relative_path) is None:
                        issues.append(
                            ValidationIssue(
                                code="manifest.detail_key",
                                path=issue_path,
                                message="file stem must match [a-z0-9][a-z0-9_-]*",
                            )
                        )

    if len(manifest_paths) != len(set(manifest_paths)):
        issues.append(
            ValidationIssue(
                code="manifest.path_duplicate",
                path="$",
                message="manifest paths must be unique",
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
    for key, relative_path in STATIC_MANIFEST.items():
        chapters[key] = _read_package_json_file(root_dir, relative_path, key)
    main_flow_details = _load_detail_files(root_dir, manifest, "main_flow_details")
    module_details = _load_detail_files(root_dir, manifest, "module_details")

    return ManifestPackage(
        root_dir=root_dir,
        manifest_path=manifest_path,
        manifest=manifest,
        chapters=chapters,
        main_flow_details=main_flow_details,
        module_details=module_details,
    )


def _validate_manifest_path(value, path, issues) -> bool:
    if not isinstance(value, str):
        issues.append(
            ValidationIssue(
                code="manifest.path",
                path=path,
                message="manifest path must be a relative POSIX .json path",
            )
        )
        return False

    if value in FORBIDDEN_AGGREGATE_PATHS:
        issues.append(
            ValidationIssue(
                code="manifest.forbidden_path",
                path=path,
                message="old aggregate path is invalid",
            )
        )
        return False

    posix_path = PurePosixPath(value)
    invalid = (
        posix_path.is_absolute()
        or "\\" in value
        or "//" in value
        or posix_path.suffix != ".json"
        or any(part in {".", ".."} for part in posix_path.parts)
    )
    if invalid:
        issues.append(
            ValidationIssue(
                code="manifest.path",
                path=path,
                message="manifest path must be a relative POSIX .json path",
            )
        )
        return False

    return True


def _detail_key(value):
    stem = PurePosixPath(value).stem
    if DETAIL_KEY_RE.fullmatch(stem):
        return stem
    return None


def _safe_package_path(root_dir: Path, relative_path: str) -> Path:
    candidate = root_dir / relative_path
    try:
        candidate.resolve().relative_to(root_dir.resolve())
    except ValueError as exc:
        raise ValueError(f"manifest path resolves outside package root: {relative_path}") from exc
    return candidate


def _read_package_json_file(root_dir: Path, relative_path: str, label: str):
    return _read_json_file(_safe_package_path(root_dir, relative_path), label)


def _load_detail_files(root_dir: Path, manifest: dict, kind: str) -> list[DetailFile]:
    details = []
    for relative_path in manifest[kind]:
        details.append(
            DetailFile(
                kind=kind,
                key=PurePosixPath(relative_path).stem,
                relative_path=relative_path,
                path=_safe_package_path(root_dir, relative_path),
                data=_read_package_json_file(root_dir, relative_path, relative_path),
            )
        )
    return details


def _read_json_file(path: Path, label: str):
    try:
        if path.is_dir():
            raise ValueError(f"{label} JSON path is a directory: {path}")
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"{label} JSON file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"{label} JSON parse failed at line {exc.lineno}, column {exc.colno}: {path}") from exc
