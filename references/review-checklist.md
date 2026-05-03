# create-structure-md Review Checklist

## Final Output Path

- Confirm the result is a single Markdown file.
- Confirm the filename comes from `document.output_file`.
- Confirm the filename is module- or system-specific.

## Fixed Chapters

- Confirm the rendered document uses the fixed 9-chapter structure.
- Confirm optional empty sections use the documented empty-state wording.

## Mermaid Validation

- Confirm DSL Mermaid sources passed strict validation, or record the user's explicit acceptance of static-only validation.
- Confirm rendered Markdown contains Mermaid fences only where Mermaid sources exist.
- If static-only validation was used, confirm the final report states that strict validation was not performed, local Mermaid CLI tooling unavailable was the reason, and the user accepted static-only validation for this run.

## No Repo Analysis

- Confirm this skill only rendered prepared design content.
- Confirm repository analysis, requirement inference, and multi-document generation were handled outside this skill.
