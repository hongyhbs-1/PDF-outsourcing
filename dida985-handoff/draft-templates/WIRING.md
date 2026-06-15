# 草案模板接线说明（draft-templates · 委托方草案版，按此精修）

> 这 4 个文件是委托方做的**草案版**（已用真数据渲染验证位置/内容正确），交给你做**版面精修**。
> class 前缀：冲刺方案 = `rp-`，逐题错因分析 = `pqc-`。渲染样本见上级目录 `../sample-payload.json`。

## 放置
- `m_remediation_plan.jinja2` / `m_per_question_causes.jinja2` → 你的 `templates/pages/`
- `m_remediation_plan.css` / `m_per_question_causes.css` → 你的 `templates/css/`（会被 css 合并自动加载）

## 接线到 report_master（2 处 include）

**① 冲刺方案 —— 紧跟封面后：**
```jinja2
{# 封面 m0_cover 之后 #}
{% if remediation_plan %}
<div class="module-page" data-section-key="remediation_plan">
  {% include 'pages/m_remediation_plan.jinja2' %}
</div>
{% endif %}
```

**② 逐题错因分析 —— 紧跟「逐题分析明细」(m9_question_detail) 之后：**
```jinja2
{# m9_question_detail 之后 #}
{% if per_question_causes %}
<div class="module-page" data-section-key="per_question_causes">
  {% include 'pages/m_per_question_causes.jinja2' %}
</div>
{% endif %}
```
> ★ 因新增「逐题错因分析」为第 8 段，**原第 8 段及之后的 TOC 编号 / 页序顺延后移一位**，请在精修时一并处理。

## 渲染字段（来自 sample-payload.json，委托方注入，你只渲染）
- `remediation_plan`：`headline` / `priority_items[]{knowledge_name,importance_level,action}` / `difficulty_upgrade{intro,stages[]{name,detail}}` / `stage_one_steps[]{step,detail}`
- `per_question_causes[]`：`no / knowledge / difficulty / cause_l1 / cause_l2 / student_summary / break_point(可选)`

## 铁律（务必保持）
- 不渲染分数（满分/得分）；重要度用**文本星级**（5星/4星），不用 ★ 符号。
- 文案不出现具体时间/周期（30天/60天/一周/每天/本周）；推进节奏用 **阶段一/阶段二/集中冲刺** + **第一步/第二步**（数据已按此口径，照渲即可）。
