# create-structure-md Orchestration And Mermaid Guidance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Strengthen the active create-structure-md 0.4.0 documentation workflow so the main agent stays in orchestration, repository understanding is delegated through a brief, and Mermaid authoring guidance encourages useful diagrams without making them mandatory everywhere.

**Architecture:** This is a documentation-only contract update. `SKILL.md` owns workflow and agent-boundary rules, `references/dsl-authoring-guide.md` owns diagram selection guidance, `references/mermaid-rules.md` stays focused on existing Mermaid rendering requirements, and `references/review-checklist.md` adds soft review prompts without changing validators, schemas, or renderer behavior.

**Tech Stack:** Markdown skill/reference files, existing Python validation/test commands for verification only.

---

## User Constraints

- Do not use TDD for this documentation-only change.
- Do not add or expand tests for this spec.
- Do not modify `tests/test_v040_docs.py`.
- Do not execute deletion commands. If a cleanup need appears, stop and show the exact command for the user to run.
- Do not change the 0.4.0 manifest shape.
- Do not change renderer, schema, or validation behavior unless a separate implementation request explicitly asks for it.

## Source Spec

Implement this spec:

- `docs/superpowers/specs/2026-05-30-create-structure-md-orchestration-and-mermaid-guidance-design.md`

Acceptance criteria from the spec:

- `SKILL.md` includes an explicit main-agent boundary for target repository reading.
- `SKILL.md` includes an early repository-understanding subagent step and routes later repository context through its brief.
- `references/dsl-authoring-guide.md` includes Mermaid diagram selection guidance.
- `references/mermaid-rules.md` remains focused on rendering and readability rules for Mermaid blocks that exist.
- `references/review-checklist.md` encourages reviewers to challenge missed diagram opportunities without adding a no-Mermaid rejection gate.
- The documentation change does not introduce TDD requirements for docs-only updates.
- No deletion command is executed.

## File Structure

Modify:

- `SKILL.md`: add the main-agent target-repository access boundary, insert the repository-understanding subagent step, renumber workflow steps, and route flow/module planning through the repository understanding brief.
- `references/dsl-authoring-guide.md`: add `## Mermaid 图选型建议` and connect the existing Mermaid block guidance and final checks to it.
- `references/mermaid-rules.md`: keep active rendering gates, remove duplicate diagram-selection policy, and point readers back to the authoring guide.
- `references/review-checklist.md`: add soft review checks for repository-understanding handoff and missed Mermaid opportunities without introducing a required-Mermaid gate.

Do not modify:

- `tests/test_v040_docs.py`
- `scripts/`
- `schemas/`
- `examples/`
- `generated/`

## Task 1: Update `SKILL.md` Main-Agent Boundary

**Nature:** Documentation-only. Review and existing-command verification only; do not use TDD.

**Files:**

- Modify: `SKILL.md`

- [ ] **Step 1: Inspect the current workflow section**

Run:

```bash
nl -ba SKILL.md | sed -n '1,260p'
```

Expected: The file contains `## Core Boundaries`, `## Workflow`, current Step 1 through Step 19, and the current boundary sentence `The main agent coordinates the workflow and does not directly write substantive chapter prose.`

- [ ] **Step 2: Replace the main-agent boundary bullets in `## Core Boundaries`**

In `SKILL.md`, replace the current main-agent boundary bullet with this text and keep the surrounding existing bullets:

```markdown
- The main agent is a workflow owner, not a repository analyst. It coordinates inputs, routing, subagent dispatch, package-level files, validation, rendering, and final review.
- The main agent may list target repository files and directories to understand package size and dispatch scope.
- The main agent must not open, read, quote, summarize, or inspect target repository source files to understand behavior, choose flows, choose modules, explain mechanisms, or select examples.
- The main agent may read create-structure-md package files, generated manifest files, reference files, validators, renderer code, and skill documentation when maintaining this create-structure-md repository itself.
- The main agent may read subagent-produced repository understanding briefs, candidate lists, review conclusions, and accepted JSON payloads.
- The main agent coordinates the workflow and does not directly write substantive chapter prose.
- When the target repository is also the current maintenance repository, the repository-access boundary applies to the repository being documented, not to create-structure-md files being edited as part of skill maintenance.
```

