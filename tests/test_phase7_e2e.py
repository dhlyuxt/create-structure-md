import json
import re
import unittest
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PHASE7_TMP_ROOT = ROOT / ".codex-tmp/create-structure-md-phase7-tests"
EXAMPLE_PATHS = [
    ROOT / "examples/minimal-from-code.dsl.json",
    ROOT / "examples/minimal-from-requirements.dsl.json",
]
POLICY_FIELD_NAMES = {"empty_allowed", "required", "min_rows"}


def make_run_dir(name):
    run_dir = PHASE7_TMP_ROOT / f"{name}-{uuid.uuid4().hex}"
    run_dir.mkdir(parents=True, exist_ok=False)
    return run_dir


def walk_json(value, path="$"):
    yield path, value
    if isinstance(value, dict):
        for key, child in value.items():
            yield from walk_json(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from walk_json(child, f"{path}[{index}]")


def non_empty_rows(document, *path):
    value = document
    for key in path:
        value = value[key]
    rows = value["rows"] if isinstance(value, dict) else value
    return [row for row in rows if row]


class Phase7ReferenceDocumentationTests(unittest.TestCase):
    REQUIRED_PHRASES = {
        "references/dsl-spec.md": [
            "Input Readiness Contract",
            "DSL Top-Level Fields",
            "Common Metadata",
            "ID Prefix Conventions",
            "Defining ID Fields And Reference ID Fields",
            "Authoritative Field Contract",
            "Fixed Table Row Fields",
            "Support Data Object Shapes",
            "Traceability Target Mapping",
            "Validation Policy Outside DSL",
            "Source Snippet Rules",
            "empty_allowed",
            "required",
            "min_rows",
        ],
        "references/document-structure.md": [
            "fixed 9-chapter outline",
            "Fixed Subchapter Numbering",
            "Chapter-By-Chapter Rendering Positions",
            "Fixed Table Visible Columns",
            "Empty-State Sentences",
            "Table-Row Support-Data Placement",
            "Chapter 9 Rendering Behavior",
            "output filename policy",
            "module- or system-specific",
            "Generic-only filenames are forbidden",
        ],
        "references/mermaid-rules.md": [
            "Mermaid-Only Output Rule",
            "Supported MVP Diagram Types",
            "Unsupported Diagram Types",
            "Diagram Field Policy",
            "DSL Source Without Fences",
            "Strict/Static Validation Difference",
            "CLI Examples",
            "Graphviz/DOT Rejection",
            "Static-Only Acceptance Reporting",
            "flowchart",
            "graph",
            "sequenceDiagram",
            "classDiagram",
            "stateDiagram-v2",
            "--work-dir",
            "no final Graphviz/DOT/SVG/PNG/PDF/image deliverables",
        ],
        "references/review-checklist.md": [
            "no repo analysis",
            "module- or system-specific output file",
            "generic filename rejection",
            "final output path",
            "temporary work directory",
            "default output overwrite protection",
            "`--overwrite`",
            "`--backup`",
            "Mermaid-only diagram output",
            "strict Mermaid validation",
            "static-only Mermaid fallback reporting",
            "Graphviz fully removed",
            "no final image artifacts",
            "no Jinja2",
            "validation policy outside DSL",
            "low-confidence summary whitelist",
            "source snippet secret review",
            "fixed 9 chapters",
            "fixed numbering",
            "post-render Markdown Mermaid validation",
        ],
    }

    SKILL_WORKFLOW_PHRASES = [
        "Create a temporary work directory.",
        "Read references/dsl-spec.md before writing DSL content.",
        "Write one complete DSL JSON file.",
        "Run `python scripts/validate_dsl.py structure.dsl.json`.",
        "Read references/mermaid-rules.md before creating/revising Mermaid.",
        "Run `python scripts/validate_mermaid.py --from-dsl structure.dsl.json --strict --work-dir <temporary-work-directory>/mermaid`.",
        "Render exactly one document with `python scripts/render_markdown.py structure.dsl.json --output-dir <output-dir>`.",
        "Run `python scripts/validate_mermaid.py --from-markdown <output-file> --static`.",
        "Review with references/review-checklist.md.",
        "Report output path, temporary work directory, assumptions, low-confidence items, and static-only Mermaid acceptance.",
        "if local Mermaid CLI tooling unavailable, stop and ask user before static-only validation",
        "Mermaid diagrams were not proven renderable by Mermaid CLI",
        "tooling unavailable",
        "user explicitly accepts static-only validation",
        "references/dsl-spec.md",
        "references/document-structure.md",
        "references/mermaid-rules.md",
        "references/review-checklist.md",
    ]

    def test_reference_files_contain_phase7_contracts(self):
        for relative_path, phrases in self.REQUIRED_PHRASES.items():
            text = (ROOT / relative_path).read_text(encoding="utf-8").casefold()
            for phrase in phrases:
                with self.subTest(path=relative_path, phrase=phrase):
                    self.assertIn(phrase.casefold(), text)

    def test_skill_workflow_contains_reference_contract(self):
        text = (ROOT / "SKILL.md").read_text(encoding="utf-8").casefold()
        for phrase in self.SKILL_WORKFLOW_PHRASES:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase.casefold(), text)


