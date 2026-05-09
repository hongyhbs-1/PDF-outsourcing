#!/usr/bin/env python3
"""
批量渲染测试脚本 — 自动扫描 samples/json/*.json 生成 HTML + PDF

用法:
    python scripts/render_all_samples.py
    python scripts/render_all_samples.py 1
    python scripts/render_all_samples.py 2
    python scripts/render_all_samples.py 2 --comic-version v2026-04-29-filled-content

注: --comic-version 为旧漫画页兼容参数；学习蓝图方案不再读取漫画图片。

输出:
    samples/output/<样本名>/<样本名>.html
    samples/output/<样本名>/<样本名>.pdf
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
PROMPT_VERSIONS_DIR = PROJECT_DIR / "prompts" / "comic" / "versions"

# 将 scripts/ 加入 path 以便 import render_standalone
sys.path.insert(0, str(SCRIPT_DIR))
import render_standalone


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="批量渲染样本 HTML + PDF。",
    )
    parser.add_argument(
        "sample_count",
        nargs="?",
        type=int,
        help="可选。输入 N 时，只执行前 N 份样本；不输入时执行全部。",
    )
    parser.add_argument(
        "--comic-version",
        help="旧漫画页兼容参数；学习蓝图方案不再读取漫画图片。",
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


def select_samples(sample_files: list[str], limit: int | None) -> list[str]:
    if limit is None:
        return sample_files
    if limit < 1 or limit > len(sample_files):
        raise ValueError(f"sample_count 必须在 1 到 {len(sample_files)} 之间")
    return sample_files[:limit]


def resolve_comic_image_root(comic_version: str | None) -> Path | None:
    """Legacy no-op compatibility hook.

    The learning blueprint flow no longer reads comic image assets, so the
    legacy version flag is accepted but ignored.
    """
    return None


def load_payload(json_path: Path) -> dict:
    if hasattr(render_standalone, "_load_json"):
        payload = render_standalone._load_json(json_path)
        if payload is not None:
            return payload
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


def print_sample_header(*, index: int, total: int, sample_file: str,
                        html_path: Path, pdf_path: Path) -> None:
    print(f"\n{'─' * 50}")
    print(f"  [{index}/{total}] {sample_file}")
    print(f"  HTML → {html_path}")
    print(f"  PDF  → {pdf_path}")
    print(f"{'─' * 50}")


def render_sample(sample_file: str, *, index: int, total: int,
                  comic_image_root: Path | None) -> dict:
    json_path = SAMPLES_DIR / sample_file
    stem = json_path.stem
    out_dir = OUTPUT_DIR / stem
    out_dir.mkdir(parents=True, exist_ok=True)

    html_path = out_dir / f"{stem}.html"
    pdf_path = out_dir / f"{stem}.pdf"
    print_sample_header(
        index=index,
        total=total,
        sample_file=sample_file,
        html_path=html_path,
        pdf_path=pdf_path,
    )

    if not json_path.exists():
        print(f"  [SKIP] 文件不存在: {json_path}")
        return {"sample": sample_file, "status": "skip", "error": "file not found"}

    t0 = time.time()
    try:
        payload = load_payload(json_path)
        html = render_standalone.render_html(
            payload,
            comic_image_root=comic_image_root,
        )
        html_path.write_text(html, encoding="utf-8")
        print(f"  HTML: {html_path.stat().st_size:,} bytes")

        render_standalone.generate_pdf(html, str(pdf_path), payload)
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
        selected_samples = select_samples(sample_files, args.sample_count)
        comic_image_root = resolve_comic_image_root(args.comic_version)
    except ValueError as exc:
        print(f"[ERROR] {exc}")
        sys.exit(2)

    print("=" * 60)
    print(f"批量渲染测试 — {len(selected_samples)} / {len(sample_files)} 份样本")
    if args.comic_version is not None:
        print(f"旧漫画图片版本参数已保留兼容，学习蓝图不会读取图片 — {args.comic_version}")
    print("=" * 60)

    results = [
        render_sample(
            sample_file,
            index=index,
            total=len(selected_samples),
            comic_image_root=comic_image_root,
        )
        for index, sample_file in enumerate(selected_samples, start=1)
    ]
    ok_count = print_summary(results, len(selected_samples))

    sys.exit(0 if ok_count == len(selected_samples) else 1)


if __name__ == "__main__":
    main()
