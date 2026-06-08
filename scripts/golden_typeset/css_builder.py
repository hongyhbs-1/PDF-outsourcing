"""
css_builder.py -- PageLayout -> CSS
====================================
输出 margin-top + wrapper flexbox 顶部阅读流。

每个 wrapper 通常有 2-3 个直接子元素（标题 + 内容卡）。
margin-top 作用于这些直接子元素。

密度策略:
  所有密度均保持 flex-start，保证章节标题从页首开始阅读。
  低密度 (ratio < 0.4) 仍在数学模型中使用紧凑 padding (u_max=10mm)，避免内容过散。

溢出保护:
  scale < 1.0 时: 使用 CSS zoom 属性压缩 wrapper 布局尺寸 (Chromium 支持)
  zoom 影响布局盒模型，真正减少内容占用的页面高度，防止溢出到新页

min-height 扣除:
  外层 .module-page::before 渐变条占 ~5px，min-height 需扣除 6px 避免溢出生成空白页
"""
from __future__ import annotations
from typing import Dict, Optional, TYPE_CHECKING
from . import WRAPPER_SELECTORS
from .math_func import PageLayout

if TYPE_CHECKING:
    from .layout_profile import LayoutProfile


# 部分报告页在标题下新增了“本页核心结论”后，DOM 直接子元素从
# “标题 + 内容卡”变为“标题 + 核心结论 + 内容卡”。黄金排版的通用
# gap 分配会把核心结论和内容卡整体向下推，导致同一套章节标签页
# 标题/归纳/主体位置不一致。这里用页级固定节奏覆盖这些页面的
# direct-child margin，只影响 PDF print typeset，不改变 HTML 结构。
# M3 is a multi-card CSS-grid report.  Chromium fragments a zoom-compressed grid
# poorly: the guide can be left alone on one PDF page while the whole grid jumps
# to the next page.  Let it paginate naturally, like the long M9 tables, so the
# first grid row can share the remaining space under the guide.
_NATURAL_PAGINATION_MODULES = {"m3", "m9"}

_COMPACT_CORE_RHYTHM_MM: dict[str, dict[int, float]] = {
    # P8：标题需要更靠近页眉，核心结论紧跟标题，主体卡片紧跟归纳。
    "m1": {1: 4.0, 2: 2.0, 3: 0.0},
    # P10：保留标题的参考下移位置，但取消隐藏 underline 与主体之间的
    # 大块黄金留白。
    "m2": {1: 18.0, 2: 0.0, 3: 4.0, 4: 3.0},
    # P9：六大领域页需要标题→核心结论→纵向主体卡片的参考节奏。
    "m4": {1: 15.0, 2: 4.0, 3: 4.0},
    # P10：城市考情页标题→归纳→主体模块使用紧凑节奏，避免归纳与主体之间出现大块空白。
    "m5": {1: 15.0, 2: 4.0},
    # P13/P14：长核心归纳页使用紧凑的标题→归纳→主体阅读流。
    "m6": {1: 15.0, 2: 3.0, 3: 3.0},
    "m7": {1: 16.0, 2: 3.0, 3: 3.0},  # ours: 与 m7=auto 配套（xc 的 4.0 耦合 m7=never，拒绝）
    # 英语深度页直接子元素规整为“标题 + 核心结论 + 主体”。保持紧凑，
    # 避免低密度页面被通用黄金间距大幅拉开，同时让系统 Chrome 进入
    # 与主报告页一致的 measured-wrapper 打印路径。
    "m10": {1: 6.0, 2: 3.0, 3: 3.0},
    "m11": {1: 6.0, 2: 3.0, 3: 3.0},
}


def _justify_for_ratio(ratio: float, layout_profile: Optional[LayoutProfile] = None) -> str:
    """保持章节页顶部阅读顺序，避免低密度页面内容垂直居中下坠。

    When layout_profile is provided with page_strategy == "center",
    allow vertical centering (useful for sparse content pages).
    """
    if layout_profile and layout_profile.page_strategy == "center":
        return "center"
    return "flex-start"


