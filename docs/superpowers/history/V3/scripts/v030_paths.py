from pathlib import Path


def is_normalized_relative_posix(value: str, *, require_json: bool = False) -> bool:
    if not isinstance(value, str) or not value:
        return False
    if value.startswith("/") or "\\" in value:
        return False
    parts = value.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        return False
    if require_json and not value.endswith(".json"):
        return False
    return True


def resolve_manifest_child(root_dir: Path, manifest_path: str) -> Path:
    if not is_normalized_relative_posix(manifest_path, require_json=True):
        raise ValueError(f"invalid manifest path: {manifest_path}")
    root = root_dir.resolve()
    target = (root_dir / manifest_path).resolve()
    if target != root and root not in target.parents:
        raise ValueError(f"manifest path escapes package root: {manifest_path}")
    return target
