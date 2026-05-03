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
    "Report output path",
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
        self.assertIn("If local Mermaid CLI tooling unavailable, stop and ask user before static-only validation", self.text)
        self.assertIn("Mermaid diagrams were not proven renderable by Mermaid CLI", self.text)
        self.assertIn("user explicitly accepts static-only validation", self.text)

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


class MarkdownMermaidStaticTests(unittest.TestCase):
    def test_from_markdown_static_accepts_all_supported_types_and_skips_comments_and_init(self):
        module = load_validator_module()
        markdown = """# Output

```mermaid

%% comment
%%{init: {"theme": "base"}}%%
flowchart TD
  A --> B
```

```mermaid
graph LR
  A --- B
```

```mermaid
sequenceDiagram
  A->>B: call
```

```mermaid
classDiagram
  class Renderer
```

```mermaid
stateDiagram-v2
  [*] --> Ready
```
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = write_markdown(tmpdir, "output.md", markdown)
            code, stdout, stderr = call_main(module, ["--from-markdown", str(path), "--static"])

        self.assertEqual(0, code, stderr)
        self.assertIn("Mermaid validation succeeded: 5 diagram(s) checked in static mode.", stdout)
        self.assertEqual("", stderr)

    def test_markdown_static_ignores_non_mermaid_fence_with_info_string(self):
        module = load_validator_module()
        markdown = '''```python linenums="1"
print("not mermaid")
```
'''
        with tempfile.TemporaryDirectory() as tmpdir:
            path = write_markdown(tmpdir, "python.md", markdown)
            code, stdout, stderr = call_main(module, ["--from-markdown", str(path), "--static"])

        self.assertEqual(0, code, stderr)
        self.assertIn("Mermaid validation succeeded: 0 diagram(s) checked in static mode.", stdout)
        self.assertEqual("", stderr)

    def test_markdown_static_accepts_mermaid_fence_with_info_string(self):
        module = load_validator_module()
        markdown = '''```mermaid title="x"
flowchart TD
  A --> B
```
'''
        with tempfile.TemporaryDirectory() as tmpdir:
            path = write_markdown(tmpdir, "mermaid-info.md", markdown)
            code, stdout, stderr = call_main(module, ["--from-markdown", str(path), "--static"])

        self.assertEqual(0, code, stderr)
        self.assertIn("Mermaid validation succeeded: 1 diagram(s) checked in static mode.", stdout)
        self.assertEqual("", stderr)

    def test_markdown_static_does_not_close_fence_on_inner_fence_with_info_string(self):
        module = load_validator_module()
        markdown = '''```python
print("not mermaid")
```js
console.log("still inside python fence")
```
'''
        with tempfile.TemporaryDirectory() as tmpdir:
            path = write_markdown(tmpdir, "inner-info.md", markdown)
            code, stdout, stderr = call_main(module, ["--from-markdown", str(path), "--static"])

        self.assertEqual(0, code, stderr)
        self.assertIn("Mermaid validation succeeded: 0 diagram(s) checked in static mode.", stdout)
        self.assertEqual("", stderr)

    def test_markdown_static_ignores_four_space_indented_mermaid_fence(self):
        module = load_validator_module()
        markdown = """    ```mermaid
    flowchart TD
      A --> B
    ```
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = write_markdown(tmpdir, "indented.md", markdown)
            code, stdout, stderr = call_main(module, ["--from-markdown", str(path), "--static"])

        self.assertEqual(0, code, stderr)
        self.assertIn("Mermaid validation succeeded: 0 diagram(s) checked in static mode.", stdout)
        self.assertEqual("", stderr)

    def test_markdown_static_rejects_empty_mermaid_block_with_line_number(self):
        module = load_validator_module()
        markdown = "# Output\n\n```mermaid\n\n```\n"
        with tempfile.TemporaryDirectory() as tmpdir:
            path = write_markdown(tmpdir, "empty.md", markdown)
            code, stdout, stderr = call_main(module, ["--from-markdown", str(path), "--static"])

        self.assertEqual(1, code)
        self.assertEqual("", stdout)
        self.assertIn("Mermaid block 1 line 3", stderr)
        self.assertIn("Mermaid block body must be non-empty", stderr)

    def test_from_markdown_directory_path_exits_two_with_read_error(self):
        module = load_validator_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            code, stdout, stderr = call_main(module, ["--from-markdown", tmpdir, "--static"])

        self.assertEqual(2, code)
        self.assertEqual("", stdout)
        self.assertIn("ERROR", stderr)
        self.assertIn("could not read file", stderr)

    def test_markdown_static_rejects_missing_or_unsupported_inferred_type(self):
        module = load_validator_module()
        markdown = """```mermaid
A --> B
```

```mermaid
erDiagram
  CUSTOMER ||--o{ ORDER : places
```
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = write_markdown(tmpdir, "unsupported.md", markdown)
            code, stdout, stderr = call_main(module, ["--from-markdown", str(path), "--static"])

        self.assertEqual(1, code)
        self.assertIn("Mermaid block 1 line 1", stderr)
        self.assertIn("could not infer supported Mermaid diagram type", stderr)
        self.assertIn("Mermaid block 2 line 5", stderr)
        self.assertIn("unsupported Mermaid diagram type erDiagram", stderr)

    def test_markdown_static_rejects_unbalanced_fences(self):
        module = load_validator_module()
        markdown = "# Output\n\n```mermaid\nflowchart TD\n  A --> B\n"
        with tempfile.TemporaryDirectory() as tmpdir:
            path = write_markdown(tmpdir, "unbalanced.md", markdown)
            code, stdout, stderr = call_main(module, ["--from-markdown", str(path), "--static"])

        self.assertEqual(1, code)
        self.assertIn("Mermaid block 1 line 3", stderr)
        self.assertIn("unbalanced fenced code block starting at line 3", stderr)

    def test_markdown_static_rejects_unclosed_non_mermaid_fence_with_markdown_line(self):
        module = load_validator_module()
        markdown = "# Output\n\n```python\nprint('not mermaid')\n"
        with tempfile.TemporaryDirectory() as tmpdir:
            path = write_markdown(tmpdir, "unclosed-python.md", markdown)
            code, stdout, stderr = call_main(module, ["--from-markdown", str(path), "--static"])

        self.assertEqual(1, code)
        self.assertEqual("", stdout)
        self.assertIn("Markdown line 3", stderr)
        self.assertIn("unbalanced fenced code block starting at line 3", stderr)


class MermaidStaticBoundaryTests(unittest.TestCase):
    def test_static_rejects_graphviz_digraph_and_rankdir(self):
        module = load_validator_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            document["architecture_views"]["module_relationship_diagram"]["source"] = "digraph G {\n  rankdir=LR;\n  A -> B;\n}"
            path = write_json(document, tmpdir, "dot.dsl.json")
            code, stdout, stderr = call_main(module, ["--from-dsl", str(path), "--static"])

        self.assertEqual(1, code)
        self.assertEqual("", stdout)
        self.assertIn("$.architecture_views.module_relationship_diagram", stderr)
        self.assertIn("Graphviz/DOT syntax is not supported", stderr)
        self.assertIn("line 1", stderr)

    def test_static_allows_common_mermaid_arrows(self):
        module = load_validator_module()
        markdown = """```mermaid
flowchart TD
  A --> B
  B --- C
  C -->|label| D
```

