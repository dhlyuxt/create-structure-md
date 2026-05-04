#!/usr/bin/env python3
import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

try:
    from v2_foundation import (
        V2_VERSION_ERROR,
        require_v2_dsl_version,
        v2_global_rule_violations,
    )
except ModuleNotFoundError:
    from scripts.v2_foundation import (
        V2_VERSION_ERROR,
        require_v2_dsl_version,
        v2_global_rule_violations,
    )


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas/structure-design.schema.json"

GENERIC_OUTPUT_NAMES = {
    "structure_design.md",
    "structure-design.md",
    "structuredesign.md",
    "design.md",
    "软件结构设计说明书.md",
}

GENERIC_OUTPUT_TOKENS = {
    "software",
    "structure",
    "design",
    "document",
    "doc",
    "system",
    "module",
    "软件",
    "结构",
    "设计",
    "说明书",
}

RESERVED_EXTRA_TABLE_COLUMN_KEYS = {
    "evidence_refs",
    "traceability_refs",
    "source_snippet_refs",
    "confidence",
}

DOCUMENT_REQUIRED_TEXT_FIELDS = [
    "title",
    "project_name",
    "document_version",
    "status",
    "language",
    "source_type",
    "output_file",
]

ISO8601_LOCAL_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:[+-]\d{2}:\d{2}|Z)?$"
)

HIGH_RISK_SNIPPET_PATTERNS = [
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"(?i)(password|passwd|secret|token|api[_-]?key)\s*[:=]\s*['\"]?[^'\"\s]+"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |)?PRIVATE KEY-----"),
    re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    re.compile(r"\b1[3-9]\d{9}\b"),
]

MARKDOWN_UNSAFE_PATTERNS = [
    re.compile(r"(?m)^\s{0,3}#{1,6}\s+"),
    re.compile(r"(?m)^\s*\|.+\|\s*$"),
    re.compile(r"```"),
    re.compile(r"(?s)<!--.*?-->"),
    re.compile(r"(?is)</?[A-Za-z][A-Za-z0-9:-]*(?:\s+[^<>]*)?>"),
    re.compile(r"(?m)^\s*(?:graph|flowchart|sequenceDiagram|classDiagram|stateDiagram-v2)\b"),
]

PROTOTYPE_PATTERNS = [
    re.compile(r"(?m)^\s*(?:(?:static|extern|inline|const|unsigned|signed|long|short)\s+)*(?:void|char|int|float|double|bool|size_t|ssize_t|[A-Za-z_]\w+_t|struct\s+[A-Za-z_]\w+|enum\s+[A-Za-z_]\w+)\s+\*?\s*[A-Za-z_]\w*\s*\([^;{}]*\)\s*;?\s*$"),
    re.compile(r"(?m)^\s*def\s+[A-Za-z_]\w*\s*\("),
    re.compile(r"(?m)^\s*class\s+[A-Za-z_]\w*(?:\(|:|\s*$)"),
    re.compile(r"(?m)^\s*typedef\s+(?:struct|enum)\b"),
    re.compile(r"(?m)^\s*enum\s*\{"),
    re.compile(r"(?m)^\s*class\s*\{"),
]

CODE_LIKE_LINE_RE = re.compile(
    r"^\s*(?:if |else:|elif |for |while |try:|except |return\b|raise\b|[A-Za-z_]\w*\(.*\)|[A-Za-z_]\w*\s*=|[{};])"
)

LOW_CONFIDENCE_COLLECTIONS = [
    ("$.architecture_views.module_intro.rows", lambda doc: doc["architecture_views"]["module_intro"]["rows"]),
    ("$.module_design.modules", lambda doc: doc["module_design"]["modules"]),
    (
        "$.module_design.modules[{module_index}].external_capability_details.provided_capabilities.rows",
        lambda doc: [
            (module_index, row_index, row)
            for module_index, module in enumerate(doc["module_design"]["modules"])
            for row_index, row in enumerate(module["external_capability_details"]["provided_capabilities"]["rows"])
        ],
    ),
    ("$.runtime_view.runtime_units.rows", lambda doc: doc["runtime_view"]["runtime_units"]["rows"]),
    ("$.configuration_data_dependencies.configuration_items.rows", lambda doc: doc["configuration_data_dependencies"]["configuration_items"]["rows"]),
    ("$.configuration_data_dependencies.structural_data_artifacts.rows", lambda doc: doc["configuration_data_dependencies"]["structural_data_artifacts"]["rows"]),
    ("$.configuration_data_dependencies.dependencies.rows", lambda doc: doc["configuration_data_dependencies"]["dependencies"]["rows"]),
    ("$.cross_module_collaboration.collaboration_scenarios.rows", lambda doc: doc["cross_module_collaboration"]["collaboration_scenarios"]["rows"]),
    ("$.key_flows.flows", lambda doc: doc["key_flows"]["flows"]),
]


@dataclass(frozen=True)
class ValidationIssue:
    level: str
    path: str
    message: str
    hint: str = ""

    def format(self):
        suffix = f" Hint: {self.hint}" if self.hint else ""
        return f"{self.level}: {self.path}: {self.message}.{suffix}"


@dataclass
class ValidationReport:
    errors: list[ValidationIssue] = field(default_factory=list)
    warnings: list[ValidationIssue] = field(default_factory=list)

    def error(self, path, message, hint=""):
        self.errors.append(ValidationIssue("ERROR", path, message, hint))

    def warn(self, path, message, hint=""):
        self.warnings.append(ValidationIssue("WARNING", path, message, hint))


def build_parser():
    parser = argparse.ArgumentParser(description="Validate create-structure-md DSL JSON.")
    parser.add_argument("dsl_file", help="Path to structure DSL JSON.")
    parser.add_argument(
        "--allow-long-snippets",
        action="store_true",
        help="Warn instead of fail for source snippets longer than 50 lines.",
    )
    return parser


