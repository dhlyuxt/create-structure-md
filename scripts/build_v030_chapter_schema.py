#!/usr/bin/env python3
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "schemas/v0.3.0/chapter.schema.json"


def ref(name):
    return {"$ref": f"#/$defs/{name}"}


def string():
    return {"type": "string", "minLength": 1}


def const(value):
    return {"const": value}


def enum(*values):
    return {"type": "string", "enum": list(values)}


def integer():
    return {"type": "integer", "minimum": 1}


def array(item, *, min_items=None, max_items=None):
    schema = {"type": "array", "items": item}
    if min_items is not None:
        schema["minItems"] = min_items
    if max_items is not None:
        schema["maxItems"] = max_items
    return schema


def obj(required, properties):
    return {
        "type": "object",
        "additionalProperties": False,
        "required": required,
        "properties": properties,
    }


def chapter_header(key, title):
    return obj(["key", "title"], {"key": const(key), "title": const(title)})


defs = {
    "Confidence": enum("high", "medium", "low"),
    "ChapterKey": enum(
        "document",
        "repository_overview",
        "directory_map",
        "module_layers",
        "repository_mainline",
        "key_mechanisms",
        "integration_boundaries",
        "risks_validation",
    ),
    "Id": {"type": "string", "pattern": "^[a-z0-9][a-z0-9_-]*$"},
    "Path": {"type": "string", "minLength": 1, "pattern": "^(?!/)(?!.*\\\\)(?!.*(?:^|/)(?:\\.|\\.\\.)(?:/|$))(?!.*//).+$"},
    "SourceRef": obj(["path"], {"path": ref("Path"), "symbol": string()}),
    "Diagram": obj(
        ["id", "title", "diagram_type", "description", "source"],
        {
            "id": ref("Id"),
            "title": string(),
            "diagram_type": enum("flowchart", "sequenceDiagram", "stateDiagram-v2"),
            "description": string(),
            "source": string(),
        },
    ),
    "FlowchartDiagram": obj(
        ["id", "title", "diagram_type", "description", "source"],
        {
            "id": ref("Id"),
            "title": string(),
            "diagram_type": const("flowchart"),
            "description": string(),
            "source": string(),
        },
    ),
    "MainlineDetailDiagram": obj(
        ["id", "title", "diagram_type", "description", "source"],
        {
            "id": ref("Id"),
            "title": string(),
            "diagram_type": enum("flowchart", "sequenceDiagram"),
            "description": string(),
            "source": string(),
        },
    ),
    "DocumentInfo": obj(
        ["title", "version", "status", "language", "generated_at", "output_file"],
        {"title": string(), "version": string(), "status": enum("draft", "reviewed", "final"), "language": const("zh-CN"), "generated_at": string(), "output_file": string()},
    ),
    "RepositoryInfo": obj(
        ["name", "root_display_path", "kind", "primary_languages"],
        {"name": string(), "root_display_path": string(), "kind": enum("c_library", "c_application", "firmware", "mixed", "other"), "primary_languages": array(string(), min_items=1)},
    ),
    "ScopeIncluded": obj(["area", "description"], {"area": string(), "description": string()}),
    "ScopeExcluded": obj(["area", "reason"], {"area": string(), "reason": string()}),
    "Scope": obj(["included", "excluded"], {"included": array(ref("ScopeIncluded")), "excluded": array(ref("ScopeExcluded"))}),
    "ConfidenceSummary": obj(["level", "summary", "validation_gaps"], {"level": ref("Confidence"), "summary": string(), "validation_gaps": array(string())}),
    "RepositoryOverview": obj(["summary", "problem_domain", "repository_purpose", "target_readers"], {"summary": string(), "problem_domain": string(), "repository_purpose": string(), "target_readers": array(string(), min_items=1)}),
    "RecommendedFile": obj(["path", "reason"], {"path": ref("Path"), "reason": string()}),
    "ReadingStep": obj(["order", "title", "why_read_this", "recommended_files", "expected_takeaway"], {"order": integer(), "title": string(), "why_read_this": string(), "recommended_files": array(ref("RecommendedFile")), "expected_takeaway": string()}),
    "ReaderOrientation": obj(["read_first", "read_later", "can_skip_initially"], {"read_first": array(string()), "read_later": array(string()), "can_skip_initially": array(string())}),
    "CoreCapability": obj(["name", "description", "entry_points", "notes"], {"name": string(), "description": string(), "entry_points": array(ref("SourceRef")), "notes": string()}),
    "DirectoryGroup": obj(["name", "role", "paths", "responsibility", "read_when", "notes"], {"name": string(), "role": enum("main_source", "public_headers", "platform_port", "plugin", "demo", "docs", "tests", "third_party", "build", "generated", "other"), "paths": array(ref("Path"), min_items=1), "responsibility": string(), "read_when": string(), "notes": string()}),
    "ImportantFile": obj(["path", "role", "why_it_matters", "related_chapters"], {"path": ref("Path"), "role": string(), "why_it_matters": string(), "related_chapters": array(ref("ChapterKey"))}),
    "RelationshipDiagram": obj(["summary"], {"summary": string(), "diagram": ref("Diagram")}),
    "AreaBoundaryNote": obj(["area", "note"], {"area": string(), "note": string()}),
    "TopicBoundaryNote": obj(["topic", "note"], {"topic": string(), "note": string()}),
    "Layer": obj(["layer_id", "name", "role", "responsibilities", "paths", "notes"], {"layer_id": ref("Id"), "name": string(), "role": string(), "responsibilities": array(string()), "paths": array(ref("Path"), min_items=1), "notes": string()}),
    "ModuleCollaboration": obj(["module_ref", "relationship"], {"module_ref": ref("Id"), "relationship": string()}),
    "Module": obj(["module_id", "name", "layer_id", "purpose", "source_paths", "owns", "consumes", "produces", "does_not_own", "collaborates_with", "read_when", "notes"], {"module_id": ref("Id"), "name": string(), "layer_id": ref("Id"), "purpose": string(), "source_paths": array(ref("Path"), min_items=1), "owns": array(string()), "consumes": array(string()), "produces": array(string()), "does_not_own": array(string()), "collaborates_with": array(ref("ModuleCollaboration")), "read_when": string(), "notes": string()}),
    "MainlineEntry": obj(["kind", "name", "description"], {"kind": enum("api", "command", "build_target", "startup", "user_action", "external_event", "other"), "name": string(), "description": string(), "source_ref": ref("SourceRef")}),
    "MainlineStep": obj(["order", "step", "source_refs", "effect"], {"order": integer(), "step": string(), "module_refs": array(ref("Id")), "source_refs": array(ref("SourceRef")), "effect": string()}),
    "Mainline": obj(["mainline_id", "name", "purpose", "entry", "steps", "result", "notes"], {"mainline_id": ref("Id"), "name": string(), "purpose": string(), "entry": ref("MainlineEntry"), "steps": array(ref("MainlineStep"), min_items=1), "result": string(), "detail_diagram": ref("MainlineDetailDiagram"), "notes": string()}),
    "MechanismSection": obj(["title"], {"title": string()}),
    "SourceFocus": obj(["source_ref", "reason"], {"source_ref": ref("SourceRef"), "reason": string()}),
    "MechanismStep": obj(["order", "step", "source_refs", "state_or_data", "notes"], {"order": integer(), "step": string(), "source_refs": array(ref("SourceRef")), "state_or_data": string(), "notes": string()}),
    "StateOrData": obj(["name", "kind", "description", "source_refs"], {"name": string(), "kind": enum("state", "struct", "enum", "macro", "storage_layout", "runtime_value", "artifact", "other"), "description": string(), "source_refs": array(ref("SourceRef"))}),
    "CommonMisunderstanding": obj(["misunderstanding", "correction"], {"misunderstanding": string(), "correction": string()}),
    "ConfigurationLocation": obj(["description"], {"description": string(), "source_ref": ref("SourceRef"), "external_name": string()}),
    "RequiredConfiguration": obj(["name", "kind", "location", "purpose", "required_when", "notes"], {"name": string(), "kind": enum("macro", "config_file", "build_option", "environment", "runtime_setting", "other"), "location": ref("ConfigurationLocation"), "purpose": string(), "required_when": string(), "notes": string()}),
    "AdaptationLocation": obj(["description"], {"description": string(), "source_ref": ref("SourceRef"), "external_name": string()}),
    "RequiredAdaptation": obj(["name", "kind", "location", "responsibility", "caller_or_consumer", "failure_if_missing"], {"name": string(), "kind": enum("port_function", "platform_hook", "driver_binding", "memory_hook", "logging_hook", "other"), "location": ref("AdaptationLocation"), "responsibility": string(), "caller_or_consumer": string(), "failure_if_missing": string()}),
    "IntegrationEntry": obj(["description"], {"description": string(), "source_ref": ref("SourceRef"), "external_name": string(), "command": string()}),
    "IntegrationPath": obj(["name", "scenario", "recommended_entry", "steps", "reference_examples", "notes"], {"name": string(), "scenario": string(), "recommended_entry": ref("IntegrationEntry"), "steps": array(string(), min_items=1), "reference_examples": array(ref("Path")), "notes": string()}),
    "ExternalDependency": obj(["name", "kind", "used_by", "integration_role", "notes"], {"name": string(), "kind": enum("library", "hardware", "toolchain", "os", "protocol", "service", "other"), "used_by": string(), "integration_role": string(), "notes": string()}),
    "OutOfScopeResponsibility": obj(["topic", "owner", "reason"], {"topic": string(), "owner": enum("caller", "platform", "application", "build_system", "deployment", "unknown"), "reason": string()}),
    "Risk": obj(["risk_id", "description", "impact", "mitigation", "related_modules", "related_mechanisms", "confidence"], {"risk_id": ref("Id"), "description": string(), "impact": string(), "mitigation": string(), "related_modules": array(ref("Id")), "related_mechanisms": array(ref("Id")), "confidence": ref("Confidence")}),
    "Assumption": obj(["assumption_id", "description", "rationale", "validation_suggestion", "confidence"], {"assumption_id": ref("Id"), "description": string(), "rationale": string(), "validation_suggestion": string(), "confidence": ref("Confidence")}),
    "ValidationGap": obj(["gap_id", "gap_type", "description", "why_it_matters", "suggested_validation", "related_chapters", "confidence"], {"gap_id": ref("Id"), "gap_type": enum("analysis_gap", "missing_build_validation", "missing_runtime_validation", "uncertain_behavior", "no_key_mechanisms_selected", "other"), "description": string(), "why_it_matters": string(), "suggested_validation": string(), "related_chapters": array(ref("ChapterKey")), "confidence": ref("Confidence")}),
    "LowConfidenceLocation": {"oneOf": [obj(["kind", "chapter"], {"kind": const("chapter"), "chapter": ref("ChapterKey")}), obj(["kind", "path"], {"kind": const("manifest_path"), "path": ref("Path")})]},
    "LowConfidenceItem": obj(["item_id", "location", "description", "reason", "needed_evidence"], {"item_id": ref("Id"), "location": ref("LowConfidenceLocation"), "description": string(), "reason": string(), "needed_evidence": string()}),
}

