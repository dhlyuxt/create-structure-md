import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_doc(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


class V030DocumentationTests(unittest.TestCase):
    def assertContainsAll(self, relative_path, expected_fragments):
        content = read_doc(relative_path)
        for fragment in expected_fragments:
            with self.subTest(path=relative_path, fragment=fragment):
                self.assertIn(fragment, content)

    def test_skill_documents_v030_manifest_workflow(self):
        self.assertContainsAll(
            "SKILL.md",
            [
                "0.3.0",
                "structure.manifest.json",
                "repo-understand",
                "固定八章",
                "不要把分析过程写入 DSL",
                "不兼容 0.2.0",
            ],
        )

    def test_dsl_spec_documents_manifest_and_shared_contracts(self):
        self.assertContainsAll(
            "references/dsl-spec.md",
            [
                "main JSON is a chapter directory only",
                "key_mechanisms",
                "DocumentInfo.language",
                "SourceRef",
                "inferred from each mechanism file stem",
                "^[a-z0-9][a-z0-9_-]*$",
                "unique package-wide",
                "MechanismChapter",
                "must not contain a `chapter` header",
            ],
        )

    def test_repo_understand_workflow_documents_mechanism_boundary(self):
        self.assertContainsAll(
            "references/repo-understand-workflow.md",
            [
                "repo-analysis-tools",
                "Chapter 6",
                "subagent",
                "mechanism JSON stores accepted content",
            ],
        )

    def test_review_checklist_documents_human_first_checks(self):
        self.assertContainsAll(
            "references/review-checklist.md",
            [
                "manifest contains only chapter paths",
                "visible Mermaid labels",
                "Chapter 4 is not an API reference",
                "Chapter 8 records validation gaps",
            ],
        )

    def test_contract_docs_do_not_name_example_repository(self):
        for relative_path in [
            "SKILL.md",
            "references/dsl-spec.md",
            "references/document-structure.md",
            "references/repo-understand-workflow.md",
            "references/review-checklist.md",
        ]:
            with self.subTest(path=relative_path):
                self.assertNotIn("EasyFlash", read_doc(relative_path))


if __name__ == "__main__":
    unittest.main()