def json_path(parts):
    path = "$"
    for part in parts:
        if isinstance(part, int):
            path += f"[{part}]"
        else:
            path += f".{part}"
    return path


def load_json_file(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ValueError(f"file not found: {path}")
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}")


def load_schema():
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def schema_errors(document):
    validator = Draft202012Validator(load_schema())
    return sorted(validator.iter_errors(document), key=lambda error: list(error.path))


def format_schema_error(error):
    return ValidationIssue(
        "ERROR",
        json_path(error.path),
        f"schema validation failed: {error.message}",
        "Fix the DSL shape before semantic validation runs",
    )


PREFIX_BY_KIND = {
    "module": "MOD-",
    "core_capability": "CAP-",
    "provided_capability": "CAP-",
    "runtime_unit": "RUN-",
    "configuration_item": "CFG-",
    "data_artifact": "DATA-",
    "collaboration": "COL-",
    "flow": "FLOW-",
    "flow_step": "STEP-",
    "flow_branch": "BR-",
    "diagram": "MER-",
    "extra_table": "TBL-",
    "evidence": "EV-",
    "traceability": "TR-",
    "risk": "RISK-",
    "assumption": "ASM-",
    "source_snippet": "SNIP-",
}

DEPENDENCY_ID_PREFIXES = ("SYSDEP-", "MDEP-")
ID_KINDS = tuple(PREFIX_BY_KIND) + ("dependency",)

SUPPORT_REF_FIELDS = {
    "evidence_refs": "evidence",
    "traceability_refs": "traceability",
    "source_snippet_refs": "source_snippet",
}

REGISTERED_REFERENCE_PATHS = [
    re.compile(r"^\$\.architecture_views\.module_intro\.rows\[\d+\]\.module_id$"),
    re.compile(r"^\$\.system_overview\.core_capabilities\[\d+\]\.capability_id$"),
    re.compile(r"^\$\.module_design\.modules\[\d+\]\.module_id$"),
    re.compile(r"^\$\.module_design\.modules\[\d+\]\.external_capability_details\.provided_capabilities\.rows\[\d+\]\.capability_id$"),
    re.compile(r"^\$\.runtime_view\.runtime_units\.rows\[\d+\]\.(unit_id|related_module_ids)$"),
    re.compile(r"^\$\.configuration_data_dependencies\.configuration_items\.rows\[\d+\]\.config_id$"),
    re.compile(r"^\$\.configuration_data_dependencies\.structural_data_artifacts\.rows\[\d+\]\.artifact_id$"),
    re.compile(r"^\$\.configuration_data_dependencies\.dependencies\.rows\[\d+\]\.dependency_id$"),
    re.compile(r"^\$\.cross_module_collaboration\.collaboration_scenarios\.rows\[\d+\]\.(collaboration_id|initiator_module_id|participant_module_ids)$"),
    re.compile(r"^\$\.key_flows\.flow_index\.rows\[\d+\]\.(flow_id|participant_module_ids|participant_runtime_unit_ids)$"),
    re.compile(r"^\$\.key_flows\.flows\[\d+\]\.(flow_id|related_module_ids|related_runtime_unit_ids)$"),
    re.compile(r"^\$\.key_flows\.flows\[\d+\]\.steps\[\d+\]\.(step_id|related_module_ids|related_runtime_unit_ids)$"),
    re.compile(r"^\$\.key_flows\.flows\[\d+\]\.branches_or_exceptions\[\d+\]\.(branch_id|related_module_ids|related_runtime_unit_ids)$"),
    # traceability.target_id resolution depends on target_type and is deferred to Task 6.
    re.compile(r"^\$\.traceability\[\d+\]\.(id|source_external_id|target_id)$"),
    re.compile(r"^\$\.(evidence|risks|assumptions|source_snippets)\[\d+\]\.id$"),
    re.compile(r"^\$.*\.(?:extra_tables\[\d+\]|extra_diagrams\[\d+\]|.*diagram)\.id$"),
]

REFERENCE_FIELD_RULES = [
    (re.compile(r"^\$\.module_design\.modules\[\d+\]\.module_id$"), "module", False, "module"),
    (re.compile(r"^\$\.runtime_view\.runtime_units\.rows\[\d+\]\.related_module_ids$"), "module", True, "module"),
    (re.compile(r"^\$\.cross_module_collaboration\.collaboration_scenarios\.rows\[\d+\]\.initiator_module_id$"), "module", False, "module"),
    (re.compile(r"^\$\.cross_module_collaboration\.collaboration_scenarios\.rows\[\d+\]\.participant_module_ids$"), "module", True, "module"),
    (re.compile(r"^\$\.key_flows\.flow_index\.rows\[\d+\]\.participant_module_ids$"), "module", True, "module"),
    (re.compile(r"^\$\.key_flows\.flow_index\.rows\[\d+\]\.participant_runtime_unit_ids$"), "runtime_unit", True, "runtime unit"),
    (re.compile(r"^\$\.key_flows\.flows\[\d+\]\.related_module_ids$"), "module", True, "module"),
    (re.compile(r"^\$\.key_flows\.flows\[\d+\]\.related_runtime_unit_ids$"), "runtime_unit", True, "runtime unit"),
    (re.compile(r"^\$\.key_flows\.flows\[\d+\]\.steps\[\d+\]\.related_module_ids$"), "module", True, "module"),
    (re.compile(r"^\$\.key_flows\.flows\[\d+\]\.steps\[\d+\]\.related_runtime_unit_ids$"), "runtime_unit", True, "runtime unit"),
    (re.compile(r"^\$\.key_flows\.flows\[\d+\]\.branches_or_exceptions\[\d+\]\.related_module_ids$"), "module", True, "module"),
    (re.compile(r"^\$\.key_flows\.flows\[\d+\]\.branches_or_exceptions\[\d+\]\.related_runtime_unit_ids$"), "runtime_unit", True, "runtime unit"),
]

