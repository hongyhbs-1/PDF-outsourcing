#!/usr/bin/env python3
"""
批量渲染测试脚本 — 自动扫描 samples/json/*.json 生成 HTML + PDF

用法:
    python scripts/render_all_samples.py 1 --学科 数学 --模式 报告
    python scripts/render_all_samples.py 9 --学科 数学 --模式 场景

参数:
    sample_index: 可选。输入 N 时，只执行排序后的第 N 份样本；不输入时执行全部。
    --学科: 必填，数学|英语。
    --模式: 必填，报告|场景。报告=家长版主报告；场景=单独两页招生蓝图。

输出:
    报告模式: samples/output/<样本名>/<样本名>.html / .pdf
    场景模式: samples/output/<样本名>/<样本名>_admissions_blueprint.html / .pdf
"""
import argparse
import json
import sys
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
SAMPLES_DIR = PROJECT_DIR / "samples" / "json"
OUTPUT_DIR = PROJECT_DIR / "samples" / "output"

# 将 scripts/ 加入 path 以便 import render_standalone
sys.path.insert(0, str(SCRIPT_DIR))
import render_standalone

SUBJECT_CHOICES = ("数学", "英语")
MODE_CHOICES = ("场景", "报告")
MODE_TO_VARIANT = {
    "报告": render_standalone.PARENT_REPORT_VARIANT,
    "场景": render_standalone.ADMISSIONS_BLUEPRINT_VARIANT,
}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="批量渲染样本 HTML + PDF。",
    )
    parser.add_argument(
        "sample_index",
        nargs="?",
        type=int,
        help="可选。输入 N 时，只执行排序后的第 N 份样本；不输入时执行全部。",
    )
    parser.add_argument(
        "--学科",
        dest="subject",
        required=True,
        choices=SUBJECT_CHOICES,
        help="必填。选择学科：数学 或 英语。",
    )
    parser.add_argument(
        "--模式",
        dest="mode",
        required=True,
        choices=MODE_CHOICES,
        help="必填。选择输出模式：报告=家长版主报告；场景=单独两页招生蓝图。",
    )
    return parser.parse_args(argv)


def discover_sample_files(samples_dir: Path = SAMPLES_DIR) -> list[str]:
    sample_files = sorted(
        path.name for path in samples_dir.glob("*.json")
        if path.is_file()
    )
    if not sample_files:
        raise ValueError(f"未找到 JSON 样本文件: {samples_dir}")
    return sample_files


def select_samples(sample_files: list[str], sample_index: int | None) -> list[str]:
    if sample_index is None:
        return sample_files
    if sample_index < 1 or sample_index > len(sample_files):
        raise ValueError(f"sample_index 必须在 1 到 {len(sample_files)} 之间")
    return [sample_files[sample_index - 1]]


def normalize_subject(value: object) -> str:
    text = str(value or "").strip().lower()
    if text in {"math", "mathematics", "数学"} or "数学" in text:
        return "数学"
    if text in {"english", "英语"} or "英语" in text:
        return "英语"
    return ""


def payload_subject(payload: dict) -> str:
    meta = payload.get("meta", {}) if isinstance(payload.get("meta", {}), dict) else {}
    cover = payload.get("cover", {}) if isinstance(payload.get("cover", {}), dict) else {}
    for value in (
        meta.get("subject_name"),
        meta.get("subject"),
        cover.get("subject"),
        meta.get("left_title"),
        meta.get("report_name"),
        meta.get("report_title"),
    ):
        subject = normalize_subject(value)
        if subject:
            return subject
    return ""


def validate_payload_subject(payload: dict, requested_subject: str, sample_file: str) -> None:
    actual_subject = payload_subject(payload)
    if actual_subject and actual_subject != requested_subject:
        raise ValueError(
            f"{sample_file} 的学科是 {actual_subject}，与 --学科 {requested_subject} 不一致"
        )


def load_payload(json_path: Path) -> dict:
    if hasattr(render_standalone, "_load_json"):
        payload = render_standalone._load_json(json_path)
        if payload is not None:
            return render_standalone.normalize_render_payload(payload)
    with open(json_path, "r", encoding="utf-8") as f:
        return render_standalone.normalize_render_payload(json.load(f))


