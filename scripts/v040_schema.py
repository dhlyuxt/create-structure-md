import json
from pathlib import Path

from jsonschema import Draft202012Validator

from scripts.v040_package import ManifestPackage
from scripts.v040_types import ValidationResult


ROOT = Path(__file__).resolve().parents[1]
CHAPTER_SCHEMA_PATH = ROOT / "schemas/v0.4.0/chapter.schema.json"

STATIC_CHAPTER_DEF_BY_KEY = {
    "document": "DocumentChapter",
    "overview": "OverviewChapter",
    "quick_start": "QuickStartChapter",
    "architecture_overview": "ArchitectureOverviewChapter",
    "main_flow_overview": "MainFlowOverviewChapter",
    "module_overview": "ModuleOverviewChapter",
}

DETAIL_DEF_BY_KIND = {
    "main_flow_details": "MainFlowDetail",
    "module_details": "ModuleDetail",
}


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


def schema_validation_result(package: ManifestPackage) -> ValidationResult:
    result = ValidationResult()
    for key, def_name in STATIC_CHAPTER_DEF_BY_KEY.items():
        _validate_value(result, def_name, package.chapters[key], "$")
    for index, detail in enumerate(package.main_flow_details):
        _validate_value(result, "MainFlowDetail", detail.data, f"$.main_flow_details[{index}]")
    for index, detail in enumerate(package.module_details):
        _validate_value(result, "ModuleDetail", detail.data, f"$.module_details[{index}]")
    return result


def _validate_value(result, def_name, value, path_prefix):
    validator = validator_for(def_name)
    errors = sorted(validator.iter_errors(value), key=lambda error: list(error.path))
    for error in errors:
        result.error("schema", _schema_error_path(path_prefix, error.path), error.message)


def _schema_error_path(path_prefix: str, path) -> str:
    if not path:
        return path_prefix
    if path_prefix == "$":
        return _json_path(path)
    return path_prefix + _json_path(path)[1:]


def _json_path(path) -> str:
    value = "$"
    for part in path:
        if isinstance(part, int):
            value += f"[{part}]"
        else:
            value += f".{part}"
    return value
