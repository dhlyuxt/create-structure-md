import json
from pathlib import Path

from jsonschema import Draft202012Validator

from scripts.v040_package import FIXED_MANIFEST, ManifestPackage
from scripts.v040_types import ValidationResult


ROOT = Path(__file__).resolve().parents[1]
CHAPTER_SCHEMA_PATH = ROOT / "schemas/v0.4.0/chapter.schema.json"

CHAPTER_DEF_BY_KEY = {
    "document": "DocumentChapter",
    "overview": "OverviewChapter",
    "quick_start": "QuickStartChapter",
    "architecture_overview": "ArchitectureOverviewChapter",
    "main_flows": "MainFlowsChapter",
    "module_details": "ModuleDetailsChapter",
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
    for key in FIXED_MANIFEST:
        validator = validator_for(CHAPTER_DEF_BY_KEY[key])
        errors = sorted(
            validator.iter_errors(package.chapters[key]),
            key=lambda error: list(error.path),
        )
        for error in errors:
            result.error("schema", f"$.{key}{_json_path(error.path)[1:]}", error.message)
    return result


def _json_path(path) -> str:
    value = "$"
    for part in path:
        if isinstance(part, int):
            value += f"[{part}]"
        else:
            value += f".{part}"
    return value
