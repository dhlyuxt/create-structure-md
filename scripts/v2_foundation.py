from dataclasses import dataclass


V2_DSL_VERSION = "0.2.0"
V2_VERSION_ERROR = "V1 DSL is not supported by the V2 renderer; migrate the input to dsl_version 0.2.0."
EVIDENCE_MODES = ("hidden", "inline")

MODULE_KIND_VALUES = (
    "documentation_contract",
    "schema_contract",
    "validator",
    "renderer",
    "installer",
    "test_suite",
    "library",
    "other",
)
VALUE_SOURCE_VALUES = (
    "default",
    "cli_argument",
    "environment",
    "constant",
    "config_file",
    "computed",
    "inferred",
    "unknown",
)
DEPENDENCY_TYPE_VALUES = (
    "runtime",
    "library",
    "tool",
    "schema_contract",
    "documentation_contract",
    "dsl_contract",
    "internal_module",
    "data_object",
    "filesystem",
    "external_service",
    "test_fixture",
    "other",
)
USAGE_RELATION_VALUES = (
    "reads",
    "writes",
    "validates_against",
    "renders",
    "invokes",
    "imports",
    "tests",
    "produces",
    "consumes",
    "uses",
    "other",
)
INTERFACE_TYPE_VALUES = (
    "command_line",
    "function",
    "method",
    "library_api",
    "schema_contract",
    "dsl_contract",
    "document_contract",
    "configuration_contract",
    "data_contract",
    "test_fixture",
    "workflow",
    "other",
)
ANCHOR_TYPE_VALUES = (
    "file_path",
    "module_id",
    "interface_id",
    "data_id",
    "dependency_id",
    "parameter_id",
    "diagram_id",
    "table_id",
    "source_snippet_id",
    "evidence_id",
    "traceability_id",
    "other",
)
EXECUTABLE_INTERFACE_TYPES = ("command_line", "function", "method", "library_api", "workflow")

GLOBAL_ENUM_BY_FIELD = {
    "module_kind": MODULE_KIND_VALUES,
    "value_source": VALUE_SOURCE_VALUES,
    "dependency_type": DEPENDENCY_TYPE_VALUES,
    "usage_relation": USAGE_RELATION_VALUES,
    "interface_type": INTERFACE_TYPE_VALUES,
    "anchor_type": ANCHOR_TYPE_VALUES,
}
OTHER_REASON_BY_FIELD = {
    "module_kind": "module_kind_reason",
    "interface_type": "interface_type_reason",
    "anchor_type": "reason",
}
V2_TYPED_ID_FIELDS = ("parameter_id", "data_id", "dependency_id", "limitation_id")
SUPPORT_ID_COLLECTIONS = (
    ("evidence", "evidence"),
    ("traceability", "traceability"),
    ("risk", "risks"),
    ("assumption", "assumptions"),
    ("source_snippet", "source_snippets"),
)


@dataclass(frozen=True)
class RuleViolation:
    path: str
    message: str


@dataclass(frozen=True)
class GateRule:
    name: str
    section_path_template: str


NOT_APPLICABLE_GATES = (
    GateRule(
        "module_configuration_parameters",
        "$.module_design.modules[{module_index}].configuration.parameters",
    ),
    GateRule("module_dependencies", "$.module_design.modules[{module_index}].dependencies"),
    GateRule("module_data_objects", "$.module_design.modules[{module_index}].data_objects"),
    GateRule("public_interfaces", "$.module_design.modules[{module_index}].public_interfaces"),
    GateRule(
        "executable_interface_parameters",
        "$.module_design.modules[{module_index}].public_interfaces.interfaces[{interface_index}].parameters",
    ),
    GateRule(
        "executable_interface_return_values",
        "$.module_design.modules[{module_index}].public_interfaces.interfaces[{interface_index}].return_values",
    ),
    GateRule("internal_mechanism", "$.module_design.modules[{module_index}].internal_mechanism"),
    GateRule("known_limitations", "$.module_design.modules[{module_index}].known_limitations"),
    GateRule("chapter_9_structure_issues", "$.structure_issues_and_suggestions"),
)
GATE_BY_NAME = {gate.name: gate for gate in NOT_APPLICABLE_GATES}


