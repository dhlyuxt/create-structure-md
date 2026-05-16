# 0.3.0 Markdown Document Structure

The 0.3.0 Markdown renderer emits one fixed eight-chapter document. JSON object
property order is not semantic; the renderer always uses this order:

1. `# <document.title>`
2. `## 1. 文档说明`
3. `## 2. 仓库概述与阅读路线`
4. `## 3. 目录地图`
5. `## 4. 系统分层与模块职责`
6. `## 5. 仓库主线`
7. `## 6. 关键机制深读`
8. `## 7. 配置、移植与集成边界`
9. `## 8. 风险、假设与验证缺口`

The renderer is human-first. Visible prose and Mermaid labels should use names,
titles, explanations, and descriptions instead of internal/reference IDs. Module
references resolve through Chapter 4 module names. Mechanism references resolve
through mechanism section titles.

Optional diagram objects are rendered when supplied, including directory
relationship diagrams, module layer diagrams, mainline detail diagrams, and
mechanism diagrams. Diagram bodies are emitted as fenced `mermaid` blocks.

Chapter 6 renders each selected mechanism as a direct subchapter:

```markdown
### 6.N <mechanism section title>
```

When `key_mechanisms` is empty, Chapter 6 still appears and contains exactly:

```markdown
本次分析未选择可深读的关键机制。
```
