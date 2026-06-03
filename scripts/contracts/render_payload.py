"""RenderPayload TypedDict contracts — 从模板和渲染管线反推的数据合约。

Phase 0 合约发现产出。每个 TypedDict 对应模板实际消费的字段集。
total=False 表示所有字段可选 — 模板用 | default() 兜底。
"""

from __future__ import annotations
from typing import TypedDict


# ---------------------------------------------------------------------------
# Meta — 报告元信息
# 消费方: 所有模板（页眉、封面、蓝图 builder）
# ---------------------------------------------------------------------------

class RenderMeta(TypedDict, total=False):
    subject: str                        # "math" | "english"
    subject_name: str                   # "数学" | "英语"
    student_display_name: str           # 学生姓名
    city_name: str                      # 城市名
    grade: str                          # 年级
    report_date: str                    # 报告日期
    report_title: str                   # 报告标题
    report_name: str                    # 报告名称（别名）
    left_title: str                     # 页眉左侧标题
    page_title: str                     # 页面标题
    module_title: str                   # 模块标题
    target_score: str                   # 目标分数
    report_id: str                      # 报告编号
    render_template: str                # 渲染模板标识（如 "brief-report-rem"）


# ---------------------------------------------------------------------------
# Cover — 封面
# 消费方: m0_cover.jinja2
# ---------------------------------------------------------------------------

class CoverBrand(TypedDict, total=False):
    name: str                           # 品牌名（如 "dida985"）
    logo_url: str                       # logo URL


class CoverMeta(TypedDict, total=False):
    student_name: str
    city_name: str
    grade: str
    report_date: str
    subject: str
    question_count: int                 # 分析题量
    total_questions: int                # 子题总数
    display_question_count: int         # 有效大题数
    paper_count: int                    # 试卷数


class CoverData(TypedDict, total=False):
    badge_text: str
    brand: CoverBrand
    title: str
    subject: str
    cover_meta: CoverMeta
    footer_tagline: str


# ---------------------------------------------------------------------------
# Summary — 诊断摘要
# 消费方: m1_summary.jinja2, student_profile.jinja2, improvement_preview.jinja2,
#          m_overview.jinja2, m6_tiered_learning.jinja2, blueprint builder
# ---------------------------------------------------------------------------

class SummaryData(TypedDict, total=False):
    banner_text: str                    # 摘要横幅文案
    current_accuracy: float             # 当前正确率（0-100 数值）
    current_accuracy_text: str          # 当前正确率文本（如 "72.5%"）
    target_accuracy: float              # 目标正确率
    target_accuracy_text: str           # 目标正确率文本
    target_score_text: str              # 目标分数文本
    current_delta: float                # 差值
    current_delta_text: str             # 差值文本
    current_trend: str                  # 趋势（up/down/stable）
    pass_rate: float                    # 达标率
    pass_rate_text: str                 # 达标率文本
    pass_segments: list                 # 达标率分段数据
    high_freq_kp_total: int             # L3 知识点总数
    high_freq_kp_total_text: str        # L3 知识点文本


# ---------------------------------------------------------------------------
# Domains — 领域数据
# 消费方: m4_domains.jinja2, m2_core_weakness.jinja2, student_profile.jinja2,
#          m6_tiered_learning.jinja2, blueprint builder
# ---------------------------------------------------------------------------

class DomainItem(TypedDict, total=False):
    name: str                           # 领域名（英文 key）
    name_cn: str                        # 领域中文名
    accuracy: float                     # 正确率
    accuracy_text: str                  # 正确率文本
    status: str                         # 状态（achieved/improving/weak）
    progress_class: str                 # CSS 进度条类名
    delta_vs_target: float              # 与目标差值
    delta_text: str                     # 差值文本


class DomainsData(TypedDict, total=False):
    target_accuracy: float              # 目标正确率
    target_accuracy_text: str
    domain_items: list[DomainItem]      # 领域列表
    note_text: str                      # 领域备注


# ---------------------------------------------------------------------------
# CoreWeakness — 核心短板
# 消费方: m2_core_weakness.jinja2
# ---------------------------------------------------------------------------

class CoreWeaknessItem(TypedDict, total=False):
    name: str
    name_cn: str
    kp_code: str
    accuracy: float
    delta: float
    level: str                          # 严重程度
    tag: str                            # 标签