Keep this existing C-repository rule after the new boundary bullets:

```markdown
- When the target repository is C, every subagent that needs repository understanding must invoke the `repo-understand` skill first and prefer `repo-analysis-tools` before reading raw source.
```

- [ ] **Step 3: Tighten Step 1's watch text**

In `### Step 1: Confirm Inputs`, replace the `**Watch:**` line with:

```markdown
**Watch:** The main agent may list files and directories to size the package and dispatch scope, but must not open target repository source files or infer content structure from implementation details.
```

- [ ] **Step 4: Update Step 2 routing references**

In `### Step 2: Load Orchestration Contract And Route References`, replace the `**References:**` list with:

```markdown
**References:**
- Main agent uses `references/dsl-spec.md` for manifest/package shape.
- Main agent uses `references/document-structure.md` for rendered section order.
- Main agent uses `references/review-checklist.md` for final gates.
- Repository-understanding subagents use `references/dsl-authoring-guide.md` plus relevant repository context.
- Authoring subagents use `references/dsl-authoring-guide.md`.
- Authoring or review subagents that touch Mermaid use `references/mermaid-rules.md` for rendering constraints and `references/dsl-authoring-guide.md` for diagram selection guidance.
- For C repositories, subagents that analyze repository structure, files, symbols, or behavior must invoke `repo-understand` first and follow its `repo-analysis-tools` CLI-first route.
```

Replace Step 2's `**Watch:**` line with:

```markdown
**Watch:** The main agent routes references and repository context; it does not use authoring references or target source files to write substantive chapter prose itself.
```

- [ ] **Step 5: Insert a new Step 3 repository-understanding handoff**

Insert this section after Step 2:

```markdown
### Step 3: Create Repository Understanding Brief

**Do:** Assign one repository-understanding subagent before chapter authoring, flow planning, or module planning.

**Input:** Repository root, package root, scope, exclusions, user constraints, file list or directory shape gathered by the main agent, and relevant authoring guidance.

**References:** Give the subagent `references/dsl-authoring-guide.md`; for C repositories, require `repo-understand` first and `repo-analysis-tools` before raw source reading.

**Watch:** The brief is the main agent's repository context. The main agent must not replace it by opening target repository source files.

**Output:** A concise repository understanding brief outside JSON, covering repository purpose and reader-facing value, major responsibility areas, likely architecture layers, important user-facing flows, candidate module responsibilities, setup or quick-start signals, exclusions, uncertainty, and evidence limits.
```

- [ ] **Step 6: Renumber the existing workflow steps**

Renumber every existing step after the inserted repository-understanding step by adding one to the old step number.

Expected final order:

```markdown
### Step 1: Confirm Inputs
### Step 2: Load Orchestration Contract And Route References
### Step 3: Create Repository Understanding Brief
### Step 4: Write Manifest And Document Metadata
### Step 5: Write Repository Overview
### Step 6: Review Repository Overview
### Step 7: Write Quick Start
### Step 8: Review Quick Start
### Step 9: Write Architecture Overview
### Step 10: Review Architecture Overview
### Step 11: Plan Main Flow List
### Step 12: Review Main Flow List
### Step 13: Write Main Flow Details
### Step 14: Review Main Flow Details
### Step 15: Plan Module List
### Step 16: Review Module List
### Step 17: Write Module Details
### Step 18: Review Module Details
### Step 19: Synthesize Overview Tables
### Step 20: Validate, Render, And Final Review
```

- [ ] **Step 7: Route overview authoring through the brief**

In the `**References:**` lines for repository overview, quick start, and architecture overview authoring steps, include the repository understanding brief.

Use these exact replacement lines:

```markdown
**References:** Give the subagent the repository understanding brief, `references/dsl-spec.md`, and `references/dsl-authoring-guide.md`.
```

Apply this replacement in:

- `### Step 5: Write Repository Overview`
- `### Step 7: Write Quick Start`
- `### Step 9: Write Architecture Overview`

- [ ] **Step 8: Route flow and module planning through the brief**

In the main-flow planning step, replace the references line with:

