# T005 Claude 独立方案 — JSON 数据包第一公民架构重设计

> **作者**: Claude (执行者) | **协调者**: Hermes (xc)
> **日期**: 2026-06-03 | **状态**: 独立分析，待联合决策

---

## 1. 执行摘要

经过对 13 个关键文件的完整阅读（render_standalone.py 1029 行、golden_typeset/ 4 个模块、22 个 jinja2 模板、3 个样本 JSON、25 个 CSS 文件、report-data-contract.md 审计文档），我的核心结论：

**Hermes 的 4 阶段方向正确，但阶段顺序和实施细节需要调整。最大的风险是跳过了"合约发现"直接建模。**

---

## 2. 对 Hermes 4 阶段方案的逐条评价

### 阶段 1 — 数据合约层 (Pydantic + Adapters + Registry)

**评价: 方向对，但有两个设计问题**

**OK 的部分:**
- Adapters 思路完全正确。数学 JSON (28 个顶层 key，扁平结构) 已经是模板的原生数据格式，English JSON (9 个顶层 key，sections 驱动) 需要完整适配
- Registry 模式合理，可以在运行时根据 `schema_version` + `meta.render_template` 选择适配器
- IdentityAdapter 对数学数据的处理是正确的 — 数学 JSON 就是 ground truth

**问题 1: Pydantic 模型时机过早**

当前的模板数据合约是隐式的 — 散布在 22 个 jinja2 模板中。`report-data-contract.md` 记录了关键路径但不是完整的合约定义。直接写 Pydantic 模型会：
- 把当前的隐式耦合固化为显式耦合，但合约边界可能不准确
- 数学 JSON 有 28 个顶层 key，其中 `_config_features`、`_internal`、`_internal_s3`、`_raw` 是内部数据，模板不需要。Pydantic 模型需要区分"合约字段"和"透传字段"

**建议**: 先定义 **TypedDict 或 Protocol**（轻量级合约标注），而非完整的 Pydantic BaseModel。等合约稳定后再升级为 Pydantic 验证。这样做的理由是：当前项目是单进程渲染脚本，不需要 Pydantic 的序列化/反序列化能力。

**问题 2: 缺少对 `learning_blueprint_builder.py` 的处理**

这个 873 行的文件做了和 `_normalize_brief_report_payload` 类似的事 — 从 payload 构建 view-model。但它更复杂（35KB），包含数学领域映射、SVG 坐标计算、分层数据组装。它应该被视为另一个"适配器"，但 Hermes 的方案没有提到它。

### 阶段 2 — 渲染引擎拆分

**评价: 完全正确，拆分点清晰**

render_standalone.py 的 4 个天然模块：

| 模块 | 行数 | 内容 | 独立性 |
|---|---|---|---|
| `pdf_utils.py` | ~300 | fontconfig、TOC 提取、page chunking、PDF merge | 完全独立 |
| `adapters/__init__.py` | ~200 | 现有 `_normalize_*` 系列函数 | 依赖 payload 类型判断 |
| `renderer.py` | ~100 | `render_html()` + `load_css()` + image helpers | 依赖 adapters + CSS |
| `pdf_generator.py` | ~200 | `generate_pdf()` + `_build_final_pdf_bytes()` | 依赖 renderer + pdf_utils + golden_typeset |

**额外发现**: `html_renderer.py` (245 行) 也是一个渲染入口，和 `render_standalone.py` 有功能重叠。拆分时需要决定保留哪个作为主入口。

### 阶段 3 — 数据驱动排版

**评价: 部分正确，但描述过于模糊**

golden_typeset 已经是数据驱动排版 — `payload_analyzer.py` 从 payload 估算内容高度，`math_func.py` 计算黄金间距，`css_builder.py` 生成 CSS。"CSS 变量化：领域列数、密度、间距由数据驱动"这个描述和现有实现重合。

**我认为真正需要的是**:
- golden_typeset 的 `payload_analyzer.py` 中经验估算（`_estimate_m1` 等 8 个函数）和 DOM 测量（`measure_dom_heights`）的切换逻辑是合理的双 Pass 架构
- 问题在于经验估算是硬编码的（`TITLE_HEIGHTS` 字典、`content_height()` 公式的 magic numbers），这些应该从 CSS 中提取而非手动维护
- "数据驱动排版"应该理解为：让 golden_typeset 能从 **标准化后的 RenderPayload**（而非原始 JSON）计算布局，这需要在阶段 1 完成后才能做

### 阶段 4 — CSS 瘦身

**评价: 正确但依赖阶段 1-3 完成**