TRACEABILITY_TARGET_KIND = {
    "module": "module",
    "core_capability": "core_capability",
    "provided_capability": "provided_capability",
    "runtime_unit": "runtime_unit",
    "flow": "flow",
    "flow_step": "flow_step",
    "flow_branch": "flow_branch",
    "collaboration": "collaboration",
    "configuration_item": "configuration_item",
    "data_artifact": "data_artifact",
    "dependency": "dependency",
    "risk": "risk",
    "assumption": "assumption",
    "source_snippet": "source_snippet",
}


def is_registered_reference_field(path, field_name):
    if field_name in SUPPORT_REF_FIELDS:
        return True
    return any(pattern.match(path) for pattern in REGISTERED_REFERENCE_PATHS)


def walk(value, path="$"):
    yield path, value
    if isinstance(value, dict):
        for key, child in value.items():
            yield from walk(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from walk(child, f"{path}[{index}]")


def is_diagram_object(value):
    return isinstance(value, dict) and {"id", "kind", "diagram_type", "source"}.issubset(value)


def is_extra_table_object(value):
    return isinstance(value, dict) and {"id", "title", "columns", "rows"}.issubset(value)


def is_diagram_registration_path(path):
    return (
        path.endswith("_diagram")
        or path.endswith(".diagram")
        or ".extra_diagrams[" in path
    ) and ".rows[" not in path


def is_extra_table_registration_path(path):
    return ".extra_tables[" in path and ".rows[" not in path


class ValidationContext:
    def __init__(self, document, report):
        self.document = document
        self.report = report
        self.ids_by_kind = {kind: {} for kind in ID_KINDS}
        self.id_owner = {}
        self.flow_index_ids = []
        self.flow_index_paths = {}
        self.traceability_targets = {}

    def build(self):
        self._register_all_ids()
        self._check_registered_references()
        self._check_support_refs(self.document)
        self._check_unregistered_id_fields(self.document)

    def register(self, kind, value, path):
        if kind == "dependency":
            if not isinstance(value, str) or not value.startswith(DEPENDENCY_ID_PREFIXES):
                self.report.error(path, "dependency ID must start with SYSDEP- or MDEP-", "Use SYSDEP- for Chapter 6 system dependencies and MDEP- for module dependencies")
                return
        else:
            prefix = PREFIX_BY_KIND[kind]
            if not isinstance(value, str) or not value.startswith(prefix):
                self.report.error(path, f"ID must start with {prefix}", "Use the documented prefix; numeric suffixes are optional")
                return
        if value in self.id_owner:
            first_kind, first_path = self.id_owner[value]
            self.report.error(path, f"duplicate ID {value}; duplicate_id={value}", f"First defined as {first_kind} at {first_path}")
            return
        self.ids_by_kind[kind][value] = path
        self.id_owner[value] = (kind, path)

    def require_ref(self, kind, value, path, label=None):
        if value not in self.ids_by_kind[kind]:
            name = label or kind.replace("_", " ")
            self.report.error(path, f"references unknown {name} ID {value}", "Define the target ID or correct the reference")

    def register_flow_index_id(self, value, path):
        prefix = PREFIX_BY_KIND["flow"]
        if not isinstance(value, str) or not value.startswith(prefix):
            self.report.error(path, f"ID must start with {prefix}", "Use the documented prefix; numeric suffixes are optional")
            return
        if value in self.flow_index_paths:
            self.report.error(path, f"duplicate flow index ID {value}", f"First defined at {self.flow_index_paths[value]}")
            return
        self.flow_index_ids.append(value)
        self.flow_index_paths[value] = path

    def _register_all_ids(self):
        doc = self.document
        for i, row in enumerate(doc["architecture_views"]["module_intro"]["rows"]):
            self.register("module", row["module_id"], f"$.architecture_views.module_intro.rows[{i}].module_id")
        for i, item in enumerate(doc["system_overview"]["core_capabilities"]):
            self.register("core_capability", item["capability_id"], f"$.system_overview.core_capabilities[{i}].capability_id")
        for m_i, module in enumerate(doc["module_design"]["modules"]):
            for c_i, row in enumerate(module["external_capability_details"]["provided_capabilities"]["rows"]):
                self.register("provided_capability", row["capability_id"], f"$.module_design.modules[{m_i}].external_capability_details.provided_capabilities.rows[{c_i}].capability_id")
        for i, row in enumerate(doc["runtime_view"]["runtime_units"]["rows"]):
            self.register("runtime_unit", row["unit_id"], f"$.runtime_view.runtime_units.rows[{i}].unit_id")
        for i, row in enumerate(doc["configuration_data_dependencies"]["configuration_items"]["rows"]):
            self.register("configuration_item", row["config_id"], f"$.configuration_data_dependencies.configuration_items.rows[{i}].config_id")
        for i, row in enumerate(doc["configuration_data_dependencies"]["structural_data_artifacts"]["rows"]):
            self.register("data_artifact", row["artifact_id"], f"$.configuration_data_dependencies.structural_data_artifacts.rows[{i}].artifact_id")
        for i, row in enumerate(doc["configuration_data_dependencies"]["dependencies"]["rows"]):
            self.register("dependency", row["dependency_id"], f"$.configuration_data_dependencies.dependencies.rows[{i}].dependency_id")
        for i, row in enumerate(doc["cross_module_collaboration"]["collaboration_scenarios"]["rows"]):
            self.register("collaboration", row["collaboration_id"], f"$.cross_module_collaboration.collaboration_scenarios.rows[{i}].collaboration_id")
        for i, row in enumerate(doc["key_flows"]["flow_index"]["rows"]):
            self.register_flow_index_id(row["flow_id"], f"$.key_flows.flow_index.rows[{i}].flow_id")
        for f_i, flow in enumerate(doc["key_flows"]["flows"]):
            self.register("flow", flow["flow_id"], f"$.key_flows.flows[{f_i}].flow_id")
            for s_i, step in enumerate(flow["steps"]):
                self.register("flow_step", step["step_id"], f"$.key_flows.flows[{f_i}].steps[{s_i}].step_id")
            for b_i, branch in enumerate(flow["branches_or_exceptions"]):
                self.register("flow_branch", branch["branch_id"], f"$.key_flows.flows[{f_i}].branches_or_exceptions[{b_i}].branch_id")
        for kind, collection_name in [("evidence", "evidence"), ("traceability", "traceability"), ("risk", "risks"), ("assumption", "assumptions"), ("source_snippet", "source_snippets")]:
            for i, item in enumerate(doc[collection_name]):
                self.register(kind, item["id"], f"$.{collection_name}[{i}].id")
        for path, value in walk(doc):
            if is_diagram_object(value) and is_diagram_registration_path(path):
                self.register("diagram", value["id"], f"{path}.id")
            elif is_extra_table_object(value) and is_extra_table_registration_path(path):
                self.register("extra_table", value["id"], f"{path}.id")

    def _check_registered_references(self):
        for path, value in walk(self.document):
            for pattern, target_kind, is_list, label in REFERENCE_FIELD_RULES:
                if not pattern.match(path):
                    continue
                if is_list:
                    for i, ref in enumerate(value):
                        self.require_ref(target_kind, ref, f"{path}[{i}]", label)
                else:
                    self.require_ref(target_kind, value, path, label)
                break

    def _check_support_refs(self, value, path="$"):
        if isinstance(value, dict):
            for field_name, target_kind in SUPPORT_REF_FIELDS.items():
                refs = value.get(field_name)
                if isinstance(refs, list):
                    for i, ref in enumerate(refs):
                        self.require_ref(target_kind, ref, f"{path}.{field_name}[{i}]", target_kind.replace("_", " "))
            for key, child in value.items():
                self._check_support_refs(child, f"{path}.{key}")
        elif isinstance(value, list):
            for i, child in enumerate(value):
                self._check_support_refs(child, f"{path}[{i}]")

    def _check_unregistered_id_fields(self, value, path="$"):
        if isinstance(value, dict):
            for key, child in value.items():
                child_path = f"{path}.{key}"
                if (key.endswith("_id") or key.endswith("_ids")) and not is_registered_reference_field(child_path, key):
                    self.report.error(f"{path}.{key}", "unregistered reference-like field", "Add the field to the schema and validator registry before using it")
                self._check_unregistered_id_fields(child, child_path)
        elif isinstance(value, list):
            for i, child in enumerate(value):
                self._check_unregistered_id_fields(child, f"{path}[{i}]")


def is_blank(value):
    return not isinstance(value, str) or value.strip() == ""


def normalized_name_tokens(value):
    normalized = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]+", " ", value.casefold())
    return [token for token in normalized.split() if token]


