from modules.providers.mootdx_provider import MootdxProvider


def test_provider_name():
    p = MootdxProvider()
    assert p.name == "mootdx"


def test_check_connection_no_data():
    """无网络环境也能正常返回 False 而非抛异常"""
    p = MootdxProvider()
    result = p.check_connection()
    assert result in (True, False)


def test_unsupported_methods_return_none():
    p = MootdxProvider()
    assert p.get_stock_basic() is None
    assert p.get_financial_data("000001.SZ") is None
    assert p.get_trade_cal() is None
    assert p.get_index_daily("000001.SZ", "20250101", "20250110") is None
    assert p.get_daily_basic("000001.SZ", "20250101", "20250110") is None