def require_v2_dsl_version(document):
    if not isinstance(document, dict) or document.get("dsl_version") != V2_DSL_VERSION:
        raise ValueError(V2_VERSION_ERROR)


def has_gated_content(value):
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, list):
        return len(value) > 0
    if isinstance(value, dict):
        return any(has_gated_content(child) for child in value.values())
    return True


def has_reason(value):
    return isinstance(value, str) and bool(value.strip())


def not_applicable_gate_violations(section_path, content_values, not_applicable_reason, stable_id=""):
    has_content = any(has_gated_content(value) for value in content_values)
    has_not_applicable_reason = has_reason(not_applicable_reason)
    stable_text = f" ({stable_id})" if stable_id else ""
    if has_content and has_not_applicable_reason:
        return [
            RuleViolation(
                section_path,
                f"{section_path}{stable_text} cannot provide both content and not_applicable_reason",
            )
        ]
    if not has_content and not has_not_applicable_reason:
        return [
            RuleViolation(
                section_path,
                f"{section_path}{stable_text} must provide not_applicable_reason when content is absent",
            )
        ]
    return []


def interface_location_violations(base_path, location, *, line_one_supported=False):
    violations = []
    if not isinstance(location, dict):
        return [RuleViolation(base_path, f"{base_path} must be an object")]

    file_path = location.get("file_path")
    if not isinstance(file_path, str) or not file_path.strip():
        violations.append(RuleViolation(base_path, f"{base_path}.file_path must be a non-empty string"))

    has_line_start = "line_start" in location
    has_line_end = "line_end" in location
    if has_line_start != has_line_end:
        violations.append(RuleViolation(base_path, f"{base_path} line_start and line_end must be paired"))
        return violations
    if not has_line_start:
        return violations

    line_start = location.get("line_start")
    line_end = location.get("line_end")
    if line_start is None and line_end is None:
        return violations
    if line_start is None or line_end is None:
        violations.append(RuleViolation(base_path, f"{base_path} line_start and line_end must both be non-null when either line value is present"))
        return violations
    if type(line_start) is not int or type(line_end) is not int:
        violations.append(RuleViolation(base_path, f"{base_path} line_start and line_end must be integers"))
        return violations
    if line_start < 1 or line_end < 1:
        violations.append(RuleViolation(base_path, f"{base_path} line_start and line_end must be >= 1"))
    if line_end < line_start:
        violations.append(RuleViolation(base_path, f"{base_path} line_end must be >= line_start"))
    if line_start == 1 and line_end == 1 and not line_one_supported:
        violations.append(RuleViolation(base_path, f"{base_path} line 1-1 is a placeholder location"))
    return violations


