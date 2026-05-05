import contextlib
import importlib.util
import io
import json
import os
import re
import shutil
import subprocess
import sys
import unittest
import uuid
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
PHASE7_TMP_ROOT = ROOT / ".codex-tmp/create-structure-md-phase7-tests"
# Tests preserve artifacts for inspection; if cleanup is desired, show this command to the user instead of running it.
PHASE7_TMP_CLEANUP_NOTICE = f"Phase 7 artifacts are preserved; user cleanup command: rm -r {PHASE7_TMP_ROOT}"
PYTHON = sys.executable
EXAMPLE_PATHS = [
    ROOT / "examples/minimal-from-code.dsl.json",
    ROOT / "examples/minimal-from-requirements.dsl.json",
]
POLICY_FIELD_NAMES = {"empty_allowed", "required", "min_rows"}
V2_DEPENDENCY_TYPES = {
    "runtime",
    "library",
    "tool",
    "schema_contract",
    "documentation_contract",
    "dsl_contract",
    "internal_module",
    "data_object",
    "filesystem",
    "external_service",
    "test_fixture",
    "other",
}


def make_run_dir(name):
    safe_name = re.sub(r"[^0-9A-Za-z_.-]+", "_", name).strip("._") or "run"
    run_dir = PHASE7_TMP_ROOT / f"{safe_name}-{uuid.uuid4().hex}"
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def preserved_process_env(run_dir):
    temp_dir = run_dir / "tmp"
    cache_dir = run_dir / "xdg-cache"
    temp_dir.mkdir(parents=True, exist_ok=True)
    cache_dir.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env.update(
        {
            "TMPDIR": str(temp_dir),
            "TMP": str(temp_dir),
            "TEMP": str(temp_dir),
            "XDG_CACHE_HOME": str(cache_dir),
        }
    )
    return env