def print_sample_header(*, index: int, total: int, sample_file: str,
                        mode: str, subject: str,
                        html_path: Path, pdf_path: Path) -> None:
    print(f"\n{'─' * 50}")
    print(f"  [{index}/{total}] {sample_file}")
    print(f"  学科: {subject} | 模式: {mode}")
    print(f"  HTML → {html_path}")
    print(f"  PDF  → {pdf_path}")
    print(f"{'─' * 50}")


def render_sample(sample_file: str, *, index: int, total: int,
                  subject: str, mode: str) -> dict:
    json_path = SAMPLES_DIR / sample_file
    stem = json_path.stem
    out_dir = OUTPUT_DIR / stem
    out_dir.mkdir(parents=True, exist_ok=True)

    if mode == "场景":
        html_path = out_dir / f"{stem}_admissions_blueprint.html"
        pdf_path = out_dir / f"{stem}_admissions_blueprint.pdf"
    else:
        html_path = out_dir / f"{stem}.html"
        pdf_path = out_dir / f"{stem}.pdf"
    report_variant = MODE_TO_VARIANT[mode]
    print_sample_header(
        index=index,
        total=total,
        sample_file=sample_file,
        mode=mode,
        subject=subject,
        html_path=html_path,
        pdf_path=pdf_path,
    )

    if not json_path.exists():
        print(f"  [SKIP] 文件不存在: {json_path}")
        return {"sample": sample_file, "status": "skip", "error": "file not found"}

    t0 = time.time()
    try:
        payload = load_payload(json_path)
        validate_payload_subject(payload, subject, sample_file)
        html = render_standalone.render_html(
            payload,
            report_variant=report_variant,
        )
        html_path.write_text(html, encoding="utf-8")
        print(f"  HTML: {html_path.stat().st_size:,} bytes")

        render_standalone.generate_pdf(
            str(pdf_path),
            payload,
            report_variant=report_variant,
        )
        pdf_size = pdf_path.stat().st_size if pdf_path.exists() else 0
        elapsed = time.time() - t0
        print(f"  PDF:  {pdf_size:,} bytes")
        print(f"  耗时: {elapsed:.1f}s")
        return {"sample": sample_file, "status": "ok", "time": elapsed}
    except Exception as e:
        elapsed = time.time() - t0
        print(f"  [FAIL] {e}")
        return {"sample": sample_file, "status": "fail", "error": str(e), "time": elapsed}


def print_summary(results: list[dict], total: int) -> int:
    print(f"\n{'=' * 60}")
    print("汇总结果")
    print("=" * 60)
    ok_count = 0
    for r in results:
        icon = "OK" if r["status"] == "ok" else ("SKIP" if r["status"] == "skip" else "FAIL")
        t = f"{r.get('time', 0):.1f}s" if "time" in r else "-"
        print(f"  [{icon:>4}] {r['sample']:45s} {t}")
        if r["status"] == "ok":
            ok_count += 1
    print(f"\n  成功: {ok_count}/{total}")

    if ok_count < total:
        print("\n  失败详情:")
        for r in results:
            if r["status"] != "ok":
                print(f"    {r['sample']}: {r.get('error', 'unknown')}")
    return ok_count


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    try:
        sample_files = discover_sample_files()
        selected_samples = select_samples(sample_files, args.sample_index)
    except ValueError as exc:
        print(f"[ERROR] {exc}")
        sys.exit(2)

    print("=" * 60)
    if args.sample_index is None:
        print(f"批量渲染测试 — 全部 {len(selected_samples)} / {len(sample_files)} 份样本")
    else:
        print(f"批量渲染测试 — 第 {args.sample_index} / {len(sample_files)} 份样本")
    print(f"学科: {args.subject} | 模式: {args.mode}")
    print("=" * 60)

    results = []
    for selected_index, sample_file in enumerate(selected_samples, start=1):
        display_index = args.sample_index if args.sample_index is not None else selected_index
        display_total = len(sample_files) if args.sample_index is not None else len(selected_samples)
        results.append(
            render_sample(
                sample_file,
                index=display_index,
                total=display_total,
                subject=args.subject,
                mode=args.mode,
            )
        )
    ok_count = print_summary(results, len(selected_samples))

    sys.exit(0 if ok_count == len(selected_samples) else 1)


if __name__ == "__main__":
    main()
