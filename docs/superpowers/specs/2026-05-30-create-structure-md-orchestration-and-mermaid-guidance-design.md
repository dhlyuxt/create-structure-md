# create-structure-md Orchestration And Mermaid Guidance Design

Date: 2026-05-30
Status: draft for user review

## Context

The active create-structure-md 0.4.0 skill successfully renders a reader guide from a manifest package, but a recent EasyFlash run exposed two authoring problems:

- The rendered guide can become prose-only, with no Mermaid diagrams to help readers build a visual model.
- The main agent can drift from orchestration into direct repository reading, even though the skill intends substantive repository understanding and chapter writing to happen through subagents.

The current wording contributes to both problems. Mermaid guidance says diagrams are used "when diagrams are expected", which lets agents skip diagrams too easily. Main-agent boundaries say the main agent coordinates workflow and does not write substantive prose, but they do not explicitly forbid the main agent from opening and interpreting target repository source files.

## Goals

- Make the main agent's repository-access boundary explicit.
- Add an early repository-understanding subagent step before chapter authoring and list planning.
- Ensure the main agent may inspect target repository file lists and directory shape, but may not open, read, quote, summarize, or inspect target repository source files.
- Define a repository understanding brief as the handoff from the repository-understanding subagent to the main agent and later authoring/review subagents.
- Add reference guidance that encourages Mermaid diagrams when they improve reader understanding.
- Describe which Mermaid diagram types are recommended for common documentation situations.
- Keep Mermaid guidance as authoring guidance, not a new hard final-render gate.

## Non-Goals

- Do not add a final review rule that rejects every rendered Markdown file without Mermaid.
- Do not make every chapter or every detail file require a diagram.
- Do not change the 0.4.0 manifest shape.
- Do not change renderer, schema, or validation behavior unless later implementation finds a small wording-aligned validation issue already covered by existing rules.
- Do not use TDD for this documentation-only change.
- Do not execute deletion commands. If cleanup is needed, provide the command for the user to run.

## Main-Agent Boundary

`SKILL.md` should define the main agent as a workflow owner, not a repository analyst.

Allowed main-agent repository actions:

- Confirm repository root, package root, output path, scope, exclusions, and user constraints.
- List target repository files and directories to understand package size and dispatch scope.
- Read create-structure-md package files, generated manifest files, reference files, validators, renderer code, and skill documentation in the create-structure-md repository when maintaining the skill itself.
- Read subagent-produced repository understanding briefs, candidate lists, review conclusions, and accepted JSON payloads.

Forbidden main-agent target-repository actions:

- Open target repository source files to understand behavior.
- Quote target repository source.
- Summarize target repository source directly.
- Inspect implementation details in target repository files.
- Use direct source reading to choose flows, modules, mechanisms, or examples.

When the target repository is also the current maintenance repository, this boundary applies to the repository being documented, not to create-structure-md files being edited as part of skill maintenance.

## Repository-Understanding Subagent

The workflow should insert a new early step after input confirmation and reference routing:

1. The main agent dispatches one repository-understanding subagent.
2. The subagent receives repository root, scope, exclusions, user constraints, the file list or directory shape gathered by the main agent, and relevant authoring guidance.
3. For C repositories, the subagent must invoke `repo-understand` first and prefer `repo-analysis-tools` before raw source reading.
4. The subagent produces a repository understanding brief outside the DSL package.
5. The main agent uses only that brief, the file list, and later subagent outputs as repository context.

The repository understanding brief should be concise and dispatch-oriented:

- repository purpose and reader-facing value
- major responsibility areas
- likely architecture layers
- important user-facing flows
- candidate module responsibilities
- setup or quick-start signals
- exclusions, uncertainty, and evidence limits

The brief must stay outside JSON. It must not be copied into renderable payloads as process metadata.

## Mermaid Guidance

`references/dsl-authoring-guide.md` should add a section such as `## Mermaid 图选型建议`.

The section should tell authoring subagents to prefer Mermaid when a diagram would reduce reader effort. The guidance should encourage diagrams without making them mandatory everywhere.

Recommended situations:

- Use `flowchart` for component relationships, layer maps, data movement, initialization pipelines, build/release paths, and dependency direction.
- Use `sequenceDiagram` for runtime conversations where order matters, such as API call flows, request/response paths, storage read/write paths, retries, or callback handoffs.
- Use `stateDiagram-v2` for lifecycle-heavy concepts, such as connection states, job states, image update phases, cache validity, or mode transitions.
- Use `classDiagram` only for stable type or interface relationships that help readers understand responsibilities. Avoid turning it into an API reference.
- Use a table instead of Mermaid when the content is only a compact comparison with no meaningful relationship or order.
- Use prose instead of Mermaid when the diagram would simply restate one sentence.

Diagram guidance should also say:

- Prefer one small, high-signal diagram over a large map.
- Keep labels human-readable.
- Avoid internal IDs in visible labels.
- Do not use Mermaid to dump call graphs or directory trees.
- Existing Mermaid blocks still need strict Mermaid CLI rendering.
- Missing Mermaid is not by itself a final rejection; reviewers should challenge omissions when relationships or behavior paths are hard to understand from text alone.

## Reference Updates

`references/mermaid-rules.md` should remain validation-focused:

- It should keep the current rule that Mermaid blocks, when present, must render through Mermaid CLI.
- It can point readers to `references/dsl-authoring-guide.md` for diagram selection guidance.
- It should not redefine a separate diagram-selection policy that can drift from the authoring guide.

`references/review-checklist.md` can add a soft review prompt:

- Reviewers should ask whether a relationship-heavy or order-heavy section would be easier with Mermaid.
- Reviewers should not reject a document only because the final Markdown contains no Mermaid.

## Acceptance Criteria

- `SKILL.md` includes an explicit main-agent boundary for target repository reading.
- `SKILL.md` includes an early repository-understanding subagent step and routes later repository context through its brief.
- `references/dsl-authoring-guide.md` includes Mermaid diagram selection guidance.
- `references/mermaid-rules.md` remains focused on rendering and readability rules for Mermaid blocks that exist.
- `references/review-checklist.md` encourages reviewers to challenge missed diagram opportunities without adding a no-Mermaid rejection gate.
- The documentation change does not introduce TDD requirements for docs-only updates.
- No deletion command is executed.

## Implementation Notes

Expected file edits:

- `SKILL.md`
- `references/dsl-authoring-guide.md`
- `references/mermaid-rules.md`
- `references/review-checklist.md`

The previous interrupted attempt also changed `tests/test_v040_docs.py`. Because the user clarified that documentation changes should not use TDD, that test edit should not be expanded as part of this spec. If cleanup is desired, handle it explicitly before implementation.
