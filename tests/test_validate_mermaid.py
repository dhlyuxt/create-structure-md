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
VALIDATOR = ROOT / "scripts/validate_mermaid.py"
FIXTURE = ROOT / "tests/fixtures/valid-phase2.dsl.json"
PYTHON = sys.executable
SKILL = ROOT / "SKILL.md"

EXPECTED_DESCRIPTION = (
    "Use when the user asks Codex to generate a single module-specific software "
    "structure design document, such as <documented-object-name>_STRUCTURE_DESIGN.md, "
    "from already-prepared structured design content using the create-structure-md "
    "DSL and Mermaid diagrams. Do not use for repo analysis, requirements inference, "
    "multi-document generation, Word/PDF output, or image export."
)

REQUIRED_INPUTS = [
    "module list and stable module IDs",
    "module responsibilities",
    "module relationships",
    "module-level external capabilities or interface requirements",
    "module internal structure information",
    "runtime units and runtime flow",
    "configuration, structural data/artifact, and dependency information when applicable",
    "cross-module collaboration scenarios when more than one module is identified",
    "key flows and one diagram concept per key flow",
    "confidence values and support-data references where the schema requires or allows them",
    "evidence references or source snippets when available and safe to disclose",
]

WORKFLOW_ORDER = [
    "Create a temporary work directory.",
    "Write one complete DSL JSON file",
    "python scripts/validate_dsl.py structure.dsl.json",
    "python scripts/validate_mermaid.py --from-dsl structure.dsl.json --strict",
    "python scripts/render_markdown.py structure.dsl.json --output-dir",
    "python scripts/validate_mermaid.py --from-markdown <output-file> --static",
    "references/review-checklist.md",
    "Report the output path",
]


def load_validator_module():
    spec = importlib.util.spec_from_file_location("validate_mermaid_under_test", VALIDATOR)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def call_main(module, args):
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        try:
            result = module.main(args)
        except SystemExit as exc:
            code = exc.code
        else:
            code = result
    return code or 0, stdout.getvalue(), stderr.getvalue()


def valid_document():
    return deepcopy(json.loads(FIXTURE.read_text(encoding="utf-8")))


def write_json(document, directory, name="structure.dsl.json"):
    path = Path(directory) / name
    path.write_text(json.dumps(document), encoding="utf-8")
    return path


def write_markdown(tmpdir, name, text):
    path = Path(tmpdir) / name
    path.write_text(text, encoding="utf-8")
    return path


def front_matter_value(front_matter, key):
    prefix = f"{key}: "
    values = [
        line[len(prefix):]
        for line in front_matter.splitlines()
        if line.startswith(prefix)
    ]
    if len(values) != 1:
        raise AssertionError(f"Expected exactly one {key!r} front matter value")
    return values[0]


