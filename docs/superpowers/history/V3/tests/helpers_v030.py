import json
from pathlib import Path


FIXED_MANIFEST = {
    "document": "chapters/01-document.json",
    "repository_overview": "chapters/02-repository-overview.json",
    "directory_map": "chapters/03-directory-map.json",
    "module_layers": "chapters/04-module-layers.json",
    "repository_mainline": "chapters/05-repository-mainline.json",
    "key_mechanisms": ["chapters/06-key-mechanisms/persistence.json"],
    "integration_boundaries": "chapters/07-integration-boundaries.json",
    "risks_validation": "chapters/08-risks-validation.json",
}


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def write_manifest_only_package(tmpdir: str, manifest=None) -> Path:
    root = Path(tmpdir)
    manifest_value = dict(FIXED_MANIFEST if manifest is None else manifest)
    write_json(root / "structure.manifest.json", manifest_value)
    for value in manifest_value.values():
        paths = value if isinstance(value, list) else [value]
        for child in paths:
            write_json(root / child, {})
    return root / "structure.manifest.json"


def minimal_document_chapter():
    return {
        "chapter": {"key": "document", "title": "文档说明"},
        "document": {
            "title": "示例仓库结构说明",
            "version": "0.1",
            "status": "draft",
            "language": "zh-CN",
            "generated_at": "2026-05-16T00:00:00+08:00",
            "output_file": "Example_STRUCTURE_DESIGN.md",
        },
        "repository": {
            "name": "example",
            "root_display_path": "example",
            "kind": "c_library",
            "primary_languages": ["C"],
        },
        "scope": {
            "included": [{"area": "library", "description": "核心库代码。"}],
            "excluded": [{"area": "hardware", "reason": "未连接目标硬件。"}],
        },
        "confidence": {
            "level": "medium",
            "summary": "基于静态阅读。",
            "validation_gaps": ["未执行目标板验证。"],
        },
    }


def minimal_repository_overview_chapter():
    return {
        "chapter": {"key": "repository_overview", "title": "仓库概述与阅读路线"},
        "overview": {
            "summary": "这是一个 C 库示例。",
            "problem_domain": "嵌入式持久化。",
            "repository_purpose": "提供可移植的存储能力。",
            "target_readers": ["首次阅读仓库的工程师"],
        },
        "core_capabilities": [
            {
                "name": "持久化读写",
                "description": "封装底层存储访问。",
                "entry_points": [{"path": "src/storage.c", "symbol": "storage_init"}],
                "notes": "入口由应用调用。",
            }
        ],
        "reading_route": {
            "summary": "先读公共头文件，再读核心实现。",
            "steps": [
                {
                    "order": 1,
                    "title": "公共接口",
                    "why_read_this": "先理解调用面。",
                    "recommended_files": [{"path": "include/storage.h", "reason": "声明主要接口。"}],
                    "expected_takeaway": "知道应用如何进入库。",
                }
            ],
        },
        "reader_orientation": {
            "read_first": ["include/storage.h"],
            "read_later": ["src/storage.c"],
            "can_skip_initially": ["docs/"],
        },
    }


def minimal_directory_map_chapter():
    return {
        "chapter": {"key": "directory_map", "title": "目录地图"},
        "summary": "目录按公共接口、核心实现、示例分组。",
        "directory_groups": [
            {
                "name": "公共头文件",
                "role": "public_headers",
                "paths": ["include"],
                "responsibility": "暴露应用集成接口。",
                "read_when": "开始集成前。",
                "notes": "保持小而稳定。",
            }
        ],
        "important_files": [
            {
                "path": "include/storage.h",
                "role": "公共接口",
                "why_it_matters": "定义应用调用面。",
                "related_chapters": ["repository_overview", "module_layers"],
            }
        ],
        "directory_relationships": {"summary": "应用通过公共头文件进入核心实现。"},
        "boundary_notes": [{"area": "demo", "note": "示例代码不是库的一部分。"}],
    }