```markdown
**References:** Give the subagent the repository understanding brief, `references/dsl-authoring-guide.md`, and relevant user constraints.
```

In the module planning step, replace the references line with:

```markdown
**References:** Give the subagent the repository understanding brief, `references/dsl-authoring-guide.md`, and relevant user constraints.
```

- [ ] **Step 9: Route detail authoring through frozen rows and the brief**

In the main-flow detail authoring step, replace the references line with:

```markdown
**References:** Give each subagent its frozen list row, the repository understanding brief, `references/dsl-spec.md`, `references/dsl-authoring-guide.md`, and `references/mermaid-rules.md` when diagrams are present or relationship/order-heavy content would benefit from a diagram.
```

In the module detail authoring step, replace the references line with:

```markdown
**References:** Give each subagent its frozen list row, the repository understanding brief, `references/dsl-spec.md`, `references/dsl-authoring-guide.md`, and `references/mermaid-rules.md` when diagrams are present or relationship/order-heavy content would benefit from a diagram.
```

- [ ] **Step 10: Route detail review through the brief and soft Mermaid challenge**

In the main-flow detail review step, replace the references and watch lines with:

```markdown
**References:** Give each reviewer the frozen list row, the repository understanding brief, assigned detail JSON, `references/dsl-spec.md`, `references/dsl-authoring-guide.md`, `references/mermaid-rules.md` when needed, and `references/review-checklist.md`.

**Watch:** Reject content that deviates from the frozen flow, becomes a call graph, duplicates module detail, includes process metadata, or modifies files outside the assigned detail file. Challenge missing Mermaid when relationship-heavy or order-heavy content is hard to understand from text alone, but do not reject a detail file only because it has no Mermaid.
```

In the module detail review step, replace the references and watch lines with:

```markdown
**References:** Give each reviewer the frozen list row, the repository understanding brief, assigned detail JSON, `references/dsl-spec.md`, `references/dsl-authoring-guide.md`, `references/mermaid-rules.md` when needed, and `references/review-checklist.md`.

**Watch:** Reject content that deviates from the frozen module, becomes a directory encyclopedia, API reference, file list, or call chain, makes auxiliary code the module focus, includes process metadata, or modifies files outside the assigned detail file. Challenge missing Mermaid when relationship-heavy or order-heavy content is hard to understand from text alone, but do not reject a detail file only because it has no Mermaid.
```

- [ ] **Step 11: Add non-negotiables for repository context and Mermaid softness**

In `## Non-Negotiables`, add these bullets:

```markdown
- The repository understanding brief is produced before chapter authoring, flow planning, and module planning.
- The main agent uses only file lists, directory shape, repository understanding briefs, candidate lists, review conclusions, and accepted JSON payloads as target-repository context.
- The main agent does not open, quote, summarize, or inspect target repository source files to understand behavior.
- Missing Mermaid is not by itself a final rejection; reviewers challenge omissions when relationships or behavior paths are hard to understand from text alone.
```

- [ ] **Step 12: Review `SKILL.md` for forbidden drift**

Run:

```bash
rg -n "when diagrams are expected|directly write substantive chapter prose|Step 19|Step 20|repository understanding brief|target repository source" SKILL.md
```

Expected:

- No line contains `when diagrams are expected`.
- `Step 20: Validate, Render, And Final Review` is present.
- `repository understanding brief` appears in the new early step and downstream routing.
- `target repository source` appears in the main-agent boundary.
- The sentence about not directly writing substantive chapter prose remains present.

## Task 2: Add Mermaid Selection Guidance To `references/dsl-authoring-guide.md`

**Nature:** Documentation-only. Review and existing-command verification only; do not use TDD.

**Files:**

- Modify: `references/dsl-authoring-guide.md`

- [ ] **Step 1: Inspect the current block guidance**

Run:

```bash
nl -ba references/dsl-authoring-guide.md | sed -n '1,180p'
```

Expected: The file contains `## 内容块使用规则` and a single Mermaid block paragraph before `## 仓库概述怎么写`.

- [ ] **Step 2: Replace the Mermaid block paragraph**

Replace the current paragraph that starts with `Mermaid blocks 用于关系或行为路径` with:

