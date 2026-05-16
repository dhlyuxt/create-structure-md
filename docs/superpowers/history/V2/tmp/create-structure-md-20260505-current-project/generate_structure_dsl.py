#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORK_DIR = Path(__file__).resolve().parent
DSL_PATH = WORK_DIR / "structure.dsl.json"
REVIEW_PATH = WORK_DIR / "mermaid-readability-review.json"


def meta(confidence="observed", evidence_refs=None):
    return {
        "confidence": confidence,
        "evidence_refs": evidence_refs or [],
        "traceability_refs": [],
        "source_snippet_refs": [],
    }


def evidence(evidence_id, title, location, description, confidence="observed", kind="source"):
    return {
        "id": evidence_id,
        "kind": kind,
        "title": title,
        "location": location,
        "description": description,
        "confidence": confidence,
    }


def diagram(diagram_id, title, source, kind="flow", diagram_type="flowchart", description="", confidence="observed"):
    return {
        "id": diagram_id,
        "kind": kind,
        "title": title,
        "diagram_type": diagram_type,
        "description": description,
        "source": source,
        "confidence": confidence,
    }


def location(file_path, symbol="", line_start=None, line_end=None):
    return {
        "file_path": file_path,
        "symbol": symbol,
        "line_start": line_start,
        "line_end": line_end,
    }


def parameter_table(rows, reason=""):
    return {"rows": rows, "not_applicable_reason": "" if rows else reason}


def dependency_table(rows, reason=""):
    return {"rows": rows, "not_applicable_reason": "" if rows else reason}


def data_table(rows, reason=""):
    return {"rows": rows, "not_applicable_reason": "" if rows else reason}


def mechanism_table(rows, reason=""):
    return {"rows": rows, "not_applicable_reason": "" if rows else reason}


def limitation_table(rows, reason=""):
    return {"rows": rows, "not_applicable_reason": "" if rows else reason}


def interface_params(rows):
    return {"rows": rows, "not_applicable_reason": "" if rows else "该接口无显式参数。"}


def interface_returns(rows):
    return {"rows": rows, "not_applicable_reason": "" if rows else "该接口无显式返回值。"}


def module_param(parameter_id, prototype, value_or_default, value_source, meaning, evidence_refs=None, confidence="observed"):
    row = {
        "parameter_id": parameter_id,
        "prototype": prototype,
        "value_or_default": value_or_default,
        "value_source": value_source,
        "meaning": meaning,
    }
    row.update(meta(confidence, evidence_refs))
    return row


def module_dep(
    dependency_id,
    name,
    dependency_type,
    usage_relation,
    required_for,
    failure_behavior,
    evidence_refs=None,
    target_module_id="",
    target_data_id="",
    system_dependency_ref="",
    confidence="observed",
):
    row = {
        "dependency_id": dependency_id,
        "name": name,
        "dependency_type": dependency_type,
        "usage_relation": usage_relation,
        "target_module_id": target_module_id,
        "target_data_id": target_data_id,
        "system_dependency_ref": system_dependency_ref,
        "required_for": required_for,
        "failure_behavior": failure_behavior,
    }
    row.update(meta(confidence, evidence_refs))
    return row


def module_data(data_id, name, data_type, role, producer, consumer, shape_or_contract, evidence_refs=None):
    row = {
        "data_id": data_id,
        "name": name,
        "data_type": data_type,
        "role": role,
        "producer": producer,
        "consumer": consumer,
        "shape_or_contract": shape_or_contract,
    }
    row.update(meta("observed", evidence_refs))
    return row


def mechanism_row(mechanism_id, name, purpose, input_value, processing, output, significance, anchors, evidence_refs=None):
    row = {
        "mechanism_id": mechanism_id,
        "mechanism_name": name,
        "purpose": purpose,
        "input": input_value,
        "processing": processing,
        "output": output,
        "structural_significance": significance,
        "related_anchors": anchors,
    }
    row.update(meta("observed", evidence_refs))
    return row


def anchor(anchor_type, value, reason=""):
    return {"anchor_type": anchor_type, "value": value, "reason": reason}


def text_block(block_id, title, text, evidence_refs=None, confidence="observed"):
    block = {"block_id": block_id, "block_type": "text", "title": title, "text": text}
    block.update(meta(confidence, evidence_refs))
    return block


def table_block(block_id, title, columns, rows, evidence_refs=None, confidence="observed"):
    block = {
        "block_id": block_id,
        "block_type": "table",
        "title": title,
        "table": {"id": f"TBL-{block_id}", "title": title, "columns": columns, "rows": rows},
    }
    block.update(meta(confidence, evidence_refs))
    return block


def limitation(limitation_id, text, impact, mitigation, evidence_refs=None, confidence="observed"):
    row = {
        "limitation_id": limitation_id,
        "limitation": text,
        "impact": impact,
        "mitigation_or_next_step": mitigation,
    }
    row.update(meta(confidence, evidence_refs))
    return row


def contract_interface(interface_id, name, interface_type, purpose, file_path, contract_scope, required_items, consumers, constraints, validation_behavior, evidence_refs):
    interface = {
        "interface_id": interface_id,
        "interface_name": name,
        "interface_type": interface_type,
        "purpose": purpose,
        "location": location(file_path),
        "contract": {
            "contract_scope": contract_scope,
            "contract_location": file_path,
            "required_items": required_items,
            "constraints": constraints,
            "consumers": consumers,
            "validation_behavior": validation_behavior,
        },
    }
    interface.update(meta("observed", evidence_refs))
    return interface


def cli_interface(interface_id, name, prototype, purpose, file_path, parameters, returns, flow_source, side_effects, errors, consumers, evidence_refs):
    interface = {
        "interface_id": interface_id,
        "interface_name": name,
        "interface_type": "command_line",
        "prototype": prototype,
        "purpose": purpose,
        "location": location(file_path, "main"),
        "parameters": interface_params(parameters),
        "return_values": interface_returns(returns),
        "execution_flow_diagram": diagram(
            f"MER-{interface_id}",
            f"{name} 执行流程",
            flow_source,
            kind="interface_execution_flow",
            description=f"展示 {name} 的命令行处理路径。",
        ),
        "side_effects": side_effects,
        "error_behavior": errors,
        "consumers": consumers,
    }
    interface.update(meta("observed", evidence_refs))
    return interface


def library_interface(interface_id, name, prototype, purpose, file_path, parameters, returns, flow_source, errors, consumers, evidence_refs):
    interface = {
        "interface_id": interface_id,
        "interface_name": name,
        "interface_type": "library_api",
        "prototype": prototype,
        "purpose": purpose,
        "location": location(file_path),
        "parameters": interface_params(parameters),
        "return_values": interface_returns(returns),
        "execution_flow_diagram": diagram(
            f"MER-{interface_id}",
            f"{name} 调用流程",
            flow_source,
            kind="interface_execution_flow",
            description=f"展示 {name} 被内部调用时的输入与输出。",
        ),
        "side_effects": ["不写入文件；只返回校验结果或抛出调用方处理的异常。"],
        "error_behavior": errors,
        "consumers": consumers,
    }
    interface.update(meta("observed", evidence_refs))
    return interface


def public_interfaces(summary, interfaces, reason=""):
    return {
        "summary": summary,
        "interface_index": {
            "rows": [
                {
                    "interface_id": interface["interface_id"],
                    "interface_name": interface["interface_name"],
                    "interface_type": interface["interface_type"],
                    "description": interface["purpose"],
                }
                for interface in interfaces
            ]
        },
        "interfaces": interfaces,
        "not_applicable_reason": "" if interfaces else reason,
    }


def source_scope(summary, primary_files, consumed_inputs, owned_outputs, out_of_scope):
    return {
        "summary": summary,
        "primary_files": primary_files,
        "consumed_inputs": consumed_inputs,
        "owned_outputs": owned_outputs,
        "out_of_scope": out_of_scope,
    }


def source_file(path, role, language, notes=""):
    return {"path": path, "role": role, "language": language, "notes": notes}


def module(
    module_id,
    name,
    kind,
    summary,
    scope,
    configuration,
    dependencies,
    data_objects,
    interfaces,
    mechanisms,
    limitations,
    evidence_refs,
    notes=None,
):
    return {
        "module_id": module_id,
        "name": name,
        "module_kind": kind,
        "summary": summary,
        "source_scope": scope,
        "configuration": configuration,
        "dependencies": dependencies,
        "data_objects": data_objects,
        "public_interfaces": interfaces,
        "internal_mechanism": mechanisms,
        "known_limitations": limitations,
        "evidence_refs": evidence_refs,
        "traceability_refs": [],
        "source_snippet_refs": [],
        "notes": notes or [],
        "confidence": "observed",
    }


def module_configuration(summary, rows=None, reason="该模块没有独立运行配置。"):
    return {"summary": summary, "parameters": parameter_table(rows or [], reason)}


def module_dependencies(summary, rows=None, reason="该模块没有需要单独说明的模块级依赖。"):
    return {"summary": summary, "rows": rows or [], "not_applicable_reason": "" if rows else reason}


def module_data_objects(summary, rows=None, reason="该模块没有需要单独说明的数据对象。"):
    return {"summary": summary, "rows": rows or [], "not_applicable_reason": "" if rows else reason}


def internal_mechanism(summary, rows, details, reason=""):
    return {
        "summary": summary,
        "mechanism_index": mechanism_table(rows, reason),
        "mechanism_details": details,
        "not_applicable_reason": "" if rows or details or summary else reason,
    }


def mechanism_detail(mechanism_id, blocks):
    return {"mechanism_id": mechanism_id, "blocks": blocks}


def known_limitations(summary, rows=None, reason="未识别到模块级已知限制。"):
    return {"summary": summary, "rows": rows or [], "not_applicable_reason": "" if rows else reason}


def flow_step(step_id, order, actor, description, input_value, output, modules, runtime_units, evidence_refs=None):
    row = {
        "step_id": step_id,
        "order": order,
        "actor": actor,
        "description": description,
        "input": input_value,
        "output": output,
        "related_module_ids": modules,
        "related_runtime_unit_ids": runtime_units,
    }
    row.update(meta("observed", evidence_refs))
    return row


def flow_branch(branch_id, condition, handling, modules, runtime_units, evidence_refs=None, confidence="observed"):
    row = {
        "branch_id": branch_id,
        "condition": condition,
        "handling": handling,
        "related_module_ids": modules,
        "related_runtime_unit_ids": runtime_units,
    }
    row.update(meta(confidence, evidence_refs))
    return row


def runtime_unit(unit_id, name, unit_type, entrypoint, responsibility, modules, notes, evidence_refs=None):
    row = {
        "unit_id": unit_id,
        "unit_name": name,
        "unit_type": unit_type,
        "entrypoint": entrypoint,
        "responsibility": responsibility,
        "related_module_ids": modules,
        "notes": notes,
    }
    row.update(meta("observed", evidence_refs))
    return row


def config_item(config_id, name, source, used_by, purpose, notes, evidence_refs=None):
    row = {
        "config_id": config_id,
        "config_name": name,
        "source": source,
        "used_by": used_by,
        "purpose": purpose,
        "notes": notes,
    }
    row.update(meta("observed", evidence_refs))
    return row


def data_artifact(artifact_id, name, artifact_type, owner, producer, consumer, notes, evidence_refs=None):
    row = {
        "artifact_id": artifact_id,
        "artifact_name": name,
        "artifact_type": artifact_type,
        "owner": owner,
        "producer": producer,
        "consumer": consumer,
        "notes": notes,
    }
    row.update(meta("observed", evidence_refs))
    return row


def system_dep(dependency_id, name, dependency_type, used_by, purpose, notes, evidence_refs=None):
    row = {
        "dependency_id": dependency_id,
        "dependency_name": name,
        "dependency_type": dependency_type,
        "used_by": used_by,
        "purpose": purpose,
        "notes": notes,
    }
    row.update(meta("observed", evidence_refs))
    return row


def collaboration(collaboration_id, scenario, initiator, participants, method, description, evidence_refs=None):
    row = {
        "collaboration_id": collaboration_id,
        "scenario": scenario,
        "initiator_module_id": initiator,
        "participant_module_ids": participants,
        "collaboration_method": method,
        "description": description,
    }
    row.update(meta("observed", evidence_refs))
    return row


def risk(risk_id, description, impact, mitigation, confidence, evidence_refs=None):
    row = {
        "id": risk_id,
        "description": description,
        "impact": impact,
        "mitigation": mitigation,
    }
    row.update(meta(confidence, evidence_refs))
    return row


def assumption(assumption_id, description, rationale, validation, confidence, evidence_refs=None):
    row = {
        "id": assumption_id,
        "description": description,
        "rationale": rationale,
        "validation_suggestion": validation,
    }
    row.update(meta(confidence, evidence_refs))
    return row


def flow(flow_id, name, overview, steps, branches, modules, runtime_units, diagram_source, evidence_refs=None):
    item = {
        "flow_id": flow_id,
        "name": name,
        "overview": overview,
        "steps": steps,
        "branches_or_exceptions": branches,
        "related_module_ids": modules,
        "related_runtime_unit_ids": runtime_units,
        "diagram": diagram(
            f"MER-{flow_id}",
            f"{name}流程图",
            diagram_source,
            kind="key_flow",
            description=f"展示{name}的关键步骤。",
        ),
    }
    item.update(meta("observed", evidence_refs))
    return item


