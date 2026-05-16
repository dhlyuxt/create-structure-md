# create-structure-md V2 Phase 4 Renderer And Mermaid Gates Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Render all V2 Phase 4 Markdown output with diagram metadata and add auditable Mermaid readability, strict validation, and rendered diagram completeness gates.

**Architecture:** Keep `scripts/validate_mermaid.py` and `references/mermaid-rules.md` unchanged. Add a Phase 4 helper module for expected-diagram collection, readability-review artifact validation, and rendered completeness checks, then add a separate verification workflow script that orchestrates the existing Mermaid validator without changing it. The renderer emits `diagram-id` metadata through the existing shared Mermaid rendering helper so Chapter 3, Chapter 4 interfaces, Chapter 4 content blocks, Chapter 5, Chapter 6, Chapter 7, Chapter 8, and Chapter 9 all share the same metadata behavior.

**Tech Stack:** Python 3, standard-library `unittest`, `jsonschema` Draft 2020-12, existing renderer helpers in `scripts/render_markdown.py`, existing Mermaid validator in `scripts/validate_mermaid.py`, no new runtime dependencies.

---

## Scope And Constraints

- Do not add repository analysis, requirement inference, Word/PDF/image export, multi-document output, or a V1-to-V2 migration tool.
- Do not modify `scripts/validate_mermaid.py`.
- Do not modify `references/mermaid-rules.md`.
- Do not run deletion commands. Workspace instruction: when cleanup is needed, give the command to the user instead of executing it.
- Keep `dsl_version` fixed at `0.2.0`; V1 DSL remains rejected input.
- Mermaid readability review artifacts are workflow metadata only: not stored in DSL instances and not rendered into final Markdown.
- Static-only Mermaid acceptance is not sufficient for final Phase 4 success. The workflow must strict-validate rendered Markdown unless the run stops before final acceptance.
- Pre-render strict validation may continue to cover only existing paths supported by `scripts/validate_mermaid.py`; post-render strict validation covers every rendered Mermaid fence, including V2 local interface and content-block diagrams.
- Use the same expected-diagram collector for readability artifact validation and rendered completeness.
- `diagram-id` comments are structural Markdown source metadata and are not controlled by `--evidence-mode`.

Use the project Python for verification:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest discover -s tests -v
```

Targeted Phase 4 verification command:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_v2_phase4_renderer_and_mermaid_gates -v
```

Boundary guard after implementation:

```bash
git diff --exit-code -- scripts/validate_mermaid.py references/mermaid-rules.md
```

Expected: no diff.

---

## File Structure

- Create: `scripts/v2_phase4.py`
  - Owns Phase 4 workflow helpers: one shared expected diagram collector, readability-review artifact validation, rendered Markdown diagram metadata extraction, and rendered diagram completeness checks.
- Create: `scripts/verify_v2_mermaid_gates.py`
  - Owns the strict Phase 4 gate workflow while leaving `scripts/validate_mermaid.py` unchanged. It validates the review artifact, optionally runs pre-render strict DSL validation, validates rendered diagram completeness, and runs post-render strict Markdown validation.
- Modify: `scripts/render_markdown.py`
  - Emits `<!-- diagram-id: ... -->` immediately before every Mermaid fence through `render_mermaid_block()`.
- Create: `tests/test_v2_phase4_renderer_and_mermaid_gates.py`
  - Covers renderer metadata, expected diagram collection, readability artifact validation, rendered completeness, and verification workflow failure modes.
- Modify: `tests/test_render_markdown.py`
  - Adds regression coverage where existing renderer tests already cover evidence modes and `not_applicable_reason` fail-fast behavior.
- Modify: `tests/test_validate_mermaid.py`
  - Updates workflow/documentation expectations only; do not add assertions that require changing `scripts/validate_mermaid.py`.
- Modify: `tests/test_phase7_e2e.py`
  - Updates end-to-end examples to assert rendered `diagram-id` metadata and Phase 4 completeness. Strict real-CLI checks remain skipped when local `node`/`mmdc` are unavailable.
- Modify: `SKILL.md`
  - Updates the skill workflow to require independent Mermaid readability review before strict validation, require review artifact path, and replace static-only post-render acceptance with Phase 4 strict gates.
- Modify: `references/dsl-spec.md`
  - Documents expected diagram paths and the fact that readability artifacts are workflow metadata, not DSL content.
- Modify: `references/document-structure.md`
  - Documents `diagram-id` metadata before Mermaid fences and rendered diagram completeness.
- Modify: `references/review-checklist.md`
  - Adds reviewer checks for review artifact coverage, completeness, strict rendered Markdown validation, and unchanged Mermaid validator/rules files.
- Verify only: `schemas/structure-design.schema.json`
  - No schema change is expected because review artifacts are outside DSL instances and `diagram-id` metadata is renderer output.
- Verify only: `scripts/validate_mermaid.py`
  - Must remain unchanged.
- Verify only: `references/mermaid-rules.md`
  - Must remain unchanged.
- Verify only: `requirements.txt`
  - Must still contain only `jsonschema`.

---

## Review History

This plan is intentionally review-driven. The main agent revises this section after each adversarial sub-agent pass.

- Draft: Initial main-agent plan before adversarial review.
- Round 1: Revised after adversarial review. Fixes added for skipped-diagram semantics, distinct workflow-order signposts, current fixture interface indexes, pre-render workflow coverage, shared safe diagram ID rules, relative `source_dsl` artifact paths, and the existing documentation test class name.
- Round 2: Revised after adversarial review. Fixes added for Phase 7 and `SKILL.md` documentation tests, malformed `source_dsl` handling, V2/global DSL gates in the verifier, fence-state-aware rendered metadata extraction, exact workflow signposts including `--work-dir`, and removal of an invalid “valid skipped diagram” fixture state.
- Round 3: Final review found no Critical/High blockers. Medium fixes added for exact stale static-only test locations, artifact/DSL path consistency, and executable-interface-only collection of local execution-flow diagrams.

---

### Task 1: Phase 4 Test Harness And Renderer Metadata Contract

**Files:**
- Create: `tests/test_v2_phase4_renderer_and_mermaid_gates.py`
- Modify: `scripts/render_markdown.py`

- [ ] **Step 1: Write failing renderer metadata tests**

Create `tests/test_v2_phase4_renderer_and_mermaid_gates.py` with these imports and the first tests:

```python
import contextlib
import importlib.util
import io
import json
import subprocess
import sys
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/valid-v2-foundation.dsl.json"
PYTHON = sys.executable


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def valid_document():
    return deepcopy(load_json(FIXTURE))


def load_script(relative_path, module_name):
    spec = importlib.util.spec_from_file_location(module_name, ROOT / relative_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_json(directory, name, value):
    path = Path(directory) / name
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def write_text(directory, name, value):
    path = Path(directory) / name
    path.write_text(value, encoding="utf-8")
    return path


def call_main(module, argv):
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        code = module.main(argv)
    return code or 0, stdout.getvalue(), stderr.getvalue()


class Phase4RendererMetadataTests(unittest.TestCase):
    def test_rendered_mermaid_fences_have_adjacent_diagram_id_metadata(self):
        renderer = load_script("scripts/render_markdown.py", "render_markdown_phase4_under_test")
        markdown = renderer.render_markdown(valid_document())

        expected_fragments = [
            "<!-- diagram-id: MER-ARCH-MODULES -->\n```mermaid",
            "<!-- diagram-id: MER-IFACE-SKILL-RENDER-CLI -->\n```mermaid",
            "<!-- diagram-id: MER-BLOCK-MECHANISM-FLOW -->\n```mermaid",
            "<!-- diagram-id: MER-RUNTIME-FLOW -->\n```mermaid",
            "<!-- diagram-id: MER-COLLABORATION-RELATIONSHIP -->\n```mermaid",
            "<!-- diagram-id: MER-FLOW-GENERATE -->\n```mermaid",
            "<!-- diagram-id: MER-BLOCK-STRUCTURE-ISSUES -->\n```mermaid",
        ]
        for fragment in expected_fragments:
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, markdown)

    def test_diagram_id_metadata_is_not_controlled_by_evidence_mode(self):
        renderer = load_script("scripts/render_markdown.py", "render_markdown_phase4_inline_under_test")
        hidden = renderer.render_markdown(valid_document(), evidence_mode="hidden")
        inline = renderer.render_markdown(valid_document(), evidence_mode="inline")
        self.assertIn("<!-- diagram-id: MER-ARCH-MODULES -->", hidden)
        self.assertIn("<!-- diagram-id: MER-ARCH-MODULES -->", inline)
