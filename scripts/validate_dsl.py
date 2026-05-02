#!/usr/bin/env python3
import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError


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
    "dependency": "DEP-",
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
        self.ids_by_kind = {kind: {} for kind in PREFIX_BY_KIND}
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
        prefix = PREFIX_BY_KIND[kind]
        if not isinstance(value, str) or not value.startswith(prefix):
            self.report.error(path, f"ID must start with {prefix}", "Use the documented prefix; numeric suffixes are optional")
            return
        if value in self.id_owner:
            first_kind, first_path = self.id_owner[value]
            self.report.error(path, f"duplicate ID {value}", f"First defined as {first_kind} at {first_path}")
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
    pass


def check_chapter_8(document, context):
    pass


def check_chapter_9(document, context):
    pass


def check_all_extra_diagrams(document, context):
    for path, value in walk(document):
        if path.endswith(".extra_diagrams") and isinstance(value, list):
            for i, diagram in enumerate(value):
                diagram_source_required(context.report, f"{path}[{i}]", diagram, "extra diagram")


def check_source_snippets(document, context, *, allow_long_snippets):
    pass


def check_markdown_safety(document, context):
    pass


def collect_low_confidence(document, context):
    pass


def validate_semantics(document, *, allow_long_snippets=False):
    report = ValidationReport()
    validate_document_fields(document, report)
    context = ValidationContext(document, report)
    context.build()
    run_semantic_checks(document, context, allow_long_snippets=allow_long_snippets)
    return report


def run_semantic_checks(document, context, *, allow_long_snippets):
    check_chapter_rules(document, context)
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
