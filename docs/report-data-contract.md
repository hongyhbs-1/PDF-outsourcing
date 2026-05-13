# 报告数据对账契约

本文档用于定位“页面数据和 JSON 数据对不上”的问题。每个展示项都应能追溯到 JSON 源路径、适配/计算位置和模板位置。

## 对账表

| 模块 | 页面展示项 | JSON 路径 | 适配/计算位置 | 模板位置 | 预期格式 | 是否允许缺失 |
|---|---|---|---|---|---|---|
| 全局 | 学生姓名 | `meta.student_display_name` | `render_standalone.render_html()` 直传 | 多页面、页眉 | 文本 | 否 |
| 全局 | 学科 | `meta.subject_name` 或 `meta.subject` | 直传 | 封面、画像、标题上下文 | 文本 | 否 |
| 全局 | 报告日期 | `meta.report_date` | `pdf_chrome_templates` 计划统一 | 页脚、封面 | 日期文本 | 否 |
| 全局 | 报告标题 | `meta.report_title` / `meta.report_name` | `pdf_chrome_templates` 计划统一 | 页脚、封面 | 文本 | 否 |
| 封面 | 分析题量 | `cover.cover_meta.question_count` / `total_questions` | 模板兼容映射 | `templates/pages/m0_cover.jinja2` | `N题` | 是，显示 `--题` |
| 概览 | 分析试卷数 | `cover.cover_meta.paper_count`，兜底 `appendix.papers.total_papers` | 模板内选择 | `templates/pages/m_overview.jinja2` | 数字 | 否 |
| 概览 | 有效大题数 | `cover.cover_meta.display_question_count` / `question_count` | 模板内选择 | `templates/pages/m_overview.jinja2` | 数字 | 否 |
| 概览 | 子题总数 | `cover.cover_meta.total_questions`，对照 `appendix.papers.total_questions` | 模板内选择 | `templates/pages/m_overview.jinja2` | 数字 | 否 |
| 概览 | 整体正确率 | `summary.current_accuracy_text`，数值 `summary.current_accuracy` | 模板内格式化兜底 | `templates/pages/m_overview.jinja2` | 百分比文本 | 否 |
| M1 | 当前正确率 | `summary.current_accuracy_text` / `summary.current_accuracy` | 模板直读 | `templates/pages/m1_summary.jinja2` | 百分比文本 | 否 |
| M1 | 目标正确率 | `summary.target_accuracy_text` / `summary.target_accuracy` | 模板直读 | `templates/pages/m1_summary.jinja2` | 百分比文本 | 否 |
| M1 | 达标率 | `summary.pass_rate` / `summary.pass_rate_text` | `donut_chart()` 渲染 | `templates/pages/m1_summary.jinja2` | 百分比 | 否 |
| M1 | L3 知识点总数 | `summary.high_freq_kp_total` | 模板说明文案 | `templates/pages/m1_summary.jinja2` | 数字 | 是 |
| M1 | P0 突破项数量 | `breakthrough.items` | 模板密度判断 | `templates/pages/m1_summary.jinja2` | 列表数量 | 否 |
| M1 | P0 知识点名称 | `breakthrough.items[].name_cn` | 模板循环 | `templates/pages/m1_summary.jinja2` | 文本 | 否 |
| 画像 | 当前正确率分档 | `summary.current_accuracy` | 模板内三档分类 | `templates/pages/student_profile.jinja2` | `<60 / 60-84 / >=85` | 否 |
| 提升预期 | 当前/目标正确率 | `summary.current_accuracy` / `summary.target_accuracy` | 模板内三档路线 | `templates/pages/improvement_preview.jinja2` | 百分比 | 否 |
| M4 | 领域列表 | `domains.domain_items` | `section_2_domains` 别名兼容 | `templates/pages/m4_domains.jinja2` | 列表 | 否 |
| M4 | 领域名称 | `domains.domain_items[].name_cn` / `name` | `get_domain_name()` | `templates/pages/m4_domains.jinja2` | 文本 | 否 |
| M4 | 领域正确率 | `domains.domain_items[].accuracy_text` / `accuracy` | 模板直读 | `templates/pages/m4_domains.jinja2` | 百分比文本 | 否 |
| M4 | 领域状态 | `domains.domain_items[].status` / `progress_class` | 状态宏映射 | `templates/pages/m4_domains.jinja2` | 中文状态/CSS 类 | 否 |
| M4 | 目标线 | `domains.target_accuracy` / `target_accuracy_text` | 模板内 section/meta/default 选择 | `templates/pages/m4_domains.jinja2` | 百分比 | 否 |
| M2 | 核心短板数量 | `core_weakness` 内列表项 | 模板直读 | `templates/pages/m2_core_weakness.jinja2` | 列表数量 | 是 |
| M3 | 知识点钻取表 | `kp_drill.*` | 模板按 L1/L2/L3/L4 展开 | `templates/pages/m3_kp_drill.jinja2` | 表格 | 是 |
| M5 | 核心短板总数 | `city_compare.overlap_summary.student_core_weak_total` | 模板直读 | `templates/pages/m5_city_compare.jinja2` | 数字 | 否 |
| M5 | 城市 TopN | `city_compare.overlap_summary.city_top_n` | 模板直读 | `templates/pages/m5_city_compare.jinja2` | 数字 | 否 |
| M5 | 交集数量 | `city_compare.overlap_summary.overlap_count` | 模板直读 | `templates/pages/m5_city_compare.jinja2` | 数字 | 否 |
| M5 | 重合率 | `city_compare.overlap_summary.overlap_ratio` | 模板支持 0-1 / 0-100 | `templates/pages/m5_city_compare.jinja2` | 百分比 | 否 |
| M5 | 高频交集项 | `city_compare.overlap_items[]` | 模板循环 | `templates/pages/m5_city_compare.jinja2` | 表格/卡片 | 是 |
| M6 | 达标率 | `tiered_learning.stage_judgement.current.pass_rate` 或 `summary.pass_rate` | 模板内兼容 | `templates/pages/m6_tiered_learning.jinja2` | 百分比 | 是 |
| M7 | 总题数 | `data_reliability.section_4_coverage.stats.total_questions` | 模板直读 | `templates/pages/m7_data_reliability.jinja2` | 数字 | 否 |
| M7 | L3 覆盖 | `data_reliability.section_4_coverage.stats.l3_covered/l3_total` | 模板直读 | `templates/pages/m7_data_reliability.jinja2` | `covered/total` | 是 |
| M7 | 低样本提醒 | `data_reliability.section_4_coverage.data_insufficient` | 模板直读 | `templates/pages/m7_data_reliability.jinja2` | 文案/列表 | 是 |
| M8 | 总题数 | `appendix.papers.total_questions` | 模板直读 | `templates/pages/m8_appendix.jinja2` | 数字 | 否 |
| M8 | 试卷数 | `appendix.papers.total_papers` | 模板直读 | `templates/pages/m8_appendix.jinja2` | 数字 | 否 |
| M8 | 试卷清单 | `appendix.papers.items[]` | 模板循环 | `templates/pages/m8_appendix.jinja2` | 表格 | 是 |
| M9 | 总题数 | `question_detail.total_count` | 模板直读 | `templates/pages/m9_question_detail.jinja2` | 数字 | 否 |
| M9 | 错题数 | `question_detail.wrong_count` | 模板直读 | `templates/pages/m9_question_detail.jinja2` | 数字 | 否 |
| M9 | 正确数 | `question_detail.correct_count`，当前模板也会算 `total_count - wrong_count` | 模板计算/源字段对照 | `templates/pages/m9_question_detail.jinja2` | 数字 | 否 |
| M9 | 试卷数 | `question_detail.papers | length` | 模板计算 | `templates/pages/m9_question_detail.jinja2` | 数字 | 否 |
| M9 | 题号 | `question_detail.papers[].wrong_questions[].no` / `correct_questions[].no` | 模板循环 | `templates/pages/m9_question_detail.jinja2` | 文本 | 是 |
| M9 | 知识点 | `question_detail.papers[].*.kp_name` | 模板循环 | `templates/pages/m9_question_detail.jinja2` | 文本 | 是 |

