try:
    from v2_foundation import RuleViolation, has_reason
except ModuleNotFoundError:
    from scripts.v2_foundation import RuleViolation, has_reason


SUPPORT_REF_FIELDS = ("evidence_refs", "traceability_refs", "source_snippet_refs")


def _non_empty(value):
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, list):
        return len(value) > 0
    return value is not None


def _duplicate_values(values):
    seen = set()
    duplicates = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    return duplicates


def iter_content_block_sections(document):
    modules = document.get("module_design", {}).get("modules", [])
    if isinstance(modules, list):
        for module_index, module in enumerate(modules):
            if not isinstance(module, dict):
                continue
            details = module.get("internal_mechanism", {}).get("mechanism_details", [])
            if not isinstance(details, list):
                continue
            for detail_index, detail in enumerate(details):
                if not isinstance(detail, dict):
                    continue
                yield (
                    "$.module_design.modules"
                    f"[{module_index}].internal_mechanism.mechanism_details[{detail_index}].blocks",
                    detail.get("blocks", []),
                    None,
                )

    structure_issues = document.get("structure_issues_and_suggestions")
    if isinstance(structure_issues, dict):
        yield (
            "$.structure_issues_and_suggestions.blocks",
            structure_issues.get("blocks", []),
            structure_issues.get("not_applicable_reason"),
        )


def phase3_content_block_violations(document):
    violations = []
    if not isinstance(document, dict):
        return violations

    for section_path, blocks, not_applicable_reason in iter_content_block_sections(document):
        if not isinstance(blocks, list):
            continue
        if not blocks:
            continue
        if has_reason(not_applicable_reason):
            continue
        block_ids = [block.get("block_id") for block in blocks if isinstance(block, dict)]
        for duplicate in _duplicate_values(block_ids):
            violations.append(RuleViolation(section_path, f"duplicate block_id {duplicate}"))
        if not any(_is_non_empty_text_block(block) for block in blocks):
            violations.append(
                RuleViolation(
                    section_path,
                    "content block section must include at least one non-empty text block",
                )
            )
        for block_index, block in enumerate(blocks):
            if isinstance(block, dict):
                violations.extend(_block_violations(block, f"{section_path}[{block_index}]"))
    return violations


def _is_non_empty_text_block(block):
    return (
        isinstance(block, dict)
        and block.get("block_type") == "text"
        and _non_empty(block.get("text"))
    )


def _block_violations(block, base):
    block_type = block.get("block_type")
    if block_type == "text":
        if not _non_empty(block.get("text")):
            return [RuleViolation(f"{base}.text", "text block text must be non-empty")]
        return []
    if block_type == "diagram":
        return _diagram_block_violations(block, base)
    if block_type == "table":
        return _table_block_violations(block, base)
    return []


def _diagram_block_violations(block, base):
    violations = []
    diagram = block.get("diagram")
    if not isinstance(diagram, dict):
        return [RuleViolation(f"{base}.diagram", "diagram block must provide diagram")]
    if not _non_empty(diagram.get("source")):
        violations.append(RuleViolation(f"{base}.diagram.source", "diagram.source must be non-empty"))
    if block.get("confidence") != diagram.get("confidence"):
        violations.append(
            RuleViolation(
                f"{base}.diagram.confidence",
                "diagram block confidence must match diagram.confidence",
            )
        )
    return violations


def _table_block_violations(block, base):
    violations = []
    table = block.get("table")
    if not isinstance(table, dict):
        return [RuleViolation(f"{base}.table", "table block must provide table")]
    columns = table.get("columns", [])
    rows = table.get("rows", [])
    if not columns:
        violations.append(RuleViolation(f"{base}.table.columns", "table block must contain at least one column"))
    if not rows:
        violations.append(RuleViolation(f"{base}.table.rows", "table block must contain at least one row"))
    column_keys = [column.get("key") for column in columns if isinstance(column, dict)]
    for column_index, key in enumerate(column_keys):
        if key in SUPPORT_REF_FIELDS:
            violations.append(
                RuleViolation(
                    f"{base}.table.columns[{column_index}].key",
                    f"reserved support metadata key {key}",
                )
            )
    for duplicate in _duplicate_values(column_keys):
        violations.append(RuleViolation(f"{base}.table.columns", f"duplicate content block table column key {duplicate}"))
    allowed_keys = set(column_keys)
    for row_index, row in enumerate(rows):
        if not isinstance(row, dict):
            continue
        support_keys = set(row).intersection(SUPPORT_REF_FIELDS)
        if support_keys:
            violations.append(
                RuleViolation(
                    f"{base}.table.rows[{row_index}]",
                    "content block table rows must not carry support refs",
                )
            )
        unknown_keys = set(row) - allowed_keys
        if unknown_keys:
            violations.append(
                RuleViolation(
                    f"{base}.table.rows[{row_index}]",
                    "content block table row contains keys outside declared columns",
                )
            )
    return violations
