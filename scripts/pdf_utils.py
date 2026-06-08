#!/usr/bin/env python3
"""
PDF 工具函数 — 预分页、TOC 注入、浏览器控制、字体配置

从 render_standalone.py 拆分出的 PDF 辅助逻辑。
"""

import os
import re
import tempfile
from pathlib import Path

from pdf_chrome_templates import build_pdf_chrome_options
from pdf_progress_rail import apply_progress_rail

# PyMuPDF 可选依赖 (目录页码提取)
try:
    import fitz  # PyMuPDF

    HAS_FITZ = True
except ImportError:
    HAS_FITZ = False

from renderer import FONTS_DIR

# ---------------------------------------------------------------------------
# 紧凑策略 — 每个模块的紧凑行为声明
# ---------------------------------------------------------------------------

COMPACT_POLICY = {
    # never: 含算法/层级/指标说明，必须独立分页
    "m2": "never",   # 短板筛选说明
    "m3": "never",   # 层级说明
    "m8": "never",   # 指标释义/难度分布
    "m9": "never",   # 逐题分析明细（天然分页能力）
    # auto: 数据量变化大，按密度判定
    "m4": "auto",    # 领域图表
    "m5": "auto",    # 城市考情
    "m6": "auto",    # 学习建议
    "m7": "auto",     # 可信度说明 — f795e15 修复 s08 回归（xc 改 never 会破坏）
    # always: 极短模块，允许接前页
    "m1": "always",

    # never: 英语专项精讲 — 正式 TOC 章节，标题不能跑到上一页
    "m10": "never",
    "m11": "never",
}

_AUTO_DENSITY_THRESHOLD = 0.70


def _build_preflight_js() -> str:
    """构建注入了 COMPACT_POLICY 的预分页 JS。"""
    import json
    policy_json = json.dumps(COMPACT_POLICY, ensure_ascii=False)
    threshold = _AUTO_DENSITY_THRESHOLD
    return _PREFLIGHT_TEMPLATE.replace("__COMPACT_POLICY__", policy_json).replace(
        "__DENSITY_THRESHOLD__", str(threshold)
    )


# ---------------------------------------------------------------------------
# 预分页 JS (移植自 pdf_service.py)
# ---------------------------------------------------------------------------

