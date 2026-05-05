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
DIAGRAM_ID_COMMENT_RE = re.compile(r"^<!-- diagram-id: ((?![A-Za-z0-9_.:-]*--)[A-Za-z0-9_.:-]+) -->$")
MERMAID_OPENING_FENCE_RE = re.compile(r"^ {0,3}```mermaid[ \t]*$")
FENCE_OPENING_RE = re.compile(r"^ {0,3}(```+|~~~+)[ \t]*(.*?)[ \t]*$")
FENCE_CLOSING_RE = re.compile(r"^ {0,3}(```+|~~~+)[ \t]*$")
EXECUTABLE_INTERFACE_TYPES = {"command_line", "function", "method", "library_api", "workflow"}
REVIEW_REQUIRED_KEYS = {
    "artifact_schema_version",
    "reviewer",
    "source_dsl",
    "checked_diagram_ids",
    "accepted_diagram_ids",
    "revised_diagram_ids",
    "split_diagram_ids",
    "skipped_diagrams",
    "remaining_readability_risks",
}


def load_json_file(path, label="JSON file"):
    path = Path(path)
    if not path.exists():
        raise Phase4GateError(f"{label} does not exist: {path}")
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise Phase4GateError(f"{label} could not be read: {path}: {exc}") from exc
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise Phase4GateError(f"{label} is malformed JSON: {path}: {exc}") from exc


def normalize_path(value, base_dir=None):
    path = Path(value).expanduser()
    if base_dir is not None and not path.is_absolute():
        path = Path(base_dir).expanduser() / path
    return str(path.resolve(strict=False))


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
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, list):
        return len(value) > 0
    if isinstance(value, dict):
        return any(
            has_gated_content(child)
            for key, child in value.items()
            if key != "not_applicable_reason"
        )
    return True


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


def extract_rendered_mermaid_metadata(markdown_text):
    lines = markdown_text.splitlines()
    records = []
    mermaid_fence_count = 0
    in_fence = False
    opening_marker = ""
    for index, line in enumerate(lines):
        if not in_fence:
            opening = FENCE_OPENING_RE.match(line)
            if not opening:
                continue
            in_fence = True
            opening_marker = opening.group(1)
            info = opening.group(2).split(None, 1)[0].lower() if opening.group(2) else ""
            if info == "mermaid":
                mermaid_fence_count += 1
                previous_line = lines[index - 1] if index > 0 else ""
                match = DIAGRAM_ID_COMMENT_RE.match(previous_line)
                records.append(
                    {
                        "diagram_id": match.group(1) if match else "",
                        "line": index + 1,
                        "has_adjacent_metadata": match is not None,
                    }
                )
            continue
        closing = FENCE_CLOSING_RE.match(line)
        if (
            closing
            and closing.group(1)[0] == opening_marker[0]
            and len(closing.group(1)) >= len(opening_marker)
        ):
            in_fence = False
            opening_marker = ""
    return records, mermaid_fence_count


def rendered_diagram_completeness_errors(document, markdown_text):
    errors = []
    expected_records = [
        record for record in collect_expected_diagrams(document) if record.should_render
    ]
    expected_ids = [record.diagram_id for record in expected_records if record.diagram_id]
    duplicate_expected_ids = _duplicate_values(expected_ids)
    if duplicate_expected_ids:
        errors.append("duplicate expected diagram IDs: " + ", ".join(duplicate_expected_ids))

    expected_by_id = {record.diagram_id: record for record in expected_records}
    rendered_records, mermaid_fence_count = extract_rendered_mermaid_metadata(markdown_text)

    if mermaid_fence_count < len(expected_records):
        errors.append(
            f"rendered Mermaid fence count {mermaid_fence_count} is less than expected diagram count "
            f"{len(expected_records)}"
        )

    rendered_counts = {}
    for record in rendered_records:
        if not record["has_adjacent_metadata"]:
            errors.append(f"Mermaid fence at line {record['line']} is missing adjacent diagram-id metadata")
            continue
        rendered_counts[record["diagram_id"]] = rendered_counts.get(record["diagram_id"], 0) + 1

    for diagram_id, expected in expected_by_id.items():
        count = rendered_counts.get(diagram_id, 0)
        if count == 0:
            errors.append(f"missing rendered diagram {diagram_id} at {expected.json_path}: {expected.title}")
        elif count != 1:
            errors.append(f"rendered diagram {diagram_id} appears {count} times; expected exactly once")

    unexpected = sorted(set(rendered_counts) - set(expected_by_id))
    if unexpected:
        errors.append("rendered Markdown contains unexpected diagram IDs: " + ", ".join(unexpected))
    return errors


def _duplicate_values(values):
    seen = set()
    duplicates = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    return sorted(duplicates)


def _require_string_list(artifact, key, errors):
    values = artifact.get(key)
    if not isinstance(values, list) or not all(
        isinstance(value, str) and value.strip() for value in values
    ):
        errors.append(f"{key} must be a list of non-empty strings")
        return set()

    normalized_values = [value.strip() for value in values]
    duplicate_ids = _duplicate_values(normalized_values)
    if duplicate_ids:
        errors.append(f"{key} contains duplicate diagram IDs: {', '.join(duplicate_ids)}")
    return set(normalized_values)


