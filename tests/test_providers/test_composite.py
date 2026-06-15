import pandas as pd
import pytest
from modules.providers.base import DataSourceProvider
from modules.providers.composite import CompositeDataProvider


class MockProviderA(DataSourceProvider):
    """第一个 Provider：总是返回数据"""
    @property
    def name(self):
        return "mock_a"

    def get_daily(self, ts_code, start_date, end_date):
        return pd.DataFrame({"close": [1.0]})

    def get_stock_basic(self):
        return pd.DataFrame({"name": ["test"]})

    def get_moneyflow(self, ts_code, start_date, end_date):
        return pd.DataFrame({"net_mf": [100]})

    def get_financial_data(self, ts_code):
        return pd.DataFrame({"revenue": [1e8]})

    def get_trade_cal(self):
        return pd.DataFrame({"cal_date": ["20250101"]})

    def get_index_daily(self, ts_code, start_date, end_date):
        return pd.DataFrame({"close": [3000]})

    def get_daily_basic(self, ts_code, start_date, end_date):
        return pd.DataFrame({"pe": [15.0]})

    def get_realtime_quote(self, ts_codes):
        return pd.DataFrame({"price": [10.0], "ts_code": ts_codes[:1]})

    def check_connection(self):
        return True


class MockProviderB(DataSourceProvider):
    """第二个 Provider：总是返回 None（模拟失败）"""
    @property
    def name(self):
        return "mock_b"

    def get_daily(self, ts_code, start_date, end_date):
        return None

    def get_stock_basic(self):
        return None

    def get_moneyflow(self, ts_code, start_date, end_date):
        return None

    def get_financial_data(self, ts_code):
        return None

    def get_trade_cal(self):
        return None

    def get_index_daily(self, ts_code, start_date, end_date):
        return None

    def get_daily_basic(self, ts_code, start_date, end_date):
        return None

    def get_realtime_quote(self, ts_codes):
        return None

    def check_connection(self):
        return False


class MockProviderC(DataSourceProvider):
    @property
    def name(self):
        return "mock_c"

    def check_connection(self):
        return True

    def get_daily(self, ts_code, start_date, end_date):
        return pd.DataFrame({"close": [2.0]})

    # 其余均返回空
    def get_stock_basic(self): return None
    def get_moneyflow(self, ts_code, start_date, end_date): return None
    def get_financial_data(self, ts_code): return None
    def get_trade_cal(self): return None
    def get_index_daily(self, ts_code, start_date, end_date): return None
    def get_daily_basic(self, ts_code, start_date, end_date): return None
    def get_realtime_quote(self, ts_codes): return None


def test_composite_uses_first_provider():
    """A 能返回数据，不会走到 B"""
    comp = CompositeDataProvider([MockProviderA(), MockProviderB()])
    df = comp.get_daily("000001.SZ", "20250101", "20250110")
    assert df["close"].iloc[0] == 1.0


def test_composite_fallsback():
    """A 返回 None，B 返回数据，Composite 应返回 B 的数据"""
    comp = CompositeDataProvider([MockProviderB(), MockProviderA()])
    df = comp.get_daily("000001.SZ", "20250101", "20250110")
    assert df["close"].iloc[0] == 1.0


def test_composite_chain_with_three():
    """A 返回 None，B 返回 None，C 返回数据"""
    comp = CompositeDataProvider([MockProviderB(), MockProviderB(), MockProviderC()])
    df = comp.get_daily("000001.SZ", "20250101", "20250110")
    assert df is not None


def test_composite_all_fail():
    """所有 Provider 都返回 None → 最终返回 None"""
    comp = CompositeDataProvider([MockProviderB(), MockProviderB()])
    assert comp.get_daily("000001.SZ", "20250101", "20250110") is None


def test_composite_check_connection_any():
    """check_connection 只要有一个 True 就返回 True"""
    comp = CompositeDataProvider([MockProviderB(), MockProviderA()])
    assert comp.check_connection()


def test_composite_no_providers():
    with pytest.raises(ValueError):
        CompositeDataProvider([])


def test_composite_get_stock_basic():
    comp = CompositeDataProvider([MockProviderA()])
    df = comp.get_stock_basic()
    assert df is not None
    assert df["name"].iloc[0] == "test"


def test_composite_get_moneyflow():
    comp = CompositeDataProvider([MockProviderB(), MockProviderA()])
    df = comp.get_moneyflow("000001.SZ", "20250101", "20250110")
    assert df["net_mf"].iloc[0] == 100


def test_composite_name():
    comp = CompositeDataProvider([MockProviderA(), MockProviderB()])
    assert comp.name == "mock_a+mock_b"


def test_composite_handler_exception():
    """一个 provider 抛异常时，Composite 应跳过它尝试下一个"""
    class FailingProvider(DataSourceProvider):
        @property
        def name(self):
            return "failing"

        def get_daily(self, ts_code, start_date, end_date):
            raise RuntimeError("connection error")

        def get_stock_basic(self): return None
        def get_moneyflow(self, ts_code, start_date, end_date): return None
        def get_financial_data(self, ts_code): return None
        def get_trade_cal(self): return None
        def get_index_daily(self, ts_code, start_date, end_date): return None
        def get_daily_basic(self, ts_code, start_date, end_date): return None
        def get_realtime_quote(self, ts_codes): return None
        def check_connection(self): return False

    comp = CompositeDataProvider([FailingProvider(), MockProviderA()])
    df = comp.get_daily("000001.SZ", "20250101", "20250110")
    assert df["close"].iloc[0] == 1.0
