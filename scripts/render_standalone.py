#!/usr/bin/env python3
"""
独立渲染脚本 — 外包专用

用法:
    # 只生成 HTML
    python render_standalone.py samples/json/sample_01_math_25q.json -o output.html

    # 生成 HTML + PDF (需要 playwright)
    python render_standalone.py samples/json/sample_01_math_25q.json -o output.html --pdf

依赖:
    pip install jinja2
    pip install playwright  # 仅 PDF 需要
    playwright install chromium  # 或用系统 Chrome: 脚本自动尝试
    pip install PyMuPDF  # 可选, 用于目录页码注入
"""
import argparse
import base64
import json
import os
import sys
import tempfile
from pathlib import Path

from learning_blueprint_builder import build_learning_blueprints
from pdf_chrome_templates import build_pdf_chrome_options
from pdf_progress_rail import apply_progress_rail

# 模板目录
SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
TEMPLATE_DIR = PROJECT_DIR / "templates"
CSS_DIR = TEMPLATE_DIR / "css"
PAGES_DIR = TEMPLATE_DIR / "pages"
FONTS_DIR = TEMPLATE_DIR / "fonts"
ASSETS_DIR = TEMPLATE_DIR / "assets"
STATIC_DIR = PROJECT_DIR / "static"
DEFAULT_COMIC_IMAGE_ROOT = STATIC_DIR / "comic"
COMIC_IMAGE_SUFFIX = ".png"
TIER_NEED_MAJOR_MAX = 60
TIER_ROOM_GROW_MAX = 85

try:
    from jinja2 import Environment, FileSystemLoader
except ImportError:
    print("请安装 jinja2: pip install jinja2")
    sys.exit(1)

# PyMuPDF 可选依赖 (目录页码提取)
try:
    import fitz  # PyMuPDF
    HAS_FITZ = True
except ImportError:
    HAS_FITZ = False

try:
    from golden_typeset.payload_analyzer import measure_dom_heights
    from golden_typeset.engine import build_typeset_css
    _HAS_GOLDEN = True
except ImportError:
    try:
        from scripts.golden_typeset.payload_analyzer import measure_dom_heights
        from scripts.golden_typeset.engine import build_typeset_css
        _HAS_GOLDEN = True
    except ImportError:
        _HAS_GOLDEN = False


# ---------------------------------------------------------------------------
# 预分页 JS (移植自 pdf_service.py)
# ---------------------------------------------------------------------------

_PREFLIGHT_JS = """
() => {
    const panels = document.querySelectorAll('.m3-kp-drill__panel');
    const panelsWithData = Array.from(panels).filter(
        panel => panel.querySelectorAll('tbody tr').length > 0
    );

    // --- M5: 强制清理 ---
    const m5 = document.querySelector('.m5-city-compare');
    if (m5) {
        m5.style.minHeight = 'auto';
        m5.style.pageBreakInside = 'auto';
    }

    // --- M1: 放松 breakthrough-grid 整体 avoid ---
    const btGrid = document.querySelector('.m1-breakthrough-grid');
    if (btGrid) {
        btGrid.style.breakInside = 'auto';
    }

    // --- M7: 置信度说明不独占页 ---
    document.querySelectorAll('.m7-note').forEach(note => {
        note.style.breakInside = 'auto';
        note.style.pageBreakInside = 'auto';
    });

    // --- 全局: 放松所有 >200px 块的 break-inside:avoid ---
    const THRESHOLD = 200;
    const avoidSelectors = [
        '.m1-suggestion-callout',
        '.m2-cw-tips-box',
        '.m4-chart-box',
        '.m4-summary-card',
    ];
    avoidSelectors.forEach(sel => {
        document.querySelectorAll(sel).forEach(el => {
            const h = el.getBoundingClientRect().height;
            if (h > THRESHOLD) {
                el.style.breakInside = 'auto';
                el.style.pageBreakInside = 'auto';
            }
        });
    });

    return {
        panels_total: panels.length,
        panels_with_data: panelsWithData.length,
        m5_fixed: !!m5,
        relaxed_blocks: avoidSelectors.length,
    };
}
"""

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
_TOC_DISPLAY_KEYS = {"m1", "m4", "m2", "m3", "m5", "m6", "m9", "m7", "m8"}

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
        "m4": ("二、六大领域达标分析",),
        "m2": ("三、核心短板清单",),
        "m3": ("四、知识点短板钻取",),
        "m5": ("五、城市考情对照",),
        "m6": ("六、分层与学习建议",),
        "m9": ("七、逐题分析明细",),
        "m7": ("七、数据", "八、数据"),
        "m8": ("分析范围",),
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
        is_toc_page = any(
            line.strip() in ("目 录", "目录")
            for line in lines[:5]
        )
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
        '<fontconfig>\n'
        f'  <dir>{FONTS_DIR.resolve()}</dir>\n'
        f'{include_line}'
        '</fontconfig>\n'
    )
    if not bundled_config.exists() or bundled_config.read_text(encoding="utf-8") != config_text:
        bundled_config.write_text(config_text, encoding="utf-8")
    os.environ["FONTCONFIG_FILE"] = str(bundled_config)


