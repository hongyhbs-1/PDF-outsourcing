#!/usr/bin/env python3
"""HTML 预览宽度回归测试。"""

from __future__ import annotations

import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
BASE_CSS = PROJECT_ROOT / "templates" / "css" / "base.css"
M4_TEMPLATE = PROJECT_ROOT / "templates" / "pages" / "m4_domains.jinja2"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class HtmlPreviewWidthTest(unittest.TestCase):
    def test_module_page_has_screen_preview_a4_width(self) -> None:
        css = read_text(BASE_CSS)
        self.assertIn("@media screen", css)
        self.assertIn("width: var(--page-width);", css)
        self.assertIn("margin: 0 auto", css)

    def test_m4_template_uses_width_constrained_root_class(self) -> None:
        template = read_text(M4_TEMPLATE)
        self.assertIn('class="m4-module-domains m4-section-domains"', template)


if __name__ == "__main__":
    unittest.main()
