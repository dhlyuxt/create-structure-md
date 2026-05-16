# create-structure-md 0.3.0 Mermaid Rules

## Purpose

Mermaid diagrams exist to help a reader build a mental model. They are not ID maps.

## Supported Diagram Types

- `flowchart`
- `sequenceDiagram`
- `stateDiagram-v2`

The first non-empty, non-comment Mermaid source line must start with the same token as `diagram_type`. Legacy `graph` declarations are rejected.

## Visible Label Gate

The validator inspects these visible-label forms:

- flowchart bracket labels such as `node[存储核心]`, `node(平台适配)`, and `node{是否已初始化}`
- flowchart edge labels, including pipe forms such as `-->|失败路径|`, `---|失败路径|`, `-.->|失败路径|`, and `==>|失败路径|`
- flowchart attribute labels with simple quoted label values such as `@{ label: "存储核心" }`
- unlabeled flowchart node IDs such as `storage_core` in `storage_core --> platform_port`; IDs with explicit rendered labels elsewhere in the diagram are not treated as visible labels
- simple flowchart subgraph titles such as `subgraph 存储核心`
- sequence aliases such as `participant api as 存储接口`
- unaliased sequence participant and actor names such as `participant 存储接口` and `actor 用户`
- implicit sequence participant names in messages such as `应用->>核心: 写入成功`
- sequence message labels such as `api->>core: 写入成功`

Visible labels must not expose legacy internal IDs such as `MOD-*`, `RUN-*`, `FLOW-*`, or `MER-*`, including when they are embedded in surrounding text. Technical node identifiers are allowed when explicit rendered labels are human-readable.

Mermaid comment lines that start with `%%` are ignored by the visible-label gate.

## Warning Policy

If a diagram uses syntax whose visible labels are not inspected, validation emits a warning. This includes unsupported node shapes such as asymmetric flowchart nodes, textual flowchart edge labels such as `-. 失败路径 .-`, and sequence boxes. Normal validation allows warnings. Strict validation promotes warnings to errors.

`stateDiagram-v2` state diagrams are supported by schema but non-strict due to partial label coverage until state label inspection is implemented.
