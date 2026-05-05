#!/usr/bin/env python3
from dataclasses import dataclass
from pathlib import Path
import json
import re


@dataclass(frozen=True)
class ExpectedDiagram:
    json_path: str
    diagram_id: str
    title: str
    source: str
    owning_section_path: str
    should_render: bool = True
    skip_reason: str = ""


class Phase4GateError(Exception):
    pass


SAFE_DIAGRAM_ID_RE = re.compile(r"^(?!.*--)[A-Za-z0-9_.:-]+$")
DIAGRAM_ID_COMMENT_RE = re.compile(r"^<!-- diagram-id: ((?!.*--)[A-Za-z0-9_.:-]+) -->$")
MERMAID_OPENING_FENCE_RE = re.compile(r"^ {0,3}```mermaid[ \t]*$")
FENCE_OPENING_RE = re.compile(r"^ {0,3}(```+|~~~+)[ \t]*(.*?)[ \t]*$")
FENCE_CLOSING_RE = re.compile(r"^ {0,3}(```+|~~~+)[ \t]*$")
EXECUTABLE_INTERFACE_TYPES = {"command_line", "function", "method", "library_api", "workflow"}


def json_path(*parts):
    path = "$"
    for part in parts:
        if isinstance(part, int):
            path += f"[{part}]"
        else:
            path += f".{part}"
    return path


def _diagram_record(diagram, path, owner_path, should_render=True, skip_reason=""):
    if not isinstance(diagram, dict):
        return None
    return ExpectedDiagram(
        json_path=path,
        diagram_id=str(diagram.get("id", "")),
        title=str(diagram.get("title", "")),
        source=str(diagram.get("source", "")),
        owning_section_path=owner_path,
        should_render=should_render,
        skip_reason=skip_reason,
    )


def has_gated_content(value):
    if isinstance(value, dict):
        return any(
            has_gated_content(child)
            for key, child in value.items()
            if key != "not_applicable_reason"
        )
    if isinstance(value, list):
        return any(has_gated_content(item) for item in value)
    if isinstance(value, str):
        return bool(value.strip())
    return bool(value)


def explicit_not_applicable_skip_reason(section):
    if not isinstance(section, dict):
        return ""
    reason = section.get("not_applicable_reason", "")
    reason = str(reason).strip() if reason is not None else ""
    if not reason:
        return ""
    if has_gated_content({key: value for key, value in section.items() if key != "not_applicable_reason"}):
        return ""
    return reason


def _append_diagram(records, diagram, path, owner_path, owner_section=None):
    skip_reason = explicit_not_applicable_skip_reason(owner_section)
    record = _diagram_record(
        diagram,
        path,
        owner_path,
        should_render=not bool(skip_reason),
        skip_reason=skip_reason,
    )
    if record is not None:
        records.append(record)


def _append_diagram_array(records, diagrams, path, owner_path, owner_section=None):
    if not isinstance(diagrams, list):
        return
    for index, diagram in enumerate(diagrams):
        _append_diagram(
            records,
            diagram,
            f"{path}[{index}]",
            owner_path,
            owner_section=owner_section,
        )


def _object(value):
    return value if isinstance(value, dict) else {}


def _list(value):
    return value if isinstance(value, list) else []


def _collect_architecture(records, document):
    section = _object(document.get("architecture_views"))
    owner_path = json_path("architecture_views")
    _append_diagram(
        records,
        section.get("module_relationship_diagram"),
        json_path("architecture_views", "module_relationship_diagram"),
        owner_path,
        owner_section=section,
    )
    _append_diagram_array(
        records,
        section.get("extra_diagrams"),
        json_path("architecture_views", "extra_diagrams"),
        owner_path,
        owner_section=section,
    )