```

- [ ] **Step 2: Run the new metadata tests to verify they fail**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_v2_phase4_renderer_and_mermaid_gates.Phase4RendererMetadataTests -v
```

Expected: FAIL because `render_mermaid_block()` currently emits Mermaid fences without `diagram-id` comments.

- [ ] **Step 3: Update the shared Mermaid renderer**

Modify `scripts/render_markdown.py` so `render_mermaid_block()` inserts a comment immediately before the fence when rendering a non-empty diagram source. Add the shared safe metadata ID regex near the renderer's other regex constants:

```python
SAFE_DIAGRAM_ID_COMMENT_RE = re.compile(r"^(?!.*--)[A-Za-z0-9_.:-]+$")
```

```python
def render_diagram_id_comment(diagram):
    diagram_id = stringify_markdown_value((diagram or {}).get("id", "")).strip()
    if not diagram_id:
        raise RenderError("Mermaid diagram must include id before rendering")
    if not SAFE_DIAGRAM_ID_COMMENT_RE.fullmatch(diagram_id):
        raise RenderError(f"unsafe Mermaid diagram id for metadata comment: {diagram_id}")
    return f"<!-- diagram-id: {diagram_id} -->"


def render_mermaid_block(diagram, empty_text=None):
    source = ""
    if diagram:
        source = str(diagram.get("source") or "")
    if source == "":
        return empty_text or ""
    if "```" in source or "~~~" in source:
        raise RenderError("Mermaid source must not contain fenced code markers")

    parts = []
    title = diagram.get("title") if diagram else ""
    description = diagram.get("description") if diagram else ""
    if title:
        parts.append(escape_plain_text(title))
    if description:
        parts.append(escape_plain_text(description))
    parts.append(f"{render_diagram_id_comment(diagram)}\n```mermaid\n{source}\n```")
    return "\n\n".join(parts)
```

- [ ] **Step 4: Run metadata tests again**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_v2_phase4_renderer_and_mermaid_gates.Phase4RendererMetadataTests -v
```

Expected: PASS.

- [ ] **Step 5: Run existing renderer tests**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_render_markdown -v
```

Expected: PASS after updating any exact Mermaid fence assertions to include the metadata comment.

---

### Task 2: Shared Expected Diagram Collector

**Files:**
- Modify: `tests/test_v2_phase4_renderer_and_mermaid_gates.py`
- Create: `scripts/v2_phase4.py`

- [ ] **Step 1: Add failing expected collector tests**

Append these tests to `tests/test_v2_phase4_renderer_and_mermaid_gates.py`:

```python
class Phase4ExpectedDiagramCollectorTests(unittest.TestCase):
    def test_expected_collector_includes_existing_and_v2_diagram_paths(self):
        phase4 = load_script("scripts/v2_phase4.py", "v2_phase4_collector_under_test")
        diagrams = phase4.collect_expected_diagrams(valid_document())
        by_id = {diagram.diagram_id: diagram for diagram in diagrams if diagram.should_render}

        expected_paths = {
            "MER-ARCH-MODULES": "$.architecture_views.module_relationship_diagram",
            "MER-IFACE-SKILL-RENDER-CLI": "$.module_design.modules[0].public_interfaces.interfaces[1].execution_flow_diagram",
            "MER-IFACE-SKILL-VALIDATE-CLI": "$.module_design.modules[0].public_interfaces.interfaces[2].execution_flow_diagram",
            "MER-BLOCK-MECHANISM-FLOW": "$.module_design.modules[0].internal_mechanism.mechanism_details[0].blocks[1].diagram",
            "MER-RUNTIME-FLOW": "$.runtime_view.runtime_flow_diagram",
            "MER-COLLABORATION-RELATIONSHIP": "$.cross_module_collaboration.collaboration_relationship_diagram",
            "MER-FLOW-GENERATE": "$.key_flows.flows[0].diagram",
            "MER-BLOCK-STRUCTURE-ISSUES": "$.structure_issues_and_suggestions.blocks[1].diagram",
        }
        self.assertEqual(set(expected_paths), set(by_id))
        for diagram_id, json_path in expected_paths.items():
            self.assertEqual(json_path, by_id[diagram_id].json_path)
            self.assertTrue(by_id[diagram_id].source.strip())
            self.assertTrue(by_id[diagram_id].title.strip())

    def test_expected_collector_ignores_removed_v1_chapter_4_paths(self):
        phase4 = load_script("scripts/v2_phase4.py", "v2_phase4_removed_paths_under_test")
        document = valid_document()
        module = document["module_design"]["modules"][0]
        module["internal_structure"] = {
            "diagram": {
                "id": "MER-REMOVED-INTERNAL-STRUCTURE",
                "kind": "mermaid",
                "diagram_type": "flowchart",
                "title": "Removed",
                "description": "",
                "source": "flowchart TD\n  A --> B",
                "confidence": "observed",
            }
        }
        diagrams = phase4.collect_expected_diagrams(document)
        self.assertNotIn("MER-REMOVED-INTERNAL-STRUCTURE", {diagram.diagram_id for diagram in diagrams})

    def test_expected_collector_ignores_contract_interface_execution_flow_diagram(self):
        phase4 = load_script("scripts/v2_phase4.py", "v2_phase4_contract_interface_flow_under_test")
        document = valid_document()
        contract_interface = document["module_design"]["modules"][0]["public_interfaces"]["interfaces"][0]
        self.assertEqual("schema_contract", contract_interface["interface_type"])
        contract_interface["execution_flow_diagram"] = {
            "id": "MER-CONTRACT-SHOULD-NOT-RENDER",
            "kind": "mermaid",
            "diagram_type": "flowchart",
            "title": "Contract diagram should not render",
            "description": "",
            "source": "flowchart TD\n  A --> B",
            "confidence": "observed",
        }
        diagrams = phase4.collect_expected_diagrams(document)
        self.assertNotIn("MER-CONTRACT-SHOULD-NOT-RENDER", {diagram.diagram_id for diagram in diagrams})
```

- [ ] **Step 2: Run collector tests to verify they fail**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_v2_phase4_renderer_and_mermaid_gates.Phase4ExpectedDiagramCollectorTests -v
```

Expected: ERROR because `scripts/v2_phase4.py` does not exist yet.

- [ ] **Step 3: Implement the collector module skeleton**

Create `scripts/v2_phase4.py`:

```python
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
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, list):
        return len(value) > 0
    if isinstance(value, dict):
        return any(has_gated_content(child) for child in value.values())
    return True


def explicit_not_applicable_skip_reason(section):
    if not isinstance(section, dict):
        return ""
    reason = section.get("not_applicable_reason")
    content_values = [value for key, value in section.items() if key != "not_applicable_reason"]
    if isinstance(reason, str) and reason.strip() and not any(has_gated_content(value) for value in content_values):
        return reason.strip()
    return ""


def _append_diagram(records, diagram, path, owner_path, owner_section=None):
    reason = explicit_not_applicable_skip_reason(owner_section)
    record = _diagram_record(
        diagram,
        path,
        owner_path,
        should_render=not bool(reason),
        skip_reason=reason,
    )
    if record is not None:
        records.append(record)


def _append_diagram_array(records, diagrams, path, owner_path, owner_section=None):
    if not isinstance(diagrams, list):
        return
    for index, diagram in enumerate(diagrams):
        _append_diagram(records, diagram, f"{path}[{index}]", owner_path, owner_section=owner_section)
```

- [ ] **Step 4: Implement all Phase 4 collector paths**

Add `collect_expected_diagrams(document)` to `scripts/v2_phase4.py`:

```python
def collect_expected_diagrams(document):
    records = []
    if not isinstance(document, dict):
        return records

    architecture = document.get("architecture_views", {})
    if isinstance(architecture, dict):
        _append_diagram(
            records,
            architecture.get("module_relationship_diagram"),
            json_path("architecture_views", "module_relationship_diagram"),
            "$.architecture_views",
        )
        _append_diagram_array(
            records,
            architecture.get("extra_diagrams"),
            json_path("architecture_views", "extra_diagrams"),
            "$.architecture_views",
        )

    modules = document.get("module_design", {}).get("modules", [])
    if isinstance(modules, list):
        for module_index, module in enumerate(modules):
            if not isinstance(module, dict):
                continue
            public_interfaces = module.get("public_interfaces", {})
            interfaces = public_interfaces.get("interfaces", []) if isinstance(public_interfaces, dict) else []
            if isinstance(interfaces, list):
                for interface_index, interface in enumerate(interfaces):
                    if isinstance(interface, dict) and interface.get("interface_type") in EXECUTABLE_INTERFACE_TYPES:
                        _append_diagram(
                            records,
                            interface.get("execution_flow_diagram"),
                            json_path(
                                "module_design",
                                "modules",
                                module_index,
                                "public_interfaces",
                                "interfaces",
                                interface_index,
                                "execution_flow_diagram",
                            ),
                            json_path("module_design", "modules", module_index, "public_interfaces"),
                            owner_section=public_interfaces,
                        )
            internal_mechanism = module.get("internal_mechanism", {})
            details = internal_mechanism.get("mechanism_details", []) if isinstance(internal_mechanism, dict) else []
            if isinstance(details, list):
                for detail_index, detail in enumerate(details):
                    if not isinstance(detail, dict):
                        continue
                    blocks = detail.get("blocks", [])
                    if not isinstance(blocks, list):
                        continue
                    for block_index, block in enumerate(blocks):
                        if isinstance(block, dict) and block.get("block_type") == "diagram":
                            _append_diagram(
                                records,
                                block.get("diagram"),
                                json_path(
                                    "module_design",
                                    "modules",
                                    module_index,
                                    "internal_mechanism",
                                    "mechanism_details",
                                    detail_index,
                                    "blocks",
                                    block_index,
                                    "diagram",
                                ),
                                json_path("module_design", "modules", module_index, "internal_mechanism"),
                                owner_section=internal_mechanism,
                            )

    runtime = document.get("runtime_view", {})
    if isinstance(runtime, dict):
        _append_diagram(records, runtime.get("runtime_flow_diagram"), json_path("runtime_view", "runtime_flow_diagram"), "$.runtime_view")
        _append_diagram(records, runtime.get("runtime_sequence_diagram"), json_path("runtime_view", "runtime_sequence_diagram"), "$.runtime_view")
        _append_diagram_array(records, runtime.get("extra_diagrams"), json_path("runtime_view", "extra_diagrams"), "$.runtime_view")

    configuration = document.get("configuration_data_dependencies", {})
    if isinstance(configuration, dict):
        _append_diagram_array(
            records,
            configuration.get("extra_diagrams"),
            json_path("configuration_data_dependencies", "extra_diagrams"),
            "$.configuration_data_dependencies",
        )

    collaboration = document.get("cross_module_collaboration", {})
    if isinstance(collaboration, dict):
        _append_diagram(
            records,
            collaboration.get("collaboration_relationship_diagram"),
            json_path("cross_module_collaboration", "collaboration_relationship_diagram"),
            "$.cross_module_collaboration",
        )
        _append_diagram_array(
            records,
            collaboration.get("extra_diagrams"),
            json_path("cross_module_collaboration", "extra_diagrams"),
            "$.cross_module_collaboration",
        )

    key_flows = document.get("key_flows", {})
    if isinstance(key_flows, dict):
        flows = key_flows.get("flows", [])
        if isinstance(flows, list):
            for flow_index, flow in enumerate(flows):
                if isinstance(flow, dict):
                    _append_diagram(
                        records,
                        flow.get("diagram"),
                        json_path("key_flows", "flows", flow_index, "diagram"),
                        json_path("key_flows", "flows", flow_index),
                    )
        _append_diagram_array(records, key_flows.get("extra_diagrams"), json_path("key_flows", "extra_diagrams"), "$.key_flows")

    issues = document.get("structure_issues_and_suggestions")
    if isinstance(issues, dict):
        blocks = issues.get("blocks", [])
        if isinstance(blocks, list):
            for block_index, block in enumerate(blocks):
                if isinstance(block, dict) and block.get("block_type") == "diagram":
                    _append_diagram(
                        records,
                        block.get("diagram"),
                        json_path("structure_issues_and_suggestions", "blocks", block_index, "diagram"),
                        "$.structure_issues_and_suggestions",
                        owner_section=issues,
                    )

    return records
```

- [ ] **Step 5: Run collector tests**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_v2_phase4_renderer_and_mermaid_gates.Phase4ExpectedDiagramCollectorTests -v
```

Expected: PASS.

---

### Task 3: Mermaid Readability Review Artifact Validation

**Files:**
- Modify: `tests/test_v2_phase4_renderer_and_mermaid_gates.py`
- Modify: `scripts/v2_phase4.py`

- [ ] **Step 1: Add failing artifact validation tests**

Append:

```python
def complete_review_artifact(source_dsl, diagram_ids):
    return {
        "artifact_schema_version": "1.0",
        "reviewer": "independent_subagent",
        "source_dsl": str(source_dsl),
        "checked_diagram_ids": sorted(diagram_ids),
        "accepted_diagram_ids": sorted(diagram_ids),
        "revised_diagram_ids": [],
        "split_diagram_ids": [],
        "skipped_diagrams": [],
        "remaining_readability_risks": [],
    }


class Phase4ReadabilityArtifactTests(unittest.TestCase):
    def expected_ids(self):
        phase4 = load_script("scripts/v2_phase4.py", "v2_phase4_artifact_ids_under_test")
        return {diagram.diagram_id for diagram in phase4.collect_expected_diagrams(valid_document()) if diagram.should_render}

    def test_complete_artifact_validates(self):
        phase4 = load_script("scripts/v2_phase4.py", "v2_phase4_artifact_complete_under_test")
        artifact = complete_review_artifact(FIXTURE, self.expected_ids())
        errors = phase4.validate_mermaid_review_artifact(valid_document(), FIXTURE, artifact)
        self.assertEqual([], errors)

    def test_relative_source_dsl_resolves_against_artifact_directory(self):
        phase4 = load_script("scripts/v2_phase4.py", "v2_phase4_artifact_relative_source_under_test")
        with tempfile.TemporaryDirectory() as tmpdir:
            dsl_path = Path(tmpdir) / "structure.dsl.json"
            artifact_path = Path(tmpdir) / "mermaid-readability-review.json"
            artifact = complete_review_artifact("structure.dsl.json", self.expected_ids())
            errors = phase4.validate_mermaid_review_artifact(
                valid_document(),
                dsl_path,
                artifact,
                artifact_base_dir=artifact_path.parent,
            )
        self.assertEqual([], errors)

    def test_missing_artifact_is_error(self):
        phase4 = load_script("scripts/v2_phase4.py", "v2_phase4_artifact_missing_under_test")
        errors = phase4.validate_mermaid_review_artifact(valid_document(), FIXTURE, None)
        self.assertIn("readability review artifact is missing", "\n".join(errors))

    def test_mismatched_source_dsl_is_error(self):
        phase4 = load_script("scripts/v2_phase4.py", "v2_phase4_artifact_source_under_test")
        artifact = complete_review_artifact(ROOT / "other.dsl.json", self.expected_ids())
        errors = phase4.validate_mermaid_review_artifact(valid_document(), FIXTURE, artifact)
        self.assertIn("source_dsl does not match", "\n".join(errors))

    def test_malformed_source_dsl_type_is_error(self):
        phase4 = load_script("scripts/v2_phase4.py", "v2_phase4_artifact_bad_source_type_under_test")
        artifact = complete_review_artifact(FIXTURE, self.expected_ids())
        artifact["source_dsl"] = []
        errors = phase4.validate_mermaid_review_artifact(valid_document(), FIXTURE, artifact)
        self.assertIn("source_dsl must be a non-empty string", "\n".join(errors))

    def test_incomplete_coverage_is_error(self):
        phase4 = load_script("scripts/v2_phase4.py", "v2_phase4_artifact_incomplete_under_test")
        expected = self.expected_ids()
        missing = sorted(expected)[0]
        artifact = complete_review_artifact(FIXTURE, expected - {missing})
        errors = phase4.validate_mermaid_review_artifact(valid_document(), FIXTURE, artifact)
        self.assertIn(missing, "\n".join(errors))

    def test_skipped_diagram_requires_non_empty_reason(self):
        phase4 = load_script("scripts/v2_phase4.py", "v2_phase4_artifact_skip_reason_under_test")
        expected = self.expected_ids()
        skipped = sorted(expected)[0]
        artifact = complete_review_artifact(FIXTURE, expected - {skipped})
        artifact["skipped_diagrams"] = [{"diagram_id": skipped, "reason": "   "}]
        errors = phase4.validate_mermaid_review_artifact(valid_document(), FIXTURE, artifact)
        self.assertIn("skipped diagram must provide reason", "\n".join(errors))

    def test_rendered_diagram_cannot_be_skipped_by_review_artifact(self):
        phase4 = load_script("scripts/v2_phase4.py", "v2_phase4_artifact_skip_rendered_under_test")
        expected = self.expected_ids()
        skipped = sorted(expected)[0]
        artifact = complete_review_artifact(FIXTURE, expected - {skipped})
        artifact["skipped_diagrams"] = [{"diagram_id": skipped, "reason": "Reviewer chose not to review it."}]
        errors = phase4.validate_mermaid_review_artifact(valid_document(), FIXTURE, artifact)
        self.assertIn("cannot be skipped because its owning section is applicable", "\n".join(errors))