```markdown
Mermaid blocks 用于关系或行为路径，必须能通过 strict Mermaid CLI rendering。图是否值得加入由 `## Mermaid 图选型建议` 判断；缺少 Mermaid 本身不是最终拒收理由，但当关系或顺序只靠文字很费力时，作者应优先考虑加一张小而清楚的图。
```

- [ ] **Step 3: Add `## Mermaid 图选型建议`**

Insert this section after `List block \`items\` values are string arrays.` and before `## 仓库概述怎么写`:

```markdown
## Mermaid 图选型建议

当图能明显降低读者理解成本时，优先使用 Mermaid。不要为了满足形式而画图；缺少 Mermaid 本身不是最终拒收理由。

优先画一张小而高信号的图，不要画覆盖整个仓库的大图。标签保持人类可读，不在可见标签中暴露内部 ID。不要用 Mermaid 倾倒调用图、目录树、源码扫描结果或 API reference。

Use `flowchart` for component relationships, layer maps, data movement, initialization pipelines, build or release paths, and dependency direction. Prefer `flowchart` over legacy `graph`.

Use `sequenceDiagram` for runtime conversations where order matters, such as API call flows, request/response paths, storage read/write paths, retries, or callback handoffs.

Use `stateDiagram-v2` for lifecycle-heavy concepts, such as connection states, job states, image update phases, cache validity, or mode transitions.

Use `classDiagram` only for stable type or interface relationships that help readers understand responsibilities. Do not turn it into an API reference.

Use a table instead of Mermaid when the content is only a compact comparison with no meaningful relationship or order.

Use prose instead of Mermaid when the diagram would simply restate one sentence.

Existing Mermaid blocks still need strict Mermaid CLI rendering. Reviewers should challenge omissions when a relationship-heavy or order-heavy section is hard to understand from text alone, but must not reject a document only because the final Markdown contains no Mermaid.
```

- [ ] **Step 4: Update main-flow authoring guidance**

In `## 主线流程怎么写`, replace:

```markdown
主线流程回答“一个重要任务如何跨组件移动”。每个 `chapters/04-main-flow-details/<flow-key>.json` 文件描述一个行为路径，可以用 blocks 叙述流程，必要时配 Mermaid 表达关系或行为路径。
```

with:

```markdown
主线流程回答“一个重要任务如何跨组件移动”。每个 `chapters/04-main-flow-details/<flow-key>.json` 文件描述一个行为路径，可以用 blocks 叙述流程；当跨组件关系、执行顺序、请求响应、存储读写或回调交接只靠文字很费力时，优先按 `## Mermaid 图选型建议` 加一张小图。
```

- [ ] **Step 5: Update module authoring guidance**

In `## 模块详解怎么写`, after this paragraph:

```markdown
每个 `chapters/05-module-details/<module-key>.json` 文件描述一个责任单元。Mechanisms 必须存在于 owning module detail 内。模块内容可以包含职责、关键路径、输入输出、机制、扩展点和风险，但不要变成逐文件清单或 API reference pages。
```

add:

```markdown
当模块责任、生命周期、状态转换、数据移动或接口协作靠文字难以快速建立模型时，优先按 `## Mermaid 图选型建议` 加一张小图。不要用 Mermaid 展开逐函数调用链或目录树。
```

- [ ] **Step 6: Update the final check list**

Replace the final Mermaid check:

```markdown
检查 Mermaid blocks 是否只出现在允许文件中，简短、人类可读、不暴露内部 ID，并能通过 Mermaid CLI 渲染。
```

with:

```markdown
检查 Mermaid blocks 是否只出现在允许文件中，简短、人类可读、不暴露内部 ID，并能通过 Mermaid CLI 渲染；当关系密集或顺序密集内容没有图时，确认文字仍然容易理解。
```

- [ ] **Step 7: Review the authoring guide for duplicate policy**

Run:

```bash
rg -n "Mermaid 图选型建议|when diagrams are expected|every chapter|每个章节|必须.*Mermaid|最终拒收|strict Mermaid CLI rendering" references/dsl-authoring-guide.md
```

Expected:

- `Mermaid 图选型建议` appears as one heading and is referenced from nearby guidance.
- No line says every chapter or every detail file must have Mermaid.
- No line says missing Mermaid is a final rejection.
- `strict Mermaid CLI rendering` remains present.

## Task 3: Keep `references/mermaid-rules.md` Validation-Focused

**Nature:** Documentation-only. Review and existing-command verification only; do not use TDD.

**Files:**

- Modify: `references/mermaid-rules.md`

- [ ] **Step 1: Inspect the current Mermaid rules file**

Run:

```bash
nl -ba references/mermaid-rules.md | sed -n '1,120p'
```

Expected: The file contains `## Active Gate` and `## Authoring Guidance`.

