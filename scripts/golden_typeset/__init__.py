"""
golden_typeset — 数学公式驱动的 PDF 排版引擎
=============================================
整页作为数学优化问题: 画布 275×170mm + 内容体积 → 求解最优布局。

策略:
  内容 ≤ 画布: 黄金间距(gₖ₊₁/gₖ=φ)填满页面
  内容 > 画布: 等比压缩, 强制单页
  CSS 兜底:    flexbox justify-content:center 安全网
"""

# 共享常量: 各模块 wrapper 的 CSS 选择器
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