## 高风险字段

| 风险类型 | 说明 | 重点位置 |
|---|---|---|
| 默认值污染 | `default(0)` 可能把缺失数据渲染成真实 0 | `m_overview`、`m1_summary`、`m9_question_detail` |
| 口径重复计算 | 正确数既可能来自源数据，也可能由 `total_count - wrong_count` 计算 | `m9_question_detail` |
| 字段同名冲突 | JSON 字段名为 `items` 时不能用点号访问 dict 方法 | `m1_summary`、M5/M8 列表 |
| 旧字段残留 | 模板注释和历史适配层可能仍写 `report_output`/旧路径 | M1/M4/M5 注释与兼容入口 |
| 显示文案拼接 | 百分比和题数字符串难以反向解析 | M1/M4/M5/M7/M8/M9 |
| 双入口不一致 | `render_standalone.py` 与 `html_renderer.py` 同时存在，可能注入别名不同 | 渲染入口 |

## 抽样基线

| 样本 | 用途 | 关注点 |
|---|---|---|
| `sample_01_math_25q.json` | 常规数学样本 | 常规题量、数学领域、基础 PDF 排版 |
| `sample_04_english_rpt2_dual.json` | 英语长样本 | 长数据、M9 逐题、M7/M8 密度、分页复杂度 |
| `sample_06_english_long_with_m10m11.json` | 英语深度页 | M10/M11 可见性与后续章节进度 |
| `sample_08_math_4paper_long.json` | 数学长样本 | 长 M5/M9/M8 尾页风险 |

## 当前审计结论

2026-04-30 使用 `scripts/audit_report_data_consistency.py` 全样本审计：

| 类型 | 样本 | 字段 | 处理结论 |
|---|---|---|---|
| 源数据缺失 | `sample_01_math_25q.json`、`sample_02_minimal.json`、`sample_03_math_full.json` | `question_detail` | 旧样本未提供逐题明细，审计标记为 `source_missing`，模板不伪造 M9 数据 |
| 源数据缺失 | `sample_01_math_25q.json`、`sample_02_minimal.json`、`sample_03_math_full.json` | `data_reliability.section_4_coverage.stats.l3_covered/l3_total` | 旧样本未提供 L3 覆盖字段，审计标记为 `source_missing` |
| 代码层对不齐 | 全部 8 个样本 | 审计覆盖的 M1/M4/M5/M7/M8/M9 关键字段 | 未发现 `mismatch` |

源数据缺失项不能在模板或适配层写死兜底值；补数据应由样本源 JSON 或上游 payload 生成逻辑完成。
