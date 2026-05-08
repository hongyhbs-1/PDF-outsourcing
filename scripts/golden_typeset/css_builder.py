"""
css_builder.py — PageLayout → CSS
==================================
只输出 margin-top, 不改变 display/position/overflow。

策略:
  - 不注入 flexbox (避免和原始 CSS 冲突)
  - 不注入 min-height/max-height (页面由 @page 决定)
  - 只用 margin-top 控制间距:
    nth-child(1): margin-top = φ²×u (顶部留白)
    nth-child(2..n): margin-top = φ^(n-k)×u (黄金间距, 上大下小)
"""
from __future__ import annotations
from typing import Dict
from .math_func import PageLayout

WRAPPER_SELECTORS = {
    "m1": "#toc-m1 > .m1-report-page",
    "m2": "#toc-m2 > .m2-core-weakness-module",
    "m3": "#toc-m3 > .m3-kp-drill",
    "m4": "#toc-m4 > section.m4-module-domains",
    "m5": "#toc-m5 > .m5-city-compare",
    "m6": "#toc-m6 > .m6-page",
    "m7": "#toc-m7 > .m7-data-reliability",
    "m9": "#toc-m9 > .m9-page",
}


def build_css(layouts: Dict[str, PageLayout]) -> str:
    parts: list[str] = []
    parts.append("/* golden_typeset — 数学排版引擎 */")

    for mod_id, layout in layouts.items():
        sel = WRAPPER_SELECTORS.get(mod_id)
        if not sel or not layout.blocks:
            continue

        tag = "compressed" if layout.scale < 1.0 else "golden"
        parts.append("")
        parts.append(f"/* [{mod_id}] content={layout.content_h}mm "
                     f"gaps={layout.gaps_h}mm top={layout.top_pad}mm "
                     f"bottom={layout.bottom_pad}mm u={layout.unit_u}mm {tag} */")
        parts.append("@media print {")

        for i, blk in enumerate(layout.blocks):
            parts.append(f"  {sel} > :nth-child({i+1}) {{")
            parts.append(f"    margin-top: {blk.gap:.2f}mm;")
            parts.append("  }")

        parts.append(f"  {sel} > :last-child {{ margin-bottom: 0; }}")
        parts.append("}")

    parts.append("")
    return "\n".join(parts)
