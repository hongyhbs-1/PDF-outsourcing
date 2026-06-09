#!/usr/bin/env python3
"""
M9 逐题分析明细 — 数据驱动的分页拆分器。

职责：
  has_m9_detail(payload) → bool
  should_split_m9(payload) → bool
  build_m9_split_pages(payload) → list[dict]

用法：
  from m9_splitter import has_m9_detail, build_m9_split_pages
"""

from __future__ import annotations

from dataclasses import dataclass


# ---------------------------------------------------------------------------
# 阈值配置（T017: 参数化，默认值基于 T016 合并时的经验常量）
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class M9SplitConfig:
    """M9 分页拆分器阈值配置。

    所有预算值单位为「行权重」（非物理行数），由 _row_weight 估算。
    """

    # 单页预算：超过此值触发拆分
    single_page_budget: float = 24.0
    # 拆分后首页预算（含统计概览，略小）
    first_page_budget: float = 20.0
    # 续页预算
    continued_page_budget: float = 34.0
    # 新试卷起始页预算
    new_paper_page_budget: float = 30.0
    # 每 chunk 行数硬上限
    max_wrong_rows: int = 22
    max_correct_rows: int = 40
    # 行权重基础与上限
    wrong_base: float = 1.20
    correct_base: float = 0.85
    wrong_cap: float = 2.90
    correct_cap: float = 1.60


# 模块级默认实例（向后兼容：不传 config 时使用）
_DEFAULT_CONFIG = M9SplitConfig()


# ---------------------------------------------------------------------------
# 公共 API
# ---------------------------------------------------------------------------


def has_m9_detail(payload: dict) -> bool:
    """判断 payload 是否包含有效的逐题分析数据。"""
    qd = payload.get("question_detail") or {}
    papers = qd.get("papers") or []
    total = qd.get("total_count", 0) or 0
    return len(papers) > 0 and total > 0


def should_split_m9(payload: dict, config: M9SplitConfig | None = None) -> bool:
    """判断 M9 是否需要拆分。"""
    if not has_m9_detail(payload):
        return False
    cfg = config or _DEFAULT_CONFIG
    total_weight = _estimate_total_weight(payload, cfg)
    return total_weight > cfg.single_page_budget


def build_m9_split_pages(
    payload: dict, config: M9SplitConfig | None = None
) -> list[dict]:
    """将 M9 数据拆分为多个页面条目。

    返回空列表表示不需要拆分（由模板用单页逻辑渲染）。
    """
    cfg = config or _DEFAULT_CONFIG
    if not should_split_m9(payload, cfg):
        return []

    qd = payload.get("question_detail") or {}
    papers = qd.get("papers") or []
    total_count = qd.get("total_count", 0) or 0
    wrong_count = qd.get("wrong_count", 0) or 0

    chunks = _build_chunks(papers, cfg)
    if len(chunks) <= 1:
        return []

    # 组装 split pages
    pages = []
    for i, chunk_group in enumerate(chunks):
        pages.append({
            "part_index": i + 1,
            "part_count": len(chunks),
            "is_first": i == 0,
            "blocks": chunk_group,
        })

    # 添加统计信息给第一页
    if pages:
        pages[0]["stats"] = {
            "total_count": total_count,
            "wrong_count": wrong_count,
            "paper_count": len(papers),
        }

    return pages


# ---------------------------------------------------------------------------
# 权重估算
# ---------------------------------------------------------------------------


def _row_weight(row: dict, section_type: str, cfg: M9SplitConfig) -> float:
    """估算单行的显示权重。"""
    weight = cfg.wrong_base if section_type == "wrong" else cfg.correct_base

    # 知识点文本长度
    kp_text = " ".join([
        str(row.get("kp_name") or ""),
        str(row.get("knowledge_point") or ""),
    ])
    if len(kp_text) > 24:
        weight += 0.20
    if len(kp_text) > 48:
        weight += 0.25

    # 薄弱标签
    tags = row.get("weakness_tags") or []
    if tags:
        weight += 0.35
        tag_text = " ".join(map(str, tags))
        if len(tag_text) > 32:
            weight += 0.25

    # 分析文本
    analysis = " ".join([
        str(row.get("error_analysis") or ""),
        str(row.get("key_points") or ""),
    ])
    if analysis:
        weight += 0.70
        if len(analysis) > 40:
            weight += 0.35
        if len(analysis) > 80:
            weight += 0.45

    cap = cfg.wrong_cap if section_type == "wrong" else cfg.correct_cap
    return min(weight, cap)


