import copy
import json
from pathlib import Path


FIXED_MANIFEST = {
    "document": "chapters/00-document.json",
    "overview": "chapters/01-overview.json",
    "quick_start": "chapters/02-quick-start.json",
    "architecture_overview": "chapters/03-architecture-overview.json",
    "main_flow_overview": "chapters/04-main-flow-overview.json",
    "main_flow_details": ["chapters/04-main-flow-details/init-flow.json"],
    "module_overview": "chapters/05-module-overview.json",
    "module_details": ["chapters/05-module-details/storage.json"],
}


DOCUMENT = {
    "document": {
        "repository_name": "示例仓库",
        "output_file": "Example_STRUCTURE_DESIGN.md",
        "summary": "用于验证 0.4.0 reader guide package 的示例仓库。",
    }
}


OVERVIEW = {
    "overview": {
        "repository_intro": {
            "blocks": [
                {
                    "type": "text",
                    "content": "这是一个用于验证结构文档渲染流程的示例仓库。",
                }
            ]
        },
        "problems_solved": {
            "blocks": [
                {
                    "type": "text",
                    "content": "帮助读者用最小上下文理解仓库结构。",
                }
            ]
        },
        "main_capabilities": {
            "blocks": [
                {
                    "type": "unordered_list",
                    "items": [
                        "初始化示例仓库能力",
                        "展示固定章节 DSL 形状",
                    ],
                }
            ]
        },
        "core_components": {
            "component_table": {
                "rows": [
                    {
                        "component": "公共 API",
                        "role": "对外提供仓库能力入口",
                        "location": "src/api",
                    }
                ]
            },
            "blocks": [
                {
                    "type": "text",
                    "content": "公共 API 是最小调用入口。",
                }
            ],
        },
        "extra_subsections": [],
    }
}


QUICK_START = {
    "quick_start": {
        "usage_scenarios": {
            "blocks": [
                {
                    "type": "unordered_list",
                    "items": ["首次验证仓库能力", "检查 reader guide 输出"],
                }
            ]
        },
        "setup": {
            "blocks": [
                {
                    "type": "code",
                    "language": "bash",
                    "content": "python -m example.init",
                }
            ]
        },
        "first_run": {
            "steps": [
                {
                    "title": "初始化仓库能力",
                    "blocks": [
                        {
                            "type": "text",
                            "content": "调用初始化入口。",
                        }
                    ],
                }
            ],
            "blocks": [
                {
                    "type": "text",
                    "content": "初始化后即可执行最小验证。",
                }
            ],
        },
        "minimal_example": {
            "blocks": [
                {
                    "type": "code",
                    "language": "python",
                    "content": "example_init()",
                }
            ]
        },
        "expected_result": {
            "blocks": [
                {
                    "type": "text",
                    "content": "示例仓库能力完成初始化。",
                }
            ]
        },
        "extra_subsections": [],
    }
}


ARCHITECTURE_OVERVIEW = {
    "architecture_overview": {
        "architecture_summary": {
            "blocks": [
                {
                    "type": "text",
                    "content": "仓库以公共 API 为入口组织初始化能力。",
                }
            ]
        },
        "layers": {
            "layer_table": {
                "rows": [
                    {
                        "layer": "接口层",
                        "role": "接收调用并转换为应用命令。",
                        "location": "src/api",
                    }
                ]
            },
            "blocks": [
                {
                    "type": "text",
                    "content": "接口层隔离外部调用和内部模块。",
                }
            ],
        },
        "module_map": {
            "module_table": {
                "rows": [
                    {
                        "module": "reader",
                        "role": "读取输入并构建领域对象。",
                        "layer": "接口层",
                        "location": "src/reader.py",
                    }
                ]
            },
            "blocks": [],
        },
        "repository_layout": {
            "blocks": [
                {
                    "type": "table",
                    "columns": ["路径", "角色"],
                    "rows": [["src/api", "公共 API 入口"]],
                }
            ]
        },
        "extra_subsections": [],
    }
}


MAIN_FLOW_OVERVIEW = {
    "main_flow_overview": {
        "intro": "本章按读者最常遇到的行为路径说明仓库如何工作。",
        "flow_table": {
            "rows": [
                {
                    "flow": "初始化主线",
                    "purpose": "准备示例仓库能力并写入初始状态。",
                    "entry": "example_init",
                    "location": "src/api/init.py",
                    "anchor": "初始化主线",
                }
            ]
        },
    }
}


MAIN_FLOW_DETAIL = {
    "title": "初始化主线",
    "purpose": "准备示例仓库能力并写入初始状态。",
    "reader_goal": "读者想知道调用初始化入口后仓库内部发生什么。",
    "entry": {"name": "example_init", "location": "src/api/init.py"},
    "blocks": [{"type": "text", "content": "初始化入口协调读取配置和追加写入。"}],
    "extra_subsections": [],
}


MODULE_OVERVIEW = {
    "module_overview": {
        "intro": "本章按责任单元说明仓库的关键模块。",
        "module_table": {
            "rows": [
                {
                    "module": "存储模块",
                    "purpose": "保存初始化流程产生的示例状态。",
                    "location": "src/storage.py",
                    "anchor": "存储模块",
                }
            ]
        },
    }
}


MODULE_DETAIL = {
    "name": "存储模块",
    "location": "src/storage.py",
    "purpose": "保存初始化流程产生的示例状态。",
    "responsibilities": ["保存初始化结果", "提供追加写入机制"],
    "blocks": [{"type": "text", "content": "存储模块负责把初始化结果持久化到本地状态。"}],
    "mechanisms": [
        {
            "title": "追加写入",
            "blocks": [{"type": "text", "content": "追加写入保留已有记录并写入新的初始化结果。"}],
        }
    ],
    "extra_subsections": [],
}


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_valid_package(root, *, include_mermaid=False):
    root = Path(root)
    write_json(root / "structure.manifest.json", FIXED_MANIFEST)

    overview = copy.deepcopy(OVERVIEW)
    if include_mermaid:
        overview["overview"]["repository_intro"]["blocks"].append(
            {
                "type": "mermaid",
                "title": "调用关系",
                "diagram_type": "flowchart",
                "source": "flowchart LR\n  app[应用] --> api[公共 API]",
            }
        )
    write_json(root / FIXED_MANIFEST["document"], DOCUMENT)
    write_json(root / FIXED_MANIFEST["overview"], overview)
    write_json(root / FIXED_MANIFEST["quick_start"], QUICK_START)
    write_json(root / FIXED_MANIFEST["architecture_overview"], ARCHITECTURE_OVERVIEW)
    write_json(root / FIXED_MANIFEST["main_flow_overview"], MAIN_FLOW_OVERVIEW)
    for relative_path in FIXED_MANIFEST["main_flow_details"]:
        write_json(root / relative_path, copy.deepcopy(MAIN_FLOW_DETAIL))
    write_json(root / FIXED_MANIFEST["module_overview"], MODULE_OVERVIEW)
    for relative_path in FIXED_MANIFEST["module_details"]:
        write_json(root / relative_path, copy.deepcopy(MODULE_DETAIL))
    return root / "structure.manifest.json"
