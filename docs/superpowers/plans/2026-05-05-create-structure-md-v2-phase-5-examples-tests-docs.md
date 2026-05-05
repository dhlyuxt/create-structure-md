# create-structure-md V2 Phase 5 Examples Tests Docs Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete V2 by making examples, rejected fixtures, documentation, and end-to-end tests prove the Phase 1-4 contracts together.

**Architecture:** Treat Phase 5 as the acceptance layer over the existing V2 implementation. Add a dedicated Phase 5 test module for example and documentation contracts, keep legacy V1 input only as a rejected fixture, enrich at least one accepted example to exercise the full V2 shape, and harden strict Mermaid real-CLI tests so they skip when the CLI is installed but the browser sandbox cannot launch in the current environment.

**Tech Stack:** Python 3, standard-library `unittest`, existing `jsonschema` dependency, existing renderer and validators, existing Phase 4 Mermaid gate workflow, no new runtime dependencies.

---

## Scope And Constraints

- Do not add repository analysis, requirement inference, Word/PDF/image export, multi-document output, or a V1-to-V2 migration tool.
- Do not modify `scripts/validate_mermaid.py`.
- Do not modify `references/mermaid-rules.md`.
- Do not run deletion commands. Workspace instruction: when cleanup is needed, give the command to the user instead of executing it.
- Code edits may replace obsolete lines as part of normal patching, but do not remove files/directories or run shell cleanup commands.
- Keep V2 examples on `dsl_version: "0.2.0"` only.
- Keep V1 input only as a rejected fixture. Do not include rejected fixtures in accepted example lists.
- Evidence rendering remains renderer policy through `--evidence-mode hidden|inline`; do not add evidence rendering policy fields to DSL examples.
- Static-only Mermaid validation is not final Phase 5 acceptance. Static validation can be a fallback signal only when the real Mermaid CLI cannot launch in the current environment.
- Current baseline note from this workspace: `python -m unittest discover -s tests -v` has 3 failures because `mmdc` is installed but Chromium cannot launch due the browser sandbox (`Operation not permitted`). Phase 5 must preserve strict Mermaid verification in mock and real-capable environments while skipping real strict tests when the local browser launch probe fails.

Use the project Python for verification:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest discover -s tests -v
```

Targeted Phase 5 verification command:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_v2_phase5_examples_tests_docs -v
```

Boundary guard after implementation:

```bash
git diff --exit-code -- scripts/validate_mermaid.py references/mermaid-rules.md
```

Expected: no diff.

---

## File Structure

- Create: `tests/test_v2_phase5_examples_tests_docs.py`
  - Owns Phase 5 acceptance coverage for accepted examples, rejected V1 fixtures, documentation signposts, hidden/inline evidence behavior over examples, and Phase 4 static gate composition.
- Create: `tests/fixtures/rejected-v1-phase2.dsl.json`
  - Explicitly named V1 rejected fixture copied from the current legacy `tests/fixtures/valid-phase2.dsl.json` content so Phase 5 tests no longer describe a V1 file as "valid".
- User-removes: `tests/fixtures/valid-phase2.dsl.json`
  - The old misleading V1 fixture path must be removed by the user, not by Codex. After the user removes it, stage that user-performed deletion with `git add -u tests/fixtures/valid-phase2.dsl.json`.
- Modify: `tests/test_validate_dsl.py`
  - Point `REJECTED_V1_FIXTURE` at `tests/fixtures/rejected-v1-phase2.dsl.json`; keep existing V1 rejection assertions.
- Modify: `tests/test_validate_dsl_semantics.py`
  - Point `REJECTED_V1_FIXTURE` at `tests/fixtures/rejected-v1-phase2.dsl.json`; keep version fail-fast assertions.
- Modify: `tests/test_render_markdown.py`
  - Point renderer V1 rejection tests at `tests/fixtures/rejected-v1-phase2.dsl.json`.
- Modify: `create-structure-md_STRUCTURE_DESIGN.md`
  - Replace stale references to `tests/fixtures/valid-phase2.dsl.json` with `tests/fixtures/rejected-v1-phase2.dsl.json`.
- Modify: `tests/test_phase7_e2e.py`
  - Keep existing end-to-end coverage, add a reusable strict Mermaid CLI launch probe, and skip real strict CLI tests when `mmdc` exists but Chromium cannot launch in this environment.
- Modify: `tests/test_v2_phase4_renderer_and_mermaid_gates.py`
  - Reuse the same real strict CLI launch probe pattern for the Phase 4 real strict rendered Markdown test.
- Modify: `examples/minimal-from-code.dsl.json`
  - Enrich this accepted example so at least one accepted example covers every Phase 5 "accepted example should include" bullet.
- Verify only: `examples/minimal-from-requirements.dsl.json`
  - Keep valid on `0.2.0`; no full enrichment is required if `minimal-from-code.dsl.json` carries the comprehensive V2 example role.
- Modify: `SKILL.md`
  - Ensure workflow and boundary text states prepared input, no repo analysis, no inference, V2-only DSL, hidden evidence default, readability artifact, rendered completeness, and strict rendered Markdown validation.
- Modify: `references/dsl-spec.md`
  - Ensure V2-only DSL, V1 rejected fixture policy, evidence-mode policy outside DSL, Chapter 4 seven-subsection model, Chapter 9 model, and expected diagram paths are explicit.
- Modify: `references/document-structure.md`
  - Ensure visible output structure documents Chapter 4 order, Chapter 9 order, hidden evidence default, diagram metadata comments, and Section 5.2 simplified columns.
- Modify: `references/review-checklist.md`
  - Ensure final review checks V2 examples, rejected V1 fixtures, readability artifact, rendered completeness, strict rendered Markdown validation, and unchanged Mermaid validator/rules files.
