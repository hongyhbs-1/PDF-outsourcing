---
type: task
id: "T002"
title: "补充README.md，审查所有文档是否过时"
status: done
priority: P1
phase: ship
assignee: "Hermes"
project: "Outsourcing-PDF-layout"
created: "2026-05-08"
updated: "2026-05-08"
blocked_by: []
blocks: []
related: []
tags: [docs, review, readme]
branch: ""
pr: ""
commits: []
merged: false
release: ""
---

# 补充README.md，审查所有文档是否过时

## 目标

1. 为项目根目录创建 README.md（项目介绍、快速开始、目录结构、技术栈）
2. 审查现有文档（需求文档、工程规范、数据契约等），标记过时内容并更新

## 验收标准

- [x] 根目录有 README.md，包含项目介绍、环境搭建、运行命令、目录结构
- [x] 现有文档全部审查完毕，过时内容已更新或标注
- [x] 文档之间无矛盾

## 范围

**审查清单**：
- `docs/需求文档.md` — 230行，需求+技术栈+环境搭建
- `docs/engineering-standards.md` — 179行，工程规范
- `docs/report-data-contract.md` — 82行，数据对账契约
- `prompts/README.md` — 29行，提示词版本管理

## Git流程触发

| 阶段 | Git操作 | 状态 |
|------|---------|------|
| decide完成 | `git checkout -b docs/T002-readme-and-review main` | ☐ |
| code完成 | `git push origin docs/T002-readme-and-review` + 创建PR | ☐ |
| ship确认 | PR merge | ☐ |

## 执行记录

| 日期 | 阶段 | summary | 事件 |
|------|------|---------|------|
| 2026-05-08 | - | - | 任务创建，初始状态 backlog |
| 2026-05-08 | code | 创建README.md(4.4KB) | 项目入口文档 |
| 2026-05-08 | code | 需求文档：英语5→4领域、样本4→8个、模块表补全10个模板、验收标准加状态 | 修复过时内容 |
| 2026-05-08 | code | 工程规范：删除不存在目录、加vault/、更新超标文件行数 | 修复过时内容 |
| 2026-05-08 | code | 数据契约：补充M10(10字段)+M11(8字段)对账条目 | 补充缺失 |
| 2026-05-08 | ship | 全部4项完成，验收通过 | 任务完成 |