class MermaidCliContractTests(unittest.TestCase):
    def test_dsl_and_markdown_sources_are_mutually_exclusive(self):
        completed = subprocess.run(
            [
                PYTHON,
                str(VALIDATOR),
                "--from-dsl",
                "structure.dsl.json",
                "--from-markdown",
                "rendered.md",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(2, completed.returncode)
        self.assertIn("not allowed with argument", completed.stderr)

    def test_static_and_strict_are_mutually_exclusive(self):
        completed = subprocess.run(
            [
                PYTHON,
                str(VALIDATOR),
                "--from-dsl",
                "structure.dsl.json",
                "--static",
                "--strict",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(2, completed.returncode)
        self.assertIn("--strict and --static are mutually exclusive", completed.stderr)

    def test_check_env_must_be_used_by_itself(self):
        completed = subprocess.run(
            [PYTHON, str(VALIDATOR), "--check-env", "--from-dsl", "structure.dsl.json"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(2, completed.returncode)
        self.assertIn("--check-env must be used by itself", completed.stderr)

    def test_check_env_reports_missing_mmdc(self):
        module = load_validator_module()
        with mock.patch.object(module.shutil, "which", side_effect=lambda name: "/usr/bin/node" if name == "node" else None):
            code, stdout, stderr = call_main(module, ["--check-env"])
        self.assertEqual(1, code)
        self.assertIn("node: found at /usr/bin/node", stdout)
        self.assertIn("mmdc: missing", stdout)
        self.assertEqual("", stderr)

    def test_check_env_reports_node_mmdc_and_mermaid_cli_version(self):
        module = load_validator_module()

        def fake_which(name):
            return {
                "node": "/usr/bin/node",
                "mmdc": "/usr/local/bin/mmdc",
            }.get(name)

        completed = subprocess.CompletedProcess(
            ["mmdc", "--version"],
            0,
            stdout="10.9.1\n",
            stderr="",
        )
        with (
            mock.patch.object(module.shutil, "which", side_effect=fake_which),
            mock.patch.object(module.subprocess, "run", return_value=completed),
        ):
            code, stdout, stderr = call_main(module, ["--check-env"])
        self.assertEqual(0, code)
        self.assertIn("node: found at /usr/bin/node", stdout)
        self.assertIn("mmdc: found at /usr/local/bin/mmdc", stdout)
        self.assertIn("mermaid-cli: 10.9.1", stdout)
        self.assertEqual("", stderr)

    def test_work_dir_is_valid_when_default_mode_is_strict(self):
        module = load_validator_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            source = write_json(valid_document(), temp_dir)
            parser = module.build_parser()
            args = parser.parse_args(
                [
                    "--from-dsl",
                    str(source),
                    "--work-dir",
                    str(Path(temp_dir) / "mermaid-work"),
                ]
            )
            module.validate_args(args, parser)
        self.assertEqual("strict", module.effective_mode(args))

    def test_static_work_dir_fails(self):
        completed = subprocess.run(
            [
                PYTHON,
                str(VALIDATOR),
                "--from-dsl",
                "structure.dsl.json",
                "--static",
                "--work-dir",
                "mermaid-work",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(2, completed.returncode)
        self.assertIn("--work-dir is valid only in strict mode", completed.stderr)

    def test_source_or_check_env_is_required(self):
        completed = subprocess.run(
            [PYTHON, str(VALIDATOR)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(2, completed.returncode)
        self.assertIn("one of --from-dsl, --from-markdown, or --check-env is required", completed.stderr)


class SkillMetadataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = SKILL.read_text(encoding="utf-8")
        cls.front_matter = cls.text.split("---", 2)[1]

    def test_yaml_front_matter_matches_contract(self):
        self.assertTrue(self.text.startswith("---\n"))
        self.assertIn("name: create-structure-md", self.front_matter)
        self.assertEqual(
            EXPECTED_DESCRIPTION,
            front_matter_value(self.front_matter, "description"),
        )

    def test_description_contains_required_trigger_terms(self):
        for term in [
            "software structure design document",
            "STRUCTURE_DESIGN.md",
            "DSL",
            "Mermaid",
        ]:
            with self.subTest(term=term):
                self.assertIn(term, self.front_matter)

    def test_description_excludes_out_of_scope_work(self):
        for term in [
            "repo analysis",
            "requirements inference",
            "multi-document generation",
            "Word/PDF output",
            "image export",
        ]:
            with self.subTest(term=term):
                self.assertIn(term, self.front_matter)


class SkillBodyContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = SKILL.read_text(encoding="utf-8")

    def test_input_readiness_contract_lists_required_inputs(self):
        for phrase in REQUIRED_INPUTS:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.text)
        self.assertIn("If any required input is missing", self.text)
        self.assertIn("outside this skill", self.text)

    def test_workflow_appears_in_required_order(self):
        positions = []
        for phrase in WORKFLOW_ORDER:
            with self.subTest(phrase=phrase):
                positions.append(self.text.index(phrase))
        self.assertEqual(sorted(positions), positions)

    def test_mermaid_strict_and_static_acceptance_rule_is_visible(self):
        self.assertIn("Strict Mermaid validation is the default", self.text)
        self.assertIn("Static-only Mermaid validation is allowed only when strict tooling is unavailable", self.text)
        self.assertIn("the user explicitly accepts that limitation for the current run", self.text)

    def test_output_and_temporary_directory_rules_are_visible(self):
        for phrase in [
            "Final output is one Markdown file named by document.output_file",
            "target repository root",
            "current working directory",
            "<documented-object-name>_STRUCTURE_DESIGN.md",
            "Generic-only filenames are forbidden",
            "STRUCTURE_DESIGN.md",
            "structure_design.md",
            "design.md",
            "软件结构设计说明书.md",
            "must end with .md",
            "must not contain path separators",
            "must not contain ..",
            "must not contain control characters",
            "Spaces in the output filename should already be normalized to _",
            ".codex-tmp/create-structure-md-<run-id>/",
            "/tmp/create-structure-md-<run-id>",
            "Temporary files in the skill working directory are not automatically deleted",
            "give the cleanup command to the user instead of deleting files",
            "Codex must not edit .gitignore automatically unless the user asks it to",
        ]:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.text)

    def test_body_keeps_skill_out_of_repository_analysis(self):
        self.assertIn("This skill does not analyze repositories", self.text)
        self.assertIn("Do not run repository analysis tools as part of this skill", self.text)
        self.assertIn("Create one module- or system-specific Markdown file", self.text)


class DslMermaidStaticTests(unittest.TestCase):
    def diagram(self, diagram_id, diagram_type="flowchart", source="flowchart TD\n  A --> B"):
        return {
            "id": diagram_id,
            "kind": "test",
            "title": diagram_id,
            "diagram_type": diagram_type,
            "description": "Test diagram.",
            "source": source,
            "confidence": "observed",
        }

    def document_with_all_known_paths(self):
        document = valid_document()
        document["architecture_views"]["module_relationship_diagram"] = self.diagram("MER-ARCH-MODULES")
        document["architecture_views"]["extra_diagrams"] = [
            self.diagram("MER-ARCH-EXTRA"),
            self.diagram("MER-ARCH-EMPTY", source=" \n\t"),
        ]
        module = document["module_design"]["modules"][0]
        module["internal_structure"]["diagram"] = self.diagram("MER-MODULE-INTERNAL")
        module["external_capability_details"]["extra_diagrams"] = [
            self.diagram("MER-MODULE-CAPABILITY-EXTRA")
        ]
        module["extra_diagrams"] = [self.diagram("MER-MODULE-EXTRA")]
        document["runtime_view"]["runtime_flow_diagram"] = self.diagram("MER-RUNTIME-FLOW")
        document["runtime_view"]["runtime_sequence_diagram"] = self.diagram(
            "MER-RUNTIME-SEQUENCE",
            diagram_type="sequenceDiagram",
            source="sequenceDiagram\n  participant A\n  participant B\n  A->>B: call",
        )
        document["runtime_view"]["extra_diagrams"] = [self.diagram("MER-RUNTIME-EXTRA")]
        document["configuration_data_dependencies"]["extra_diagrams"] = [
            self.diagram("MER-CONFIG-EXTRA")
        ]
        document["cross_module_collaboration"]["collaboration_relationship_diagram"] = self.diagram(
            "MER-COLLABORATION-RELATIONSHIP"
        )
        document["cross_module_collaboration"]["extra_diagrams"] = [
            self.diagram("MER-COLLAB-EXTRA")
        ]
        document["key_flows"]["flows"][0]["diagram"] = self.diagram("MER-KEY-FLOW")
        document["key_flows"]["extra_diagrams"] = [self.diagram("MER-KEY-FLOW-EXTRA")]
        return document

    def test_extracts_non_empty_diagrams_from_all_known_dsl_paths_and_skips_empty_optional_sources(self):
        module = load_validator_module()
        diagrams = module.extract_diagrams_from_dsl(self.document_with_all_known_paths())
        paths_by_id = {diagram.diagram_id: diagram.json_path for diagram in diagrams}
        expected_paths = {
            "MER-ARCH-MODULES": "$.architecture_views.module_relationship_diagram",
            "MER-ARCH-EXTRA": "$.architecture_views.extra_diagrams[0]",
            "MER-MODULE-INTERNAL": "$.module_design.modules[0].internal_structure.diagram",
            "MER-MODULE-CAPABILITY-EXTRA": "$.module_design.modules[0].external_capability_details.extra_diagrams[0]",
            "MER-MODULE-EXTRA": "$.module_design.modules[0].extra_diagrams[0]",
            "MER-RUNTIME-FLOW": "$.runtime_view.runtime_flow_diagram",
            "MER-RUNTIME-SEQUENCE": "$.runtime_view.runtime_sequence_diagram",
            "MER-RUNTIME-EXTRA": "$.runtime_view.extra_diagrams[0]",
            "MER-CONFIG-EXTRA": "$.configuration_data_dependencies.extra_diagrams[0]",
            "MER-COLLABORATION-RELATIONSHIP": "$.cross_module_collaboration.collaboration_relationship_diagram",
            "MER-COLLAB-EXTRA": "$.cross_module_collaboration.extra_diagrams[0]",
            "MER-KEY-FLOW": "$.key_flows.flows[0].diagram",
            "MER-KEY-FLOW-EXTRA": "$.key_flows.extra_diagrams[0]",
        }
        self.assertEqual(expected_paths, paths_by_id)
        self.assertNotIn("MER-ARCH-EMPTY", paths_by_id)

    def test_from_dsl_static_succeeds(self):
        module = load_validator_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            source = write_json(valid_document(), tmpdir)
            code, stdout, stderr = call_main(module, ["--from-dsl", str(source), "--static"])
        self.assertEqual(0, code)
        self.assertIn("Mermaid validation succeeded", stdout)
        self.assertIn("static mode", stdout)
        self.assertEqual("", stderr)

    def test_missing_dsl_file_exits_2_with_read_error(self):
        module = load_validator_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "missing.dsl.json"
            code, stdout, stderr = call_main(module, ["--from-dsl", str(source), "--static"])
        self.assertEqual(2, code)
        self.assertEqual("", stdout)
        self.assertIn("ERROR", stderr)
        self.assertIn("could not read file", stderr)

    def test_directory_path_as_dsl_exits_2_with_read_error(self):
        module = load_validator_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            code, stdout, stderr = call_main(module, ["--from-dsl", tmpdir, "--static"])
        self.assertEqual(2, code)
        self.assertEqual("", stdout)
        self.assertIn("ERROR", stderr)
        self.assertIn("could not read file", stderr)

    def test_invalid_json_exits_2_with_invalid_json_error(self):
        module = load_validator_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "invalid.dsl.json"
            source.write_text("{", encoding="utf-8")
            code, stdout, stderr = call_main(module, ["--from-dsl", str(source), "--static"])
        self.assertEqual(2, code)
        self.assertEqual("", stdout)
        self.assertIn("ERROR", stderr)
        self.assertIn("invalid JSON", stderr)

    def test_non_object_dsl_root_exits_2_without_traceback(self):
        module = load_validator_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            source = write_json([], tmpdir)
            code, stdout, stderr = call_main(module, ["--from-dsl", str(source), "--static"])
        self.assertEqual(2, code)
        self.assertEqual("", stdout)
        self.assertIn("ERROR", stderr)
        self.assertIn("DSL root must be an object", stderr)
        self.assertNotIn("Traceback", stderr)

    def test_non_object_known_dsl_sections_exit_2_without_traceback(self):
        module = load_validator_module()
        for section_name in ["runtime_view", "architecture_views"]:
            with self.subTest(section_name=section_name):
                document = valid_document()
                document[section_name] = []
                with tempfile.TemporaryDirectory() as tmpdir:
                    source = write_json(document, tmpdir)
                    code, stdout, stderr = call_main(module, ["--from-dsl", str(source), "--static"])
                self.assertEqual(2, code)
                self.assertEqual("", stdout)
                self.assertIn("ERROR", stderr)
                self.assertIn("must be an object", stderr)
                self.assertIn(f"$.{section_name}", stderr)
                self.assertNotIn("Traceback", stderr)

    def test_dsl_static_rejects_diagram_type_first_line_mismatch(self):
        module = load_validator_module()
        document = valid_document()
        diagram = document["runtime_view"]["runtime_flow_diagram"]
        diagram["id"] = "MER-RUNTIME-MISMATCH"
        diagram["diagram_type"] = "sequenceDiagram"
        diagram["source"] = "flowchart TD\n  A --> B"
        with tempfile.TemporaryDirectory() as tmpdir:
            source = write_json(document, tmpdir)
            code, stdout, stderr = call_main(module, ["--from-dsl", str(source), "--static"])
        self.assertEqual(1, code)
        self.assertEqual("", stdout)
        self.assertIn("$.runtime_view.runtime_flow_diagram", stderr)
        self.assertIn("MER-RUNTIME-MISMATCH", stderr)
        self.assertIn(
            "first meaningful line starts with flowchart but diagram_type is sequenceDiagram",
            stderr,
        )

    def test_dsl_static_rejects_unsupported_diagram_type(self):
        module = load_validator_module()
        document = valid_document()
        document["runtime_view"]["runtime_flow_diagram"]["diagram_type"] = "erDiagram"
        with tempfile.TemporaryDirectory() as tmpdir:
            source = write_json(document, tmpdir)
            code, stdout, stderr = call_main(module, ["--from-dsl", str(source), "--static"])
        self.assertEqual(1, code)
        self.assertIn("$.runtime_view.runtime_flow_diagram", stderr)
        self.assertIn("unsupported diagram_type erDiagram", stderr)

    def test_optional_full_runtime_sequence_diagram_with_empty_source_is_skipped(self):
        module = load_validator_module()
        document = valid_document()
        document["runtime_view"]["runtime_sequence_diagram"] = self.diagram(
            "MER-RUNTIME-SEQUENCE-EMPTY",
            diagram_type="sequenceDiagram",
            source="",
        )
        diagrams = module.extract_diagrams_from_dsl(document)
        self.assertNotIn("MER-RUNTIME-SEQUENCE-EMPTY", {diagram.diagram_id for diagram in diagrams})

    def test_duplicate_diagram_ids_fail_for_dsl_input(self):
        module = load_validator_module()
        document = valid_document()
        document["runtime_view"]["runtime_flow_diagram"]["id"] = "MER-DUPLICATE"
        document["cross_module_collaboration"]["collaboration_relationship_diagram"]["id"] = "MER-DUPLICATE"
        with tempfile.TemporaryDirectory() as tmpdir:
            source = write_json(document, tmpdir)
            code, stdout, stderr = call_main(module, ["--from-dsl", str(source), "--static"])
        self.assertEqual(1, code)
        self.assertEqual("", stdout)
        self.assertIn("duplicate diagram id MER-DUPLICATE", stderr)
        self.assertIn("$.runtime_view.runtime_flow_diagram", stderr)
        self.assertIn("$.cross_module_collaboration.collaboration_relationship_diagram", stderr)

    def test_markdown_fences_inside_dsl_source_fail(self):
        module = load_validator_module()
        document = valid_document()
        document["architecture_views"]["module_relationship_diagram"]["source"] = (
            "```mermaid\nflowchart TD\n  A --> B\n```"
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            source = write_json(document, tmpdir)
            code, stdout, stderr = call_main(module, ["--from-dsl", str(source), "--static"])
        self.assertEqual(1, code)
        self.assertIn("$.architecture_views.module_relationship_diagram", stderr)
        self.assertIn("must not include Markdown code fences", stderr)

    def test_type_inference_fails_closed_for_unsupported_prefixes(self):
        module = load_validator_module()
        for first_line in ["graphical TD", "flowchartish TD", "stateDiagram-v20"]:
            with self.subTest(first_line=first_line):
                document = valid_document()
                document["architecture_views"]["module_relationship_diagram"]["source"] = first_line
                with tempfile.TemporaryDirectory() as tmpdir:
                    source = write_json(document, tmpdir)
                    code, stdout, stderr = call_main(module, ["--from-dsl", str(source), "--static"])
                self.assertEqual(1, code)
                self.assertEqual("", stdout)
                self.assertIn(
                    "first meaningful line does not start with a supported Mermaid diagram type",
                    stderr,
                )


if __name__ == "__main__":
    unittest.main()
