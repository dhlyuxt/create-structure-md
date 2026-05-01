# create-structure-md Phase 5 Spec: Markdown Renderer

## Goal

Implement `scripts/render_markdown.py` to render one module- or system-specific Markdown structure design document from a validated DSL file.

This phase focuses on deterministic document generation, fixed section numbering, safe output paths, fixed table rendering, Mermaid fences, overwrite protection, and chapter-level empty states.

## Dependencies

Depends on Phases 1, 2, and 3.

The renderer assumes the DSL passed `validate_dsl.py`, but still performs defensive checks.

## CLI Contract

```bash
python scripts/render_markdown.py structure.dsl.json --output-dir .
python scripts/render_markdown.py structure.dsl.json --output-dir . --overwrite
python scripts/render_markdown.py structure.dsl.json --output-dir . --backup
```

Rules:

- One positional DSL JSON path is required.
- Missing file fails.
- Invalid JSON fails.
- Missing or invalid `document.output_file` fails.
- `--overwrite` and `--backup` are mutually exclusive.
- Renderer writes `document.output_file` under `--output-dir`.

## Output Filename

Renderer writes exactly one Markdown file.

`document.output_file` must:

- end with `.md`
- be module- or system-specific
- follow the recommended pattern `<documented-object-name>_STRUCTURE_DESIGN.md`
- not be generic-only
- not contain `/`, `\`, `..`, or control characters

Backup path:

```text
<output_file>.bak-YYYYMMDD_HHMMSS
```

Backup timestamp uses local system clock and `%Y%m%d_%H%M%S`.

## Fixed Markdown Structure

Renderer uses fixed numbering for all chapters and subchapters.

Optional content absence must not move later sections forward.

The final document always renders:

1. 文档信息
2. 系统概览
3. 架构视图
4. 模块设计
5. 运行时视图
6. 配置、数据与依赖关系
7. 跨模块协作关系
8. 关键流程
9. 结构问题与改进建议

Required fixed empty states include:

- missing runtime sequence diagram: `未提供运行时序图。`
- single-module collaboration: `本系统当前仅识别到一个结构模块，暂无跨模块协作关系。`
- missing collaboration diagram: `未提供跨模块协作关系图。`
- empty supplement sections: `无补充内容。` or a more specific table/diagram sentence.

## Rendering Responsibilities

Renderer owns:

- fixed chapter order
- fixed section numbering
- fixed table headers
- empty-state text
- Mermaid fence generation
- safe source snippet fences
- support-data insertion hooks
- chapter 9 appended sections
- Markdown escaping

Renderer must not invent design content.

## Tables

Fixed table columns are owned by renderer, not DSL instances.

Fixed table nodes contain `rows`.

Extra table nodes include `id`, `title`, `columns`, and `rows`.

Table cell escaping must handle:

- `|`
- newlines
- unsafe fenced-code markers
- raw HTML block injection

## Mermaid Blocks

Renderer wraps diagram source in Markdown:

````markdown
```mermaid
flowchart TD
  A --> B
```
````

DSL source must not already contain fences.

Empty optional diagrams render fixed empty-state text and no Mermaid block.

Extra diagrams always render because they must have non-empty source.

## Chapter 9

Renderer outputs:

- free-form `structure_issues_and_suggestions` when non-empty
- `风险` section when risks exist
- `假设` section when assumptions exist
- `低置信度项` section when whitelist-collected unknown-confidence items exist

It renders `未识别到明确的结构问题与改进建议。` only when all of those are empty.

## generated_at

If `document.generated_at` is empty, renderer fills the rendered Markdown value but does not mutate the DSL file.

## Tests

Phase 5 tests cover:

- output file naming and generic-name rejection
- overwrite default failure
- `--overwrite`
- `--backup`
- fixed chapter and section numbering
- empty optional sections do not shift numbering
- fixed table rendering
- table cell escaping
- Mermaid fence generation
- generated_at fill without DSL mutation
- rendered output passes `validate_mermaid.py --from-markdown <output-file> --static`

## Acceptance Criteria

- A semantically valid DSL renders to exactly one Markdown file.
- Output file handling is safe and deterministic.
- Fixed structure is stable across optional content differences.

## Out of Scope

- DSL semantic validation beyond defensive checks.
- Strict Mermaid CLI validation.
- Advanced support-data rendering beyond basic hooks, which is completed in Phase 6.
