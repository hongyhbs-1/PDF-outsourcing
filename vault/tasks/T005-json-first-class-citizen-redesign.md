---
title: "T005: JSON 数据包第一公民 — 数据可视化架构重设计"
status: done
priority: P0
phase: review
assignee: hermes
branch: longxiang
created: 2026-06-02
acceptance_criteria:
  - 完成第一性原理深度调研报告
  - 输出架构重设计方案
  - 用户确认方向后进入 decide 阶段
related: [T003, T004]
---

# T005: JSON 数据包第一公民 — 数据可视化架构重设计

## 背景

用户提出核心命题：**如果 JSON 数据包是第一公民，你会怎么完成这个高质量、层级排版统一的数据可视化项目？**

当前痛点：
1. 数学 JSON（30+ 顶层 key, 1.8MB）与英语 JSON（10 顶层 key, 10-15KB sections 格式）结构完全不同
2. render_standalone.py 有 200+ 行适配代码 (`_normalize_brief_report_payload`) 做格式转换
3. CSS 是最高公民（25 个 CSS 文件，最大的 60KB），数据反而是二等公民
4. 模板直接透传 JSON 字段，没有中间层

## 联合决策结果

**方案**: 5 阶段重设计（Phase 0-4）
**核心决策**:
1. TypedDict 而非 Pydantic（单进程渲染不需要序列化）
2. Adapter Registry 替代 197 行 if/else
3. learning_blueprint_builder.py 暂不拆分（接口清晰）
4. CSS !important 是症状，先完成适配器层再处理
5. html_renderer.py 标记 deprecated，不统一

**分工**: Hermes=合约发现+视觉验收, Claude=代码重构
**Claude 方案**: `docs/t005-claude-proposal.md`
**预计**: 3.5-4 天
