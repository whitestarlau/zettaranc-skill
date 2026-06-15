"""Mootdx 数据源实现（免费，无需 API Key，实现 DataSourceProvider 抽象基类）"""
import logging
from typing import Optional

import pandas as pd

from modules.providers.base import DataSourceProvider
from modules.providers.code_utils import tushare_to_mootdx

logger = logging.getLogger(__name__)


class MootdxProvider(DataSourceProvider):
    """Mootdx 数据源实现（免费，无需 API Key，作为 Tushare 备选）"""

    def __init__(self):
        self._client = None

    @property
    def name(self) -> str:
        return "mootdx"

    def _get_client(self):
        if self._client is None:
            from mootdx.quotes import Quotes
            self._client = Quotes.factory(market="std")
        return self._client

    def get_daily(self, ts_code: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        try:
            client = self._get_client()
            mdx_code = tushare_to_mootdx(ts_code)
            market, code = mdx_code.split(".")
            market = int(market)

            bars = client.bars(
                symbol=code,
                frequency=9,  # 日线
                offset=0,
                start=int(start_date[:4]),
                market=market,
            )
            if bars is None or len(bars) == 0:
                return None

            df = bars.copy()
            df = df.rename(columns={
                "volume": "vol",
                "code": "ts_code",
                "date": "trade_date",
            })
            df["ts_code"] = ts_code
            df["trade_date"] = pd.to_datetime(df["trade_date"]).dt.strftime("%Y%m%d")

            # 过滤日期范围
            df = df[(df["trade_date"] >= start_date) & (df["trade_date"] <= end_date)]

            # 计算涨跌幅
            close_col = df["close"].astype(float)
            df["pct_chg"] = close_col.pct_change() * 100
            df["pct_chg"] = df["pct_chg"].fillna(0).round(2)

            for col in ["open", "high", "low", "close", "vol", "amount"]:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce")

            return df[["ts_code", "trade_date", "open", "high", "low", "close", "vol", "amount", "pct_chg"]]
        except Exception as e:
            logger.error(f"MootdxProvider get_daily error for {ts_code}: {e}")
            return None

    def get_stock_basic(self) -> Optional[pd.DataFrame]:
        logger.warning("MootdxProvider does not support get_stock_basic")
        return None

    def get_moneyflow(self, ts_code: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        try:
            client = self._get_client()
            mdx_code = tushare_to_mootdx(ts_code)
            market, code = mdx_code.split(".")
            market = int(market)

            mf = client.moneyflow(market=market, symbol=code)
            if mf is None or len(mf) == 0:
                return None

            df = mf.copy()
            df["ts_code"] = ts_code
            if "date" in df.columns:
                df = df.rename(columns={"date": "trade_date"})
                df["trade_date"] = pd.to_datetime(df["trade_date"]).dt.strftime("%Y%m%d")
            # 过滤日期范围
            if "trade_date" in df.columns:
                df = df[(df["trade_date"] >= start_date) & (df["trade_date"] <= end_date)]
            return df
        except Exception as e:
            logger.error(f"MootdxProvider get_moneyflow error for {ts_code}: {e}")
            return None

    def get_financial_data(self, ts_code: str) -> Optional[pd.DataFrame]:
        logger.warning("MootdxProvider does not support get_financial_data")
        return None

    def get_trade_cal(self) -> Optional[pd.DataFrame]:
        logger.warning("MootdxProvider does not support get_trade_cal")
        return None

    def get_index_daily(self, ts_code: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        logger.warning("MootdxProvider does not support get_index_daily")
        return None

    def get_daily_basic(self, ts_code: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        logger.warning("MootdxProvider does not support get_daily_basic")
        return None

    def get_realtime_quote(self, ts_codes: list[str]) -> Optional[pd.DataFrame]:
        try:
            client = self._get_client()
            results = []
            for ts_code in ts_codes:
                mdx_code = tushare_to_mootdx(ts_code)
                market, code = mdx_code.split(".")
                market = int(market)
                quote = client.quote(market=market, symbol=code)
                if quote is not None and len(quote) > 0:
                    quote["ts_code"] = ts_code
                    results.append(quote)
            if results:
                return pd.concat(results, ignore_index=True)
            return None
        except Exception as e:
            logger.error(f"MootdxProvider get_realtime_quote error: {e}")
            return None

    def check_connection(self) -> bool:
        try:
            df = self.get_daily("000001.SZ", "20250101", "20250110")
            return df is not None and not df.empty
        except Exception:
            return False
