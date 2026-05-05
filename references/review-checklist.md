# create-structure-md Review Checklist

## Final Report

- Confirm the final report states the final output path.
- Confirm the final report states the temporary work directory.
- Confirm the final report includes the final output path and temporary work directory.
- Confirm the final report lists assumptions and low-confidence items, or explicitly states that none were identified.
- Confirm assumptions and low-confidence items are reported when present.
- Confirm the final report states Mermaid gate results, including Mermaid readability artifact path, rendered diagram completeness status, and strict rendered Markdown validation status.
- Confirm static-only Mermaid checks, if mentioned, are reported as non-final diagnostics and not as final acceptance for V2 Phase 4.
- If strict validation did not run, confirm the final report states that final Mermaid gate acceptance is incomplete and why.
- Confirm strict Mermaid validation is the default final-generation gate, and Static-only Mermaid validation is not final acceptance for V2 Phase 4.
- Confirm the module- or system-specific output file path is reported.
- Confirm generic filename rejection is reported when the renderer or validator refuses a generic-only filename.
- Confirm default output overwrite protection is reported when an existing file blocks rendering.

## Boundary Checks

- Confirm this skill only rendered prepared design content.
- Confirm repository analysis, requirement inference, and multi-document generation were handled outside this skill.
- Confirm no repo analysis was performed during this skill workflow.
- Confirm no repo analysis, requirements inference, multi-document generation, Word/PDF output, image export, Graphviz output, or Jinja2 template rendering happened inside the skill.
- Confirm Graphviz fully removed means no final image artifacts and no `dot` or `graphviz` code fences.
- Confirm Mermaid-only diagram output: final diagrams are Markdown Mermaid fences, not image artifacts.
- Confirm no Jinja2 dependency, template requirement, or Jinja2 rendering path was introduced.
- Confirm the result is a single Markdown file.
- Confirm the filename comes from `document.output_file`.
- Confirm `document.output_file` is the exact generated filename.
- Confirm the filename is module- or system-specific.
- Confirm the result is a module- or system-specific output file.
- Confirm generic filename rejection was enforced for generic-only names.
- Confirm an existing output file is refused by default.
- Confirm default output overwrite protection is active.
- Confirm `--overwrite` is used only for intentional replacement.
- Confirm `--backup` preserves the previous file before writing the new output.
- Confirm `generated_at` is filled in the rendered output without mutating the DSL.

## DSL Policy Checks

- Confirm validation policy outside DSL: validation behavior is enforced by scripts and workflow references, not embedded as design prose.
- Confirm DSL instances do not contain `empty_allowed`, `required`, `min_rows`, or similar schema policy fields.
- Confirm common metadata, canonical module IDs, traceability target mappings, and ID reference rules were checked.
- Confirm traceability uses `target_type` and `target_id` as the authoritative binding; when inline evidence mode was requested, confirm duplicate traceability renders once.
- Confirm optional, required, and extra diagram rules were checked.
- Confirm fixed table columns are owned by renderer/schema/reference docs, not DSL instances.
- When inline evidence mode was requested, confirm extra table evidence renders after the table; confirm support metadata names are not visible column keys and extra diagrams render only when non-empty.
- Confirm Chapter 4 mechanism details and Chapter 9 structure issues use the same content-block behavior.
- Confirm every non-empty content-block section includes at least one text block.
- Confirm content-block table rows do not carry support refs.
- Confirm Chapter 9 renders risks, assumptions, low-confidence items, then structure issues.

## V2 Foundation Checks

- Confirm DSL input uses `dsl_version: "0.2.0"`.
- Confirm V1 DSL fixtures are rejected fixtures, not renderer acceptance fixtures.
- Confirm final Markdown was rendered with hidden evidence mode unless inline evidence was requested.
- Confirm evidence refs remain DSL metadata when hidden from final Markdown.
- Confirm no repository analysis was added to create-structure-md.
- Confirm Chapter 4 uses the seven fixed V2 subsections in order.
- Confirm public interface index rows and detail sections match and render in index order.
- Confirm Section 5.2 simplified runtime unit table omits V1 reason columns.

## Mermaid Validation

- Confirm Mermaid-only diagram output: every final diagram is a Markdown Mermaid code block.
- Confirm supported MVP core Mermaid diagram types only are used.
- Confirm required Mermaid diagrams are present.
- Confirm an independent Mermaid readability review artifact was produced before strict validation.
- Confirm the Mermaid readability artifact covers every expected DSL diagram ID or gives a non-empty skipped reason for an explicitly not-applicable owning section.
- Confirm DSL Mermaid sources passed strict validation.
- Confirm strict Mermaid validation ran with `--work-dir`.
- Confirm rendered Markdown contains Mermaid fences only where Mermaid sources exist.
- Confirm every Mermaid fence in rendered Markdown has an adjacent `diagram-id` metadata comment.
- Confirm rendered diagram completeness passed and missing diagrams were not accepted by title-only matches.
- Confirm strict rendered Markdown validation ran in strict mode.
- Confirm strict rendered Markdown validation covers `validate_mermaid.py --from-markdown <output-file>`.
- Confirm rendered Mermaid passes `verify_v2_mermaid_gates.py --rendered-markdown <output-file> --post-render`.
- Confirm post-render Markdown Mermaid validation was run.
- Confirm Static-only Mermaid validation is not final acceptance.
- Confirm `scripts/validate_mermaid.py` and `references/mermaid-rules.md` were not modified.
- Confirm Graphviz fully removed from final output.
- Confirm no final image artifacts were produced.
- Confirm Graphviz, DOT, SVG, PNG, PDF, and exported image deliverables are absent.

## Text Safety

- Confirm plain text and Markdown-capable field safety: normal design text remains prose, and Markdown-capable fields cannot break the rendered document.
- Confirm structure-design lint for normal design text was reviewed.
- Confirm source snippets are evidence-only exceptions to normal prose rules.
- Confirm evidence and snippet restraint: include only necessary, minimal, safe evidence.
- Confirm source snippets are necessary, redacted, safely fenced, and not inside table cells.
- Confirm source snippet secret review was completed before rendering snippets.
- Confirm source snippets do not contain obvious secrets, tokens, private keys, credentials, personal data, or unrelated code.

## Rendered Structure

- Confirm the rendered document uses the fixed 9-chapter structure.
- Confirm the rendered document has fixed 9 chapters.
- Confirm fixed section numbering remains stable when optional content is absent.
- Confirm fixed numbering remains stable for all fixed sections.
- Confirm Chapter 4 seven fixed subsections are present for every rendered module.
- Confirm public interface index and details are consistent.
- Confirm Section 5.2 simplified runtime unit table uses only `运行单元 | 类型 | 入口 | 职责 | 关联模块 | 备注`.
- Confirm optional empty sections use the documented empty-state wording.
- When inline evidence mode was requested, confirm table-row support data rendered outside Markdown table cells.
- Confirm IDs, confidence, and refs are not visible table columns except in chapter 9 risks, assumptions, and low-confidence summaries.
- When inline evidence mode was requested, confirm evidence notes render near the referenced design item or after the referenced table row.
- Confirm unreferenced evidence warnings were reviewed.
- Confirm risks and assumptions render in chapter 9; when inline evidence mode was requested, confirm support refs render when present.
- Confirm Chapter 9 risk/assumption/low-confidence visibility when those items are present.
- Confirm low-confidence summary excludes support data and Mermaid diagram nodes.
- Confirm low-confidence summary whitelist includes only intended design content.
