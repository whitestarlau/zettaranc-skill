import re


def tushare_to_baostock(ts_code: str) -> str:
    """000001.SZ -> sz.000001, 600487.SH -> sh.600487"""
    code, market = ts_code.split(".")
    market = market.lower()
    if market == "sz":
        return f"sz.{code}"
    elif market == "sh":
        return f"sh.{code}"
    raise ValueError(f"Unknown market: {market}")


def tushare_to_mootdx(ts_code: str) -> str:
    """000001.SZ -> 1.000001, 600487.SH -> 0.600487"""
    code, market = ts_code.split(".")
    if market == "SZ":
        return f"1.{code}"
    elif market == "SH":
        return f"0.{code}"
    raise ValueError(f"Unknown market: {market}")


def baostock_to_tushare(bs_code: str) -> str:
    """sz.000001 -> 000001.SZ, sh.600487 -> 600487.SH"""
    market, code = bs_code.split(".")
    return f"{code}.{market.upper()}"


def mootdx_to_tushare(mootdx_code: str) -> str:
    """1.000001 -> 000001.SZ, 0.600487 -> 600487.SH"""
    market_flag, code = mootdx_code.split(".")
    if market_flag == "1":
        return f"{code}.SZ"
    elif market_flag == "0":
        return f"{code}.SH"
    raise ValueError(f"Unknown mootdx market flag: {market_flag}")


def is_valid_ts_code(ts_code: str) -> bool:
    return bool(re.match(r"^\d{6}\.(SZ|SH)$", ts_code))
