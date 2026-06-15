from modules.providers.baostock_provider import BaostockProvider


def test_provider_name():
    p = BaostockProvider()
    assert p.name == "baostock"


def test_check_connection_no_data():
    """无网络环境也能正常返回 False 而非抛异常"""
    p = BaostockProvider()
    result = p.check_connection()
    assert result in (True, False)


def test_unsupported_methods_return_none():
    p = BaostockProvider()
    assert p.get_moneyflow("000001.SZ", "20250101", "20250110") is None
    assert p.get_financial_data("000001.SZ") is None
    assert p.get_daily_basic("000001.SZ", "20250101", "20250110") is None
    assert p.get_realtime_quote(["000001.SZ"]) is None
