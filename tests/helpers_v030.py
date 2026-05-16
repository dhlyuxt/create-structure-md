import json
from pathlib import Path


FIXED_MANIFEST = {
    "document": "chapters/01-document.json",
    "repository_overview": "chapters/02-repository-overview.json",
    "directory_map": "chapters/03-directory-map.json",
    "module_layers": "chapters/04-module-layers.json",
    "repository_mainline": "chapters/05-repository-mainline.json",
    "key_mechanisms": ["chapters/06-key-mechanisms/persistence.json"],
    "integration_boundaries": "chapters/07-integration-boundaries.json",
    "risks_validation": "chapters/08-risks-validation.json",
}


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def write_manifest_only_package(tmpdir: str, manifest=None) -> Path:
    root = Path(tmpdir)
    manifest_value = dict(FIXED_MANIFEST if manifest is None else manifest)
    write_json(root / "structure.manifest.json", manifest_value)
    for value in manifest_value.values():
        paths = value if isinstance(value, list) else [value]
        for child in paths:
            write_json(root / child, {})
    return root / "structure.manifest.json"