def _build_pdf_chrome_meta(payload: dict) -> dict:
    """Build PDF header/footer metadata from the full payload."""
    meta = dict(payload.get("meta") or {})
    cover_meta = payload.get("cover", {}).get("cover_meta", {}) or {}
    summary = payload.get("summary", {}) or {}

    meta.setdefault("grade", cover_meta.get("grade", ""))
    meta.setdefault("target_score_text", summary.get("target_score_text", ""))
    return meta


def _build_pdf_kwargs(payload: dict) -> dict:
    """构建 Playwright page.pdf() 参数, 含页眉页脚。"""
    return {
        "format": "A4",
        "print_background": True,
        **build_pdf_chrome_options(_build_pdf_chrome_meta(payload)),
    }


# ---------------------------------------------------------------------------
# 核心: CSS 合并 + HTML 渲染
# ---------------------------------------------------------------------------

def _rewrite_font_urls(css: str) -> str:
    """Rewrite bundled font URLs to absolute file URIs for PDF rendering."""
    font_file = FONTS_DIR / "NotoSansSC-Variable.ttf"
    if not font_file.exists():
        return css
    font_uri = font_file.resolve().as_uri()
    return css.replace("url('../fonts/NotoSansSC-Variable.ttf')", f"url('{font_uri}')")


def load_css() -> str:
    """合并所有 CSS 文件。
    
    加载顺序：base.css → m*.css（模块样式）→ shared_*.css（共享覆盖）
    不依赖文件名字母序 hack，显式控制优先级。
    """
    css_parts: list[str] = []
    base = CSS_DIR / "base.css"
    if base.exists():
        css_parts.append(base.read_text(encoding="utf-8"))
    # 模块 CSS（m*.css）
    for f in sorted(CSS_DIR.glob("m*.css")):
        css_parts.append(f.read_text(encoding="utf-8"))
    # 模块 CSS（非 m 前缀的模块样式，如 comic、student_profile 等）
    for f in sorted(CSS_DIR.glob("*.css")):
        if f.name == "base.css" or f.name.startswith("m") or f.name.startswith("shared_"):
            continue
        css_parts.append(f.read_text(encoding="utf-8"))
    # 共享覆盖（shared_*.css）— 最后加载，优先级最高
    for f in sorted(CSS_DIR.glob("shared_*.css")):
        css_parts.append(f.read_text(encoding="utf-8"))
    return _rewrite_font_urls("\n".join(css_parts))


