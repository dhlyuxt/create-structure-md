import json
import os
import shutil
import subprocess
from pathlib import Path

from scripts.v030_semantics import collect_diagrams
from scripts.v030_types import ValidationResult


MERMAID_MODULE_ENV = "MERMAID_ESM_PATH"
MERMAID_PACKAGE_ENV = "MERMAID_PACKAGE_PATH"
NODE_ENV = "MERMAID_NODE_PATH"

DIAGRAM_TYPE_MAP = {
    "flowchart": "flowchart",
    "flowchart-v2": "flowchart",
    "sequence": "sequenceDiagram",
    "sequenceDiagram": "sequenceDiagram",
    "stateDiagram": "stateDiagram-v2",
    "stateDiagram-v2": "stateDiagram-v2",
}


def _first_declaration_word(source: str) -> str:
    for line in source.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("%%"):
            return stripped.split(maxsplit=1)[0]
    return ""


def _normalize_diagram_type(diagram_type: str | None) -> str:
    if diagram_type is None:
        return ""
    return DIAGRAM_TYPE_MAP.get(diagram_type, diagram_type)


def _locate_node() -> Path | None:
    configured = os.environ.get(NODE_ENV)
    if configured:
        path = Path(configured)
        return path if path.exists() else None
    discovered = shutil.which("node")
    return Path(discovered) if discovered else None


def _mermaid_module_from_path(path: Path) -> Path | None:
    if path.is_file():
        return path
    candidates = [
        path / "dist" / "mermaid.esm.mjs",
        path / "node_modules" / "mermaid" / "dist" / "mermaid.esm.mjs",
        path / "mermaid" / "dist" / "mermaid.esm.mjs",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def _mmdc_package_candidates() -> list[Path]:
    mmdc = shutil.which("mmdc")
    if not mmdc:
        return []
    mmdc_path = Path(mmdc).resolve()
    candidates = []
    for parent in [mmdc_path.parent, *mmdc_path.parents]:
        candidates.extend(
            [
                parent / "node_modules" / "mermaid" / "dist" / "mermaid.esm.mjs",
                parent / "node_modules" / "@mermaid-js" / "mermaid-cli" / "node_modules" / "mermaid" / "dist" / "mermaid.esm.mjs",
                parent / "mermaid" / "dist" / "mermaid.esm.mjs",
            ]
        )
    return candidates


def _local_node_modules_candidates() -> list[Path]:
    root = Path(__file__).resolve().parents[1]
    return [
        root / "node_modules" / "mermaid" / "dist" / "mermaid.esm.mjs",
        root.parent / "node_modules" / "mermaid" / "dist" / "mermaid.esm.mjs",
    ]


def _locate_mermaid_module() -> Path | None:
    for env_name in (MERMAID_MODULE_ENV, MERMAID_PACKAGE_ENV):
        configured = os.environ.get(env_name)
        if configured:
            module = _mermaid_module_from_path(Path(configured))
            if module:
                return module
            return None
    for candidate in [*_mmdc_package_candidates(), *_local_node_modules_candidates()]:
        if candidate.exists():
            return candidate
    return None


def _node_script(mermaid_module: Path) -> str:
    module_url = mermaid_module.resolve().as_uri()
    return f"""
Function.prototype.addHook = Function.prototype.addHook || function() {{}};
Function.prototype.sanitize = Function.prototype.sanitize || function(text) {{ return text; }};

const mermaid = (await import({json.dumps(module_url)})).default;

let source = "";
for await (const chunk of process.stdin) {{
  source += chunk;
}}

try {{
  mermaid.initialize({{ startOnLoad: false }});
  const parseResult = await mermaid.parse(source, {{ suppressErrors: false }});
  const diagramType =
    parseResult && typeof parseResult === "object"
      ? (parseResult.diagramType || parseResult.type || parseResult.name || null)
      : null;
  console.log(JSON.stringify({{
    ok: true,
    diagramType,
    warnings: parseResult && Array.isArray(parseResult.warnings) ? parseResult.warnings : []
  }}));
}} catch (error) {{
  console.log(JSON.stringify({{
    ok: false,
    error: error && error.message ? error.message : String(error)
  }}));
}}
"""


def _run_mermaid_parse(source: str) -> tuple[str, list[str]]:
    node = _locate_node()
    if node is None:
        raise RuntimeError(f"Node executable not found; set {NODE_ENV}")
    mermaid_module = _locate_mermaid_module()
    if mermaid_module is None:
        raise RuntimeError(f"Mermaid ESM package not found; set {MERMAID_MODULE_ENV} or {MERMAID_PACKAGE_ENV}")

    completed = subprocess.run(
        [str(node), "--input-type=module", "--eval", _node_script(mermaid_module)],
        input=source,
        text=True,
        capture_output=True,
        check=False,
        timeout=20,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or f"exit code {completed.returncode}"
        raise RuntimeError(f"Mermaid tooling failed: {detail}")
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Mermaid tooling returned non-JSON output: {exc}") from exc
    if not isinstance(payload, dict):
        raise RuntimeError("Mermaid tooling returned an unexpected payload")
    if not payload.get("ok"):
        error = str(payload.get("error") or "Mermaid parse failed")
        raise ValueError(error)
    warnings = payload.get("warnings") or []
    if not isinstance(warnings, list):
        warnings = [str(warnings)]
    return _normalize_diagram_type(payload.get("diagramType")), [str(warning) for warning in warnings]


def _all_diagrams(package):
    for key, chapter in package.chapters.items():
        yield from collect_diagrams(chapter, f"$.{key}")
    for index, mechanism in enumerate(package.mechanisms):
        yield from collect_diagrams(mechanism.data, f"$.key_mechanisms[{index}]")


def mermaid_validation_result(package) -> ValidationResult:
    result = ValidationResult()
    for path, diagram in _all_diagrams(package):
        source_path = path + ".source"
        source = diagram["source"]
        if _first_declaration_word(source) == "graph":
            result.error("mermaid.legacy_graph", source_path, "legacy graph declarations are rejected in 0.3.0; use flowchart")
            continue
        try:
            tool_type, warnings = _run_mermaid_parse(source)
        except ValueError as exc:
            result.error("mermaid.syntax", source_path, str(exc))
            continue
        except (OSError, RuntimeError, subprocess.SubprocessError) as exc:
            result.error("mermaid.tooling", source_path, str(exc))
            continue
        expected_type = _normalize_diagram_type(diagram["diagram_type"])
        if tool_type != expected_type:
            result.error("mermaid.diagram_type", source_path, f"diagram_type does not match Mermaid tool result: {expected_type} != {tool_type or '<unknown>'}")
        for warning in warnings:
            result.warn("mermaid.warning", source_path, warning)
    return result