```mermaid
sequenceDiagram
  A->>B: call
  B->C: return
```
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = write_markdown(tmpdir, "arrows.md", markdown)
            code, stdout, stderr = call_main(module, ["--from-markdown", str(path), "--static"])

        self.assertEqual(0, code, stderr)
        self.assertIn("2 diagram(s)", stdout)

    def test_static_rejects_dot_style_single_arrow_statement_without_rejecting_sequence_arrows(self):
        module = load_validator_module()
        markdown = """```mermaid
flowchart TD
  node -> other;
```
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = write_markdown(tmpdir, "dot-arrow.md", markdown)
            code, stdout, stderr = call_main(module, ["--from-markdown", str(path), "--static"])

        self.assertEqual(1, code)
        self.assertIn("Mermaid block 1 line 1", stderr)
        self.assertIn("Graphviz/DOT syntax is not supported", stderr)
        self.assertIn("line 2", stderr)

    def test_static_rejects_graphviz_graph_keyword_in_dsl(self):
        module = load_validator_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            diagram = document["architecture_views"]["module_relationship_diagram"]
            diagram["diagram_type"] = "graph"
            diagram["source"] = "graph G {\n  A -- B;\n}"
            path = write_json(document, tmpdir, "dot-graph.dsl.json")
            code, stdout, stderr = call_main(module, ["--from-dsl", str(path), "--static"])

        self.assertEqual(1, code)
        self.assertEqual("", stdout)
        self.assertIn("Graphviz/DOT syntax is not supported", stderr)
        self.assertIn("line 1", stderr)

    def test_static_rejects_graphviz_graph_keyword_in_markdown(self):
        module = load_validator_module()
        markdown = """```mermaid
graph G {
  A -- B;
}
```
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = write_markdown(tmpdir, "dot-graph.md", markdown)
            code, stdout, stderr = call_main(module, ["--from-markdown", str(path), "--static"])

        self.assertEqual(1, code)
        self.assertIn("Mermaid block 1 line 1", stderr)
        self.assertIn("Graphviz/DOT syntax is not supported", stderr)

    def test_static_rejects_dot_edge_with_attributes(self):
        module = load_validator_module()
        markdown = """```mermaid
flowchart TD
  A -> B [label="calls"];
```
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = write_markdown(tmpdir, "dot-attribute.md", markdown)
            code, stdout, stderr = call_main(module, ["--from-markdown", str(path), "--static"])

        self.assertEqual(1, code)
        self.assertIn("Graphviz/DOT syntax is not supported", stderr)
        self.assertIn("line 2", stderr)

    def test_static_rejects_dot_edge_with_quoted_ids(self):
        module = load_validator_module()
        markdown = """```mermaid
flowchart TD
  "A node" -> "B node";
```
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = write_markdown(tmpdir, "dot-quoted.md", markdown)
            code, stdout, stderr = call_main(module, ["--from-markdown", str(path), "--static"])

        self.assertEqual(1, code)
        self.assertIn("Graphviz/DOT syntax is not supported", stderr)
        self.assertIn("line 2", stderr)

    def test_static_reports_dot_syntax_and_duplicate_dsl_ids_together(self):
        module = load_validator_module()
        document = valid_document()
        document["runtime_view"]["runtime_flow_diagram"]["id"] = "MER-DUPLICATE-DOT"
        document["runtime_view"]["runtime_flow_diagram"]["source"] = "digraph G {\n  A -> B;\n}"
        document["cross_module_collaboration"]["collaboration_relationship_diagram"]["id"] = "MER-DUPLICATE-DOT"
        with tempfile.TemporaryDirectory() as tmpdir:
            path = write_json(document, tmpdir, "duplicate-dot.dsl.json")
            code, stdout, stderr = call_main(module, ["--from-dsl", str(path), "--static"])

        self.assertEqual(1, code)
        self.assertEqual("", stdout)
        self.assertIn("Graphviz/DOT syntax is not supported", stderr)
        self.assertIn("duplicate diagram id MER-DUPLICATE-DOT", stderr)