def _estimate_total_weight(payload: dict, cfg: M9SplitConfig) -> float:
    """估算整个 M9 的总权重。"""
    qd = payload.get("question_detail") or {}
    papers = qd.get("papers") or []
    total = 0.0
    for paper in papers:
        for q in paper.get("wrong_questions") or []:
            total += _row_weight(q, "wrong", cfg)
        for q in paper.get("correct_questions") or []:
            total += _row_weight(q, "correct", cfg)
    return total


# ---------------------------------------------------------------------------
# Chunk 构建
# ---------------------------------------------------------------------------


def _build_chunks(papers: list[dict], cfg: M9SplitConfig) -> list[list[dict]]:
    """将试卷数据按预算拆分为 chunk 组。"""
    chunks: list[list[dict]] = []
    current_blocks: list[dict] = []
    current_budget = cfg.first_page_budget

    for pi, paper in enumerate(papers):
        paper_name = paper.get("paper_name", f"试卷{pi + 1}")
        paper_total = paper.get("total", 0)
        started_new_paper = False

        # 错题
        wrong = paper.get("wrong_questions") or []
        if wrong:
            wrong_meta = _detect_meta(wrong)
            for start in range(0, len(wrong), cfg.max_wrong_rows):
                batch = wrong[start:start + cfg.max_wrong_rows]
                block = {
                    "paper_index": pi,
                    "paper_name": paper_name,
                    "paper_total": paper_total,
                    "section_type": "wrong",
                    "section_label": f"错题诊断（{len(batch)} 题）",
                    "questions": batch,
                    "has_weakness": wrong_meta["has_weakness"],
                    "has_analysis": wrong_meta["has_analysis"],
                }
                block_weight = sum(_row_weight(q, "wrong", cfg) for q in batch)

                # 新试卷：如果当前页已有内容，从新页开始
                if not started_new_paper and current_blocks and pi > 0:
                    chunks.append(current_blocks)
                    current_blocks = []
                    current_budget = cfg.new_paper_page_budget
                    started_new_paper = True

                if block_weight > current_budget and current_blocks:
                    chunks.append(current_blocks)
                    current_blocks = []
                    current_budget = cfg.continued_page_budget

                current_blocks.append(block)
                current_budget -= block_weight

        # 正确题
        correct = paper.get("correct_questions") or []
        if correct:
            for start in range(0, len(correct), cfg.max_correct_rows):
                batch = correct[start:start + cfg.max_correct_rows]
                block = {
                    "paper_index": pi,
                    "paper_name": paper_name,
                    "paper_total": paper_total,
                    "section_type": "correct",
                    "section_label": f"正确题目（{len(batch)} 题）",
                    "questions": batch,
                }
                block_weight = sum(_row_weight(q, "correct", cfg) for q in batch)

                if block_weight > current_budget and current_blocks:
                    chunks.append(current_blocks)
                    current_blocks = []
                    current_budget = cfg.continued_page_budget

                current_blocks.append(block)
                current_budget -= block_weight

    if current_blocks:
        chunks.append(current_blocks)

    return chunks


def _detect_meta(questions: list[dict]) -> dict:
    """检测题组是否有 weakness_tags 和 analysis 字段。"""
    has_weakness = False
    has_analysis = False
    for q in questions:
        if q.get("weakness_tags"):
            has_weakness = True
        if q.get("error_analysis") or q.get("key_points"):
            has_analysis = True
        if has_weakness and has_analysis:
            break
    return {"has_weakness": has_weakness, "has_analysis": has_analysis}
