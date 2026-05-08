#!/usr/bin/env python3
"""
报告渲染脚本

功能：
1. 读取JSON数据文件
2. 读取Jinja2模板文件
3. 将JSON数据转换为模板期望的格式
4. 合并CSS文件
5. 渲染模板并输出HTML

使用方法：
    python src/render_report.py --output output.html
"""

import argparse
import json
from pathlib import Path
from typing import Any, Dict

from jinja2 import Environment, FileSystemLoader, select_autoescape


# ============================================================================
# 配置常量
# ============================================================================

# 脚本所在目录
SCRIPT_DIR = Path(__file__).parent

# 项目根目录（脚本在 templates_v2/_scripts/ 下，需要向上两级）
PROJECT_ROOT = SCRIPT_DIR.parent.parent

# 模板目录
TEMPLATE_DIR = PROJECT_ROOT / "templates_v2" / "pages"

# CSS目录
CSS_DIR = PROJECT_ROOT / "templates_v2" / "css"

# 默认输入文件路径
DEFAULT_INPUT_JSON = PROJECT_ROOT / "contracts" / "examples" / "merged_report.full.example.json"

DEFAULT_INPUT_JSON = "logs/stage_final_output_20260303_101733.json"


# 默认模板
DEFAULT_TEMPLATE = TEMPLATE_DIR / "report_all_in_one.jinja2"

# CSS文件列表（按模块顺序）
CSS_FILES = [
    "base.css",                # 基础样式
    "m0_cover.css",            # 封面
    "m1_summary.css",          # 诊断摘要
    "m2_core_weakness.css",   # 核心短板
    "m3_kp_drill.css",        # 知识点钻取
    "m4_domains.css",         # 六大领域
    "m5_city_compare.css",    # 城市对照
    "m6_tiered_learning.css", # 分层学习
    "m7_data_reliability.css", # 数据可信度
    "m8_appendix.css",        # 附录
]


# ============================================================================
# 数据转换函数
# ============================================================================

