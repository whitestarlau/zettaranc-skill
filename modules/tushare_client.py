"""向后兼容的 TushareClient 包装器，内部委托给 TushareProvider"""
import logging
from typing import Optional
import pandas as pd
from modules.providers.tushare_provider import TushareProvider

logger = logging.getLogger(__name__)


class TushareClient:
    """Tushare 客户端（向后兼容，内部委托给 TushareProvider）"""

    def __init__(self, token: Optional[str] = None):
        self._provider = TushareProvider(token=token)
        self._pro = self._provider._pro
        self.min_request_interval = self._provider.min_request_interval
        self.last_request_time = self._provider.last_request_time
        self.token = token or ""

    def get_daily(self, ts_code: str, start_date: str = "", end_date: str = "") -> Optional[pd.DataFrame]:
        return self._provider.get_daily(ts_code, start_date, end_date)

    def get_index_daily(self, ts_code: str, start_date: str = "", end_date: str = "") -> Optional[pd.DataFrame]:
        return self._provider.get_index_daily(ts_code, start_date, end_date)

    def get_realtime_quote(self, ts_codes: list[str]) -> Optional[pd.DataFrame]:
        return self._provider.get_realtime_quote(ts_codes)

    def get_moneyflow(self, ts_code: str, trade_date: str = "") -> Optional[pd.DataFrame]:
        return self._provider.get_moneyflow(ts_code, trade_date, trade_date)

    def get_stock_basic(self, ts_code: Optional[str] = None, name: Optional[str] = None) -> Optional[pd.DataFrame]:
        return self._provider.get_stock_basic()

    def get_financial_data(self, ts_code: str, start_date: str = "", end_date: str = "") -> Optional[pd.DataFrame]:
        return self._provider.get_financial_data(ts_code)

    def get_trade_cal(self, exchange: str = "SSE", start_date: str = "", end_date: str = "") -> Optional[pd.DataFrame]:
        return self._provider.get_trade_cal(exchange, start_date, end_date)

    def check_connection(self) -> bool:
        return self._provider.check_connection()

    def get_limit_list(self, trade_date: str) -> Optional[pd.DataFrame]:
        """TushareClient v1 compat — not supported via provider"""
        try:
            self._provider._rate_limit()
            return self._provider._pro.limit_list_d(trade_date=trade_date)
        except Exception as e:
            logger.error(f"get_limit_list failed: {e}")
            return None

    def get_top_list(self, trade_date: str) -> Optional[pd.DataFrame]:
        """TushareClient v1 compat — not supported via provider"""
        try:
            self._provider._rate_limit()
            return self._provider._pro.top_list(trade_date=trade_date)
        except Exception as e:
            logger.error(f"get_top_list failed: {e}")
            return None