_PREFLIGHT_TEMPLATE = """
() => {
    // ─── 分页治理: JS 只做检测+标记, 不直接改 style ───
    // 所有 break-inside/page-break-inside 控制由 CSS class 驱动
    // JS 添加 .break-relax / .break-relax-tall / .break-relax-last
    // CSS 层在 base.css 统一定义这些 class 的行为

    const COMPACT_POLICY = __COMPACT_POLICY__;
    const AUTO_THRESHOLD = __DENSITY_THRESHOLD__;

    const modulePages = document.querySelectorAll('.module-page');

    // --- S1: M5 清理 (min-height + 分页) ---
    const m5 = document.querySelector('.m5-city-compare');
    if (m5) m5.classList.add('break-relax');

    // --- S2: M1 breakthrough-grid 整体放松 ---
    const btGrid = document.querySelector('.m1-breakthrough-grid');
    if (btGrid) btGrid.classList.add('break-relax');

    // --- S3: M7 置信度说明不独占页 ---
    document.querySelectorAll('.m7-note').forEach(n => n.classList.add('break-relax'));

    // --- S4: 大块元素(>200px)条件放松 ---
    const THRESHOLD = 200;
    const tallSelectors = [
        '.m1-suggestion-callout',
        '.m2-cw-tips-box',
        '.m4-chart-box',
        '.m4-summary-card',
    ];
    tallSelectors.forEach(sel => {
        document.querySelectorAll(sel).forEach(el => {
            if (el.getBoundingClientRect().height > THRESHOLD) {
                el.classList.add('break-relax-tall');
            }
        });
    });

    // --- S5: M8 最后面板 — 已由 base.css :last-of-type 覆盖, JS 不再处理 ---

    // --- S6: M3 领域面板允许跨页 ---
    const m3Section = document.querySelector('section.m3-kp-drill');
    if (m3Section) {
        m3Section.querySelectorAll('.m3-kp-drill__panel').forEach(p => {
            p.classList.add('break-relax');
        });
    }

    // --- S7: 模块尾元素允许跨页 ---
    modulePages.forEach(page => {
        const candidates = page.querySelectorAll(
            '.card, .kp-card, .domain-card, .breakthrough-card, .m8-appendix-panel, .m7-note, table'
        );
        if (candidates.length > 0) {
            candidates[candidates.length - 1].classList.add('break-relax-last');
        }
    });

    // ─── 紧凑算法: 策略驱动 ───
    const PAGE_HEIGHT = 1123;

    function getModuleId(mp) {
        const targets = [mp.querySelector('section'), mp.firstElementChild];
        for (const el of targets) {
            if (!el) continue;
            for (const cls of el.classList) {
                const m = cls.match(/^(m\d+)(?:$|-)/);
                if (m) return m[1];
            }
        }
        return null;
    }

    let tocIndex = -1;
    modulePages.forEach((mp, i) => {
        if (mp.querySelector('.mtoc-page, [class*="toc"]')) tocIndex = i;
    });

    modulePages.forEach((page, index) => {
        if (index === 0 || page.classList.contains('comic-module')) return;
        const modId = getModuleId(page);
        if (!modId) return;
        if (tocIndex >= 0 && index === tocIndex + 1) return;

        const policy = COMPACT_POLICY[modId] || 'auto';

        // never: 保持独立页, 跳过
        if (policy === 'never') return;

        page.style.minHeight = '0';
        for (const child of page.children) {
            child.style.minHeight = '0';
        }

        let shouldCompact = false;
        if (policy === 'always') {
            shouldCompact = true;
        } else {
            // auto: 密度判定
            const contentHeight = page.scrollHeight;
            shouldCompact = contentHeight / PAGE_HEIGHT < AUTO_THRESHOLD;
        }

        if (shouldCompact) {
            page.style.breakBefore = 'auto';
            page.style.pageBreakBefore = 'auto';
        } else {
            page.style.minHeight = '';
            for (const child of page.children) {
                child.style.minHeight = '';
            }
        }
    });

    // M3 panel 统计 (保留原返回值兼容)
    const panels = document.querySelectorAll('.m3-kp-drill__panel');
    const panelsWithData = Array.from(panels).filter(
        p => p.querySelectorAll('tbody tr').length > 0
    );

    return {
        panels_total: panels.length,
        panels_with_data: panelsWithData.length,
        m5_fixed: !!m5,
        relaxed_blocks: tallSelectors.length,
    };
}
"""

# 预构建实例, 供 pdf_service / _build_final_pdf_bytes 使用
_PREFLIGHT_JS = _build_preflight_js()

# ---------------------------------------------------------------------------
# TOC 页码提取 (移植自 pdf_service.py)
# ---------------------------------------------------------------------------

_TOC_SEARCH_MAP: list[tuple[str, str]] = [
    ("m1", "一、"),
    ("m4", "二、"),
    ("m2", "三、"),
    ("m3", "四、"),
    ("m5", "五、"),
    ("m6", "六、"),
    ("m9", "七、"),
    ("m7", "八、"),
    ("m8", "分析范围"),
    ("m10", "十、"),
    ("m11", "十一、"),
]
_TOC_DISPLAY_KEYS = {"m1", "m4", "m2", "m3", "m5", "m6", "m9", "m7", "m8", "m10", "m11"}

_TOC_INJECT_JS = """
(toc_pages) => {
    let injected = 0;
    for (const [key, pageNum] of Object.entries(toc_pages)) {
        const el = document.querySelector(`[data-toc-key="${key}"]`);
        if (el) {
            el.textContent = String(pageNum);
            injected++;
        }
    }
    return injected;
}
"""


