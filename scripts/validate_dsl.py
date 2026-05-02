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
    pass


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