def _image_to_data_uri(path: Path) -> str:
    """将本地图片文件转换为 data:image/...;base64,... Data URI。

    Playwright page.set_content() 创建 opaque origin, 无法加载 file:// 资源。
    将图片内嵌为 Data URI 可绕过此限制。
    """
    if not path.exists():
        return ""
    suffix_map = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".gif": "image/gif", ".svg": "image/svg+xml", ".webp": "image/webp"}
    mime = suffix_map.get(path.suffix.lower(), "image/png")
    b64 = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{b64}"


def _select_tier_name(payload: dict) -> str:
    """根据当前准确率选择漫画学生等级名。"""
    summary = payload.get("summary", {})
    acc = summary.get("current_accuracy", 0)

    if acc < TIER_NEED_MAJOR_MAX:
        return "差生"
    if acc < TIER_ROOM_GROW_MAX:
        return "中等生"
    return "优等生"


def _comic_image_candidates(image_root: Path, scene: str,
                            tier_name: str) -> list[Path]:
    return [image_root / scene / f"{tier_name}-中文{COMIC_IMAGE_SUFFIX}"]


def _select_comic_image_path(image_root: Path, scene: str, tier_name: str,
                             *, require_existing: bool) -> Path:
    candidates = _comic_image_candidates(image_root, scene, tier_name)
    for candidate in candidates:
        if candidate.exists():
            return candidate
    if require_existing:
        paths = ", ".join(str(candidate) for candidate in candidates)
        raise FileNotFoundError(f"漫画图片不存在: {paths}")
    return candidates[0]


def _resolve_comic_image_paths(tier_name: str,
                               comic_image_root: Path | None = None
                               ) -> tuple[Path, Path]:
    """解析场景1/2漫画图片路径。指定版本目录时必须图片存在。"""
    image_root = DEFAULT_COMIC_IMAGE_ROOT if comic_image_root is None else comic_image_root
    require_existing = comic_image_root is not None
    return (
        _select_comic_image_path(
            image_root, "scene1", tier_name,
            require_existing=require_existing,
        ),
        _select_comic_image_path(
            image_root, "scene2", tier_name,
            require_existing=require_existing,
        ),
    )


def render_html(payload: dict, comic_image_root: Path | None = None, typeset_css: str = "") -> str:
    """将 JSON payload 渲染为 HTML。"""
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=False,
    )
    template = env.get_template("report_master.jinja2")

    font_path = FONTS_DIR / "NotoSansSC-Variable.ttf"
    logo_path = ASSETS_DIR / "logo_dida985.png"

    context = dict(payload)
    context["combined_css"] = load_css() + typeset_css
    context["render_payload"] = payload
    context.update(build_learning_blueprints(payload))
    context["font_path"] = str(font_path)
    context["logo_path"] = _image_to_data_uri(logo_path)
    # Kept for compatibility with older templates/debug output. Opening comic
    # pages are now replaced by the dynamic learning blueprint pages.
    context["tier_name"] = _select_tier_name(payload)

    # 将封面 logo 路径也转为 Data URI (同因: page.set_content() 无法加载 file://)
    logo_data_uri = _image_to_data_uri(logo_path)
    cover = context.get("cover", context.get("module_0_cover", {}))
    brand = cover.get("brand", {}) if isinstance(cover, dict) else {}
    if logo_data_uri and isinstance(brand, dict):
        brand["logo_url"] = logo_data_uri

    # page_visibility 兜底
    if "page_visibility" not in context:
        context["page_visibility"] = {}
    pv = context["page_visibility"]
    pv.setdefault("m5_city_compare", True)
    pv.setdefault("m10_composition", False)
    pv.setdefault("m11_reading_deep", False)
    pv.setdefault("show_teacher_supplement", False)

    return template.render(**context)


# ---------------------------------------------------------------------------
# PDF 生成 (预分页 + 两阶段 TOC 注入)
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


