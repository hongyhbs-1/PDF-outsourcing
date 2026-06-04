---
title: "T009: 全模块VH层级审查与统一"
priority: P0
phase: review
assignee: "Hermes + Claude"
project: "Outsourcing-PDF-layout"
created: "2026-06-04"
updated: "2026-06-04"
---

## 目标
逐模块 Playwright 扫描所有标题级元素，发现 18 处层级异常，与 Claude 讨论 3 类决策后执行修复。

## 审查数据
Playwright 实测 math_parent 样本，扫描 m1-m9 + mov/sp/ip 所有 >= 12px 元素。

## 发现 18 处异常 → 分 3 类

### A类：核心结论 16px/800 → Hero 18px/700（6 处）
m1/m4/m5/m6/m7/m8 的 core-conclusion__text

### B类：统计数字大小不统一（5 处）
- m1-goal-metric-value 26px, m7-kp-level-num 22px → 24px
- m1-donut-center 42px, m5-overlap-num 40px, m7-overview-card__num 56px → 保持（几何空间决定）

### C类：区块标题 16px/800 → L1 14px/700（3 处）
m5-table-title, m5-card-title, m7-block-title

## 决策（Hermes + Claude 共识）
- A类: 同意。加 .module-page 前缀升特异性（同 m9 已验证方案）
- B类: 2 修 3 不动。行内数值统一 Stat Hero 24px，图表内嵌/仪表盘大数字保持原尺寸
- C类: 同意 L1 14px/700。同 A 类方案

## 根因
shared_icon_enhancements.css 用 .module-page 前缀（特异性 0,2,0）压制 VH 的（0,1,0）
VH 规则增加 .module-page 等特异性选择器解决

## 执行
- visual_hierarchy.css: Hero 规则扩展到 m1-m9 全部 conclusion + .module-page 前缀
- Stat Hero 规则增加 m1-goal-metric-value + m7-kp-level-num
- L1 规则增加 m5/m7 的 3 个区块标题 + .module-page 前缀

## 验证
- Playwright 15/15 (A:9 + B:3 + C:3) 全通过
- 21/21 golden_typeset tests
- math + english 2 样本 PDF exit 0

## 量化
- Hero 覆盖: 3→12 选择器 (m1-m9 全 conclusion)
- Stat Hero 覆盖: 1→3 (m9 + m1 + m7)
- L1 覆盖: +3 选择器 + 3 .module-page 前缀
- VH 文件: 195→212 行

## 非主模块审查 (T009-2)
扫描 cover/mtoc/mov/sp/ip，发现 12 处异常。

### 决策（Hermes + Claude 共识）
- A类: mtoc/mov/sp/ip 标题统一 L0 22px/800 (4处)
- B类: mov-hero/sp-hero 统一 Hero 18px/700 (2处)
- C类: mov-card__num/sp-metric/ip-gain 统一 Stat Hero 24px (3处)
- D类: mtoc 导航条目豁免（非内容层级）
- m0 cover 全部豁免（设计专用）

### 验证
- Playwright 9/9 (A:4 + B:2 + C:3)
- 21/21 golden_typeset tests
- 2 样本 PDF exit 0
