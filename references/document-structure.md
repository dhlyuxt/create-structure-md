# create-structure-md 0.4.0 Document Structure

This file documents only the active rendered section order for create-structure-md 0.4.0.

Rendered Markdown is generated output. The source of truth is `structure.manifest.json` plus referenced child JSON files.

## Rendered Markdown Structure

```markdown
# <repository_name> 结构说明

## 入门
### 概述
### 快速开始

## 深入解析
### 架构概述
### 主线流程
#### <main_flow_details[].title>
### 模块详解
#### <module_details[].name>
##### <module_details[].mechanisms[].title>
```

## Fixed Headings

Renderer-owned fixed headings are not repeated as `title` fields in fixed DSL sections. Fixed sections also do not carry `key` fields.

Main-flow detail headings come from `main_flow_details[].title`.

Module detail headings come from `module_details[].name`.

Mechanism headings come from `module_details[].mechanisms[].title`.

Extra subsection headings come from each extra subsection `title`; their stable identifiers come from `key`.

Extra subsections render after fixed content in array order at the level where they are declared.