def build_css(layouts: Dict[str, PageLayout],
               layout_profile: Optional[LayoutProfile] = None) -> str:
    parts: list[str] = []
    parts.append("/* golden_typeset -- 数学排版引擎 */")

    # Inject :root CSS variables from LayoutProfile when provided
    if layout_profile is not None:
        lp = layout_profile
        parts.append("")
        parts.append("/* golden_typeset -- LayoutProfile variables */")
        parts.append(":root {")
        parts.append(f"  --typography-scale: {lp.typography_scale:.2f};")
        parts.append(f"  --padding-scale: {lp.padding_scale:.2f};")
        parts.append(f"  --grid-columns: {lp.grid_columns};")
        parts.append(f"  --grid-gap: {lp.grid_gap_mm:.1f}mm;")
        for var_name, var_value in lp.css_overrides.items():
            if var_name not in ("--typography-scale", "--padding-scale", "--grid-columns", "--grid-gap"):
                parts.append(f"  {var_name}: {var_value};")
        parts.append("}")

    # LayoutProfile-driven typography adjustments (consume the CSS variables)
    if layout_profile is not None:
        lp = layout_profile
        parts.append("")
        parts.append("/* golden_typeset -- LayoutProfile-driven typography adjustments */")
        parts.append("@media print {")
        # typography_scale controls body font-size across all module pages
        if lp.typography_scale != 1.0:
            parts.append(f"  .module-page {{ font-size: calc(var(--vh-body-font-size) * {lp.typography_scale:.2f}); }}")
        # padding_scale controls card padding and gap tokens
        if lp.padding_scale != 1.0:
            parts.append(f"  .module-page {{ --vh-card-padding: calc(10px * {lp.padding_scale:.2f}) calc(12px * {lp.padding_scale:.2f}); }}")
            parts.append(f"  .module-page {{ --vh-gap-md: calc(10px * {lp.padding_scale:.2f}); }}")
        # Per-module grid_columns overrides from module_overrides
        _GRID_SELECTORS = {"m3": ".m3-kp-drill__panels"}
        if lp.module_overrides:
            for _mod_id, overrides in lp.module_overrides.items():
                if "grid_columns" in overrides:
                    sel = _GRID_SELECTORS.get(_mod_id)
                    if sel:
                        parts.append(f"  {sel} {{ grid-template-columns: repeat({overrides['grid_columns']}, 1fr); }}")
        parts.append("}")

    for mod_id, layout in layouts.items():
        sel = WRAPPER_SELECTORS.get(mod_id)
        if not sel or not layout.blocks:
            continue

        ratio = layout.content_ratio
        tag = "compressed" if layout.scale < 1.0 else "golden"
        density_tag = "high" if ratio >= 0.6 else ("low" if ratio < 0.4 else "mid")
        parts.append("")
        parts.append(f"/* [{mod_id}] content={layout.content_h}mm "
                     f"gaps={layout.gaps_h}mm top={layout.top_pad}mm "
                     f"bottom={layout.bottom_pad}mm u={layout.unit_u}mm "
                     f"ratio={ratio:.2f} {tag}/{density_tag} */")
        parts.append("@media print {")

        # Wrapper: min-height + flex + 自适应 justify-content
        justify = _justify_for_ratio(ratio, layout_profile=layout_profile)
        parts.append(f"  {sel} {{")
        # 低密度模块 (< 0.5) 不设 min-height，让内容自然高度决定页面占用，
        # 允许与前一个模块共享同一页（配合 break-before: auto）。
        # 高密度模块保持 min-height 确保黄金间距排版有空间。
        if ratio >= 0.50:
            parts.append(f"    min-height: calc(275mm - 6px);")
        else:
            parts.append(f"    /* ratio={ratio:.2f} < 0.5: no min-height, natural height */")
        parts.append(f"    display: flex;")
        parts.append(f"    flex-direction: column;")
        parts.append(f"    justify-content: {justify};")

        # 压缩时使用 zoom (影响布局尺寸, 防止溢出)。
        # M9 是逐题长表，必须自然分页；若按整页高度压缩 wrapper，
        # Chromium 会把 100+ 行表格缩成一页，导致 PDF 正文字号接近不可读。
        if layout.scale < 1.0:
            parts.append(f"    /* scale={layout.scale:.4f} */")
            if mod_id in _NATURAL_PAGINATION_MODULES:
                parts.append("    /* natural-pagination: zoom intentionally disabled */")
            else:
                parts.append(f"    zoom: {layout.scale:.4f};")

        parts.append("  }")

        # 每个直接子元素的 margin-top
        for i, blk in enumerate(layout.blocks):
            parts.append(f"  /* block: {blk.key} */")
            parts.append(f"  {sel} > :nth-child({i+1}) {{")
            parts.append(f"    margin-top: {blk.gap:.2f}mm;")
            parts.append("  }")

        parts.append(f"  {sel} > :last-child {{ margin-bottom: 0; }}")
        parts.append("}")

    compact_modules = [mid for mid in layouts if mid in _COMPACT_CORE_RHYTHM_MM]
    if compact_modules:
        parts.append("")
        parts.append("/* golden_typeset -- reference-aligned compact core-conclusion rhythm */")
        parts.append("@media print {")
        for mod_id in compact_modules:
            sel = WRAPPER_SELECTORS.get(mod_id)
            if not sel:
                continue
            for child_index, margin_mm in _COMPACT_CORE_RHYTHM_MM[mod_id].items():
                parts.append(f"  {sel} > :nth-child({child_index}) {{")
                parts.append(f"    margin-top: {margin_mm:.2f}mm;")
                parts.append("  }")
        parts.append("}")

    # 表格跨页表头重复 (P1-5)
    parts.append("")
    parts.append("/* golden_typeset -- 表格跨页安全 */")
    parts.append("@media print {")
    parts.append("  thead { display: table-header-group; }")
    parts.append("  tr { page-break-inside: avoid; }")
    parts.append("}")

    # GOLDEN_RATIOS: 供 _PREFLIGHT_JS 读取各模块 ratio 用于动态分页
    ratio_parts = []
    for mod_id, layout in layouts.items():
        ratio_parts.append(f"{mod_id}:{layout.content_ratio:.2f}")
    if ratio_parts:
        parts.append(f"/* GOLDEN_RATIOS: {','.join(ratio_parts)} */")

    parts.append("")
    return "\n".join(parts)
