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

    def test_renderer_uses_tables_for_structured_repeated_content(self):
        tmpdir, markdown = self.render_fixture()
        with tmpdir:
            expected_tables = [
                "| 能力 | 描述 | 入口 | 备注 |",
                "| 持久化读写 | 封装底层存储访问。 | src/storage.c::storage_init | 入口由应用调用。 |",
                "| 顺序 | 主题 | 为什么读 | 推荐文件 | 目标收获 |",
                "| 1 | 公共接口 | 先理解调用面。 | include/storage.h（声明主要接口。） | 知道应用如何进入库。 |",
                "| 分组 | 职责 | 路径 | 阅读时机 | 备注 |",
                "| 公共头文件 | 暴露应用集成接口。 | include | 开始集成前。 | 保持小而稳定。 |",
                "| 层 | 角色 | 职责 | 路径 | 备注 |",
                "| 接口层 | 接收应用调用。 | 稳定入口 | include | 不拥有存储细节。 |",
                "| 层 | 模块 | 目的 | 源码路径 | 阅读时机 |",
                "| 接口层 | 存储接口 | 提供应用入口。 | include/storage.h | 理解集成入口时。 |",
                "#### 存储接口",
                "| 负责 | 接口契约 |",
                "| 消费 | 应用请求 |",
                "| 产出 | 核心调用 |",
                "| 不负责 | 平台驱动 |",
                "| 备注 | 只描述职责，不列函数原型。 |",
                "##### 协作",
                "| 协作模块 | 关系 |",
                "| 存储核心 | 调用核心实现。 |",
                "| 序号 | 步骤 | 影响 | 模块 | 参考 |",
                "| 1 | 应用调用公共入口。 | 进入库边界。 | 存储接口 | include/storage.h::storage_init |",
                "| 序号 | 步骤 | 数据或状态 | 参考 | 备注 |",
                "| 1 | 检查写入请求。 | 写入缓冲区。 | src/storage.c::storage_write | 这里只讲机制，不列 API 表。 |",
                "| 名称 | 类型 | 说明 | 参考 |",
                "| 写入缓冲区 | runtime_value | 调用方传入的数据。 | src/storage.c::storage_write |",
                "| 名称 | 类型 | 用途 | 位置 | 要求 | 备注 |",
                "| 存储大小 | macro | 定义可用存储空间。 | 配置头文件（include/storage_cfg.h） | 启用库时。 | 示例值不代表生产配置。 |",
                "| 风险 | 影响 | 缓解 | 相关模块 | 相关机制 | 可信度 |",
                "| 未执行目标硬件验证。 | 时序问题可能遗漏。 | 在目标板运行集成测试。 | 存储核心 | 持久化写入机制 | medium |",
            ]
            for table_fragment in expected_tables:
                self.assertIn(table_fragment, markdown)
            self.assertNotIn("| 模块 | 目的 | 源码路径 | 负责 | 消费 | 产出 | 不负责 | 协作 | 阅读时机 | 备注 |", markdown)

    def test_renders_directory_relationship_diagram_when_present(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            package = load_manifest_package(write_valid_package(tmpdir))
            package.chapters["directory_map"]["directory_relationships"]["diagram"] = {
                "id": "directory_relationships",
                "title": "目录关系图",
                "diagram_type": "flowchart",
                "description": "展示公共头文件到核心实现的目录关系。",
                "source": "flowchart TD\n  headers[公共头文件] --> core[核心实现]",
            }
            markdown = render_markdown(package)
        self.assertIn("### 目录关系图", markdown)
        self.assertIn("```mermaid\nflowchart TD\n  headers[公共头文件] --> core[核心实现]\n```", markdown)

    def test_renders_layer_diagram_when_present(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            package = load_manifest_package(write_valid_package(tmpdir))
            package.chapters["module_layers"]["layer_diagram"] = {
                "id": "layer_view",
                "title": "分层关系图",
                "diagram_type": "flowchart",
                "description": "展示接口层与核心层的调用关系。",
                "source": "flowchart TD\n  api[接口层] --> core[核心层]",
            }
            markdown = render_markdown(package)
        self.assertIn("### 分层关系图", markdown)
        self.assertIn("```mermaid\nflowchart TD\n  api[接口层] --> core[核心层]\n```", markdown)

    def test_renders_mainline_detail_diagram_when_present(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            package = load_manifest_package(write_valid_package(tmpdir))
            package.chapters["repository_mainline"]["mainlines"][0]["detail_diagram"] = {
                "id": "init_detail",
                "title": "初始化细节图",
                "diagram_type": "sequenceDiagram",
                "description": "展示应用、存储接口与存储核心之间的初始化交互。",
                "source": "sequenceDiagram\n  participant App as 应用\n  participant Api as 存储接口\n  participant Core as 存储核心\n  App->>Api: 初始化\n  Api->>Core: 准备状态",
            }
            markdown = render_markdown(package)
        self.assertIn("#### 初始化细节图", markdown)
        self.assertIn("```mermaid\nsequenceDiagram\n  participant App as 应用", markdown)
        self.assertIn("Api->>Core: 准备状态\n```", markdown)

    def test_renders_mechanism_diagram_when_present(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            package = load_manifest_package(write_valid_package(tmpdir))
            package.mechanisms[0].data["diagram"] = {
                "id": "persistence_flow",
                "title": "持久化写入流程图",
                "diagram_type": "flowchart",
                "description": "展示写入请求如何进入平台适配。",
                "source": "flowchart TD\n  core[存储核心] --> port[平台适配]",
            }
            markdown = render_markdown(package)
        self.assertIn("#### 持久化写入流程图", markdown)
        self.assertIn("```mermaid\nflowchart TD\n  core[存储核心] --> port[平台适配]\n```", markdown)

    def test_optional_source_ref_absence_does_not_render_empty_parentheses(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            package = load_manifest_package(write_valid_package(tmpdir))
            package.chapters["repository_mainline"]["mainlines"][0]["entry"].pop("source_ref")
            package.chapters["integration_boundaries"]["required_configuration"][0]["location"].pop("source_ref")
            package.chapters["integration_boundaries"]["required_adaptations"][0]["location"].pop("source_ref")
            package.chapters["integration_boundaries"]["integration_paths"][0]["recommended_entry"].pop("source_ref")
            markdown = render_markdown(package)
        self.assertNotIn("（）", markdown)
        self.assertIn("| 入口 | storage_init | api | 应用初始化入口。 | - |", markdown)
        self.assertIn("| 存储大小 | macro | 定义可用存储空间。 | 配置头文件 | 启用库时。 | 示例值不代表生产配置。 |", markdown)
        self.assertIn("| 底层写入 | port_function | 把数据写入硬件。 | 存储核心。 | 平台适配文件 | 写入请求无法完成。 |", markdown)
        self.assertIn("| 应用集成 | 应用初始化存储库。 | 调用公共初始化接口。 |", markdown)

    def test_empty_source_refs_do_not_render_empty_reference_punctuation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            package = load_manifest_package(write_valid_package(tmpdir))
            package.mechanisms[0].data["flow"][0]["source_refs"] = []
            package.mechanisms[0].data["key_states_or_data"][0]["source_refs"] = []
            markdown = render_markdown(package)
        self.assertNotIn("参考：。", markdown)
        self.assertNotIn("，）", markdown)
        self.assertIn("| 1 | 检查写入请求。 | 写入缓冲区。 | - | 这里只讲机制，不列 API 表。 |", markdown)
        self.assertIn("| 写入缓冲区 | runtime_value | 调用方传入的数据。 | - |", markdown)

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

    def test_render_cli_rejects_default_absolute_output_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            outside = root / "outside.md"
            manifest = write_valid_package(str(root / "dsl"), output_file=str(outside))
            stderr = io.StringIO()
            with mock.patch("scripts.render_markdown.mermaid_validation_result") as mermaid:
                mermaid.return_value.ok = True
                mermaid.return_value.errors = []
                mermaid.return_value.warnings = []
                with contextlib.redirect_stderr(stderr):
                    code = render_cli.main([str(manifest)])
            self.assertEqual(2, code)
            self.assertFalse(outside.exists())
            self.assertIn("document.output_file must stay within the package root", stderr.getvalue())

    def test_render_cli_rejects_default_dotdot_output_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            manifest = write_valid_package(str(root / "dsl" / "inner"), output_file="../../out.md")
            outside = (manifest.parent / "../../out.md").resolve()
            stderr = io.StringIO()
            with mock.patch("scripts.render_markdown.mermaid_validation_result") as mermaid:
                mermaid.return_value.ok = True
                mermaid.return_value.errors = []
                mermaid.return_value.warnings = []
                with contextlib.redirect_stderr(stderr):
                    code = render_cli.main([str(manifest)])
            self.assertEqual(2, code)
            self.assertFalse(outside.exists())
            self.assertIn("document.output_file must stay within the package root", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
