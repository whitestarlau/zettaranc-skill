from modules.providers.code_utils import (
    tushare_to_baostock,
    tushare_to_mootdx,
    baostock_to_tushare,
    mootdx_to_tushare,
    is_valid_ts_code,
)


def test_tushare_to_baostock():
    assert tushare_to_baostock("000001.SZ") == "sz.000001"
    assert tushare_to_baostock("600487.SH") == "sh.600487"


def test_tushare_to_mootdx():
    assert tushare_to_mootdx("000001.SZ") == "1.000001"
    assert tushare_to_mootdx("600487.SH") == "0.600487"


def test_roundtrip_tushare_baostock():
    original = "000001.SZ"
    bs = tushare_to_baostock(original)
    assert baostock_to_tushare(bs) == original


def test_roundtrip_tushare_mootdx():
    original = "000001.SZ"
    mdx = tushare_to_mootdx(original)
    assert mootdx_to_tushare(mdx) == original


def test_is_valid_ts_code():
    assert is_valid_ts_code("000001.SZ")
    assert is_valid_ts_code("600487.SH")
    assert not is_valid_ts_code("000001")
    assert not is_valid_ts_code("000001.SZ1")
    assert not is_valid_ts_code("hello.SZ")
