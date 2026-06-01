#!/usr/bin/env python3
"""
[薄壳] 生成自选股池的 Z哥量化评估报告（markdown）
v2.10.0 重构：业务逻辑迁至 modules.report.assess_watchlist + render_assessment
"""
import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modules.report import assess_watchlist, write_assessment


def _load_watchlist() -> list:
    path = os.environ.get("STOCKS_JSON") or str(
        Path(__file__).resolve().parent.parent / "data" / "stocks_final.json"
    )
    with open(path) as f:
        items = json.load(f)
    return [
        item["code"] + ".SH" if item["code"].startswith("6") else item["code"] + ".SZ"
        for item in items
    ]


def main():
    p = argparse.ArgumentParser(description="生成自选股评估报告（薄壳）")
    p.add_argument(
        "--out",
        default=None,
        help="输出文件路径，默认 ./data/stocks_assessment_<时间>.md",
    )
    args = p.parse_args()

    ts_codes = _load_watchlist()
    if not ts_codes:
        print("自选股清单为空")
        return

    assessments = assess_watchlist(ts_codes)
    n_with_indicator = sum(1 for a in assessments if a.has_indicator)
    print(f"已加载 {len(assessments)} 只，{n_with_indicator} 只有完整量化指标")

    out_path = args.out or str(
        Path(__file__).resolve().parent.parent
        / "data"
        / f"stocks_assessment_{datetime.now().strftime('%Y%m%d_%H%M')}.md"
    )
    bytes_written = write_assessment(assessments, out_path)
    print(f"报告已写入: {out_path} ({bytes_written} 字节)")


if __name__ == "__main__":
    main()