def _build_final_pdf_bytes(page, pdf_kwargs: dict) -> bytes:
    # 0. 切换到 print 模式: 让 CSS @media print 生效
    page.emulate_media(media='print')

    # 1. Preflight JS: 修改分页属性
    result = page.evaluate(_PREFLIGHT_JS)
    print(f"[预分页] M3面板={result['panels_with_data']}, "
          f"放松大块={result['relaxed_blocks']}")

    # 等待 DOM 重排完成
    page.evaluate("() => new Promise(r => requestAnimationFrame(r))")

    # 2. Pass 1: 生成 PDF, 提取目录页码
    #    排版由 Python 侧 build_typeset_css() 预注入 CSS 完成, 不依赖 JS 运行时测量
    pdf_bytes = page.pdf(**pdf_kwargs)
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
    final_bytes = page.pdf(**pdf_kwargs)
    return apply_progress_rail(final_bytes, toc_pages)


def generate_pdf(output_path: str, payload: dict, comic_image_root=None) -> Path:
    """双 Pass 精确排版 → PDF。

    Pass 1: 渲染 HTML → 测量 DOM 高度
    Pass 2: 用测量值生成排版 CSS → 渲染 HTML → 生成 PDF
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("PDF 生成需要 playwright: pip install playwright")
        sys.exit(1)

    _ensure_fontconfig_env()
    pdf_kwargs = _build_pdf_kwargs(payload)
    output = Path(output_path)

    temp_html_paths: list[Path] = []
    with sync_playwright() as p:
        browser = _launch_chromium(p)
        page = browser.new_page()

        def load_html_via_file(html: str) -> None:
            """Load HTML from file:// so bundled fonts resolve in Chromium PDF."""
            with tempfile.NamedTemporaryFile(
                "w",
                suffix=".html",
                encoding="utf-8",
                delete=False,
            ) as temp_html:
                temp_html.write(html)
                temp_path = Path(temp_html.name)
            temp_html_paths.append(temp_path)
            page.goto(temp_path.as_uri(), wait_until="load")

        try:
            # -- Pass 1: 测量 DOM 高度 --
            measured = {}
            if _HAS_GOLDEN:
                html_pass1 = render_html(payload, comic_image_root=comic_image_root)
                load_html_via_file(html_pass1)
                page.emulate_media(media='print')
                try:
                    measured = measure_dom_heights(page)
                    print(f"[Pass 1] DOM 测量完成: {len(measured)} 个模块")
                except Exception as e:
                    print(f"[WARNING] Pass 1 DOM 测量失败, 回退到单 Pass 模式: {e}")
                    measured = {}

            # -- Pass 2: 精确排版 + PDF 生成 --
            typeset_css = ""
            if _HAS_GOLDEN and measured:
                typeset_css = build_typeset_css(payload, measured=measured)

            html_pass2 = render_html(payload, comic_image_root=comic_image_root, typeset_css=typeset_css)
            load_html_via_file(html_pass2)
            _wait_for_images(page)

            final_bytes = _build_final_pdf_bytes(page, pdf_kwargs)
            output.write_bytes(final_bytes)

            print(f"PDF: {output} ({output.stat().st_size:,} bytes)")
        finally:
            page.close()
            browser.close()
            for temp_html_path in temp_html_paths:
                temp_html_path.unlink(missing_ok=True)

    return output


# ---------------------------------------------------------------------------
# 入口
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="报告渲染 (外包独立使用)")
    parser.add_argument("json_file", help="render_payload JSON 文件路径")
    parser.add_argument("-o", "--output", default="output.html", help="输出 HTML 路径")
    parser.add_argument("--pdf", action="store_true", help="同时生成 PDF")
    args = parser.parse_args()

    with open(args.json_file, "r", encoding="utf-8") as f:
        payload = json.load(f)

    typeset_css = ""
    if _HAS_GOLDEN:
        typeset_css = build_typeset_css(payload)

    html = render_html(payload, typeset_css=typeset_css)
    Path(args.output).write_text(html, encoding="utf-8")
    print(f"HTML: {args.output}")

    if args.pdf:
        pdf_path = args.output.replace(".html", ".pdf")
        generate_pdf(pdf_path, payload)


if __name__ == "__main__":
    main()