- Verify only: `schemas/structure-design.schema.json`
  - Expected to already enforce V2 schema. Modify only if a Phase 5 test exposes a real schema gap.
- Verify only: `scripts/validate_dsl.py`
  - Expected to already fail fast for non-`0.2.0`. Modify only if a Phase 5 test exposes a real validator gap.
- Verify only: `scripts/render_markdown.py`
  - Expected to already default hidden evidence mode and support inline evidence mode. Modify only if a Phase 5 test exposes a real renderer gap.
- Verify only: `scripts/verify_v2_mermaid_gates.py`
  - Expected to already validate readability artifacts and rendered completeness. Modify only if a Phase 5 test exposes a workflow gap.
- Verify only: `scripts/validate_mermaid.py`
  - Must remain unchanged.
- Verify only: `references/mermaid-rules.md`
  - Must remain unchanged.
- Verify only: `requirements.txt`
  - Must still contain only `jsonschema`.

---

## Review History

This plan is intentionally review-driven. The main agent revises this section after each adversarial sub-agent pass.

- Draft: Initial main-agent plan before adversarial review. Includes explicit rejected V1 fixture naming, accepted example enrichment, Phase 5 acceptance tests, documentation signposts, real Mermaid CLI launch probing, and final boundary guards.
- Round 1: Revised after adversarial review. Fixes added for strict Mermaid probe fail-vs-skip behavior, missing `shutil` import, explicit Phase 4 V1 gate coverage, user-executed removal command for the old `valid-phase2` V1 fixture, semantic documentation assertions, concrete documentation paragraphs, and requirements-example verify-only scope.
- Round 2: Revised after adversarial review. Fixes added for a blocking user-removal checkpoint for the old `valid-phase2` fixture, staging that user-performed deletion, stale generated-document path updates, non-optional strict Mermaid tooling requirements, staged and unstaged out-of-scope guards before commits, and removal of the contradictory final all-files commit.
- Round 3: Final adversarial review found no Critical issues. Fixes added for review-checklist semantic test wording, bare `valid-phase2 fixture` generated-document references, and stricter browser-launch skip detection that does not skip on a bare `Operation not permitted`.

---

### Task 1: Phase 5 Acceptance Harness

**Files:**
- Create: `tests/test_v2_phase5_examples_tests_docs.py`

- [ ] **Step 1: Write the failing Phase 5 harness**

Create `tests/test_v2_phase5_examples_tests_docs.py` with these helpers and tests:

```python
import contextlib
import importlib.util
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
ACCEPTED_EXAMPLE_PATHS = [
    ROOT / "examples/minimal-from-code.dsl.json",
    ROOT / "examples/minimal-from-requirements.dsl.json",
]
CANONICAL_V2_FIXTURE = ROOT / "tests/fixtures/valid-v2-foundation.dsl.json"
REJECTED_V1_FIXTURE = ROOT / "tests/fixtures/rejected-v1-phase2.dsl.json"
MISLEADING_V1_FIXTURE = ROOT / "tests/fixtures/valid-phase2.dsl.json"
OUT_OF_SCOPE_MERMAID_FILES = [
    ROOT / "scripts/validate_mermaid.py",
    ROOT / "references/mermaid-rules.md",
]


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_script(relative_path, module_name):
    spec = importlib.util.spec_from_file_location(module_name, ROOT / relative_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def call_main(module, argv):
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        try:
            result = module.main(argv)
        except SystemExit as exc:
            code = exc.code
        else:
            code = result
    return code or 0, stdout.getvalue(), stderr.getvalue()


def run_script(*args):
    return subprocess.run(
        [PYTHON, *map(str, args)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def committed_file_text(path):
    completed = subprocess.run(
        ["git", "show", f"HEAD:{path.relative_to(ROOT)}"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        return None
    return completed.stdout


def walk_json(value, path="$"):
    yield path, value
    if isinstance(value, dict):
        for key, child in value.items():
            yield from walk_json(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from walk_json(child, f"{path}[{index}]")


def all_blocks(document):
    for module in document["module_design"]["modules"]:
        for detail in module["internal_mechanism"]["mechanism_details"]:
            yield from detail["blocks"]
    yield from document["structure_issues_and_suggestions"]["blocks"]


def expected_diagram_ids(document):
    phase4 = load_script("scripts/v2_phase4.py", "phase5_v2_phase4_under_test")
    return {
        diagram.diagram_id
        for diagram in phase4.collect_expected_diagrams(document)
        if diagram.should_render
    }


class Phase5RejectedV1FixtureTests(unittest.TestCase):
    def test_rejected_v1_fixture_is_named_as_rejected_and_not_an_accepted_example(self):
        self.assertTrue(REJECTED_V1_FIXTURE.is_file())
        self.assertFalse(MISLEADING_V1_FIXTURE.exists(), f"Remove misleading V1 fixture name: {MISLEADING_V1_FIXTURE}")
        accepted = {path.resolve() for path in ACCEPTED_EXAMPLE_PATHS}
        self.assertNotIn(REJECTED_V1_FIXTURE.resolve(), accepted)

        document = load_json(REJECTED_V1_FIXTURE)
        self.assertNotEqual("0.2.0", document.get("dsl_version"))
        self.assertIn("internal_structure", document["module_design"]["modules"][0])
        self.assertIn("external_capability_details", document["module_design"]["modules"][0])

    def test_rejected_v1_fixture_fails_validator_renderer_and_phase4_gate_before_output(self):
        validator = run_script("scripts/validate_dsl.py", REJECTED_V1_FIXTURE)
        self.assertEqual(2, validator.returncode)
        self.assertIn("V1 DSL is not supported by the V2 renderer", validator.stderr)

        with tempfile.TemporaryDirectory() as tmpdir:
            renderer = run_script("scripts/render_markdown.py", REJECTED_V1_FIXTURE, "--output-dir", tmpdir)
            self.assertEqual(2, renderer.returncode)
            self.assertIn("V1 DSL is not supported by the V2 renderer", renderer.stderr)
            self.assertEqual([], list(Path(tmpdir).glob("*.md")))

            phase4_gate = run_script(
                "scripts/verify_v2_mermaid_gates.py",
                REJECTED_V1_FIXTURE,
                "--mermaid-review-artifact",
                Path(tmpdir) / "missing-review.json",
                "--pre-render",
                "--work-dir",
                Path(tmpdir) / "mermaid",
            )
            self.assertEqual(2, phase4_gate.returncode)
            self.assertIn("V1 DSL is not supported by the V2 renderer", phase4_gate.stderr)
            self.assertNotIn("readability review artifact is missing", phase4_gate.stderr)


class Phase5AcceptedExampleContractTests(unittest.TestCase):
    def load_examples(self):
        return [(path, load_json(path)) for path in ACCEPTED_EXAMPLE_PATHS]

    def test_accepted_examples_validate_render_and_pass_static_mermaid_completeness(self):
        for path, document in self.load_examples():
            with self.subTest(path=path.name):
                self.assertEqual("0.2.0", document["dsl_version"])
                validate = run_script("scripts/validate_dsl.py", path)
                self.assertEqual(0, validate.returncode, validate.stderr)
                self.assertIn("Validation succeeded", validate.stdout)

                with tempfile.TemporaryDirectory() as tmpdir:
                    render = run_script("scripts/render_markdown.py", path, "--output-dir", tmpdir)
                    self.assertEqual(0, render.returncode, render.stderr)
                    output_path = Path(tmpdir) / document["document"]["output_file"]
                    self.assertTrue(output_path.is_file())
                    markdown = output_path.read_text(encoding="utf-8")

                    phase4 = load_script("scripts/v2_phase4.py", f"phase5_v2_phase4_{path.stem}")
                    self.assertEqual([], phase4.rendered_diagram_completeness_errors(document, markdown))
                    self.assertEqual(len(expected_diagram_ids(document)), markdown.count("<!-- diagram-id:"))

                    static = run_script("scripts/validate_mermaid.py", "--from-markdown", output_path, "--static")
                    self.assertEqual(0, static.returncode, static.stderr)
                    self.assertIn("Mermaid validation succeeded", static.stdout)

    def test_at_least_one_accepted_example_exercises_full_v2_shape(self):
        rich_examples = []
        for path, document in self.load_examples():
            module = document["module_design"]["modules"][0]
            interface_rows = module["public_interfaces"]["interface_index"]["rows"]
            interfaces = module["public_interfaces"]["interfaces"]
            executable_interfaces = [
                interface for interface in interfaces
                if interface["interface_type"] in {"command_line", "function", "method", "library_api", "workflow"}
            ]
            contract_interfaces = [
                interface for interface in interfaces
                if interface["interface_type"] in {
                    "schema_contract",
                    "dsl_contract",
                    "document_contract",
                    "configuration_contract",
                    "data_contract",
                    "test_fixture",
                }
            ]
            mechanism = module["internal_mechanism"]
            blocks = list(all_blocks(document))
            block_types = {block["block_type"] for block in blocks}
            has_typed_anchors = any(
                isinstance(anchor, dict) and anchor.get("anchor_type") and anchor.get("value")
                for row in mechanism["mechanism_index"]["rows"]
                for anchor in row.get("related_anchors", [])
            )
            has_hidden_support_refs = any(
                value
                for _json_path, node in walk_json(document)
                if isinstance(node, dict)
                for key, value in node.items()
                if key in {"evidence_refs", "traceability_refs", "source_snippet_refs"} and value
            )

            covers_full_shape = all(
                [
                    module.get("source_scope", {}).get("summary"),
                    module["source_scope"]["primary_files"],
                    module["configuration"]["parameters"]["rows"],
                    module["dependencies"]["rows"],
                    module["data_objects"]["rows"],
                    interface_rows,
                    executable_interfaces,
                    all(interface["execution_flow_diagram"]["source"].strip() for interface in executable_interfaces),
                    contract_interfaces,
                    any(interface["contract"]["required_items"] for interface in contract_interfaces),
                    mechanism["mechanism_index"]["rows"],
                    mechanism["mechanism_details"],
                    {"text", "diagram", "table"} <= block_types,
                    has_typed_anchors,
                    module["known_limitations"]["rows"],
                    document["structure_issues_and_suggestions"]["summary"],
                    any(block["block_type"] == "diagram" for block in document["structure_issues_and_suggestions"]["blocks"]),
                    has_hidden_support_refs,
                ]
            )
            if covers_full_shape:
                rich_examples.append(path.name)

        self.assertTrue(rich_examples, "At least one accepted example must cover the full V2 Phase 5 shape")

    def test_hidden_evidence_is_default_and_inline_can_opt_in_for_examples(self):
        renderer = load_script("scripts/render_markdown.py", "phase5_render_markdown_under_test")
        examples_with_support = [
            (path, document)
            for path, document in self.load_examples()
            if any(
                value
                for _json_path, node in walk_json(document)
                if isinstance(node, dict)
                for key, value in node.items()
                if key in {"evidence_refs", "traceability_refs", "source_snippet_refs"} and value
            )
        ]
        self.assertTrue(examples_with_support, "Need at least one accepted example with hidden support refs")

        for path, document in examples_with_support:
            with self.subTest(path=path.name):
                hidden = renderer.render_markdown(document)
                inline = renderer.render_markdown(document, evidence_mode="inline")
                self.assertNotIn("依据：", hidden)
                self.assertNotIn("来源片段：", hidden)
                self.assertTrue("依据：" in inline or "来源片段：" in inline)


class Phase5DocumentationContractTests(unittest.TestCase):
    REQUIRED_SEMANTICS = {
        "SKILL.md": [
            ("boundary", ["does not analyze repositories", "does not infer", "does not invent missing design content"]),
            ("v2 version", ["dsl_version: \"0.2.0\"", "0.2.0"]),
            ("hidden evidence default", ["hidden by default", "--evidence-mode hidden"]),
            ("readability artifact", ["Mermaid readability review", "mermaid-readability-review.json"]),
            ("rendered completeness", ["rendered diagram completeness"]),
            ("strict rendered validation", ["strict rendered Markdown validation"]),
            ("static-only boundary", ["Static-only Mermaid validation is not final acceptance"]),
        ],
        "references/dsl-spec.md": [
            ("v2 only", ["V2 accepts only `dsl_version: \"0.2.0\"`"]),
            ("v1 rejected fixtures", ["V1 fixtures", "rejected fixtures"]),
            ("evidence mode policy", ["evidence-mode", "renderer policy"]),
            ("chapter 4 model", ["Chapter 4 Module Model", "4.x.1"]),
            ("chapter 9 model", ["Chapter 9", "risks", "assumptions", "low-confidence", "structure issues"]),
            ("content blocks", ["Reusable Content Blocks", "block_type"]),
            ("expected diagrams", ["Expected Mermaid Diagram Paths"]),
            ("readability artifact metadata", ["Mermaid readability review artifacts", "workflow metadata"]),
        ],
        "references/document-structure.md": [
            ("chapter 4 first subsection", ["4.x.1 模块定位与源码/产物范围"]),
            ("chapter 4 last subsection", ["4.x.7 已知限制"]),
            ("chapter 9 risks", ["9.1 风险清单"]),
            ("chapter 9 structure issues", ["9.4 结构问题与改进建议"]),
            ("diagram metadata", ["diagram-id"]),
            ("runtime unit columns", ["运行单元 | 类型 | 入口 | 职责 | 关联模块 | 备注"]),
        ],
        "references/review-checklist.md": [
            ("accepted examples", ["V2 examples", "accepted examples"]),
            ("rejected v1", ["rejected V1 fixtures"]),
            ("evidence modes", ["hidden evidence", "inline evidence"]),
            ("readability artifact", ["Mermaid readability artifact"]),
            ("rendered completeness", ["rendered diagram completeness"]),
            ("strict rendered validation", ["strict rendered Markdown validation"]),
            ("out of scope validator", ["scripts/validate_mermaid.py", "unchanged"]),
            ("out of scope rules", ["references/mermaid-rules.md", "unchanged"]),
        ],
    }

    def test_phase5_documentation_semantics_are_present(self):
        for relative_path, semantic_groups in self.REQUIRED_SEMANTICS.items():
            text = (ROOT / relative_path).read_text(encoding="utf-8").casefold()
            for label, required_terms in semantic_groups:
                with self.subTest(path=relative_path, label=label):
                    missing = [term for term in required_terms if term.casefold() not in text]
                    self.assertEqual([], missing)

    def test_out_of_scope_mermaid_files_are_not_phase5_documentation_targets(self):
        spec = (ROOT / "docs/superpowers/specs/2026-05-04-create-structure-md-v2-phase-5-examples-tests-docs.md").read_text(encoding="utf-8")
        self.assertIn("Do not modify `scripts/validate_mermaid.py`", spec)
        self.assertIn("Do not modify `references/mermaid-rules.md`", spec)

        for path in OUT_OF_SCOPE_MERMAID_FILES:
            with self.subTest(path=path.relative_to(ROOT)):
                committed = committed_file_text(path)
                if committed is not None:
                    self.assertEqual(committed, path.read_text(encoding="utf-8"))