- [ ] **Step 2: Replace `## Authoring Guidance` with validation-focused text**

Replace the entire `## Authoring Guidance` section with:

```markdown
## Relationship To Authoring Guidance

Use `references/dsl-authoring-guide.md` as the canonical source for Mermaid diagram selection guidance.

This file only records validation and readability constraints for Mermaid blocks that exist:

- Mermaid blocks must be short enough to review directly in the DSL.
- Mermaid labels must be human-readable.
- Visible labels must not expose internal IDs.
- Mermaid blocks must not contain process logs, command transcripts, raw scan logs, rejected drafts, or subagent reports.
- Mermaid blocks must not dump call graphs, directory trees, or API references.
- Missing Mermaid is not by itself a rendering or final-review failure.
- Static readability guidance does not replace CLI rendering.
```

- [ ] **Step 3: Keep active gate rules unchanged**

Confirm that these lines remain in `## Active Gate`:

```markdown
Every Mermaid block must render through Mermaid CLI when Mermaid blocks exist.

Mermaid blocks can appear in detail files and shared-block static chapters, but not in `main_flow_overview` or `module_overview`.

Missing `mmdc` is an error.

Render failure is an error.

Missing SVG output after zero exit is an error.
```

- [ ] **Step 4: Review for selection-policy drift**

Run:

```bash
rg -n 'flowchart|sequenceDiagram|stateDiagram|classDiagram|Use `|Prefer|Missing Mermaid' references/mermaid-rules.md
```

Expected:

- The file does not enumerate diagram type selection rules.
- `Missing Mermaid is not by itself a rendering or final-review failure.` is present.
- Active rendering failures are still listed.

## Task 4: Add Soft Review Prompts To `references/review-checklist.md`

**Nature:** Documentation-only. Review and existing-command verification only; do not use TDD.

**Files:**

- Modify: `references/review-checklist.md`

- [ ] **Step 1: Inspect current review checklist sections**

Run:

```bash
nl -ba references/review-checklist.md | sed -n '1,140p'
```

Expected: The file contains `## Contract`, `## Ownership And Review`, `## Blocks`, `## Subagent Hygiene`, and `## Final Render`.

- [ ] **Step 2: Add repository-understanding handoff checks**

In `## Ownership And Review`, after:

```markdown
- Confirms separate adversarial detail review for every accepted detail file.
```

add:

```markdown
- Confirms one repository-understanding brief was produced before chapter authoring, flow planning, and module planning.
- Confirms the repository understanding brief stayed outside the DSL package.
- Confirms the main agent did not open, quote, summarize, or inspect target repository source files to understand behavior.
```

- [ ] **Step 3: Update Mermaid block review language**

In `## Blocks`, replace:

```markdown
- Mermaid readability is checked before final acceptance.
- Mermaid blocks are relationship or behavior diagrams and pass strict Mermaid CLI rendering.
```

with:

```markdown
- Mermaid readability is checked for every Mermaid block before final acceptance.
- Mermaid blocks are relationship or behavior diagrams and pass strict Mermaid CLI rendering.
- Reviewers challenge missing Mermaid when relationship-heavy or order-heavy content is hard to understand from text alone.
- Reviewers do not reject a document only because the final Markdown contains no Mermaid.
```

- [ ] **Step 4: Strengthen subagent hygiene for briefs**

In `## Subagent Hygiene`, replace:

```markdown
- Repository-understanding notes stay outside the DSL package.
```

with:

```markdown
- Repository-understanding briefs and notes stay outside the DSL package.
```