defs["DocumentChapter"] = obj(["chapter", "document", "repository", "scope", "confidence"], {"chapter": chapter_header("document", "文档说明"), "document": ref("DocumentInfo"), "repository": ref("RepositoryInfo"), "scope": ref("Scope"), "confidence": ref("ConfidenceSummary")})
defs["RepositoryOverviewChapter"] = obj(["chapter", "overview", "core_capabilities", "reading_route", "reader_orientation"], {"chapter": chapter_header("repository_overview", "仓库概述与阅读路线"), "overview": ref("RepositoryOverview"), "core_capabilities": array(ref("CoreCapability"), min_items=1), "reading_route": obj(["summary", "steps"], {"summary": string(), "steps": array(ref("ReadingStep"), min_items=1)}), "reader_orientation": ref("ReaderOrientation")})
defs["DirectoryMapChapter"] = obj(["chapter", "summary", "directory_groups", "important_files", "directory_relationships", "boundary_notes"], {"chapter": chapter_header("directory_map", "目录地图"), "summary": string(), "directory_groups": array(ref("DirectoryGroup"), min_items=1), "important_files": array(ref("ImportantFile")), "directory_relationships": ref("RelationshipDiagram"), "boundary_notes": array(ref("AreaBoundaryNote"))})
defs["ModuleLayersChapter"] = obj(["chapter", "summary", "layers", "modules", "boundary_notes"], {"chapter": chapter_header("module_layers", "系统分层与模块职责"), "summary": string(), "layers": array(ref("Layer"), min_items=1), "modules": array(ref("Module"), min_items=1), "boundary_notes": array(ref("TopicBoundaryNote")), "layer_diagram": ref("Diagram")})
defs["RepositoryMainlineChapter"] = obj(["chapter", "summary", "mainline_overview_diagram", "mainlines", "cross_mainline_notes"], {"chapter": chapter_header("repository_mainline", "仓库主线"), "summary": string(), "mainline_overview_diagram": ref("FlowchartDiagram"), "mainlines": array(ref("Mainline"), min_items=1, max_items=3), "cross_mainline_notes": array(ref("TopicBoundaryNote"))})
defs["MechanismChapter"] = obj(["section", "why_it_matters", "reader_prerequisites", "related_modules", "source_focus", "mechanism_overview", "flow", "key_states_or_data", "common_misunderstandings", "validation_gaps", "confidence"], {"section": ref("MechanismSection"), "why_it_matters": string(), "reader_prerequisites": array(string()), "related_modules": array(ref("Id")), "source_focus": array(ref("SourceFocus"), min_items=1), "mechanism_overview": string(), "flow": array(ref("MechanismStep"), min_items=1), "key_states_or_data": array(ref("StateOrData")), "common_misunderstandings": array(ref("CommonMisunderstanding")), "validation_gaps": array(string()), "confidence": ref("Confidence"), "diagram": ref("Diagram")})
defs["IntegrationBoundariesChapter"] = obj(["chapter", "summary", "required_configuration", "required_adaptations", "integration_paths", "external_dependencies", "out_of_scope_responsibilities"], {"chapter": chapter_header("integration_boundaries", "配置、移植与集成边界"), "summary": string(), "required_configuration": array(ref("RequiredConfiguration")), "required_adaptations": array(ref("RequiredAdaptation")), "integration_paths": array(ref("IntegrationPath")), "external_dependencies": array(ref("ExternalDependency")), "out_of_scope_responsibilities": array(ref("OutOfScopeResponsibility"))})
defs["RisksValidationChapter"] = obj(["chapter", "summary", "risks", "assumptions", "validation_gaps", "low_confidence_items"], {"chapter": chapter_header("risks_validation", "风险、假设与验证缺口"), "summary": string(), "risks": array(ref("Risk")), "assumptions": array(ref("Assumption")), "validation_gaps": array(ref("ValidationGap")), "low_confidence_items": array(ref("LowConfidenceItem"))})

schema = {"$schema": "https://json-schema.org/draft/2020-12/schema", "$id": "https://create-structure-md.local/schemas/v0.3.0/chapter.schema.json", "$defs": defs}

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(schema, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
