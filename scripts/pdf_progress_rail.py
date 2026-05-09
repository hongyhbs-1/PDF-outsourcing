"""Overlay a section-tab navigation rail onto generated report PDFs."""

from __future__ import annotations

from dataclasses import dataclass


try:
    import fitz
except ImportError as exc:  # pragma: no cover - exercised only without PyMuPDF
    fitz = None
    FITZ_IMPORT_ERROR = exc
else:
    FITZ_IMPORT_ERROR = None


SECTION_DEFS = (
    ("m1", "一、诊断摘要", "一", "诊断摘要"),
    ("m4", "二、六大领域达标分析", "二", "领域分析"),
    ("m2", "三、核心短板清单", "三", "核心短板"),
    ("m3", "四、知识点短板钻取", "四", "知识点"),
    ("m5", "五、城市考情对照", "五", "城市考情"),
    ("m6", "六、分层学习建议", "六", "学习建议"),
    ("m9", "七、逐题分析明细", "七", "逐题分析"),
    ("m7", "八、数据可信度说明", "八", "可信度"),
    ("m8", "附录", "附", "附录"),
    ("m10", "英语作文专项", "作", "作文"),
    ("m11", "阅读理解深度分析", "阅", "阅读"),
)

# Chinese ordinal numerals for dynamic renumbering
_CN_ORDINALS = ["一", "二", "三", "四", "五", "六", "七", "八", "九", "十", "十一"]

# Keys that use ordinal numbers (m8/m10/m11 use fixed non-ordinal labels)
_ORDINAL_KEYS = {"m1", "m4", "m2", "m3", "m5", "m6", "m9", "m7"}

NAV_TOP = 52
NAV_BOTTOM = 52
TAB_RIGHT_INSET = 2
TAB_INACTIVE_WIDTH = 26
TAB_ACTIVE_WIDTH = 30
TAB_HEIGHT_MIN = 44
TAB_HEIGHT_MAX = 78
TAB_GAP_MIN = 5
TAB_GAP_MAX = 10
TAB_RADIUS_RATIO = 0.18
TAB_BORDER_WIDTH = 0.45
TAB_SHADOW_OFFSET_X = 1.6
TAB_SHADOW_OFFSET_Y = 1.6
TAB_SHADOW_OPACITY = 0.16
TAB_LABEL_PADDING_X = 3
TAB_LABEL_PADDING_Y = 6
LABEL_ROTATE = 270
LABEL_MIN_FONT_SIZE = 7.0
LABEL_MAX_FONT_SIZE = 9.5
LABEL_MIN_CHARS = 3
LINK_EXPAND = 1.5

COLOR_TAB_ACTIVE_FILL = "#1f6f78"
COLOR_TAB_ACTIVE_BORDER = "#12344d"
COLOR_TAB_ACTIVE_TEXT = "#FFFFFF"
COLOR_TAB_INACTIVE_FILL = "#c8d3dc"
COLOR_TAB_INACTIVE_BORDER = "#a8b5c2"
COLOR_TAB_INACTIVE_TEXT = "#3a4a5c"
COLOR_TAB_SHADOW = "#8896a7"


@dataclass(frozen=True)
class SectionRange:
    key: str
    title: str
    short_label: str
    tab_label: str
    start_page: int
    end_page: int


def _color(hex_color: str) -> tuple[float, float, float]:
    raw = hex_color.lstrip("#")
    return tuple(int(raw[index:index + 2], 16) / 255 for index in (0, 2, 4))


def _validate_page(page_number: int, total_pages: int, key: str) -> None:
    if page_number < 1 or page_number > total_pages:
        raise ValueError(
            f"章节 {key} 页码越界: {page_number}, PDF 总页数: {total_pages}"
        )