def _extract_toc_pages(pdf_bytes: bytes) -> dict[str, int]:
    """从 PDF 中提取各章节起始页码 (1-based)。

    搜索策略：在每个页面的前几行文本中查找精确的章节标题前缀。
    排除目录页（含 '目 录' 或 '目录' 独立行），避免误匹配目录列表中的条目。
    """
    if not HAS_FITZ:
        print("[INFO] PyMuPDF 未安装, 跳过目录页码注入 (pip install PyMuPDF)")
        return {}

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    result: dict[str, int] = {}
    found_keys: set[str] = set()

    # 精确标题匹配：必须是行首的完整章节标题
    # m7 标题可能因 M9 是否存在而变化序号（七、/八、），提供两个候选
    # m8 标题可能因数据不同而变化，使用较短前缀
    _EXACT_TITLES = {
        "m1": ("一、诊断摘要",),
        "m4": ("二、六大领域达标分析", "二、六大领域达标总览"),
        "m2": ("三、核心短板清单", "三、个性化突破路径", "三、学习成果展示"),
        "m3": ("四、知识点短板钻取",),
        "m5": ("五、城市考情对照",),
        "m6": ("六、分层与学习建议",),
        "m9": ("七、逐题分析明细",),
        "m7": ("七、数据", "八、数据", "七、题检覆盖", "八、题检覆盖"),
        "m8": ("八、附录", "九、附录", "附录", "分析范围"),
        "m10": ("十、",),
        "m11": ("十一、",),
    }

    # m7 需要额外验证：标题行必须很短（< 30 字符），排除正文中的偶然匹配
    _SHORT_TITLE_KEYS = {"m7"}
    _SHORT_TITLE_MAX_LEN = 30
    _CONTAINS_TITLE_FALLBACKS = {
        # Chromium can emit the Chinese numeral in the M3 title as a null glyph
        # when the bundled CJK font is subset for PDF. Keep TOC extraction
        # stable by matching the semantic title after skipping the TOC page.
        "m3": ("知识点短板钻取",),
    }

    for page_idx in range(len(doc)):
        text = doc[page_idx].get_text()
        lines = text.split("\n")

        # 跳过目录页
        is_toc_page = any(line.strip() in ("目 录", "目录") for line in lines[:5])
        if is_toc_page:
            continue

        for key, titles in _EXACT_TITLES.items():
            if key in found_keys:
                continue
            for line in lines:
                stripped = line.strip()
                matched = any(stripped.startswith(t) for t in titles)
                if not matched:
                    matched = any(
                        fallback in stripped
                        for fallback in _CONTAINS_TITLE_FALLBACKS.get(key, ())
                    )
                if not matched:
                    continue
                # 对短前缀标题额外验证：行长度不能太长（排除正文中的偶然匹配）
                if key in _SHORT_TITLE_KEYS and len(stripped) > _SHORT_TITLE_MAX_LEN:
                    continue
                result[key] = page_idx + 1
                found_keys.add(key)
                break

        if len(found_keys) == len(_EXACT_TITLES):
            break

    doc.close()
    print(f"[目录] 提取章节页码: {result}")
    return result


def _toc_pages_for_injection(toc_pages: dict[str, int]) -> dict[str, int]:
    return {
        key: page_number
        for key, page_number in toc_pages.items()
        if key in _TOC_DISPLAY_KEYS
    }


# ---------------------------------------------------------------------------
# Fontconfig 环境
# ---------------------------------------------------------------------------

FONTCONFIG_PATH = os.environ.get("FONTCONFIG_PATH", "")


def _ensure_fontconfig_env():
    """确保 WSL2/Linux 环境下 Fontconfig 可用并能发现内置中文字体。"""
    global FONTCONFIG_PATH
    if not FONTCONFIG_PATH:
        for candidate in ["/etc/fonts", "/usr/local/etc/fonts"]:
            if Path(candidate).is_dir():
                os.environ["FONTCONFIG_PATH"] = candidate
                FONTCONFIG_PATH = candidate
                break

    font_file = FONTS_DIR / "NotoSansSC-Variable.ttf"
    if not font_file.exists():
        return

    default_config = Path("/etc/fonts/fonts.conf")
    include_line = (
        f'  <include ignore_missing="yes">{default_config}</include>\n'
        if default_config.exists()
        else ""
    )
    bundled_config = Path(tempfile.gettempdir()) / "dida985-fonts.conf"
    config_text = (
        '<?xml version="1.0"?>\n'
        '<!DOCTYPE fontconfig SYSTEM "fonts.dtd">\n'
        "<fontconfig>\n"
        f"  <dir>{FONTS_DIR.resolve()}</dir>\n"
        f"{include_line}"
        "</fontconfig>\n"
    )
    if (
        not bundled_config.exists()
        or bundled_config.read_text(encoding="utf-8") != config_text
    ):
        bundled_config.write_text(config_text, encoding="utf-8")
    os.environ["FONTCONFIG_FILE"] = str(bundled_config)


