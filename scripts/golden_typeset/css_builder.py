"""
css_builder.py -- PageLayout -> CSS
====================================
输出 margin-top + wrapper flexbox 居中。

每个 wrapper 通常有 2-3 个直接子元素（标题 + 内容卡）。
margin-top 作用于这些直接子元素。

密度策略:
  高密度 (content_ratio >= 0.6): flex-start, 内容靠上, 底部自然留白
  中密度 (0.4 <= ratio < 0.6):   center, 居中
  低密度 (ratio < 0.4):          center + 紧凑 padding (u_max=10mm)

溢出保护:
  scale < 1.0 时: 使用 CSS zoom 属性压缩 wrapper 布局尺寸 (Chromium 支持)
  zoom 影响布局盒模型，真正减少内容占用的页面高度，防止溢出到新页
"""
from __future__ import annotations
from typing import Dict
from . import WRAPPER_SELECTORS
from .math_func import PageLayout


def _justify_for_ratio(ratio: float) -> str:
    """根据密度选择 justify-content 值。"""
    if ratio >= 0.6:
        return "flex-start"
    return "center"


def build_css(layouts: Dict[str, PageLayout]) -> str:
    parts: list[str] = []
    parts.append("/* golden_typeset -- 数学排版引擎 */")

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
        justify = _justify_for_ratio(ratio)
        parts.append(f"  {sel} {{")
        parts.append(f"    min-height: 275mm;")
        parts.append(f"    display: flex;")
        parts.append(f"    flex-direction: column;")
        parts.append(f"    justify-content: {justify};")

        # 压缩时使用 zoom (影响布局尺寸, 防止溢出)
        if layout.scale < 1.0:
            parts.append(f"    /* scale={layout.scale:.4f} */")
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

    # 表格跨页表头重复 (P1-5)
    parts.append("")
    parts.append("/* golden_typeset -- 表格跨页安全 */")
    parts.append("@media print {")
    parts.append("  thead { display: table-header-group; }")
    parts.append("  tr { page-break-inside: avoid; }")
    parts.append("}")

    parts.append("")
    return "\n".join(parts)