def _collect_module_design(records, document):
    module_design = _object(document.get("module_design"))
    for module_index, module in enumerate(_list(module_design.get("modules"))):
        if not isinstance(module, dict):
            continue

        public_interfaces = _object(module.get("public_interfaces"))
        public_interfaces_path = json_path("module_design", "modules", module_index, "public_interfaces")
        interfaces_path = json_path("module_design", "modules", module_index, "public_interfaces", "interfaces")
        for interface_index, interface in enumerate(_list(public_interfaces.get("interfaces"))):
            if not isinstance(interface, dict):
                continue
            if interface.get("interface_type") not in EXECUTABLE_INTERFACE_TYPES:
                continue
            interface_path = f"{interfaces_path}[{interface_index}]"
            _append_diagram(
                records,
                interface.get("execution_flow_diagram"),
                f"{interface_path}.execution_flow_diagram",
                public_interfaces_path,
                owner_section=public_interfaces,
            )

        internal_mechanism = _object(module.get("internal_mechanism"))
        internal_mechanism_path = json_path("module_design", "modules", module_index, "internal_mechanism")
        details_path = json_path("module_design", "modules", module_index, "internal_mechanism", "mechanism_details")
        for detail_index, detail in enumerate(_list(internal_mechanism.get("mechanism_details"))):
            if not isinstance(detail, dict):
                continue
            blocks_path = f"{details_path}[{detail_index}].blocks"
            for block_index, block in enumerate(_list(detail.get("blocks"))):
                if not isinstance(block, dict) or block.get("block_type") != "diagram":
                    continue
                block_path = f"{blocks_path}[{block_index}]"
                _append_diagram(
                    records,
                    block.get("diagram"),
                    f"{block_path}.diagram",
                    internal_mechanism_path,
                    owner_section=internal_mechanism,
                )


def _collect_runtime(records, document):
    section = _object(document.get("runtime_view"))
    owner_path = json_path("runtime_view")
    _append_diagram(
        records,
        section.get("runtime_flow_diagram"),
        json_path("runtime_view", "runtime_flow_diagram"),
        owner_path,
        owner_section=section,
    )
    _append_diagram(
        records,
        section.get("runtime_sequence_diagram"),
        json_path("runtime_view", "runtime_sequence_diagram"),
        owner_path,
        owner_section=section,
    )
    _append_diagram_array(
        records,
        section.get("extra_diagrams"),
        json_path("runtime_view", "extra_diagrams"),
        owner_path,
        owner_section=section,
    )


def _collect_configuration(records, document):
    section = _object(document.get("configuration_data_dependencies"))
    owner_path = json_path("configuration_data_dependencies")
    _append_diagram_array(
        records,
        section.get("extra_diagrams"),
        json_path("configuration_data_dependencies", "extra_diagrams"),
        owner_path,
        owner_section=section,
    )


def _collect_collaboration(records, document):
    section = _object(document.get("cross_module_collaboration"))
    owner_path = json_path("cross_module_collaboration")
    _append_diagram(
        records,
        section.get("collaboration_relationship_diagram"),
        json_path("cross_module_collaboration", "collaboration_relationship_diagram"),
        owner_path,
        owner_section=section,
    )
    _append_diagram_array(
        records,
        section.get("extra_diagrams"),
        json_path("cross_module_collaboration", "extra_diagrams"),
        owner_path,
        owner_section=section,
    )


def _collect_key_flows(records, document):
    section = _object(document.get("key_flows"))
    flows_path = json_path("key_flows", "flows")
    for flow_index, flow in enumerate(_list(section.get("flows"))):
        if not isinstance(flow, dict):
            continue
        flow_path = f"{flows_path}[{flow_index}]"
        _append_diagram(
            records,
            flow.get("diagram"),
            f"{flow_path}.diagram",
            flow_path,
            owner_section=flow,
        )
    _append_diagram_array(
        records,
        section.get("extra_diagrams"),
        json_path("key_flows", "extra_diagrams"),
        json_path("key_flows"),
        owner_section=section,
    )


def _collect_structure_issues(records, document):
    section = _object(document.get("structure_issues_and_suggestions"))
    owner_path = json_path("structure_issues_and_suggestions")
    blocks_path = json_path("structure_issues_and_suggestions", "blocks")
    for block_index, block in enumerate(_list(section.get("blocks"))):
        if not isinstance(block, dict) or block.get("block_type") != "diagram":
            continue
        block_path = f"{blocks_path}[{block_index}]"
        _append_diagram(
            records,
            block.get("diagram"),
            f"{block_path}.diagram",
            owner_path,
            owner_section=section,
        )


def collect_expected_diagrams(document):
    if not isinstance(document, dict):
        return []
    records = []
    _collect_architecture(records, document)
    _collect_module_design(records, document)
    _collect_runtime(records, document)
    _collect_configuration(records, document)
    _collect_collaboration(records, document)
    _collect_key_flows(records, document)
    _collect_structure_issues(records, document)
    return records
