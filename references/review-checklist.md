# create-structure-md Review Checklist

## Final Output Path

- Confirm the result is a single Markdown file.
- Confirm the filename comes from `document.output_file`.
- Confirm `document.output_file` is the exact generated filename.
- Confirm the filename is module- or system-specific.
- Confirm the result is a module- or system-specific output file.
- Confirm generic filename rejection was enforced for generic-only names.
- Confirm the final output path is reported.
- Confirm the temporary work directory is reported.
- Confirm an existing output file is refused by default.
- Confirm default output overwrite protection is active.
- Confirm `--overwrite` is used only for intentional replacement.
- Confirm `--backup` preserves the previous file before writing the new output.
- Confirm `generated_at` is filled in the rendered output without mutating the DSL.

## Fixed Chapters

- Confirm the rendered document uses the fixed 9-chapter structure.
- Confirm the rendered document has fixed 9 chapters.
- Confirm fixed section numbering remains stable when optional content is absent.
- Confirm fixed numbering remains stable for all fixed sections.
- Confirm optional empty sections use the documented empty-state wording.
- Confirm IDs, confidence, and refs are not visible table columns except in chapter 9 risks, assumptions, and low-confidence summaries.

## Mermaid Validation

- Confirm Mermaid-only diagram output: every final diagram is a Markdown Mermaid code block.
- Confirm DSL Mermaid sources passed strict validation, or record the user's explicit acceptance of static-only validation.
- Confirm strict Mermaid validation ran with `--work-dir` unless the user accepted the static-only fallback.
- Confirm rendered Markdown contains Mermaid fences only where Mermaid sources exist.
- Confirm rendered Mermaid passes `validate_mermaid.py --from-markdown <output-file> --static`.
- Confirm post-render Markdown Mermaid validation was run.
- Confirm static-only Mermaid fallback reporting states the CLI renderability limitation, tooling unavailability, and user acceptance.
- If static-only validation was used, confirm the final report states that strict validation was not performed, local Mermaid CLI tooling unavailable was the reason, and the user accepted static-only validation for this run.
- Confirm Graphviz fully removed from final output.
- Confirm no final image artifacts were produced.
- Confirm Graphviz, DOT, SVG, PNG, PDF, and exported image deliverables are absent.

## Support Data

- Confirm evidence notes render near the referenced design item or after the referenced table row.
- Confirm unreferenced evidence warnings were reviewed.
- Confirm traceability uses `target_type` and `target_id` as the authoritative binding and duplicates render once.
- Confirm source snippets are necessary, redacted, safely fenced, and not inside table cells.
- Confirm source snippet secret review was completed before rendering snippets.
- Confirm risks and assumptions render in chapter 9 with support refs when present.
- Confirm low-confidence summary excludes support data and Mermaid diagram nodes.
- Confirm low-confidence summary whitelist includes only intended design content.
- Confirm extra table evidence renders after the table, support metadata names are not visible column keys, and extra diagrams render only when non-empty.
- Confirm validation policy outside DSL: validation behavior is enforced by scripts and workflow references, not embedded as design prose.

## No Repo Analysis

- Confirm this skill only rendered prepared design content.
- Confirm repository analysis, requirement inference, and multi-document generation were handled outside this skill.
- Confirm no repo analysis was performed during this skill workflow.
- Confirm no Jinja2 dependency, template requirement, or Jinja2 rendering path was introduced.