def minimal_module_layers_chapter():
    return {
        "chapter": {"key": "module_layers", "title": "系统分层与模块职责"},
        "summary": "系统分为接口层和核心层。",
        "layers": [
            {
                "layer_id": "api",
                "name": "接口层",
                "role": "接收应用调用。",
                "responsibilities": ["稳定入口"],
                "paths": ["include"],
                "notes": "不拥有存储细节。",
            },
            {
                "layer_id": "core",
                "name": "核心层",
                "role": "实现持久化流程。",
                "responsibilities": ["调度读写"],
                "paths": ["src"],
                "notes": "依赖平台适配。",
            },
        ],
        "modules": [
            {
                "module_id": "storage_api",
                "name": "存储接口",
                "layer_id": "api",
                "purpose": "提供应用入口。",
                "source_paths": ["include/storage.h"],
                "owns": ["接口契约"],
                "consumes": ["应用请求"],
                "produces": ["核心调用"],
                "does_not_own": ["平台驱动"],
                "collaborates_with": [{"module_ref": "storage_core", "relationship": "调用核心实现。"}],
                "read_when": "理解集成入口时。",
                "notes": "只描述职责，不列函数原型。",
            },
            {
                "module_id": "storage_core",
                "name": "存储核心",
                "layer_id": "core",
                "purpose": "组织持久化读写。",
                "source_paths": ["src/storage.c"],
                "owns": ["读写流程"],
                "consumes": ["接口层调用"],
                "produces": ["平台适配调用"],
                "does_not_own": ["具体硬件"],
                "collaborates_with": [],
                "read_when": "理解主线行为时。",
                "notes": "机制细节放在第六章。",
            },
        ],
        "boundary_notes": [{"topic": "API 细节", "note": "不在本章展开参数和返回值。"}],
    }


def minimal_repository_mainline_chapter():
    return {
        "chapter": {"key": "repository_mainline", "title": "仓库主线"},
        "summary": "主线展示应用初始化到存储就绪的路径。",
        "mainline_overview_diagram": {
            "id": "mainline_overview",
            "title": "初始化主线",
            "diagram_type": "flowchart",
            "description": "应用进入库并完成核心初始化。",
            "source": "flowchart TD\n  app[应用] --> api[存储接口]\n  api --> core[存储核心]",
        },
        "mainlines": [
            {
                "mainline_id": "init",
                "name": "初始化",
                "purpose": "让存储能力可用。",
                "entry": {
                    "kind": "api",
                    "name": "storage_init",
                    "description": "应用初始化入口。",
                    "source_ref": {"path": "include/storage.h", "symbol": "storage_init"},
                },
                "steps": [
                    {
                        "order": 1,
                        "step": "应用调用公共入口。",
                        "module_refs": ["storage_api"],
                        "source_refs": [{"path": "include/storage.h", "symbol": "storage_init"}],
                        "effect": "进入库边界。",
                    },
                    {
                        "order": 2,
                        "step": "核心层准备运行状态。",
                        "module_refs": ["storage_core"],
                        "source_refs": [{"path": "src/storage.c", "symbol": "storage_init"}],
                        "effect": "存储核心可处理请求。",
                    },
                ],
                "result": "初始化完成。",
                "notes": "这是阅读主线，不是调用序列参考。",
            }
        ],
        "cross_mainline_notes": [{"topic": "移植", "note": "平台驱动由第七章说明。"}],
    }


def minimal_mechanism_chapter():
    return {
        "section": {"title": "持久化写入机制"},
        "why_it_matters": "这是理解仓库行为的核心机制。",
        "reader_prerequisites": ["先读仓库主线。"],
        "related_modules": ["storage_core"],
        "source_focus": [{"source_ref": {"path": "src/storage.c", "symbol": "storage_write"}, "reason": "写入流程入口。"}],
        "mechanism_overview": "核心层接收写入请求并交给平台适配完成。",
        "flow": [
            {
                "order": 1,
                "step": "检查写入请求。",
                "source_refs": [{"path": "src/storage.c", "symbol": "storage_write"}],
                "state_or_data": "写入缓冲区。",
                "notes": "这里只讲机制，不列 API 表。",
            }
        ],
        "key_states_or_data": [
            {
                "name": "写入缓冲区",
                "kind": "runtime_value",
                "description": "调用方传入的数据。",
                "source_refs": [{"path": "src/storage.c", "symbol": "storage_write"}],
            }
        ],
        "common_misunderstandings": [{"misunderstanding": "核心层直接访问硬件。", "correction": "硬件访问属于平台适配。"}],
        "validation_gaps": ["未在真实硬件上验证写入时序。"],
        "confidence": "medium",
    }