`shared_icon_enhancements.css` 的 438 个 `!important` 是 CSS 特异性战争的产物。它的存在原因是：
1. 模块 CSS 文件各自定义了组件样式
2. 跨模块共享的 icon/增强效果需要覆盖模块级样式
3. CSS 加载顺序（`load_css()` 中 shared_*.css 最后加载）提供了部分优先级，但不够
4. 所以用 `!important` 来强制覆盖

**直接删除 !important 会导致视觉回归。** 必须先完成阶段 2（确定模块边界），然后重新设计 CSS 层级结构。

492KB → 300KB 的目标合理，但我建议分为两步：
- 先做到 380KB（删除弃用的 comic CSS、合并重复声明）
- 再做到 300KB（重构 shared 层）

---

## 3. 我的替代方案：调整后的 5 阶段

### Phase 0: 合约发现（Hermes 方案没有，我新增）

**目标**: 从模板反推完整的 RenderPayload 合约

**为什么需要**: `report-data-contract.md` 只覆盖了 M0-M11 的关键字段，没有覆盖：
- `student_profile` 和 `improvement_preview` 的完整字段（这两个模板是后加的）
- `learning_blueprint_builder` 生成的所有 view-model 字段
- `page_visibility` 的完整 key 集合
- `meta` 的 24 个字段中哪些是模板必需的 vs 可选的

**交付物**:
```
scripts/contracts/
  render_payload.py     # TypedDict 定义，~150 行
  view_models.py        # builder 输出的 TypedDict，~100 行
```

**具体设计**:

```python
# scripts/contracts/render_payload.py
from typing import TypedDict, Optional

class RenderMeta(TypedDict, total=False):
    subject: str                    # "math" | "english"
    subject_name: str               # "数学" | "英语"
    student_display_name: str
    city_name: str
    grade: str
    report_date: str
    report_title: str
    report_name: str
    left_title: str
    page_title: str
    module_title: str
    # ... 完整 24 字段

class PageVisibility(TypedDict, total=False):
    m5_city_compare: bool           # default True
    m10_composition: bool           # default False
    m11_reading_deep: bool          # default False
    show_teacher_supplement: bool   # default False

class RenderPayload(TypedDict, total=False):
    meta: RenderMeta
    cover: dict
    summary: dict
    domains: dict
    core_weakness: dict
    kp_drill: dict
    city_compare: dict
    tiered_learning: dict
    question_detail: dict
    appendix: dict
    data_reliability: dict
    key_findings: list
    breakthrough: dict
    suggestion: dict
    page_visibility: PageVisibility
    # 以下为英语模板需要但数学不需要的
    student_profile: dict
    improvement_preview: dict
    # 透传字段（不进模板，golden_typeset 可能读取）
    section_2_domains: dict
    section_core_weakness: dict
```

**时间**: 0.5 天

### Phase 1: 适配器层（对齐 Hermes 阶段 1，去掉 Pydantic）

**目标**: 将 `_normalize_brief_report_payload` 迁移为独立适配器

**目录结构**:
```
scripts/adapters/
  __init__.py              # Registry + detect + adapt
  identity.py              # 数学 JSON 原样传递（加 page_visibility 兜底）
  english_brief.py         # 迁移自 _normalize_brief_report_payload
```

**具体设计**:

```python
# scripts/adapters/__init__.py
from typing import Protocol

class PayloadAdapter(Protocol):
    def detect(self, payload: dict) -> bool: ...
    def adapt(self, payload: dict) -> dict: ...

_REGISTRY: list[PayloadAdapter] = []

def register(adapter: PayloadAdapter) -> None:
    _REGISTRY.append(adapter)

def adapt_payload(payload: dict) -> dict:
    for adapter in _REGISTRY:
        if adapter.detect(payload):
            return adapter.adapt(payload)
    # 无匹配 → 数学默认路径
    return _ensure_page_visibility(payload)

def _ensure_page_visibility(payload: dict) -> dict:
    """所有路径都需要 page_visibility 兜底"""
    pv = payload.setdefault("page_visibility", {})
    pv.setdefault("m5_city_compare", True)
    pv.setdefault("m10_composition", False)
    pv.setdefault("m11_reading_deep", False)
    pv.setdefault("show_teacher_supplement", False)
    return payload
```