# ---------------------------------------------------------------------------
# PDF 参数构建
# ---------------------------------------------------------------------------


def _build_pdf_chrome_meta(payload: dict) -> dict:
    """Build PDF header/footer metadata from the full payload."""
    meta = dict(payload.get("meta") or {})
    cover_meta = payload.get("cover", {}).get("cover_meta", {}) or {}
    summary = payload.get("summary", {}) or {}

    meta.setdefault("grade", cover_meta.get("grade", ""))
    meta.setdefault("target_score_text", summary.get("target_score_text", ""))
    return meta


def _build_pdf_kwargs(payload: dict, *, landscape: bool = False) -> dict:
    """构建 Playwright page.pdf() 参数, 含页眉页脚。"""
    kwargs = {
        "format": "A4",
        "print_background": True,
        "scale": 0.9,
        **build_pdf_chrome_options(_build_pdf_chrome_meta(payload)),
    }
    if landscape:
        kwargs["landscape"] = True
    return kwargs


# ---------------------------------------------------------------------------
# PDF 分块
# ---------------------------------------------------------------------------

# Windows system Chrome can fail Page.printToPDF for large contiguous reports
# while smaller page ranges from the same document succeed. Generate PDFs in
# deterministic page chunks and merge them so we avoid the failing aggregation
# path without changing page content, TOC numbering, headers/footers, or rails.
_PDF_CHUNK_PAGE_COUNT = 15


def _is_page_range_exceeds_page_count_error(exc: Exception) -> bool:
    return "Page range exceeds page count" in str(exc)


def _pdf_page_count(pdf_bytes: bytes) -> int:
    if not HAS_FITZ:
        return 0
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    try:
        return doc.page_count
    finally:
        doc.close()


def _pdf_total_pages_from_footer(pdf_bytes: bytes) -> int | None:
    """Read Chromium header/footer total page count from a printed chunk."""
    if not HAS_FITZ:
        return None
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    try:
        # The footer template uses "第 <pageNumber> / <totalPages> 页". One or two
        # pages are enough; keep this cheap because it runs during PDF generation.
        for page in list(doc)[:2]:
            text = page.get_text("text")
            match = re.search(r"第\s*\d+\s*/\s*(\d+)\s*页", text)
            if match:
                return int(match.group(1))
    finally:
        doc.close()
    return None


def _merge_pdf_chunks(pdf_chunks: list[bytes]) -> bytes:
    if len(pdf_chunks) == 1:
        return pdf_chunks[0]
    if not HAS_FITZ:
        raise RuntimeError("PyMuPDF is required to merge segmented PDF chunks")

    merged = fitz.open()
    try:
        for pdf_chunk in pdf_chunks:
            chunk_doc = fitz.open(stream=pdf_chunk, filetype="pdf")
            try:
                merged.insert_pdf(chunk_doc)
            finally:
                chunk_doc.close()
        return merged.tobytes()
    finally:
        merged.close()


