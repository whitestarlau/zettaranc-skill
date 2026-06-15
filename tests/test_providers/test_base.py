import pytest
from modules.providers.base import DataSourceProvider


class ConcreteProvider(DataSourceProvider):
    @property
    def name(self):
        return "test"

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


def test_provider_instantiation():
    p = ConcreteProvider()
    assert p.name == "test"


def test_provider_cannot_instantiate_abc():
    with pytest.raises(TypeError):
        DataSourceProvider()
