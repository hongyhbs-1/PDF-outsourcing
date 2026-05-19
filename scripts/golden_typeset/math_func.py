"""
math_func.py -- 黄金比例排版模型
===================================
纯数学, 零 DOM 依赖。

核心模型:
  n 个容器, n-1 个容器间间距。
  间距序列使用严格 phi 增长 (golden_gaps):

  基本单位 u 决定一切:
    top_pad    = u                (顶部留白, 与底部对称)
    inter[k]   = u * phi^k       (第 k 个间距, k=0..n-2)
    bottom_pad = u                (底部留白, 与顶部对称)

  相邻间距比: inter[k+1]/inter[k] = phi  (严格黄金比例)

  总留白 = u * (2 + sum(phi^k, k=0..num_inter-1))

  u = remaining / (2 + weighted_sum)
  u 受 u_max 约束: 紧凑模式 10mm, 正常模式 15mm

V(f, C, F, W)  -> 内容自然高度 (mm)
G(R, n)        -> 黄金间距序列 [mm]
L(heights, H)  -> PageLayout
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List

PHI = (1.0 + math.sqrt(5.0)) / 2.0  # 1.6180339887

# A4 画布 (mm)
CANVAS_H = 297.0 - 12.0 - 10.0   # 275mm
CANVAS_W = 210.0 - 20.0 - 20.0   # 170mm

# 字号 (mm, 1px ~ 0.35mm)
F_BODY  = 3.5
F_SMALL = 3.0
F_TABLE = 3.2
LR = 1.6

# Row-height constants (mm)
ROW_TABLE: float = 7.0       # standard table row
ROW_ANALYSIS: float = 12.0   # table row with analysis text
ROW_CHECKLIST: float = 8.0   # checklist / bullet item


def content_height(font_mm: float, char_count: float, field_count: float,
                   width_mm: float = CANVAS_W - 14.0, lr: float = LR) -> float:
    """V(f, C, F, W) -> 自然高度 mm

    根据字号、字符数、字段数估算内容的自然高度。
    """
    if font_mm <= 0 or width_mm <= 0:
        return 20.0
    n = width_mm / font_mm
    lines = math.ceil(char_count / n) if char_count > 0 else 0
    text_h = lines * font_mm * lr
    field_h = field_count * (font_mm * lr + 2.0)
    return 8.0 + text_h + field_h + 12.0


def golden_gaps(remaining: float, n: int,
                content_ratio: float = 1.0) -> List[float]:
    """G(R, n) -> [top_pad, inter_0, ..., inter_{n-2}, bottom_pad]

    间距序列使用严格 phi 增长:
      top_pad    = u
      inter[k]   = u * phi^k       (k = 0, 1, ..., n-2)
      bottom_pad = u

    相邻间距比: inter[k+1]/inter[k] = phi  (严格黄金比例, 可验证)

    总留白 = u * (2 + sum(phi^k, k=0..num_inter-1))

    content_ratio < 0.4 时启用紧凑模式: u_max = 10mm
    否则 u_max = 15mm
    """
    if remaining <= 0 or n <= 0:
        return [0.0] * max(n + 1, 1)

    if n == 1:
        # 单容器: top_pad = bottom_pad = remaining/2, 但受 u_max 限制
        u_max = 10.0 if content_ratio < 0.4 else 15.0
        half = min(remaining / 2.0, u_max)
        return [half, half]

    # 多容器: n-1 个容器间间距
    num_inter = n - 1

    # 加权和: sum(phi^k, k=0..num_inter-1)
    geo_sum = sum(PHI ** k for k in range(num_inter))
    total_weight = 2.0 + geo_sum

    # u_max: 紧凑模式 vs 正常模式
    u_max = 10.0 if content_ratio < 0.4 else 15.0
    u = min(u_max, remaining / total_weight)

    # top_pad = u
    # inter[k] = u * phi^k
    # bottom_pad = u
    result = [u]  # top_pad
    for k in range(num_inter):
        result.append(u * PHI ** k)
    result.append(u)  # bottom_pad

    return result


@dataclass
class Block:
    key: str
    h: float
    gap: float = 0.0   # margin-top 值
    y: float = 0.0


@dataclass
class PageLayout:
    blocks: List[Block]
    content_h: float
    gaps_h: float
    top_pad: float      # 居中用的顶部留白
    bottom_pad: float   # 底部留白
    scale: float
    unit_u: float       # 基本单位 u (用于验证)
    content_ratio: float  # total_content / page_h (密度比, 用于 CSS 策略)


def layout_page(heights: List[tuple[str, float]],
                page_h: float = CANVAS_H) -> PageLayout:
    """L(heights, H) -> PageLayout

    策略:
      1. 内容 > H: 等比压缩 scale = (H * 0.95) / total, 无硬上限
      2. 接近溢出 (ratio >= 0.85): 预防性压缩, 确保内容+间距 <= H
      3. 内容 <= H: 黄金间距排版
         - top_pad = bottom_pad = u  (垂直居中)
         - inter[k] = u * phi^k      (严格黄金比例增长)
         - u 受 u_max 约束 (紧凑/正常模式)
      4. content_ratio < 0.4: 紧凑模式, u_max=10mm
         content_ratio >= 0.6: 高密度, 靠上排列
    """
    keys = [t[0] for t in heights]
    hs = [t[1] for t in heights]
    n = len(hs)
    if n == 0:
        return PageLayout([], 0, 0, 0, page_h, 1.0, 0.0, 0.0)

    total = sum(hs)
    scale = 1.0

    # 溢出 -> 等比压缩
    if total > page_h:
        scale = (page_h * 0.95) / total
        hs = [h * scale for h in hs]
        total = sum(hs)
    elif total >= page_h * 0.80:
        # 接近溢出时先按实际 CSS 间距检查是否真的需要压缩。
        # 注意 CSS 生成阶段只把 top_pad 和 inter gaps 写成各直接子元素
        # 的 margin-top，并没有给 wrapper 写 bottom_pad。若这里把 bottom_pad
        # 也计入，会在内容实际可放下时误触发 zoom；Windows Chrome 对 dense
        # print wrapper 的 zoom 更敏感，可能直接导致 Page.printToPDF 失败。
        raw_ratio = total / page_h
        gaps_preview = golden_gaps(page_h - total, n, content_ratio=raw_ratio)
        applied_gaps_total = sum(gaps_preview[:-1])
        if total + applied_gaps_total > page_h:
            # 实际写入 CSS 的间距 + 内容超过页面 -> 压缩
            target = page_h * 0.90
            scale = target / (total + applied_gaps_total)
            scale = max(scale, 0.65)  # 不要压缩太多
            hs = [h * scale for h in hs]
            total = sum(hs)

    # 密度比 (基于压缩后高度)
    content_ratio = total / page_h

    remaining = page_h - total

    # 黄金间距 (传入 content_ratio 以选择 u_max)
    gaps_raw = golden_gaps(remaining, n, content_ratio=content_ratio)
    # gaps_raw = [top_pad, inter_0, ..., inter_{n-2}, bottom_pad]
    top_pad = gaps_raw[0]
    bottom_pad = gaps_raw[-1]
    inter = gaps_raw[1:-1]

    # 容器 margin-top: 第一个 = top_pad, 后续 = inter[i]
    gaps = [top_pad] + inter

    # 定位
    y = 0.0
    blocks = []
    for i in range(n):
        y += gaps[i]
        blocks.append(Block(key=keys[i], h=round(hs[i], 2),
                            gap=round(gaps[i], 2), y=round(y, 2)))
        y += hs[i]

    # 基本单位 u = top_pad = bottom_pad
    unit_u = top_pad

    return PageLayout(blocks=blocks, content_h=round(total, 2),
                      gaps_h=round(sum(gaps), 2),
                      top_pad=round(top_pad, 2),
                      bottom_pad=round(bottom_pad, 2),
                      scale=round(scale, 4),
                      unit_u=round(unit_u, 4),
                      content_ratio=round(content_ratio, 4))
