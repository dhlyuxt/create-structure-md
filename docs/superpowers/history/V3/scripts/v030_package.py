import json
import re
from dataclasses import dataclass
from pathlib import Path

from jsonschema import Draft202012Validator

from scripts.v030_paths import is_normalized_relative_posix, resolve_manifest_child
from scripts.v030_types import ValidationIssue


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_SCHEMA_PATH = ROOT / "schemas/v0.3.0/structure.manifest.schema.json"
FIXED_MANIFEST_KEYS = [
    "document",
    "repository_overview",
    "directory_map",
    "module_layers",
    "repository_mainline",
    "key_mechanisms",
    "integration_boundaries",
    "risks_validation",
]
SINGLE_CHAPTER_KEYS = [key for key in FIXED_MANIFEST_KEYS if key != "key_mechanisms"]
MECHANISM_KEY_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
FORBIDDEN_MECHANISM_AGGREGATE = "chapters/06-key-mechanisms.json"


@dataclass(frozen=True)
class MechanismFile:
    key: str
    manifest_path: str
    filesystem_path: Path
    data: dict


@dataclass(frozen=True)
class ManifestPackage:
    manifest_path: Path
    root_dir: Path
    manifest: dict
    chapters: dict[str, dict]
    chapter_files: dict[str, Path]
    mechanisms: list[MechanismFile]

    @property
    def declared_paths(self) -> set[str]:
        paths = set()
        for key in SINGLE_CHAPTER_KEYS:
            paths.add(self.manifest[key])
        paths.update(self.manifest["key_mechanisms"])
        return paths


def infer_mechanism_key(manifest_path: str) -> str:
    return Path(manifest_path).name.removesuffix(".json")


def manifest_schema_errors(manifest) -> list[ValidationIssue]:
    schema = json.loads(MANIFEST_SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    return [
        ValidationIssue("ERROR", "manifest.schema", "$", error.message)
        for error in sorted(validator.iter_errors(manifest), key=lambda item: list(item.path))
    ]


def manifest_shape_errors(manifest) -> list[ValidationIssue]:
    errors: list[ValidationIssue] = []
    if not isinstance(manifest, dict):
        return [ValidationIssue("ERROR", "manifest.root", "$", "manifest root must be an object")]
    errors.extend(manifest_schema_errors(manifest))
    if set(manifest.keys()) != set(FIXED_MANIFEST_KEYS):
        errors.append(
            ValidationIssue(
                "ERROR",
                "manifest.fixed_keys",
                "$",
                "structure.manifest.json must contain exactly the fixed chapter keys",
            )
        )
    paths: list[str] = []
    for key in SINGLE_CHAPTER_KEYS:
        value = manifest.get(key)
        if not is_normalized_relative_posix(value, require_json=True):
            errors.append(
                ValidationIssue(
                    "ERROR",
                    "manifest.path",
                    f"$.{key}",
                    "manifest path must be a normalized relative POSIX .json path",
                )
            )
        else:
            paths.append(value)
    mechanisms = manifest.get("key_mechanisms")
    if not isinstance(mechanisms, list):
        errors.append(
            ValidationIssue(
                "ERROR",
                "manifest.key_mechanisms",
                "$.key_mechanisms",
                "key_mechanisms must be an array of manifest paths",
            )
        )
        mechanisms = []
    seen_keys: set[str] = set()
    for index, value in enumerate(mechanisms):
        if value == FORBIDDEN_MECHANISM_AGGREGATE:
            errors.append(
                ValidationIssue(
                    "ERROR",
                    "manifest.no_aggregate_chapter6",
                    f"$.key_mechanisms[{index}]",
                    "chapters/06-key-mechanisms.json is forbidden",
                )
            )
            continue
        if not is_normalized_relative_posix(value, require_json=True):
            errors.append(
                ValidationIssue(
                    "ERROR",
                    "manifest.path",
                    f"$.key_mechanisms[{index}]",
                    "manifest path must be a normalized relative POSIX .json path",
                )
            )
            continue
        key = infer_mechanism_key(value)
        if not MECHANISM_KEY_RE.match(key):
            errors.append(
                ValidationIssue(
                    "ERROR",
                    "manifest.mechanism_key",
                    f"$.key_mechanisms[{index}]",
                    f"invalid mechanism key: {key}",
                )
            )
        if key in seen_keys:
            errors.append(
                ValidationIssue(
                    "ERROR",
                    "manifest.mechanism_key_unique",
                    f"$.key_mechanisms[{index}]",
                    f"duplicate mechanism key: {key}",
                )
            )
        seen_keys.add(key)
        paths.append(value)
    if len(paths) != len(set(paths)):
        errors.append(ValidationIssue("ERROR", "manifest.path_unique", "$", "Manifest paths must be unique"))
    return errors


def load_json(path: Path) -> dict:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise ValueError(f"file not found: {path}") from exc
    except OSError as exc:
        raise ValueError(f"unable to read JSON file {path}: {exc.strerror or exc}") from exc
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON at {path}:{exc.lineno}:{exc.colno}: {exc.msg}") from exc


def load_manifest_package(manifest_path: Path | str) -> ManifestPackage:
    manifest_path = Path(manifest_path)
    manifest = load_json(manifest_path)
    errors = manifest_shape_errors(manifest)
    if errors:
        raise ValueError(errors[0].format())
    root_dir = manifest_path.parent
    chapters: dict[str, dict] = {}
    chapter_files: dict[str, Path] = {}
    for key in SINGLE_CHAPTER_KEYS:
        child_path = resolve_manifest_child(root_dir, manifest[key])
        chapters[key] = load_json(child_path)
        chapter_files[key] = child_path
    mechanisms: list[MechanismFile] = []
    for value in manifest["key_mechanisms"]:
        child_path = resolve_manifest_child(root_dir, value)
        mechanisms.append(MechanismFile(infer_mechanism_key(value), value, child_path, load_json(child_path)))
    return ManifestPackage(manifest_path, root_dir, manifest, chapters, chapter_files, mechanisms)