def documented_object_tokens(document):
    doc = document["document"]
    tokens = set(normalized_name_tokens(doc.get("project_name", "")))
    for row in document["architecture_views"]["module_intro"]["rows"]:
        tokens.update(normalized_name_tokens(row["module_id"]))
        tokens.update(normalized_name_tokens(row["module_name"]))
    for module in document["module_design"]["modules"]:
        tokens.update(normalized_name_tokens(module["module_id"]))
        tokens.update(normalized_name_tokens(module["name"]))
    return {token for token in tokens if token not in GENERIC_OUTPUT_TOKENS and len(token) >= 2}


def validate_document_fields(document, report):
    doc = document.get("document", {})
    for field_name in DOCUMENT_REQUIRED_TEXT_FIELDS:
        if is_blank(doc.get(field_name)):
            report.error(
                f"$.document.{field_name}",
                "must be non-empty",
                "Revise the DSL content instead of fabricating filler",
            )

    output_file = doc.get("output_file", "")
    folded = output_file.casefold()
    output_tokens = normalized_name_tokens(Path(output_file).stem)
    concrete_tokens = documented_object_tokens(document)
    contains_concrete_token = any(token in output_tokens for token in concrete_tokens)
    generic_only = bool(output_tokens) and all(token in GENERIC_OUTPUT_TOKENS for token in output_tokens)
    if folded in GENERIC_OUTPUT_NAMES or generic_only:
        report.error(
            "$.document.output_file",
            "generic-only output filename is not allowed",
            "Use a concrete module, subsystem, system, package, or tool name",
        )
    elif not contains_concrete_token:
        report.error(
            "$.document.output_file",
            "must include a concrete documented object name",
            "Use document.project_name, a module ID, a module name, or another documented object name",
        )
    if " " in output_file:
        report.warn(
            "$.document.output_file",
            "contains spaces",
            "Normalize spaces to '_' before writing the final DSL when possible",
        )

    generated_at = doc.get("generated_at", "")
    if generated_at and not ISO8601_LOCAL_RE.match(generated_at):
        report.warn(
            "$.document.generated_at",
            "should use ISO-8601 local datetime with timezone when available",
            "Example: 2026-05-02T10:30:00+08:00",
        )


def check_chapter_rules(document, context):
    check_chapter_2(document, context)
    check_chapter_3(document, context)
    check_chapter_4(document, context)
    check_chapter_5(document, context)
    check_chapter_6(document, context)
    check_chapter_7(document, context)
    check_chapter_8(document, context)
    check_chapter_9(document, context)
    check_all_extra_diagrams(document, context)


def require_non_empty(report, path, value, label):
    if is_blank(value):
        report.error(path, f"{label} must be non-empty", "Revise the structured design content")


def require_non_empty_list(report, path, value, label):
    if not isinstance(value, list) or len(value) == 0:
        report.error(path, f"{label} must contain at least one item", "Provide real content or use the documented empty representation only when allowed")