```

- [ ] **Step 2: Run artifact tests to verify they fail**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_v2_phase4_renderer_and_mermaid_gates.Phase4ReadabilityArtifactTests -v
```

Expected: FAIL because artifact validation does not exist yet.

- [ ] **Step 3: Implement artifact file helpers**

Add to `scripts/v2_phase4.py`:

```python
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
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise Phase4GateError(f"{label} is missing: {path}") from exc
    except OSError as exc:
        raise Phase4GateError(f"could not read {label} {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise Phase4GateError(f"malformed {label} JSON: {exc}") from exc


def normalize_path(value, base_dir=None):
    path = Path(value).expanduser()
    if not path.is_absolute() and base_dir is not None:
        path = Path(base_dir) / path
    return str(path.resolve(strict=False))
```

- [ ] **Step 4: Implement artifact validation**

Add:

```python
def _require_string_list(artifact, key, errors):
    value = artifact.get(key)
    if not isinstance(value, list) or not all(isinstance(item, str) and item.strip() for item in value):
        errors.append(f"{key} must be a list of non-empty strings")
        return set()
    return set(value)


def validate_mermaid_review_artifact(document, source_dsl_path, artifact, artifact_base_dir=None):
    if artifact is None:
        return ["readability review artifact is missing"]
    if not isinstance(artifact, dict):
        return ["readability review artifact must be a JSON object"]

    errors = []
    missing_keys = REVIEW_REQUIRED_KEYS - set(artifact)
    if missing_keys:
        errors.append("readability review artifact missing keys: " + ", ".join(sorted(missing_keys)))
        return errors
    if artifact.get("artifact_schema_version") != "1.0":
        errors.append("artifact_schema_version must be 1.0")
    if not isinstance(artifact.get("reviewer"), str) or not artifact["reviewer"].strip():
        errors.append("reviewer must be a non-empty string")
    source_dsl = artifact.get("source_dsl")
    if not isinstance(source_dsl, str) or not source_dsl.strip():
        errors.append("source_dsl must be a non-empty string")
    elif normalize_path(source_dsl, artifact_base_dir) != normalize_path(source_dsl_path):
        errors.append("source_dsl does not match the DSL input used for expected diagram collection")

    expected_records = collect_expected_diagrams(document)
    records_by_id = {record.diagram_id: record for record in expected_records}
    all_expected_ids = set(records_by_id)
    rendered_ids = {record.diagram_id for record in expected_records if record.should_render}
    skippable_ids = {record.diagram_id for record in expected_records if not record.should_render}

    checked_ids = _require_string_list(artifact, "checked_diagram_ids", errors)
    accepted_ids = _require_string_list(artifact, "accepted_diagram_ids", errors)
    revised_ids = _require_string_list(artifact, "revised_diagram_ids", errors)
    split_ids = _require_string_list(artifact, "split_diagram_ids", errors)

    skipped_ids = set()
    skipped = artifact.get("skipped_diagrams")
    if not isinstance(skipped, list):
        errors.append("skipped_diagrams must be a list")
    else:
        for index, item in enumerate(skipped):
            if not isinstance(item, dict):
                errors.append(f"skipped_diagrams[{index}] must be an object")
                continue
            diagram_id = item.get("diagram_id")
            reason = item.get("reason")
            if not isinstance(diagram_id, str) or not diagram_id.strip():
                errors.append(f"skipped_diagrams[{index}].diagram_id must be non-empty")
                continue
            if not isinstance(reason, str) or not reason.strip():
                errors.append(f"skipped diagram must provide reason: {diagram_id}")
            skipped_ids.add(diagram_id)

    covered_ids = checked_ids | skipped_ids
    missing_coverage = all_expected_ids - covered_ids
    if missing_coverage:
        errors.append("readability review artifact does not cover expected diagrams: " + ", ".join(sorted(missing_coverage)))

    unknown_checked = checked_ids - all_expected_ids
    if unknown_checked:
        errors.append("checked_diagram_ids contains unknown diagram IDs: " + ", ".join(sorted(unknown_checked)))
    unknown_skipped = skipped_ids - all_expected_ids
    if unknown_skipped:
        errors.append("skipped_diagrams contains unknown diagram IDs: " + ", ".join(sorted(unknown_skipped)))
    invalid_skips = skipped_ids & rendered_ids
    if invalid_skips:
        errors.append(
            "skipped_diagrams contains diagram IDs that cannot be skipped because their owning section is applicable: "
            + ", ".join(sorted(invalid_skips))
        )
    missing_skip_reason_for_collector = {
        diagram_id
        for diagram_id in skipped_ids & skippable_ids
        if not records_by_id[diagram_id].skip_reason
    }
    if missing_skip_reason_for_collector:
        errors.append(
            "skipped_diagrams contains IDs without an explicitly not-applicable owning section: "
            + ", ".join(sorted(missing_skip_reason_for_collector))
        )

    reviewed_ids = accepted_ids | revised_ids | split_ids
    unknown_reviewed = reviewed_ids - checked_ids
    derived_split_ids = {item for item in unknown_reviewed if any(item.startswith(f"{checked}::") for checked in checked_ids)}
    unresolved_reviewed = unknown_reviewed - derived_split_ids
    if unresolved_reviewed:
        errors.append("accepted/revised/split IDs must refer to checked diagrams: " + ", ".join(sorted(unresolved_reviewed)))

    remaining_risks = artifact.get("remaining_readability_risks")
    if not isinstance(remaining_risks, list):
        errors.append("remaining_readability_risks must be a list")
    return errors
```

