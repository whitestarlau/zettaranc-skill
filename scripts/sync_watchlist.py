#!/usr/bin/env python3
"""
[薄壳] 同步自选股清单中"在 daily_kline 表里完全缺失"的股票
v2.10.0 重构：业务逻辑迁至 modules.data_sync.DataSyncer.sync_missing
"""
import argparse
import json
import os
import sys
from pathlib import Path

# 让 scripts/ 能 import 项目根的 modules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modules.data_sync import DataSyncer
from modules.tushare_client import TushareClient  # noqa: F401  触发 env / token 校验


def _load_watchlist() -> list:
    """
    读取自选股清单路径：优先 STOCKS_JSON env，否则项目内默认 data/stocks_final.json
    支持 JSON 格式：[{code, name}, ...]
    """
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
    p = argparse.ArgumentParser(description="同步缺失的自选股 K 线（薄壳）")
    p.add_argument("--days", type=int, default=730, help="同步天数")
    args = p.parse_args()

    ts_codes = _load_watchlist()
    if not ts_codes:
        print("自选股清单为空")
        return

    syncer = DataSyncer()
    results = syncer.sync_missing(ts_codes, days=args.days)
    synced = sum(1 for v in results.values() if v > 0)
    print(f"sync_missing 完成: 总 {len(ts_codes)} 只, 补齐 {len(results)} 只, 成功 {synced} 只")


if __name__ == "__main__":
    main()
