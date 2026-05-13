#!/usr/bin/env python3
"""
render_smoke_test.py — Jinja2 渲染冒烟测试

用 3 个 example 数据分别渲染完整报告:
  - Golden  → 期望成功, HTML 包含 9 个模块 CSS class
  - Minimal → 期望成功, 无 UndefinedError
  - Negative → 期望成功 (降级渲染, 不崩溃)

PASS 条件:
  - Golden 和 Minimal 渲染无 Exception
  - Golden HTML 包含 9 个模块 CSS class

用法:
  python render_smoke_test.py [--verbose]
"""

import json
import sys
import traceback
from pathlib import Path

try:
    import jinja2
except ImportError:
    print("[ERROR] 需要安装 jinja2: pip install jinja2")
    sys.exit(1)

# ---------------------------------------------------------------------------
# 路径配置
# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent
TEMPLATES_V2_DIR = SCRIPT_DIR.parent
PROJECT_ROOT = TEMPLATES_V2_DIR.parent
CONTRACTS_DIR = PROJECT_ROOT / "contracts"
EXAMPLES_DIR = CONTRACTS_DIR / "examples"
OUTPUT_DIR = SCRIPT_DIR / "_output"
CSS_DIR = TEMPLATES_V2_DIR / "css"

# 3 个 example 文件
EXAMPLES = {
    "golden": EXAMPLES_DIR / "golden_render_payload.json",
    "minimal": EXAMPLES_DIR / "minimal_render_payload.json",
    "negative": EXAMPLES_DIR / "negative_render_payload.json",
}

# 9 个模块期望的 CSS class (存在于 Golden HTML 中)
EXPECTED_MODULE_CLASSES = [
    "m0-cover",
    "m1-summary",
    "m2-core-weakness",
    "m3-kp-drill",
    "m4-domains",
    "m5-city-compare",
    "m6-tiered",
    "m7-reliability",
    "m8-appendix",
]


# ---------------------------------------------------------------------------
# CSS 拼接
# ---------------------------------------------------------------------------

def load_combined_css() -> str:
    """读取并拼接所有 CSS 文件"""
    css_parts = []

    # 先加载 base.css
    base_css = CSS_DIR / "base.css"
    if base_css.exists():
        css_parts.append(base_css.read_text(encoding='utf-8'))

    # 再加载模块 CSS (按名称排序)
    for css_file in sorted(CSS_DIR.glob("m*.css")):
        css_parts.append(css_file.read_text(encoding='utf-8'))

    return "\n".join(css_parts)


# ---------------------------------------------------------------------------
# Jinja2 环境
# ---------------------------------------------------------------------------

def create_jinja_env() -> jinja2.Environment:
    """创建 Jinja2 渲染环境 (宽松模式, 允许降级)"""
    return jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(TEMPLATES_V2_DIR)),
        undefined=jinja2.Undefined,  # 非 StrictUndefined, 允许降级
        autoescape=True,
    )


# ---------------------------------------------------------------------------
# 渲染单个 example
# ---------------------------------------------------------------------------