```python
# scripts/adapters/english_brief.py
"""English brief-report-rem adapter.
Migrated from render_standalone._normalize_brief_report_payload (L526-566).

Sections mapping:
  section_1_high_freq → summary
  section_2_domains   → domains
  section_3_breakthrough → core_weakness
  section_4_coverage  → appendix + data_reliability
"""

def detect(payload: dict) -> bool:
    if not isinstance(payload, dict):
        return False
    meta = payload.get("meta", {}) or {}
    sections = payload.get("sections", {}) or {}
    return (
        payload.get("schema_version") == "render_payload.v1"
        and meta.get("render_template") == "brief-report-rem"
        and "section_1_high_freq" in sections
    )

def adapt(payload: dict) -> dict:
    """Full adaptation: sections → flat contract"""
    # 直接迁移现有 _brief_report_* 函数
    from . import _english_brief_sections as sec
    sections = payload.get("sections") or {}
    meta = sec.build_meta(payload)
    summary = sec.build_summary(sections)
    domains = dict(sections.get("section_2_domains") or {})
    domains.setdefault("target_accuracy", summary.get("target_accuracy"))

    normalized = dict(payload)
    normalized.update({
        "meta": meta,
        "cover": sec.build_cover(payload, meta),
        "summary": summary,
        "domains": domains,
        "core_weakness": sec.build_core_weakness(sections),
        "kp_drill": sec.build_kp_drill_empty(),
        "data_reliability": {"section_4_coverage": sections.get("section_4_coverage") or {}},
        "appendix": sec.build_appendix(sections, meta),
        "key_findings": [],
        "breakthrough": sections.get("section_3_breakthrough") or {},
        "suggestion": {"text": (sections.get("section_3_breakthrough") or {}).get("note_text", "")},
        "city_compare": {"has_data": False, "overlap_items": [], "overlap_summary": {"has_data": False}},
        "tiered_learning": sec.build_tiered_learning(summary, domains, meta),
        "page_visibility": {
            "m5_city_compare": False,
            "m10_composition": False,
            "m11_reading_deep": False,
            "show_teacher_supplement": False,
        },
    })
    return normalized
```

**迁移策略**: `_brief_report_meta`、`_brief_report_cover` 等 6 个辅助函数迁移到 `adapters/_english_brief_sections.py`，保持函数签名不变，只改 import 路径。

**时间**: 0.5 天

### Phase 2: 渲染引擎拆分（对齐 Hermes 阶段 2）

**目标**: render_standalone.py 从 1029 行降到 <100 行（薄入口）

**拆分方案**:

```
scripts/
  render_standalone.py        # 薄入口 CLI (< 100 行)
  pdf_utils.py                # fontconfig + TOC + chunking (~250 行)
  pdf_generator.py            # generate_pdf + build_final (~200 行)
  renderer.py                 # render_html + load_css + images (~120 行)
  adapters/                   # Phase 1 产出
  golden_typeset/             # 不变
  learning_blueprint_builder.py  # 暂不拆分（风险高，收益低）
```

**render_standalone.py 瘦身后**:

```python
#!/usr/bin/env python3
"""报告渲染入口 — CLI"""
import argparse, json, sys
from pathlib import Path
from adapters import adapt_payload
from renderer import render_html
from pdf_generator import generate_pdf

def main():
    parser = argparse.ArgumentParser(description="报告渲染 (外包独立使用)")
    parser.add_argument("json_file")
    parser.add_argument("-o", "--output", default="output.html")
    parser.add_argument("--pdf", action="store_true")
    parser.add_argument("--landscape", action="store_true")
    parser.add_argument("--report-variant", choices=["parent", "admissions_blueprint", "full"], default="parent")
    args = parser.parse_args()

    with open(args.json_file, "r", encoding="utf-8") as f:
        payload = adapt_payload(json.load(f))

    from golden_typeset.engine import build_typeset_css
    typeset_css = build_typeset_css(payload)
    landscape = bool(args.landscape or args.report_variant == "admissions_blueprint")

    html = render_html(payload, typeset_css=typeset_css,
                       report_variant=args.report_variant, landscape=landscape)
    Path(args.output).write_text(html, encoding="utf-8")
    print(f"HTML: {args.output}")

    if args.pdf:
        pdf_path = args.output.replace(".html", ".pdf")
        generate_pdf(pdf_path, payload,
                     report_variant=args.report_variant, landscape=landscape)

if __name__ == "__main__":
    main()
```

**关键决策: `html_renderer.py` 的处理**

`html_renderer.py` (245 行) 是另一个渲染入口，用于 `render_report.py` 和 `render_smoke_test.py`。它有自己的 `_build_context()` 函数和 `render_to_html()` 函数。

**建议**: 不删除，但标记为 deprecated。新的适配器层对两个入口都可用。等 Phase 2 稳定后再统一入口。

**时间**: 1 天

### Phase 3: 数据驱动排版增强（调整 Hermes 阶段 3）

**目标**: golden_typeset 从标准化 RenderPayload 读取数据，而非原始 JSON

**当前问题**:
- `payload_analyzer.py` 的 `_estimate_m1` 等函数直接从 payload 读取 `summary`、`breakthrough` 等字段
- 这些字段在数学 JSON 中直接存在，但在英语 JSON 中由适配器生成
- 如果适配器输出格式有变化，估算函数需要同步修改