class CoreWeaknessData(TypedDict, total=False):
    module_title: str
    intro_text: str
    legend: list
    table_columns: list
    items: list[CoreWeaknessItem]
    has_data: bool
    empty_guidance: str
    reasoning: dict
    tips: list[str]


# ---------------------------------------------------------------------------
# Breakthrough — P0 突破项
# 消费方: m1_summary.jinja2（P0 突破项列表）
# ---------------------------------------------------------------------------

class BreakthroughData(TypedDict, total=False):
    items: list[dict]                   # P0 突破项
    note_text: str
    cta_text: str
    all_achieved: bool
    title: str


# ---------------------------------------------------------------------------
# KpDrill — 知识点钻取
# 消费方: m3_kp_drill.jinja2
# ---------------------------------------------------------------------------

class KpDrillData(TypedDict, total=False):
    module_title: str
    intro_text: str
    has_data: bool
    level_guide: list
    tables: dict                        # {l1: [...], l2: [...], l3: [...], l4: [...]}
    path_example: dict
    domain_panels: list
    header: dict


# ---------------------------------------------------------------------------
# CityCompare — 城市考情对比
# 消费方: m5_city_compare.jinja2
# ---------------------------------------------------------------------------

class OverlapSummary(TypedDict, total=False):
    has_data: bool
    student_core_weak_total: int
    city_top_n: int
    overlap_count: int
    overlap_ratio: float


class CityCompareData(TypedDict, total=False):
    has_data: bool
    overlap_items: list[dict]
    overlap_summary: OverlapSummary
    advice_list: list[str]


# ---------------------------------------------------------------------------
# TieredLearning — 分层学习建议
# 消费方: m6_tiered_learning.jinja2
# ---------------------------------------------------------------------------

class TieredLearningData(TypedDict, total=False):
    page_header: dict
    module: dict                        # {cards: {stage_judgement, student_suggestion, ...}}


# ---------------------------------------------------------------------------
# QuestionDetail — 逐题分析
# 消费方: m9_question_detail.jinja2
# ---------------------------------------------------------------------------

class QuestionPaper(TypedDict, total=False):
    paper_name: str
    wrong_questions: list[dict]
    correct_questions: list[dict]


class QuestionDetailData(TypedDict, total=False):
    total_count: int
    wrong_count: int
    correct_count: int
    papers: list[QuestionPaper]


# ---------------------------------------------------------------------------
# DataReliability — 数据可信度
# 消费方: m7_data_reliability.jinja2
# ---------------------------------------------------------------------------

class CoverageStats(TypedDict, total=False):
    total_questions: int
    total_questions_text: str
    l2_covered: int
    l2_covered_text: str
    l3_covered: int
    l3_total: int
    test_period: str


class DataReliabilityData(TypedDict, total=False):
    section_4_coverage: dict            # {stats: CoverageStats, data_insufficient: list}


# ---------------------------------------------------------------------------
# Appendix — 附录
# 消费方: m8_appendix.jinja2
# ---------------------------------------------------------------------------

class AppendixData(TypedDict, total=False):
    analysis_scope: dict
    difficulty: dict
    papers: dict                        # {total_papers, total_questions, items: list}
    metric_definitions: list[dict]


# ---------------------------------------------------------------------------
# Suggestion — 学习建议
# 消费方: m6_tiered_learning.jinja2
# ---------------------------------------------------------------------------

class SuggestionData(TypedDict, total=False):
    text: str
    summary: str
    sections: list


# ---------------------------------------------------------------------------
# CompositionDeep — 作文精讲（英语专属）
# 消费方: m10_composition.jinja2
# ---------------------------------------------------------------------------

class CompositionDeepData(TypedDict, total=False):
    enabled: bool
    score_overview: dict
    priority_fixes: list[str]
    topic_analysis: str
    content_analysis: str
    language_analysis: str
    organization_analysis: str
    weekly_suggestion: str
    reference_essay: str
    highlights_and_issues: list[dict]


# ---------------------------------------------------------------------------
# ReadingDeep — 阅读精讲（英语专属）
# 消费方: m11_reading_deep.jinja2
# ---------------------------------------------------------------------------

class ReadingDeepData(TypedDict, total=False):
    enabled: bool
    passage_overview: dict
    selection_reason: str
    overall_diagnosis: str
    question_analyses: list[dict]
    reading_strategies: list[str]
    three_day_plan: str
    encouragement: str


