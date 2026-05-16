import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tests.helpers_v030 import write_valid_package

from scripts import render_markdown as render_cli
from scripts.v030_package import load_manifest_package
from scripts.v030_renderer import render_markdown


EXPECTED_HEADINGS = [
    "# 示例仓库结构说明",
    "## 1. 文档说明",
    "## 2. 仓库概述与阅读路线",
    "## 3. 目录地图",
    "## 4. 系统分层与模块职责",
    "## 5. 仓库主线",
    "## 6. 关键机制深读",
    "## 7. 配置、移植与集成边界",
    "## 8. 风险、假设与验证缺口",
]


class V030RendererTests(unittest.TestCase):
    def render_fixture(self, *, key_mechanisms=True):
        tmpdir = tempfile.TemporaryDirectory()
        manifest = write_valid_package(tmpdir.name, key_mechanisms=key_mechanisms)
        package = load_manifest_package(manifest)
        return tmpdir, render_markdown(package)

    def test_renders_fixed_eight_chapters_in_order(self):
        tmpdir, markdown = self.render_fixture()
        with tmpdir:
            positions = [markdown.index(heading) for heading in EXPECTED_HEADINGS]
        self.assertEqual(sorted(positions), positions)

    def test_visible_text_uses_human_names_instead_of_internal_ids(self):
        tmpdir, markdown = self.render_fixture()
        with tmpdir:
            for hidden in [
                "storage_api",
                "storage_core",
                "mainline_overview",
                "static_only",
                "caller_initializes_once",
            ]:
                self.assertNotIn(hidden, markdown)
            self.assertIn("存储接口", markdown)
            self.assertIn("存储核心", markdown)

    def test_empty_key_mechanisms_renders_fixed_empty_sentence(self):
        tmpdir, markdown = self.render_fixture(key_mechanisms=False)
        with tmpdir:
            self.assertIn("## 6. 关键机制深读", markdown)
            self.assertIn("本次分析未选择可深读的关键机制。", markdown)

    def test_renderer_includes_required_fixture_content_across_chapters(self):
        tmpdir, markdown = self.render_fixture()
        with tmpdir:
            expected = [
                "基于静态阅读。",
                "这是一个 C 库示例。",
                "公共头文件",
                "系统分为接口层和核心层。",
                "初始化主线",
                "```mermaid",
                "持久化写入机制",
                "底层写入",
                "未执行目标硬件验证。",
            ]
            for text in expected:
                self.assertIn(text, markdown)

    def test_render_cli_writes_default_output_file_and_prints_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest = write_valid_package(tmpdir)
            expected_output = Path(tmpdir) / "Example_STRUCTURE_DESIGN.md"
            stdout = io.StringIO()
            with mock.patch("scripts.render_markdown.mermaid_validation_result") as mermaid:
                mermaid.return_value.ok = True
                mermaid.return_value.errors = []
                mermaid.return_value.warnings = []
                with contextlib.redirect_stdout(stdout):
                    code = render_cli.main([str(manifest)])
            self.assertEqual(0, code)
            self.assertTrue(expected_output.exists())
            self.assertIn(f"Document written: {expected_output}", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
