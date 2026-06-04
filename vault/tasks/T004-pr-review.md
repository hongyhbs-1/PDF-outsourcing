---
type: task
id: "T004"
title: "longxiang 分支全量审查（PR 前终审）"
status: in_progress
priority: P0
phase: review
assignee: "Hermes"
project: "Outsourcing-PDF-layout"
created: "2026-05-08"
updated: "2026-05-08"
blocked_by: []
blocks: []
related: ["T002", "T003"]
tags: [review, pr-ready]
branch: "longxiang"
pr: ""
commits: ["531ac95", "de355a0", "de355a0", "82640d2", "d8508d3", "cf3e371", "6de7756", "74d46b3"]
merged: false
release: ""
---

# longxiang 分支全量审查

## 目标

对 longxiang 分支相对 main 的全部差异进行终审，确认 PR 就绪状态。

## 审查范围

longxiang 分支独有变更（8 个 commit，170 文件）：
1. README.md 新建 + 多次更新
2. docs/ 全量文档更新（需求文档/工程规范/数据契约/使用说明）
3. samples/json/ 替换（8旧→3新）
4. 删除 prompts/、static/、docs/archive/、docs/images/（+ .gitignore）
5. vault/ dev-flow 任务管理初始化

## 验收标准

- [ ] 无 P0 问题
- [ ] P1 问题已全部修复或有明确原因保留
- [ ] 文档间无矛盾
- [ ] .gitignore 覆盖所有已删除目录

## 执行记录

| 日期 | 阶段 | summary | 事件 |
|------|------|---------|------|
| 2026-05-08 | review | 审查启动 | Hermes 单方审查 |
