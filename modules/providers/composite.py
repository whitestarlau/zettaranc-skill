"""CompositeDataProvider: 按优先级链式回退的数据源编排器"""
import logging
from typing import Optional

import pandas as pd

from modules.providers.base import DataSourceProvider

logger = logging.getLogger(__name__)


class CompositeDataProvider(DataSourceProvider):
    """复合数据源提供者：按优先级依次尝试每个 provider，第一个成功就返回

    用法:
        provider = CompositeDataProvider([TushareProvider(), MootdxProvider(), BaostockProvider()])
        df = provider.get_daily("000001.SZ", "20250101", "20250110")
        # 依次尝试 Tushare → Mootdx → Baostock，第一个有数据的返回
    """

    def __init__(self, providers: list[DataSourceProvider]):
        if not providers:
            raise ValueError("CompositeDataProvider requires at least one provider")
        self._providers = providers

    @property
    def name(self) -> str:
        return "+".join(p.name for p in self._providers)

    def _try_providers(self, method_name: str, *args, **kwargs) -> Optional[pd.DataFrame]:
        for p in self._providers:
            try:
                method = getattr(p, method_name)
                result = method(*args, **kwargs)
                if result is not None and not result.empty:
                    logger.debug(f"Composite: {p.name} returned data for {method_name}")
                    return result
                logger.debug(f"Composite: {p.name} returned empty for {method_name}")
            except Exception as e:
                logger.warning(f"Composite: {p.name} failed for {method_name}: {e}")
                continue
        return None

    def _try_providers_bool(self, method_name: str, *args, **kwargs) -> bool:
        for p in self._providers:
            try:
                method = getattr(p, method_name)
                result = method(*args, **kwargs)
                if result:
                    return True
            except Exception:
                continue
        return False

    def get_daily(self, ts_code: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        return self._try_providers("get_daily", ts_code, start_date, end_date)

    def get_stock_basic(self) -> Optional[pd.DataFrame]:
        return self._try_providers("get_stock_basic")

    def get_moneyflow(self, ts_code: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        return self._try_providers("get_moneyflow", ts_code, start_date, end_date)

    def get_financial_data(self, ts_code: str) -> Optional[pd.DataFrame]:
        return self._try_providers("get_financial_data", ts_code)

    def get_trade_cal(self) -> Optional[pd.DataFrame]:
        return self._try_providers("get_trade_cal")

    def get_index_daily(self, ts_code: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        return self._try_providers("get_index_daily", ts_code, start_date, end_date)

    def get_daily_basic(self, ts_code: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        return self._try_providers("get_daily_basic", ts_code, start_date, end_date)

    def get_realtime_quote(self, ts_codes: list[str]) -> Optional[pd.DataFrame]:
        return self._try_providers("get_realtime_quote", ts_codes)

    def check_connection(self) -> bool:
        return self._try_providers_bool("check_connection")