def run_command(*args, env=None):
    return subprocess.run(
        [PYTHON, *map(str, args)],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def load_script_module(relative_path, module_name):
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


def markdown_section(text, heading):
    start = text.find(heading)
    if start == -1:
        return ""
    next_heading = text.find("\n## ", start + len(heading))
    if next_heading == -1:
        return text[start:]
    return text[start:next_heading]


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
            "Mermaid readability artifact",
            "rendered diagram completeness",
            "strict rendered Markdown validation",
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
        "Write one complete DSL JSON file at `<temporary-work-directory>/structure.dsl.json`.",
        "Run `python scripts/validate_dsl.py <temporary-work-directory>/structure.dsl.json`.",
        "Read references/mermaid-rules.md before creating/revising Mermaid.",
        "Dispatch an independent Mermaid readability review subagent.",
        "Write `<temporary-work-directory>/mermaid-readability-review.json`.",
        "Run `python scripts/verify_v2_mermaid_gates.py <temporary-work-directory>/structure.dsl.json --mermaid-review-artifact <temporary-work-directory>/mermaid-readability-review.json --pre-render --work-dir <temporary-work-directory>/mermaid`.",
        "Render exactly one document with `python scripts/render_markdown.py <temporary-work-directory>/structure.dsl.json --output-dir <output-dir>`.",
        "Run `python scripts/verify_v2_mermaid_gates.py <temporary-work-directory>/structure.dsl.json --mermaid-review-artifact <temporary-work-directory>/mermaid-readability-review.json --rendered-markdown <output-file> --post-render --work-dir <temporary-work-directory>/mermaid`.",
        "Review with references/review-checklist.md.",
        "Report output path, temporary work directory, assumptions, low-confidence items, and Mermaid gate results.",
        "Static-only Mermaid validation is not final acceptance for V2 Phase 4",
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

    def test_dsl_spec_documents_exact_id_prefix_and_support_id_contracts(self):
        text = (ROOT / "references/dsl-spec.md").read_text(encoding="utf-8")
        prefix_section = markdown_section(text, "## ID Prefix Conventions")
        documented_prefixes = re.findall(r"`([A-Z]+-)`", prefix_section)
        self.assertEqual(
            [
                "MOD-",
                "CAP-",
                "RUN-",
                "FLOW-",
                "CFG-",
                "DATA-",
                "DEP-",
                "COL-",
                "STEP-",
                "BR-",
                "MER-",
                "TBL-",
                "EV-",
                "TR-",
                "RISK-",
                "ASM-",
                "SNIP-",
            ],
            documented_prefixes,
        )
        for misleading_prefix in ("IF-", "RU-", "SRC-"):
            with self.subTest(prefix=misleading_prefix):
                self.assertNotIn(misleading_prefix, prefix_section)

        for nonexistent_field in ("evidence_id", "traceability_id", "source_snippet_id"):
            with self.subTest(field=nonexistent_field):
                self.assertNotIn(nonexistent_field, text)
        for support_shape in ("`evidence[].id`", "`traceability[].id`", "`source_snippets[].id`"):
            with self.subTest(shape=support_shape):
                self.assertIn(support_shape, text)
        self.assertIn("`key_flows.flow_index.rows[]`", text)
        self.assertIn("index-only references", text)
        self.assertIn("do not carry `confidence`", text)

    def test_mermaid_rules_document_required_cli_examples(self):
        text = (ROOT / "references/mermaid-rules.md").read_text(encoding="utf-8")
        for command in [
            "python scripts/validate_mermaid.py --check-env",
            "python scripts/validate_mermaid.py --from-dsl structure.dsl.json --static",
            "python scripts/validate_mermaid.py --from-dsl structure.dsl.json --strict --work-dir <temporary-work-directory>/mermaid",
            "python scripts/validate_mermaid.py --from-markdown <output-file> --static",
        ]:
            with self.subTest(command=command):
                self.assertIn(command, text)

    def test_review_checklist_documents_final_review_sections_and_safety_points(self):
        text = (ROOT / "references/review-checklist.md").read_text(encoding="utf-8")
        for heading in [
            "## Final Report",
            "## Boundary Checks",
            "## DSL Policy Checks",
            "## Text Safety",
            "## Rendered Structure",
        ]:
            with self.subTest(heading=heading):
                self.assertIn(heading, text)

        final_report = markdown_section(text, "## Final Report")
        for phrase in [
            "assumptions",
            "low-confidence",
            "final output path",
            "temporary work directory",
            "default final-generation gate",
            "module- or system-specific output file path",
            "generic filename rejection is reported",
            "default output overwrite protection is reported",
        ]:
            with self.subTest(section="Final Report", phrase=phrase):
                self.assertIn(phrase, final_report)
        boundary_checks = markdown_section(text, "## Boundary Checks")
        for phrase in [
            "requirements inference",
            "Word/PDF output",
            "image export",
            "Graphviz output",
            "Jinja2 template rendering",
            "Markdown Mermaid fences, not image artifacts",
        ]:
            with self.subTest(section="Boundary Checks", phrase=phrase):
                self.assertIn(phrase, boundary_checks)
        for phrase in [
            "Markdown-capable field",
            "source snippets are evidence-only exceptions",
            "fixed table columns are owned by renderer/schema/reference docs",
            "required Mermaid diagrams are present",
            "post-render Markdown Mermaid validation",
        ]:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)

    def test_preserved_phase7_run_dirs_use_name_uuid_contract(self):
        fake_uuid = mock.Mock(hex="abcdef0123456789")
        with mock.patch.object(uuid, "uuid4", return_value=fake_uuid):
            run_dir = make_run_dir("phase 7 sample")

        self.assertEqual(PHASE7_TMP_ROOT / "phase_7_sample-abcdef0123456789", run_dir)
        self.assertTrue(run_dir.is_dir())
        self.assertEqual(PHASE7_TMP_ROOT, run_dir.parent)
        self.assertIn(f"rm -r {PHASE7_TMP_ROOT}", PHASE7_TMP_CLEANUP_NOTICE)

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
                self.assertEqual("0.2.0", document["dsl_version"])
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
                        self.assertIn("source_scope", module)
                        self.assertIn("configuration", module)
                        self.assertIn("dependencies", module)
                        self.assertIn("data_objects", module)
                        self.assertIn("public_interfaces", module)
                        self.assertIn("internal_mechanism", module)
                        self.assertIn("known_limitations", module)

                self.assertGreaterEqual(len(non_empty_rows(document, "runtime_view", "runtime_units")), 1)
                for unit in document["runtime_view"]["runtime_units"]["rows"]:
                    with self.subTest(path=path.name, runtime_unit=unit["unit_id"]):
                        self.assertNotIn("entrypoint_not_applicable_reason", unit)
                        self.assertNotIn("external_environment_reason", unit)
                self.assert_non_empty_text(
                    document["runtime_view"]["runtime_flow_diagram"]["source"],
                    "runtime flow source",
                )

                chapter_6 = document["configuration_data_dependencies"]
                for table_key in ("configuration_items", "structural_data_artifacts", "dependencies"):
                    self.assertIn(table_key, chapter_6)
                    self.assertIn("rows", chapter_6[table_key])
                for row in non_empty_rows(chapter_6, "dependencies"):
                    with self.subTest(path=path.name, dependency=row["dependency_id"]):
                        self.assertIn(row["dependency_type"], V2_DEPENDENCY_TYPES)

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


