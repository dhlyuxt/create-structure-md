import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
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


if __name__ == "__main__":
    unittest.main()