def diagram_source_required(report, path, diagram, label):
    if is_blank(diagram.get("source", "")):
        report.error(f"{path}.source", f"{label} source must be non-empty", "Mermaid syntax is checked by validate_mermaid.py; this validator only requires content")


def check_chapter_2(document, context):
    overview = document["system_overview"]
    require_non_empty(context.report, "$.system_overview.summary", overview["summary"], "chapter 2 summary")
    require_non_empty(context.report, "$.system_overview.purpose", overview["purpose"], "chapter 2 purpose")
    for i, capability in enumerate(overview["core_capabilities"]):
        base = f"$.system_overview.core_capabilities[{i}]"
        require_non_empty(context.report, f"{base}.capability_id", capability["capability_id"], "core capability ID")
        require_non_empty(context.report, f"{base}.name", capability["name"], "core capability name")
        require_non_empty(context.report, f"{base}.description", capability["description"], "core capability description")


def check_chapter_3(document, context):
    arch = document["architecture_views"]
    require_non_empty(context.report, "$.architecture_views.summary", arch["summary"], "chapter 3 summary")
    rows = arch["module_intro"]["rows"]
    if not rows:
        context.report.error("$.architecture_views.module_intro.rows", "must contain at least one module", "Chapter 3 defines canonical module IDs")
    diagram_source_required(context.report, "$.architecture_views.module_relationship_diagram", arch["module_relationship_diagram"], "module relationship diagram")
    source = arch["module_relationship_diagram"].get("source", "")
    for i, row in enumerate(rows):
        base = f"$.architecture_views.module_intro.rows[{i}]"
        for field_name in ["module_id", "module_name", "responsibility"]:
            require_non_empty(context.report, f"{base}.{field_name}", row[field_name], field_name)
        if row["module_id"] not in source and row["module_name"] not in source:
            context.report.warn(f"{base}.module_id", f"module relationship diagram does not mention module {row['module_id']} or {row['module_name']}", "Mention the module ID or name in the diagram source")


def check_chapter_4(document, context):
    module_ids = [row["module_id"] for row in document["architecture_views"]["module_intro"]["rows"]]
    design_modules = document["module_design"]["modules"]
    design_ids = [item["module_id"] for item in design_modules]
    require_non_empty(context.report, "$.module_design.summary", document["module_design"]["summary"], "chapter 4 summary")
    if sorted(module_ids) != sorted(design_ids) or len(module_ids) != len(design_ids):
        context.report.error("$.module_design.modules", "must match chapter 3 modules one-to-one", "Create exactly one module design entry for each chapter 3 module")
    for i, module in enumerate(design_modules):
        base = f"$.module_design.modules[{i}]"
        context.require_ref("module", module["module_id"], f"{base}.module_id", "module")
        require_non_empty_list(context.report, f"{base}.responsibilities", module["responsibilities"], "module responsibilities")
        require_non_empty(context.report, f"{base}.external_capability_summary.description", module["external_capability_summary"]["description"], "external capability summary description")
        rows = module["external_capability_details"]["provided_capabilities"]["rows"]
        require_non_empty_list(context.report, f"{base}.external_capability_details.provided_capabilities.rows", rows, "provided capability rows")
        internal = module["internal_structure"]
        if is_blank(internal["diagram"].get("source", "")) and is_blank(internal["textual_structure"]):
            context.report.error(f"{base}.internal_structure", "requires diagram source or textual_structure", "not_applicable_reason alone does not satisfy the internal structure rule")


def check_chapter_5(document, context):
    runtime = document["runtime_view"]
    require_non_empty(context.report, "$.runtime_view.summary", runtime["summary"], "chapter 5 summary")
    units = runtime["runtime_units"]["rows"]
    require_non_empty_list(context.report, "$.runtime_view.runtime_units.rows", units, "runtime units")
    for i, unit in enumerate(units):
        base = f"$.runtime_view.runtime_units.rows[{i}]"
        for ref_i, module_id in enumerate(unit["related_module_ids"]):
            context.require_ref("module", module_id, f"{base}.related_module_ids[{ref_i}]", "module")
        if is_blank(unit["entrypoint"]):
            require_non_empty(context.report, f"{base}.entrypoint_not_applicable_reason", unit["entrypoint_not_applicable_reason"], "entrypoint_not_applicable_reason")
        if not unit["related_module_ids"]:
            require_non_empty(context.report, f"{base}.external_environment_reason", unit["external_environment_reason"], "external_environment_reason")
    diagram_source_required(context.report, "$.runtime_view.runtime_flow_diagram", runtime["runtime_flow_diagram"], "runtime flow diagram")
    sequence = runtime.get("runtime_sequence_diagram")
    if sequence and not is_blank(sequence.get("source", "")) and not sequence["source"].lstrip().startswith("sequenceDiagram"):
        context.report.error("$.runtime_view.runtime_sequence_diagram.source", "must use sequenceDiagram", "Mermaid syntax remains the responsibility of validate_mermaid.py")


def check_chapter_6(document, context):
    for table_name, id_field, required_fields in [
        ("configuration_items", "config_id", ["config_id", "config_name", "purpose"]),
        ("structural_data_artifacts", "artifact_id", ["artifact_id", "artifact_name", "artifact_type", "owner"]),
        ("dependencies", "dependency_id", ["dependency_id", "dependency_name", "dependency_type", "purpose"]),
    ]:
        for i, row in enumerate(document["configuration_data_dependencies"][table_name]["rows"]):
            base = f"$.configuration_data_dependencies.{table_name}.rows[{i}]"
            for field_name in required_fields:
                require_non_empty(context.report, f"{base}.{field_name}", row[field_name], field_name)


