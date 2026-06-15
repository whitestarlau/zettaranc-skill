"""Tushare 数据源实现（实现 DataSourceProvider 抽象基类）"""
import os
import time
import logging
from typing import Optional

import pandas as pd
import tushare as ts

from modules.providers.base import DataSourceProvider

logger = logging.getLogger(__name__)

TUSHARE_TOKEN = os.getenv("TUSHARE_TOKEN", "")
TUSHARE_API_URL = os.getenv("TUSHARE_API_URL", "")
DATA_MODE = os.getenv("DATA_MODE", "websearch")


class TushareProvider(DataSourceProvider):
    """Tushare 数据源实现"""

    def __init__(self, token: Optional[str] = None):
        self.token = token or TUSHARE_TOKEN
        self._pro = None
        self.min_request_interval = 0.55
        self.last_request_time = 0.0

        if DATA_MODE == "jnb" and self.token and TUSHARE_API_URL:
            ts.set_token(self.token)
            self._pro = ts.pro_api()
            self._pro._DataApi__http_url = TUSHARE_API_URL

    @property
    def name(self) -> str:
        return "tushare"

    def _check_pro(self) -> bool:
        if self._pro is None:
            logger.warning("TushareProvider: pro_api not initialized (no token or wrong mode)")
            return False
        return True

    def _rate_limit(self):
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()

    def get_daily(self, ts_code: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        if not self._check_pro():
            return None
        self._rate_limit()
        try:
            df = ts.pro_bar(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date,
                adj="qfq",
                api=self._pro,
            )
            return df
        except Exception as e:
            logger.error(f"Tushare get_daily error for {ts_code}: {e}")
            return None

    def get_stock_basic(self) -> Optional[pd.DataFrame]:
        if not self._check_pro():
            return None
        self._rate_limit()
        try:
            return self._pro.stock_basic(
                exchange="", list_status="L", fields="ts_code,name,area,industry,market,list_date,is_hs"
            )
        except Exception as e:
            logger.error(f"Tushare get_stock_basic error: {e}")
            return None

    def get_moneyflow(self, ts_code: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        if not self._check_pro():
            return None
        self._rate_limit()
        try:
            return self._pro.moneyflow(ts_code=ts_code, start_date=start_date, end_date=end_date)
        except Exception as e:
            logger.error(f"Tushare get_moneyflow error for {ts_code}: {e}")
            return None

    def get_financial_data(self, ts_code: str) -> Optional[pd.DataFrame]:
        if not self._check_pro():
            return None
        self._rate_limit()
        try:
            return self._pro.fina_indicator(ts_code=ts_code)
        except Exception as e:
            logger.error(f"Tushare get_financial_data error for {ts_code}: {e}")
            return None

    def get_trade_cal(
        self, exchange: str = "SSE", start_date: str = "", end_date: str = ""
    ) -> Optional[pd.DataFrame]:
        if not self._check_pro():
            return None
        self._rate_limit()
        try:
            import datetime
            if not start_date:
                start_date = "19900101"
            if not end_date:
                end_date = datetime.datetime.now().strftime("%Y%m%d")
            return self._pro.trade_cal(exchange=exchange, start_date=start_date, end_date=end_date)
        except Exception as e:
            logger.error(f"Tushare get_trade_cal error: {e}")
            return None

    def get_index_daily(self, ts_code: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        if not self._check_pro():
            return None
        self._rate_limit()
        try:
            return self._pro.index_daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
        except Exception as e:
            logger.error(f"Tushare get_index_daily error for {ts_code}: {e}")
            return None

    def get_daily_basic(self, ts_code: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        if not self._check_pro():
            return None
        self._rate_limit()
        try:
            return self._pro.daily_basic(ts_code=ts_code, start_date=start_date, end_date=end_date)
        except Exception as e:
            logger.error(f"Tushare get_daily_basic error for {ts_code}: {e}")
            return None

    def get_realtime_quote(self, ts_codes: list[str]) -> Optional[pd.DataFrame]:
        if not self._check_pro():
            return None
        self._rate_limit()
        try:
            ts_code_str = ",".join(ts_codes)
            return ts.realtime_quote(ts_code=ts_code_str)
        except Exception as e:
            logger.error(f"Tushare get_realtime_quote error: {e}")
            return None

    def check_connection(self) -> bool:
        df = self.get_daily("000001.SZ", "20240101", "20240110")
        return df is not None and not df.empty
