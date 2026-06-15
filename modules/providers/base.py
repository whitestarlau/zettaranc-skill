from abc import ABC, abstractmethod
from typing import Optional
import pandas as pd


class DataSourceProvider(ABC):
    """数据源提供者抽象基类"""

    @property
    @abstractmethod
    def name(self) -> str:
        """数据源名称标识: tushare / mootdx / baostock"""
        ...

    @abstractmethod
    def get_daily(
        self,
        ts_code: str,
        start_date: str,
        end_date: str,
    ) -> Optional[pd.DataFrame]:
        """获取日 K 线数据，返回列: ts_code, trade_date, open, high, low, close, vol, amount, pct_chg"""
        ...

    @abstractmethod
    def get_stock_basic(self) -> Optional[pd.DataFrame]:
        """获取股票基本信息，返回列: ts_code, name, area, industry, market, list_date"""
        ...

    @abstractmethod
    def get_moneyflow(
        self,
        ts_code: str,
        start_date: str,
        end_date: str,
    ) -> Optional[pd.DataFrame]:
        """获取资金流向数据"""
        ...

    @abstractmethod
    def get_financial_data(self, ts_code: str) -> Optional[pd.DataFrame]:
        """获取财务指标数据"""
        ...

    @abstractmethod
    def get_trade_cal(self) -> Optional[pd.DataFrame]:
        """获取交易日历"""
        ...

    @abstractmethod
    def get_index_daily(
        self,
        ts_code: str,
        start_date: str,
        end_date: str,
    ) -> Optional[pd.DataFrame]:
        """获取指数日线"""
        ...

    @abstractmethod
    def get_daily_basic(
        self,
        ts_code: str,
        start_date: str,
        end_date: str,
    ) -> Optional[pd.DataFrame]:
        """获取每日基本面（PE/PB/PS/circ_mv）"""
        ...

    @abstractmethod
    def get_realtime_quote(self, ts_codes: list[str]) -> Optional[pd.DataFrame]:
        """获取实时行情"""
        ...

    @abstractmethod
    def check_connection(self) -> bool:
        """检查数据源连通性"""
        ...