def check_chapter_7(document, context):
    collaboration = document["cross_module_collaboration"]
    module_count = len(document["architecture_views"]["module_intro"]["rows"])
    is_multi_module = module_count > 1
    rows = collaboration["collaboration_scenarios"]["rows"]
    diagram = collaboration.get("collaboration_relationship_diagram")

    if is_multi_module:
        require_non_empty(context.report, "$.cross_module_collaboration.summary", collaboration["summary"], "chapter 7 summary")
        require_non_empty_list(context.report, "$.cross_module_collaboration.collaboration_scenarios.rows", rows, "collaboration scenarios")
        if not isinstance(diagram, dict):
            context.report.error(
                "$.cross_module_collaboration.collaboration_relationship_diagram",
                "collaboration relationship diagram must be present for multi-module documents",
                "Show how the documented modules collaborate",
            )
        else:
            diagram_source_required(context.report, "$.cross_module_collaboration.collaboration_relationship_diagram", diagram, "collaboration relationship diagram")

    for i, row in enumerate(rows):
        base = f"$.cross_module_collaboration.collaboration_scenarios.rows[{i}]"
        context.require_ref("module", row["initiator_module_id"], f"{base}.initiator_module_id", "module")
        for ref_i, module_id in enumerate(row["participant_module_ids"]):
            context.require_ref("module", module_id, f"{base}.participant_module_ids[{ref_i}]", "module")
        if is_multi_module:
            involved_module_ids = {row["initiator_module_id"], *row["participant_module_ids"]}
            if len(involved_module_ids) < 2:
                context.report.error(
                    base,
                    "collaboration scenario must involve at least two distinct modules",
                    "Use chapter 7 for cross-module collaboration, or keep it empty for a single-module document",
                )


def check_chapter_8(document, context):
    key_flows = document["key_flows"]
    require_non_empty(context.report, "$.key_flows.summary", key_flows["summary"], "chapter 8 summary")

    flow_index_rows = key_flows["flow_index"]["rows"]
    flows = key_flows["flows"]
    require_non_empty_list(context.report, "$.key_flows.flow_index.rows", flow_index_rows, "flow index rows")

    index_ids = [row["flow_id"] for row in flow_index_rows]
    detail_ids = [flow["flow_id"] for flow in flows]
    if sorted(index_ids) != sorted(detail_ids) or len(index_ids) != len(detail_ids):
        context.report.error(
            "$.key_flows",
            "flow_index rows and flow details must match one-to-one",
            "Create exactly one flow detail for each flow_index row using the same flow_id",
        )

    for i, row in enumerate(flow_index_rows):
        base = f"$.key_flows.flow_index.rows[{i}]"
        participant_module_ids = row["participant_module_ids"]
        participant_runtime_unit_ids = row["participant_runtime_unit_ids"]
        if not participant_module_ids and not participant_runtime_unit_ids:
            context.report.error(
                base,
                "flow index row must have at least one participant",
                "Add a participant_module_ids or participant_runtime_unit_ids reference",
            )
        for ref_i, module_id in enumerate(participant_module_ids):
            context.require_ref("module", module_id, f"{base}.participant_module_ids[{ref_i}]", "module")
        for ref_i, runtime_unit_id in enumerate(participant_runtime_unit_ids):
            context.require_ref("runtime_unit", runtime_unit_id, f"{base}.participant_runtime_unit_ids[{ref_i}]", "runtime unit")

    for f_i, flow in enumerate(flows):
        base = f"$.key_flows.flows[{f_i}]"
        require_non_empty_list(context.report, f"{base}.steps", flow["steps"], "flow steps")
        diagram_source_required(context.report, f"{base}.diagram", flow["diagram"], "key flow diagram")

        for ref_i, module_id in enumerate(flow["related_module_ids"]):
            context.require_ref("module", module_id, f"{base}.related_module_ids[{ref_i}]", "module")
        for ref_i, runtime_unit_id in enumerate(flow["related_runtime_unit_ids"]):
            context.require_ref("runtime_unit", runtime_unit_id, f"{base}.related_runtime_unit_ids[{ref_i}]", "runtime unit")

        seen_orders = set()
        for s_i, step in enumerate(flow["steps"]):
            step_base = f"{base}.steps[{s_i}]"
            order = step["order"]
            if order in seen_orders:
                context.report.error(
                    base,
                    "step order values must be unique",
                    "Give each step in this flow a distinct order value",
                )
                break
            seen_orders.add(order)
            for ref_i, module_id in enumerate(step["related_module_ids"]):
                context.require_ref("module", module_id, f"{step_base}.related_module_ids[{ref_i}]", "module")
            for ref_i, runtime_unit_id in enumerate(step["related_runtime_unit_ids"]):
                context.require_ref("runtime_unit", runtime_unit_id, f"{step_base}.related_runtime_unit_ids[{ref_i}]", "runtime unit")

        for b_i, branch in enumerate(flow["branches_or_exceptions"]):
            branch_base = f"{base}.branches_or_exceptions[{b_i}]"
            for ref_i, module_id in enumerate(branch["related_module_ids"]):
                context.require_ref("module", module_id, f"{branch_base}.related_module_ids[{ref_i}]", "module")
            for ref_i, runtime_unit_id in enumerate(branch["related_runtime_unit_ids"]):
                context.require_ref("runtime_unit", runtime_unit_id, f"{branch_base}.related_runtime_unit_ids[{ref_i}]", "runtime unit")


def check_all_extra_diagrams(document, context):
    for path, value in walk(document):
        if path.endswith(".extra_diagrams") and isinstance(value, list):
            for i, diagram in enumerate(value):
                diagram_source_required(context.report, f"{path}[{i}]", diagram, "extra diagram")