def _page_pdf_segmented(
    page, pdf_kwargs: dict, chunk_pages: int = _PDF_CHUNK_PAGE_COUNT
) -> bytes:
    """Print PDF in stable page ranges and merge the chunks.

    Chromium preserves original pageNumber/totalPages in header/footer even
    when page_ranges is used, so chunking avoids Windows full-document print
    failures without changing visible page numbering.
    """
    if not HAS_FITZ:
        return page.pdf(**pdf_kwargs)

    chunks: list[bytes] = []
    start_page = 1
    total_pages: int | None = None
    while True:
        end_page = start_page + chunk_pages - 1
        if total_pages is not None:
            end_page = min(end_page, total_pages)
        try:
            chunk = page.pdf(
                **{**pdf_kwargs, "page_ranges": f"{start_page}-{end_page}"}
            )
        except Exception as exc:
            if chunks and _is_page_range_exceeds_page_count_error(exc):
                break
            raise
        chunks.append(chunk)

        if total_pages is None:
            total_pages = _pdf_total_pages_from_footer(chunk)
        page_count = _pdf_page_count(chunk)
        if page_count <= 0 or page_count < chunk_pages:
            break
        if total_pages is not None and end_page >= total_pages:
            break
        start_page = end_page + 1

    return _merge_pdf_chunks(chunks)


# ---------------------------------------------------------------------------
# 浏览器控制
# ---------------------------------------------------------------------------


def _launch_chromium(playwright):
    try:
        return playwright.chromium.launch(headless=True, args=["--no-sandbox"])
    except Exception:
        print("[INFO] Playwright Chromium 不可用, 尝试系统 Chrome")
        return playwright.chromium.launch(channel="chrome")


def _wait_for_images(page) -> None:
    print("[INFO] 等待图片加载...")
    img_status = page.evaluate("""() => {
                const images = Array.from(document.images);
                const comicImages = images.filter(img => img.classList.contains('comic-image'));
                return {
                    total: images.length,
                    comic: comicImages.length,
                    comic_src: comicImages.map(img => ({
                        src: img.src.substring(0, 100) + '...',
                        complete: img.complete,
                        naturalWidth: img.naturalWidth,
                        naturalHeight: img.naturalHeight
                    }))
                };
            }""")
    print(f"[INFO] 图片状态: 总数={img_status['total']}, 漫画={img_status['comic']}")
    if img_status["comic"] > 0:
        for ci in img_status["comic_src"]:
            print(
                f"[INFO]   - {ci['src']}, complete={ci['complete']}, "
                f"size={ci['naturalWidth']}x{ci['naturalHeight']}"
            )

    page.evaluate("""() => {
                return Promise.all(
                    Array.from(document.images).map(img => {
                        if (img.complete && img.naturalWidth > 0) return Promise.resolve();
                        return new Promise(resolve => {
                            img.addEventListener('load', resolve, {once: true});
                            img.addEventListener('error', resolve, {once: true});
                            // 大图解码超时保护 (10秒)
                            setTimeout(resolve, 10000);
                        });
                    })
                );
            }""")
    import time

    time.sleep(2)


# ---------------------------------------------------------------------------
# 最终 PDF 构建 (双 Pass)
# ---------------------------------------------------------------------------


def _build_final_pdf_bytes(page, pdf_kwargs: dict) -> bytes:
    # 0. 切换到 print 模式: 让 CSS @media print 生效
    page.emulate_media(media="print")

    # 1. Preflight JS: 修改分页属性
    result = page.evaluate(_PREFLIGHT_JS)
    print(
        f"[预分页] M3面板={result['panels_with_data']}, "
        f"放松大块={result['relaxed_blocks']}"
    )

    # 等待 DOM 重排完成
    page.evaluate("() => new Promise(r => requestAnimationFrame(r))")

    # 2. Pass 1: 生成 PDF, 提取目录页码
    #    排版由 Python 侧 build_typeset_css() 预注入 CSS 完成, 不依赖 JS 运行时测量
    pdf_bytes = _page_pdf_segmented(page, pdf_kwargs)
    toc_pages = _extract_toc_pages(pdf_bytes)
    if not toc_pages:
        return pdf_bytes

    # 3. 注入目录页码 (使用绝对定位, 零高度影响)
    display_pages = _toc_pages_for_injection(toc_pages)
    injected = page.evaluate(_TOC_INJECT_JS, display_pages)
    print(f"[目录] 注入 {injected}/{len(display_pages)} 个页码")

    # 等待页码文本渲染
    page.evaluate("() => new Promise(r => requestAnimationFrame(r))")

    # 4. Pass 2: 最终 PDF
    final_bytes = _page_pdf_segmented(page, pdf_kwargs)
    return apply_progress_rail(final_bytes, toc_pages)
