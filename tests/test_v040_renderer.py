import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.v040_package import load_manifest_package
from scripts.v040_renderer import render_markdown
from tests.helpers_v040 import write_json, write_valid_package


EXPECTED_HEADINGS = [
    "# 示例仓库结构说明",
    "## 入门",
    "### 概述",
    "#### 当前仓库介绍",
    "#### 解决的问题",
    "#### 主要功能",
    "#### 核心组件",
    "### 快速开始",
    "#### 使用场景",
    "#### 准备工作",
    "#### 第一次运行/接入",
    "#### 最小示例",
    "#### 预期结果",
    "## 深入解析",
    "### 架构概述",
    "#### 架构总览",
    "#### 软件分层",
    "#### 模块划分",
    "#### 目录角色",
    "### 主线流程",
    "### 模块详解",
]


class V040RendererTests(unittest.TestCase):
    def render_package(self, mutator=None, *, include_mermaid=False):
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = write_valid_package(tmpdir, include_mermaid=include_mermaid)
            if mutator:
                mutator(Path(tmpdir))
            package = load_manifest_package(manifest_path)
            return render_markdown(package)

    def test_renders_expected_headings_in_order(self):
        markdown = self.render_package()
        positions = [markdown.index(heading) for heading in EXPECTED_HEADINGS]
        self.assertEqual(sorted(positions), positions)

    def test_core_component_table_renders_before_component_blocks(self):
        markdown = self.render_package()
        self.assertLess(
            markdown.index("| 组件 | 作用 | 位置 |"),
            markdown.index("公共 API 是最小调用入口。"),
        )

    def test_quick_start_first_run_steps_are_fifth_level_headings(self):
        markdown = self.render_package()
        self.assertIn("##### 1. 初始化仓库能力", markdown)
        self.assertIn("调用初始化入口。", markdown)

    def test_main_flow_has_fourth_level_heading_and_no_step_headings(self):
        markdown = self.render_package()
        main_flow_section = markdown[
            markdown.index("### 主线流程") : markdown.index("### 模块详解")
        ]
        self.assertIn("#### 初始化主线", main_flow_section)
        self.assertIn("入口：`example_init`", main_flow_section)
        self.assertNotIn("##### 1.", main_flow_section)

    def test_main_flow_without_entry_location_skips_empty_position_lines(self):
        def mutate(root):
            data = _read(root / "chapters/04-main-flows.json")
            del data["main_flows"]["flows"][0]["entry"]["location"]
            write_json(root / "chapters/04-main-flows.json", data)

        markdown = self.render_package(mutate)
        main_flow_section = markdown[
            markdown.index("### 主线流程") : markdown.index("### 模块详解")
        ]
        self.assertNotIn("位置：", main_flow_section)
        self.assertNotIn("None", main_flow_section)

    def test_module_mechanisms_render_inside_owning_module(self):
        markdown = self.render_package()
        self.assertLess(markdown.index("#### 存储模块"), markdown.index("##### 追加写入"))

    def test_module_intro_blocks_render_directly_under_module_details(self):
        def mutate(root):
            data = _read(root / "chapters/05-module-details.json")
            data["module_details"]["intro_blocks"] = [
                {"type": "text", "content": "模块详情总览。"}
            ]
            write_json(root / "chapters/05-module-details.json", data)

        markdown = self.render_package(mutate)
        module_details = markdown[markdown.index("### 模块详解") :]
        self.assertLess(module_details.index("模块详情总览。"), module_details.index("#### 存储模块"))
        self.assertNotIn("#### 模块导语", module_details)

    def test_mermaid_block_renders_as_fenced_mermaid_code(self):
        markdown = self.render_package(include_mermaid=True)
        self.assertIn("```mermaid\nflowchart LR\n  app[应用] --> api[公共 API]\n```", markdown)

    def test_code_block_without_title_renders_fence_without_none(self):
        markdown = self.render_package()
        self.assertIn("```bash\npython -m example.init\n```", markdown)
        self.assertNotIn("None", markdown)

    def test_extra_subsections_render_in_order_with_titles_and_hidden_keys(self):
        def mutate(root):
            overview = _read(root / "chapters/01-overview.json")
            overview["overview"]["extra_subsections"] = [
                {
                    "key": "overview_extra_alpha",
                    "title": "概述扩展一",
                    "blocks": [{"type": "text", "content": "概述扩展一内容。"}],
                },
                {
                    "key": "overview_extra_beta",
                    "title": "概述扩展二",
                    "blocks": [{"type": "text", "content": "概述扩展二内容。"}],
                },
            ]
            write_json(root / "chapters/01-overview.json", overview)

            quick_start = _read(root / "chapters/02-quick-start.json")
            quick_start["quick_start"]["extra_subsections"] = [
                {
                    "key": "quick_extra_alpha",
                    "title": "快速开始扩展",
                    "blocks": [{"type": "text", "content": "快速开始扩展内容。"}],
                }
            ]
            write_json(root / "chapters/02-quick-start.json", quick_start)

            architecture = _read(root / "chapters/03-architecture-overview.json")
            architecture["architecture_overview"]["extra_subsections"] = [
                {
                    "key": "architecture_extra_alpha",
                    "title": "架构扩展",
                    "blocks": [{"type": "text", "content": "架构扩展内容。"}],
                }
            ]
            write_json(root / "chapters/03-architecture-overview.json", architecture)

            main_flows = _read(root / "chapters/04-main-flows.json")
            main_flows["main_flows"]["extra_subsections"] = [
                {
                    "key": "main_flow_extra_alpha",
                    "title": "主线扩展",
                    "blocks": [{"type": "text", "content": "主线扩展内容。"}],
                }
            ]
            write_json(root / "chapters/04-main-flows.json", main_flows)

            module_details = _read(root / "chapters/05-module-details.json")
            module_details["module_details"]["extra_subsections"] = [
                {
                    "key": "module_details_extra_alpha",
                    "title": "模块总览扩展",
                    "blocks": [{"type": "text", "content": "模块总览扩展内容。"}],
                }
            ]
            module_details["module_details"]["modules"][0]["extra_subsections"] = [
                {
                    "key": "module_extra_alpha",
                    "title": "模块扩展一",
                    "blocks": [{"type": "text", "content": "模块扩展一内容。"}],
                }
            ]
            write_json(root / "chapters/05-module-details.json", module_details)

        markdown = self.render_package(mutate)
        self.assertLess(markdown.index("#### 概述扩展一"), markdown.index("#### 概述扩展二"))
        self.assertGreater(markdown.index("#### 概述扩展一"), markdown.index("公共 API 是最小调用入口。"))
        self.assertGreater(markdown.index("#### 快速开始扩展"), markdown.index("#### 预期结果"))
        self.assertGreater(markdown.index("#### 架构扩展"), markdown.index("#### 目录角色"))
        self.assertGreater(markdown.index("#### 主线扩展"), markdown.index("#### 初始化主线"))
        self.assertLess(markdown.index("#### 模块总览扩展"), markdown.index("#### 存储模块"))
        self.assertIn("##### 模块扩展一", markdown)
        self.assertGreater(markdown.index("##### 模块扩展一"), markdown.index("##### 追加写入"))
        for key in [
            "overview_extra_alpha",
            "overview_extra_beta",
            "quick_extra_alpha",
            "architecture_extra_alpha",
            "main_flow_extra_alpha",
            "module_details_extra_alpha",
            "module_extra_alpha",
        ]:
            self.assertNotIn(key, markdown)


def _read(path):
    return json.loads(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