def minimal_integration_boundaries_chapter():
    return {
        "chapter": {"key": "integration_boundaries", "title": "配置、移植与集成边界"},
        "summary": "集成者需要提供平台驱动。",
        "required_configuration": [
            {
                "name": "存储大小",
                "kind": "macro",
                "location": {"description": "配置头文件", "source_ref": {"path": "include/storage_cfg.h"}},
                "purpose": "定义可用存储空间。",
                "required_when": "启用库时。",
                "notes": "示例值不代表生产配置。",
            }
        ],
        "required_adaptations": [
            {
                "name": "底层写入",
                "kind": "port_function",
                "location": {"description": "平台适配文件", "source_ref": {"path": "port/storage_port.c", "symbol": "storage_port_write"}},
                "responsibility": "把数据写入硬件。",
                "caller_or_consumer": "存储核心。",
                "failure_if_missing": "写入请求无法完成。",
            }
        ],
        "integration_paths": [
            {
                "name": "应用集成",
                "scenario": "应用初始化存储库。",
                "recommended_entry": {"description": "调用公共初始化接口。", "source_ref": {"path": "include/storage.h", "symbol": "storage_init"}},
                "steps": ["配置宏", "实现平台函数", "调用初始化入口"],
                "reference_examples": ["examples/basic"],
                "notes": "示例路径可不存在于最小测试仓库。",
            }
        ],
        "external_dependencies": [{"name": "Flash 驱动", "kind": "hardware", "used_by": "平台适配", "integration_role": "提供擦写能力。", "notes": "由平台工程提供。"}],
        "out_of_scope_responsibilities": [{"topic": "硬件寿命评估", "owner": "application", "reason": "依赖产品场景。"}],
    }


def minimal_risks_validation_chapter():
    return {
        "chapter": {"key": "risks_validation", "title": "风险、假设与验证缺口"},
        "summary": "主要缺口来自静态分析。",
        "risks": [
            {
                "risk_id": "static_only",
                "description": "未执行目标硬件验证。",
                "impact": "时序问题可能遗漏。",
                "mitigation": "在目标板运行集成测试。",
                "related_modules": ["storage_core"],
                "related_mechanisms": ["persistence"],
                "confidence": "medium",
            }
        ],
        "assumptions": [
            {
                "assumption_id": "caller_initializes_once",
                "description": "应用按预期只初始化一次。",
                "rationale": "静态阅读未发现重复初始化保护。",
                "validation_suggestion": "补充重复初始化测试。",
                "confidence": "low",
            }
        ],
        "validation_gaps": [
            {
                "gap_id": "target_board",
                "gap_type": "missing_runtime_validation",
                "description": "未运行目标板测试。",
                "why_it_matters": "硬件行为影响持久化可靠性。",
                "suggested_validation": "在目标板执行写入回读。",
                "related_chapters": ["key_mechanisms"],
                "confidence": "medium",
            }
        ],
        "low_confidence_items": [
            {
                "item_id": "port_behavior",
                "location": {"kind": "chapter", "chapter": "integration_boundaries"},
                "description": "平台适配行为来自接口推断。",
                "reason": "没有目标平台实现。",
                "needed_evidence": "具体平台代码。",
            }
        ],
    }


def write_valid_package(
    tmpdir: str,
    *,
    key_mechanisms=True,
    repository_name="example",
    document_title="示例仓库结构说明",
    output_file="Example_STRUCTURE_DESIGN.md",
) -> Path:
    root = Path(tmpdir)
    manifest = dict(FIXED_MANIFEST)
    if not key_mechanisms:
        manifest["key_mechanisms"] = []
    write_json(root / "structure.manifest.json", manifest)
    document = minimal_document_chapter()
    document["document"]["title"] = document_title
    document["document"]["output_file"] = output_file
    document["repository"]["name"] = repository_name
    document["repository"]["root_display_path"] = repository_name
    write_json(root / manifest["document"], document)
    write_json(root / manifest["repository_overview"], minimal_repository_overview_chapter())
    write_json(root / manifest["directory_map"], minimal_directory_map_chapter())
    write_json(root / manifest["module_layers"], minimal_module_layers_chapter())
    write_json(root / manifest["repository_mainline"], minimal_repository_mainline_chapter())
    if key_mechanisms:
        write_json(root / manifest["key_mechanisms"][0], minimal_mechanism_chapter())
    integration = manifest["integration_boundaries"]
    risks = minimal_risks_validation_chapter()
    if not key_mechanisms:
        risks["risks"][0]["related_mechanisms"] = []
        risks["validation_gaps"].append(
            {
                "gap_id": "no_mechanisms",
                "gap_type": "no_key_mechanisms_selected",
                "description": "本次分析未选择关键机制。",
                "why_it_matters": "第六章为空需要显式说明。",
                "suggested_validation": "重新评估候选机制。",
                "related_chapters": ["key_mechanisms"],
                "confidence": "medium",
            }
        )
    write_json(root / integration, minimal_integration_boundaries_chapter())
    write_json(root / manifest["risks_validation"], risks)
    return root / "structure.manifest.json"
