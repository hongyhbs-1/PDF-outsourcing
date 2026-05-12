"""Build a standalone preview HTML for the two-page learning blueprint."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import jinja2

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src_v2.services.learning_blueprint_builder import build_learning_blueprints  # noqa: E402


def main() -> None:
    sample_path = ROOT / "examples" / "sample_minimal_render_payload.json"
    payload = json.loads(sample_path.read_text(encoding="utf-8"))
    context = dict(payload)
    context.update(build_learning_blueprints(payload))

    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(ROOT / "templates_v2")),
        autoescape=True,
        undefined=jinja2.Undefined,
    )
    css = (ROOT / "templates_v2" / "css" / "m00_learning_blueprint.css").read_text(encoding="utf-8")
    html = """<!DOCTYPE html>
<html lang=\"zh-CN\">
<head><meta charset=\"utf-8\"><title>Learning Blueprint Preview</title><style>
@page { size: A4 portrait; margin: 0; }
body { margin:0; background:#e5e7eb; font-family: 'Noto Sans SC', 'PingFang SC', 'Microsoft YaHei', sans-serif; }
.module-page, .m0-module-page { break-before: page; }
.module-page:first-child, .m0-module-page:first-child { break-before:auto; }
""" + css + """</style></head><body>
"""
    html += env.get_template("m00_student_diagnostic_blueprint.jinja2").render(**context)
    html += env.get_template("m01_tutoring_execution_blueprint.jinja2").render(**context)
    html += "</body></html>"
    out = ROOT / "examples" / "learning_blueprint_preview.html"
    out.write_text(html, encoding="utf-8")
    vm = {
        "diagnostic_blueprint": context["diagnostic_blueprint"],
        "execution_blueprint": context["execution_blueprint"],
    }
    (ROOT / "examples" / "sample_blueprint_view_model.json").write_text(json.dumps(vm, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
