# create-structure-md Review Checklist

## Final Output Path

- Confirm the result is a single Markdown file.
- Confirm the filename comes from `document.output_file`.
- Confirm `document.output_file` is the exact generated filename.
- Confirm the filename is module- or system-specific.
- Confirm an existing output file is refused by default.
- Confirm `--overwrite` is used only for intentional replacement.
- Confirm `--backup` preserves the previous file before writing the new output.
- Confirm `generated_at` is filled in the rendered output without mutating the DSL.

## Fixed Chapters

- Confirm the rendered document uses the fixed 9-chapter structure.
- Confirm fixed section numbering remains stable when optional content is absent.
- Confirm optional empty sections use the documented empty-state wording.
- Confirm IDs, confidence, and refs are not visible table columns except in chapter 9 risks, assumptions, and low-confidence summaries.

## Mermaid Validation

- Confirm DSL Mermaid sources passed strict validation, or record the user's explicit acceptance of static-only validation.
- Confirm rendered Markdown contains Mermaid fences only where Mermaid sources exist.
- Confirm rendered Mermaid passes `validate_mermaid.py --from-markdown <output-file> --static`.
- If static-only validation was used, confirm the final report states that strict validation was not performed, local Mermaid CLI tooling unavailable was the reason, and the user accepted static-only validation for this run.

## Support Data

- Confirm evidence notes render near the referenced design item or after the referenced table row.
- Confirm unreferenced evidence warnings were reviewed.
- Confirm traceability uses `target_type` and `target_id` as the authoritative binding and duplicates render once.
- Confirm source snippets are necessary, redacted, safely fenced, and not inside table cells.
- Confirm risks and assumptions render in chapter 9 with support refs when present.
- Confirm low-confidence summary excludes support data and Mermaid diagram nodes.
- Confirm extra table evidence renders after the table, support metadata names are not visible column keys, and extra diagrams render only when non-empty.

## No Repo Analysis

- Confirm this skill only rendered prepared design content.
- Confirm repository analysis, requirement inference, and multi-document generation were handled outside this skill.