- [ ] **Step 5: Run artifact tests**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_v2_phase4_renderer_and_mermaid_gates.Phase4ReadabilityArtifactTests -v
```

Expected: PASS.

---

### Task 4: Rendered Diagram Completeness Check

**Files:**
- Modify: `tests/test_v2_phase4_renderer_and_mermaid_gates.py`
- Modify: `scripts/v2_phase4.py`

- [ ] **Step 1: Add failing rendered completeness tests**

Append:

```python
class Phase4RenderedCompletenessTests(unittest.TestCase):
    def test_rendered_completeness_passes_for_renderer_output(self):
        renderer = load_script("scripts/render_markdown.py", "render_markdown_phase4_complete_under_test")
        phase4 = load_script("scripts/v2_phase4.py", "v2_phase4_complete_under_test")
        markdown = renderer.render_markdown(valid_document())
        errors = phase4.rendered_diagram_completeness_errors(valid_document(), markdown)
        self.assertEqual([], errors)

    def test_rendered_completeness_catches_missing_interface_diagram(self):
        renderer = load_script("scripts/render_markdown.py", "render_markdown_phase4_missing_iface_under_test")
        phase4 = load_script("scripts/v2_phase4.py", "v2_phase4_missing_iface_under_test")
        markdown = renderer.render_markdown(valid_document()).replace(
            "<!-- diagram-id: MER-IFACE-SKILL-RENDER-CLI -->\n```mermaid",
            "```mermaid",
            1,
        )
        errors = phase4.rendered_diagram_completeness_errors(valid_document(), markdown)
        rendered = "\n".join(errors)
        self.assertIn("MER-IFACE-SKILL-RENDER-CLI", rendered)
        self.assertIn("$.module_design.modules[0].public_interfaces.interfaces[1].execution_flow_diagram", rendered)

    def test_rendered_completeness_catches_missing_internal_mechanism_diagram(self):
        renderer = load_script("scripts/render_markdown.py", "render_markdown_phase4_missing_mech_under_test")
        phase4 = load_script("scripts/v2_phase4.py", "v2_phase4_missing_mech_under_test")
        markdown = renderer.render_markdown(valid_document()).replace("MER-BLOCK-MECHANISM-FLOW", "MER-WRONG-TITLE-ONLY", 1)
        errors = phase4.rendered_diagram_completeness_errors(valid_document(), markdown)
        self.assertIn("MER-BLOCK-MECHANISM-FLOW", "\n".join(errors))

    def test_rendered_completeness_catches_missing_chapter_9_diagram(self):
        renderer = load_script("scripts/render_markdown.py", "render_markdown_phase4_missing_ch9_under_test")
        phase4 = load_script("scripts/v2_phase4.py", "v2_phase4_missing_ch9_under_test")
        markdown = renderer.render_markdown(valid_document()).replace("MER-BLOCK-STRUCTURE-ISSUES", "MER-TITLE-MATCH-ONLY", 1)
        errors = phase4.rendered_diagram_completeness_errors(valid_document(), markdown)
        self.assertIn("MER-BLOCK-STRUCTURE-ISSUES", "\n".join(errors))

    def test_rendered_completeness_rejects_duplicate_metadata(self):
        renderer = load_script("scripts/render_markdown.py", "render_markdown_phase4_duplicate_meta_under_test")
        phase4 = load_script("scripts/v2_phase4.py", "v2_phase4_duplicate_meta_under_test")
        markdown = renderer.render_markdown(valid_document())
        markdown = markdown.replace("<!-- diagram-id: MER-RUNTIME-FLOW -->", "<!-- diagram-id: MER-ARCH-MODULES -->", 1)
        errors = phase4.rendered_diagram_completeness_errors(valid_document(), markdown)
        self.assertIn("appears 2 times", "\n".join(errors))

    def test_rendered_completeness_ignores_mermaid_text_inside_longer_source_snippet_fence(self):
        renderer = load_script("scripts/render_markdown.py", "render_markdown_phase4_snippet_under_test")
        phase4 = load_script("scripts/v2_phase4.py", "v2_phase4_snippet_under_test")
        document = valid_document()
        document["evidence"] = [
            {"id": "EV-SNIP", "kind": "source", "title": "Snippet", "location": "test", "description": "snippet", "confidence": "observed"}
        ]
        document["source_snippets"] = [
            {
                "id": "SNIP-MERMAID-TEXT",
                "path": "README.md",
                "line_start": 1,
                "line_end": 4,
                "language": "markdown",
                "purpose": "Proves nested mermaid-looking text is only evidence.",
                "content": "````markdown\n```mermaid\nflowchart TD\n  X --> Y\n```\n````",
                "confidence": "observed",
            }
        ]
        document["module_design"]["modules"][0]["evidence_refs"] = ["EV-SNIP"]
        document["module_design"]["modules"][0]["source_snippet_refs"] = ["SNIP-MERMAID-TEXT"]
        markdown = renderer.render_markdown(document, evidence_mode="inline")
        errors = phase4.rendered_diagram_completeness_errors(document, markdown)
        self.assertEqual([], errors)
```

- [ ] **Step 2: Run completeness tests to verify they fail**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_v2_phase4_renderer_and_mermaid_gates.Phase4RenderedCompletenessTests -v
```

Expected: FAIL because rendered completeness helpers do not exist yet.

- [ ] **Step 3: Implement rendered metadata extraction**

Add to `scripts/v2_phase4.py`:

```python
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
        if closing and closing.group(1)[0] == opening_marker[0] and len(closing.group(1)) >= len(opening_marker):
            in_fence = False
            opening_marker = ""
    return records, mermaid_fence_count
```

- [ ] **Step 4: Implement completeness errors**

Add:

```python
def rendered_diagram_completeness_errors(document, markdown_text):
    errors = []
    expected_records = [record for record in collect_expected_diagrams(document) if record.should_render]
    expected_by_id = {record.diagram_id: record for record in expected_records}
    rendered_records, mermaid_fence_count = extract_rendered_mermaid_metadata(markdown_text)

    if mermaid_fence_count < len(expected_records):
        errors.append(
            f"rendered Mermaid fence count {mermaid_fence_count} is less than expected diagram count {len(expected_records)}"
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
```

