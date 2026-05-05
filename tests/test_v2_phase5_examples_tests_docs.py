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
            has_hidden_support_refs = any(
                value
                for _json_path, node in walk_json(document)
                if isinstance(node, dict)
                for key, value in node.items()
                if key in {"evidence_refs", "traceability_refs", "source_snippet_refs"} and value
            )
            structure_issues = document["structure_issues_and_suggestions"]
            example_level_blocks = structure_issues["blocks"]

            for module in document["module_design"]["modules"]:
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
                module_blocks = [
                    block
                    for detail in mechanism["mechanism_details"]
                    for block in detail["blocks"]
                ]
                block_types = {block["block_type"] for block in [*module_blocks, *example_level_blocks]}
                has_typed_anchors = any(
                    isinstance(anchor, dict) and anchor.get("anchor_type") and anchor.get("value")
                    for row in mechanism["mechanism_index"]["rows"]
                    for anchor in row.get("related_anchors", [])
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
                        structure_issues["summary"],
                        any(block["block_type"] == "diagram" for block in structure_issues["blocks"]),
                        has_hidden_support_refs,
                    ]
                )
                if covers_full_shape:
                    rich_examples.append(path.name)
                    break

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