# ---------------------------------------------------------------------------
# PageVisibility — 模块可见性控制
# 消费方: report_master.jinja2
# ---------------------------------------------------------------------------

class PageVisibility(TypedDict, total=False):
    m5_city_compare: bool               # 默认 True（英语暂关）
    m10_composition: bool               # 默认 False
    m11_reading_deep: bool              # 默认 False
    show_teacher_supplement: bool       # 默认 False


# ---------------------------------------------------------------------------
# KeyFindings — 关键发现
# 消费方: m1_summary.jinja2
# ---------------------------------------------------------------------------

class KeyFinding(TypedDict, total=False):
    text: str
    priority: str
    category: str


# ===========================================================================
# RenderPayload — 模板消费的顶层合约
# ===========================================================================

class RenderPayload(TypedDict, total=False):
    """模板系统消费的统一数据合约。

    所有 adapter 的输出必须满足此合约。
    模板通过 context = dict(payload) 展开，直接访问顶层 key。
    """

    # --- 报告元信息 ---
    meta: RenderMeta

    # --- 封面 ---
    cover: CoverData

    # --- 诊断摘要 ---
    summary: SummaryData

    # --- 领域数据 ---
    domains: DomainsData

    # --- 核心短板 ---
    core_weakness: CoreWeaknessData

    # --- P0 突破项 ---
    breakthrough: BreakthroughData

    # --- 知识点钻取 ---
    kp_drill: KpDrillData

    # --- 城市考情 ---
    city_compare: CityCompareData

    # --- 分层学习 ---
    tiered_learning: TieredLearningData

    # --- 逐题分析 ---
    question_detail: QuestionDetailData

    # --- 数据可信度 ---
    data_reliability: DataReliabilityData

    # --- 附录 ---
    appendix: AppendixData

    # --- 学习建议 ---
    suggestion: SuggestionData

    # --- 关键发现 ---
    key_findings: list[KeyFinding]

    # --- 模块可见性 ---
    page_visibility: PageVisibility

    # --- 英语专属模块 ---
    composition_deep: CompositionDeepData
    reading_deep: ReadingDeepData

    # --- 英语专属模块（模板别名） ---
    m10: CompositionDeepData               # 模板用 m10 | default({}, true)
    m11: ReadingDeepData                   # 模板用 m11 | default({}, true)

    # --- 透传字段（适配器可能设置，模板不直接消费但 builder 需要）---
    section_2_domains: dict             # 英语 brief 需要的别名
    section_core_weakness: dict         # 英语 brief 需要的别名
    schema_version: str                 # 数据格式版本标识


# ===========================================================================
# Blueprint View-Models — learning_blueprint_builder 输出
# ===========================================================================

class BlueprintMeta(TypedDict, total=False):
    student_name: str
    grade: str
    subject_name: str
    city_name: str
    report_title: str
    target_score_text: str
    report_date: str
    report_id: str
    ability_map_title: str
    ability_map_aria: str
    ability_axis_label: str
    l1_label: str
    page1_label: str
    page2_label: str


class DiagnosticBlueprint(TypedDict, total=False):
    meta: BlueprintMeta
    headline: dict                      # {title, subtitle, slogan}
    profile: dict                       # 学生画像摘要
    domains: list                       # 领域能力轴数据
    shortlist: list                     # 短板优先列表
    diagnostic_drill_rows: list         # 钻取行
    city_focus: list                    # 城市聚焦
    stage_plan: dict                    # 阶段计划
    evidence: dict                      # 数据支撑
    confidence: dict                    # 可信度
    note: str                           # 业务说明
    footer: dict                        # 页脚


class ExecutionBlueprint(TypedDict, total=False):
    meta: BlueprintMeta
    headline: dict
    focus_paths: list                   # 聚焦路径
    execution_tasks: list               # 执行任务
    stage_plan: dict
    evidence: dict
    confidence: dict
    data_engine: dict                   # 数据引擎说明
    support_system: dict                # 支撑体系
    axis: dict                          # 阶段轴
    footer: dict


class BlueprintOutput(TypedDict):
    """build_learning_blueprints() 的返回类型"""
    diagnostic_blueprint: DiagnosticBlueprint
    execution_blueprint: ExecutionBlueprint