def build_section_ranges(
    toc_pages: dict[str, int],
    total_pages: int,
) -> list[SectionRange]:
    if total_pages < 1:
        raise ValueError(f"PDF 总页数必须大于 0: {total_pages}")

    # Collect visible sections, renumbering ordinals dynamically
    sections = []
    ordinal_idx = 0
    for key, title, short_label, tab_label in SECTION_DEFS:
        if key not in toc_pages:
            continue
        page_number = int(toc_pages[key])
        _validate_page(page_number, total_pages, key)
        # Renumber ordinal keys so gaps don't leave wrong numbers
        if key in _ORDINAL_KEYS:
            cn = _CN_ORDINALS[ordinal_idx] if ordinal_idx < len(_CN_ORDINALS) else short_label
            ordinal_idx += 1
            title = f"{cn}、{title.split('、', 1)[-1]}" if "、" in title else title
            short_label = cn
        sections.append((key, title, short_label, tab_label, page_number))

    ranges: list[SectionRange] = []
    for index, item in enumerate(sections):
        next_start = sections[index + 1][4] if index + 1 < len(sections) else total_pages + 1
        end_page = max(item[4], next_start - 1)
        ranges.append(
            SectionRange(item[0], item[1], item[2], item[3], item[4], end_page)
        )
    return ranges


def section_for_page(
    page_number: int,
    ranges: list[SectionRange],
) -> SectionRange | None:
    for section in ranges:
        if section.start_page <= page_number <= section.end_page:
            return section
    return None


def _label_font_size(text: str, tab_height: float) -> float:
    char_count = max(len(text), LABEL_MIN_CHARS)
    size = (tab_height - TAB_LABEL_PADDING_Y * 2) / char_count
    return max(LABEL_MIN_FONT_SIZE, min(LABEL_MAX_FONT_SIZE, size))


def _tab_metrics(rect, count: int) -> tuple[float, float, float]:
    available = rect.height - NAV_TOP - NAV_BOTTOM
    gap = min(TAB_GAP_MAX, max(TAB_GAP_MIN, available * 0.012))
    tab_height = (available - gap * max(count - 1, 0)) / max(count, 1)

    if tab_height < TAB_HEIGHT_MIN and count > 1:
        gap = max(TAB_GAP_MIN, (available - TAB_HEIGHT_MIN * count) / (count - 1))
        tab_height = (available - gap * (count - 1)) / count

    tab_height = min(TAB_HEIGHT_MAX, max(TAB_HEIGHT_MIN, tab_height))
    content_height = tab_height * count + gap * max(count - 1, 0)
    top = rect.y0 + NAV_TOP + max(0, (available - content_height) / 2)
    return top, tab_height, gap


def _tab_rect(page_rect, top: float, index: int, height: float, gap: float, active: bool):
    width = TAB_ACTIVE_WIDTH if active else TAB_INACTIVE_WIDTH
    x1 = page_rect.x1 - TAB_RIGHT_INSET
    x0 = x1 - width
    y0 = top + index * (height + gap)
    return fitz.Rect(x0, y0, x1, y0 + height)


def _draw_shadow(page, rect) -> None:
    shadow = fitz.Rect(
        rect.x0 + TAB_SHADOW_OFFSET_X,
        rect.y0 + TAB_SHADOW_OFFSET_Y,
        rect.x1 + TAB_SHADOW_OFFSET_X,
        rect.y1 + TAB_SHADOW_OFFSET_Y,
    )
    page.draw_rect(
        shadow,
        color=_color(COLOR_TAB_SHADOW),
        fill=_color(COLOR_TAB_SHADOW),
        width=0,
        radius=TAB_RADIUS_RATIO,
        fill_opacity=TAB_SHADOW_OPACITY,
        stroke_opacity=0,
        overlay=True,
    )


def _draw_tab(page, rect, active: bool) -> None:
    fill = COLOR_TAB_ACTIVE_FILL if active else COLOR_TAB_INACTIVE_FILL
    border = COLOR_TAB_ACTIVE_BORDER if active else COLOR_TAB_INACTIVE_BORDER
    _draw_shadow(page, rect)
    page.draw_rect(
        rect,
        color=_color(border),
        fill=_color(fill),
        width=TAB_BORDER_WIDTH,
        radius=TAB_RADIUS_RATIO,
        overlay=True,
    )


