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
    "# 示例仓库 结构说明",
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

    def test_main_flow_detail_file_renders_as_fourth_level_heading(self):
        markdown = self.render_package()
        main_flow_section = markdown[
            markdown.index("### 主线流程") : markdown.index("### 模块详解")
        ]
        self.assertIn("#### 初始化主线", main_flow_section)

    def test_main_flow_without_entry_location_skips_empty_position_lines(self):
        def mutate(root):
            detail = _read(root / "chapters/04-main-flow-details/init-flow.json")
            detail["entry"]["location"] = ""
            write_json(root / "chapters/04-main-flow-details/init-flow.json", detail)

            overview = _read(root / "chapters/04-main-flow-overview.json")
            overview["main_flow_overview"]["flow_table"]["rows"][0]["location"] = ""
            write_json(root / "chapters/04-main-flow-overview.json", overview)

        markdown = self.render_package(mutate)
        main_flow_section = markdown[
            markdown.index("### 主线流程") : markdown.index("### 模块详解")
        ]
        self.assertNotIn("位置：", main_flow_section)
        self.assertNotIn("None", main_flow_section)

    def test_main_flow_overview_table_links_to_detail_heading(self):
        markdown = self.render_package()
        self.assertIn("| 主线 | 目的 | 入口 | 位置 |", markdown)
        self.assertIn(
            "| [初始化主线](#初始化主线) | 准备示例仓库能力并写入初始状态。 | `example_init` | src/api/init.py |",
            markdown,
        )
        self.assertLess(markdown.index("| 主线 | 目的 | 入口 | 位置 |"), markdown.index("#### 初始化主线"))

    def test_module_overview_table_links_to_detail_heading(self):
        markdown = self.render_package()
        self.assertIn("| 模块 | 职责 | 位置 |", markdown)
        self.assertIn(
            "| [存储模块](#存储模块) | 保存初始化流程产生的示例状态。 | src/storage.py |",
            markdown,
        )
        self.assertLess(markdown.index("| 模块 | 职责 | 位置 |"), markdown.index("#### 存储模块"))

    def test_detail_files_render_in_manifest_order(self):
        def mutate(root):
            manifest = _read(root / "structure.manifest.json")
            manifest["main_flow_details"].append("chapters/04-main-flow-details/render-flow.json")
            manifest["module_details"].append("chapters/05-module-details/render.json")
            write_json(root / "structure.manifest.json", manifest)
            write_json(
                root / "chapters/04-main-flow-details/render-flow.json",
                {
                    "title": "渲染主线",
                    "purpose": "渲染结构文档。",
                    "reader_goal": "读者想知道验证通过后如何生成 Markdown。",
                    "entry": {"name": "render_markdown", "location": "scripts/render_markdown.py"},
                    "blocks": [{"type": "text", "content": "渲染入口读取已验证包并输出 Markdown。"}],
                    "extra_subsections": [],
                },
            )
            flow_overview = _read(root / "chapters/04-main-flow-overview.json")
            flow_overview["main_flow_overview"]["flow_table"]["rows"].append(
                {
                    "flow": "渲染主线",
                    "purpose": "渲染结构文档。",
                    "entry": "render_markdown",
                    "location": "scripts/render_markdown.py",
                    "anchor": "渲染主线",
                }
            )
            write_json(root / "chapters/04-main-flow-overview.json", flow_overview)
            write_json(
                root / "chapters/05-module-details/render.json",
                {
                    "name": "渲染模块",
                    "location": "scripts/v040_renderer.py",
                    "purpose": "把结构包转换为 Markdown。",
                    "responsibilities": ["渲染固定章节", "渲染详情文件"],
                    "blocks": [{"type": "text", "content": "渲染模块按 manifest 顺序输出内容。"}],
                    "mechanisms": [],
                    "extra_subsections": [],
                },
            )
            module_overview = _read(root / "chapters/05-module-overview.json")
            module_overview["module_overview"]["module_table"]["rows"].append(
                {
                    "module": "渲染模块",
                    "purpose": "把结构包转换为 Markdown。",
                    "location": "scripts/v040_renderer.py",
                    "anchor": "渲染模块",
                }
            )
            write_json(root / "chapters/05-module-overview.json", module_overview)

        markdown = self.render_package(mutate)

        self.assertLess(markdown.index("#### 初始化主线"), markdown.index("#### 渲染主线"))
        self.assertLess(markdown.index("#### 存储模块"), markdown.index("#### 渲染模块"))

    def test_module_mechanisms_render_inside_owning_module(self):
        markdown = self.render_package()
        self.assertLess(markdown.index("#### 存储模块"), markdown.index("##### 追加写入"))

    def test_mermaid_block_renders_as_fenced_mermaid_code(self):
        markdown = self.render_package(include_mermaid=True)
        self.assertIn("```mermaid\nflowchart LR\n  app[应用] --> api[公共 API]\n```", markdown)

    def test_code_and_mermaid_block_titles_render_as_nested_headings(self):
        def mutate(root):
            quick_start = _read(root / "chapters/02-quick-start.json")
            quick_start["quick_start"]["setup"]["blocks"] = [
                {
                    "type": "code",
                    "title": "安装命令",
                    "language": "bash",
                    "content": "python -m example.init",
                }
            ]
            write_json(root / "chapters/02-quick-start.json", quick_start)

            overview = _read(root / "chapters/01-overview.json")
            overview["overview"]["repository_intro"]["blocks"].append(
                {
                    "type": "mermaid",
                    "title": "组件关系",
                    "diagram_type": "flowchart",
                    "source": "flowchart LR\n  app[应用] --> api[公共 API]",
                }
            )
            write_json(root / "chapters/01-overview.json", overview)

        markdown = self.render_package(mutate)

        self.assertIn(
            "##### 安装命令\n\n```bash\npython -m example.init\n```",
            markdown,
        )
        self.assertIn(
            "##### 组件关系\n\n```mermaid\nflowchart LR\n  app[应用] --> api[公共 API]\n```",
            markdown,
        )

    def test_code_block_without_title_renders_fence_without_none(self):
        markdown = self.render_package()
        self.assertIn("```bash\npython -m example.init\n```", markdown)
        self.assertNotIn("None", markdown)

    def test_code_and_mermaid_fences_are_longer_than_content_backtick_runs(self):
        def mutate(root):
            quick_start = _read(root / "chapters/02-quick-start.json")
            quick_start["quick_start"]["setup"]["blocks"] = [
                {
                    "type": "code",
                    "language": "markdown",
                    "content": "before\n```python\nprint('inside')\n```\nafter",
                }
            ]
            write_json(root / "chapters/02-quick-start.json", quick_start)

            overview = _read(root / "chapters/01-overview.json")
            overview["overview"]["repository_intro"]["blocks"].append(
                {
                    "type": "mermaid",
                    "title": "包含围栏的图",
                    "diagram_type": "flowchart",
                    "source": "flowchart LR\n  A[```] --> B[done]",
                }
            )
            write_json(root / "chapters/01-overview.json", overview)

        markdown = self.render_package(mutate)
        self.assertIn("````markdown\nbefore\n```python\nprint('inside')\n```\nafter\n````", markdown)
        self.assertIn("````mermaid\nflowchart LR\n  A[```] --> B[done]\n````", markdown)

    def test_table_cells_escape_pipes_and_normalize_newlines(self):
        def mutate(root):
            architecture = _read(root / "chapters/03-architecture-overview.json")
            architecture["architecture_overview"]["repository_layout"]["blocks"] = [
                {
                    "type": "table",
                    "columns": ["路径|名称", "角色\n描述"],
                    "rows": [["src/api|v1", "公共\r\nAPI\n入口"]],
                }
            ]
            architecture["architecture_overview"]["layers"]["layer_table"]["rows"] = [
                {
                    "layer": "接口|层",
                    "role": "接收\r调用\n并转换为应用命令。",
                    "location": "src/api|public",
                }
            ]
            write_json(root / "chapters/03-architecture-overview.json", architecture)

        markdown = self.render_package(mutate)
        self.assertIn("| 路径\\|名称 | 角色 描述 |", markdown)
        self.assertIn("| src/api\\|v1 | 公共 API 入口 |", markdown)
        self.assertIn("| 接口\\|层 | 接收 调用 并转换为应用命令。 | src/api\\|public |", markdown)

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

            main_flow_detail = _read(root / "chapters/04-main-flow-details/init-flow.json")
            main_flow_detail["extra_subsections"] = [
                {
                    "key": "main_flow_extra_alpha",
                    "title": "主线扩展",
                    "blocks": [{"type": "text", "content": "主线扩展内容。"}],
                }
            ]
            write_json(root / "chapters/04-main-flow-details/init-flow.json", main_flow_detail)

            module_detail = _read(root / "chapters/05-module-details/storage.json")
            module_detail["extra_subsections"] = [
                {
                    "key": "module_extra_alpha",
                    "title": "模块扩展一",
                    "blocks": [{"type": "text", "content": "模块扩展一内容。"}],
                }
            ]
            write_json(root / "chapters/05-module-details/storage.json", module_detail)

        markdown = self.render_package(mutate)
        self.assertLess(markdown.index("#### 概述扩展一"), markdown.index("#### 概述扩展二"))
        self.assertGreater(markdown.index("#### 概述扩展一"), markdown.index("公共 API 是最小调用入口。"))
        self.assertGreater(markdown.index("#### 快速开始扩展"), markdown.index("#### 预期结果"))
        self.assertGreater(markdown.index("#### 架构扩展"), markdown.index("#### 目录角色"))
        self.assertGreater(markdown.index("#### 主线扩展"), markdown.index("#### 初始化主线"))
        self.assertIn("##### 模块扩展一", markdown)
        self.assertGreater(markdown.index("##### 模块扩展一"), markdown.index("##### 追加写入"))
        for key in [
            "overview_extra_alpha",
            "overview_extra_beta",
            "quick_extra_alpha",
            "architecture_extra_alpha",
            "main_flow_extra_alpha",
            "module_extra_alpha",
        ]:
            self.assertNotIn(key, markdown)


def _read(path):
    return json.loads(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
