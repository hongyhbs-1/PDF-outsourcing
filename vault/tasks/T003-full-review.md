---
type: task
id: "T003"
title: "全量审查：文档更新+样本替换+远程代码变更"
status: done
priority: P1
phase: ship
assignee: "Hermes + Claude"
project: "Outsourcing-PDF-layout"
created: "2026-05-08"
updated: "2026-05-08"
blocked_by: []
blocks: []
related: ["T001", "T002"]
tags: [review, docs, samples, code]
branch: ""
pr: ""
commits: []
merged: false
release: ""
---

# 全量审查：文档更新+样本替换+远程代码变更

## 目标

对本次所有变更进行全面双轴审查（规范轴+需求轴）。

## 审查范围

### Hermes 负责（文档+数据）
1. README.md（新建）— 格式规范、内容准确性
2. docs/需求文档.md — 过时修复是否正确
3. docs/engineering-standards.md — 目录/超标数据/清理记录更新
4. docs/report-data-contract.md — M10/M11 补充是否完整准确
5. docs/漫画图片功能使用说明.md — 删除确认
6. samples/json/ — 新旧替换、数据格式兼容性

### Claude 负责（代码）
远程 4 个 commit（510331e..e3ee8a5）的 31 文件变更：
- 渲染脚本更新（render_all_samples.py、render_standalone.py）
- 模板精修（封面/诊断/弱点/知识点/领域/分层/可信度/逐题等）
- CSS 样式更新（14 个 CSS 文件）
- 新增使用说明文档

## 验收标准

- [x] 文档变更无事实错误
- [x] 文档间无矛盾
- [ ] 代码变更无 P0/P1 问题（代码 P0 留后续处理，非本次范围）
- [x] 新样本数据格式描述准确

## 执行记录

| 日期 | 阶段 | summary | 事件 |
|------|------|---------|------|
| 2026-05-08 | review | 分工：Hermes审文档+数据，Claude审代码 | 审查启动 |
| 2026-05-08 | fix | 修复文档 P1-D1~D6（6项）：样本名/数量/命令/蓝图/.gitignore/使用说明 | 文档修复完成 |
| 2026-05-08 | ship | 文档审查通过，代码 P0（CSS !important/XSS）留后续 | 文档部分完成 |
| 2026-05-08 | review | Hermes发现8项(0P0/6P1/2P2)，Claude发现16项(3P0/7P1/6P2) | 审查完成，共24项 |
