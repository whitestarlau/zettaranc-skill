"""向后兼容的 TushareClient 包装器，内部委托给 TushareProvider"""
import logging
import os
from typing import Optional
import pandas as pd
from modules.providers.tushare_provider import TushareProvider

logger = logging.getLogger(__name__)

TUSHARE_API_URL = os.environ.get("TUSHARE_API_URL", "")


class TushareClient:
    """Tushare 客户端（向后兼容，内部委托给 TushareProvider）"""

    def __init__(self, token: Optional[str] = None):
        self.token = token or os.getenv("TUSHARE_TOKEN", "")
        data_mode = os.getenv("DATA_MODE", "websearch")

        # 保持旧的 JNB 模式验证行为（向后兼容）
        if data_mode == "jnb":
            if not self.token:
                raise ValueError(
                    "JNB 模式下未设置 TUSHARE_TOKEN，请在 .env 中配置。\n或者将 DATA_MODE 改为 websearch。"
                )
            if not TUSHARE_API_URL:
                raise ValueError(
                    "JNB 模式下未设置 TUSHARE_API_URL，请在 .env 中配置中转 API 地址。\n"
                    "示例：TUSHARE_API_URL=https://tt.xiaodefa.cn"
                )

        self._provider = TushareProvider(token=self.token)
        self._pro = self._provider._pro
        self.min_request_interval = self._provider.min_request_interval
        self.last_request_time = self._provider.last_request_time

    def _safe_call(self, method_name: str, *args, **kwargs) -> Optional[pd.DataFrame]:
        try:
            method = getattr(self._provider, method_name)
            return method(*args, **kwargs)
        except Exception as e:
            logger.error(f"{method_name} failed: {e}")
            return None

    def get_daily(self, ts_code: str, start_date: str = "", end_date: str = "") -> Optional[pd.DataFrame]:
        return self._safe_call("get_daily", ts_code, start_date, end_date)

    def get_index_daily(self, ts_code: str, start_date: str = "", end_date: str = "") -> Optional[pd.DataFrame]:
        return self._safe_call("get_index_daily", ts_code, start_date, end_date)

    def get_realtime_quote(self, ts_codes: list[str]) -> Optional[pd.DataFrame]:
        return self._safe_call("get_realtime_quote", ts_codes)

    def get_moneyflow(self, ts_code: str, trade_date: str = "") -> Optional[pd.DataFrame]:
        return self._safe_call("get_moneyflow", ts_code, trade_date, trade_date)

    def get_stock_basic(self, ts_code: Optional[str] = None, name: Optional[str] = None) -> Optional[pd.DataFrame]:
        df = self._safe_call("get_stock_basic")
        if df is not None and not df.empty:
            if ts_code:
                df = df[df["ts_code"] == ts_code]
            if name:
                df = df[df["name"].str.contains(name, na=False)]
        return df

    def get_financial_data(self, ts_code: str, start_date: str = "", end_date: str = "") -> Optional[pd.DataFrame]:
        return self._safe_call("get_financial_data", ts_code)

    def get_trade_cal(self, exchange: str = "SSE", start_date: str = "", end_date: str = "") -> Optional[pd.DataFrame]:
        return self._safe_call("get_trade_cal", exchange, start_date, end_date)

    def check_connection(self) -> bool:
        return self._provider.check_connection()

    def _rate_limit(self):
        """向后兼容的限流方法"""
        self._provider._rate_limit()

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


# 测试
if __name__ == "__main__":
    import sys
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    logging.basicConfig(level=logging.INFO)

    client = TushareClient()
    print("=" * 50)
    print("Tushare 中转 API 连通性测试")
    print("=" * 50)

    if client.check_connection():
        print("[PASS] 连通性测试通过")
    else:
        print("[FAIL] 连通性测试失败")

    print("\n=== 平安银行 (000001.SZ) 日线 ===")
    df = client.get_daily("000001.SZ", "20250508", "20250515")
    if df is not None and len(df) > 0:
        print(df[["trade_date", "open", "high", "low", "close", "pct_chg"]].to_string(index=False))
    else:
        print("无数据")

    print("\n=== 沪深300 (000300.SH) 指数日线 ===")
    df2 = client.get_index_daily("000300.SH", "20250508", "20250515")
    if df2 is not None and len(df2) > 0:
        print(df2[["trade_date", "open", "high", "low", "close", "pct_chg"]].to_string(index=False))
    else:
        print("无数据")

    print("\n=== 实时行情 ===")
    df3 = client.get_realtime_quote(["000300.SH", "000001.SZ"])
    if df3 is not None and len(df3) > 0:
        print(df3[["TS_CODE", "NAME", "PRICE", "HIGH", "LOW", "VOLUME"]].to_string(index=False))
    else:
        print("无数据")