def check_extra_tables(document, context):
    for path, value in walk(document):
        if not is_extra_table_object(value) or not is_extra_table_registration_path(path):
            continue
        column_keys = [column["key"] for column in value["columns"]]
        seen_column_keys = set()
        for i, key in enumerate(column_keys):
            if key in RESERVED_EXTRA_TABLE_COLUMN_KEYS:
                context.report.error(
                    f"{path}.columns[{i}].key",
                    f"reserved support metadata key {key}",
                    "Use a domain-specific column key that does not shadow support metadata",
                )
            if key in seen_column_keys:
                context.report.error(
                    f"{path}.columns[{i}].key",
                    f"duplicate extra table column key {key}",
                    "Each extra table column key must be unique",
                )
            seen_column_keys.add(key)
        allowed_keys = set(column_keys) | {"evidence_refs"}
        for i, row in enumerate(value["rows"]):
            row_keys = set(row)
            unknown_keys = row_keys - allowed_keys
            if unknown_keys:
                context.report.error(
                    f"{path}.rows[{i}]",
                    "row contains keys outside declared columns",
                    f"Remove unknown keys: {', '.join(sorted(unknown_keys))}",
                )


def check_traceability(document, context):
    for i, trace in enumerate(document["traceability"]):
        target_type = trace["target_type"]
        target_id = trace["target_id"]
        kind = TRACEABILITY_TARGET_KIND[target_type]
        if target_id not in context.ids_by_kind[kind]:
            context.report.error(
                f"$.traceability[{i}].target_id",
                f"does not resolve for target_type {target_type}",
                "Use an ID defined by the target mapping in the Phase 3 spec",
            )
        context.traceability_targets[trace["id"]] = (target_type, target_id)
    check_traceability_backlinks(document, context)


def current_traceability_target(path, value):
    if not isinstance(value, dict):
        return None
    if "module_id" in value:
        return ("module", value["module_id"])
    if "capability_id" in value and ".system_overview.core_capabilities" in path:
        return ("core_capability", value["capability_id"])
    if "capability_id" in value and ".provided_capabilities.rows" in path:
        return ("provided_capability", value["capability_id"])
    if "unit_id" in value:
        return ("runtime_unit", value["unit_id"])
    if "collaboration_id" in value:
        return ("collaboration", value["collaboration_id"])
    if "config_id" in value:
        return ("configuration_item", value["config_id"])
    if "artifact_id" in value:
        return ("data_artifact", value["artifact_id"])
    if "dependency_id" in value:
        return ("dependency", value["dependency_id"])
    if "flow_id" in value and ".key_flows.flows" in path:
        return ("flow", value["flow_id"])
    if "step_id" in value:
        return ("flow_step", value["step_id"])
    if "branch_id" in value:
        return ("flow_branch", value["branch_id"])
    if path.startswith("$.risks["):
        return ("risk", value.get("id"))
    if path.startswith("$.assumptions["):
        return ("assumption", value.get("id"))
    return None


def check_traceability_backlinks(document, context):
    for path, value in walk(document):
        if not isinstance(value, dict) or "traceability_refs" not in value:
            continue
        current = current_traceability_target(path, value)
        if current is None:
            continue
        for i, trace_id in enumerate(value["traceability_refs"]):
            target = context.traceability_targets.get(trace_id)
            if target and target != current:
                context.report.error(
                    f"{path}.traceability_refs[{i}]",
                    f"traceability {trace_id} targets {target[0]} {target[1]} instead of {current[0]} {current[1]}",
                    "Local backlinks must point to traceability items for the current node",
                )


def check_unreferenced_evidence(document, context):
    referenced = set()
    for _path, value in walk(document):
        if isinstance(value, dict):
            referenced.update(value.get("evidence_refs", []))
    for i, evidence in enumerate(document["evidence"]):
        if evidence["id"] not in referenced:
            context.report.warn(
                "$.evidence[%d].id" % i,
                f"unreferenced evidence {evidence['id']}",
                "Remove it from the DSL or cite it from an evidence_refs field",
            )


def content_line_count(content):
    if content == "":
        return 0
    return len(content.splitlines())


def check_source_snippets(document, context, *, allow_long_snippets):
    referenced = set()
    for _path, value in walk(document):
        if isinstance(value, dict):
            referenced.update(value.get("source_snippet_refs", []))

    for i, snippet in enumerate(document["source_snippets"]):
        base = f"$.source_snippets[{i}]"
        if snippet["line_end"] < snippet["line_start"]:
            context.report.error(
                f"{base}.line_end",
                "must be greater than or equal to line_start",
                "Use a positive inclusive line range",
            )
        line_count = content_line_count(snippet["content"])
        if line_count > 50:
            if allow_long_snippets:
                context.report.warn(
                    f"{base}.content",
                    "source snippet is longer than 50 lines",
                    "Keep only necessary evidence when possible",
                )
            else:
                context.report.error(
                    f"{base}.content",
                    "source snippet is longer than 50 lines",
                    "Pass --allow-long-snippets only when the long evidence is intentional",
                )
        elif line_count > 20:
            context.report.warn(
                f"{base}.content",
                "source snippet is longer than 20 lines",
                "Shorter snippets are easier to review",
            )
        if snippet["id"] not in referenced:
            context.report.error(
                f"{base}.id",
                f"unreferenced source snippet {snippet['id']}",
                "Reference it from source_snippet_refs or remove it from the DSL",
            )
        for pattern in HIGH_RISK_SNIPPET_PATTERNS:
            if pattern.search(snippet["content"]):
                context.report.error(
                    f"{base}.content",
                    "contains high-risk secret or personal data pattern",
                    "Redact the snippet before validation",
                )
                break


def has_large_code_like_block(value):
    run_length = 0
    for line in value.splitlines():
        if CODE_LIKE_LINE_RE.search(line):
            run_length += 1
            if run_length >= 5:
                return True
        elif line.strip():
            run_length = 0
    return False


def check_chapter_9(document, context):
    value = document["structure_issues_and_suggestions"]
    for pattern in MARKDOWN_UNSAFE_PATTERNS:
        if pattern.search(value):
            context.report.error(
                "$.structure_issues_and_suggestions",
                "unsafe Markdown structure is not allowed in chapter 9",
                "Use paragraphs, simple lists, emphasis, and inline code only",
            )
            return


