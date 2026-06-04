---
title: "T007: CSS !important 治理 + 英语主题 token 消费"
status: in_progress
priority: P1
phase: review
assignee: hermes
branch: longxiang
created: 2026-06-04
blocked_by: []
acceptance_criteria:
  - shared_icon_enhancements.css !important 数量 < 50（当前 444）
  - 英语主题 CSS 消费 --vh-* token
  - visual_hierarchy.css 无需 !important 即可生效（cascade 自然优先）
  - 所有样本 PDF 输出不变
related: [T006]
---

# T007: CSS !important 治理 + 英语主题 token 消费

## 背景

T006 建立了完整的视觉层级系统（--vh-* token），但 shared_icon_enhancements.css 有 444 个 !important 会架空这个系统。当前通过"visual_hierarchy.css 最后加载"临时绕过，但这不是长久之策。

## 范围

1. **Phase A: !important 清理** — shared_icon_enhancements.css
   - 统计 444 个 !important 的分布
   - 逐模块评估是否可以移除
   - 移除后用 CSS specificity 或加载顺序保证覆盖
   
2. **Phase B: 英语主题统一** — english_subject_theme.css + m10/m11
   - 消费 --vh-* 层级 token
   - 确保英语主题的标题层级与数学一致

3. **Phase C: cascade 去临时化**
   - 移除 renderer.py 中 visual_hierarchy.css 特殊加载逻辑
   - 让层级系统通过正常的 CSS specificity 生效

## 不做

- 模板简化（T008）
- 新功能开发
