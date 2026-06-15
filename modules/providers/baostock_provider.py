"""Baostock 数据源实现（免费，需 bs.login/bs.logout，懒初始化）"""
import logging
import threading
from typing import Optional

import pandas as pd

from modules.providers.base import DataSourceProvider
from modules.providers.code_utils import tushare_to_baostock

logger = logging.getLogger(__name__)


class BaostockProvider(DataSourceProvider):
    """Baostock 数据源实现（免费，需 login/logout，懒初始化）

    Baostock 需要先 bs.login() 再查询，查询完成后应 bs.logout()。
    本 Provider 采用懒初始化 + 线程安全锁。
    """

    def __init__(self):
        self._logged_in = False
        self._lock = threading.Lock()

    @property
    def name(self) -> str:
        return "baostock"

    def _ensure_login(self):
        if not self._logged_in:
            with self._lock:
                if not self._logged_in:
                    import baostock as bs
                    lg = bs.login()
                    if lg.error_code != "0":
                        logger.error(f"Baostock login failed: {lg.error_msg}")
                        return False
                    self._logged_in = True
        return True

    def _ensure_logout(self):
        if self._logged_in:
            with self._lock:
                if self._logged_in:
                    import baostock as bs
                    bs.logout()
                    self._logged_in = False

    def _safe_query(self, query_func, *args, **kwargs):
        if not self._ensure_login():
            return None
        try:
            rs = query_func(*args, **kwargs)
            if rs.error_code != "0":
                logger.error(f"Baostock query error: {rs.error_msg}")
                return None
            return rs
        except Exception as e:
            logger.error(f"Baostock query exception: {e}")
            return None

    def _to_date_str(self, date_str: str) -> str:
        """YYYYMMDD -> YYYY-MM-DD"""
        return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"

    def _result_to_df(self, rs, columns: list[str]) -> Optional[pd.DataFrame]:
        rows = []
        while rs.next():
            rows.append(rs.get_row_data())
        if not rows:
            return None
        df = pd.DataFrame(rows, columns=columns)
        for col in columns[1:]:
            if col != "trade_date":
                df[col] = pd.to_numeric(df[col], errors="coerce")
        return df

    def get_daily(self, ts_code: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        import baostock as bs
        bs_code = tushare_to_baostock(ts_code)

        rs = self._safe_query(
            bs.query_history_k_data_plus,
            bs_code,
            "date,open,high,low,close,volume,amount,pctChg",
            start_date=self._to_date_str(start_date),
            end_date=self._to_date_str(end_date),
            frequency="d",
            adjustflag="2",  # 前复权
        )
        if rs is None:
            return None

        df = self._result_to_df(rs, ["trade_date", "open", "high", "low", "close", "vol", "amount", "pct_chg"])
        if df is None:
            return None

        df["ts_code"] = ts_code
        df["trade_date"] = df["trade_date"].str.replace("-", "")
        return df[["ts_code", "trade_date", "open", "high", "low", "close", "vol", "amount", "pct_chg"]]

    def get_stock_basic(self) -> Optional[pd.DataFrame]:
        import baostock as bs

        # 查询所有股票
        rs = self._safe_query(bs.query_all_stock, day="2026-01-01")
        if rs is None:
            return None

        all_stocks = []
        while rs.next():
            all_stocks.append(rs.get_row_data())

        if not all_stocks:
            return None

        df = pd.DataFrame(all_stocks, columns=["code", "trade_date", "code_name", "status", "type"])
        df = df[df["type"] == "1"].copy()  # 只保留股票（type=1），排除指数（type=2）

        # 转换为 Tushare 格式
        df["ts_code"] = df["code"].apply(
            lambda x: x.split(".")[1] + "." + x.split(".")[0].upper()
        )
        df["name"] = df["code_name"]

        # 补充行业分类
        industry_map = {}
        industry_rs = self._safe_query(bs.query_stock_industry)
        if industry_rs:
            while industry_rs.next():
                row = industry_rs.get_row_data()
                code = row[0]
                industry_name = row[-1]
                industry_map[code] = industry_name

        df["industry"] = df["code"].map(industry_map).fillna("")
        df["area"] = ""
        df["market"] = df["code"].apply(lambda x: x.split(".")[0].upper())
        df["list_date"] = df["trade_date"].str.replace("-", "")

        return df[["ts_code", "name", "area", "industry", "market", "list_date"]]

    def get_moneyflow(self, ts_code: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        logger.warning("BaostockProvider does not support get_moneyflow yet")
        return None

    def get_financial_data(self, ts_code: str) -> Optional[pd.DataFrame]:
        logger.warning("BaostockProvider does not support get_financial_data yet")
        return None

    def get_trade_cal(self) -> Optional[pd.DataFrame]:
        import baostock as bs
        rs = self._safe_query(bs.query_trade_dates, start_date="1990-01-01", end_date="2026-12-31")
        if rs is None:
            return None

        df = self._result_to_df(rs, ["trade_date", "is_open"])
        if df is None:
            return None

        df["trade_date"] = df["trade_date"].str.replace("-", "")
        return df

    def get_index_daily(self, ts_code: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        import baostock as bs
        bs_code = tushare_to_baostock(ts_code)

        rs = self._safe_query(
            bs.query_history_k_data_plus,
            bs_code,
            "date,open,high,low,close,volume,amount,pctChg",
            start_date=self._to_date_str(start_date),
            end_date=self._to_date_str(end_date),
            frequency="d",
            adjustflag="3",  # 不复权（指数的复权无意义）
        )
        if rs is None:
            return None

        df = self._result_to_df(rs, ["trade_date", "open", "high", "low", "close", "vol", "amount", "pct_chg"])
        if df is None:
            return None

        df["ts_code"] = ts_code
        df["trade_date"] = df["trade_date"].str.replace("-", "")
        return df[["ts_code", "trade_date", "open", "high", "low", "close", "vol", "amount", "pct_chg"]]

    def get_daily_basic(self, ts_code: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        logger.warning("BaostockProvider does not support get_daily_basic yet")
        return None

    def get_realtime_quote(self, ts_codes: list[str]) -> Optional[pd.DataFrame]:
        logger.warning("BaostockProvider does not support get_realtime_quote")
        return None

    def check_connection(self) -> bool:
        try:
            df = self.get_daily("000001.SZ", "20250101", "20250110")
            return df is not None and not df.empty
        except Exception:
            return False
        finally:
            self._ensure_logout()
