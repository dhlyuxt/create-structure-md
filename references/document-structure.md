# create-structure-md 0.4.0 Document Structure

This file documents only the active rendered section order for create-structure-md 0.4.0.

Rendered Markdown is generated output. The source of truth is `structure.manifest.json` plus referenced child JSON files.

## Rendered Markdown Structure

```markdown
# <repository_name> 结构说明

## 仓库概述
### 当前仓库介绍
### 解决的问题
### 主要功能
### 核心组件

## 快速开始
### 使用场景
### 准备工作
### 第一次运行/接入
#### <quick_start.first_run.steps[].title>
### 最小示例
### 预期结果

## 架构概述
### 架构总览
### 软件分层
### 模块划分
### 目录角色

## 主线流程
### <main_flow_details[].title>

## 模块详解
### <module_details[].name>
#### 责任
#### <module_details[].mechanisms[].title>
```

## Fixed Headings

Renderer-owned fixed headings are not repeated as `title` fields in fixed DSL sections. Fixed sections also do not carry `key` fields.

Main-flow detail headings come from `main_flow_details[].title`.

Module detail headings come from `module_details[].name`.

Mechanism headings come from `module_details[].mechanisms[].title`.

Extra subsection headings come from each extra subsection `title`; their stable identifiers come from `key`.

Extra subsections render after fixed content in array order at the level where they are declared.
