# Field Mapping

This document maps RenderPayload fields to blueprint fill points.

## Page 1: Student Diagnostic Panorama

| Fill point | View model path | RenderPayload source | Fallback |
|---|---|---|---|
| Student name | `diagnostic_blueprint.meta.student_name` | `meta.student_display_name` | `学生` |
| Grade | `diagnostic_blueprint.meta.grade` | `meta.grade` | `—` |
| Subject | `diagnostic_blueprint.meta.subject_name` | `meta.subject_name` | `—` |
| City | `diagnostic_blueprint.profile.city_name` | `meta.city_name`, `cover.cover_meta.city_name`, `cover.cover_meta.city` | `—` |
| Report title | `diagnostic_blueprint.meta.report_title` | `meta.report_title`, `meta.report_name` | `学情诊断报告` |
| Target score | `diagnostic_blueprint.meta.target_score_text` | `summary.target_score_text`, `meta.target_score` | `—` |
| Current accuracy | `diagnostic_blueprint.profile.current_accuracy_text` | `summary.current_accuracy_text`, `summary.current_accuracy` | `—` |
| Target accuracy | `diagnostic_blueprint.profile.target_accuracy_text` | `summary.target_accuracy_text`, `summary.target_accuracy`, `meta.target_accuracy` | `—` |
| Gap to target | `diagnostic_blueprint.profile.delta_text` | `summary.current_delta_text` | `—` |
| Learning stage | `diagnostic_blueprint.profile.stage_name` | `tiered_learning.module.cards.stage_judgement.current.stage_name` | `待确认` |
| Stage hint | `diagnostic_blueprint.profile.stage_hint` | `tiered_learning.module.cards.stage_judgement.current.position_hint` | `根据数据持续更新` |
| Focus domains | `diagnostic_blueprint.profile.focus_domains_text` | derived from shortlist domains | `待补测` |
| Domain nodes | `diagnostic_blueprint.domains[]` | `kp_drill.domain_panels`, `domains.domain_items` | Math six-domain skeleton |
| Shortlist | `diagnostic_blueprint.shortlist[]` | `core_weakness.items`; fallback `city_compare.overlap_items` | 高频考点补测清单 |
| Evidence paper count | `diagnostic_blueprint.evidence.paper_count` | `cover.cover_meta.paper_count`, `appendix.papers.total_papers` | `—` |
| Valid questions | `diagnostic_blueprint.evidence.valid_questions` | `cover.cover_meta.display_question_count`, `appendix.papers.total_questions` | `—` |
| Expanded questions | `diagnostic_blueprint.evidence.expanded_questions` | `question_detail.total_count`, `cover.cover_meta.total_questions` | `—` |
| L2 coverage | `diagnostic_blueprint.evidence.l2_coverage_text` | `data_reliability.section_4_coverage.stats.l2_covered_text` | computed from l2_covered/l2_total |
| L3 coverage | `diagnostic_blueprint.evidence.l3_coverage_text` | `data_reliability.section_4_coverage.stats.l3_covered_text` | computed from l3_covered/l3_total |
| Confidence | `diagnostic_blueprint.confidence.level` | `data_reliability.conclusion.total_level` | `未知` |

## Page 2: Tutoring Execution and Tracking

| Fill point | View model path | RenderPayload source | Fallback |
|---|---|---|---|
| Knowledge drill rows | `execution_blueprint.focus_paths[]` | `core_weakness.items`, `city_compare.overlap_items`, `data_reliability...uncovered_core.items` | Generated from top city focus |
| Stage plan | `execution_blueprint.stage_plan` | derived from current/target accuracy; may be replaced by custom plan | Conservative 3-stage plan |
| Data engine paper count | `execution_blueprint.data_engine.paper_count` | same evidence builder | `—` |
| Data engine modules | `execution_blueprint.data_engine.domain_modules` | `data_reliability.section_4_coverage.stats.l2_total` | `—` |
| Data period | `execution_blueprint.data_engine.period` | `data_reliability.section_4_coverage.stats.test_period` | `—` |
| Reliability stars | `execution_blueprint.data_engine.stars` | derived from `data_reliability.conclusion.total_level` | 3 |
| Support system text | `execution_blueprint.support_system` | static product logic | fixed |
| Active execution stage | `execution_blueprint.axis.active_stage` | derived from report type, reliability, and available weakness list | `AI诊断分析` |
