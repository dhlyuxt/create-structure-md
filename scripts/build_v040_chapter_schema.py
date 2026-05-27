#!/usr/bin/env python3
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "schemas/v0.4.0/chapter.schema.json"
EXTRA_KEY_PATTERN = "^[a-z][a-z0-9_]*$"


def ref(name):
    return {"$ref": f"#/$defs/{name}"}


def string():
    return {"type": "string", "minLength": 1}


def const(value):
    return {"const": value}


def array(item, *, min_items=None):
    schema = {"type": "array", "items": item}
    if min_items is not None:
        schema["minItems"] = min_items
    return schema


def obj(required, properties):
    return {
        "type": "object",
        "additionalProperties": False,
        "required": required,
        "properties": properties,
    }


def block_array(*, min_items=None):
    return array(ref("Block"), min_items=min_items)


def fixed_section():
    return obj(["blocks"], {"blocks": block_array()})


def extra_subsections():
    return array(ref("ExtraSubsection"))


defs = {
    "TextBlock": obj(["type", "content"], {"type": const("text"), "content": string()}),
    "UnorderedListBlock": obj(
        ["type", "items"],
        {"type": const("unordered_list"), "items": array(string(), min_items=1)},
    ),
    "OrderedListBlock": obj(
        ["type", "items"],
        {"type": const("ordered_list"), "items": array(string(), min_items=1)},
    ),
    "TableBlock": obj(
        ["type", "columns", "rows"],
        {
            "type": const("table"),
            "columns": array(string(), min_items=1),
            "rows": array(array(string())),
        },
    ),
    "MermaidBlock": obj(
        ["type", "title", "diagram_type", "source"],
        {
            "type": const("mermaid"),
            "title": string(),
            "diagram_type": string(),
            "source": string(),
        },
    ),
    "CodeBlock": obj(
        ["type", "language", "content"],
        {
            "type": const("code"),
            "language": string(),
            "title": string(),
            "content": string(),
        },
    ),
}

defs["Block"] = {
    "oneOf": [
        ref("TextBlock"),
        ref("UnorderedListBlock"),
        ref("OrderedListBlock"),
        ref("TableBlock"),
        ref("MermaidBlock"),
        ref("CodeBlock"),
    ]
}

defs["ExtraSubsection"] = obj(
    ["key", "title", "blocks"],
    {
        "key": {"type": "string", "pattern": EXTRA_KEY_PATTERN},
        "title": string(),
        "blocks": block_array(),
    },
)

defs["DocumentChapter"] = obj(
    ["document"],
    {
        "document": obj(
            ["repository_name", "output_file"],
            {
                "repository_name": string(),
                "output_file": string(),
                "summary": string(),
            },
        )
    },
)

defs["ComponentRow"] = obj(
    ["component", "role", "location"],
    {"component": string(), "role": string(), "location": string()},
)
defs["LayerRow"] = obj(
    ["layer", "role", "location"],
    {"layer": string(), "role": string(), "location": string()},
)
defs["ModuleTableRow"] = obj(
    ["module", "role", "layer", "location"],
    {"module": string(), "role": string(), "layer": string(), "location": string()},
)

defs["ComponentTable"] = obj(["rows"], {"rows": array(ref("ComponentRow"))})
defs["LayerTable"] = obj(["rows"], {"rows": array(ref("LayerRow"))})
defs["ModuleTable"] = obj(["rows"], {"rows": array(ref("ModuleTableRow"))})

defs["CoreComponentsSection"] = obj(
    ["component_table"],
    {"component_table": ref("ComponentTable"), "blocks": block_array()},
)
defs["LayersSection"] = obj(
    ["layer_table"],
    {"layer_table": ref("LayerTable"), "blocks": block_array()},
)
defs["ModuleMapSection"] = obj(
    ["module_table"],
    {"module_table": ref("ModuleTable"), "blocks": block_array()},
)

defs["OverviewChapter"] = obj(
    ["overview"],
    {
        "overview": obj(
            [
                "repository_intro",
                "problems_solved",
                "main_capabilities",
                "core_components",
                "extra_subsections",
            ],
            {
                "repository_intro": fixed_section(),
                "problems_solved": fixed_section(),
                "main_capabilities": fixed_section(),
                "core_components": ref("CoreComponentsSection"),
                "extra_subsections": extra_subsections(),
            },
        )
    },
)

defs["FirstRunStep"] = obj(["title", "blocks"], {"title": string(), "blocks": block_array()})
defs["FirstRunSection"] = obj(
    ["steps", "blocks"],
    {"steps": array(ref("FirstRunStep"), min_items=1), "blocks": block_array()},
)

defs["QuickStartChapter"] = obj(
    ["quick_start"],
    {
        "quick_start": obj(
            [
                "usage_scenarios",
                "setup",
                "first_run",
                "minimal_example",
                "expected_result",
                "extra_subsections",
            ],
            {
                "usage_scenarios": fixed_section(),
                "setup": fixed_section(),
                "first_run": ref("FirstRunSection"),
                "minimal_example": fixed_section(),
                "expected_result": fixed_section(),
                "extra_subsections": extra_subsections(),
            },
        )
    },
)

defs["ArchitectureOverviewChapter"] = obj(
    ["architecture_overview"],
    {
        "architecture_overview": obj(
            [
                "architecture_summary",
                "layers",
                "module_map",
                "repository_layout",
                "extra_subsections",
            ],
            {
                "architecture_summary": fixed_section(),
                "layers": ref("LayersSection"),
                "module_map": ref("ModuleMapSection"),
                "repository_layout": fixed_section(),
                "extra_subsections": extra_subsections(),
            },
        )
    },
)

defs["MainFlowEntry"] = obj(["name"], {"name": string(), "location": string()})
defs["MainFlow"] = obj(
    ["title", "purpose", "entry", "blocks"],
    {
        "title": string(),
        "purpose": string(),
        "entry": ref("MainFlowEntry"),
        "blocks": block_array(),
    },
)
defs["MainFlowsChapter"] = obj(
    ["main_flows"],
    {
        "main_flows": obj(
            ["flow_overview", "flows", "extra_subsections"],
            {
                "flow_overview": fixed_section(),
                "flows": array(ref("MainFlow"), min_items=1),
                "extra_subsections": extra_subsections(),
            },
        )
    },
)

defs["Mechanism"] = obj(["title", "blocks"], {"title": string(), "blocks": block_array()})
defs["Module"] = obj(
    ["name", "location", "purpose", "blocks", "mechanisms", "extra_subsections"],
    {
        "name": string(),
        "location": string(),
        "purpose": string(),
        "blocks": block_array(),
        "mechanisms": array(ref("Mechanism")),
        "extra_subsections": extra_subsections(),
    },
)
defs["ModuleDetailsChapter"] = obj(
    ["module_details"],
    {
        "module_details": obj(
            ["intro_blocks", "modules", "extra_subsections"],
            {
                "intro_blocks": block_array(),
                "modules": array(ref("Module"), min_items=1),
                "extra_subsections": extra_subsections(),
            },
        )
    },
)

schema = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://create-structure-md.local/schemas/v0.4.0/chapter.schema.json",
    "$defs": defs,
}

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(schema, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"wrote {OUT}")
