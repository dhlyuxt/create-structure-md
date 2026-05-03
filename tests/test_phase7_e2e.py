import unittest
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PHASE7_TMP_ROOT = ROOT / ".codex-tmp/create-structure-md-phase7-tests"


def make_run_dir(name):
    run_dir = PHASE7_TMP_ROOT / f"{name}-{uuid.uuid4().hex}"
    run_dir.mkdir(parents=True, exist_ok=False)
    return run_dir


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