def _draw_label(page, rect, text: str, active: bool) -> None:
    color = COLOR_TAB_ACTIVE_TEXT if active else COLOR_TAB_INACTIVE_TEXT
    font_size = _label_font_size(text, rect.height)
    textbox = fitz.Rect(
        rect.x0 + TAB_LABEL_PADDING_X,
        rect.y0 + TAB_LABEL_PADDING_Y,
        rect.x1 - TAB_LABEL_PADDING_X,
        rect.y1 - TAB_LABEL_PADDING_Y,
    )
    page.insert_textbox(
        textbox,
        text,
        fontname="china-ss",
        fontsize=font_size,
        color=_color(color),
        align=fitz.TEXT_ALIGN_CENTER,
        rotate=LABEL_ROTATE,
        overlay=True,
    )


def _link_rect(rect):
    return fitz.Rect(
        rect.x0 - LINK_EXPAND,
        rect.y0 - LINK_EXPAND,
        rect.x1 + LINK_EXPAND,
        rect.y1 + LINK_EXPAND,
    )


def _insert_section_link(page, rect, section: SectionRange) -> None:
    page.insert_link({
        "kind": fitz.LINK_GOTO,
        "from": _link_rect(rect),
        "page": section.start_page - 1,
        "to": fitz.Point(0, 0),
    })


def _draw_progress_rail(
    page,
    ranges: list[SectionRange],
    current: SectionRange | None,
) -> None:
    rect = page.rect
    count = len(ranges)
    top, tab_height, gap = _tab_metrics(rect, count)

    for index, section in enumerate(ranges):
        active = current is not None and section.key == current.key
        tab = _tab_rect(rect, top, index, tab_height, gap, active)
        _draw_tab(page, tab, active)
        # _insert_section_link(page, tab, section)  # 点击跳转已禁用
        _draw_label(page, tab, section.tab_label, active)


def _require_fitz() -> None:
    if fitz is None:
        raise RuntimeError("PyMuPDF 未安装，无法叠加 PDF 阅读进度边条") from FITZ_IMPORT_ERROR


def apply_progress_rail(pdf_bytes: bytes, toc_pages: dict[str, int]) -> bytes:
    _require_fitz()
    if not toc_pages:
        return pdf_bytes

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    ranges = build_section_ranges(toc_pages, len(doc))
    if not ranges:
        doc.close()
        return pdf_bytes

    # Find the TOC page number by searching for "目 录" or "目录"
    toc_page_num = 0
    for page_idx in range(len(doc)):
        text = doc[page_idx].get_text()
        if "目 录" in text or "目录" in text:
            # Only match standalone TOC title, not references to TOC
            lines = text.strip().split("\n")
            for line in lines[:5]:
                stripped = line.strip()
                if stripped in ("目 录", "目录") or stripped.startswith("目 录") or stripped.startswith("目录"):
                    toc_page_num = page_idx + 1
                    break
            if toc_page_num:
                break

    # Navigation rail starts from the page AFTER TOC
    start_page = toc_page_num + 1 if toc_page_num else 1
    print(f"[导航栏] 目录页={toc_page_num}, 起始页={start_page}")
    print(f"[导航栏] 章节范围:")
    for r in ranges:
        print(f"  {r.key}: pages {r.start_page}-{r.end_page} -> tab=\"{r.tab_label}\"")

    for index, page in enumerate(doc, start=1):
        if index < start_page:
            continue
        current = section_for_page(index, ranges)
        if current is None:
            continue
        # Clear existing rail links to prevent duplication on re-render
        for link in page.get_links():
            if link.get('kind') == 1:  # LINK_GOTO
                page.delete_link(link)
        _draw_progress_rail(page, ranges, current)

    output = doc.tobytes(garbage=4, deflate=True)
    doc.close()
    return output
