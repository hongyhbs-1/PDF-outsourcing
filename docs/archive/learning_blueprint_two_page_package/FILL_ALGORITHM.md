# Fill Algorithm

## 1. Build evidence block

Inputs:

- `cover.cover_meta.raw_question_count`
- `cover.cover_meta.display_question_count`
- `question_detail.total_count`
- `cover.cover_meta.paper_count`
- `data_reliability.section_4_coverage.stats.*`

Outputs:

- raw questions
- valid big questions
- expanded sub-questions
- L2/L3 coverage text
- data period

## 2. Domain state algorithm

For each math domain:

```text
方程与不等式 / 函数 / 数与代数 / 统计与概率 / 应用问题 / 几何
```

The builder first checks `domains.domain_items`, then `kp_drill.domain_panels`.

State rules:

```text
if has_data is false or accuracy is missing:
    state = nodata
elif accuracy >= target_accuracy:
    state = achieved
elif target_accuracy - accuracy <= 10:
    state = attention
else:
    state = improve
```

Visual mapping:

| State | Label | Visual |
|---|---|---|
| `achieved` | 已达标 | teal |
| `attention` | 需关注 | amber |
| `improve` | 需加强 | orange/red |
| `nodata` | 数据不足 | gray-blue |

## 3. Core shortlist algorithm

If `core_weakness.items` exists:

```text
sort by priority P0 > P1 > P2, then by absolute gap to target, then input order
```

If it does not exist:

```text
fallback to city_compare.overlap_items top 3/4
priority = 补测
state = 优先补测
```

This prevents the report from pretending that there is a stable weakness conclusion when evidence is insufficient.

## 4. City focus algorithm

Inputs:

- `city_compare.overlap_items`

Sorting:

```text
city_rank ASC, then importance_score DESC
```

Tag rules:

```text
if student_accuracy is null:
    tag = 优先补测
elif student_accuracy < target_accuracy:
    tag = 高频+薄弱
else:
    tag = 保持巩固
```

## 5. Data confidence algorithm

Input:

- `data_reliability.conclusion.total_level`
- `data_reliability.conclusion.conclusion_credibility.weighted_score`

Rules:

```text
if total_level contains 高: stars = 5
elif total_level contains 中: stars = 3
elif total_level contains 低 or 不足: stars = 2
else fallback to weighted score
```

## 6. Active execution axis stage

Rules:

```text
if report_title contains 追踪 or 阶段:
    active_stage = 追踪复测
elif data reliability is 低 / 不足:
    active_stage = 补齐证据
elif stable core weakness exists:
    active_stage = 老师执行
else:
    active_stage = AI诊断分析
```

## 7. Stage plan algorithm

Inputs:

- current accuracy
- target accuracy
- top 1-2 weakness/focus points

Default plan when no custom tutoring plan exists:

```text
Stage 1: 0-30 days, current + 35% of gap, at least +8pp
Stage 2: 30-60 days, current + 70% of gap, at least +15pp
Stage 3: 60+ days, target accuracy
```

Important: These are stage reference markers, not guaranteed score promises. If your system has a dedicated plan module, replace this default algorithm with the plan module output.
