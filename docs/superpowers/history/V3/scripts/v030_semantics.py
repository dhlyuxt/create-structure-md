from pathlib import Path

from scripts.v030_package import ManifestPackage
from scripts.v030_types import ValidationResult


def collect_diagrams(value, path="$"):
    if isinstance(value, dict):
        if {"id", "title", "diagram_type", "description", "source"}.issubset(value):
            yield path, value
        for key, child in value.items():
            yield from collect_diagrams(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from collect_diagrams(child, f"{path}[{index}]")


def walk_source_refs(value, path="$"):
    if isinstance(value, dict):
        if "path" in value and set(value.keys()).issubset({"path", "symbol"}):
            yield path, value
        for key, child in value.items():
            yield from walk_source_refs(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from walk_source_refs(child, f"{path}[{index}]")


def check_unique(result: ValidationResult, collection, id_field: str, label: str, path: str) -> None:
    seen: dict[str, int] = {}
    for index, item in enumerate(collection):
        value = item[id_field]
        if value in seen:
            result.error(f"semantic.{label}_unique", f"{path}[{index}].{id_field}", f"duplicate {label}: {value}")
        else:
            seen[value] = index


def check_ordered(result: ValidationResult, collection, path: str) -> None:
    orders = [item["order"] for item in collection]
    expected = list(range(1, len(collection) + 1))
    if orders != expected:
        result.error("semantic.order", path, f"order values must start at 1 without gaps: expected {expected}, got {orders}")


def semantic_validation_result(package: ManifestPackage, repo_root: Path | None = None) -> ValidationResult:
    result = ValidationResult()
    module_layers = package.chapters["module_layers"]
    risks_chapter = package.chapters["risks_validation"]

    check_unique(result, module_layers["layers"], "layer_id", "layer-id", "$.module_layers.layers")
    check_unique(result, module_layers["modules"], "module_id", "module-id", "$.module_layers.modules")
    check_unique(result, package.chapters["repository_mainline"]["mainlines"], "mainline_id", "mainline-id", "$.repository_mainline.mainlines")
    check_unique(result, risks_chapter["risks"], "risk_id", "risk-id", "$.risks_validation.risks")
    check_unique(result, risks_chapter["assumptions"], "assumption_id", "assumption-id", "$.risks_validation.assumptions")
    check_unique(result, risks_chapter["validation_gaps"], "gap_id", "gap-id", "$.risks_validation.validation_gaps")
    check_unique(result, risks_chapter["low_confidence_items"], "item_id", "item-id", "$.risks_validation.low_confidence_items")
    check_ordered(result, package.chapters["repository_overview"]["reading_route"]["steps"], "$.repository_overview.reading_route.steps")

    module_ids = {module["module_id"] for module in module_layers["modules"]}
    layer_ids = {layer["layer_id"] for layer in module_layers["layers"]}
    mechanism_keys = {mechanism.key for mechanism in package.mechanisms}

    for module_index, module in enumerate(module_layers["modules"]):
        if module["layer_id"] not in layer_ids:
            result.error("semantic.layer_ref", f"$.module_layers.modules[{module_index}].layer_id", f"layer-id does not resolve: {module['layer_id']}")
        for collab_index, collab in enumerate(module.get("collaborates_with", [])):
            if collab["module_ref"] not in module_ids:
                result.error("semantic.module_ref", f"$.module_layers.modules[{module_index}].collaborates_with[{collab_index}].module_ref", f"module-id does not resolve: {collab['module_ref']}")

    for mainline_index, mainline in enumerate(package.chapters["repository_mainline"]["mainlines"]):
        check_ordered(result, mainline["steps"], f"$.repository_mainline.mainlines[{mainline_index}].steps")
        for step_index, step in enumerate(mainline["steps"]):
            for ref_index, module_ref in enumerate(step.get("module_refs", [])):
                if module_ref not in module_ids:
                    result.error("semantic.module_ref", f"$.repository_mainline.mainlines[{mainline_index}].steps[{step_index}].module_refs[{ref_index}]", f"module-id does not resolve: {module_ref}")

    for mechanism_index, mechanism in enumerate(package.mechanisms):
        check_ordered(result, mechanism.data["flow"], f"$.key_mechanisms[{mechanism_index}].flow")
        for ref_index, module_ref in enumerate(mechanism.data.get("related_modules", [])):
            if module_ref not in module_ids:
                result.error("semantic.module_ref", f"$.key_mechanisms[{mechanism_index}].related_modules[{ref_index}]", f"module-id does not resolve: {module_ref}")

    for risk_index, risk in enumerate(risks_chapter["risks"]):
        for ref_index, module_ref in enumerate(risk["related_modules"]):
            if module_ref not in module_ids:
                result.error("semantic.module_ref", f"$.risks_validation.risks[{risk_index}].related_modules[{ref_index}]", f"module-id does not resolve: {module_ref}")
        for ref_index, mechanism_key in enumerate(risk["related_mechanisms"]):
            if mechanism_key not in mechanism_keys:
                result.error("semantic.mechanism_ref", f"$.risks_validation.risks[{risk_index}].related_mechanisms[{ref_index}]", f"mechanism-key does not resolve: {mechanism_key}")

    diagram_ids: dict[str, str] = {}
    for key, chapter in package.chapters.items():
        for path, diagram in collect_diagrams(chapter, f"$.{key}"):
            diagram_id = diagram["id"]
            if diagram_id in diagram_ids:
                result.error("semantic.diagram_id_unique", path + ".id", f"duplicate diagram-id: {diagram_id}")
            diagram_ids[diagram_id] = path
    for index, mechanism in enumerate(package.mechanisms):
        for path, diagram in collect_diagrams(mechanism.data, f"$.key_mechanisms[{index}]"):
            diagram_id = diagram["id"]
            if diagram_id in diagram_ids:
                result.error("semantic.diagram_id_unique", path + ".id", f"duplicate diagram-id: {diagram_id}")
            diagram_ids[diagram_id] = path

    if not package.mechanisms:
        gaps = risks_chapter["validation_gaps"]
        has_required_gap = any(
            gap["gap_type"] == "no_key_mechanisms_selected" and "key_mechanisms" in gap["related_chapters"]
            for gap in gaps
        )
        if not has_required_gap:
            result.error("semantic.empty_mechanisms_gap", "$.risks_validation.validation_gaps", "empty key_mechanisms requires a no_key_mechanisms_selected validation gap related to key_mechanisms")

    for item_index, item in enumerate(risks_chapter["low_confidence_items"]):
        location = item["location"]
        if location["kind"] == "manifest_path" and location["path"] not in package.declared_paths:
            result.error(
                "semantic.diagnostic_manifest_path",
                f"$.risks_validation.low_confidence_items[{item_index}].location.path",
                f"diagnostic manifest path does not resolve to a manifest child: {location['path']}",
            )

    if repo_root is not None:
        repo_root = Path(repo_root)
        for key, chapter in package.chapters.items():
            for path, source_ref in walk_source_refs(chapter, f"$.{key}"):
                source_path = repo_root / source_ref["path"]
                if not source_path.exists():
                    result.error("semantic.source_ref_path", path + ".path", f"SourceRef.path does not exist: {source_ref['path']}")
                elif "symbol" in source_ref and not source_path.is_file():
                    result.error("semantic.source_ref_file", path + ".path", f"SourceRef.symbol requires path to identify a source file: {source_ref['path']}")
        for index, mechanism in enumerate(package.mechanisms):
            for path, source_ref in walk_source_refs(mechanism.data, f"$.key_mechanisms[{index}]"):
                source_path = repo_root / source_ref["path"]
                if not source_path.exists():
                    result.error("semantic.source_ref_path", path + ".path", f"SourceRef.path does not exist: {source_ref['path']}")
                elif "symbol" in source_ref and not source_path.is_file():
                    result.error("semantic.source_ref_file", path + ".path", f"SourceRef.symbol requires path to identify a source file: {source_ref['path']}")

    return result