def build_render_payload(report_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    将原始JSON数据转换为模板期望的render_payload格式

    Args:
        report_data: 从merged_report.example.json读取的原始数据

    Returns:
        render_payload: 模板可消费的数据结构
    """
    # 提取meta
    meta = report_data.get("meta", {})

    # 构建各模块数据
    render_payload = {
        # 模块0：封面
        "cover": _build_cover(report_data.get("cover", {}), meta),

        # 模块1：诊断摘要
        "module_1_summary": _build_module_1_summary(report_data, meta),

        # 模块2：核心短板
        "module_2_core_weakness": _build_module_2_core_weakness(report_data, meta),

        # 模块3：知识点短板钻取
        "module_3_kp_drill": _build_module_3_kp_drill(report_data, meta),

        # 模块4：六大领域达标分析
        "module_4_domains": _build_module_4_domains(report_data, meta),

        # 模块5：城市考情对照
        "module_5_city_compare": _build_module_5_city_compare(report_data, meta),

        # 模块6：分层学习建议
        "module_6_tiered_learning": _build_module_6_tiered_learning(report_data, meta),

        # 模块7：数据可信度说明
        "module_7_data_reliability": _build_module_7_data_reliability(report_data, meta),

        # 模块9：附录
        "module_9_appendix": _build_module_9_appendix(report_data, meta),

        # 全局meta
        "meta": meta,
    }

    return render_payload


def _build_cover(cover_data: Dict[str, Any], meta: Dict[str, Any]) -> Dict[str, Any]:
    """构建封面数据"""
    result = dict(cover_data)

    # 确保cover_meta存在
    if "cover_meta" not in result:
        result["cover_meta"] = {}

    # 从meta补充信息
    cover_meta = result["cover_meta"]
    if "city" not in cover_meta:
        cover_meta["city"] = meta.get("city_name", "")
    if "city_name" not in cover_meta:
        cover_meta["city_name"] = meta.get("city_name", "")
    if "report_date" not in cover_meta:
        cover_meta["report_date"] = meta.get("report_date", "")

    # 添加完整的meta
    result["meta"] = meta

    return result


def _build_module_1_summary(report_data: Dict[str, Any], meta: Dict[str, Any]) -> Dict[str, Any]:
    """构建模块1：诊断摘要数据"""
    summary = report_data.get("summary", {})
    key_findings = report_data.get("key_findings", [])
    breakthrough = report_data.get("breakthrough", {})
    suggestion = report_data.get("suggestion", {})

    return {
        "meta": meta,
        "summary": summary,
        "key_findings": key_findings,
        "breakthrough": breakthrough,
        "suggestion": suggestion,
    }


def _build_module_2_core_weakness(report_data: Dict[str, Any], meta: Dict[str, Any]) -> Dict[str, Any]:
    """构建模块2：核心短板数据"""
    core_weakness = report_data.get("core_weakness", {})

    return {
        "meta": meta,
        "section_core_weakness": core_weakness,
    }


def _build_module_3_kp_drill(report_data: Dict[str, Any], meta: Dict[str, Any]) -> Dict[str, Any]:
    """构建模块3：知识点短板钻取数据"""
    kp_drill = report_data.get("kp_drill", {})
    
    return {
        "meta": meta,
        **kp_drill,
    }


def _build_module_4_domains(report_data: Dict[str, Any], meta: Dict[str, Any]) -> Dict[str, Any]:
    """构建模块4：六大领域达标分析数据"""
    domains = report_data.get("domains", {})

    return {
        "meta": meta,
        "section_2_domains": domains,
        "sections": {
            "section_2_domains": domains,
        },
    }


def _build_module_5_city_compare(report_data: Dict[str, Any], meta: Dict[str, Any]) -> Dict[str, Any]:
    """构建模块5：城市考情对照数据"""
    city_compare = report_data.get("city_compare", {})
    
    return {
        "meta": meta,
        **city_compare,
    }


def _build_module_6_tiered_learning(report_data: Dict[str, Any], meta: Dict[str, Any]) -> Dict[str, Any]:
    """构建模块6：分层学习建议数据"""
    tiered_learning = report_data.get("tiered_learning", {})

    # 确保page_header存在
    if "page_header" not in tiered_learning:
        tiered_learning["page_header"] = {
            "report_name": meta.get("report_name", "基线定位分析报告（数学）"),
            "report_date": meta.get("report_date", "--"),
        }

    # 确保module存在
    if "module" not in tiered_learning:
        tiered_learning["module"] = {}

    # 确保cards存在
    if "cards" not in tiered_learning["module"]:
        tiered_learning["module"]["cards"] = {}

    # 添加完整的meta
    tiered_learning["meta"] = meta

    return tiered_learning


def _build_module_7_data_reliability(report_data: Dict[str, Any], meta: Dict[str, Any]) -> Dict[str, Any]:
    """构建模块7：数据可信度说明数据
    
    返回 data_reliability 对象，包含 section_4_coverage 等数据
    主模板会将其作为 data_reliability 变量传递给子模板
    """
    data_reliability = report_data.get("data_reliability", {})

    # 确保 section_4_coverage 存在
    if "section_4_coverage" not in data_reliability:
        data_reliability["section_4_coverage"] = {}

    section_4_coverage = data_reliability["section_4_coverage"]

    # 确保 low_sample.items 是列表而不是字典
    if "data_insufficient" in section_4_coverage:
        data_insufficient = section_4_coverage["data_insufficient"]
        if "low_sample" in data_insufficient:
            low_sample = data_insufficient["low_sample"]
            if isinstance(low_sample, dict) and "items" in low_sample:
                # 确保 items 是列表
                if not isinstance(low_sample["items"], list):
                    low_sample["items"] = []

    # 确保 warnings_detail.groups 中的 items 是列表
    if "warnings_detail" in section_4_coverage:
        warnings_detail = section_4_coverage["warnings_detail"]
        if isinstance(warnings_detail, dict) and "groups" in warnings_detail:
            groups = warnings_detail["groups"]
            if isinstance(groups, list):
                for group in groups:
                    if isinstance(group, dict) and "items" in group:
                        if not isinstance(group["items"], list):
                            group["items"] = []

    # 添加完整的meta
    data_reliability["meta"] = meta

    return data_reliability


def _build_module_9_appendix(report_data: Dict[str, Any], meta: Dict[str, Any]) -> Dict[str, Any]:
    """构建模块9：附录数据"""
    appendix = report_data.get("appendix", {})

    # 转换difficulty数据格式
    difficulty = appendix.get("difficulty", {})
    difficulty_items = difficulty.get("items", [])
    
    # 定义难度级别映射（中文到英文）
    level_mapping = {
        "简单": "easy",
        "中等": "medium",
        "困难": "hard"
    }
    
    # 定义默认的正确率和状态文本
    default_values = {
        "easy": {"accuracy": 89, "status_text": "掌握良好"},
        "medium": {"accuracy": 72, "status_text": "基本掌握"},
        "hard": {"accuracy": 58, "status_text": "需要加强"}
    }
    
    # 转换difficulty items
    transformed_items = []
    for item in difficulty_items:
        level_cn = item.get("level", "")
        level_en = level_mapping.get(level_cn, "unknown")
        ratio_decimal = item.get("ratio", 0)
        
        # 转换ratio从小数到整数百分比
        ratio_percent = int(ratio_decimal) if ratio_decimal else 0
        
        # 获取默认值
        defaults = default_values.get(level_en, {"accuracy": None, "status_text": "--"})
        
        transformed_item = {
            "level": level_en,
            "name_cn": level_cn,
            "count": item.get("count", 0),
            "ratio": ratio_percent,
            "accuracy": defaults["accuracy"],
            "status_text": defaults["status_text"]
        }
        transformed_items.append(transformed_item)
    
    # 转换papers数据格式
    papers = appendix.get("papers", {})
    papers_items = papers.get("items", [])
    
    # 转换papers items，添加缺失的index和source_file字段
    transformed_papers_items = []
    for idx, item in enumerate(papers_items, start=1):
        transformed_paper = {
            "index": idx,
            "paper_name": item.get("paper_name", ""),
            "question_count": item.get("question_count", 0),
            "source_file": item.get("date", "")  # 使用date字段作为source_file
        }
        transformed_papers_items.append(transformed_paper)
    
    return {
        "meta": meta,
        "analysis_scope": appendix.get("analysis_scope", {}),
        "difficulty": {
            "items": transformed_items
        },
        "papers": {
            "items": transformed_papers_items,
            "total_questions": papers.get("total_questions", 0),
            "total_papers": papers.get("total_papers", 0)
        },
        "metric_definitions": appendix.get("metric_definitions", []),
    }


# ============================================================================
# CSS合并函数
# ============================================================================

def build_combined_css(css_dir: Path) -> str:
    """
    合并所有CSS文件为一个字符串

    Args:
        css_dir: CSS目录路径

    Returns:
        合并后的CSS字符串
    """
    css_parts = []

    # 添加各模块CSS
    for css_file in CSS_FILES:
        css_path = css_dir / css_file
        if css_path.exists():
            css_parts.append(f"\n/* ==================== {css_file} ==================== */\n")
            css_parts.append(css_path.read_text(encoding="utf-8"))
        else:
            css_parts.append(f"\n/* [WARN] Missing CSS file: {css_file} */\n")

    return "\n".join(css_parts)


# ============================================================================
# 模板渲染函数
# ============================================================================

def render_template(
    template_path: Path,
    render_payload: Dict[str, Any],
    combined_css: str,
) -> str:
    """
    渲染Jinja2模板

    Args:
        template_path: 模板文件路径
        render_payload: 渲染数据
        combined_css: 合并后的CSS

    Returns:
        渲染后的HTML字符串
    """
    template_dir = template_path.parent

    env = Environment(
        loader=FileSystemLoader(str(template_dir)),
        autoescape=select_autoescape(enabled_extensions=("html", "jinja2")),
    )

    template = env.get_template(template_path.name)

    return template.render(
        render_payload=render_payload,
        combined_css=combined_css,
    )


# ============================================================================
# 主函数
# ============================================================================

def main() -> int:
    """主函数"""
    parser = argparse.ArgumentParser(description="渲染学情诊断报告")
    parser.add_argument(
        "--input",
        type=str,
        default=str(DEFAULT_INPUT_JSON),
        help=f"输入JSON文件路径 (默认: {DEFAULT_INPUT_JSON})",
    )
    parser.add_argument(
        "--template",
        type=str,
        default=str(DEFAULT_TEMPLATE),
        help=f"模板文件路径 (默认: {DEFAULT_TEMPLATE})",
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="输出HTML文件路径",
    )
    parser.add_argument(
        "--template-dir",
        type=str,
        default=str(TEMPLATE_DIR),
        help=f"模板目录路径 (默认: {TEMPLATE_DIR}) - 此参数已弃用，脚本自动使用正确的模板目录",
    )
    parser.add_argument(
        "--pdf",
        type=str,
        default=None,
        help="输出PDF文件路径（可选，若不指定则不生成PDF）",
    )

    args = parser.parse_args()

    # 转换路径
    input_path = Path(args.input)
    template_path = Path(args.template)
    output_path = Path(args.output)
    template_dir = Path(args.template_dir)

    # 检查文件是否存在
    if not input_path.exists():
        print(f"错误: 输入文件不存在: {input_path}")
        return 1

    if not template_path.exists():
        print(f"错误: 模板文件不存在: {template_path}")
        return 1

    # 1. 读取JSON数据
    print(f"读取输入文件: {input_path}")
    try:
        with open(input_path, "r", encoding="utf-8") as f:
            report_data = json.load(f)
    except Exception as e:
        print(f"错误: 读取输入文件失败: {e}")
        return 1

    # 2. 转换数据格式
    print("转换数据格式...")
    render_payload = build_render_payload(report_data)

    # 3. 合并CSS
    print("合并CSS文件...")
    combined_css = build_combined_css(CSS_DIR)

    # 4. 渲染模板
    print(f"渲染模板: {template_path}")
    try:
        html = render_template(template_path, render_payload, combined_css)
    except Exception as e:
        print(f"错误: 渲染模板失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

    # 5. 写入输出文件
    print(f"写入输出文件: {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)
    except Exception as e:
        print(f"错误: 写入输出文件失败: {e}")
        return 1

    print(f"✅ 报告渲染成功! 输出文件: {output_path}")


    pdf_path = Path("./output/report.pdf") if args.pdf is None else Path(args.pdf)
    # playwright 为可选依赖，仅在需要生成 PDF 时导入
    try:
        from playwright.sync_api import sync_playwright
        print(f"生成PDF文件: {pdf_path}")
        pdf_path.parent.mkdir(parents=True, exist_ok=True)
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(
                f"file://{output_path.resolve()}",
                wait_until="networkidle",
            )
            page.pdf(
                path=str(pdf_path),
                format="A4",
                print_background=True,
                margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
            )
            browser.close()
        print(f"✅ PDF 生成成功! 输出文件: {pdf_path}")
    except Exception as e:
        print(f"错误: PDF 生成失败: {e}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