- [ ] **Step 5: Run completeness tests**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_v2_phase4_renderer_and_mermaid_gates.Phase4RenderedCompletenessTests -v
```

Expected: PASS.

---

### Task 5: Strict Phase 4 Verification Workflow Script

**Files:**
- Modify: `tests/test_v2_phase4_renderer_and_mermaid_gates.py`
- Create: `scripts/verify_v2_mermaid_gates.py`

- [ ] **Step 1: Add failing workflow CLI tests**

Append:

```python
class Phase4VerificationWorkflowTests(unittest.TestCase):
    def write_complete_artifact(self, tmpdir, dsl_path, document):
        phase4 = load_script("scripts/v2_phase4.py", "v2_phase4_workflow_artifact_under_test")
        expected_ids = {diagram.diagram_id for diagram in phase4.collect_expected_diagrams(document) if diagram.should_render}
        artifact = complete_review_artifact(dsl_path, expected_ids)
        return write_json(tmpdir, "mermaid-readability-review.json", artifact)

    def test_missing_review_artifact_fails_workflow(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            dsl_path = write_json(tmpdir, "structure.dsl.json", document)
            markdown_path = write_text(tmpdir, "rendered.md", "")
            completed = subprocess.run(
                [
                    PYTHON,
                    str(ROOT / "scripts/verify_v2_mermaid_gates.py"),
                    str(dsl_path),
                    "--mermaid-review-artifact",
                    str(Path(tmpdir) / "missing.json"),
                    "--rendered-markdown",
                    str(markdown_path),
                    "--post-render",
                    "--work-dir",
                    str(Path(tmpdir) / "mermaid-work"),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(2, completed.returncode)
        self.assertIn("readability review artifact is missing", completed.stderr)

    def test_incomplete_review_artifact_fails_workflow_before_mermaid_cli(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            dsl_path = write_json(tmpdir, "structure.dsl.json", document)
            artifact_path = write_json(tmpdir, "mermaid-readability-review.json", complete_review_artifact(dsl_path, set()))
            renderer = load_script("scripts/render_markdown.py", "render_markdown_workflow_incomplete_under_test")
            markdown_path = write_text(tmpdir, "rendered.md", renderer.render_markdown(document))
            completed = subprocess.run(
                [
                    PYTHON,
                    str(ROOT / "scripts/verify_v2_mermaid_gates.py"),
                    str(dsl_path),
                    "--mermaid-review-artifact",
                    str(artifact_path),
                    "--rendered-markdown",
                    str(markdown_path),
                    "--post-render",
                    "--work-dir",
                    str(Path(tmpdir) / "mermaid-work"),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(1, completed.returncode)
        self.assertIn("does not cover expected diagrams", completed.stderr)

    def test_rendered_completeness_failure_blocks_post_render_strict_validation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            dsl_path = write_json(tmpdir, "structure.dsl.json", document)
            artifact_path = self.write_complete_artifact(tmpdir, dsl_path, document)
            renderer = load_script("scripts/render_markdown.py", "render_markdown_workflow_missing_meta_under_test")
            markdown = renderer.render_markdown(document).replace("<!-- diagram-id: MER-FLOW-GENERATE -->\n", "", 1)
            markdown_path = write_text(tmpdir, "rendered.md", markdown)
            completed = subprocess.run(
                [
                    PYTHON,
                    str(ROOT / "scripts/verify_v2_mermaid_gates.py"),
                    str(dsl_path),
                    "--mermaid-review-artifact",
                    str(artifact_path),
                    "--rendered-markdown",
                    str(markdown_path),
                    "--post-render",
                    "--work-dir",
                    str(Path(tmpdir) / "mermaid-work"),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(1, completed.returncode)
        self.assertIn("MER-FLOW-GENERATE", completed.stderr)

    def test_v1_dsl_rejected_before_artifact_gate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            document["dsl_version"] = "0.1.0"
            dsl_path = write_json(tmpdir, "structure.dsl.json", document)
            completed = subprocess.run(
                [
                    PYTHON,
                    str(ROOT / "scripts/verify_v2_mermaid_gates.py"),
                    str(dsl_path),
                    "--mermaid-review-artifact",
                    str(Path(tmpdir) / "missing-artifact.json"),
                    "--pre-render",
                    "--work-dir",
                    str(Path(tmpdir) / "mermaid-work"),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(2, completed.returncode)
        self.assertIn("V1 DSL is not supported", completed.stderr)
        self.assertNotIn("readability review artifact is missing", completed.stderr)

    def test_not_applicable_contradiction_rejected_before_artifact_gate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            document["structure_issues_and_suggestions"]["not_applicable_reason"] = "结构问题章节不适用。"
            dsl_path = write_json(tmpdir, "structure.dsl.json", document)
            artifact_path = self.write_complete_artifact(tmpdir, dsl_path, valid_document())
            completed = subprocess.run(
                [
                    PYTHON,
                    str(ROOT / "scripts/verify_v2_mermaid_gates.py"),
                    str(dsl_path),
                    "--mermaid-review-artifact",
                    str(artifact_path),
                    "--pre-render",
                    "--work-dir",
                    str(Path(tmpdir) / "mermaid-work"),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(1, completed.returncode)
        self.assertIn("cannot provide both content and not_applicable_reason", completed.stderr)
        self.assertNotIn("strict mode", completed.stdout)

    def test_pre_render_invokes_existing_dsl_strict_validator_after_artifact_gate(self):
        workflow = load_script("scripts/verify_v2_mermaid_gates.py", "verify_v2_mermaid_gates_pre_render_under_test")
        document = valid_document()
        with tempfile.TemporaryDirectory() as tmpdir:
            dsl_path = write_json(tmpdir, "structure.dsl.json", document)
            artifact_path = self.write_complete_artifact(tmpdir, dsl_path, document)
            with mock.patch.object(workflow.subprocess, "run") as run_validate:
                run_validate.return_value = subprocess.CompletedProcess(
                    ["validate_mermaid.py"],
                    0,
                    stdout="Mermaid validation succeeded: 6 diagram(s) checked in strict mode.\n",
                    stderr="",
                )
                code, stdout, stderr = call_main(
                    workflow,
                    [
                        str(dsl_path),
                        "--mermaid-review-artifact",
                        str(artifact_path),
                        "--pre-render",
                        "--work-dir",
                        str(Path(tmpdir) / "mermaid-work"),
                    ],
                )
        self.assertEqual(0, code, stderr)
        self.assertIn("strict mode", stdout)
        argv = run_validate.call_args.args[0]
        self.assertIn("--from-dsl", argv)
        self.assertIn(str(dsl_path), argv)
        self.assertIn("--strict", argv)
        self.assertIn(str(Path(tmpdir) / "mermaid-work" / "pre-render"), argv)
```

- [ ] **Step 2: Run workflow tests to verify they fail**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_v2_phase4_renderer_and_mermaid_gates.Phase4VerificationWorkflowTests -v
```

Expected: ERROR because `scripts/verify_v2_mermaid_gates.py` does not exist yet.

- [ ] **Step 3: Implement the workflow parser and file loading**

Create `scripts/verify_v2_mermaid_gates.py`:

```python
#!/usr/bin/env python3
import argparse
import json
import subprocess
import sys
from pathlib import Path

try:
    from v2_phase4 import (
        Phase4GateError,
        load_json_file,
        rendered_diagram_completeness_errors,
        validate_mermaid_review_artifact,
    )
except ModuleNotFoundError:
    from scripts.v2_phase4 import (
        Phase4GateError,
        load_json_file,
        rendered_diagram_completeness_errors,
        validate_mermaid_review_artifact,
    )

try:
    from v2_foundation import V2_VERSION_ERROR, require_v2_dsl_version, v2_global_rule_violations
except ModuleNotFoundError:
    from scripts.v2_foundation import V2_VERSION_ERROR, require_v2_dsl_version, v2_global_rule_violations


ROOT = Path(__file__).resolve().parents[1]


def build_parser():
    parser = argparse.ArgumentParser(description="Verify V2 Mermaid readability and rendered completeness gates.")
    parser.add_argument("dsl_file", help="Path to structure DSL JSON.")
    parser.add_argument("--mermaid-review-artifact", required=True, help="Path to Mermaid readability review JSON artifact.")
    parser.add_argument("--rendered-markdown", help="Path to rendered Markdown for post-render gates.")
    phase = parser.add_mutually_exclusive_group(required=True)
    phase.add_argument("--pre-render", action="store_true", help="Validate artifact and run pre-render strict DSL Mermaid validation.")
    phase.add_argument("--post-render", action="store_true", help="Validate artifact, rendered completeness, and strict rendered Markdown Mermaid validation.")
    parser.add_argument("--work-dir", required=True, help="Directory for strict Mermaid validation artifacts.")
    return parser


def load_text_file(path):
    try:
        return Path(path).read_text(encoding="utf-8")
    except OSError as exc:
        raise Phase4GateError(f"could not read rendered Markdown {path}: {exc}") from exc
```

- [ ] **Step 4: Implement artifact gate and strict-validator invocation**

Add:

```python
def print_errors(errors):
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)


def validate_dsl_gate(document):
    try:
        require_v2_dsl_version(document)
    except ValueError:
        print(f"ERROR: {V2_VERSION_ERROR}", file=sys.stderr)
        return 2
    violations = v2_global_rule_violations(document)
    if violations:
        print_errors([violation.message for violation in violations])
        return 1
    return 0


def validate_artifact_gate(document, dsl_file, artifact_path):
    artifact_path = Path(artifact_path)
    artifact = load_json_file(artifact_path, label="readability review artifact")
    errors = validate_mermaid_review_artifact(
        document,
        dsl_file,
        artifact,
        artifact_base_dir=artifact_path.parent,
    )
    if errors:
        print_errors(errors)
        return 1
    return 0


def run_validate_mermaid(args):
    completed = subprocess.run(
        [sys.executable, str(ROOT / "scripts/validate_mermaid.py"), *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.stdout:
        print(completed.stdout, end="")
    if completed.stderr:
        print(completed.stderr, end="", file=sys.stderr)
    return completed.returncode


def pre_render_gate(dsl_file, work_dir):
    return run_validate_mermaid(
        [
            "--from-dsl",
            str(dsl_file),
            "--strict",
            "--work-dir",
            str(Path(work_dir) / "pre-render"),
        ]
    )


def post_render_gate(document, rendered_markdown, work_dir):
    markdown_text = load_text_file(rendered_markdown)
    completeness = rendered_diagram_completeness_errors(document, markdown_text)
    if completeness:
        print_errors(completeness)
        return 1
    return run_validate_mermaid(
        [
            "--from-markdown",
            str(rendered_markdown),
            "--strict",
            "--work-dir",
            str(Path(work_dir) / "post-render"),
        ]
    )
```

- [ ] **Step 5: Implement `main()`**

Add:

```python
def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.post_render and not args.rendered_markdown:
        parser.error("--post-render requires --rendered-markdown")

    dsl_file = Path(args.dsl_file)
    try:
        document = load_json_file(dsl_file, label="DSL input")
        dsl_code = validate_dsl_gate(document)
        if dsl_code:
            return dsl_code
        artifact_code = validate_artifact_gate(document, dsl_file, args.mermaid_review_artifact)
        if artifact_code:
            return artifact_code
        if args.pre_render:
            return pre_render_gate(dsl_file, args.work_dir)
        return post_render_gate(document, Path(args.rendered_markdown), args.work_dir)
    except Phase4GateError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 6: Run workflow tests**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_v2_phase4_renderer_and_mermaid_gates.Phase4VerificationWorkflowTests -v
```

Expected: PASS for failure-mode tests without requiring local `mmdc`.

---

### Task 6: Strict Rendered Markdown Validation With V2 Local Diagrams

**Files:**
- Modify: `tests/test_v2_phase4_renderer_and_mermaid_gates.py`
- Modify: `scripts/verify_v2_mermaid_gates.py`
- Verify only: `scripts/validate_mermaid.py`

- [ ] **Step 1: Add mocked strict validation orchestration tests**

Append:

```python
class Phase4StrictRenderedMarkdownTests(unittest.TestCase):
    def test_post_render_strict_validates_local_interface_and_content_block_diagrams(self):
        workflow = load_script("scripts/verify_v2_mermaid_gates.py", "verify_v2_mermaid_gates_strict_under_test")
        renderer = load_script("scripts/render_markdown.py", "render_markdown_strict_post_under_test")
        document = valid_document()
        markdown = renderer.render_markdown(document)

        with tempfile.TemporaryDirectory() as tmpdir:
            dsl_path = write_json(tmpdir, "structure.dsl.json", document)
            phase4 = load_script("scripts/v2_phase4.py", "v2_phase4_strict_artifact_under_test")
            expected_ids = {diagram.diagram_id for diagram in phase4.collect_expected_diagrams(document) if diagram.should_render}
            artifact_path = write_json(tmpdir, "mermaid-readability-review.json", complete_review_artifact(dsl_path, expected_ids))
            markdown_path = write_text(tmpdir, "rendered.md", markdown)
            with mock.patch.object(workflow.subprocess, "run") as run_validate:
                run_validate.return_value = subprocess.CompletedProcess(
                    ["validate_mermaid.py"],
                    0,
                    stdout="Mermaid validation succeeded: 8 diagram(s) checked in strict mode.\n",
                    stderr="",
                )
                code, stdout, stderr = call_main(
                    workflow,
                    [
                        str(dsl_path),
                        "--mermaid-review-artifact",
                        str(artifact_path),
                        "--rendered-markdown",
                        str(markdown_path),
                        "--post-render",
                        "--work-dir",
                        str(Path(tmpdir) / "mermaid-work"),
                    ],
                )

        self.assertEqual(0, code, stderr)
        self.assertIn("strict mode", stdout)
        self.assertEqual("", stderr)
        self.assertEqual(1, run_validate.call_count)
        argv = run_validate.call_args.args[0]
        self.assertIn("--from-markdown", argv)
        self.assertIn(str(markdown_path), argv)
        self.assertIn("--strict", argv)
        self.assertIn("--work-dir", argv)
```

- [ ] **Step 2: Run mocked strict test**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_v2_phase4_renderer_and_mermaid_gates.Phase4StrictRenderedMarkdownTests -v
```

Expected: PASS.

- [ ] **Step 3: Add a real strict validation test that skips when CLI is unavailable**

Add a real local-tooling test:

```python
class Phase4RealStrictRenderedMarkdownTests(unittest.TestCase):
    def test_rendered_markdown_passes_real_strict_validation_when_cli_available(self):
        import shutil

        if shutil.which("node") is None or shutil.which("mmdc") is None:
            self.skipTest("node or mmdc unavailable")

        renderer = load_script("scripts/render_markdown.py", "render_markdown_real_strict_under_test")
        document = valid_document()
        with tempfile.TemporaryDirectory() as tmpdir:
            dsl_path = write_json(tmpdir, "structure.dsl.json", document)
            phase4 = load_script("scripts/v2_phase4.py", "v2_phase4_real_strict_artifact_under_test")
            expected_ids = {diagram.diagram_id for diagram in phase4.collect_expected_diagrams(document) if diagram.should_render}
            artifact_path = write_json(tmpdir, "mermaid-readability-review.json", complete_review_artifact(dsl_path, expected_ids))
            markdown_path = write_text(tmpdir, document["document"]["output_file"], renderer.render_markdown(document))
            completed = subprocess.run(
                [
                    PYTHON,
                    str(ROOT / "scripts/verify_v2_mermaid_gates.py"),
                    str(dsl_path),
                    "--mermaid-review-artifact",
                    str(artifact_path),
                    "--rendered-markdown",
                    str(markdown_path),
                    "--post-render",
                    "--work-dir",
                    str(Path(tmpdir) / "mermaid-work"),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(0, completed.returncode, completed.stderr)
```

- [ ] **Step 4: Run strict rendered tests**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_v2_phase4_renderer_and_mermaid_gates.Phase4StrictRenderedMarkdownTests tests.test_v2_phase4_renderer_and_mermaid_gates.Phase4RealStrictRenderedMarkdownTests -v
```

Expected: mocked strict test passes; real strict test passes when `node`/`mmdc` are available and skips otherwise.

---

### Task 7: Existing Test Suite And E2E Updates

**Files:**
- Modify: `tests/test_render_markdown.py`
- Modify: `tests/test_validate_mermaid.py`
- Modify: `tests/test_phase7_e2e.py`

- [ ] **Step 1: Update existing renderer expectations**

In `tests/test_render_markdown.py`, update exact assertions that currently expect raw Mermaid fences. For example, replace checks like:

```python
self.assertIn("```mermaid\nflowchart TD", markdown)
```

with:

```python
self.assertIn("<!-- diagram-id: MER-ARCH-MODULES -->\n```mermaid\nflowchart TD", markdown)
```

When an assertion is not tied to a specific diagram ID, use both checks:

```python
self.assertIn("<!-- diagram-id:", markdown)
self.assertIn("```mermaid\nflowchart TD", markdown)
```

- [ ] **Step 2: Add a renderer fail-fast regression for unsafe diagram IDs**

Add to `tests/test_render_markdown.py`:

```python
class RendererPhase4DiagramMetadataTests(unittest.TestCase):
    def test_renderer_rejects_unsafe_diagram_id_metadata_comment(self):
        module = load_renderer_module()
        document = valid_document()
        document["architecture_views"]["module_relationship_diagram"]["id"] = "MER-BAD--COMMENT"
        with self.assertRaisesRegex(module.RenderError, "unsafe Mermaid diagram id"):
            module.render_markdown(document)
```

- [ ] **Step 3: Update Mermaid workflow documentation tests without changing the validator**

In `tests/test_validate_mermaid.py`, update `WORKFLOW_ORDER` to reflect the Phase 4 workflow:

```python
WORKFLOW_ORDER = [
    "Create a temporary work directory.",
    "Write one complete DSL JSON file",
    "python scripts/validate_dsl.py <temporary-work-directory>/structure.dsl.json",
    "Dispatch an independent Mermaid readability review",
    "mermaid-readability-review.json",
    "python scripts/verify_v2_mermaid_gates.py <temporary-work-directory>/structure.dsl.json --mermaid-review-artifact <temporary-work-directory>/mermaid-readability-review.json --pre-render --work-dir <temporary-work-directory>/mermaid",
    "python scripts/render_markdown.py <temporary-work-directory>/structure.dsl.json --output-dir",
    "python scripts/verify_v2_mermaid_gates.py <temporary-work-directory>/structure.dsl.json --mermaid-review-artifact <temporary-work-directory>/mermaid-readability-review.json --rendered-markdown <output-file> --post-render --work-dir <temporary-work-directory>/mermaid",
    "references/review-checklist.md",
    "Report output path",
]
```

Keep tests that exercise `scripts/validate_mermaid.py` focused on the current CLI. Do not add a `--mermaid-review-artifact` expectation to `scripts/validate_mermaid.py`.

Replace `SkillBodyContractTests.test_mermaid_strict_and_static_acceptance_rule_is_visible` with:

```python
def test_mermaid_phase4_strict_gate_rule_is_visible(self):
    self.assertIn("Strict Mermaid validation is the default", self.text)
    self.assertIn("Mermaid readability artifact is workflow metadata", self.text)
    self.assertIn("Every rendered Mermaid fence must have an adjacent", self.text)
    self.assertIn("Static-only Mermaid validation is not final acceptance for V2 Phase 4", self.text)
    self.assertNotIn("user explicitly accepts static-only validation", self.text)
```

In `tests/test_phase7_e2e.py`, update `Phase7ReferenceDocumentationTests.SKILL_WORKFLOW_PHRASES` to remove the old direct `validate_mermaid.py --from-dsl ... --strict` and `validate_mermaid.py --from-markdown ... --static` workflow entries. Use:

```python
SKILL_WORKFLOW_PHRASES = [
    "Create a temporary work directory.",
    "Read references/dsl-spec.md before writing DSL content.",
    "Write one complete DSL JSON file at `<temporary-work-directory>/structure.dsl.json`.",
    "Run `python scripts/validate_dsl.py <temporary-work-directory>/structure.dsl.json`.",
    "Read references/mermaid-rules.md before creating/revising Mermaid.",
    "Dispatch an independent subagent to review every expected Mermaid diagram for readability.",
    "mermaid-readability-review.json",
    "Run `python scripts/verify_v2_mermaid_gates.py <temporary-work-directory>/structure.dsl.json --mermaid-review-artifact <temporary-work-directory>/mermaid-readability-review.json --pre-render --work-dir <temporary-work-directory>/mermaid`.",
    "Render exactly one document with `python scripts/render_markdown.py <temporary-work-directory>/structure.dsl.json --output-dir <output-dir>`.",
    "Run `python scripts/verify_v2_mermaid_gates.py <temporary-work-directory>/structure.dsl.json --mermaid-review-artifact <temporary-work-directory>/mermaid-readability-review.json --rendered-markdown <output-file> --post-render --work-dir <temporary-work-directory>/mermaid`.",
    "Review with references/review-checklist.md.",
    "Report output path, temporary work directory, assumptions, low-confidence items, Mermaid readability artifact path, rendered diagram completeness status, and strict rendered Markdown validation status.",
    "Static-only Mermaid validation is not final acceptance for V2 Phase 4.",
    "references/dsl-spec.md",
    "references/document-structure.md",
    "references/mermaid-rules.md",
    "references/review-checklist.md",
]
```

Also update the real stale documentation expectations:

- In `Phase7ReferenceDocumentationTests.REQUIRED_PHRASES["references/review-checklist.md"]`, replace the old static-only fallback-reporting phrase with `Mermaid readability artifact`, `rendered diagram completeness`, and `strict rendered Markdown validation`.
- In `tests/test_validate_mermaid.py`, replace `MermaidIntegrationRegressionTests.test_review_checklist_keeps_strict_or_static_acceptance_boundary_visible` with a Phase 4 assertion that requires strict validation, readability artifact coverage, rendered completeness, and the phrase `Static-only Mermaid validation is not final acceptance`.

- [ ] **Step 4: Update Phase 7 example workflow tests**

In `tests/test_phase7_e2e.py`, update helper flow:

```python
def write_phase4_review_artifact(self, dsl_path, document, run_dir):
    phase4 = load_script_module("scripts/v2_phase4.py", "phase7_v2_phase4_under_test")
    expected_ids = {diagram.diagram_id for diagram in phase4.collect_expected_diagrams(document) if diagram.should_render}
    artifact = {
        "artifact_schema_version": "1.0",
        "reviewer": "independent_subagent",
        "source_dsl": str(dsl_path),
        "checked_diagram_ids": sorted(expected_ids),
        "accepted_diagram_ids": sorted(expected_ids),
        "revised_diagram_ids": [],
        "split_diagram_ids": [],
        "skipped_diagrams": [],
        "remaining_readability_risks": [],
    }
    artifact_path = run_dir / "mermaid-readability-review.json"
    artifact_path.write_text(json.dumps(artifact, ensure_ascii=False, indent=2), encoding="utf-8")
    return artifact_path
```

After rendering in the static workflow, assert metadata and completeness without claiming strict success:

```python
phase4 = load_script_module("scripts/v2_phase4.py", "phase7_v2_phase4_completeness_under_test")
self.assertEqual([], phase4.rendered_diagram_completeness_errors(document, markdown))
self.assertIn("<!-- diagram-id:", markdown)
```

For strict orchestration tests that mock Mermaid CLI availability, use `scripts/verify_v2_mermaid_gates.py --post-render` and assert the mocked call uses `validate_mermaid.py --from-markdown <output-file> --strict`.

- [ ] **Step 5: Run updated test groups**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_render_markdown tests.test_validate_mermaid tests.test_phase7_e2e -v
```

Expected: PASS, with real strict Mermaid tests skipped when local CLI tooling is unavailable.

---

### Task 8: Skill And Reference Documentation Updates

**Files:**
- Modify: `SKILL.md`
- Modify: `references/dsl-spec.md`
- Modify: `references/document-structure.md`
- Modify: `references/review-checklist.md`

- [ ] **Step 1: Update `SKILL.md` workflow**

Replace the Mermaid workflow portion with this order:

```markdown
3. Write one complete DSL JSON file at `<temporary-work-directory>/structure.dsl.json`.
4. Run `python scripts/validate_dsl.py <temporary-work-directory>/structure.dsl.json`.
5. Read references/mermaid-rules.md before creating/revising Mermaid.
6. Dispatch an independent subagent to review every expected Mermaid diagram for readability. Save the JSON artifact as `<temporary-work-directory>/mermaid-readability-review.json`.
7. Run `python scripts/verify_v2_mermaid_gates.py <temporary-work-directory>/structure.dsl.json --mermaid-review-artifact <temporary-work-directory>/mermaid-readability-review.json --pre-render --work-dir <temporary-work-directory>/mermaid`.
8. Render exactly one document with `python scripts/render_markdown.py <temporary-work-directory>/structure.dsl.json --output-dir <output-dir>`. Evidence support blocks are hidden by default; use `--evidence-mode inline` only when the user explicitly asks to preserve inline support data in final Markdown.
9. Run `python scripts/verify_v2_mermaid_gates.py <temporary-work-directory>/structure.dsl.json --mermaid-review-artifact <temporary-work-directory>/mermaid-readability-review.json --rendered-markdown <output-file> --post-render --work-dir <temporary-work-directory>/mermaid`.
10. Review with references/review-checklist.md.
11. Report output path, temporary work directory, assumptions, low-confidence items, Mermaid readability artifact path, rendered diagram completeness status, and strict rendered Markdown validation status.
```

Also add:

```markdown
The Mermaid readability artifact is workflow metadata. Do not store it inside DSL JSON and do not render it into final Markdown.
The artifact `source_dsl` value must identify the same DSL path passed to `verify_v2_mermaid_gates.py`; prefer `<temporary-work-directory>/structure.dsl.json` or an absolute path.
Every rendered Mermaid fence must have an adjacent `<!-- diagram-id: ... -->` comment immediately before the fence.
Static-only Mermaid validation is not final acceptance for V2 Phase 4.
```

- [ ] **Step 2: Update `references/dsl-spec.md`**

Add a section:

```markdown
## Expected Mermaid Diagram Paths

The Phase 4 expected diagram collector gathers present Mermaid diagram objects from these DSL paths: architecture relationship and extra diagrams, runtime flow/sequence/extra diagrams, configuration extra diagrams, collaboration relationship/extra diagrams, key-flow diagrams and extra diagrams, executable public interface execution flow diagrams, internal mechanism diagram content blocks, and Chapter 9 diagram content blocks.

Removed V1 Chapter 4 diagram paths are not V2 inputs: `module_design.modules[].internal_structure.diagram`, `module_design.modules[].external_capability_details.extra_diagrams[]`, and `module_design.modules[].extra_diagrams[]`.

Mermaid readability review artifacts are workflow metadata. They are not DSL fields.
```

- [ ] **Step 3: Update `references/document-structure.md`**

Add:

```markdown
Every rendered Mermaid fence is preceded immediately by `<!-- diagram-id: MER-... -->`. The comment is structural Markdown source metadata, not evidence support data, and it renders regardless of `--evidence-mode`.

Rendered diagram completeness checks match expected DSL diagram IDs to these metadata comments. Title-only matches do not count.
```

- [ ] **Step 4: Update `references/review-checklist.md`**

Add checks under Mermaid Validation:

```markdown
- Confirm an independent Mermaid readability review artifact was produced before strict validation.
- Confirm the artifact covers every expected DSL diagram ID or gives a non-empty skipped reason for an explicitly not-applicable owning section.
- Confirm every Mermaid fence in rendered Markdown has an adjacent `diagram-id` metadata comment.
- Confirm rendered diagram completeness passed and missing diagrams were not accepted by title-only matches.
- Confirm rendered Markdown Mermaid validation ran in strict mode.
- Confirm `scripts/validate_mermaid.py` and `references/mermaid-rules.md` were not modified.
```

- [ ] **Step 5: Run documentation signpost tests**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_validate_mermaid.SkillBodyContractTests tests.test_render_markdown.ReferenceSignpostTests -v
```

Expected: PASS after updating test class names if current names differ.

---

### Task 9: Full Verification And Boundary Guards

**Files:**
- Verify only: whole repository
- Verify only: `scripts/validate_mermaid.py`
- Verify only: `references/mermaid-rules.md`

- [ ] **Step 1: Run targeted Phase 4 tests**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_v2_phase4_renderer_and_mermaid_gates -v
```

Expected: PASS, with real strict Mermaid tests skipped when `node` or `mmdc` is unavailable.

- [ ] **Step 2: Run renderer and Mermaid-adjacent regression tests**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_render_markdown tests.test_validate_mermaid tests.test_phase7_e2e -v
```

Expected: PASS, with real strict Mermaid tests skipped when local CLI tooling is unavailable.

- [ ] **Step 3: Run the full test suite**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest discover -s tests -v
```

Expected: PASS, except tests explicitly skipped for unavailable local Mermaid CLI tooling.

- [ ] **Step 4: Verify no forbidden Mermaid files changed**

Run:

```bash
git diff --exit-code -- scripts/validate_mermaid.py references/mermaid-rules.md
```

Expected: no diff.

- [ ] **Step 5: Inspect changed files**

Run:

```bash
git status --short
git diff --stat
```

Expected changed files are limited to the Phase 4 implementation, tests, and documentation listed in this plan. Do not run cleanup or deletion commands; if temporary cleanup is needed, give the command to the user.
