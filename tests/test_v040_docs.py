import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


class V040DocsTests(unittest.TestCase):
    def test_skill_mentions_v040_authoring_references_and_terms(self):
        content = (ROOT / "SKILL.md").read_text(encoding="utf-8")

        for expected in [
            "references/dsl-authoring-guide.md",
            "references/mermaid-rules.md",
            "0.4.0",
            "repository_identity",
            "generated_module_object",
        ]:
            self.assertIn(expected, content)

    def test_authoring_guide_includes_required_headings(self):
        content = (ROOT / "references/dsl-authoring-guide.md").read_text(encoding="utf-8")

        for heading in [
            "## 总原则",
            "## 内容块使用规则",
            "## 概述怎么写",
            "## 快速开始怎么写",
            "## 架构概述怎么写",
            "## 主线流程怎么写",
            "## 模块详解怎么写",
            "## 不要写什么",
            "## 写完检查",
        ]:
            self.assertIn(heading, content)

    def test_dsl_spec_keeps_v040_reader_guide_sections_current(self):
        content = (ROOT / "references/dsl-spec.md").read_text(encoding="utf-8")

        self.assertIn("## Overview", content)
        self.assertIn("## Module Details", content)
        self.assertNotIn("key_mechanisms", content)
        self.assertNotIn("risks_validation", content)


if __name__ == "__main__":
    unittest.main()