**改进**:
1. `payload_analyzer.py` 的输入从 `dict` 改为依赖 `contracts.RenderPayload` 类型标注
2. 经验估算函数使用合约中定义的字段名，而非硬编码字符串
3. `WRAPPER_SELECTORS` 和 `_COMPACT_CORE_RHYTHM_MM` 从 `__init__.py` 移到 `payload_analyzer.py`（它们是分析配置，不是共享常量）

**时间**: 0.5 天

### Phase 4: CSS 架构重构（合并 Hermes 阶段 3+4）

**目标**: 492KB → 380KB，438 个 !important → <100 个

**分两步**:

**Step 4a — 清理（低风险）**:
- 删除 `comic_scene1.css` + `comic_scene2.css`（3.9KB，已标记 deprecated）
- 从 `shared_icon_enhancements.css` 中提取按模块分组为 `shared_m1_icons.css`、`shared_m4_icons.css` 等
- 每个 `shared_mN_*.css` 只包含对应模块的 icon 增强，不再需要 !important（因为加载顺序已保证优先级）

**Step 4b — 重构（中风险，需要视觉回归测试）**:
- 合并 `shared_chapter_underlines.css` (2.9KB) 到 `base.css`（这是全局样式）
- 合并 `shared_english_deep_pages.css` (8.1KB) 到 `english_subject_theme.css`（都是英语专属）
- 审计剩余 !important，只保留跨模块覆盖必要的

**CSS 加载新顺序**:
```
base.css → 模块 CSS (字母序) → shared_mN_*.css (对应模块) → 主题 CSS
```

**时间**: 1.5 天（Step 4a: 0.5 天，Step 4b: 1 天）

---

## 4. 风险分析与缓解

| 风险 | 概率 | 影响 | 缓解措施 |
|---|---|---|---|
| 适配器迁移引入回归 | 中 | 高 | 迁移前用所有 3 个样本生成 PDF 快照，迁移后做像素对比 |
| TypedDict 合约定义不完整 | 高 | 低 | TypedDict 用 `total=False`，遗漏字段不会报错。逐步完善 |
| CSS 拆分导致视觉变化 | 中 | 中 | Step 4a 只做文件移动不改内容；Step 4b 逐模块验证 |
| `html_renderer.py` 统一时遗漏逻辑 | 低 | 高 | Phase 2 不统一，只标记 deprecated |
| `learning_blueprint_builder.py` 873 行未处理 | 低 | 中 | 它是独立的 view-model builder，接口清晰（`build_learning_blueprints(payload)` → dict），暂不拆分 |
| Phase 0 合约发现耗时长 | 低 | 低 | 已有 `report-data-contract.md` 作为基础，只需补全 |

---

## 5. 完整时间线

```
Day 1: Phase 0 (合约发现) + Phase 1 (适配器层)
Day 2: Phase 2 (渲染引擎拆分)
Day 3: Phase 3 (golden_typeset 增强) + Phase 4a (CSS 清理)
Day 4: Phase 4b (CSS 重构) + 回归测试
```

**总工作量**: 3.5-4 天

---

## 6. 分工建议

### Hermes (xc) 负责
- **Phase 0**: 合约发现 — 从模板反推 TypedDict 定义（需要深度理解每个模板的字段需求）
- **Phase 4b**: CSS 重构的视觉验收（需要人眼判断 PDF 输出是否正确）
- **整体**: 方案决策、风险判断、进度协调

### Claude 负责
- **Phase 1**: 适配器层代码实现（机械迁移 + Registry 搭建）
- **Phase 2**: 渲染引擎拆分（代码重构）
- **Phase 3**: golden_typeset 类型标注更新
- **Phase 4a**: CSS 文件清理（安全的机械操作）
- **回归测试**: 生成 PDF 快照并对比

### 协作模式
- Phase 0 由 Hermes 主导（合约发现需要产品判断）
- Phase 1-3 由 Claude 执行（代码重构）
- Phase 4 协作（Claude 改代码，Hermes 验收视觉）
- 每个 Phase 完成后做一次快速同步

---

## 7. 不做的事（明确排除）

1. **不引入 Pydantic** — 当前是单进程渲染脚本，TypedDict 足够。等合约稳定后再考虑
2. **不拆分 learning_blueprint_builder.py** — 873 行但接口清晰，风险收益比不合适
3. **不统一 html_renderer.py 和 render_standalone.py** — 等适配器层稳定后再处理
4. **不做模板引擎迁移**（Jinja2 → 其他）— 超出范围
5. **不修改样本 JSON** — 合约适配由适配器层负责，不改源数据