- [ ] **Step 5: Review for hard Mermaid gate avoidance**

Run:

```bash
rg -n "Mermaid|no Mermaid|contains no Mermaid|must contain|必须.*Mermaid|reject.*Mermaid" references/review-checklist.md
```

Expected:

- The checklist still rejects invalid Mermaid blocks when they exist.
- The checklist says reviewers do not reject a document only because the final Markdown contains no Mermaid.
- No line requires every rendered Markdown file, chapter, flow, or module to contain Mermaid.

## Task 5: Final Verification And Handoff

**Nature:** Documentation-only. Verification only; do not use TDD.

**Files:**

- Verify: `SKILL.md`
- Verify: `references/dsl-authoring-guide.md`
- Verify: `references/mermaid-rules.md`
- Verify: `references/review-checklist.md`
- Verify unchanged: `tests/test_v040_docs.py`

- [ ] **Step 1: Confirm only intended files changed**

Run:

```bash
git diff --name-only
```

Expected changed tracked files:

```text
SKILL.md
references/dsl-authoring-guide.md
references/mermaid-rules.md
references/review-checklist.md
```

The spec file and generated files may appear as unrelated untracked work in this workspace. Do not modify or delete them during this implementation.

- [ ] **Step 2: Confirm no test file edit was introduced**

Run:

```bash
git diff -- tests/test_v040_docs.py
```

Expected: no output.

If output appears, stop and report the diff summary to the user; do not revert it with `git checkout` and do not expand the test.

- [ ] **Step 3: Check documentation wording against acceptance criteria**

Run:

```bash
rg -n "workflow owner|not a repository analyst|repository understanding brief|target repository source|Mermaid 图选型建议|Missing Mermaid|do not reject a document only because|strict Mermaid CLI rendering" SKILL.md references/dsl-authoring-guide.md references/mermaid-rules.md references/review-checklist.md
```

Expected:

- `SKILL.md` contains `workflow owner`, `not a repository analyst`, `repository understanding brief`, and `target repository source`.
- `references/dsl-authoring-guide.md` contains `Mermaid 图选型建议` and `strict Mermaid CLI rendering`.
- `references/mermaid-rules.md` contains `Missing Mermaid is not by itself a rendering or final-review failure.`
- `references/review-checklist.md` contains `Reviewers do not reject a document only because the final Markdown contains no Mermaid.`

- [ ] **Step 4: Check for forbidden TDD language in this docs-only change**

Run:

```bash
rg -n "failing test|verify it fails|TDD|test_v040_docs.py" docs/superpowers/plans/2026-05-30-create-structure-md-orchestration-and-mermaid-guidance-implementation.md SKILL.md references/dsl-authoring-guide.md references/mermaid-rules.md references/review-checklist.md
```

Expected:

- The plan contains user constraints saying not to use TDD and not to modify `tests/test_v040_docs.py`.
- The implementation files do not introduce TDD workflow instructions.
- No step asks for a failing test.

- [ ] **Step 5: Run whitespace verification**

Run:

```bash
git diff --check
```

Expected: no output and exit code 0.

- [ ] **Step 6: Run existing docs smoke test without editing it**

Run:

```bash
python -m unittest tests.test_v040_docs
```

Expected:

```text
OK
```

This is regression verification only. Do not edit or expand `tests/test_v040_docs.py`.

- [ ] **Step 7: Commit the documentation update**

Run:

```bash
git add SKILL.md references/dsl-authoring-guide.md references/mermaid-rules.md references/review-checklist.md
git commit -m "docs: clarify orchestration and mermaid guidance"
```

Expected: one commit containing only the four intended documentation files.

Do not add untracked generated files or the source spec unless the user explicitly asks to include them.

## Self-Review Checklist

- Every acceptance criterion in `docs/superpowers/specs/2026-05-30-create-structure-md-orchestration-and-mermaid-guidance-design.md` maps to a task above.
- No task writes a failing test or expands a test file.
- No task executes a deletion command.
- `SKILL.md` changes preserve the create-structure-md 0.4.0 manifest shape and validation commands.
- Mermaid guidance encourages useful diagrams and explicitly avoids a required-Mermaid final gate.