def render_example(env: jinja2.Environment, example_name: str,
                   example_path: Path, combined_css: str,
                   verbose: bool = False) -> dict:
    """
    渲染单个 example。
    返回 {status, html_length, warnings, error, module_classes_found}
    """
    result = {
        "name": example_name,
        "status": "UNKNOWN",
        "html_length": 0,
        "warnings": [],
        "error": None,
        "module_classes_found": [],
        "module_classes_missing": [],
    }

    # 加载 example 数据
    try:
        with open(example_path, 'r', encoding='utf-8') as f:
            payload = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        result["status"] = "ERROR"
        result["error"] = f"无法加载 {example_path.name}: {e}"
        return result

    # 准备渲染上下文
    context = dict(payload)
    context["combined_css"] = combined_css

    # 渲染
    try:
        template = env.get_template("report_master.jinja2")
        html = template.render(**context)
        result["html_length"] = len(html)
        result["status"] = "OK"

        # 检查模块 CSS class
        for cls in EXPECTED_MODULE_CLASSES:
            if cls in html:
                result["module_classes_found"].append(cls)
            else:
                result["module_classes_missing"].append(cls)

        # 写 HTML 文件
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        output_file = OUTPUT_DIR / f"{example_name}.html"
        output_file.write_text(html, encoding='utf-8')

    except jinja2.UndefinedError as e:
        result["status"] = "UNDEFINED_ERROR"
        result["error"] = f"UndefinedError: {e}"
        if verbose:
            traceback.print_exc()
    except jinja2.TemplateError as e:
        result["status"] = "TEMPLATE_ERROR"
        result["error"] = f"TemplateError: {e}"
        if verbose:
            traceback.print_exc()
    except Exception as e:
        result["status"] = "EXCEPTION"
        result["error"] = f"{type(e).__name__}: {e}"
        if verbose:
            traceback.print_exc()

    return result


# ---------------------------------------------------------------------------
# 主逻辑
# ---------------------------------------------------------------------------

def run_smoke_test(verbose: bool = False) -> dict:
    """
    执行渲染冒烟测试。
    返回结果字典。
    """
    print("=" * 60)
    print("Render Smoke Test: Jinja2 渲染冒烟测试")
    print("=" * 60)

    # 1. 加载 CSS
    print("\n1. 加载 CSS...")
    combined_css = load_combined_css()
    print(f"   CSS 总长度: {len(combined_css)} 字符")

    # 2. 创建 Jinja2 环境
    env = create_jinja_env()

    # 3. 逐个渲染
    all_results = {}
    overall_pass = True

    for example_name, example_path in EXAMPLES.items():
        print(f"\n--- 渲染 {example_name} ---")

        if not example_path.exists():
            print(f"  [SKIP] 文件不存在: {example_path}")
            all_results[example_name] = {
                "name": example_name,
                "status": "SKIP",
                "error": f"文件不存在: {example_path}",
            }
            continue

        result = render_example(env, example_name, example_path, combined_css, verbose)
        all_results[example_name] = result

        # 打印结果
        if result["status"] == "OK":
            found = len(result["module_classes_found"])
            missing = len(result["module_classes_missing"])
            print(f"  状态: OK | HTML: {result['html_length']} bytes")
            print(f"  模块 CSS class: {found}/9 found", end="")
            if missing > 0:
                print(f", missing: {result['module_classes_missing']}")
            else:
                print()
            output_file = OUTPUT_DIR / f"{example_name}.html"
            print(f"  输出: {output_file}")
        else:
            print(f"  状态: {result['status']}")
            if result["error"]:
                print(f"  错误: {result['error']}")

        # 判定
        if example_name in ("golden", "minimal"):
            if result["status"] != "OK":
                overall_pass = False
        # golden 额外检查 module classes
        if example_name == "golden":
            if result.get("module_classes_missing"):
                overall_pass = False

    # 4. 汇总
    status = "PASS" if overall_pass else "FAIL"

    final_result = {
        "status": status,
        "examples": all_results,
    }

    print(f"\n{'─' * 40}")
    for name, res in all_results.items():
        icon = "OK" if res["status"] == "OK" else res["status"]
        print(f"  {name:12s} → {icon}")
    print(f"{'─' * 40}")
    status_str = "PASS [OK]" if status == "PASS" else "FAIL [NG]"
    print(f"Smoke Test 结果: {status_str}")

    # 写 JSON 报告
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    report_file = OUTPUT_DIR / "smoke_test_report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(final_result, f, ensure_ascii=False, indent=2, default=str)
    print(f"详细报告: {report_file}")

    return final_result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    result = run_smoke_test(verbose=verbose)
    sys.exit(0 if result["status"] == "PASS" else 1)
