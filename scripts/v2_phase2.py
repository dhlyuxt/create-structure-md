from dataclasses import dataclass

try:
    from v2_foundation import (
        ANCHOR_TYPE_VALUES,
        EXECUTABLE_INTERFACE_TYPES,
        RuleViolation,
        as_rows,
        has_reason,
    )
except ModuleNotFoundError:
    from scripts.v2_foundation import (
        ANCHOR_TYPE_VALUES,
        EXECUTABLE_INTERFACE_TYPES,
        RuleViolation,
        as_rows,
        has_reason,
    )


CONTRACT_INTERFACE_TYPES = (
    "schema_contract",
    "dsl_contract",
    "document_contract",
    "configuration_contract",
    "data_contract",
    "test_fixture",
)


@dataclass(frozen=True)
class Phase2Warning:
    path: str
    message: str


def _non_empty(value):
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, list):
        return len(value) > 0
    return value is not None


def _walk(value, path="$"):
    yield path, value
    if isinstance(value, dict):
        for key, child in value.items():
            yield from _walk(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _walk(child, f"{path}[{index}]")


def _ids_from_collection(collection, field_name):
    return {
        row.get(field_name)
        for row in collection
        if isinstance(row, dict) and isinstance(row.get(field_name), str) and row.get(field_name)
    }


def _module_ids(document):
    rows = document.get("architecture_views", {}).get("module_intro", {}).get("rows", [])
    return _ids_from_collection(rows if isinstance(rows, list) else [], "module_id")


def _chapter6_dependency_ids(document):
    rows = document.get("configuration_data_dependencies", {}).get("dependencies", {}).get("rows", [])
    return _ids_from_collection(rows if isinstance(rows, list) else [], "dependency_id")


def _module_data_ids(document):
    ids = set()
    for module in document.get("module_design", {}).get("modules", []):
        if isinstance(module, dict):
            ids.update(_ids_from_collection(as_rows(module.get("data_objects")), "data_id"))
    return ids


def _module_dependency_ids(document):
    ids = set()
    for module in document.get("module_design", {}).get("modules", []):
        if isinstance(module, dict):
            ids.update(_ids_from_collection(as_rows(module.get("dependencies")), "dependency_id"))
    return ids


def _parameter_ids(document):
    ids = set()
    for module in document.get("module_design", {}).get("modules", []):
        if not isinstance(module, dict):
            continue
        parameters = module.get("configuration", {}).get("parameters", {})
        ids.update(_ids_from_collection(as_rows(parameters), "parameter_id"))
    return ids


def _interface_ids(document):
    ids = set()
    for module in document.get("module_design", {}).get("modules", []):
        if not isinstance(module, dict):
            continue
        public_interfaces = module.get("public_interfaces", {})
        interface_index = public_interfaces.get("interface_index", {})
        ids.update(_ids_from_collection(as_rows(interface_index), "interface_id"))
        ids.update(_ids_from_collection(public_interfaces.get("interfaces", []), "interface_id"))
    return ids


def _mechanism_ids(document):
    ids = set()
    for module in document.get("module_design", {}).get("modules", []):
        if not isinstance(module, dict):
            continue
        mechanism = module.get("internal_mechanism", {})
        ids.update(_ids_from_collection(as_rows(mechanism.get("mechanism_index")), "mechanism_id"))
        ids.update(_ids_from_collection(mechanism.get("mechanism_details", []), "mechanism_id"))
    return ids


def _diagram_ids(document):
    ids = set()
    for _path, value in _walk(document):
        if isinstance(value, dict) and {"id", "diagram_type", "source"}.issubset(value):
            diagram_id = value.get("id")
            if isinstance(diagram_id, str) and diagram_id:
                ids.add(diagram_id)
    return ids


def _table_ids(document):
    ids = set()
    for _path, value in _walk(document):
        if isinstance(value, dict) and {"id", "title", "columns", "rows"}.issubset(value):
            table_id = value.get("id")
            if isinstance(table_id, str) and table_id:
                ids.add(table_id)
    return ids


def _support_ids(document):
    return {
        "evidence_id": _ids_from_collection(document.get("evidence", []), "id"),
        "traceability_id": _ids_from_collection(document.get("traceability", []), "id"),
        "source_snippet_id": _ids_from_collection(document.get("source_snippets", []), "id"),
    }


def _duplicate_values(values):
    seen = set()
    duplicates = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    return duplicates


def phase2_module_model_violations(document):
    violations = []
    if not isinstance(document, dict):
        return violations

    chapter3_ids = _module_ids(document)
    system_dependency_ids = _chapter6_dependency_ids(document)
    module_data_ids = _module_data_ids(document)
    diagram_ids = _diagram_ids(document)
    table_ids = _table_ids(document)
    support_ids = _support_ids(document)

    design_modules = document.get("module_design", {}).get("modules", [])
    if not isinstance(design_modules, list):
        return violations
    design_ids = [
        module.get("module_id")
        for module in design_modules
        if isinstance(module, dict) and isinstance(module.get("module_id"), str)
    ]
    if set(design_ids) != chapter3_ids or len(design_ids) != len(chapter3_ids):
        violations.append(
            RuleViolation(
                "$.module_design.modules",
                "must match chapter 3 modules one-to-one",
            )
        )

    anchor_targets = {
        "module_id": chapter3_ids,
        "interface_id": _interface_ids(document),
        "data_id": module_data_ids,
        "dependency_id": system_dependency_ids | _module_dependency_ids(document),
        "parameter_id": _parameter_ids(document),
        "diagram_id": diagram_ids,
        "table_id": table_ids,
        **support_ids,
    }

    for module_index, module in enumerate(design_modules):
        if not isinstance(module, dict):
            continue
        base = f"$.module_design.modules[{module_index}]"
        violations.extend(_source_scope_violations(module, base))
        violations.extend(_configuration_violations(module, base))
        violations.extend(_dependency_violations(module, base, chapter3_ids, module_data_ids, system_dependency_ids))
        violations.extend(_interface_violations(module, base))
        violations.extend(_internal_mechanism_violations(module, base, anchor_targets))

    violations.extend(_runtime_unit_violations(document))
    return violations


def phase2_module_model_warnings(document):
    warnings = []
    modules = document.get("module_design", {}).get("modules", [])
    if not isinstance(modules, list):
        return warnings
    for module_index, module in enumerate(modules):
        interfaces = module.get("public_interfaces", {}).get("interfaces", []) if isinstance(module, dict) else []
        if not isinstance(interfaces, list):
            continue
        for interface_index, interface in enumerate(interfaces):
            if not isinstance(interface, dict):
                continue
            interface_type = interface.get("interface_type")
            if interface_type not in ("function", "method") or interface.get("confidence") != "observed":
                continue
            location = interface.get("location", {})
            symbol = location.get("symbol") if isinstance(location, dict) else ""
            line_start = location.get("line_start") if isinstance(location, dict) else None
            line_end = location.get("line_end") if isinstance(location, dict) else None
            has_symbol = isinstance(symbol, str) and bool(symbol.strip())
            has_line_range = isinstance(line_start, int) and isinstance(line_end, int)
            if not has_symbol and not has_line_range:
                warnings.append(
                    Phase2Warning(
                        f"$.module_design.modules[{module_index}].public_interfaces.interfaces[{interface_index}].location",
                        "observed function or method interface should provide symbol or line range",
                    )
                )
    return warnings


def _source_scope_violations(module, base):
    source_scope = module.get("source_scope", {})
    scope_fields = ["primary_files", "consumed_inputs", "owned_outputs"]
    if not any(isinstance(source_scope.get(field_name), list) and source_scope.get(field_name) for field_name in scope_fields):
        return [
            RuleViolation(
                f"{base}.source_scope",
                "source_scope must provide primary_files, consumed_inputs, or owned_outputs",
            )
        ]
    return []


def _configuration_violations(module, base):
    violations = []
    parameters = module.get("configuration", {}).get("parameters", {})
    for row_index, row in enumerate(as_rows(parameters)):
        if row.get("value_source") != "unknown" and not _non_empty(row.get("value_or_default")):
            violations.append(
                RuleViolation(
                    f"{base}.configuration.parameters.rows[{row_index}].value_or_default",
                    "value_or_default must be non-empty unless value_source is unknown",
                )
            )
    return violations


def _dependency_violations(module, base, module_ids, module_data_ids, system_dependency_ids):
    violations = []
    for row_index, row in enumerate(as_rows(module.get("dependencies"))):
        row_base = f"{base}.dependencies.rows[{row_index}]"
        if row.get("dependency_type") == "internal_module" and row.get("target_module_id") not in module_ids:
            violations.append(
                RuleViolation(
                    f"{row_base}.target_module_id",
                    "target_module_id must reference an existing module",
                )
            )
        if row.get("dependency_type") == "data_object" and row.get("target_data_id") not in module_data_ids:
            violations.append(
                RuleViolation(
                    f"{row_base}.target_data_id",
                    "target_data_id must reference an existing data object",
                )
            )
        system_dependency_ref = row.get("system_dependency_ref")
        if _non_empty(system_dependency_ref) and system_dependency_ref not in system_dependency_ids:
            violations.append(
                RuleViolation(
                    f"{row_base}.system_dependency_ref",
                    "system_dependency_ref must reference a Chapter 6 dependency",
                )
            )
        if _non_empty(row.get("dependency_id")) and row.get("dependency_id") == system_dependency_ref:
            violations.append(
                RuleViolation(
                    f"{row_base}.system_dependency_ref",
                    "dependency_id must not equal system_dependency_ref",
                )
            )
    return violations


def _interface_violations(module, base):
    violations = []
    public_interfaces = module.get("public_interfaces", {})
    index_rows = as_rows(public_interfaces.get("interface_index", {}))
    details = public_interfaces.get("interfaces", [])
    if not isinstance(details, list):
        details = []
    index_ids = [row.get("interface_id") for row in index_rows]
    detail_ids = [detail.get("interface_id") for detail in details if isinstance(detail, dict)]
    if set(index_ids) != set(detail_ids) or len(index_ids) != len(detail_ids):
        violations.append(
            RuleViolation(
                f"{base}.public_interfaces",
                "interface_index rows and interface details must have matching interface_id sets",
            )
        )
    for duplicate in _duplicate_values(index_ids):
        violations.append(RuleViolation(f"{base}.public_interfaces.interface_index.rows", f"duplicate interface_id {duplicate}"))
    for duplicate in _duplicate_values(detail_ids):
        violations.append(RuleViolation(f"{base}.public_interfaces.interfaces", f"duplicate interface_id {duplicate}"))

    for interface_index, interface in enumerate(details):
        if not isinstance(interface, dict):
            continue
        interface_base = f"{base}.public_interfaces.interfaces[{interface_index}]"
        interface_type = interface.get("interface_type")
        if interface_type in EXECUTABLE_INTERFACE_TYPES:
            violations.extend(_executable_interface_violations(interface, interface_base))
        elif interface_type in CONTRACT_INTERFACE_TYPES:
            violations.extend(_contract_interface_violations(interface, interface_base))
    return violations


def _executable_interface_violations(interface, base):
    violations = []
    if not _non_empty(interface.get("prototype")):
        violations.append(RuleViolation(f"{base}.prototype", "prototype must be non-empty"))
    diagram = interface.get("execution_flow_diagram")
    if not isinstance(diagram, dict) or not _non_empty(diagram.get("source")):
        violations.append(
            RuleViolation(
                f"{base}.execution_flow_diagram.source",
                "execution_flow_diagram.source must be non-empty",
            )
        )
    if not _non_empty(interface.get("side_effects")):
        violations.append(RuleViolation(f"{base}.side_effects", "side_effects must contain at least one item"))
    if not _non_empty(interface.get("error_behavior")):
        violations.append(RuleViolation(f"{base}.error_behavior", "error_behavior must contain at least one item"))
    return violations


def _contract_interface_violations(interface, base):
    violations = []
    contract = interface.get("contract")
    if not isinstance(contract, dict):
        return [RuleViolation(f"{base}.contract", "contract must be present")]
    if "required_fields" in contract:
        violations.append(RuleViolation(f"{base}.contract.required_fields", "contract.required_fields is not allowed"))
    if not _non_empty(contract.get("required_items")):
        violations.append(
            RuleViolation(
                f"{base}.contract.required_items",
                "contract.required_items must contain at least one item",
            )
        )
    if not _non_empty(contract.get("consumers")):
        violations.append(RuleViolation(f"{base}.contract.consumers", "contract.consumers must contain at least one item"))
    if "constraints" in contract and not _non_empty(contract.get("constraints")):
        violations.append(
            RuleViolation(
                f"{base}.contract.constraints",
                "contract.constraints must contain at least one item when present",
            )
        )
    return violations


def _internal_mechanism_violations(module, base, anchor_targets):
    violations = []
    mechanism = module.get("internal_mechanism", {})
    index_rows = as_rows(mechanism.get("mechanism_index", {}))
    details = mechanism.get("mechanism_details", [])
    if not isinstance(details, list):
        details = []
    index_ids = [row.get("mechanism_id") for row in index_rows]
    detail_ids = [detail.get("mechanism_id") for detail in details if isinstance(detail, dict)]

    for duplicate in _duplicate_values(index_ids):
        violations.append(RuleViolation(f"{base}.internal_mechanism.mechanism_index.rows", f"duplicate mechanism_id {duplicate}"))
    for duplicate in _duplicate_values(detail_ids):
        violations.append(RuleViolation(f"{base}.internal_mechanism.mechanism_details", f"duplicate mechanism_id {duplicate}"))
    if set(index_ids) != set(detail_ids) or len(index_ids) != len(detail_ids):
        violations.append(
            RuleViolation(
                f"{base}.internal_mechanism",
                "mechanism_index rows and mechanism_details must have matching mechanism_id sets",
            )
        )

    for row_index, row in enumerate(index_rows):
        row_base = f"{base}.internal_mechanism.mechanism_index.rows[{row_index}]"
        related_anchors = row.get("related_anchors")
        if not isinstance(related_anchors, list) or not related_anchors:
            violations.append(RuleViolation(f"{row_base}.related_anchors", "related_anchors must contain at least one anchor"))
            continue
        for anchor_index, anchor in enumerate(related_anchors):
            violations.extend(_related_anchor_violations(anchor, f"{row_base}.related_anchors[{anchor_index}]", anchor_targets))

    for detail_index, detail in enumerate(details):
        detail_base = f"{base}.internal_mechanism.mechanism_details[{detail_index}]"
        blocks = detail.get("blocks", []) if isinstance(detail, dict) else []
        if not any(isinstance(block, dict) and block.get("block_type") == "text" and _non_empty(block.get("text")) for block in blocks):
            violations.append(
                RuleViolation(
                    f"{detail_base}.blocks",
                    "mechanism detail must include at least one non-empty text block",
                )
            )
    return violations


def _related_anchor_violations(anchor, base, anchor_targets):
    if not isinstance(anchor, dict):
        return []
    violations = []
    anchor_type = anchor.get("anchor_type")
    if anchor_type == "other" and not has_reason(anchor.get("reason")):
        violations.append(RuleViolation(f"{base}.reason", "reason is required when anchor_type is other"))
    if anchor_type == "file_path":
        return violations
    if anchor_type not in ANCHOR_TYPE_VALUES or anchor_type == "other":
        return violations
    valid_values = anchor_targets.get(anchor_type, set())
    if anchor.get("value") not in valid_values:
        violations.append(RuleViolation(f"{base}.value", "related_anchors value must resolve"))
    return violations


def _runtime_anchor_violations(document):
    return []


def _runtime_unit_violations(document):
    violations = []
    rows = document.get("runtime_view", {}).get("runtime_units", {}).get("rows", [])
    if not isinstance(rows, list):
        return violations
    for row_index, unit in enumerate(rows):
        if not isinstance(unit, dict):
            continue
        base = f"$.runtime_view.runtime_units.rows[{row_index}]"
        entrypoint = unit.get("entrypoint")
        if entrypoint == "不适用" and not _non_empty(unit.get("notes")):
            violations.append(RuleViolation(f"{base}.notes", "entrypoint 不适用 requires non-empty notes"))
        if isinstance(entrypoint, str) and entrypoint.startswith("不适用："):
            violations.append(
                RuleViolation(
                    f"{base}.entrypoint",
                    "entrypoint must be exactly 不适用 without inline reason",
                )
            )
    return violations + _runtime_anchor_violations(document)