class MermaidStrictValidationTests(unittest.TestCase):
    def call_main_without_traceback(self, module, args):
        try:
            return call_main(module, args)
        except Exception as exc:
            self.fail(f"unexpected exception {type(exc).__name__}: {exc}")

    def fake_strict_tooling(self, name):
        return {"node": "/usr/bin/node", "mmdc": "mmdc"}.get(name)

    def test_default_mode_is_strict_and_missing_tooling_is_explicit(self):
        module = load_validator_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            source = write_json(valid_document(), tmpdir)
            with mock.patch.object(module.shutil, "which", return_value=None):
                code, stdout, stderr = call_main(module, ["--from-dsl", str(source)])

        self.assertEqual(1, code)
        self.assertEqual("", stdout)
        self.assertIn("Mermaid strict validation was not performed", stderr)
        self.assertIn("local Mermaid CLI tooling unavailable", stderr)
        self.assertIn("mmdc", stderr)
        self.assertNotIn("proven renderable", stdout + stderr)

    def test_strict_mode_writes_mmd_files_and_preserves_work_dir_artifacts(self):
        module = load_validator_module()

        def fake_which(name):
            return {"node": "/usr/bin/node", "mmdc": "/usr/local/bin/mmdc"}.get(name)

        completed = subprocess.CompletedProcess(["mmdc"], 0, stdout="", stderr="")
        with tempfile.TemporaryDirectory() as tmpdir:
            source = write_json(valid_document(), tmpdir)
            work_dir = Path(tmpdir) / "mermaid-work"
            with (
                mock.patch.object(module.shutil, "which", side_effect=fake_which),
                mock.patch.object(module.subprocess, "run", return_value=completed) as mocked_run,
            ):
                code, stdout, stderr = call_main(
                    module,
                    ["--from-dsl", str(source), "--strict", "--work-dir", str(work_dir)],
                )

            self.assertEqual(0, code, stderr)
            self.assertIn("Mermaid validation succeeded", stdout)
            self.assertIn("strict mode", stdout)
            self.assertEqual("", stderr)
            self.assertTrue((work_dir / "MER-ARCH-MODULES.mmd").is_file())
            self.assertTrue((work_dir / "MER-ARCH-MODULES.svg").parent.is_dir())
            first_command = mocked_run.call_args_list[0].args[0]
            self.assertEqual("/usr/local/bin/mmdc", first_command[0])
            self.assertIn("-i", first_command)
            self.assertIn("-o", first_command)
            input_path = Path(first_command[first_command.index("-i") + 1])
            output_path = Path(first_command[first_command.index("-o") + 1])
            self.assertEqual(work_dir / "MER-ARCH-MODULES.mmd", input_path)
            self.assertEqual(work_dir / "MER-ARCH-MODULES.svg", output_path)

    def test_default_strict_mode_accepts_work_dir_without_explicit_strict_flag_for_dsl(self):
        module = load_validator_module()

        def fake_which(name):
            return {"node": "/usr/bin/node", "mmdc": "/usr/local/bin/mmdc"}.get(name)

        completed = subprocess.CompletedProcess(["mmdc"], 0, stdout="", stderr="")
        with tempfile.TemporaryDirectory() as tmpdir:
            source = write_json(valid_document(), tmpdir)
            work_dir = Path(tmpdir) / "mermaid-work"
            with (
                mock.patch.object(module.shutil, "which", side_effect=fake_which),
                mock.patch.object(module.subprocess, "run", return_value=completed),
            ):
                code, stdout, stderr = call_main(
                    module,
                    ["--from-dsl", str(source), "--work-dir", str(work_dir)],
                )

            self.assertEqual(0, code, stderr)
            self.assertIn("strict mode", stdout)
            self.assertEqual("", stderr)
            self.assertTrue((work_dir / "MER-ARCH-MODULES.mmd").is_file())

    def test_default_strict_mode_accepts_work_dir_without_explicit_strict_flag_for_markdown(self):
        module = load_validator_module()

        def fake_which(name):
            return {"node": "/usr/bin/node", "mmdc": "/usr/local/bin/mmdc"}.get(name)

        completed = subprocess.CompletedProcess(["mmdc"], 0, stdout="", stderr="")
        markdown = """# Output

```mermaid
flowchart TD
  A --> B
```
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            source = write_markdown(tmpdir, "output.md", markdown)
            work_dir = Path(tmpdir) / "mermaid-work"
            with (
                mock.patch.object(module.shutil, "which", side_effect=fake_which),
                mock.patch.object(module.subprocess, "run", return_value=completed),
            ):
                code, stdout, stderr = call_main(
                    module,
                    ["--from-markdown", str(source), "--work-dir", str(work_dir)],
                )

            self.assertEqual(0, code, stderr)
            self.assertIn("strict mode", stdout)
            self.assertEqual("", stderr)
            self.assertTrue((work_dir / "markdown-block-1.mmd").is_file())

    def test_strict_mode_reports_mmdc_failure_with_diagram_location(self):
        module = load_validator_module()

        def fake_which(name):
            return {"node": "/usr/bin/node", "mmdc": "/usr/local/bin/mmdc"}.get(name)

        completed = subprocess.CompletedProcess(
            ["mmdc"],
            1,
            stdout="",
            stderr="Parse error on line 2",
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            source = write_json(valid_document(), tmpdir)
            with (
                mock.patch.object(module.shutil, "which", side_effect=fake_which),
                mock.patch.object(module.subprocess, "run", return_value=completed),
            ):
                code, stdout, stderr = call_main(module, ["--from-dsl", str(source), "--strict"])

        self.assertEqual(1, code)
        self.assertEqual("", stdout)
        self.assertIn("$.architecture_views.module_relationship_diagram", stderr)
        self.assertIn("MER-ARCH-MODULES", stderr)
        self.assertIn("mmdc failed", stderr)
        self.assertIn("Parse error on line 2", stderr)

    def test_strict_dsl_static_errors_stop_before_mmdc(self):
        module = load_validator_module()

        def fake_which(name):
            return {"node": "/usr/bin/node", "mmdc": "/usr/local/bin/mmdc"}.get(name)

        with tempfile.TemporaryDirectory() as tmpdir:
            document = valid_document()
            document["architecture_views"]["module_relationship_diagram"]["source"] = (
                "digraph G {\n  A -> B;\n}"
            )
            source = write_json(document, tmpdir)
            with (
                mock.patch.object(module.shutil, "which", side_effect=fake_which),
                mock.patch.object(module.subprocess, "run") as mocked_run,
            ):
                code, stdout, stderr = call_main(module, ["--from-dsl", str(source), "--strict"])

        self.assertEqual(1, code)
        self.assertEqual("", stdout)
        self.assertIn("Graphviz/DOT", stderr)
        mocked_run.assert_not_called()

    def test_strict_markdown_unbalanced_fence_stops_before_mmdc(self):
        module = load_validator_module()

        def fake_which(name):
            return {"node": "/usr/bin/node", "mmdc": "/usr/local/bin/mmdc"}.get(name)

        markdown = "# Output\n\n```mermaid\nflowchart TD\n  A --> B\n"
        with tempfile.TemporaryDirectory() as tmpdir:
            source = write_markdown(tmpdir, "unbalanced.md", markdown)
            with (
                mock.patch.object(module.shutil, "which", side_effect=fake_which),
                mock.patch.object(module.subprocess, "run") as mocked_run,
            ):
                code, stdout, stderr = call_main(
                    module,
                    ["--from-markdown", str(source), "--strict"],
                )

        self.assertEqual(1, code)
        self.assertEqual("", stdout)
        self.assertIn("Mermaid block 1 line 3", stderr)
        self.assertIn("unbalanced fenced code block starting at line 3", stderr)
        mocked_run.assert_not_called()

    def test_strict_markdown_unsupported_type_stops_before_mmdc(self):
        module = load_validator_module()

        def fake_which(name):
            return {"node": "/usr/bin/node", "mmdc": "/usr/local/bin/mmdc"}.get(name)

        markdown = """```mermaid
erDiagram
  CUSTOMER ||--o{ ORDER : places
```
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            source = write_markdown(tmpdir, "unsupported.md", markdown)
            with (
                mock.patch.object(module.shutil, "which", side_effect=fake_which),
                mock.patch.object(module.subprocess, "run") as mocked_run,
            ):
                code, stdout, stderr = call_main(
                    module,
                    ["--from-markdown", str(source), "--strict"],
                )

        self.assertEqual(1, code)
        self.assertEqual("", stdout)
        self.assertIn("unsupported Mermaid diagram type erDiagram", stderr)
        mocked_run.assert_not_called()

    def test_strict_markdown_unclosed_non_mermaid_fence_stops_before_mmdc(self):
        module = load_validator_module()

        def fake_which(name):
            return {"node": "/usr/bin/node", "mmdc": "/usr/local/bin/mmdc"}.get(name)

        markdown = "# Output\n\n```python\nprint('not mermaid')\n"
        with tempfile.TemporaryDirectory() as tmpdir:
            source = write_markdown(tmpdir, "unclosed-python.md", markdown)
            with (
                mock.patch.object(module.shutil, "which", side_effect=fake_which),
                mock.patch.object(module.subprocess, "run") as mocked_run,
            ):
                code, stdout, stderr = call_main(
                    module,
                    ["--from-markdown", str(source), "--strict"],
                )

        self.assertEqual(1, code)
        self.assertEqual("", stdout)
        self.assertIn("Markdown line 3", stderr)
        self.assertIn("unbalanced fenced code block starting at line 3", stderr)
        mocked_run.assert_not_called()

    def test_strict_work_dir_existing_file_reports_preparation_error_without_traceback(self):
        module = load_validator_module()
        completed = subprocess.CompletedProcess(["mmdc"], 0, stdout="", stderr="")
        with tempfile.TemporaryDirectory() as tmpdir:
            source = write_json(valid_document(), tmpdir)
            work_dir = Path(tmpdir) / "requirements.txt"
            work_dir.write_text("not a directory", encoding="utf-8")
            with (
                mock.patch.object(module.shutil, "which", side_effect=self.fake_strict_tooling),
                mock.patch.object(module.subprocess, "run", return_value=completed),
            ):
                code, stdout, stderr = self.call_main_without_traceback(
                    module,
                    ["--from-dsl", str(source), "--strict", "--work-dir", str(work_dir)],
                )

        self.assertEqual(1, code)
        self.assertEqual("", stdout)
        self.assertIn("strict Mermaid validation", stderr)
        self.assertIn(str(work_dir), stderr)
        self.assertIn("could not prepare work directory", stderr)
        self.assertNotIn("Traceback", stderr)

    def test_strict_artifact_write_failure_reports_diagram_location_without_traceback(self):
        module = load_validator_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            source = write_json(valid_document(), tmpdir)
            with (
                mock.patch.object(module.shutil, "which", side_effect=self.fake_strict_tooling),
                mock.patch.object(module.Path, "write_text", side_effect=OSError("disk full")),
            ):
                code, stdout, stderr = self.call_main_without_traceback(
                    module,
                    ["--from-dsl", str(source), "--strict"],
                )

        self.assertEqual(1, code)
        self.assertEqual("", stdout)
        self.assertIn("$.architecture_views.module_relationship_diagram", stderr)
        self.assertIn("MER-ARCH-MODULES", stderr)
        self.assertIn(".mmd", stderr)
        self.assertIn("disk full", stderr)
        self.assertNotIn("Traceback", stderr)

    def test_strict_mmdc_start_failure_reports_diagram_location_without_traceback(self):
        module = load_validator_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            source = write_json(valid_document(), tmpdir)
            with (
                mock.patch.object(module.shutil, "which", side_effect=self.fake_strict_tooling),
                mock.patch.object(module.subprocess, "run", side_effect=FileNotFoundError("mmdc")),
            ):
                code, stdout, stderr = self.call_main_without_traceback(
                    module,
                    ["--from-dsl", str(source), "--strict"],
                )

        self.assertEqual(1, code)
        self.assertEqual("", stdout)
        self.assertIn("$.architecture_views.module_relationship_diagram", stderr)
        self.assertIn("MER-ARCH-MODULES", stderr)
        self.assertIn("mmdc failed to start", stderr)
        self.assertIn("mmdc", stderr)
        self.assertNotIn("Traceback", stderr)