FIXED_RENDERED_HEADINGS = [
    "# 软件结构设计说明书",
    "## 1. 文档信息",
    "## 2. 系统概览",
    "## 3. 架构视图",
    "### 3.1 架构概述",
    "### 3.2 各模块介绍",
    "### 3.3 模块关系图",
    "### 3.4 补充架构图表",
    "## 4. 模块设计",
    "#### 4.1.1 模块定位与源码/产物范围",
    "#### 4.1.2 配置",
    "#### 4.1.3 依赖",
    "#### 4.1.4 数据对象",
    "#### 4.1.5 对外接口",
    "#### 4.1.6 实现机制说明",
    "#### 4.1.7 已知限制",
    "## 5. 运行时视图",
    "### 5.1 运行时概述",
    "### 5.2 运行单元说明",
    "### 5.3 运行时流程图",
    "### 5.4 运行时序图（推荐）",
    "### 5.5 补充运行时图表",
    "## 6. 配置、数据与依赖关系",
    "### 6.1 配置项说明",
    "### 6.2 关键结构数据与产物",
    "### 6.3 依赖项说明",
    "### 6.4 补充图表",
    "## 7. 跨模块协作关系",
    "### 7.1 协作关系概述",
    "### 7.2 跨模块协作说明",
    "### 7.3 跨模块协作关系图",
    "### 7.4 补充协作图表",
    "## 8. 关键流程",
    "### 8.1 关键流程概述",
    "### 8.2 关键流程清单",
    "## 9. 结构问题与改进建议",
]


def assert_markers_in_order(testcase, text, markers):
    positions = []
    for marker in markers:
        with testcase.subTest(marker=marker):
            positions.append(text.index(marker))
    testcase.assertEqual(sorted(positions), positions)