class Phase7ExampleContractTests(unittest.TestCase):
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

    def load_example(self, path):
        return json.loads(path.read_text(encoding="utf-8"))

    def assert_non_empty_text(self, value, label):
        self.assertIsInstance(value, str, label)
        self.assertTrue(value.strip(), label)

    def assert_module_specific_output_file(self, output_file):
        self.assertTrue(
            output_file.endswith("_STRUCTURE_DESIGN.md"),
            f"{output_file} must end with _STRUCTURE_DESIGN.md",
        )
        self.assertNotIn(output_file.casefold(), self.GENERIC_OUTPUT_NAMES)
        prefix = output_file[: -len("_STRUCTURE_DESIGN.md")]
        tokens = {token for token in re.split(r"[^0-9A-Za-z\u4e00-\u9fff]+", prefix.casefold()) if token}
        self.assertTrue(tokens, f"{output_file} must include a project/module prefix")
        self.assertFalse(
            tokens <= self.GENERIC_OUTPUT_TOKENS,
            f"{output_file} must not be generic-only",
        )

    def assert_source_snippet_matches_file_slice(self, snippet):
        snippet_path = (ROOT / snippet["path"]).resolve()
        try:
            snippet_path.relative_to(ROOT.resolve())
        except ValueError:
            self.fail(f"{snippet['id']} path must resolve under repository root")

        lines = snippet_path.read_text(encoding="utf-8").splitlines()
        expected_content = "\n".join(lines[snippet["line_start"] - 1 : snippet["line_end"]])
        self.assertEqual(expected_content, snippet["content"], snippet["id"])

    def test_examples_have_no_policy_fields_or_graphviz_content(self):
        graphviz_patterns = [
            re.compile(r"(?im)^\s*digraph\b"),
            re.compile(r"(?im)^\s*rankdir\s*="),
        ]
        for path in EXAMPLE_PATHS:
            text = path.read_text(encoding="utf-8")
            document = json.loads(text)
            with self.subTest(path=path.name):
                for json_path, value in walk_json(document):
                    if isinstance(value, dict):
                        policy_keys = POLICY_FIELD_NAMES & set(value)
                        self.assertFalse(policy_keys, f"{json_path} contains policy keys {sorted(policy_keys)}")
                lowered = text.casefold()
                self.assertNotIn("```dot", lowered)
                self.assertNotIn("```graphviz", lowered)
                for pattern in graphviz_patterns:
                    self.assertIsNone(pattern.search(text), pattern.pattern)

    def test_examples_cover_minimum_fixed_chapter_content(self):
        for path in EXAMPLE_PATHS:
            document = self.load_example(path)
            with self.subTest(path=path.name):
                self.assert_module_specific_output_file(document["document"]["output_file"])
                self.assert_non_empty_text(document["system_overview"]["summary"], "system overview summary")
                self.assertGreaterEqual(len(document["system_overview"]["core_capabilities"]), 1)

                module_intro_rows = non_empty_rows(document, "architecture_views", "module_intro")
                module_design_modules = document["module_design"]["modules"]
                self.assertGreaterEqual(len(module_intro_rows), 1)
                self.assert_non_empty_text(
                    document["architecture_views"]["module_relationship_diagram"]["source"],
                    "module relationship source",
                )
                self.assertEqual(len(module_intro_rows), len(module_design_modules))

                for module in module_design_modules:
                    with self.subTest(path=path.name, module=module["module_id"]):
                        capabilities = non_empty_rows(
                            module,
                            "external_capability_details",
                            "provided_capabilities",
                        )
                        self.assertGreaterEqual(len(capabilities), 1)
                        internal = module["internal_structure"]
                        has_diagram = bool(internal["diagram"]["source"].strip())
                        has_text = bool(internal["textual_structure"].strip())
                        self.assertTrue(has_diagram or has_text)

                self.assertGreaterEqual(len(non_empty_rows(document, "runtime_view", "runtime_units")), 1)
                self.assert_non_empty_text(
                    document["runtime_view"]["runtime_flow_diagram"]["source"],
                    "runtime flow source",
                )

                chapter_6 = document["configuration_data_dependencies"]
                for table_key in ("configuration_items", "structural_data_artifacts", "dependencies"):
                    self.assertIn(table_key, chapter_6)
                    self.assertIn("rows", chapter_6[table_key])

                self.assertGreaterEqual(len(non_empty_rows(document, "key_flows", "flow_index")), 1)
                self.assertGreaterEqual(len(document["key_flows"]["flows"]), 1)
                for flow in document["key_flows"]["flows"]:
                    with self.subTest(path=path.name, flow=flow["flow_id"]):
                        self.assertGreaterEqual(len(flow["steps"]), 1)
                        self.assert_non_empty_text(flow["diagram"]["source"], "flow diagram source")

                self.assertIn("structure_issues_and_suggestions", document)
                for support_key in ("evidence", "traceability", "risks", "assumptions", "source_snippets"):
                    self.assertIn(support_key, document)
                    self.assertIsInstance(document[support_key], list)
                for snippet in document["source_snippets"]:
                    with self.subTest(path=path.name, source_snippet=snippet["id"]):
                        self.assert_source_snippet_matches_file_slice(snippet)

    def test_examples_collectively_exercise_support_data_and_low_confidence(self):
        examples = [self.load_example(path) for path in EXAMPLE_PATHS]

        self.assertTrue(any(example["evidence"] for example in examples), "missing evidence coverage")
        self.assertTrue(any(example["traceability"] for example in examples), "missing traceability coverage")
        self.assertTrue(any(example["risks"] or example["assumptions"] for example in examples), "missing risk or assumption coverage")
        self.assertTrue(any(example["source_snippets"] for example in examples), "missing source snippet coverage")

        low_confidence_items = []
        for example in examples:
            low_confidence_items.extend(
                row
                for row in example["architecture_views"]["module_intro"]["rows"]
                if row.get("confidence") == "unknown"
            )
            low_confidence_items.extend(
                module
                for module in example["module_design"]["modules"]
                if module.get("confidence") == "unknown"
            )
        self.assertTrue(low_confidence_items, "missing low-confidence module intro or module design coverage")
