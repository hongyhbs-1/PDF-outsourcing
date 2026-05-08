"""
math_func.py — 黄金比例统一排版模型
=====================================
纯数学，零 DOM 依赖。

核心思想:
  用一个基本单元 u 同时决定顶部留白、容器间隙、底部留白，
  三者均处于 φ 的幂次体系，形成全局黄金韵律。

数学模型:
  设 n 个容器，n-1 个间隙。
  令基本单元 u 满足:
    M_top    = φ² × u          (顶部留白)
    inter[k] = φ^(k+1) × u     (第 k 个间隙, k=0..n-2)
    M_bottom = u               (底部留白)

  总留白 = (φ² + Σ_{k=1}^{n-1} φ^k + 1) × u = S(n) × u
  其中 S(n) = φ² + (φ - φ^n)/(1-φ) + 1  (几何级数求和)

  若总留白 > remaining:
    u = remaining / S(n)       (等比缩小)
  否则:
    u 取标准值, 居中处理

  方向: inter[k] 从上到下递减 (大间距在上, 小间距在下),
  符合阅读节奏 (标题后大留白, 底部紧凑).

V(f, C, F, W)  → 内容自然高度 (mm)
G(R, n)        → 黄金空隙序列 [mm]
L(heights, H)  → PageLayout
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List

PHI = (1.0 + math.sqrt(5.0)) / 2.0

# A4 画布 (mm)
CANVAS_H = 297.0 - 12.0 - 10.0   # 275mm
CANVAS_W = 210.0 - 20.0 - 20.0   # 170mm

# 字号 (mm, 1px ≈ 0.35mm)
F_BODY  = 3.5
F_SMALL = 3.0
F_TABLE = 3.2
LR = 1.6


def content_height(font_mm: float, char_count: float, field_count: float,
                   width_mm: float = CANVAS_W - 14.0, lr: float = LR) -> float:
    """V(f, C, F, W) → 自然高度 mm"""
    if font_mm <= 0 or width_mm <= 0:
        return 20.0
    n = width_mm / font_mm
    lines = math.ceil(char_count / n) if char_count > 0 else 0
    text_h = lines * font_mm * lr
    field_h = field_count * (font_mm * lr + 2.0)
    return 8.0 + text_h + field_h + 12.0


def golden_gaps(remaining: float, n: int) -> List[float]:
    """G(R, n) → [g₀..gₙ], 长度 n+1: [top_pad, inter_0, ..., inter_{n-2}, bottom_pad]

    全部间距处于 φ 的幂次体系:
      top_pad    = φ² × u
      inter[k]   = φ^(n-k) × u   (上大下小, 符合阅读节奏)
      bottom_pad = u

    Σ = u × (φ² + Σ_{k=1}^{n-1} φ^k + 1) = u × S(n)
    u = remaining / S(n)
    """
    if remaining <= 0 or n <= 0:
        return [0.0] * (n + 1)
    if n == 1:
        # 单容器也遵守黄金体系: top = φ²×u, bottom = u
        # φ² + 1 = φ² + 1 ≈ 3.618
        s = PHI * PHI + 1.0
        u = remaining / s
        return [PHI * PHI * u, u]

    # 多容器: top + (n-1) 个 inter + bottom
    # 权重序列: top=φ², inter[k]=φ^(n-k), bottom=1
    # inter 从大到小: φ^(n-1), φ^(n-2), ..., φ^1
    weights = [PHI * PHI]  # top
    for k in range(n - 1):
        weights.append(PHI ** (n - k))  # inter: φ^n, φ^(n-1), ..., φ^2
    weights.append(1.0)  # bottom

    s = sum(weights)
    u = remaining / s
    return [w * u for w in weights]


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
    unit_u: float       # 基本单元 u (用于验证)


def layout_page(heights: List[tuple[str, float]],
                page_h: float = CANVAS_H) -> PageLayout:
    """L(heights, H) → PageLayout

    策略:
      1. 内容 > H: 等比压缩, 无硬上限
      2. 内容 ≤ H: 黄金统一排版
         - 用基本单元 u 同时决定 top/inter/bottom
         - top = φ²×u, inter[k] = φ^(n-k)×u, bottom = u
         - 无魔术系数, 全部由 φ 的幂次统一
    """
    keys = [t[0] for t in heights]
    hs = [t[1] for t in heights]
    n = len(hs)
    if n == 0:
        return PageLayout([], 0, 0, 0, page_h, 1.0, 0.0)

    total = sum(hs)
    scale = 1.0

    # 溢出 → 等比压缩
    if total > page_h:
        scale = (page_h * 0.95) / total
        hs = [h * scale for h in hs]
        total = sum(hs)

    remaining = page_h - total

    # 黄金统一间距
    gaps_raw = golden_gaps(remaining, n)
    # gaps_raw = [top_pad, inter_0, ..., inter_{n-2}, bottom_pad]
    top_pad = gaps_raw[0]
    bottom_pad = gaps_raw[-1]
    # 容器 margin-top: 第一个 = top_pad, 后续 = inter[i]
    inter = gaps_raw[1:-1]
    gaps = [top_pad] + inter

    # 定位
    y = 0.0
    blocks = []
    for i in range(n):
        y += gaps[i]
        blocks.append(Block(key=keys[i], h=round(hs[i], 2),
                            gap=round(gaps[i], 2), y=round(y, 2)))
        y += hs[i]

    # 基本单元 u (用于验证)
    unit_u = bottom_pad if bottom_pad > 0 else 0.0

    return PageLayout(blocks=blocks, content_h=round(total, 2),
                      gaps_h=round(sum(gaps), 2),
                      top_pad=round(top_pad, 2),
                      bottom_pad=round(bottom_pad, 2),
                      scale=round(scale, 4),
                      unit_u=round(unit_u, 4))