class Phase7Phase4ArtifactMixin:
    def write_phase4_review_artifact(self, dsl_path, document, run_dir):
        phase4 = load_script_module("scripts/v2_phase4.py", "phase7_v2_phase4_under_test")
        expected_ids = {
            diagram.diagram_id
            for diagram in phase4.collect_expected_diagrams(document)
            if diagram.should_render
        }
        artifact = {
            "artifact_schema_version": "1.0",
            "reviewer": "phase7-e2e-test",
            "source_dsl": str(dsl_path),
            "checked_diagram_ids": sorted(expected_ids),
            "accepted_diagram_ids": sorted(expected_ids),
            "revised_diagram_ids": [],
            "split_diagram_ids": [],
            "skipped_diagrams": [],
            "remaining_readability_risks": [],
        }
        artifact_path = run_dir / "mermaid-readability-review.json"
        artifact_path.write_text(
            json.dumps(artifact, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return artifact_path


class Phase7EndToEndWorkflowTests(Phase7Phase4ArtifactMixin, unittest.TestCase):
    def load_example(self, dsl_path):
        return json.loads(dsl_path.read_text(encoding="utf-8"))

    def assert_command_success(self, completed, label):
        self.assertEqual(
            0,
            completed.returncode,
            f"{label} failed\nSTDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}",
        )

    def render_static_workflow(self, dsl_path, run_dir_name):
        document = self.load_example(dsl_path)
        tmpdir = make_run_dir(run_dir_name)

        self.assert_command_success(
            run_command("scripts/validate_dsl.py", dsl_path),
            f"validate_dsl.py {dsl_path.name}",
        )
        self.assert_command_success(
            run_command("scripts/validate_mermaid.py", "--from-dsl", dsl_path, "--static"),
            f"validate_mermaid.py --from-dsl {dsl_path.name} --static",
        )
        self.assert_command_success(
            run_command("scripts/render_markdown.py", dsl_path, "--output-dir", tmpdir, "--overwrite"),
            f"render_markdown.py {dsl_path.name}",
        )

        output_path = tmpdir / document["document"]["output_file"]
        self.assertEqual([output_path], sorted(tmpdir.glob("*.md")))
        self.assertTrue(output_path.is_file())

        self.assert_command_success(
            run_command("scripts/validate_mermaid.py", "--from-markdown", output_path, "--static"),
            f"validate_mermaid.py --from-markdown {output_path.name} --static",
        )
        markdown = output_path.read_text(encoding="utf-8")
        phase4 = load_script_module("scripts/v2_phase4.py", "phase7_v2_phase4_completeness_under_test")
        self.assertEqual([], phase4.rendered_diagram_completeness_errors(document, markdown))
        self.assertIn("<!-- diagram-id:", markdown)
        return document, output_path, markdown

    def test_static_workflow_validates_renders_and_revalidates_examples(self):
        for dsl_path in EXAMPLE_PATHS:
            with self.subTest(path=dsl_path.name):
                document, _output_path, markdown = self.render_static_workflow(
                    dsl_path,
                    f"{dsl_path.stem}-static-workflow",
                )
                self.assertEqual("0.2.0", document["dsl_version"])
                lowered = markdown.casefold()
                self.assertNotIn("```dot", lowered)
                self.assertNotIn("```graphviz", lowered)
                self.assertIsNone(re.search(r"(?im)^\s*digraph\b", markdown))
                self.assertIsNone(re.search(r"(?im)^\s*rankdir\s*=", markdown))

                assert_markers_in_order(self, markdown, FIXED_RENDERED_HEADINGS)
                first_flow_name = document["key_flows"]["flows"][0]["name"]
                expected_once = [
                    "### 3.4 补充架构图表",
                    "### 5.4 运行时序图（推荐）",
                    "### 6.4 补充图表",
                    "### 7.4 补充协作图表",
                    "### 8.2 关键流程清单",
                    f"### 8.3 {first_flow_name}",
                ]
                for marker in expected_once:
                    with self.subTest(path=dsl_path.name, marker=marker):
                        self.assertEqual(1, markdown.count(marker))
                assert_markers_in_order(
                    self,
                    markdown,
                    [
                        f"### 8.3 {first_flow_name}",
                        "#### 8.3.1 流程概述",
                        "#### 8.3.2 步骤说明",
                        "#### 8.3.3 异常/分支说明",
                        "#### 8.3.4 流程图",
                    ],
                )


class Phase7StrictMermaidAndFallbackTests(Phase7Phase4ArtifactMixin, unittest.TestCase):
    def test_examples_orchestrate_strict_mermaid_cli_invocations_when_cli_is_available(self):
        module = load_script_module("scripts/verify_v2_mermaid_gates.py", "phase7_verify_v2_mermaid_gates_under_test")
        completed = subprocess.CompletedProcess(
            [PYTHON, str(ROOT / "scripts/validate_mermaid.py")],
            0,
            stdout="Mermaid validation succeeded\n",
            stderr="",
        )
        for dsl_path in EXAMPLE_PATHS:
            with self.subTest(path=dsl_path.name):
                document = json.loads(dsl_path.read_text(encoding="utf-8"))
                run_dir = make_run_dir(f"{dsl_path.stem}-strict-orchestration")
                render = run_command(
                    "scripts/render_markdown.py",
                    dsl_path,
                    "--output-dir",
                    run_dir,
                    "--overwrite",
                )
                self.assertEqual(0, render.returncode, render.stderr)
                output_path = run_dir / document["document"]["output_file"]
                artifact_path = self.write_phase4_review_artifact(dsl_path, document, run_dir)
                work_dir = run_dir / "mermaid"
                with mock.patch.object(module.subprocess, "run", return_value=completed) as run_validator:
                    code, stdout, stderr = call_main(
                        module,
                        [
                            str(dsl_path),
                            "--mermaid-review-artifact",
                            str(artifact_path),
                            "--pre-render",
                            "--work-dir",
                            str(work_dir),
                        ],
                    )
                    self.assertEqual(0, code, f"STDOUT:\n{stdout}\nSTDERR:\n{stderr}")
                    self.assertIn("Mermaid validation succeeded", stdout)
                    self.assertEqual("", stderr)
                    run_validator.assert_called_once_with(
                        [
                            sys.executable,
                            str(ROOT / "scripts/validate_mermaid.py"),
                            "--from-dsl",
                            str(dsl_path),
                            "--strict",
                            "--work-dir",
                            str(work_dir / "pre-render"),
                        ],
                        cwd=ROOT,
                        text=True,
                        capture_output=True,
                        check=False,
                    )

                    run_validator.reset_mock()
                    code, stdout, stderr = call_main(
                        module,
                        [
                            str(dsl_path),
                            "--mermaid-review-artifact",
                            str(artifact_path),
                            "--rendered-markdown",
                            str(output_path),
                            "--post-render",
                            "--work-dir",
                            str(work_dir),
                        ],
                    )
                    self.assertEqual(0, code, f"STDOUT:\n{stdout}\nSTDERR:\n{stderr}")
                    self.assertIn("Mermaid validation succeeded", stdout)
                    self.assertEqual("", stderr)
                    run_validator.assert_called_once_with(
                        [
                            sys.executable,
                            str(ROOT / "scripts/validate_mermaid.py"),
                            "--from-markdown",
                            str(output_path),
                            "--strict",
                            "--work-dir",
                            str(work_dir / "post-render"),
                        ],
                        cwd=ROOT,
                        text=True,
                        capture_output=True,
                        check=False,
                    )

    def test_examples_pass_strict_mermaid_workflow_with_real_cli_when_available(self):
        if shutil.which("mmdc") is None:
            self.skipTest("mmdc unavailable")
        if shutil.which("node") is None:
            self.skipTest("node unavailable")

        for dsl_path in EXAMPLE_PATHS:
            with self.subTest(path=dsl_path.name):
                run_dir = make_run_dir(f"{dsl_path.stem}-strict-real-cli")
                document = json.loads(dsl_path.read_text(encoding="utf-8"))
                artifact_path = self.write_phase4_review_artifact(dsl_path, document, run_dir)
                work_dir = run_dir / "mermaid"
                pre_render = run_command(
                    "scripts/verify_v2_mermaid_gates.py",
                    dsl_path,
                    "--mermaid-review-artifact",
                    artifact_path,
                    "--pre-render",
                    "--work-dir",
                    work_dir,
                    env=preserved_process_env(run_dir),
                )
                self.assertEqual(
                    0,
                    pre_render.returncode,
                    f"STDOUT:\n{pre_render.stdout}\nSTDERR:\n{pre_render.stderr}",
                )
                render = run_command(
                    "scripts/render_markdown.py",
                    dsl_path,
                    "--output-dir",
                    run_dir,
                    "--overwrite",
                    env=preserved_process_env(run_dir),
                )
                self.assertEqual(0, render.returncode, render.stderr)
                output_path = run_dir / document["document"]["output_file"]
                post_render = run_command(
                    "scripts/verify_v2_mermaid_gates.py",
                    dsl_path,
                    "--mermaid-review-artifact",
                    artifact_path,
                    "--rendered-markdown",
                    output_path,
                    "--post-render",
                    "--work-dir",
                    work_dir,
                    env=preserved_process_env(run_dir),
                )
                self.assertEqual(
                    0,
                    post_render.returncode,
                    f"STDOUT:\n{post_render.stdout}\nSTDERR:\n{post_render.stderr}",
                )

    def test_check_env_and_reference_docs_cover_phase4_static_boundary(self):
        module = load_script_module("scripts/validate_mermaid.py", "phase7_validate_mermaid_env_under_test")
        with mock.patch.object(
            module.shutil,
            "which",
            side_effect=lambda name: "/usr/bin/node" if name == "node" else None,
        ):
            code, stdout, stderr = call_main(module, ["--check-env"])
        self.assertEqual(1, code)
        self.assertIn("node: found at /usr/bin/node", stdout)
        self.assertIn("mmdc: missing", stdout)
        self.assertEqual("", stderr)

        combined_docs = "\n".join(
            (ROOT / relative_path).read_text(encoding="utf-8")
            for relative_path in [
                "SKILL.md",
                "references/mermaid-rules.md",
                "references/review-checklist.md",
            ]
        ).casefold()
        required_phrases = [
            "Static-only Mermaid validation is not final acceptance for V2 Phase 4",
            "Mermaid readability artifact",
            "rendered diagram completeness",
            "strict rendered Markdown validation",
        ]
        for phrase in required_phrases:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase.casefold(), combined_docs)