```

- [ ] **Step 2: Run the new harness to verify it fails for missing Phase 5 assets**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_v2_phase5_examples_tests_docs -v
```

Expected before implementation: FAIL because `tests/fixtures/rejected-v1-phase2.dsl.json` does not exist, `tests/fixtures/valid-phase2.dsl.json` still exists under a misleading V1 `valid-` name, at least one accepted example lacks full content-block diagram/table coverage, and some documentation semantics may be absent.

- [ ] **Step 3: Run out-of-scope guards before committing the failing harness**

Run:

```bash
git diff --exit-code -- scripts/validate_mermaid.py references/mermaid-rules.md
git diff --cached --exit-code -- scripts/validate_mermaid.py references/mermaid-rules.md
```

Expected: both commands produce no output and exit code 0.

- [ ] **Step 4: Commit after the failing harness**

```bash
git add tests/test_v2_phase5_examples_tests_docs.py
git commit -m "test: add v2 phase 5 acceptance harness"
```

---

### Task 2: Explicit Rejected V1 Fixture

**Files:**
- Create: `tests/fixtures/rejected-v1-phase2.dsl.json`
- Modify: `tests/test_validate_dsl.py`
- Modify: `tests/test_validate_dsl_semantics.py`
- Modify: `tests/test_render_markdown.py`

- [ ] **Step 1: Create the explicitly rejected fixture**

Copy the current legacy V1 fixture into an explicitly named rejected fixture. This is a non-deletion mechanical copy:

```bash
cp tests/fixtures/valid-phase2.dsl.json tests/fixtures/rejected-v1-phase2.dsl.json
```

Expected fixture properties:

```json
{
  "dsl_version": "0.1.0",
  "module_design": {
    "modules": [
      {
        "external_capability_details": {},
        "internal_structure": {}
      }
    ]
  }
}
```