def _split_ids_are_derived_from_checked(split_ids, checked_ids, errors):
    unresolved_ids = set()
    empty_suffix_ids = []
    for split_id in split_ids:
        if split_id in checked_ids:
            continue

        derived_from_checked_id = False
        for checked_id in sorted(checked_ids, key=lambda value: (-len(value), value)):
            prefix = f"{checked_id}::"
            if not split_id.startswith(prefix):
                continue
            derived_from_checked_id = True
            if not split_id.removeprefix(prefix).strip():
                empty_suffix_ids.append(split_id)
            break

        if derived_from_checked_id:
            continue

        unresolved_ids.add(split_id)
    if empty_suffix_ids:
        errors.append(
            "split_diagram_ids must use a non-empty derived suffix: "
            + ", ".join(sorted(empty_suffix_ids))
        )
    return unresolved_ids


def validate_mermaid_review_artifact(document, source_dsl_path, artifact, artifact_base_dir=None):
    if artifact is None:
        return ["readability review artifact is missing"]
    if not isinstance(artifact, dict):
        return ["readability review artifact must be a JSON object"]

    errors = []
    missing_keys = sorted(REVIEW_REQUIRED_KEYS - set(artifact))
    if missing_keys:
        return [f"readability review artifact missing keys: {', '.join(missing_keys)}"]

    if artifact.get("artifact_schema_version") != "1.0":
        errors.append("artifact_schema_version must be 1.0")

    reviewer = artifact.get("reviewer")
    if not isinstance(reviewer, str) or not reviewer.strip():
        errors.append("reviewer must be a non-empty string")

    source_dsl = artifact.get("source_dsl")
    if not isinstance(source_dsl, str) or not source_dsl.strip():
        errors.append("source_dsl must be a non-empty string")
    elif normalize_path(source_dsl, artifact_base_dir) != normalize_path(source_dsl_path):
        errors.append("source_dsl does not match the DSL input used for expected diagram collection")

    records = collect_expected_diagrams(document)
    expected_diagram_ids = [record.diagram_id for record in records if record.diagram_id]
    duplicate_expected_ids = _duplicate_values(expected_diagram_ids)
    if duplicate_expected_ids:
        errors.append("duplicate expected diagram IDs: " + ", ".join(duplicate_expected_ids))

    records_by_id = {record.diagram_id: record for record in records if record.diagram_id}
    all_expected_ids = set(records_by_id)
    rendered_ids = {
        diagram_id
        for diagram_id, record in records_by_id.items()
        if record.should_render
    }
    skippable_ids = all_expected_ids - rendered_ids

    checked_ids = _require_string_list(artifact, "checked_diagram_ids", errors)
    accepted_ids = _require_string_list(artifact, "accepted_diagram_ids", errors)
    revised_ids = _require_string_list(artifact, "revised_diagram_ids", errors)
    split_ids = _require_string_list(artifact, "split_diagram_ids", errors)

    skipped_ids = set()
    skipped_id_values = []
    skipped_diagrams = artifact.get("skipped_diagrams")
    if not isinstance(skipped_diagrams, list):
        errors.append("skipped_diagrams must be a list")
    else:
        for skipped_diagram in skipped_diagrams:
            if not isinstance(skipped_diagram, dict):
                errors.append("skipped diagram must be an object")
                continue
            diagram_id = skipped_diagram.get("diagram_id")
            if not isinstance(diagram_id, str) or not diagram_id.strip():
                errors.append("skipped diagram must provide diagram_id")
                continue
            diagram_id = diagram_id.strip()
            skipped_id_values.append(diagram_id)
            skipped_ids.add(diagram_id)

            reason = skipped_diagram.get("reason")
            if not isinstance(reason, str) or not reason.strip():
                errors.append(f"skipped diagram must provide reason: {diagram_id}")
        duplicate_skipped_ids = _duplicate_values(skipped_id_values)
        if duplicate_skipped_ids:
            errors.append(
                "skipped_diagrams contains duplicate diagram IDs: "
                + ", ".join(duplicate_skipped_ids)
            )

    covered_ids = checked_ids | skipped_ids
    missing_coverage_ids = all_expected_ids - covered_ids
    if missing_coverage_ids:
        errors.append(
            "readability review artifact does not cover expected diagrams: "
            + ", ".join(sorted(missing_coverage_ids))
        )

    unknown_checked_ids = checked_ids - all_expected_ids
    if unknown_checked_ids:
        errors.append("checked_diagram_ids contains unknown diagram IDs: " + ", ".join(sorted(unknown_checked_ids)))

    unknown_skipped_ids = skipped_ids - all_expected_ids
    if unknown_skipped_ids:
        errors.append("skipped_diagrams contains unknown diagram IDs: " + ", ".join(sorted(unknown_skipped_ids)))

    rendered_skipped_ids = skipped_ids & rendered_ids
    if rendered_skipped_ids:
        errors.append(
            "skipped_diagrams contains diagram IDs that cannot be skipped because their owning section is applicable: "
            + ", ".join(sorted(rendered_skipped_ids))
        )

    skipped_without_reason_ids = {
        diagram_id
        for diagram_id in skipped_ids & skippable_ids
        if not records_by_id[diagram_id].skip_reason
    }
    if skipped_without_reason_ids:
        errors.append(
            "skipped_diagrams contains IDs without an explicitly not-applicable owning section: "
            + ", ".join(sorted(skipped_without_reason_ids))
        )

    unresolved_review_ids = (accepted_ids | revised_ids) - checked_ids
    unresolved_review_ids |= _split_ids_are_derived_from_checked(split_ids, checked_ids, errors)
    if unresolved_review_ids:
        errors.append(
            "accepted/revised/split IDs must refer to checked diagrams: "
            + ", ".join(sorted(unresolved_review_ids))
        )

    if not isinstance(artifact.get("remaining_readability_risks"), list):
        errors.append("remaining_readability_risks must be a list")

    return errors