def walk(value, path="$"):
    yield path, value
    if isinstance(value, dict):
        for key, child in value.items():
            yield from walk(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from walk(child, f"{path}[{index}]")


def as_rows(section):
    if isinstance(section, dict) and isinstance(section.get("rows"), list):
        return section["rows"]
    return []


def add_gate_result(violations, name, path, content_values, reason, stable_id=""):
    for violation in not_applicable_gate_violations(path, content_values, reason, stable_id=stable_id):
        violations.append(RuleViolation(violation.path, f"{name}: {violation.message}"))


def _format_gate_path(name, **kwargs):
    return GATE_BY_NAME[name].section_path_template.format(**kwargs)


def _first_stable_id(rows, *fields):
    for row in rows:
        if not isinstance(row, dict):
            continue
        for field in fields:
            value = row.get(field)
            if isinstance(value, str) and value:
                return value
    return ""


def not_applicable_mapping_violations(document):
    violations = []
    if not isinstance(document, dict):
        return violations

    modules = document.get("module_design", {}).get("modules", [])
    if isinstance(modules, list):
        for module_index, module in enumerate(modules):
            if not isinstance(module, dict):
                continue

            configuration = module.get("configuration")
            if isinstance(configuration, dict) and "parameters" in configuration:
                parameters = configuration.get("parameters")
                if isinstance(parameters, dict):
                    rows = as_rows(parameters)
                    add_gate_result(
                        violations,
                        "module_configuration_parameters",
                        _format_gate_path("module_configuration_parameters", module_index=module_index),
                        [rows],
                        parameters.get("not_applicable_reason"),
                        _first_stable_id(rows, "parameter_id"),
                    )

            dependencies = module.get("dependencies")
            if isinstance(dependencies, dict):
                rows = as_rows(dependencies)
                add_gate_result(
                    violations,
                    "module_dependencies",
                    _format_gate_path("module_dependencies", module_index=module_index),
                    [rows],
                    dependencies.get("not_applicable_reason"),
                    _first_stable_id(rows, "dependency_id"),
                )

            data_objects = module.get("data_objects")
            if isinstance(data_objects, dict):
                rows = as_rows(data_objects)
                add_gate_result(
                    violations,
                    "module_data_objects",
                    _format_gate_path("module_data_objects", module_index=module_index),
                    [rows],
                    data_objects.get("not_applicable_reason"),
                    _first_stable_id(rows, "data_id"),
                )

            public_interfaces = module.get("public_interfaces")
            if isinstance(public_interfaces, dict):
                interface_index = public_interfaces.get("interface_index")
                index_rows = as_rows(interface_index)
                interfaces = public_interfaces.get("interfaces") if isinstance(public_interfaces.get("interfaces"), list) else []
                add_gate_result(
                    violations,
                    "public_interfaces",
                    _format_gate_path("public_interfaces", module_index=module_index),
                    [index_rows, interfaces],
                    public_interfaces.get("not_applicable_reason"),
                    _first_stable_id(index_rows, "interface_id"),
                )

                for interface_index_value, interface in enumerate(interfaces):
                    if not isinstance(interface, dict):
                        continue
                    interface_type = interface.get("interface_type")
                    is_executable = interface_type in EXECUTABLE_INTERFACE_TYPES
                    parameters = interface.get("parameters")
                    if is_executable or "parameters" in interface:
                        if isinstance(parameters, dict):
                            rows = as_rows(parameters)
                            add_gate_result(
                                violations,
                                "executable_interface_parameters",
                                _format_gate_path(
                                    "executable_interface_parameters",
                                    module_index=module_index,
                                    interface_index=interface_index_value,
                                ),
                                [rows],
                                parameters.get("not_applicable_reason"),
                                _first_stable_id(rows, "parameter_id"),
                            )
                        elif is_executable:
                            add_gate_result(
                                violations,
                                "executable_interface_parameters",
                                _format_gate_path(
                                    "executable_interface_parameters",
                                    module_index=module_index,
                                    interface_index=interface_index_value,
                                ),
                                [],
                                None,
                                interface.get("interface_id", ""),
                            )
                    return_values = interface.get("return_values")
                    if is_executable or "return_values" in interface:
                        if isinstance(return_values, dict):
                            rows = as_rows(return_values)
                            add_gate_result(
                                violations,
                                "executable_interface_return_values",
                                _format_gate_path(
                                    "executable_interface_return_values",
                                    module_index=module_index,
                                    interface_index=interface_index_value,
                                ),
                                [rows],
                                return_values.get("not_applicable_reason"),
                                interface.get("interface_id", ""),
                            )
                        elif is_executable:
                            add_gate_result(
                                violations,
                                "executable_interface_return_values",
                                _format_gate_path(
                                    "executable_interface_return_values",
                                    module_index=module_index,
                                    interface_index=interface_index_value,
                                ),
                                [],
                                None,
                                interface.get("interface_id", ""),
                            )

            internal_mechanism = module.get("internal_mechanism")
            if isinstance(internal_mechanism, dict):
                mechanism_index = internal_mechanism.get("mechanism_index")
                add_gate_result(
                    violations,
                    "internal_mechanism",
                    _format_gate_path("internal_mechanism", module_index=module_index),
                    [
                        internal_mechanism.get("summary"),
                        as_rows(mechanism_index),
                        internal_mechanism.get("mechanism_details", []),
                    ],
                    internal_mechanism.get("not_applicable_reason"),
                )

            known_limitations = module.get("known_limitations")
            if isinstance(known_limitations, dict):
                rows = as_rows(known_limitations)
                add_gate_result(
                    violations,
                    "known_limitations",
                    _format_gate_path("known_limitations", module_index=module_index),
                    [rows],
                    known_limitations.get("not_applicable_reason"),
                    _first_stable_id(rows, "limitation_id"),
                )

    structure_issues = document.get("structure_issues_and_suggestions")
    if isinstance(structure_issues, dict):
        add_gate_result(
            violations,
            "chapter_9_structure_issues",
            _format_gate_path("chapter_9_structure_issues"),
            [structure_issues.get("summary"), structure_issues.get("blocks", [])],
            structure_issues.get("not_applicable_reason"),
        )

    return violations


def invalid_reason_field_violations(document):
    violations = []
    modules = document.get("module_design", {}).get("modules", []) if isinstance(document, dict) else []
    if not isinstance(modules, list):
        return violations
    for module_index, module in enumerate(modules):
        if not isinstance(module, dict):
            continue
        for section_name in ("source_scope", "configuration"):
            section = module.get(section_name)
            if isinstance(section, dict) and "not_applicable_reason" in section:
                path = f"$.module_design.modules[{module_index}].{section_name}.not_applicable_reason"
                violations.append(RuleViolation(path, f"{path} is not a supported not_applicable_reason field"))
    return violations


def enum_and_other_reason_violations(document):
    violations = []
    for path, value in walk(document):
        if not isinstance(value, dict):
            continue
        for field, allowed in GLOBAL_ENUM_BY_FIELD.items():
            if field not in value:
                continue
            field_value = value.get(field)
            field_path = f"{path}.{field}"
            if field_value not in allowed:
                violations.append(
                    RuleViolation(field_path, f"{field_path} must be one of {', '.join(allowed)}")
                )
            reason_field = OTHER_REASON_BY_FIELD.get(field)
            if field_value == "other" and reason_field and not has_reason(value.get(reason_field)):
                violations.append(
                    RuleViolation(
                        f"{path}.{reason_field}",
                        f"{path}.{reason_field} is required when {field} is other",
                    )
                )
    return violations


def location_scan_violations(document):
    violations = []
    for path, value in walk(document):
        if path.endswith(".location"):
            violations.extend(interface_location_violations(path, value))
    return violations


def interface_id_scope_violations(document):
    violations = []
    modules = document.get("module_design", {}).get("modules", []) if isinstance(document, dict) else []
    if not isinstance(modules, list):
        return violations

    owner_by_interface_id = {}
    for module_index, module in enumerate(modules):
        if not isinstance(module, dict):
            continue
        module_id = module.get("module_id", f"module[{module_index}]")
        public_interfaces = module.get("public_interfaces", {})
        if not isinstance(public_interfaces, dict):
            continue

        index_seen = set()
        logical_ids = []
        logical_seen = set()
        interface_index = public_interfaces.get("interface_index")
        for row_index, row in enumerate(as_rows(interface_index)):
            if not isinstance(row, dict):
                continue
            interface_id = row.get("interface_id")
            if not isinstance(interface_id, str) or not interface_id:
                continue
            path = (
                "$.module_design.modules"
                f"[{module_index}].public_interfaces.interface_index.rows[{row_index}].interface_id"
            )
            if interface_id in index_seen:
                violations.append(
                    RuleViolation(path, f"duplicate interface_id in interface_index: {interface_id}")
                )
            index_seen.add(interface_id)
            if interface_id not in logical_seen:
                logical_ids.append(interface_id)
                logical_seen.add(interface_id)

        detail_seen = set()
        interfaces = public_interfaces.get("interfaces")
        if not isinstance(interfaces, list):
            interfaces = []
        for detail_index, interface in enumerate(interfaces):
            if not isinstance(interface, dict):
                continue
            interface_id = interface.get("interface_id")
            if not isinstance(interface_id, str) or not interface_id:
                continue
            path = (
                "$.module_design.modules"
                f"[{module_index}].public_interfaces.interfaces[{detail_index}].interface_id"
            )
            if interface_id in detail_seen:
                violations.append(
                    RuleViolation(path, f"duplicate interface_id in interface details: {interface_id}")
                )
            detail_seen.add(interface_id)
            if interface_id not in logical_seen:
                logical_ids.append(interface_id)
                logical_seen.add(interface_id)

        for interface_id in logical_ids:
            owner_index = owner_by_interface_id.get(interface_id)
            if owner_index is not None and owner_index != module_index:
                violations.append(
                    RuleViolation(
                        f"$.module_design.modules[{module_index}].public_interfaces",
                        f"interface_id {interface_id} is already defined under module index {owner_index}; reused by module {module_id}",
                    )
                )
            else:
                owner_by_interface_id[interface_id] = module_index
    return violations


def module_id_scope_violations(document):
    violations = []
    if not isinstance(document, dict):
        return violations

    intro_seen = {}
    intro_rows = as_rows(document.get("architecture_views", {}).get("module_intro"))
    for row_index, row in enumerate(intro_rows):
        if not isinstance(row, dict):
            continue
        module_id = row.get("module_id")
        if not isinstance(module_id, str) or not module_id:
            continue
        path = f"$.architecture_views.module_intro.rows[{row_index}].module_id"
        previous_path = intro_seen.get(module_id)
        if previous_path:
            violations.append(RuleViolation(path, f"duplicate module_id {module_id}; first seen at {previous_path}"))
        else:
            intro_seen[module_id] = path

    design_seen = {}
    modules = document.get("module_design", {}).get("modules", [])
    if not isinstance(modules, list):
        return violations
    for module_index, module in enumerate(modules):
        if not isinstance(module, dict):
            continue
        module_id = module.get("module_id")
        if not isinstance(module_id, str) or not module_id:
            continue
        path = f"$.module_design.modules[{module_index}].module_id"
        previous_path = design_seen.get(module_id)
        if previous_path:
            violations.append(RuleViolation(path, f"duplicate module_id {module_id}; first seen at {previous_path}"))
        else:
            design_seen[module_id] = path
    return violations


def id_scope_violations(document):
    violations = []
    seen_by_field = {field: {} for field in V2_TYPED_ID_FIELDS}
    for path, value in walk(document):
        if not isinstance(value, dict):
            continue
        for field in V2_TYPED_ID_FIELDS:
            field_value = value.get(field)
            if not isinstance(field_value, str) or not field_value:
                continue
            field_path = f"{path}.{field}"
            previous_path = seen_by_field[field].get(field_value)
            if previous_path:
                violations.append(
                    RuleViolation(field_path, f"duplicate {field} {field_value}; first seen at {previous_path}")
                )
            else:
                seen_by_field[field][field_value] = field_path

    for path, value in walk(document):
        if not path.endswith(".blocks") or not isinstance(value, list):
            continue
        seen_block_ids = {}
        for index, block in enumerate(value):
            if not isinstance(block, dict):
                continue
            block_id = block.get("block_id")
            if not isinstance(block_id, str) or not block_id:
                continue
            field_path = f"{path}[{index}].block_id"
            previous_path = seen_block_ids.get(block_id)
            if previous_path:
                violations.append(
                    RuleViolation(field_path, f"duplicate block_id {block_id}; first seen at {previous_path}")
                )
            else:
                seen_block_ids[block_id] = field_path
    return violations


def _path_leaf(path):
    return path.rsplit(".", 1)[-1]


def _is_diagram_object(path, value):
    leaf = _path_leaf(path)
    return (
        isinstance(value, dict)
        and isinstance(value.get("id"), str)
        and value.get("id") != ""
        and (leaf == "diagram" or leaf.endswith("_diagram") or leaf.startswith("diagrams[") or "diagram_type" in value)
    )


def _is_table_object(path, value):
    leaf = _path_leaf(path)
    return (
        isinstance(value, dict)
        and isinstance(value.get("id"), str)
        and value.get("id") != ""
        and (leaf == "table" or leaf.endswith("_table") or leaf.startswith("tables["))
    )


def diagram_table_id_scope_violations(document):
    violations = []
    seen_diagrams = {}
    seen_tables = {}
    for path, value in walk(document):
        if _is_diagram_object(path, value):
            diagram_id = value["id"]
            id_path = f"{path}.id"
            previous_path = seen_diagrams.get(diagram_id)
            if previous_path:
                violations.append(RuleViolation(id_path, f"duplicate diagram.id {diagram_id}; first seen at {previous_path}"))
            else:
                seen_diagrams[diagram_id] = id_path
        if _is_table_object(path, value):
            table_id = value["id"]
            id_path = f"{path}.id"
            previous_path = seen_tables.get(table_id)
            if previous_path:
                violations.append(RuleViolation(id_path, f"duplicate table.id {table_id}; first seen at {previous_path}"))
            else:
                seen_tables[table_id] = id_path
    return violations


def support_id_scope_violations(document):
    violations = []
    if not isinstance(document, dict):
        return violations

    seen_support_ids = {}
    for kind, collection_name in SUPPORT_ID_COLLECTIONS:
        collection = document.get(collection_name, [])
        if not isinstance(collection, list):
            continue
        for index, item in enumerate(collection):
            if not isinstance(item, dict):
                continue
            support_id = item.get("id")
            if not isinstance(support_id, str) or not support_id:
                continue
            path = f"$.{collection_name}[{index}].id"
            previous = seen_support_ids.get(support_id)
            if previous:
                previous_kind, previous_path = previous
                violations.append(
                    RuleViolation(
                        path,
                        f"duplicate support ID {support_id}; first seen as {previous_kind} at {previous_path}",
                    )
                )
            else:
                seen_support_ids[support_id] = (kind, path)
    return violations


def dependency_prefix_violations(document):
    violations = []
    if not isinstance(document, dict):
        return violations

    system_rows = as_rows(document.get("configuration_data_dependencies", {}).get("dependencies"))
    for row_index, row in enumerate(system_rows):
        if not isinstance(row, dict):
            continue
        dependency_id = row.get("dependency_id")
        if isinstance(dependency_id, str) and not dependency_id.startswith("SYSDEP-"):
            path = f"$.configuration_data_dependencies.dependencies.rows[{row_index}].dependency_id"
            violations.append(RuleViolation(path, f"{path} must start with SYSDEP-"))

    modules = document.get("module_design", {}).get("modules", [])
    if not isinstance(modules, list):
        return violations
    for module_index, module in enumerate(modules):
        if not isinstance(module, dict):
            continue
        for row_index, row in enumerate(as_rows(module.get("dependencies"))):
            if not isinstance(row, dict):
                continue
            dependency_id = row.get("dependency_id")
            if isinstance(dependency_id, str) and not dependency_id.startswith("MDEP-"):
                path = f"$.module_design.modules[{module_index}].dependencies.rows[{row_index}].dependency_id"
                violations.append(RuleViolation(path, f"{path} must start with MDEP-"))
    return violations


def v2_global_rule_violations(document):
    violations = []
    violations.extend(not_applicable_mapping_violations(document))
    violations.extend(invalid_reason_field_violations(document))
    violations.extend(enum_and_other_reason_violations(document))
    violations.extend(location_scan_violations(document))
    violations.extend(interface_id_scope_violations(document))
    violations.extend(module_id_scope_violations(document))
    violations.extend(id_scope_violations(document))
    violations.extend(diagram_table_id_scope_violations(document))
    violations.extend(support_id_scope_violations(document))
    violations.extend(dependency_prefix_violations(document))
    return violations