The copied file contains full legacy data; the snippet above shows the required identifying properties, not the whole file.

- [ ] **Step 2: Stop for user removal of the old misleading fixture path**

Do not run this deletion command. Show it to the user and wait for them to execute it. This is a blocking Phase 5 checkpoint because accepted V2 completion must not leave a `valid-` named V1 fixture in the repository:

```bash
rm tests/fixtures/valid-phase2.dsl.json
```

After the user confirms they ran the command, verify the old path is gone:

```bash
test ! -e tests/fixtures/valid-phase2.dsl.json
```

Expected: exit code 0.

- [ ] **Step 3: Point V1 rejection tests at the rejected fixture name**

In `tests/test_validate_dsl.py`, change:

```python
REJECTED_V1_FIXTURE = ROOT / "tests/fixtures/valid-phase2.dsl.json"
```

to:

```python
REJECTED_V1_FIXTURE = ROOT / "tests/fixtures/rejected-v1-phase2.dsl.json"
```

Update direct string loads in the same file:

```python
document = load_json("tests/fixtures/rejected-v1-phase2.dsl.json")
```

In `tests/test_validate_dsl_semantics.py`, change:

```python
REJECTED_V1_FIXTURE = ROOT / "tests/fixtures/valid-phase2.dsl.json"
```

to:

```python
REJECTED_V1_FIXTURE = ROOT / "tests/fixtures/rejected-v1-phase2.dsl.json"
```

In `tests/test_render_markdown.py`, change the V1 renderer rejection command to use:

```python
ROOT / "tests/fixtures/rejected-v1-phase2.dsl.json"
```

In `create-structure-md_STRUCTURE_DESIGN.md`, replace every occurrence of:

```text
tests/fixtures/valid-phase2.dsl.json
```

with:

```text
tests/fixtures/rejected-v1-phase2.dsl.json
```

Also replace every bare phrase:

```text
valid-phase2 fixture
```

with:

```text
rejected-v1-phase2 fixture
```

- [ ] **Step 4: Run V1 rejection tests**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest \
  tests.test_validate_dsl.V2VersionSchemaTests \
  tests.test_validate_dsl_semantics.V2VersionCliTests \
  tests.test_render_markdown.RendererV2VersionTests \
  tests.test_v2_phase5_examples_tests_docs.Phase5RejectedV1FixtureTests -v