def is_mermaid_source_path(path):
    return is_real_diagram_field_path(path, "source")


def is_diagram_type_path(path):
    return is_real_diagram_field_path(path, "diagram_type")


def is_real_diagram_field_path(path, field_name):
    diagram_source_patterns = real_diagram_field_patterns(field_name)
    return any(re.match(pattern, path) for pattern in diagram_source_patterns)


def real_diagram_field_patterns(field_name):
    escaped_field_name = re.escape(field_name)
    return [
        rf"^\$\.architecture_views\.module_relationship_diagram\.{escaped_field_name}$",
        rf"^\$\.module_design\.modules\[\d+\]\.internal_structure\.diagram\.{escaped_field_name}$",
        rf"^\$\.runtime_view\.runtime_flow_diagram\.{escaped_field_name}$",
        rf"^\$\.runtime_view\.runtime_sequence_diagram\.{escaped_field_name}$",
        rf"^\$\.cross_module_collaboration\.collaboration_relationship_diagram\.{escaped_field_name}$",
        rf"^\$\.key_flows\.flows\[\d+\]\.diagram\.{escaped_field_name}$",
        rf"^\$\.architecture_views\.extra_diagrams\[\d+\]\.{escaped_field_name}$",
        rf"^\$\.module_design\.modules\[\d+\]\.external_capability_details\.extra_diagrams\[\d+\]\.{escaped_field_name}$",
        rf"^\$\.module_design\.modules\[\d+\]\.extra_diagrams\[\d+\]\.{escaped_field_name}$",
        rf"^\$\.runtime_view\.extra_diagrams\[\d+\]\.{escaped_field_name}$",
        rf"^\$\.configuration_data_dependencies\.extra_diagrams\[\d+\]\.{escaped_field_name}$",
        rf"^\$\.cross_module_collaboration\.extra_diagrams\[\d+\]\.{escaped_field_name}$",
        rf"^\$\.key_flows\.extra_diagrams\[\d+\]\.{escaped_field_name}$",
    ]


def check_markdown_safety(document, context):
    for path, value in walk(document):
        if not isinstance(value, str):
            continue
        if path.startswith("$.source_snippets["):
            continue
        if is_mermaid_source_path(path):
            if "```" in value:
                context.report.error(path, "Mermaid source must not include Markdown fences", "Store raw Mermaid source only")
            continue
        if is_diagram_type_path(path):
            continue
        if path == "$.structure_issues_and_suggestions":
            continue
        for pattern in MARKDOWN_UNSAFE_PATTERNS:
            if pattern.search(value):
                context.report.error(path, "unsafe Markdown structure is not allowed in plain text fields", "Keep document structure controlled by the renderer")
                break
        for pattern in PROTOTYPE_PATTERNS:
            if pattern.search(value):
                context.report.error(path, "prototype/detail-design content is outside this DSL field", "Move code evidence into source_snippets or summarize structurally")
                break
        if has_large_code_like_block(value):
            context.report.error(path, "large code-like block is outside this DSL field", "Move code evidence into source_snippets or summarize structurally")


def collect_low_confidence(document, context):
    for base_path, getter in LOW_CONFIDENCE_COLLECTIONS:
        values = getter(document)
        for i, item in enumerate(values):
            if isinstance(item, tuple):
                module_index, row_index, row = item
                path = base_path.format(module_index=module_index) + f"[{row_index}]"
                candidate = row
            else:
                path = f"{base_path}[{i}]"
                candidate = item
            if candidate.get("confidence") == "unknown":
                context.report.warn(path, "low-confidence item", "Summarize in chapter 9 when useful")
    for f_i, flow in enumerate(document["key_flows"]["flows"]):
        for s_i, step in enumerate(flow["steps"]):
            if step.get("confidence") == "unknown":
                context.report.warn(f"$.key_flows.flows[{f_i}].steps[{s_i}]", "low-confidence item", "Summarize in chapter 9 when useful")
        for b_i, branch in enumerate(flow["branches_or_exceptions"]):
            if branch.get("confidence") == "unknown":
                context.report.warn(f"$.key_flows.flows[{f_i}].branches_or_exceptions[{b_i}]", "low-confidence item", "Summarize in chapter 9 when useful")


def validate_semantics(document, *, allow_long_snippets=False):
    report = ValidationReport()
    validate_document_fields(document, report)
    context = ValidationContext(document, report)
    context.build()
    run_semantic_checks(document, context, allow_long_snippets=allow_long_snippets)
    return report


def check_v2_global_foundation_rules(document, report):
    for violation in v2_global_rule_violations(document):
        report.error(violation.path, violation.message)


def run_semantic_checks(document, context, *, allow_long_snippets):
    check_v2_global_foundation_rules(document, context.report)
    check_chapter_rules(document, context)
    check_extra_tables(document, context)
    check_traceability(document, context)
    check_unreferenced_evidence(document, context)
    check_source_snippets(document, context, allow_long_snippets=allow_long_snippets)
    check_markdown_safety(document, context)
    collect_low_confidence(document, context)


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    path = Path(args.dsl_file)

    try:
        document = load_json_file(path)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    try:
        require_v2_dsl_version(document)
    except ValueError:
        print(f"ERROR: {V2_VERSION_ERROR}", file=sys.stderr)
        return 2

    schema_failure = schema_errors(document)
    if schema_failure:
        print(format_schema_error(schema_failure[0]).format(), file=sys.stderr)
        return 2

    report = validate_semantics(document, allow_long_snippets=args.allow_long_snippets)
    if report.errors:
        for issue in report.errors:
            print(issue.format(), file=sys.stderr)
        for issue in report.warnings:
            print(issue.format(), file=sys.stderr)
        return 1

    for issue in report.warnings:
        print(issue.format())
    print("Validation succeeded")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