class MermaidIntegrationRegressionTests(unittest.TestCase):
    def test_static_validation_accepts_both_minimal_examples(self):
        module = load_validator_module()
        for relative_path in [
            "examples/minimal-from-code.dsl.json",
            "examples/minimal-from-requirements.dsl.json",
        ]:
            with self.subTest(relative_path=relative_path):
                code, stdout, stderr = call_main(module, ["--from-dsl", str(ROOT / relative_path), "--static"])
                self.assertEqual(0, code, stderr)
                self.assertIn("Mermaid validation succeeded", stdout)
                self.assertEqual("", stderr)

    def test_requirements_remain_runtime_only(self):
        requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8")
        dependency_lines = [
            line.strip()
            for line in requirements.splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]
        self.assertEqual(["jsonschema"], dependency_lines)
        for forbidden in ["pytest", "markdown", "mermaid", "playwright", "selenium"]:
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, requirements)

    def test_mermaid_reference_rules_match_validator_supported_types(self):
        module = load_validator_module()
        text = (ROOT / "references/mermaid-rules.md").read_text(encoding="utf-8")
        for diagram_type in sorted(module.SUPPORTED_TYPES):
            with self.subTest(diagram_type=diagram_type):
                self.assertIn(diagram_type, text)
        self.assertIn("Graphviz", text)
        self.assertIn("DOT", text)

    def test_review_checklist_keeps_strict_or_static_acceptance_boundary_visible(self):
        text = (ROOT / "references/review-checklist.md").read_text(encoding="utf-8")
        self.assertIn("strict validation", text)
        self.assertIn("static-only validation", text)
        self.assertIn("explicit acceptance", text)
        self.assertIn("strict validation was not performed", text)
        self.assertIn("local Mermaid CLI tooling unavailable", text)
        self.assertIn("user accepted static-only validation", text)


if __name__ == "__main__":
    unittest.main()