```

Expected: PASS.

- [ ] **Step 5: Run out-of-scope guards before committing**

Run:

```bash
git diff --exit-code -- scripts/validate_mermaid.py references/mermaid-rules.md
git diff --cached --exit-code -- scripts/validate_mermaid.py references/mermaid-rules.md
```

Expected: both commands produce no output and exit code 0.

- [ ] **Step 6: Commit**

```bash
git add tests/fixtures/rejected-v1-phase2.dsl.json tests/test_validate_dsl.py tests/test_validate_dsl_semantics.py tests/test_render_markdown.py create-structure-md_STRUCTURE_DESIGN.md
git add -u tests/fixtures/valid-phase2.dsl.json
git commit -m "test: mark legacy v1 fixture as rejected input"
```

---

### Task 3: Enrich One Accepted V2 Example

**Files:**
- Modify: `examples/minimal-from-code.dsl.json`
- Modify: `tests/test_phase7_e2e.py`
- Modify: `tests/test_render_markdown.py`

- [ ] **Step 1: Add diagram and table blocks to the code example internal mechanism**

In `examples/minimal-from-code.dsl.json`, replace the single-item `module_design.modules[0].internal_mechanism.mechanism_details[0].blocks` array with this three-block array:

```json
[
  {
    "block_id": "BLOCK-SKILL-VALIDATION-TEXT",
    "block_type": "text",
    "title": "DSL 校验管线说明",
    "text": "校验入口先拒绝非 0.2.0 DSL，再执行 JSON Schema 检查和语义检查；只有通过校验的 DSL 才进入渲染流程。",
    "confidence": "observed",
    "evidence_refs": ["EV-CODE-V2-BOUNDARY"],
    "traceability_refs": [],
    "source_snippet_refs": []
  },
  {
    "block_id": "BLOCK-SKILL-VALIDATION-DIAGRAM",
    "block_type": "diagram",
    "title": "DSL 校验管线图",
    "confidence": "observed",
    "evidence_refs": [],
    "traceability_refs": [],
    "source_snippet_refs": [],
    "diagram": {
      "id": "MER-BLOCK-MECHANISM-FLOW",
      "kind": "content_block",
      "title": "DSL 校验管线图",
      "diagram_type": "flowchart",
      "description": "展示校验管线如何从 DSL 输入走向校验结果。",
      "source": "flowchart TD\n  A[\"DSL JSON\"] --> B[\"Version gate\"]\n  B --> C[\"Schema validation\"]\n  C --> D[\"Semantic validation\"]\n  D --> E[\"Validation result\"]",
      "confidence": "observed"
    }
  },
  {
    "block_id": "BLOCK-SKILL-VALIDATION-TABLE",
    "block_type": "table",
    "title": "DSL 校验管线阶段",
    "confidence": "observed",
    "evidence_refs": [],
    "traceability_refs": [],
    "source_snippet_refs": [],
    "table": {
      "id": "TBL-BLOCK-MECHANISM-STAGES",
      "title": "DSL 校验管线阶段",
      "columns": [
        { "key": "stage", "title": "阶段" },
        { "key": "description", "title": "说明" }
      ],
      "rows": [
        {
          "stage": "Version gate",
          "description": "拒绝非 0.2.0 DSL。"
        },
        {
          "stage": "Semantic validation",
          "description": "检查跨字段引用、not_applicable 互斥和内容安全。"
        }
      ]
    }
  }
]
```

- [ ] **Step 2: Add diagram and table blocks to the code example Chapter 9 section**

In `examples/minimal-from-code.dsl.json`, replace `structure_issues_and_suggestions.blocks` with:

```json
[
  {
    "block_id": "ISSUE-TEXT-001",
    "block_type": "text",
    "title": "输入完整性依赖",
    "text": "如果 DSL 缺少某个模块、流程或依赖信息，渲染器不会从仓库源码中推理补齐。",
    "confidence": "observed",
    "evidence_refs": ["EV-CODE-V2-BOUNDARY"],
    "traceability_refs": [],
    "source_snippet_refs": []
  },
  {
    "block_id": "ISSUE-DIAGRAM-001",
    "block_type": "diagram",
    "title": "结构问题关系图",
    "confidence": "observed",
    "evidence_refs": [],
    "traceability_refs": [],
    "source_snippet_refs": [],
    "diagram": {
      "id": "MER-BLOCK-STRUCTURE-ISSUES",
      "kind": "content_block",
      "title": "结构问题关系图",
      "diagram_type": "flowchart",
      "description": "展示上游内容完整性如何影响最终结构文档。",
      "source": "flowchart TD\n  A[\"Prepared DSL\"] --> B[\"Validation\"]\n  B --> C[\"Markdown rendering\"]\n  A --> D[\"Missing content risk\"]",
      "confidence": "observed"
    }
  },
  {
    "block_id": "ISSUE-TABLE-001",
    "block_type": "table",
    "title": "结构问题与改进方向",
    "confidence": "observed",
    "evidence_refs": [],
    "traceability_refs": [],
    "source_snippet_refs": [],
    "table": {
      "id": "TBL-BLOCK-STRUCTURE-ISSUES",
      "title": "结构问题与改进方向",
      "columns": [
        { "key": "issue", "title": "问题" },
        { "key": "improvement", "title": "改进方向" }
      ],
      "rows": [
        {
          "issue": "缺失仓库分析能力",
          "improvement": "由上游 repo-analysis skill 或人工准备 DSL。"
        }
      ]
    }
  }
]
```

- [ ] **Step 3: Add hidden support refs to the code example**

Set `module_design.modules[0].evidence_refs` to:

```json
["EV-CODE-V2-BOUNDARY"]
```

Set the top-level `evidence` array in `examples/minimal-from-code.dsl.json` to:

```json
[
  {
    "id": "EV-CODE-V2-BOUNDARY",
    "kind": "source",
    "title": "V2 prepared-content boundary",
    "location": "SKILL.md",
    "description": "The skill consumes prepared structure content and does not analyze repositories or infer missing design content.",
    "confidence": "observed"
  }
]
```

- [ ] **Step 4: Strengthen existing example contract tests**

In `tests/test_phase7_e2e.py`, extend `Phase7ExampleContractTests.test_examples_cover_minimum_fixed_chapter_content` so it asserts at least one accepted example includes all three content block types in Chapter 4 and Chapter 9:

```python
    def test_one_accepted_example_covers_rich_v2_content_blocks(self):
        rich_examples = []
        for path in EXAMPLE_PATHS:
            document = self.load_example(path)
            blocks = []
            for module in document["module_design"]["modules"]:
                for detail in module["internal_mechanism"]["mechanism_details"]:
                    blocks.extend(detail["blocks"])
            issue_blocks = document["structure_issues_and_suggestions"]["blocks"]
            block_types = {block["block_type"] for block in blocks}
            issue_block_types = {block["block_type"] for block in issue_blocks}
            if {"text", "diagram", "table"} <= block_types and {"text", "diagram", "table"} <= issue_block_types:
                rich_examples.append(path.name)
        self.assertTrue(rich_examples, "at least one accepted example must cover rich V2 content blocks")
```

In `tests/test_render_markdown.py`, extend `RendererIntegrationTests.test_minimal_examples_render_after_v2_migration` to assert the enriched code example renders both content-block diagram metadata IDs:

```python
if relative_path == "examples/minimal-from-code.dsl.json":
    markdown = next(Path(tmpdir).glob("*.md")).read_text(encoding="utf-8")
    self.assertIn("<!-- diagram-id: MER-BLOCK-MECHANISM-FLOW -->", markdown)
    self.assertIn("<!-- diagram-id: MER-BLOCK-STRUCTURE-ISSUES -->", markdown)
```

- [ ] **Step 5: Run enriched example tests**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest \
  tests.test_v2_phase5_examples_tests_docs.Phase5AcceptedExampleContractTests \
  tests.test_phase7_e2e.Phase7ExampleContractTests \
  tests.test_render_markdown.RendererIntegrationTests.test_minimal_examples_render_after_v2_migration -v
```

Expected: PASS.

- [ ] **Step 6: Run out-of-scope guards before committing**

Run:

```bash
git diff --exit-code -- scripts/validate_mermaid.py references/mermaid-rules.md
git diff --cached --exit-code -- scripts/validate_mermaid.py references/mermaid-rules.md
```

Expected: both commands produce no output and exit code 0.

- [ ] **Step 7: Commit**

```bash
git add examples/minimal-from-code.dsl.json tests/test_phase7_e2e.py tests/test_render_markdown.py
git commit -m "test: enrich accepted v2 example coverage"
```

---

### Task 4: Documentation Acceptance

**Files:**
- Modify: `SKILL.md`
- Modify: `references/dsl-spec.md`
- Modify: `references/document-structure.md`
- Modify: `references/review-checklist.md`

- [ ] **Step 1: Update `SKILL.md` V2 workflow signposts**

Add this paragraph at the end of the Boundary section:

```markdown
For V2, create-structure-md accepts only `dsl_version: "0.2.0"`. create-structure-md does not analyze repositories, does not infer missing requirements, and does not invent missing design content from source code; another actor must prepare the structure content before this skill runs.
```

Add this paragraph after the workflow list:

```markdown
Evidence support blocks are hidden by default through renderer policy, equivalent to `--evidence-mode hidden`. Use `--evidence-mode inline` only when the user explicitly wants inline evidence notes. Static-only Mermaid validation is not final acceptance: the final workflow requires a Mermaid readability review artifact, rendered diagram completeness, and strict rendered Markdown validation.
```

- [ ] **Step 2: Update `references/dsl-spec.md` Phase 5 signposts**

Add this paragraph under `## V2 DSL Version Contract`:

```markdown
Accepted examples are renderer acceptance inputs and must use `dsl_version: "0.2.0"`. V1 examples may remain only as rejected fixtures; they are used to prove fail-fast migration errors and must not appear in accepted example lists.
```

Add this paragraph under `## Support Data`:

```markdown
The evidence-mode choice is renderer policy outside DSL content. Hidden mode is the default and suppresses evidence, traceability, and source snippet notes in final Markdown while preserving normal structural facts. Inline mode renders those support notes near the content that references them.
```

Add this paragraph under the Chapter 9 section:

```markdown
Chapter 9 renders risks, assumptions, low-confidence items, and structure issues in that order. The structure issues section renders its summary before reusable content blocks.
```

- [ ] **Step 3: Update `references/document-structure.md` Phase 5 signposts**

Add this paragraph to the Chapter 4 section:

```markdown
Each Chapter 4 module renders exactly these subsections in order: `4.x.1 模块定位与源码/产物范围`, `4.x.2 配置`, `4.x.3 依赖`, `4.x.4 数据对象`, `4.x.5 对外接口`, `4.x.6 实现机制说明`, and `4.x.7 已知限制`.
```

Add this paragraph to the Chapter 5 section:

```markdown
Section 5.2 renders runtime units with the simplified visible columns `运行单元 | 类型 | 入口 | 职责 | 关联模块 | 备注`. It does not render V1 `入口不适用原因` or `外部环境原因` columns.
```

Add this paragraph to the Chapter 9 section:

```markdown
Chapter 9 renders `9.1 风险清单`, `9.2 假设清单`, `9.3 低置信度项目`, and `9.4 结构问题与改进建议` in that fixed order.
```

Add this paragraph near the Mermaid rendering rules:

```markdown
Every rendered Mermaid fence is preceded by a `diagram-id` metadata comment so rendered diagram completeness can bind Markdown fences back to DSL diagram IDs.
```

- [ ] **Step 4: Update `references/review-checklist.md` Phase 5 signposts**

Add this checklist section:

```markdown
## Phase 5 Acceptance Checks

- V2 examples validate, render, and pass rendered diagram completeness.
- Accepted examples use `dsl_version: "0.2.0"` and rejected V1 fixtures are not renderer acceptance fixtures.
- hidden evidence mode is the default and inline evidence mode is available only through renderer CLI policy.
- Mermaid readability artifact exists before strict validation and covers expected diagrams.
- rendered diagram completeness passes before strict rendered Markdown validation.
- strict rendered Markdown validation is reported; static-only Mermaid validation is not final acceptance.
- `scripts/validate_mermaid.py` unchanged.
- `references/mermaid-rules.md` unchanged.
```

- [ ] **Step 5: Run documentation contract tests**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest \
  tests.test_v2_phase5_examples_tests_docs.Phase5DocumentationContractTests \
  tests.test_phase7_e2e.Phase7ReferenceDocumentationTests \
  tests.test_validate_mermaid.SkillBodyContractTests \
  tests.test_render_markdown.ReferenceSignpostTests -v
```

Expected: PASS.

- [ ] **Step 6: Run out-of-scope guards before committing**

Run:

```bash
git diff --exit-code -- scripts/validate_mermaid.py references/mermaid-rules.md
git diff --cached --exit-code -- scripts/validate_mermaid.py references/mermaid-rules.md
```

Expected: both commands produce no output and exit code 0.

- [ ] **Step 7: Commit**

```bash
git add SKILL.md references/dsl-spec.md references/document-structure.md references/review-checklist.md
git commit -m "docs: document v2 phase 5 acceptance workflow"
```

---

### Task 5: Real Mermaid CLI Launch Probe For Strict Tests

**Files:**
- Modify: `tests/test_phase7_e2e.py`
- Modify: `tests/test_v2_phase4_renderer_and_mermaid_gates.py`

- [ ] **Step 1: Add a launch probe helper to `tests/test_phase7_e2e.py`**

Add this helper near `preserved_process_env()`:

```python
MERMAID_BROWSER_LAUNCH_FAILURE_PATTERNS = [
    "Failed to launch the browser process",
    "Operation not permitted",
    "No usable sandbox",
]


def strict_mermaid_cli_probe_result(run_dir):
    if shutil.which("mmdc") is None:
        return "fail", "mmdc unavailable; strict Mermaid validation cannot be accepted"
    if shutil.which("node") is None:
        return "fail", "node unavailable; strict Mermaid validation cannot be accepted"

    probe_dir = run_dir / "mermaid-probe"
    probe_markdown = run_dir / "mermaid-probe.md"
    probe_markdown.write_text(
        "```mermaid\nflowchart TD\n  A[Probe] --> B[OK]\n```\n",
        encoding="utf-8",
    )
    completed = run_command(
        "scripts/validate_mermaid.py",
        "--from-markdown",
        probe_markdown,
        "--strict",
        "--work-dir",
        probe_dir,
        env=preserved_process_env(run_dir),
    )
    if completed.returncode == 0:
        return "ok", ""
    combined = completed.stdout + completed.stderr
    browser_launch_failed = "Failed to launch the browser process" in combined or "No usable sandbox" in combined
    browser_sandbox_denied = "Operation not permitted" in combined
    if browser_launch_failed and browser_sandbox_denied:
        return "skip", "mmdc browser launch unavailable in this environment"
    return "fail", combined
