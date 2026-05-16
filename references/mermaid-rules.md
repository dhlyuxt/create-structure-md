# create-structure-md 0.3.0 Mermaid Rules

## Purpose

Mermaid diagrams exist to help a reader build a mental model. They are not ID maps.

## Supported Diagram Types

- `flowchart`
- `sequenceDiagram`
- `stateDiagram-v2`

The first non-empty Mermaid source line must start with the same token as `diagram_type`. Legacy `graph` declarations are rejected.

## Visible Label Gate

The validator inspects these visible-label forms:

- flowchart bracket labels such as `node[存储核心]`, `node(平台适配)`, and `node{是否已初始化}`
- flowchart edge labels using `-->|失败路径|`, such as `api -->|失败路径| fallback`
- sequence aliases such as `participant api as 存储接口`
- sequence message labels such as `api->>core: 写入成功`

Visible labels must not expose legacy internal IDs such as `MOD-*`, `RUN-*`, `FLOW-*`, or `MER-*`. Technical node identifiers are allowed when the rendered labels are human-readable.

Mermaid comment lines that start with `%%` are ignored by the visible-label gate.

## Warning Policy

If a diagram uses syntax whose visible labels are not inspected, validation emits a warning. Normal validation allows warnings. Strict validation promotes warnings to errors.