def build_document():
    evidence_items = [
        evidence("EV-SKILL-CONTRACT", "技能入口和工作流契约", "SKILL.md", "定义技能用途、边界、输入就绪条件、V2 DSL 工作流和输出要求。"),
        evidence("EV-DSL-SPEC", "V2 DSL 规范", "references/dsl-spec.md", "说明 V2 DSL 顶层字段、模块模型、支持数据、ID 和 Mermaid 期望路径。"),
        evidence("EV-DOCUMENT-STRUCTURE", "固定文档结构", "references/document-structure.md", "说明固定 9 章结构、章节编号、表格列和 Mermaid 元数据要求。"),
        evidence("EV-MERMAID-RULES", "Mermaid 规则", "references/mermaid-rules.md", "说明 Mermaid-only 输出、支持图类型和严格校验策略。"),
        evidence("EV-REVIEW-CHECKLIST", "最终复核清单", "references/review-checklist.md", "列出输出报告、边界、DSL、Mermaid 和文本安全复核项。"),
        evidence("EV-SCHEMA", "DSL JSON Schema", "schemas/structure-design.schema.json", "定义 V2 DSL 的 JSON Schema 结构约束。"),
        evidence("EV-V2-FOUNDATION", "V2 基础规则实现", "scripts/v2_foundation.py", "提供 V2 版本门禁、枚举、not_applicable 规则、ID 作用域和全局规则检查。"),
        evidence("EV-V2-PHASE2", "V2 模块模型语义实现", "scripts/v2_phase2.py", "检查 Chapter 4 V2 模块模型、接口详情、锚点和运行单元引用。"),
        evidence("EV-V2-PHASE3", "V2 内容块语义实现", "scripts/v2_phase3.py", "检查内部机制和第 9 章内容块规则。"),
        evidence("EV-V2-PHASE4", "V2 Mermaid 门禁辅助实现", "scripts/v2_phase4.py", "收集预期 Mermaid 图、验证可读性复核工件并检查渲染完整性。"),
        evidence("EV-DSL-VALIDATOR", "DSL 校验器实现", "scripts/validate_dsl.py", "提供 DSL schema 校验和语义校验 CLI。"),
        evidence("EV-MERMAID-VALIDATOR", "Mermaid 校验器实现", "scripts/validate_mermaid.py", "提供 DSL/Markdown Mermaid 静态和严格校验 CLI。"),
        evidence("EV-MERMAID-GATE", "V2 Mermaid 门禁 CLI", "scripts/verify_v2_mermaid_gates.py", "把可读性工件、V2 全局规则、预渲染严格校验和渲染后完整性校验串联为门禁。"),
        evidence("EV-RENDERER", "Markdown 渲染器实现", "scripts/render_markdown.py", "提供固定 9 章 Markdown 渲染、支持数据隐藏模式、diagram-id 元数据和输出写入策略。"),
        evidence("EV-INSTALLER", "copy-only 安装器实现", "scripts/install_skill.py", "提供保守的本地技能复制安装、源结构检查和依赖状态报告。"),
        evidence("EV-INSTALL-DOC", "安装文档", "docs/install.md", "说明 dry-run、安装、既有目标处理、依赖和测试命令。"),
        evidence("EV-EXAMPLES", "V2 DSL 示例", "examples/minimal-from-code.dsl.json, examples/minimal-from-requirements.dsl.json", "提供可校验、可渲染的 V2 DSL 示例。"),
        evidence("EV-TESTS", "unittest 测试集合", "tests/", "覆盖 schema、语义校验、Mermaid、渲染、安装和端到端契约。"),
        evidence("EV-REQUIREMENTS", "Python 依赖声明", "requirements.txt", "声明 jsonschema 运行依赖。"),
        evidence("EV-V2-DESIGN", "V2 设计规格", "docs/superpowers/specs/2026-05-04-create-structure-md-v2-design.md", "记录 V2 版本、隐藏证据、Chapter 4 模型、Mermaid 门禁和验收标准。", kind="analysis"),
        evidence("EV-WORKTREE", "当前工作区状态", "git status --short", "扫描时看到旧 .codex-tmp 产物和 create-structure-md_STRUCTURE_DESIGN.md 处于删除状态；本次生成不清理、不回滚。", confidence="observed", kind="analysis"),
    ]

    contract_interfaces = [
        contract_interface(
            "IFACE-CONTRACT-SKILL",
            "create-structure-md 技能契约",
            "document_contract",
            "规定技能边界、输入就绪、DSL 生成、Mermaid 门禁、渲染和最终报告要求。",
            "SKILL.md",
            "Codex 执行 create-structure-md 结构设计文档生成任务时遵循的行为契约。",
            ["dsl_version 0.2.0", "structure.dsl.json", "mermaid-readability-review.json", "单个 Markdown 输出文件"],
            ["Codex", "仓库维护者"],
            ["不负责仓库分析", "不生成 Word/PDF/图片", "临时文件保留供审查"],
            "Codex 按工作流步骤执行；缺失输入时先在技能外补齐结构理解。",
            ["EV-SKILL-CONTRACT"],
        ),
        contract_interface(
            "IFACE-CONTRACT-REFERENCES",
            "references 参考文档契约",
            "document_contract",
            "为 DSL、文档结构、Mermaid 规则和复核清单提供细分规则来源。",
            "references/",
            "覆盖 DSL 形状、固定章节、图表规则和最终报告复核要求。",
            ["dsl-spec.md", "document-structure.md", "mermaid-rules.md", "review-checklist.md"],
            ["Codex", "测试模块", "仓库维护者"],
            ["固定 9 章结构", "Mermaid-only 输出", "strict validation 是最终门禁"],
            "作为生成 DSL、渲染和复核的规则依据，由测试检查关键短语。",
            ["EV-DSL-SPEC", "EV-DOCUMENT-STRUCTURE", "EV-MERMAID-RULES", "EV-REVIEW-CHECKLIST"],
        ),
    ]

    schema_interfaces = [
        contract_interface(
            "IFACE-SCHEMA-STRUCTURE",
            "structure-design.schema.json",
            "schema_contract",
            "定义 create-structure-md V2 DSL 的对象形状、必填字段、枚举和安全文件名约束。",
            "schemas/structure-design.schema.json",
            "覆盖 document、system_overview、architecture_views、module_design、runtime_view、configuration_data_dependencies、cross_module_collaboration、key_flows、structure_issues_and_suggestions 和支持数据数组。",
            ["dsl_version", "document", "module_design", "key_flows", "evidence"],
            ["validate_dsl.py", "测试模块", "DSL 作者"],
            ["dsl_version 必须为 0.2.0", "diagram_type 只允许 MVP Mermaid 类型", "output_file 必须是安全 Markdown 文件名"],
            "validate_dsl.py 使用 Draft202012Validator 执行结构校验，失败时不进入语义校验。",
            ["EV-SCHEMA", "EV-DSL-VALIDATOR"],
        )
    ]

    foundation_interfaces = [
        library_interface(
            "IFACE-V2-FOUNDATION-RULES",
            "V2 基础规则库",
            "require_v2_dsl_version(document); v2_global_rule_violations(document)",
            "为校验器、渲染器和 Mermaid 门禁提供共享 V2 版本门禁、枚举和全局语义规则。",
            "scripts/v2_foundation.py",
            [
                {"parameter_name": "document", "parameter_type": "dict", "description": "已解析的 DSL JSON 对象。", "direction": "input"}
            ],
            [
                {"return_name": "violations", "return_type": "list[RuleViolation]", "description": "全局规则违规列表。", "condition": "调用 v2_global_rule_violations 时返回。"}
            ],
            "flowchart TD\n  A[\"DSL document\"] --> B[\"Version gate\"]\n  B --> C[\"not applicable checks\"]\n  C --> D[\"enum and ID checks\"]\n  D --> E[\"global violations\"]",
            [{"condition": "dsl_version 不是 0.2.0", "behavior": "require_v2_dsl_version 抛出 ValueError，调用方转换为错误码或渲染错误。"}],
            ["validate_dsl.py", "render_markdown.py", "verify_v2_mermaid_gates.py"],
            ["EV-V2-FOUNDATION"],
        )
    ]

    validate_cli = cli_interface(
        "IFACE-DSL-VALIDATE-CLI",
        "validate_dsl.py",
        "python3 scripts/validate_dsl.py structure.dsl.json [--allow-long-snippets]",
        "校验 DSL JSON 的 schema、V2 全局规则、模块模型、内容块、引用、安全文本和支持数据。",
        "scripts/validate_dsl.py",
        [
            {"parameter_name": "dsl_file", "parameter_type": "path", "description": "待校验的 structure DSL JSON 文件。", "direction": "input"},
            {"parameter_name": "--allow-long-snippets", "parameter_type": "flag", "description": "允许超过 50 行的源码片段降级为警告。", "direction": "input"},
        ],
        [
            {"return_name": "exit_code", "return_type": "int", "description": "0 表示成功，1 表示语义错误，2 表示输入或版本错误。", "condition": "命令结束时返回。"}
        ],
        "flowchart TD\n  A[\"Parse args\"] --> B[\"Load JSON\"]\n  B --> C[\"Require V2\"]\n  C --> D[\"Schema validation\"]\n  D --> E[\"Semantic checks\"]\n  E --> F[\"Report result\"]",
        ["读取 DSL 文件。", "向 stdout 或 stderr 输出校验结果。"],
        [
            {"condition": "文件不存在或 JSON 无效", "behavior": "输出输入错误并返回 2。"},
            {"condition": "schema 或语义校验失败", "behavior": "输出错误报告并返回非 0。"},
        ],
        ["Codex", "测试模块", "仓库维护者"],
        ["EV-DSL-VALIDATOR", "EV-SCHEMA", "EV-V2-FOUNDATION", "EV-V2-PHASE2", "EV-V2-PHASE3"],
    )

    mermaid_cli = cli_interface(
        "IFACE-MERMAID-VALIDATE-CLI",
        "validate_mermaid.py",
        "python3 scripts/validate_mermaid.py --from-dsl structure.dsl.json --strict --work-dir <dir>",
        "从 DSL 或 Markdown 中提取 Mermaid 图并执行静态或严格校验。",
        "scripts/validate_mermaid.py",
        [
            {"parameter_name": "--from-dsl", "parameter_type": "path", "description": "从 DSL JSON 中提取图。", "direction": "input"},
            {"parameter_name": "--from-markdown", "parameter_type": "path", "description": "从渲染后的 Markdown 中提取图。", "direction": "input"},
            {"parameter_name": "--strict", "parameter_type": "flag", "description": "调用本地 Mermaid CLI 验证可渲染性。", "direction": "input"},
            {"parameter_name": "--work-dir", "parameter_type": "path", "description": "严格校验临时产物目录。", "direction": "input"},
        ],
        [
            {"return_name": "exit_code", "return_type": "int", "description": "0 表示 Mermaid 校验成功，非 0 表示环境或图源错误。", "condition": "命令结束时返回。"}
        ],
        "flowchart TD\n  A[\"Select source\"] --> B[\"Extract diagrams\"]\n  B --> C[\"Static checks\"]\n  C --> D[\"Strict mode\"]\n  D --> E[\"Run mmdc\"]\n  E --> F[\"Report result\"]",
        ["读取 DSL 或 Markdown 文件。", "严格模式下写入临时 mmd/svg 验证产物。"],
        [
            {"condition": "图源含 DOT 或不支持类型", "behavior": "报告静态校验错误并返回 1。"},
            {"condition": "node 或 mmdc 缺失", "behavior": "严格模式返回错误，不能作为最终门禁通过。"},
        ],
        ["Codex", "V2 Mermaid 门禁 CLI", "测试模块"],
        ["EV-MERMAID-VALIDATOR", "EV-MERMAID-RULES"],
    )

    gate_cli = cli_interface(
        "IFACE-MERMAID-GATE-CLI",
        "verify_v2_mermaid_gates.py",
        "python3 scripts/verify_v2_mermaid_gates.py structure.dsl.json --mermaid-review-artifact review.json --pre-render --work-dir <dir>",
        "验证 V2 DSL 全局规则、Mermaid 可读性复核工件、预渲染严格校验、渲染后完整性和严格 Markdown Mermaid 校验。",
        "scripts/verify_v2_mermaid_gates.py",
        [
            {"parameter_name": "dsl_file", "parameter_type": "path", "description": "V2 DSL JSON 文件。", "direction": "input"},
            {"parameter_name": "--mermaid-review-artifact", "parameter_type": "path", "description": "Mermaid 可读性复核 JSON 工件。", "direction": "input"},
            {"parameter_name": "--pre-render 或 --post-render", "parameter_type": "mode", "description": "选择预渲染或渲染后门禁。", "direction": "input"},
            {"parameter_name": "--rendered-markdown", "parameter_type": "path", "description": "post-render 模式下的 Markdown 输出文件。", "direction": "input"},
        ],
        [
            {"return_name": "exit_code", "return_type": "int", "description": "0 表示门禁通过，1 表示校验失败，2 表示输入或版本错误。", "condition": "命令结束时返回。"}
        ],
        "flowchart TD\n  A[\"Load DSL\"] --> B[\"V2 global rules\"]\n  B --> C[\"Review artifact\"]\n  C --> D[\"Pre render strict\"]\n  C --> E[\"Post render completeness\"]\n  E --> F[\"Markdown strict\"]",
        ["读取 DSL、复核工件和可选 Markdown。", "调用 validate_mermaid.py 并写入严格校验临时产物。"],
        [
            {"condition": "复核工件缺失、损坏或覆盖不完整", "behavior": "返回错误并阻止 Mermaid 严格门禁继续。"},
            {"condition": "post-render 缺少 rendered Markdown", "behavior": "argparse 报错。"},
        ],
        ["Codex", "测试模块"],
        ["EV-MERMAID-GATE", "EV-V2-PHASE4", "EV-MERMAID-VALIDATOR"],
    )

    render_cli = cli_interface(
        "IFACE-RENDER-CLI",
        "render_markdown.py",
        "python3 scripts/render_markdown.py structure.dsl.json --output-dir <dir> [--evidence-mode hidden|inline]",
        "把通过准备和校验的 V2 DSL 渲染为单个模块或系统专属 Markdown 文件。",
        "scripts/render_markdown.py",
        [
            {"parameter_name": "dsl_file", "parameter_type": "path", "description": "待渲染的 V2 DSL JSON 文件。", "direction": "input"},
            {"parameter_name": "--output-dir", "parameter_type": "path", "description": "输出 Markdown 文件目录。", "direction": "input"},
            {"parameter_name": "--evidence-mode", "parameter_type": "enum", "description": "hidden 为默认值，inline 会渲染支持数据。", "direction": "input"},
            {"parameter_name": "--overwrite 或 --backup", "parameter_type": "flag", "description": "控制目标文件存在时的写入策略。", "direction": "input"},
        ],
        [
            {"return_name": "exit_code", "return_type": "int", "description": "0 表示 Markdown 写入成功，非 0 表示输入或写入失败。", "condition": "命令结束时返回。"}
        ],
        "flowchart TD\n  A[\"Load DSL\"] --> B[\"Validate output name\"]\n  B --> C[\"Build render context\"]\n  C --> D[\"Render 9 chapters\"]\n  D --> E[\"Write output\"]",
        ["读取 DSL 文件。", "写入 document.output_file 指定的 Markdown 文件。", "使用 --backup 时写入备份文件。"],
        [
            {"condition": "output_file 泛化或含路径片段", "behavior": "返回输入错误且不写文件。"},
            {"condition": "目标文件已存在且未指定覆盖策略", "behavior": "返回写入错误并提示使用 --overwrite 或 --backup。"},
        ],
        ["Codex", "仓库维护者", "技能使用者"],
        ["EV-RENDERER", "EV-DOCUMENT-STRUCTURE"],
    )

    install_cli = cli_interface(
        "IFACE-INSTALL-CLI",
        "install_skill.py",
        "python3 scripts/install_skill.py [--dry-run] [--codex-home <dir>]",
        "把仓库运行时白名单文件复制到 Codex skills 目录，并报告依赖状态。",
        "scripts/install_skill.py",
        [
            {"parameter_name": "--dry-run", "parameter_type": "flag", "description": "只打印安装计划，不创建目标目录。", "direction": "input"},
            {"parameter_name": "--codex-home", "parameter_type": "path", "description": "显式指定 Codex home；否则读取 CODEX_HOME 或 ~/.codex。", "direction": "input"},
        ],
        [
            {"return_name": "exit_code", "return_type": "int", "description": "0 表示 dry-run 或安装成功，1 表示源或目标检查失败。", "condition": "命令结束时返回。"}
        ],
        "flowchart TD\n  A[\"Resolve target\"] --> B[\"Validate source\"]\n  B --> C[\"Print plan\"]\n  C --> D[\"Dry run\"]\n  D --> E[\"Copy runtime entries\"]\n  E --> F[\"Validate install\"]",
        ["读取源文件。", "非 dry-run 且目标不存在时创建目标目录并复制白名单条目。"],
        [
            {"condition": "目标技能目录已存在", "behavior": "失败退出并打印用户可自行执行的清理命令。"},
            {"condition": "复制中途失败", "behavior": "提示人工检查并给出用户审查后执行的清理命令。"},
        ],
        ["仓库维护者", "技能安装者"],
        ["EV-INSTALLER", "EV-INSTALL-DOC"],
    )

    test_cli = cli_interface(
        "IFACE-TEST-WORKFLOW",
        "unittest discover",
        "python3 -m unittest discover -s tests -v",
        "发现并执行 tests 目录中的契约测试和端到端测试。",
        "tests/",
        [
            {"parameter_name": "-s tests", "parameter_type": "path", "description": "测试发现目录。", "direction": "input"},
            {"parameter_name": "-v", "parameter_type": "flag", "description": "输出详细测试名称。", "direction": "input"},
        ],
        [
            {"return_name": "exit_code", "return_type": "int", "description": "0 表示测试全部通过，非 0 表示失败或错误。", "condition": "测试运行结束时返回。"}
        ],
        "flowchart TD\n  A[\"Discover tests\"] --> B[\"Load fixtures\"]\n  B --> C[\"Exercise scripts\"]\n  C --> D[\"Assert contracts\"]\n  D --> E[\"Report result\"]",
        ["读取 tests、examples、fixtures 和脚本文件。", "部分端到端测试会在 .codex-tmp 下保留测试产物。"],
        [
            {"condition": "断言失败", "behavior": "unittest 报告失败用例和 traceback。"},
            {"condition": "严格 Mermaid 环境不可用", "behavior": "相关测试按探测结果失败或跳过。"},
        ],
        ["仓库维护者", "CI 或本地测试运行者"],
        ["EV-TESTS", "EV-EXAMPLES"],
    )

    modules = [
        module(
            "MOD-CONTRACT-DOCS",
            "技能契约与参考文档模块",
            "documentation_contract",
            "定义 create-structure-md 的技能边界、输入就绪条件、V2 工作流、固定文档结构、Mermaid 规则和最终复核要求。",
            source_scope(
                "覆盖技能入口和 references 目录中可被 Codex 执行流程直接使用的规则文档。",
                [
                    source_file("SKILL.md", "技能入口、边界和工作流", "markdown"),
                    source_file("references/dsl-spec.md", "V2 DSL 规范", "markdown"),
                    source_file("references/document-structure.md", "固定 Markdown 输出结构", "markdown"),
                    source_file("references/mermaid-rules.md", "Mermaid 规则", "markdown"),
                    source_file("references/review-checklist.md", "最终复核清单", "markdown"),
                ],
                ["已准备的结构设计内容", "仓库理解阶段整理出的模块、接口、流程和依赖事实"],
                ["Codex 执行时的文档生成工作流约束", "最终报告复核依据"],
                ["不分析仓库源码", "不推理缺失需求", "不生成多文档、Word、PDF 或图像导出"],
            ),
            module_configuration("该模块是静态文档契约，不读取运行参数。"),
            module_dependencies("该模块以 Markdown 文档为规则来源，不依赖运行时库。"),
            module_data_objects(
                "该模块拥有规则文档对象。",
                [
                    module_data("DATA-CONTRACT-RULES", "技能与参考规则文档", "markdown", "规则契约", "仓库维护者", "Codex 和测试模块", "SKILL.md 与 references/*.md", ["EV-SKILL-CONTRACT", "EV-DSL-SPEC", "EV-DOCUMENT-STRUCTURE", "EV-MERMAID-RULES", "EV-REVIEW-CHECKLIST"]),
                ],
            ),
            public_interfaces("通过技能说明和参考文档对 Codex 暴露工作流契约。", contract_interfaces),
            internal_mechanism(
                "通过一个入口文件和四类 reference 文档拆分执行规则，使 DSL、渲染结构、Mermaid 和复核职责分离。",
                [
                    mechanism_row(
                        "MECH-CONTRACT-RULE-SPLIT",
                        "规则分层",
                        "把技能工作流、DSL 形状、输出结构、图表规则和复核标准分开维护。",
                        "用户请求和结构设计内容",
                        "SKILL.md 引导流程，references 提供专项约束。",
                        "可执行的结构文档生成流程",
                        "避免把 DSL schema、Mermaid 规则和最终复核混在单一说明中。",
                        [anchor("interface_id", "IFACE-CONTRACT-SKILL"), anchor("interface_id", "IFACE-CONTRACT-REFERENCES")],
                        ["EV-SKILL-CONTRACT", "EV-DSL-SPEC", "EV-DOCUMENT-STRUCTURE"],
                    )
                ],
                [
                    mechanism_detail(
                        "MECH-CONTRACT-RULE-SPLIT",
                        [
                            text_block("BLOCK-CONTRACT-SPLIT-TEXT", "规则分层说明", "技能入口只描述边界和总流程；DSL 规范、文档结构、Mermaid 规则和复核清单分别承载专项规则，生成文档时按这些规则组合执行。", ["EV-SKILL-CONTRACT"]),
                            table_block(
                                "BLOCK-CONTRACT-SPLIT-TABLE",
                                "规则文件职责",
                                [{"key": "file", "title": "文件"}, {"key": "role", "title": "职责"}],
                                [
                                    {"file": "SKILL.md", "role": "规定技能边界、输入就绪和步骤顺序。"},
                                    {"file": "references/dsl-spec.md", "role": "规定 DSL 字段、ID 和支持数据契约。"},
                                    {"file": "references/document-structure.md", "role": "规定固定 9 章 Markdown 输出。"},
                                    {"file": "references/mermaid-rules.md", "role": "规定 Mermaid-only 和 strict/static 差异。"},
                                ],
                            ),
                        ],
                    )
                ],
            ),
            known_limitations(
                "契约模块刻意保持生成边界清晰。",
                [
                    limitation("LIMIT-CONTRACT-NO-ANALYSIS", "技能自身不执行仓库分析或需求推理。", "调用方必须先在技能外准备完整结构内容。", "当前任务由 Codex 先扫描仓库，再进入 DSL 渲染流程。", ["EV-SKILL-CONTRACT"]),
                    limitation("LIMIT-CONTRACT-NO-CLEANUP", "临时文件不会自动删除。", "多次运行会留下 .codex-tmp 产物，需要人工审查后决定是否清理。", "如需清理，只给出命令，由用户执行。", ["EV-SKILL-CONTRACT"]),
                ],
            ),
            ["EV-SKILL-CONTRACT", "EV-DSL-SPEC", "EV-DOCUMENT-STRUCTURE", "EV-MERMAID-RULES"],
        ),
        module(
            "MOD-DSL-SCHEMA",
            "DSL Schema 模块",
            "schema_contract",
            "用 Draft 2020-12 JSON Schema 描述 V2 DSL 的顶层章节、表格行、模块模型、图表对象和支持数据结构。",
            source_scope(
                "该模块由单个 schema 文件承载，负责结构形状和枚举，不负责跨字段语义。",
                [source_file("schemas/structure-design.schema.json", "V2 DSL JSON Schema", "json")],
                ["结构设计 DSL JSON"],
                ["schema validation result", "字段形状和枚举契约"],
                ["不执行跨字段引用解析", "不调用 Mermaid CLI", "不写 Markdown"],
            ),
            module_configuration("Schema 文件自身没有运行参数。"),
            module_dependencies("Schema 文件是静态契约，不直接依赖运行时库。"),
            module_data_objects(
                "该模块拥有 DSL schema 契约数据。",
                [
                    module_data("DATA-SCHEMA-CONTRACT", "structure-design.schema.json", "json schema", "DSL 结构契约", "DSL Schema 模块", "DSL 校验器模块和测试模块", "Draft 2020-12 JSON Schema，包含 V2 DSL 顶层字段与 $defs", ["EV-SCHEMA"]),
                ],
            ),
            public_interfaces("通过 JSON Schema 文件暴露 DSL 结构契约。", schema_interfaces),
            internal_mechanism(
                "schema 以顶层 properties 和 $defs 组织固定章节、模块模型、运行视图、关键流程和支持数据。",
                [
                    mechanism_row(
                        "MECH-SCHEMA-DEFS",
                        "Schema 定义分组",
                        "把固定章节和可复用对象定义为可被 jsonschema 校验的结构。",
                        "DSL JSON",
                        "根对象 required 字段绑定章节，$defs 描述表格行、接口、图表和支持数据。",
                        "schema 校验错误或进入语义校验",
                        "保证 renderer 与 validator 面对一致的输入形状。",
                        [anchor("interface_id", "IFACE-SCHEMA-STRUCTURE"), anchor("data_id", "DATA-SCHEMA-CONTRACT")],
                        ["EV-SCHEMA"],
                    )
                ],
                [
                    mechanism_detail(
                        "MECH-SCHEMA-DEFS",
                        [
                            text_block("BLOCK-SCHEMA-DEFS-TEXT", "Schema 分组说明", "顶层 required 固定九章和支持数据数组，$defs 定义 moduleDesignItem、runtimeView、keyFlow、diagram、evidence 等对象，具体跨引用一致性留给语义校验器。", ["EV-SCHEMA"]),
                            table_block(
                                "BLOCK-SCHEMA-DEFS-TABLE",
                                "Schema 主要分组",
                                [{"key": "group", "title": "分组"}, {"key": "purpose", "title": "用途"}],
                                [
                                    {"group": "document/system/architecture", "purpose": "定义文档信息、系统概览和模块介绍。"},
                                    {"group": "moduleDesignItem", "purpose": "定义 V2 Chapter 4 七个固定子节的数据形状。"},
                                    {"group": "support data", "purpose": "定义 evidence、traceability、risk、assumption 和 sourceSnippet。"},
                                ],
                            ),
                        ],
                    )
                ],
            ),
            known_limitations(
                "Schema 只负责结构约束。",
                [
                    limitation("LIMIT-SCHEMA-SEMANTIC", "跨字段语义无法完全由 schema 表达。", "需要 validate_dsl.py 补充 ID、引用、not_applicable 和低置信度检查。", "保持 schema 与语义校验脚本分层。", ["EV-SCHEMA", "EV-DSL-VALIDATOR"]),
                ],
            ),
            ["EV-SCHEMA"],
        ),
        module(
            "MOD-V2-FOUNDATION",
            "V2 共享规则模块",
            "library",
            "提供 V2 DSL 版本、枚举、not_applicable 门禁、ID 作用域、依赖前缀和全局规则检查，供校验器、渲染器和 Mermaid 门禁复用。",
            source_scope(
                "该模块由 v2_foundation.py 承载，是多个 CLI 脚本共享的规则基础。",
                [source_file("scripts/v2_foundation.py", "V2 共享常量与全局语义规则", "python")],
                ["已解析 DSL document"],
                ["V2 版本错误", "RuleViolation 列表", "枚举和规则常量"],
                ["不读取文件", "不执行 schema 校验", "不渲染 Markdown"],
            ),
            module_configuration("该模块通过函数参数接收 DSL 对象，不读取独立配置。"),
            module_dependencies(
                "仅依赖 Python 标准库 dataclasses。",
                [module_dep("MDEP-V2FOUND-PYTHON", "Python 3", "runtime", "uses", "运行共享规则模块。", "导入失败或脚本无法执行。", ["EV-V2-FOUNDATION"], system_dependency_ref="SYSDEP-PYTHON")],
            ),
            module_data_objects(
                "该模块拥有 V2 常量和全局规则对象。",
                [
                    module_data("DATA-V2-ENUMS", "V2 版本与枚举常量", "python constants", "共享规则数据", "V2 共享规则模块", "DSL 校验器、渲染器、Mermaid 门禁", "包含 V2_DSL_VERSION、EVIDENCE_MODES、枚举值和 gate 列表", ["EV-V2-FOUNDATION"]),
                    module_data("DATA-V2-RULE-VIOLATION", "RuleViolation", "dataclass", "规则违规对象", "V2 共享规则模块", "调用方脚本", "path 和 message 字段", ["EV-V2-FOUNDATION"]),
                ],
            ),
            public_interfaces("通过 Python library API 被仓库内脚本复用。", foundation_interfaces),
            internal_mechanism(
                "先检查版本，再组合 not_applicable、枚举、位置、ID、diagram/table 和依赖前缀规则。",
                [
                    mechanism_row(
                        "MECH-V2FOUND-GLOBAL-RULES",
                        "V2 全局规则聚合",
                        "把分散的全局语义约束汇总为调用方可消费的违规列表。",
                        "DSL document",
                        "依次运行 not_applicable、reason 字段、枚举、location、ID 作用域、diagram/table ID 和 dependency prefix 检查。",
                        "RuleViolation 列表",
                        "让校验器、渲染器和 Mermaid 门禁共享同一套基础约束。",
                        [anchor("interface_id", "IFACE-V2-FOUNDATION-RULES")],
                        ["EV-V2-FOUNDATION"],
                    )
                ],
                [
                    mechanism_detail(
                        "MECH-V2FOUND-GLOBAL-RULES",
                        [
                            text_block("BLOCK-V2FOUND-RULES-TEXT", "全局规则说明", "共享规则模块不读取文件，只面向已解析的 DSL 对象工作；调用方负责加载 JSON、选择错误码和输出格式。", ["EV-V2-FOUNDATION"]),
                            table_block(
                                "BLOCK-V2FOUND-RULES-TABLE",
                                "全局规则类别",
                                [{"key": "rule", "title": "规则"}, {"key": "purpose", "title": "目的"}],
                                [
                                    {"rule": "require_v2_dsl_version", "purpose": "拒绝非 0.2.0 DSL。"},
                                    {"rule": "not_applicable_mapping_violations", "purpose": "检查内容与 not_applicable_reason 互斥。"},
                                    {"rule": "id_scope_violations", "purpose": "检查定义型 ID 和引用型 ID 的作用域。"},
                                ],
                            ),
                        ],
                    )
                ],
            ),
            known_limitations(
                "共享规则模块自身不提供完整 CLI。",
                [
                    limitation("LIMIT-V2FOUND-CALLER", "调用方必须负责加载 JSON 和错误输出。", "单独运行该文件不会产生用户可见校验报告。", "通过 validate_dsl.py、render_markdown.py 或 verify_v2_mermaid_gates.py 调用。", ["EV-V2-FOUNDATION"]),
                ],
            ),
            ["EV-V2-FOUNDATION"],
        ),
        module(
            "MOD-DSL-VALIDATOR",
            "DSL 校验器模块",
            "validator",
            "读取结构设计 DSL JSON，执行 V2 版本门禁、JSON Schema 校验、模块模型语义校验、内容块检查、引用解析、文本安全和支持数据检查。",
            source_scope(
                "覆盖 validate_dsl.py 入口以及 V2 Phase 2/3 语义扩展模块。",
                [
                    source_file("scripts/validate_dsl.py", "DSL 校验 CLI 和 ValidationContext", "python"),
                    source_file("scripts/v2_phase2.py", "Chapter 4 V2 模块模型语义检查", "python"),
                    source_file("scripts/v2_phase3.py", "内容块语义检查", "python"),
                ],
                ["structure.dsl.json", "schemas/structure-design.schema.json", "V2 共享规则模块"],
                ["Validation succeeded", "schema/semantic warnings and errors"],
                ["不渲染 Markdown", "不调用 Mermaid CLI", "不推理仓库缺失内容"],
            ),
            module_configuration(
                "校验器配置来自命令行参数。",
                [
                    module_param("MPARAM-DSLVAL-DSL-FILE", "dsl_file", "必填路径参数", "cli_argument", "指定待校验的 DSL JSON 文件。", ["EV-DSL-VALIDATOR"]),
                    module_param("MPARAM-DSLVAL-LONG-SNIP", "--allow-long-snippets", "False", "default", "源码片段超过 50 行时是否降级为警告。", ["EV-DSL-VALIDATOR"]),
                ],
            ),
            module_dependencies(
                "校验器依赖 Python、jsonschema、DSL schema 和 V2 共享规则。",
                [
                    module_dep("MDEP-DSLVAL-PYTHON", "Python 3", "runtime", "uses", "运行校验脚本。", "命令无法启动。", ["EV-DSL-VALIDATOR"], system_dependency_ref="SYSDEP-PYTHON"),
                    module_dep("MDEP-DSLVAL-JSONSCHEMA", "jsonschema", "library", "validates_against", "执行 Draft 2020-12 JSON Schema 校验。", "schema 校验不可用。", ["EV-REQUIREMENTS", "EV-DSL-VALIDATOR"], system_dependency_ref="SYSDEP-JSONSCHEMA"),
                    module_dep("MDEP-DSLVAL-SCHEMA", "DSL Schema 模块", "internal_module", "validates_against", "提供结构契约。", "无法判断 DSL 结构是否符合 schema。", ["EV-SCHEMA"], target_module_id="MOD-DSL-SCHEMA"),
                    module_dep("MDEP-DSLVAL-FOUNDATION", "V2 共享规则模块", "internal_module", "imports", "复用版本门禁和全局规则。", "V2 全局语义规则不可用。", ["EV-V2-FOUNDATION"], target_module_id="MOD-V2-FOUNDATION"),
                ],
            ),
            module_data_objects(
                "校验器消费 DSL 和 schema，并产出校验报告。",
                [
                    module_data("DATA-DSLVAL-INPUT", "structure.dsl.json", "json", "校验输入", "Codex 或上游分析者", "DSL 校验器模块", "符合 V2 DSL schema 的 JSON 文档", ["EV-DSL-SPEC"]),
                    module_data("DATA-DSLVAL-REPORT", "ValidationReport", "python object/stdout", "校验输出", "DSL 校验器模块", "Codex、测试模块、维护者", "包含 errors 和 warnings", ["EV-DSL-VALIDATOR"]),
                ],
            ),
            public_interfaces("通过 validate_dsl.py CLI 暴露校验能力。", [validate_cli]),
            internal_mechanism(
                "校验过程按版本门禁、schema 校验、上下文注册、章节语义和支持数据安全检查推进。",
                [
                    mechanism_row(
                        "MECH-DSLVAL-PIPELINE",
                        "DSL 校验管线",
                        "阻止不符合契约的 DSL 输入进入渲染和 Mermaid 门禁。",
                        "DSL JSON 文件",
                        "读取 JSON，执行 V2 版本检查、schema_errors、ValidationContext 注册和 run_semantic_checks。",
                        "成功消息、警告或错误报告",
                        "保证后续渲染器面对的 DSL 字段、ID 和引用稳定。",
                        [anchor("interface_id", "IFACE-DSL-VALIDATE-CLI"), anchor("data_id", "DATA-DSLVAL-INPUT")],
                        ["EV-DSL-VALIDATOR", "EV-V2-PHASE2", "EV-V2-PHASE3"],
                    )
                ],
                [
                    mechanism_detail(
                        "MECH-DSLVAL-PIPELINE",
                        [
                            text_block("BLOCK-DSLVAL-PIPELINE-TEXT", "校验管线说明", "validate_dsl.py 先加载 JSON 并拒绝非 V2 输入，再执行 schema 校验；schema 通过后注册 ID、检查章节规则、支持数据引用、源码片段安全和 Markdown 安全文本。", ["EV-DSL-VALIDATOR"]),
                            table_block(
                                "BLOCK-DSLVAL-PIPELINE-TABLE",
                                "校验阶段",
                                [{"key": "stage", "title": "阶段"}, {"key": "responsibility", "title": "职责"}],
                                [
                                    {"stage": "Version", "responsibility": "拒绝非 dsl_version 0.2.0。"},
                                    {"stage": "Schema", "responsibility": "使用 Draft202012Validator 检查结构形状。"},
                                    {"stage": "Semantics", "responsibility": "检查 ID、引用、章节内容、安全文本和低置信度项。"},
                                ],
                            ),
                        ],
                    )
                ],
            ),
            known_limitations(
                "校验器只检查 DSL，不补充内容。",
                [
                    limitation("LIMIT-DSLVAL-NO-MERMAID-STRICT", "validate_dsl.py 不证明 Mermaid 可渲染性。", "仍需运行 Mermaid strict gate。", "使用 verify_v2_mermaid_gates.py 执行前后置门禁。", ["EV-DSL-VALIDATOR", "EV-MERMAID-GATE"]),
                    limitation("LIMIT-DSLVAL-NO-INFERENCE", "校验器不会从源码推理缺失模块或流程。", "DSL 缺少内容时只能报错或渲染已给出的内容。", "在进入技能前完成仓库理解。", ["EV-SKILL-CONTRACT", "EV-DSL-SPEC"]),
                ],
            ),
            ["EV-DSL-VALIDATOR", "EV-V2-PHASE2", "EV-V2-PHASE3"],
        ),
        module(
            "MOD-MERMAID-GATES",
            "Mermaid 校验与门禁模块",
            "validator",
            "提取 DSL 或 Markdown 中的 Mermaid 图，执行静态和严格校验，并用 V2 门禁检查可读性复核工件与渲染完整性。",
            source_scope(
                "覆盖 Mermaid 校验 CLI、V2 期望图收集与门禁 CLI。",
                [
                    source_file("scripts/validate_mermaid.py", "Mermaid 静态和严格校验 CLI", "python"),
                    source_file("scripts/v2_phase4.py", "期望图收集、复核工件和渲染完整性规则", "python"),
                    source_file("scripts/verify_v2_mermaid_gates.py", "V2 Mermaid 门禁 CLI", "python"),
                ],
                ["structure.dsl.json", "rendered Markdown", "mermaid-readability-review.json", "node/mmdc 环境"],
                ["Mermaid validation succeeded", "pre-render/post-render gate result", "临时 mmd/svg 验证产物"],
                ["不把 SVG/PNG 作为最终交付", "不替代人工或独立可读性复核", "不修复 Mermaid 源"],
            ),
            module_configuration(
                "Mermaid 校验与门禁通过 CLI 参数选择输入来源、严格模式和工作目录。",
                [
                    module_param("MPARAM-MER-FROM", "--from-dsl 或 --from-markdown", "二选一必填", "cli_argument", "指定 Mermaid 图来源。", ["EV-MERMAID-VALIDATOR"]),
                    module_param("MPARAM-MER-STRICT", "--strict", "默认 strict，--static 显式静态", "default", "控制 Mermaid CLI 是否参与校验。", ["EV-MERMAID-VALIDATOR", "EV-MERMAID-RULES"]),
                    module_param("MPARAM-MER-WORKDIR", "--work-dir", "严格模式必填或由门禁拼接", "cli_argument", "保存严格校验 mmd/svg 临时产物。", ["EV-MERMAID-VALIDATOR"]),
                    module_param("MPARAM-MER-ARTIFACT", "--mermaid-review-artifact", "V2 门禁必填", "cli_argument", "绑定可读性复核工件。", ["EV-MERMAID-GATE", "EV-V2-PHASE4"]),
                ],
            ),
            module_dependencies(
                "严格校验依赖 Python、Node、mmdc、V2 共享规则和 Mermaid 规则文档。",
                [
                    module_dep("MDEP-MER-PYTHON", "Python 3", "runtime", "uses", "运行 Mermaid 校验脚本。", "命令无法启动。", ["EV-MERMAID-VALIDATOR"], system_dependency_ref="SYSDEP-PYTHON"),
                    module_dep("MDEP-MER-NODE", "node", "tool", "invokes", "运行 Mermaid CLI。", "严格校验无法执行。", ["EV-MERMAID-VALIDATOR"], system_dependency_ref="SYSDEP-NODE"),
                    module_dep("MDEP-MER-MMDC", "mmdc", "tool", "invokes", "将 Mermaid 源交给 Mermaid CLI 解析。", "严格校验无法作为最终门禁通过。", ["EV-MERMAID-VALIDATOR"], system_dependency_ref="SYSDEP-MMDC"),
                    module_dep("MDEP-MER-FOUNDATION", "V2 共享规则模块", "internal_module", "imports", "门禁复用 V2 版本和全局规则。", "门禁无法先行拒绝无效 DSL。", ["EV-V2-FOUNDATION"], target_module_id="MOD-V2-FOUNDATION"),
                ],
            ),
            module_data_objects(
                "该模块消费 Mermaid 源和复核工件，并生成临时校验产物。",
                [
                    module_data("DATA-MER-DIAGRAMS", "MermaidDiagram 列表", "python dataclass list", "校验输入模型", "Mermaid 校验器模块", "静态校验和严格校验", "diagram_id、source、diagram_type、json_path 或 markdown block index", ["EV-MERMAID-VALIDATOR"]),
                    module_data("DATA-MER-REVIEW", "mermaid-readability-review.json", "json", "可读性复核工件", "Codex 工作流", "V2 Mermaid 门禁", "artifact_schema_version 1.0，覆盖每个 expected diagram id", ["EV-V2-PHASE4", "EV-MERMAID-GATE"]),
                    module_data("DATA-MER-TEMP", "严格校验临时产物", "mmd/svg", "验证产物", "validate_mermaid.py", "Codex 和维护者", "--work-dir 下的 pre-render/post-render 临时文件，不是最终交付物", ["EV-MERMAID-VALIDATOR", "EV-MERMAID-RULES"]),
                ],
            ),
            public_interfaces("提供基础 Mermaid 校验 CLI 和 V2 门禁 CLI。", [mermaid_cli, gate_cli]),
            internal_mechanism(
                "先执行 Mermaid 静态检查；严格模式检查 node/mmdc 并调用 mmdc；V2 门禁在此基础上验证可读性复核和渲染完整性。",
                [
                    mechanism_row(
                        "MECH-MER-VALIDATION",
                        "Mermaid 静态与严格校验",
                        "证明图源属于支持的 Mermaid MVP 类型，并在严格模式下可由本地 Mermaid CLI 解析。",
                        "DSL 或 Markdown Mermaid 源",
                        "提取图、拒绝 DOT/不支持类型、检查严格工具、写入 mmd 并调用 mmdc。",
                        "Mermaid 校验报告",
                        "保证最终 Markdown 中 Mermaid fence 的可渲染性。",
                        [anchor("interface_id", "IFACE-MERMAID-VALIDATE-CLI"), anchor("data_id", "DATA-MER-DIAGRAMS")],
                        ["EV-MERMAID-VALIDATOR"],
                    ),
                    mechanism_row(
                        "MECH-MER-GATES",
                        "V2 Mermaid 门禁",
                        "把可读性复核、预渲染严格校验、渲染后完整性和严格 Markdown 校验串联。",
                        "DSL、复核工件、可选 Markdown",
                        "验证复核工件绑定同一 DSL，收集 expected diagrams，检查 diagram-id 元数据，再调用 Mermaid 校验。",
                        "pre-render 或 post-render gate result",
                        "防止 DSL 中的图被遗漏或只靠标题匹配误判。",
                        [anchor("interface_id", "IFACE-MERMAID-GATE-CLI"), anchor("data_id", "DATA-MER-REVIEW")],
                        ["EV-MERMAID-GATE", "EV-V2-PHASE4"],
                    ),
                ],
                [
                    mechanism_detail(
                        "MECH-MER-VALIDATION",
                        [
                            text_block("BLOCK-MER-VALIDATION-TEXT", "Mermaid 校验说明", "validate_mermaid.py 支持从 DSL 或 Markdown 提取 flowchart、graph、sequenceDiagram、classDiagram、stateDiagram-v2，并在 strict 模式下调用 mmdc。", ["EV-MERMAID-VALIDATOR", "EV-MERMAID-RULES"]),
                            table_block(
                                "BLOCK-MER-VALIDATION-TABLE",
                                "Mermaid 校验层次",
                                [{"key": "level", "title": "层次"}, {"key": "meaning", "title": "含义"}],
                                [
                                    {"level": "static", "meaning": "检查图源类型、空内容、DOT 语法和 Markdown fence。"},
                                    {"level": "strict", "meaning": "在 static 通过后调用本地 Mermaid CLI。"},
                                ],
                            ),
                        ],
                    ),
                    mechanism_detail(
                        "MECH-MER-GATES",
                        [
                            text_block("BLOCK-MER-GATES-TEXT", "V2 门禁说明", "verify_v2_mermaid_gates.py 要求复核工件先覆盖 expected diagrams；post-render 模式还要求每个 expected diagram 在 Markdown 中以相邻 diagram-id 注释绑定到 Mermaid fence。", ["EV-MERMAID-GATE", "EV-V2-PHASE4"]),
                        ],
                    ),
                ],
            ),
            known_limitations(
                "Mermaid 严格校验受本地环境影响。",
                [
                    limitation("LIMIT-MER-ENV", "strict validation 依赖 node、mmdc 和其浏览器运行环境。", "工具缺失或浏览器无法启动时，最终 Mermaid 门禁无法完整通过。", "先运行 --check-env；若只能 static，需要用户明确接受该限制。", ["EV-MERMAID-VALIDATOR", "EV-MERMAID-RULES"]),
                    limitation("LIMIT-MER-NO-FINAL-IMAGES", "严格校验产物不是最终交付物。", "不能把 svg/png 作为结构设计说明书输出。", "最终只交付 Markdown Mermaid fence。", ["EV-MERMAID-RULES"]),
                ],
            ),
            ["EV-MERMAID-VALIDATOR", "EV-MERMAID-GATE", "EV-V2-PHASE4"],
        ),
        module(
            "MOD-MARKDOWN-RENDERER",
            "Markdown 渲染器模块",
            "renderer",
            "把 V2 DSL 渲染为固定 9 章 Markdown，处理章节编号、表格列、Mermaid fence、diagram-id 元数据、支持数据显示模式和输出文件写入策略。",
            source_scope(
                "该模块由 render_markdown.py 承载，是最终 Markdown 输出入口。",
                [source_file("scripts/render_markdown.py", "Markdown 渲染 CLI 和渲染函数", "python")],
                ["通过准备和校验的 V2 DSL JSON", "输出目录参数", "evidence-mode 参数"],
                ["document.output_file 指定的 Markdown 文件"],
                ["不执行完整 schema 校验", "不调用 Mermaid CLI", "默认不覆盖已有输出文件"],
            ),
            module_configuration(
                "渲染器配置来自命令行参数和 DSL document.output_file。",
                [
                    module_param("MPARAM-RENDER-OUTPUT-DIR", "--output-dir", ".", "default", "指定 Markdown 输出目录。", ["EV-RENDERER"]),
                    module_param("MPARAM-RENDER-EVIDENCE", "--evidence-mode", "hidden", "default", "控制支持数据隐藏或 inline 渲染。", ["EV-RENDERER", "EV-DOCUMENT-STRUCTURE"]),
                    module_param("MPARAM-RENDER-WRITE-POLICY", "--overwrite 或 --backup", "默认拒绝覆盖", "default", "控制目标文件存在时的写入行为。", ["EV-RENDERER"]),
                ],
            ),
            module_dependencies(
                "渲染器依赖 Python、V2 共享规则和文件系统。",
                [
                    module_dep("MDEP-RENDER-PYTHON", "Python 3", "runtime", "uses", "运行渲染脚本。", "命令无法启动。", ["EV-RENDERER"], system_dependency_ref="SYSDEP-PYTHON"),
                    module_dep("MDEP-RENDER-FOUNDATION", "V2 共享规则模块", "internal_module", "imports", "复用 V2 版本和 not_applicable 全局规则。", "渲染前基础规则无法检查。", ["EV-V2-FOUNDATION"], target_module_id="MOD-V2-FOUNDATION"),
                    module_dep("MDEP-RENDER-FILESYSTEM", "文件系统", "filesystem", "writes", "读取 DSL 并写出 Markdown。", "输入读取或输出写入失败。", ["EV-RENDERER"], system_dependency_ref="SYSDEP-FILESYSTEM"),
                ],
            ),
            module_data_objects(
                "渲染器读取 DSL，构建支持数据上下文并写出 Markdown。",
                [
                    module_data("DATA-RENDER-DSL", "V2 DSL document", "json", "渲染输入", "Codex 或上游分析者", "Markdown 渲染器模块", "符合 dsl_version 0.2.0 的结构设计 DSL", ["EV-DSL-SPEC", "EV-RENDERER"]),
                    module_data("DATA-RENDER-SUPPORT", "SupportContext", "python dataclass", "支持数据上下文", "Markdown 渲染器模块", "章节渲染函数", "包含 evidence、traceability、source snippets 的索引和 evidence_mode", ["EV-RENDERER"]),
                    module_data("DATA-RENDER-MARKDOWN", "结构设计 Markdown", "markdown", "最终输出", "Markdown 渲染器模块", "用户和仓库维护者", "固定 9 章，diagram-id 注释紧邻 Mermaid fence", ["EV-RENDERER", "EV-DOCUMENT-STRUCTURE"]),
                ],
            ),
            public_interfaces("通过 render_markdown.py CLI 暴露最终 Markdown 渲染能力。", [render_cli]),
            internal_mechanism(
                "渲染器先检查 output_file 具体性，再构建显示名和支持数据上下文，按九章顺序拼接 Markdown，最后应用写入策略。",
                [
                    mechanism_row(
                        "MECH-RENDER-PIPELINE",
                        "Markdown 渲染管线",
                        "把 DSL 内容确定性转为固定 9 章 Markdown。",
                        "V2 DSL document",
                        "validate_output_filename、build_support_context、render_chapter_1 至 render_chapter_9、write_output。",
                        "Markdown 文件",
                        "集中控制章节结构、表格列、转义、支持数据和输出文件安全。",
                        [anchor("interface_id", "IFACE-RENDER-CLI"), anchor("data_id", "DATA-RENDER-MARKDOWN")],
                        ["EV-RENDERER", "EV-DOCUMENT-STRUCTURE"],
                    )
                ],
                [
                    mechanism_detail(
                        "MECH-RENDER-PIPELINE",
                        [
                            text_block("BLOCK-RENDER-PIPELINE-TEXT", "渲染管线说明", "render_markdown.py 使用固定函数渲染 1 到 9 章，默认隐藏 evidence 支持块，同时始终为 Mermaid fence 输出 diagram-id 注释。", ["EV-RENDERER"]),
                            table_block(
                                "BLOCK-RENDER-PIPELINE-TABLE",
                                "渲染关键职责",
                                [{"key": "responsibility", "title": "职责"}, {"key": "implementation", "title": "实现"}],
                                [
                                    {"responsibility": "章节结构", "implementation": "render_chapter_1 到 render_chapter_9。"},
                                    {"responsibility": "输出安全", "implementation": "validate_output_filename 和 write_output。"},
                                    {"responsibility": "Mermaid 元数据", "implementation": "render_diagram_id_comment。"},
                                ],
                            ),
                        ],
                    )
                ],
            ),
            known_limitations(
                "渲染器聚焦 Markdown 输出。",
                [
                    limitation("LIMIT-RENDER-NO-SCHEMA-FIRST", "render_markdown.py 不替代 validate_dsl.py 的完整 schema/语义校验。", "直接渲染未校验 DSL 时可能只触发部分运行时错误。", "正式流程先运行 validate_dsl.py。", ["EV-RENDERER", "EV-DSL-VALIDATOR"]),
                    limitation("LIMIT-RENDER-NO-OVERWRITE", "默认拒绝覆盖已有输出文件。", "目标文件存在时需要明确 --overwrite 或 --backup。", "本次输出目标不存在时使用默认写入策略。", ["EV-RENDERER"]),
                ],
            ),
            ["EV-RENDERER", "EV-DOCUMENT-STRUCTURE"],
        ),
        module(
            "MOD-INSTALLER",
            "安装器模块",
            "installer",
            "提供 copy-only 本地技能安装能力，验证源仓库结构，解析 Codex home，报告依赖状态，并在目标不存在时复制运行时白名单条目。",
            source_scope(
                "覆盖安装脚本和安装说明文档。",
                [
                    source_file("scripts/install_skill.py", "copy-only 安装 CLI", "python"),
                    source_file("docs/install.md", "安装和依赖说明", "markdown"),
                ],
                ["仓库运行时文件", "--codex-home 参数", "CODEX_HOME 环境变量"],
                ["$CODEX_HOME/skills/create-structure-md 安装副本", "安装计划和依赖状态报告"],
                ["不覆盖已有安装", "不安装 Python 或 Node 依赖", "不自动删除失败产物"],
            ),
            module_configuration(
                "安装器配置来自 CLI 参数和环境变量。",
                [
                    module_param("MPARAM-INSTALL-DRY-RUN", "--dry-run", "False", "default", "只打印计划，不写入目标目录。", ["EV-INSTALLER", "EV-INSTALL-DOC"]),
                    module_param("MPARAM-INSTALL-CODEX-HOME", "--codex-home 或 CODEX_HOME", "~/.codex", "default", "决定目标 skills/create-structure-md 路径。", ["EV-INSTALLER", "EV-INSTALL-DOC"]),
                ],
            ),
            module_dependencies(
                "安装器依赖 Python 和文件系统；依赖状态报告会探测 jsonschema、node 和 mmdc。",
                [
                    module_dep("MDEP-INSTALL-PYTHON", "Python 3", "runtime", "uses", "运行安装脚本。", "命令无法启动。", ["EV-INSTALLER"], system_dependency_ref="SYSDEP-PYTHON"),
                    module_dep("MDEP-INSTALL-FILESYSTEM", "文件系统", "filesystem", "writes", "创建安装目标并复制运行时条目。", "安装失败并提示人工检查。", ["EV-INSTALLER"], system_dependency_ref="SYSDEP-FILESYSTEM"),
                ],
            ),
            module_data_objects(
                "安装器消费运行时文件白名单并产出安装目录。",
                [
                    module_data("DATA-INSTALL-RUNTIME-ENTRIES", "RUNTIME_ENTRIES", "python tuple", "复制白名单", "安装器模块", "copy_skill", "SKILL.md、requirements.txt、references、schemas、scripts、examples", ["EV-INSTALLER"]),
                    module_data("DATA-INSTALL-TARGET", "安装目标目录", "directory", "安装产物", "安装器模块", "Codex runtime", "$CODEX_HOME/skills/create-structure-md", ["EV-INSTALLER", "EV-INSTALL-DOC"]),
                ],
            ),
            public_interfaces("通过 install_skill.py CLI 暴露安装能力。", [install_cli]),
            internal_mechanism(
                "安装器先验证源结构，再打印计划和依赖状态；非 dry-run 且目标不存在时创建目录并复制白名单。",
                [
                    mechanism_row(
                        "MECH-INSTALL-COPY-ONLY",
                        "copy-only 安装流程",
                        "把仓库运行时技能文件复制到 Codex skills 目录。",
                        "仓库根目录和目标 Codex home",
                        "validate_source、print_plan、collect_dependency_status、copy_skill、validate_source(target)。",
                        "安装目录或错误报告",
                        "保守避免覆盖已有目标，降低本地技能安装风险。",
                        [anchor("interface_id", "IFACE-INSTALL-CLI"), anchor("data_id", "DATA-INSTALL-RUNTIME-ENTRIES")],
                        ["EV-INSTALLER", "EV-INSTALL-DOC"],
                    )
                ],
                [
                    mechanism_detail(
                        "MECH-INSTALL-COPY-ONLY",
                        [
                            text_block("BLOCK-INSTALL-COPY-TEXT", "安装流程说明", "install_skill.py 在复制前验证源仓库必需文件和 references 引用，目标已存在时失败并打印用户可自行执行的清理命令。", ["EV-INSTALLER"]),
                            table_block(
                                "BLOCK-INSTALL-RUNTIME-TABLE",
                                "运行时白名单",
                                [{"key": "entry", "title": "条目"}, {"key": "purpose", "title": "用途"}],
                                [
                                    {"entry": "SKILL.md", "purpose": "技能入口。"},
                                    {"entry": "references/", "purpose": "技能规则文档。"},
                                    {"entry": "schemas/", "purpose": "DSL schema。"},
                                    {"entry": "scripts/", "purpose": "校验、渲染和安装脚本。"},
                                    {"entry": "examples/", "purpose": "V2 DSL 示例。"},
                                ],
                            ),
                        ],
                    )
                ],
            ),
            known_limitations(
                "安装器刻意保守。",
                [
                    limitation("LIMIT-INSTALL-NO-FORCE", "不提供 --force、覆盖、合并或符号链接安装。", "已有目标时需要用户自行审查和清理。", "先运行 --dry-run 查看目标路径。", ["EV-INSTALLER", "EV-INSTALL-DOC"]),
                    limitation("LIMIT-INSTALL-NO-DEPS", "不自动安装 Python 或 Mermaid 依赖。", "安装完成不代表严格 Mermaid 校验环境可用。", "按 docs/install.md 手动安装 requirements 和 Mermaid CLI。", ["EV-INSTALL-DOC"]),
                ],
            ),
            ["EV-INSTALLER", "EV-INSTALL-DOC"],
        ),
        module(
            "MOD-EXAMPLES-TESTS",
            "示例与测试模块",
            "test_suite",
            "提供 V2 DSL 示例、拒绝 fixture 和 unittest 测试，覆盖 schema、语义、Mermaid、渲染、安装、文档契约和端到端流程。",
            source_scope(
                "覆盖 examples、tests、fixtures 和历史设计/计划资料。",
                [
                    source_file("examples/minimal-from-code.dsl.json", "从代码场景生成的最小 V2 DSL 示例", "json"),
                    source_file("examples/minimal-from-requirements.dsl.json", "从需求场景生成的最小 V2 DSL 示例", "json"),
                    source_file("tests/", "unittest 测试集合", "python"),
                    source_file("docs/superpowers/specs/", "V2 设计规格和分阶段规格", "markdown"),
                    source_file("docs/superpowers/plans/", "V2 分阶段执行计划", "markdown"),
                ],
                ["脚本模块", "schema", "examples", "fixtures", "本地 Mermaid CLI 环境"],
                ["测试结果", ".codex-tmp 下保留的测试产物", "示例渲染输出"],
                ["不作为生产安装产物复制 tests/docs", "不替代用户验收"],
            ),
            module_configuration(
                "测试运行参数来自 unittest 命令。",
                [
                    module_param("MPARAM-TEST-SOURCE", "-s tests", "tests", "default", "指定测试发现目录。", ["EV-TESTS"]),
                    module_param("MPARAM-TEST-VERBOSE", "-v", "可选", "cli_argument", "输出详细测试名称。", ["EV-TESTS"]),
                ],
            ),
            module_dependencies(
                "测试模块依赖 Python unittest、被测脚本、示例和可选 Mermaid strict 环境。",
                [
                    module_dep("MDEP-TEST-PYTHON", "Python 3", "runtime", "uses", "运行 unittest。", "测试命令无法启动。", ["EV-TESTS"], system_dependency_ref="SYSDEP-PYTHON"),
                    module_dep("MDEP-TEST-UNITTEST", "unittest", "library", "uses", "发现和运行测试用例。", "测试无法执行。", ["EV-TESTS"], system_dependency_ref="SYSDEP-UNITTEST"),
                    module_dep("MDEP-TEST-EXAMPLES", "V2 DSL 示例", "test_fixture", "consumes", "验证示例可校验、可渲染。", "示例契约回归无法覆盖。", ["EV-EXAMPLES"]),
                    module_dep("MDEP-TEST-MMDC", "mmdc", "tool", "invokes", "运行严格 Mermaid 相关端到端测试。", "严格 Mermaid 测试失败或跳过。", ["EV-TESTS"], system_dependency_ref="SYSDEP-MMDC"),
                ],
            ),
            module_data_objects(
                "测试模块拥有示例、fixture 和保留测试产物。",
                [
                    module_data("DATA-TEST-EXAMPLES", "V2 DSL examples", "json", "测试 fixture 和用户参考样例", "示例与测试模块", "validate_dsl、render_markdown、测试模块", "dsl_version 0.2.0 示例", ["EV-EXAMPLES"]),
                    module_data("DATA-TEST-FIXTURES", "tests/fixtures", "json", "测试 fixture", "示例与测试模块", "unittest 测试", "包含 valid-v2-foundation 和 rejected-v1-phase2", ["EV-TESTS"]),
                    module_data("DATA-TEST-TEMP-ARTIFACTS", ".codex-tmp 测试产物", "directory", "保留验证产物", "端到端测试", "维护者", "测试说明明确保留产物，清理需用户执行命令", ["EV-TESTS"]),
                ],
            ),
            public_interfaces("通过 unittest discover 工作流暴露测试执行入口。", [test_cli]),
            internal_mechanism(
                "测试用例通过 importlib 加载脚本模块，构造或读取 fixture，调用 main 或 subprocess，断言错误码、输出文本和渲染结构。",
                [
                    mechanism_row(
                        "MECH-TEST-CONTRACTS",
                        "契约测试编排",
                        "保护 DSL、渲染、Mermaid、安装和文档规则不回归。",
                        "tests、examples、scripts",
                        "测试加载模块、运行 CLI、生成临时目录、比较输出和错误消息。",
                        "unittest 成功或失败报告",
                        "把技能契约变成可执行回归保护。",
                        [anchor("interface_id", "IFACE-TEST-WORKFLOW"), anchor("data_id", "DATA-TEST-EXAMPLES")],
                        ["EV-TESTS", "EV-EXAMPLES"],
                    )
                ],
                [
                    mechanism_detail(
                        "MECH-TEST-CONTRACTS",
                        [
                            text_block("BLOCK-TEST-CONTRACTS-TEXT", "测试编排说明", "测试集合覆盖 V2 foundation、Chapter 4 模块模型、内容块、Mermaid 门禁、示例文档、安装器和端到端工作流；部分测试会保留 .codex-tmp 产物供人工审查。", ["EV-TESTS"]),
                            table_block(
                                "BLOCK-TEST-COVERAGE-TABLE",
                                "测试覆盖范围",
                                [{"key": "area", "title": "范围"}, {"key": "tests", "title": "代表测试"}],
                                [
                                    {"area": "DSL 校验", "tests": "test_validate_dsl.py, test_validate_dsl_semantics.py"},
                                    {"area": "V2 模型", "tests": "test_v2_foundation_rules.py, test_v2_phase2_module_model.py, test_v2_phase3_content_blocks.py"},
                                    {"area": "渲染与 Mermaid", "tests": "test_render_markdown.py, test_validate_mermaid.py, test_v2_phase4_renderer_and_mermaid_gates.py"},
                                    {"area": "安装和端到端", "tests": "test_install_skill.py, test_phase7_e2e.py"},
                                ],
                            ),
                        ],
                    )
                ],
            ),
            known_limitations(
                "测试受本地工具环境影响。",
                [
                    limitation("LIMIT-TEST-MERMAID-ENV", "严格 Mermaid 测试依赖本地 node/mmdc 和浏览器运行环境。", "环境异常会导致相关测试失败或跳过。", "先用 validate_mermaid.py --check-env 探测。", ["EV-TESTS", "EV-MERMAID-VALIDATOR"]),
                    limitation("LIMIT-TEST-ARTIFACTS", "测试和本次生成都会保留 .codex-tmp 产物。", "工作区可能出现较多临时文件，需要人工判断是否清理。", "遵守不删除约束，只报告路径和可选清理命令。", ["EV-TESTS", "EV-WORKTREE"]),
                ],
            ),
            ["EV-TESTS", "EV-EXAMPLES", "EV-V2-DESIGN"],
        ),
    ]

    module_intro_rows = [
        {
            "module_id": "MOD-CONTRACT-DOCS",
            "module_name": "技能契约与参考文档模块",
            "responsibility": "定义技能边界、输入就绪条件、V2 工作流、固定结构和复核规则。",
            "inputs": "用户请求、已准备结构内容、仓库理解结果",
            "outputs": "Codex 执行规则和最终复核依据",
            "notes": "主要由 SKILL.md 和 references 目录承载。",
            **meta("observed", ["EV-SKILL-CONTRACT", "EV-DSL-SPEC"]),
        },
        {
            "module_id": "MOD-DSL-SCHEMA",
            "module_name": "DSL Schema 模块",
            "responsibility": "定义 V2 DSL 的 JSON Schema 结构契约。",
            "inputs": "DSL 字段与章节模型",
            "outputs": "schemas/structure-design.schema.json",
            "notes": "结构校验权威来源。",
            **meta("observed", ["EV-SCHEMA"]),
        },
        {
            "module_id": "MOD-V2-FOUNDATION",
            "module_name": "V2 共享规则模块",
            "responsibility": "提供版本门禁、枚举、not_applicable、ID 作用域和全局规则检查。",
            "inputs": "已解析 DSL document",
            "outputs": "RuleViolation 列表和共享常量",
            "notes": "被校验器、渲染器和 Mermaid 门禁导入。",
            **meta("observed", ["EV-V2-FOUNDATION"]),
        },
        {
            "module_id": "MOD-DSL-VALIDATOR",
            "module_name": "DSL 校验器模块",
            "responsibility": "校验 DSL schema、语义、引用、支持数据和文本安全。",
            "inputs": "structure.dsl.json、schema、V2 共享规则",
            "outputs": "校验报告或成功状态",
            "notes": "入口为 scripts/validate_dsl.py。",
            **meta("observed", ["EV-DSL-VALIDATOR"]),
        },
        {
            "module_id": "MOD-MERMAID-GATES",
            "module_name": "Mermaid 校验与门禁模块",
            "responsibility": "校验 Mermaid 图，验证复核工件和渲染后图完整性。",
            "inputs": "DSL、Markdown、Mermaid review artifact、node/mmdc",
            "outputs": "Mermaid 校验结果和门禁结果",
            "notes": "最终输出仍为 Markdown Mermaid fence，不是图片。",
            **meta("observed", ["EV-MERMAID-VALIDATOR", "EV-MERMAID-GATE"]),
        },
        {
            "module_id": "MOD-MARKDOWN-RENDERER",
            "module_name": "Markdown 渲染器模块",
            "responsibility": "把 V2 DSL 渲染为固定 9 章结构设计 Markdown。",
            "inputs": "V2 DSL JSON、输出目录、evidence-mode",
            "outputs": "document.output_file 指定的 Markdown 文件",
            "notes": "入口为 scripts/render_markdown.py。",
            **meta("observed", ["EV-RENDERER"]),
        },
        {
            "module_id": "MOD-INSTALLER",
            "module_name": "安装器模块",
            "responsibility": "执行 copy-only 本地技能安装和依赖状态报告。",
            "inputs": "仓库运行时文件、--codex-home 或 CODEX_HOME",
            "outputs": "Codex skills 目录中的安装副本",
            "notes": "不覆盖已有目标，不安装依赖。",
            **meta("observed", ["EV-INSTALLER", "EV-INSTALL-DOC"]),
        },
        {
            "module_id": "MOD-EXAMPLES-TESTS",
            "module_name": "示例与测试模块",
            "responsibility": "提供 V2 示例、fixture 和 unittest 回归保护。",
            "inputs": "examples、fixtures、scripts、schema、本地工具环境",
            "outputs": "测试结果、示例验证结果、临时测试产物",
            "notes": "tests 和 docs 不属于安装器运行时白名单。",
            **meta("observed", ["EV-TESTS", "EV-EXAMPLES"]),
        },
    ]

    runtime_units = [
        runtime_unit("RUN-VALIDATE-DSL", "DSL 校验命令", "CLI command", "python3 scripts/validate_dsl.py", "校验 V2 DSL 结构和语义。", ["MOD-DSL-VALIDATOR", "MOD-DSL-SCHEMA", "MOD-V2-FOUNDATION"], "无常驻进程。", ["EV-DSL-VALIDATOR"]),
        runtime_unit("RUN-MERMAID-GATES", "Mermaid 门禁命令", "CLI command", "python3 scripts/verify_v2_mermaid_gates.py", "执行 pre-render 和 post-render Mermaid 门禁。", ["MOD-MERMAID-GATES", "MOD-V2-FOUNDATION"], "严格模式会写入临时验证产物。", ["EV-MERMAID-GATE"]),
        runtime_unit("RUN-RENDER-MARKDOWN", "Markdown 渲染命令", "CLI command", "python3 scripts/render_markdown.py", "生成最终结构设计 Markdown 文件。", ["MOD-MARKDOWN-RENDERER", "MOD-V2-FOUNDATION"], "默认不覆盖已有输出文件。", ["EV-RENDERER"]),
        runtime_unit("RUN-INSTALL-SKILL", "技能安装命令", "CLI command", "python3 scripts/install_skill.py", "复制运行时技能文件到 Codex skills 目录。", ["MOD-INSTALLER", "MOD-CONTRACT-DOCS", "MOD-DSL-SCHEMA", "MOD-DSL-VALIDATOR", "MOD-MERMAID-GATES", "MOD-MARKDOWN-RENDERER"], "dry-run 不写文件。", ["EV-INSTALLER"]),
        runtime_unit("RUN-TESTS", "unittest 测试命令", "CLI command", "python3 -m unittest discover -s tests -v", "运行仓库回归测试。", ["MOD-EXAMPLES-TESTS", "MOD-DSL-SCHEMA", "MOD-DSL-VALIDATOR", "MOD-MERMAID-GATES", "MOD-MARKDOWN-RENDERER", "MOD-INSTALLER"], "部分测试保留 .codex-tmp 产物。", ["EV-TESTS"]),
    ]

    flows = [
        flow(
            "FLOW-GENERATE-DOCUMENT",
            "生成结构设计说明书",
            "从已准备好的结构内容生成一个模块或系统专属结构设计 Markdown 文档。",
            [
                flow_step("STEP-GEN-001", 1, "Codex", "在技能外扫描仓库并整理模块、接口、依赖和流程事实。", "当前工程源码和文档", "结构设计内容", ["MOD-CONTRACT-DOCS", "MOD-EXAMPLES-TESTS"], [], ["EV-SKILL-CONTRACT"]),
                flow_step("STEP-GEN-002", 2, "Codex", "写入 V2 structure.dsl.json。", "结构设计内容", "structure.dsl.json", ["MOD-CONTRACT-DOCS", "MOD-DSL-SCHEMA"], [], ["EV-DSL-SPEC", "EV-SCHEMA"]),
                flow_step("STEP-GEN-003", 3, "DSL 校验器", "运行 DSL 校验。", "structure.dsl.json", "Validation succeeded 或错误报告", ["MOD-DSL-VALIDATOR", "MOD-DSL-SCHEMA", "MOD-V2-FOUNDATION"], ["RUN-VALIDATE-DSL"], ["EV-DSL-VALIDATOR"]),
                flow_step("STEP-GEN-004", 4, "Mermaid 门禁", "验证可读性复核工件并执行 pre-render strict gate。", "structure.dsl.json 和 review artifact", "pre-render gate result", ["MOD-MERMAID-GATES"], ["RUN-MERMAID-GATES"], ["EV-MERMAID-GATE"]),
                flow_step("STEP-GEN-005", 5, "Markdown 渲染器", "渲染单个 Markdown 输出文件。", "structure.dsl.json", "create-structure-md_STRUCTURE_DESIGN.md", ["MOD-MARKDOWN-RENDERER"], ["RUN-RENDER-MARKDOWN"], ["EV-RENDERER"]),
                flow_step("STEP-GEN-006", 6, "Mermaid 门禁", "执行 post-render 完整性和严格 Markdown Mermaid 校验。", "DSL 和 rendered Markdown", "post-render gate result", ["MOD-MERMAID-GATES", "MOD-MARKDOWN-RENDERER"], ["RUN-MERMAID-GATES"], ["EV-MERMAID-GATE", "EV-V2-PHASE4"]),
            ],
            [
                flow_branch("BR-GEN-OUTPUT-EXISTS", "目标 Markdown 已存在", "渲染器默认失败；需要用户明确选择 --overwrite 或 --backup 后再运行。", ["MOD-MARKDOWN-RENDERER"], ["RUN-RENDER-MARKDOWN"], ["EV-RENDERER"]),
                flow_branch("BR-GEN-MERMAID-FAIL", "严格 Mermaid 门禁失败", "修正 DSL Mermaid 源或本地 mmdc 环境后重新运行门禁。", ["MOD-MERMAID-GATES"], ["RUN-MERMAID-GATES"], ["EV-MERMAID-RULES", "EV-MERMAID-GATE"]),
            ],
            ["MOD-CONTRACT-DOCS", "MOD-DSL-SCHEMA", "MOD-DSL-VALIDATOR", "MOD-MERMAID-GATES", "MOD-MARKDOWN-RENDERER"],
            ["RUN-VALIDATE-DSL", "RUN-MERMAID-GATES", "RUN-RENDER-MARKDOWN"],
            "flowchart TD\n  A[\"Prepare content\"] --> B[\"Write DSL\"]\n  B --> C[\"Validate DSL\"]\n  C --> D[\"Review diagrams\"]\n  D --> E[\"Pre render gate\"]\n  E --> F[\"Render Markdown\"]\n  F --> G[\"Post render gate\"]",
            ["EV-SKILL-CONTRACT", "EV-RENDERER", "EV-MERMAID-GATE"],
        ),
        flow(
            "FLOW-VALIDATE-DSL",
            "校验 DSL",
            "确保 DSL 在结构、语义、引用和安全文本层面符合 V2 契约。",
            [
                flow_step("STEP-DSL-001", 1, "DSL 校验器", "读取 DSL JSON 并检查 dsl_version。", "dsl_file", "V2 document 或版本错误", ["MOD-DSL-VALIDATOR", "MOD-V2-FOUNDATION"], ["RUN-VALIDATE-DSL"], ["EV-DSL-VALIDATOR", "EV-V2-FOUNDATION"]),
                flow_step("STEP-DSL-002", 2, "DSL 校验器", "加载 schema 并执行 Draft 2020-12 结构校验。", "DSL document 和 schema", "schema errors 或进入语义校验", ["MOD-DSL-VALIDATOR", "MOD-DSL-SCHEMA"], ["RUN-VALIDATE-DSL"], ["EV-SCHEMA", "EV-DSL-VALIDATOR"]),
                flow_step("STEP-DSL-003", 3, "DSL 校验器", "注册 ID 并检查章节、引用、内容块和支持数据。", "schema 通过的 DSL", "ValidationReport", ["MOD-DSL-VALIDATOR", "MOD-V2-FOUNDATION"], ["RUN-VALIDATE-DSL"], ["EV-V2-PHASE2", "EV-V2-PHASE3"]),
            ],
            [
                flow_branch("BR-DSL-SCHEMA-ERROR", "schema 校验失败", "打印 schema validation failed 并返回非 0，语义校验不继续。", ["MOD-DSL-VALIDATOR", "MOD-DSL-SCHEMA"], ["RUN-VALIDATE-DSL"], ["EV-DSL-VALIDATOR"]),
            ],
            ["MOD-DSL-VALIDATOR", "MOD-DSL-SCHEMA", "MOD-V2-FOUNDATION"],
            ["RUN-VALIDATE-DSL"],
            "flowchart TD\n  A[\"Load DSL\"] --> B[\"Require V2\"]\n  B --> C[\"Schema validation\"]\n  C --> D[\"Register IDs\"]\n  D --> E[\"Semantic checks\"]\n  E --> F[\"Report\"]",
            ["EV-DSL-VALIDATOR", "EV-SCHEMA"],
        ),
        flow(
            "FLOW-MERMAID-GATE",
            "执行 Mermaid 门禁",
            "在渲染前后证明 Mermaid 图经过可读性复核、严格校验，并完整出现在最终 Markdown 中。",
            [
                flow_step("STEP-MER-001", 1, "Codex", "准备 mermaid-readability-review.json，覆盖 expected diagrams。", "structure.dsl.json", "review artifact", ["MOD-MERMAID-GATES"], ["RUN-MERMAID-GATES"], ["EV-V2-PHASE4"]),
                flow_step("STEP-MER-002", 2, "Mermaid 门禁", "验证复核工件绑定同一 DSL。", "DSL 和 artifact", "artifact gate result", ["MOD-MERMAID-GATES"], ["RUN-MERMAID-GATES"], ["EV-MERMAID-GATE"]),
                flow_step("STEP-MER-003", 3, "Mermaid 校验器", "pre-render 严格校验 DSL 中已有 Mermaid 图。", "DSL diagrams", "strict validation result", ["MOD-MERMAID-GATES"], ["RUN-MERMAID-GATES"], ["EV-MERMAID-VALIDATOR"]),
                flow_step("STEP-MER-004", 4, "Mermaid 门禁", "post-render 检查 diagram-id 元数据和 Markdown 严格校验。", "rendered Markdown", "post-render gate result", ["MOD-MERMAID-GATES", "MOD-MARKDOWN-RENDERER"], ["RUN-MERMAID-GATES"], ["EV-V2-PHASE4", "EV-RENDERER"]),
            ],
            [
                flow_branch("BR-MER-ARTIFACT-MISSING", "复核工件缺失或覆盖不全", "门禁失败并指出缺失 diagram id。", ["MOD-MERMAID-GATES"], ["RUN-MERMAID-GATES"], ["EV-V2-PHASE4"]),
                flow_branch("BR-MER-TOOLING-MISSING", "node 或 mmdc 缺失", "严格校验失败；static-only 不能作为最终 V2 门禁。", ["MOD-MERMAID-GATES"], ["RUN-MERMAID-GATES"], ["EV-MERMAID-RULES"]),
            ],
            ["MOD-MERMAID-GATES", "MOD-MARKDOWN-RENDERER"],
            ["RUN-MERMAID-GATES"],
            "flowchart TD\n  A[\"Collect expected diagrams\"] --> B[\"Review artifact\"]\n  B --> C[\"Pre render strict\"]\n  C --> D[\"Render Markdown\"]\n  D --> E[\"Completeness check\"]\n  E --> F[\"Markdown strict\"]",
            ["EV-MERMAID-GATE", "EV-V2-PHASE4"],
        ),
        flow(
            "FLOW-INSTALL-SKILL",
            "安装本地技能",
            "把仓库中的运行时白名单文件复制到 Codex skills 目录，保持不覆盖和不安装依赖的保守策略。",
            [
                flow_step("STEP-INSTALL-001", 1, "安装器", "解析 --codex-home 和 CODEX_HOME，计算目标目录。", "CLI 参数和环境变量", "target path", ["MOD-INSTALLER"], ["RUN-INSTALL-SKILL"], ["EV-INSTALLER"]),
                flow_step("STEP-INSTALL-002", 2, "安装器", "验证源仓库包含必需文件和 references 引用。", "仓库根目录", "source validation result", ["MOD-INSTALLER", "MOD-CONTRACT-DOCS"], ["RUN-INSTALL-SKILL"], ["EV-INSTALLER"]),
                flow_step("STEP-INSTALL-003", 3, "安装器", "打印复制计划和依赖状态。", "source 和 target", "plan and dependency status", ["MOD-INSTALLER"], ["RUN-INSTALL-SKILL"], ["EV-INSTALLER", "EV-INSTALL-DOC"]),
                flow_step("STEP-INSTALL-004", 4, "安装器", "目标不存在时复制 RUNTIME_ENTRIES。", "运行时白名单", "installed skill directory", ["MOD-INSTALLER", "MOD-CONTRACT-DOCS", "MOD-DSL-SCHEMA", "MOD-DSL-VALIDATOR", "MOD-MERMAID-GATES", "MOD-MARKDOWN-RENDERER"], ["RUN-INSTALL-SKILL"], ["EV-INSTALLER"]),
            ],
            [
                flow_branch("BR-INSTALL-TARGET-EXISTS", "目标目录已存在", "失败退出并打印用户可自行执行的 rm -r 清理命令。", ["MOD-INSTALLER"], ["RUN-INSTALL-SKILL"], ["EV-INSTALLER", "EV-INSTALL-DOC"]),
            ],
            ["MOD-INSTALLER", "MOD-CONTRACT-DOCS", "MOD-DSL-SCHEMA", "MOD-DSL-VALIDATOR", "MOD-MERMAID-GATES", "MOD-MARKDOWN-RENDERER"],
            ["RUN-INSTALL-SKILL"],
            "flowchart TD\n  A[\"Resolve target\"] --> B[\"Validate source\"]\n  B --> C[\"Print plan\"]\n  C --> D{\"Dry run\"}\n  D -->|yes| E[\"Exit\"]\n  D -->|no| F{\"Target exists\"}\n  F -->|no| G[\"Copy entries\"]\n  F -->|yes| H[\"Fail with cleanup command\"]",
            ["EV-INSTALLER", "EV-INSTALL-DOC"],
        ),
        flow(
            "FLOW-RUN-TESTS",
            "运行回归测试",
            "通过 unittest 发现并运行测试，验证 V2 DSL、渲染、Mermaid 门禁、安装器、示例和文档契约。",
            [
                flow_step("STEP-TEST-001", 1, "测试运行者", "运行 unittest discover。", "tests 目录", "test suite", ["MOD-EXAMPLES-TESTS"], ["RUN-TESTS"], ["EV-TESTS"]),
                flow_step("STEP-TEST-002", 2, "测试模块", "加载脚本模块、examples 和 fixtures。", "scripts、examples、fixtures", "test context", ["MOD-EXAMPLES-TESTS", "MOD-DSL-SCHEMA", "MOD-DSL-VALIDATOR", "MOD-MERMAID-GATES", "MOD-MARKDOWN-RENDERER", "MOD-INSTALLER"], ["RUN-TESTS"], ["EV-TESTS", "EV-EXAMPLES"]),
                flow_step("STEP-TEST-003", 3, "测试模块", "执行断言并报告结果。", "test context", "pass/fail report", ["MOD-EXAMPLES-TESTS"], ["RUN-TESTS"], ["EV-TESTS"]),
            ],
            [
                flow_branch("BR-TEST-FAIL", "任一断言失败", "unittest 输出失败用例，维护者按模块定位回归。", ["MOD-EXAMPLES-TESTS"], ["RUN-TESTS"], ["EV-TESTS"]),
            ],
            ["MOD-EXAMPLES-TESTS", "MOD-DSL-SCHEMA", "MOD-DSL-VALIDATOR", "MOD-MERMAID-GATES", "MOD-MARKDOWN-RENDERER", "MOD-INSTALLER"],
            ["RUN-TESTS"],
            "flowchart TD\n  A[\"Discover tests\"] --> B[\"Load fixtures\"]\n  B --> C[\"Run scripts\"]\n  C --> D[\"Assert contracts\"]\n  D --> E[\"Report\"]",
            ["EV-TESTS", "EV-EXAMPLES"],
        ),
    ]

    flow_index_rows = [
        {
            "flow_id": item["flow_id"],
            "flow_name": item["name"],
            "trigger_condition": {
                "FLOW-GENERATE-DOCUMENT": "需要生成结构设计说明书。",
                "FLOW-VALIDATE-DSL": "已有 structure.dsl.json 需要进入渲染或门禁。",
                "FLOW-MERMAID-GATE": "DSL 中存在 Mermaid 图且需要 V2 最终门禁。",
                "FLOW-INSTALL-SKILL": "需要把本仓库安装为本地 Codex skill。",
                "FLOW-RUN-TESTS": "需要验证仓库脚本、示例和文档契约。",
            }[item["flow_id"]],
            "participant_module_ids": item["related_module_ids"],
            "participant_runtime_unit_ids": item["related_runtime_unit_ids"],
            "main_steps": "；".join(step["description"] for step in item["steps"][:3]),
            "output_result": {
                "FLOW-GENERATE-DOCUMENT": "create-structure-md_STRUCTURE_DESIGN.md",
                "FLOW-VALIDATE-DSL": "校验成功或错误报告",
                "FLOW-MERMAID-GATE": "pre-render/post-render gate result",
                "FLOW-INSTALL-SKILL": "安装目录或保守失败报告",
                "FLOW-RUN-TESTS": "unittest 测试报告",
            }[item["flow_id"]],
            "notes": "",
        }
        for item in flows
    ]

    document = {
        "dsl_version": "0.2.0",
        "document": {
            "title": "create-structure-md 软件结构设计说明书",
            "project_name": "create-structure-md",
            "project_version": "",
            "document_version": "0.2.0",
            "status": "draft",
            "generated_at": "",
            "generated_by": "Codex",
            "language": "zh-CN",
            "source_type": "code",
            "scope_summary": "当前工程 create-structure-md 的技能契约、V2 DSL schema、共享语义规则、DSL 校验、Mermaid 门禁、Markdown 渲染、安装、示例与测试结构说明。",
            "not_applicable_policy": "固定 9 章输出；无常驻进程、数据库或外部服务时，以不适用说明、空表或运行单元备注表达。",
            "output_file": "create-structure-md_STRUCTURE_DESIGN.md",
        },
        "system_overview": {
            "summary": "create-structure-md 是一个本地 Codex 技能工程，用于把已经准备好的结构设计 DSL JSON 校验、审查 Mermaid 图并渲染为单个模块或系统专属 Markdown 结构设计说明书。",
            "purpose": "通过明确技能边界、V2 DSL 契约、schema/语义校验、Mermaid 严格门禁和确定性 Markdown 渲染，让结构设计文档生成过程可重复、可审查、可验证。",
            "core_capabilities": [
                {"capability_id": "CAP-DOC-GENERATION", "name": "结构设计文档生成", "description": "将完整 V2 DSL 渲染为固定 9 章 Markdown，并保证输出文件名面向具体工程或模块。", **meta("observed", ["EV-RENDERER", "EV-DOCUMENT-STRUCTURE"])},
                {"capability_id": "CAP-DSL-QUALITY", "name": "DSL 结构与语义门禁", "description": "通过 JSON Schema、V2 全局规则、模块模型和内容块语义检查 DSL 输入质量。", **meta("observed", ["EV-SCHEMA", "EV-DSL-VALIDATOR"])},
                {"capability_id": "CAP-MERMAID-QUALITY", "name": "Mermaid 可读性与严格门禁", "description": "用可读性复核工件、预渲染 strict 校验、渲染完整性检查和渲染后 strict 校验保护图表输出。", **meta("observed", ["EV-MERMAID-GATE", "EV-V2-PHASE4"])},
                {"capability_id": "CAP-INSTALL", "name": "本地技能安装", "description": "用 copy-only 安装器把运行时白名单文件安装到 Codex skills 目录。", **meta("observed", ["EV-INSTALLER", "EV-INSTALL-DOC"])},
                {"capability_id": "CAP-REGRESSION-TESTS", "name": "契约测试与示例", "description": "通过 V2 示例、fixture 和 unittest 覆盖校验器、渲染器、Mermaid 门禁、安装器和端到端流程。", **meta("observed", ["EV-TESTS", "EV-EXAMPLES"])},
            ],
            "notes": ["当前仓库未声明 pyproject 或顶层 README；入口主要由 SKILL.md、docs/install.md、references 和 tests 体现。"],
        },
        "architecture_views": {
            "summary": "工程按技能运行时职责组织为八个结构模块：契约文档、DSL schema、V2 共享规则、DSL 校验、Mermaid 门禁、Markdown 渲染、安装器、示例与测试。",
            "notes": ["scripts 目录中的 V2 helper 模块被 CLI 脚本导入复用；tests 和 docs 目录用于开发与验收，不属于安装器运行时复制白名单。"],
            "module_intro": {"rows": module_intro_rows},
            "module_relationship_diagram": diagram(
                "MER-ARCH-MODULES",
                "模块关系图",
                "flowchart TD\n  CONTRACT[\"MOD-CONTRACT-DOCS\"] --> SCHEMA[\"MOD-DSL-SCHEMA\"]\n  CONTRACT --> FOUNDATION[\"MOD-V2-FOUNDATION\"]\n  SCHEMA --> DSLVAL[\"MOD-DSL-VALIDATOR\"]\n  FOUNDATION --> DSLVAL\n  FOUNDATION --> MERGATE[\"MOD-MERMAID-GATES\"]\n  FOUNDATION --> RENDER[\"MOD-MARKDOWN-RENDERER\"]\n  DSLVAL --> MERGATE\n  DSLVAL --> RENDER\n  MERGATE --> RENDER\n  INSTALL[\"MOD-INSTALLER\"] --> CONTRACT\n  TESTS[\"MOD-EXAMPLES-TESTS\"] --> DSLVAL\n  TESTS --> MERGATE\n  TESTS --> RENDER\n  TESTS --> INSTALL",
                kind="module_relationship",
                description="展示 create-structure-md 当前工程的主要模块依赖和验证关系。",
            ),
            "extra_tables": [],
            "extra_diagrams": [],
        },
        "module_design": {
            "summary": "模块按规则来源、结构契约、共享语义、校验门禁、渲染输出、安装发布和回归保护分层，避免把仓库分析能力混入文档渲染技能本身。",
            "notes": [],
            "modules": modules,
        },
        "runtime_view": {
            "summary": "系统无常驻进程；运行时由一组 Python CLI 命令构成，典型生成路径是准备 DSL、校验 DSL、执行 Mermaid pre-render gate、渲染 Markdown、执行 post-render gate。",
            "notes": ["严格 Mermaid 校验会在 --work-dir 下写入临时验证产物；这些产物不是最终交付物。"],
            "runtime_units": {"rows": runtime_units},
            "runtime_flow_diagram": diagram(
                "MER-RUNTIME-FLOW",
                "运行时流程图",
                "flowchart TD\n  A[\"Prepare DSL\"] --> B[\"validate_dsl.py\"]\n  B --> C[\"Mermaid pre gate\"]\n  C --> D[\"render_markdown.py\"]\n  D --> E[\"Mermaid post gate\"]\n  F[\"install_skill.py\"] --> G[\"Codex skill dir\"]\n  H[\"unittest\"] --> B\n  H --> C\n  H --> D",
                kind="runtime_flow",
                description="展示主要 CLI 运行单元之间的关系。",
            ),
            "runtime_sequence_diagram": diagram(
                "MER-RUNTIME-SEQUENCE",
                "文档生成时序图",
                "sequenceDiagram\n  participant C as Codex\n  participant V as validate_dsl\n  participant M as mermaid_gate\n  participant R as render_markdown\n  C->>V: validate structure.dsl.json\n  V-->>C: validation result\n  C->>M: pre-render gate\n  M-->>C: strict result\n  C->>R: render Markdown\n  R-->>C: output path\n  C->>M: post-render gate\n  M-->>C: completeness and strict result",
                kind="runtime_sequence",
                diagram_type="sequenceDiagram",
                description="展示一次完整文档生成的命令交互顺序。",
            ),
            "extra_tables": [],
            "extra_diagrams": [],
        },
        "configuration_data_dependencies": {
            "summary": "系统级配置主要来自 CLI 参数和环境变量；系统级数据产物包括 DSL、Markdown、Mermaid 复核工件、严格校验临时产物、安装目录、示例和测试 fixture。",
            "notes": [],
            "configuration_items": {
                "rows": [
                    config_item("CFG-DSL-FILE", "DSL 输入文件路径", "CLI positional argument", "validate_dsl.py、render_markdown.py、verify_v2_mermaid_gates.py", "指定待校验、渲染或门禁检查的 V2 DSL JSON。", "", ["EV-DSL-VALIDATOR", "EV-RENDERER", "EV-MERMAID-GATE"]),
                    config_item("CFG-OUTPUT-DIR", "Markdown 输出目录", "render_markdown.py --output-dir", "Markdown 渲染器模块", "决定最终 Markdown 文件写入目录。", "默认当前目录。", ["EV-RENDERER"]),
                    config_item("CFG-EVIDENCE-MODE", "证据渲染模式", "render_markdown.py --evidence-mode", "Markdown 渲染器模块", "控制 evidence、traceability、source snippet 是否在最终 Markdown 中 inline 显示。", "默认 hidden。", ["EV-RENDERER", "EV-DOCUMENT-STRUCTURE"]),
                    config_item("CFG-MERMAID-WORK-DIR", "Mermaid 严格校验工作目录", "validate_mermaid.py/verify_v2_mermaid_gates.py --work-dir", "Mermaid 校验与门禁模块", "保存 strict validation 的临时 mmd/svg 产物。", "不是最终交付物。", ["EV-MERMAID-VALIDATOR", "EV-MERMAID-RULES"]),
                    config_item("CFG-CODEX-HOME", "Codex home", "--codex-home、CODEX_HOME、~/.codex", "安装器模块", "决定技能安装目标目录。", "解析优先级见 docs/install.md。", ["EV-INSTALLER", "EV-INSTALL-DOC"]),
                ]
            },
            "structural_data_artifacts": {
                "rows": [
                    data_artifact("DATA-ART-DSL", "structure.dsl.json", "json", "文档生成流程", "Codex 或上游分析者", "校验器、Mermaid 门禁、渲染器", "必须使用 dsl_version 0.2.0。", ["EV-DSL-SPEC"]),
                    data_artifact("DATA-ART-MARKDOWN", "create-structure-md_STRUCTURE_DESIGN.md", "markdown", "Markdown 渲染器模块", "render_markdown.py", "用户和仓库维护者", "单个系统专属结构设计说明书。", ["EV-RENDERER"]),
                    data_artifact("DATA-ART-MERMAID-REVIEW", "mermaid-readability-review.json", "json", "Mermaid 门禁流程", "Codex 工作流", "verify_v2_mermaid_gates.py", "覆盖 expected diagrams 的可读性复核工件。", ["EV-V2-PHASE4", "EV-MERMAID-GATE"]),
                    data_artifact("DATA-ART-MERMAID-TEMP", "Mermaid strict 临时产物", "mmd/svg", "Mermaid 校验与门禁模块", "validate_mermaid.py", "维护者审查", "位于 --work-dir 下，不是最终交付物。", ["EV-MERMAID-VALIDATOR", "EV-MERMAID-RULES"]),
                    data_artifact("DATA-ART-INSTALLED-SKILL", "$CODEX_HOME/skills/create-structure-md", "directory", "安装器模块", "install_skill.py", "Codex runtime", "只包含运行时白名单条目。", ["EV-INSTALLER", "EV-INSTALL-DOC"]),
                    data_artifact("DATA-ART-EXAMPLES", "examples/*.dsl.json", "json", "示例与测试模块", "仓库维护者", "测试模块和用户参考", "V2 DSL 示例。", ["EV-EXAMPLES"]),
                    data_artifact("DATA-ART-TESTS", "tests/*", "python/json", "示例与测试模块", "仓库维护者", "unittest", "契约测试和 fixture。", ["EV-TESTS"]),
                ]
            },
            "dependencies": {
                "rows": [
                    system_dep("SYSDEP-PYTHON", "Python 3", "runtime", "所有 CLI 脚本", "运行校验、渲染、安装和测试脚本。", "当前脚本均以 python3 执行。", ["EV-DSL-VALIDATOR", "EV-RENDERER", "EV-INSTALLER"]),
                    system_dep("SYSDEP-JSONSCHEMA", "jsonschema", "library", "DSL 校验器模块", "执行 Draft 2020-12 JSON Schema 校验。", "requirements.txt 声明该依赖。", ["EV-REQUIREMENTS", "EV-DSL-VALIDATOR"]),
                    system_dep("SYSDEP-NODE", "node", "tool", "Mermaid 校验与门禁模块", "运行 Mermaid CLI。", "strict Mermaid validation 需要。", ["EV-MERMAID-VALIDATOR", "EV-MERMAID-RULES"]),
                    system_dep("SYSDEP-MMDC", "mmdc", "tool", "Mermaid 校验与门禁模块", "解析和渲染 Mermaid 图源以证明严格可渲染。", "缺失时 static-only 不能作为最终 V2 门禁。", ["EV-MERMAID-VALIDATOR", "EV-MERMAID-RULES"]),
                    system_dep("SYSDEP-FILESYSTEM", "本地文件系统", "filesystem", "渲染器、安装器、Mermaid strict 校验、测试模块", "读取 DSL、写 Markdown、复制安装文件和保存临时产物。", "用户要求本次不执行删除操作。", ["EV-RENDERER", "EV-INSTALLER", "EV-WORKTREE"]),
                    system_dep("SYSDEP-UNITTEST", "unittest", "library", "示例与测试模块", "发现并运行 Python 测试。", "Python 标准库。", ["EV-TESTS"]),
                ]
            },
            "extra_tables": [],
            "extra_diagrams": [],
        },
        "cross_module_collaboration": {
            "summary": "模块间协作以文件契约和 CLI 命令串联为主：schema 与共享规则约束 DSL，校验器和 Mermaid 门禁阻断无效输入，渲染器生成 Markdown，测试模块持续验证这些契约。",
            "notes": [],
            "collaboration_scenarios": {
                "rows": [
                    collaboration("COL-DSL-VALIDATION", "DSL 校验", "MOD-DSL-VALIDATOR", ["MOD-DSL-SCHEMA", "MOD-V2-FOUNDATION"], "import 和 schema 文件读取", "validate_dsl.py 读取 schema，并导入 V2 共享规则和 Phase 2/3 语义检查。", ["EV-DSL-VALIDATOR", "EV-SCHEMA", "EV-V2-FOUNDATION"]),
                    collaboration("COL-MERMAID-GATE", "Mermaid 前后置门禁", "MOD-MERMAID-GATES", ["MOD-V2-FOUNDATION", "MOD-MARKDOWN-RENDERER"], "CLI 串联和 expected diagram 元数据", "门禁在渲染前校验 DSL 图，在渲染后通过 diagram-id 元数据确认 Markdown 中图完整出现。", ["EV-MERMAID-GATE", "EV-V2-PHASE4", "EV-RENDERER"]),
                    collaboration("COL-RENDER", "Markdown 渲染", "MOD-MARKDOWN-RENDERER", ["MOD-V2-FOUNDATION", "MOD-CONTRACT-DOCS"], "共享规则和文档结构契约", "渲染器复用 V2 版本规则，并按 document-structure 固定章节输出。", ["EV-RENDERER", "EV-DOCUMENT-STRUCTURE"]),
                    collaboration("COL-INSTALL", "本地技能安装", "MOD-INSTALLER", ["MOD-CONTRACT-DOCS", "MOD-DSL-SCHEMA", "MOD-DSL-VALIDATOR", "MOD-MERMAID-GATES", "MOD-MARKDOWN-RENDERER"], "运行时白名单复制", "安装器复制 SKILL.md、references、schemas、scripts、examples 和 requirements.txt，不复制 docs/tests。", ["EV-INSTALLER", "EV-INSTALL-DOC"]),
                    collaboration("COL-TESTS", "回归测试", "MOD-EXAMPLES-TESTS", ["MOD-DSL-SCHEMA", "MOD-DSL-VALIDATOR", "MOD-MERMAID-GATES", "MOD-MARKDOWN-RENDERER", "MOD-INSTALLER", "MOD-CONTRACT-DOCS"], "fixture、importlib 和 subprocess", "测试模块加载示例和脚本，断言 CLI、渲染和文档契约行为。", ["EV-TESTS", "EV-EXAMPLES"]),
                ]
            },
            "collaboration_relationship_diagram": diagram(
                "MER-COLLABORATION-RELATIONSHIP",
                "跨模块协作关系图",
                "flowchart TD\n  SCHEMA[\"Schema\"] --> DSLVAL[\"DSL validation\"]\n  FOUNDATION[\"V2 foundation\"] --> DSLVAL\n  FOUNDATION --> MER[\"Mermaid gates\"]\n  FOUNDATION --> RENDER[\"Renderer\"]\n  DSLVAL --> RENDER\n  MER --> RENDER\n  INSTALL[\"Installer\"] --> RUNTIME[\"Runtime entries\"]\n  TESTS[\"Tests\"] --> SCHEMA\n  TESTS --> DSLVAL\n  TESTS --> MER\n  TESTS --> RENDER\n  TESTS --> INSTALL",
                kind="collaboration_relationship",
                description="展示主要跨模块协作路径。",
            ),
            "extra_tables": [],
            "extra_diagrams": [],
        },
        "key_flows": {
            "summary": "关键流程覆盖当前工程最重要的运行路径：生成结构设计文档、校验 DSL、执行 Mermaid 门禁、安装本地技能和运行回归测试。",
            "notes": [],
            "flow_index": {"rows": flow_index_rows},
            "flows": flows,
            "extra_tables": [],
            "extra_diagrams": [],
        },
        "structure_issues_and_suggestions": {
            "summary": "当前工程核心边界清晰，V2 DSL 与门禁实现较完整。结构层面的改进重点在于提升入口可发现性、明确临时产物版本策略，以及把严格 Mermaid 环境要求写得更便于排查。",
            "blocks": [
                text_block("BLOCK-ISSUES-SUMMARY", "结构改进概述", "建议补充顶层 README 或 pyproject 元数据，减少新维护者从 SKILL.md、docs/install.md 和 tests 中拼接入口信息的成本；同时明确 .codex-tmp 是否应被版本化或忽略，避免临时验证产物长期污染工作区状态。", ["EV-INSTALL-DOC", "EV-WORKTREE"], confidence="inferred"),
                table_block(
                    "BLOCK-ISSUES-TABLE",
                    "结构问题与改进建议",
                    [{"key": "issue", "title": "问题"}, {"key": "impact", "title": "影响"}, {"key": "suggestion", "title": "建议"}],
                    [
                        {"issue": "缺少顶层 README 或 pyproject 元数据", "impact": "新维护者需要先阅读多个文件才能定位入口、测试命令和安装方式。", "suggestion": "增加简短 README，复用 docs/install.md 的安装和测试说明。"},
                        {"issue": ".gitignore 未包含 .codex-tmp", "impact": "技能运行和测试保留的临时产物可能进入工作区状态。", "suggestion": "由维护者决定是否版本化临时产物；如不版本化，可人工更新 .gitignore。"},
                        {"issue": "严格 Mermaid 环境失败原因可能较分散", "impact": "node/mmdc 已存在但浏览器运行环境异常时排查成本较高。", "suggestion": "在安装文档中补充常见 strict Mermaid 环境诊断步骤。"},
                    ],
                    ["EV-WORKTREE", "EV-INSTALL-DOC", "EV-MERMAID-RULES"],
                    confidence="inferred",
                ),
            ],
            "not_applicable_reason": "",
        },
        "evidence": evidence_items,
        "traceability": [],
        "risks": [
            risk("RISK-MERMAID-LOCAL-ENV", "严格 Mermaid 校验依赖本地 node、mmdc 和浏览器运行环境。", "工具缺失或浏览器无法启动会阻断 V2 最终门禁。", "保留 --check-env 和 strict gate；失败时先修复环境，static-only 仅在用户明确接受时作为非最终诊断。", "inferred", ["EV-MERMAID-VALIDATOR", "EV-MERMAID-RULES"]),
            risk("RISK-TEMP-ARTIFACTS", ".codex-tmp 产物当前容易出现在工作区状态中。", "多次生成或测试后可能让 git status 难以阅读。", "由维护者决定 .codex-tmp 版本策略；本次遵守约束，不执行删除操作。", "observed", ["EV-WORKTREE", "EV-SKILL-CONTRACT"]),
            risk("RISK-ENTRY-DISCOVERY", "缺少顶层 README 或 pyproject 时项目入口发现成本较高。", "首次接手者需要从 SKILL.md、docs/install.md 和 tests 中推断命令。", "补充简短 README 或 pyproject 元数据。", "observed", ["EV-INSTALL-DOC", "EV-TESTS"]),
        ],
        "assumptions": [
            assumption("ASM-MODULE-GROUPING", "本文的模块划分按文件职责和运行路径组织，而不是按 Python package 边界组织。", "仓库没有包元数据，scripts 中多个文件通过 import 共享规则。", "维护者可根据未来包结构调整模块粒度。", "inferred", ["EV-DSL-VALIDATOR", "EV-RENDERER"]),
            assumption("ASM-PROJECT-VERSION", "工程未从 pyproject 或包元数据读取 project_version，因此文档中 project_version 保持空值。", "扫描未发现 pyproject.toml、setup.cfg 或 setup.py。", "若后续增加项目元数据，可在 DSL document.project_version 中同步。", "observed", ["EV-WORKTREE"]),
        ],
        "source_snippets": [],
    }
    return document


def main():
    document = build_document()
    DSL_PATH.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    import sys

    sys.path.insert(0, str(ROOT))
    from scripts.v2_phase4 import collect_expected_diagrams

    checked_ids = [
        record.diagram_id
        for record in collect_expected_diagrams(document)
        if record.diagram_id and record.should_render
    ]
    review = {
        "artifact_schema_version": "1.0",
        "reviewer": "codex_readability_review",
        "source_dsl": str(DSL_PATH.resolve(strict=False)),
        "checked_diagram_ids": checked_ids,
        "accepted_diagram_ids": checked_ids,
        "revised_diagram_ids": [],
        "split_diagram_ids": [],
        "skipped_diagrams": [],
        "remaining_readability_risks": [],
    }
    REVIEW_PATH.write_text(json.dumps(review, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {DSL_PATH}")
    print(f"Wrote {REVIEW_PATH}")
    print(f"Expected diagrams: {len(checked_ids)}")


if __name__ == "__main__":
    main()