```

- [ ] **Step 2: Use the probe in `test_examples_pass_strict_mermaid_workflow_with_real_cli_when_available`**

Replace the current `shutil.which()` skips with:

```python
probe_run_dir = make_run_dir("strict-mermaid-probe")
probe_status, probe_detail = strict_mermaid_cli_probe_result(probe_run_dir)
if probe_status == "skip":
    self.skipTest(probe_detail)
self.assertEqual("ok", probe_status, probe_detail)
```

Keep the existing strict pre-render and post-render assertions unchanged after the skip block.

- [ ] **Step 3: Add the same launch probe pattern to Phase 4 real strict test**

In `tests/test_v2_phase4_renderer_and_mermaid_gates.py`, add `import shutil` at module scope near the other imports, then add an equivalent helper near the real strict test class:

```python
def strict_mermaid_cli_probe_result(tmpdir):
    if shutil.which("mmdc") is None:
        return "fail", "mmdc unavailable; strict Mermaid validation cannot be accepted"
    if shutil.which("node") is None:
        return "fail", "node unavailable; strict Mermaid validation cannot be accepted"

    probe_markdown = Path(tmpdir) / "probe.md"
    probe_markdown.write_text(
        "```mermaid\nflowchart TD\n  A[Probe] --> B[OK]\n```\n",
        encoding="utf-8",
    )
    completed = subprocess.run(
        [
            PYTHON,
            str(ROOT / "scripts/validate_mermaid.py"),
            "--from-markdown",
            str(probe_markdown),
            "--strict",
            "--work-dir",
            str(Path(tmpdir) / "probe-work"),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode == 0:
        return "ok", ""
    combined = completed.stdout + completed.stderr
    browser_launch_failed = "Failed to launch the browser process" in combined or "No usable sandbox" in combined
    browser_sandbox_denied = "Operation not permitted" in combined
    if browser_launch_failed and browser_sandbox_denied:
        return "skip", "mmdc browser launch unavailable in this environment"
    return "fail", combined
```

At the start of `Phase4RealStrictRenderedMarkdownTests.test_rendered_markdown_passes_real_strict_validation_when_cli_available`, use:

```python
with tempfile.TemporaryDirectory() as tmpdir:
    probe_status, probe_detail = strict_mermaid_cli_probe_result(tmpdir)
    if probe_status == "skip":
        self.skipTest(probe_detail)
    self.assertEqual("ok", probe_status, probe_detail)
```

Then keep the current real strict rendered Markdown validation flow.

- [ ] **Step 4: Run strict-test targets**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest \
  tests.test_phase7_e2e.Phase7StrictMermaidAndFallbackTests \
  tests.test_v2_phase4_renderer_and_mermaid_gates.Phase4RealStrictRenderedMarkdownTests -v
```

Expected in this workspace: PASS with real strict tests skipped because `mmdc` and `node` are present but Chromium cannot launch. Expected in an environment where `mmdc` can launch: PASS by running the real strict workflow. Expected in an environment missing `mmdc` or `node`: FAIL with an explicit strict-tooling unavailable message, because Phase 5 final acceptance cannot silently fall back to static-only validation.

- [ ] **Step 5: Run out-of-scope guards before committing**

Run:

```bash
git diff --exit-code -- scripts/validate_mermaid.py references/mermaid-rules.md
git diff --cached --exit-code -- scripts/validate_mermaid.py references/mermaid-rules.md
```

Expected: both commands produce no output and exit code 0.

- [ ] **Step 6: Commit**

```bash
git add tests/test_phase7_e2e.py tests/test_v2_phase4_renderer_and_mermaid_gates.py
git commit -m "test: probe real mermaid cli launch before strict e2e"
```

---

### Task 6: Final Full Workflow Verification

**Files:**
- Verify only: all Phase 5 touched files
- Verify only: `scripts/validate_mermaid.py`
- Verify only: `references/mermaid-rules.md`
- Verify only: `requirements.txt`

- [ ] **Step 1: Run targeted Phase 5 tests**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_v2_phase5_examples_tests_docs -v
```

Expected: PASS.

- [ ] **Step 2: Run full test suite**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest discover -s tests -v
```

Expected in this workspace: PASS, with real strict Mermaid tests skipped if the browser launch probe reports the sandbox failure.

- [ ] **Step 3: Verify out-of-scope Mermaid files remain unchanged**

Run:

```bash
git diff --exit-code -- scripts/validate_mermaid.py references/mermaid-rules.md
git diff --cached --exit-code -- scripts/validate_mermaid.py references/mermaid-rules.md
```

Expected: both commands produce no output and exit code 0.

- [ ] **Step 4: Verify runtime dependencies remain unchanged**

Run:

```bash
git diff --exit-code -- requirements.txt
```

Expected: no output and exit code 0.

- [ ] **Step 5: Inspect changed files**

Run:

```bash
git status --short
```

Expected: no tracked Phase 5 changes remain because Tasks 1-5 committed their own work. Existing `.codex-tmp/...` preserved test artifacts may remain untracked; do not delete them.

If `.codex-tmp` cleanup is desired after verification, do not run deletion. Report this command to the user instead:

```bash
rm -r .codex-tmp/create-structure-md-phase7-tests .codex-tmp/install-skill-tests
```
