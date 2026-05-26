import copy
import json
from pathlib import Path


FIXED_MANIFEST = {
    "document": "chapters/00-document.json",
    "overview": "chapters/01-overview.json",
    "quick_start": "chapters/02-quick-start.json",
    "architecture_overview": "chapters/03-architecture-overview.json",
    "main_flows": "chapters/04-main-flows.json",
    "module_details": "chapters/05-module-details.json",
}


DOCUMENT = {
    "document": {
        "repository_name": "示例仓库",
        "output_file": "Example_STRUCTURE_DESIGN.md",
    }
}


OVERVIEW = {
    "overview": {
        "repository_intro": {
            "blocks": [
                {
                    "type": "paragraph",
                    "text": "这是一个用于验证结构文档渲染流程的示例仓库。",
                }
            ]
        },
        "components": [
            {
                "component": "公共 API",
                "role": "对外提供仓库能力入口",
                "location": "src/api",
            }
        ],
    }
}


QUICK_START = {
    "quick_start": {
        "first_run": [
            {
                "title": "初始化仓库能力",
                "commands": ["python -m example.init"],
                "notes": "准备示例数据和本地运行环境。",
            }
        ]
    }
}


ARCHITECTURE_OVERVIEW = {
    "architecture_overview": {
        "layers": [
            {
                "layer": "接口层",
                "responsibility": "接收调用并转换为应用命令。",
                "modules": "src/api",
            }
        ],
        "modules": [
            {
                "module": "reader",
                "responsibility": "读取输入并构建领域对象。",
                "location": "src/reader.py",
            }
        ],
    }
}


MAIN_FLOWS = {
    "main_flows": {
        "flows": [
            {
                "name": "生成结构说明",
                "summary": "读取仓库信息并输出结构文档。",
                "steps": ["加载配置", "分析目录", "写入 Markdown"],
            }
        ]
    }
}


MODULE_DETAILS = {
    "module_details": {
        "intro_blocks": [],
        "modules": [
            {
                "name": "reader",
                "location": "src/reader.py",
                "mechanisms": [
                    {
                        "name": "路径扫描",
                        "summary": "遍历项目文件并收集结构节点。",
                    }
                ],
            }
        ],
    }
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
    write_json(root / FIXED_MANIFEST["main_flows"], MAIN_FLOWS)
    write_json(root / FIXED_MANIFEST["module_details"], MODULE_DETAILS)
    return root / "structure.manifest.json"
