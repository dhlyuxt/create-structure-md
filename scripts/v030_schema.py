import json
from pathlib import Path

from jsonschema import Draft202012Validator

from scripts.v030_package import SINGLE_CHAPTER_KEYS, ManifestPackage
from scripts.v030_types import ValidationResult, json_path


ROOT = Path(__file__).resolve().parents[1]
CHAPTER_SCHEMA_PATH = ROOT / "schemas/v0.3.0/chapter.schema.json"


def load_chapter_schema() -> dict:
    return json.loads(CHAPTER_SCHEMA_PATH.read_text(encoding="utf-8"))


def validator_for(def_name: str) -> Draft202012Validator:
    schema = load_chapter_schema()
    selected = {
        "$schema": schema["$schema"],
        "$defs": schema["$defs"],
        "$ref": f"#/$defs/{def_name}",
    }
    Draft202012Validator.check_schema(selected)
    return Draft202012Validator(selected)


CHAPTER_DEF_BY_KEY = {
    "document": "DocumentChapter",
    "repository_overview": "RepositoryOverviewChapter",
    "directory_map": "DirectoryMapChapter",
    "module_layers": "ModuleLayersChapter",
    "repository_mainline": "RepositoryMainlineChapter",
    "integration_boundaries": "IntegrationBoundariesChapter",
    "risks_validation": "RisksValidationChapter",
}


def append_schema_errors(result: ValidationResult, def_name: str, value, prefix: str) -> None:
    errors = sorted(validator_for(def_name).iter_errors(value), key=lambda error: list(error.path))
    for error in errors:
        result.error("schema", f"{prefix}{json_path(error.path)[1:]}", error.message)


def schema_validation_result(package: ManifestPackage) -> ValidationResult:
    result = ValidationResult()
    for key in SINGLE_CHAPTER_KEYS:
        data = package.chapters[key]
        append_schema_errors(result, CHAPTER_DEF_BY_KEY[key], data, f"$.{key}")
        if not isinstance(data, dict):
            continue
        chapter = data.get("chapter", {})
        if chapter.get("key") != key:
            result.error("chapter.key", f"$.{key}.chapter.key", "chapter.key must match manifest property")
    for index, mechanism in enumerate(package.mechanisms):
        append_schema_errors(result, "MechanismChapter", mechanism.data, f"$.key_mechanisms[{index}]")
        if isinstance(mechanism.data, dict) and "chapter" in mechanism.data:
            result.error("mechanism.chapter", f"$.key_mechanisms[{index}].chapter", "Mechanism JSON files must not contain chapter")
    return result
