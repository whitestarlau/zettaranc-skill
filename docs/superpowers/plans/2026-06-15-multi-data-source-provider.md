# 多数据源 Provider 抽象层实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 为 zettaranc-skill 引入 DataSourceProvider 抽象层，新增 mootdx/baostock 作为 Tushare 的备选数据源

**Architecture:** 新增 `modules/providers/` 子包，包含 DataSourceProvider ABC、TushareProvider/MootdxProvider/BaostockProvider 三个实现、CompositeDataProvider 编排器。DataSyncer 改调 provider 而非直接调 Tushare SDK。

**Tech Stack:** Python 3.10+, mootdx, baostock, pandas, sqlite3

---

### Task 1: 基础设施 — base.py + code_utils.py

**Files:**
- Create: `modules/providers/__init__.py`
- Create: `modules/providers/base.py`
- Create: `modules/providers/code_utils.py`
- Test: `tests/test_providers/test_base.py`
- Test: `tests/test_providers/test_code_utils.py`

- [ ] **Step 1: Create `modules/providers/` package**

```bash
mkdir -p modules/providers tests/test_providers
```

- [ ] **Step 2: Write `modules/providers/base.py` with DataSourceProvider ABC**

```python
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
```

- [ ] **Step 3: Write `modules/providers/code_utils.py` with ts_code 转换工具**

```python
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
```

- [ ] **Step 4: Write tests for code_utils**

```python
# tests/test_providers/test_code_utils.py
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
```

- [ ] **Step 5: Write tests for base class (interface check)**

```python
# tests/test_providers/test_base.py
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
```

- [ ] **Step 6: Run tests and commit**

```bash
python -m pytest tests/test_providers/ -v
```

Expected: 7 passed

```bash
git add modules/providers/ tests/test_providers/
git commit -m "feat: add DataSourceProvider ABC and ts_code utils"
```

---

### Task 2: TushareProvider（从 TushareClient 抽取）

**Files:**
- Create: `modules/providers/tushare_provider.py`
- Modify: `modules/tushare_client.py`
- Test: `tests/test_providers/test_tushare_provider.py`

- [ ] **Step 1: Write `modules/providers/tushare_provider.py`**

从 `modules/tushare_client.py` 现有代码抽取，实现 DataSourceProvider。

```python
import os
import time
import logging
from typing import Optional

import pandas as pd
import tushare as ts

from modules.providers.base import DataSourceProvider

logger = logging.getLogger(__name__)

TUSHARE_TOKEN = os.getenv("TUSHARE_TOKEN", "")
TUSHARE_API_URL = os.getenv("TUSHARE_API_URL", "")
DATA_MODE = os.getenv("DATA_MODE", "websearch")


class TushareProvider(DataSourceProvider):
    """Tushare 数据源实现"""

    def __init__(self, token: Optional[str] = None):
        self.token = token or TUSHARE_TOKEN
        self._pro = None
        self.min_request_interval = 0.55

        if DATA_MODE == "jnb" and self.token and TUSHARE_API_URL:
            ts.set_token(self.token)
            self._pro = ts.pro_api()
            self._pro._DataApi__http_url = TUSHARE_API_URL

    @property
    def name(self) -> str:
        return "tushare"

    def _check_pro(self):
        if self._pro is None:
            logger.warning("TushareProvider: pro_api not initialized (no token or wrong mode)")
            return False
        return True

    def _rate_limit(self):
        time.sleep(self.min_request_interval)

    def _safe_call(self, func, *args, **kwargs):
        self._rate_limit()
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Tushare API error: {e}")
            return None

    def get_daily(self, ts_code: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        if not self._check_pro():
            return None
        # 使用 pro_bar 获取复权数据（与现有逻辑一致）
        df = self._safe_call(
            ts.pro_bar,
            ts_code=ts_code,
            adj="qfq",
            start_date=start_date,
            end_date=end_date,
        )
        if df is not None and not df.empty:
            df = df.rename(columns={"vol": "vol"})
            df["ts_code"] = ts_code
        return df

    def get_stock_basic(self) -> Optional[pd.DataFrame]:
        if not self._check_pro():
            return None
        return self._safe_call(self._pro.stock_basic)

    def get_moneyflow(self, ts_code: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        if not self._check_pro():
            return None
        df = self._safe_call(
            self._pro.moneyflow,
            ts_code=ts_code,
            start_date=start_date,
            end_date=end_date,
        )
        return df

    def get_financial_data(self, ts_code: str) -> Optional[pd.DataFrame]:
        if not self._check_pro():
            return None
        return self._safe_call(self._pro.fina_indicator, ts_code=ts_code)

    def get_trade_cal(self) -> Optional[pd.DataFrame]:
        if not self._check_pro():
            return None
        import datetime
        start = "19900101"
        end = datetime.datetime.now().strftime("%Y%m%d")
        df = self._safe_call(self._pro.trade_cal, start_date=start, end_date=end)
        if df is not None:
            df = df[df["is_open"] == 1]
        return df

    def get_index_daily(self, ts_code: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        if not self._check_pro():
            return None
        return self._safe_call(
            self._pro.index_daily,
            ts_code=ts_code,
            start_date=start_date,
            end_date=end_date,
        )

    def get_daily_basic(self, ts_code: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        if not self._check_pro():
            return None
        return self._safe_call(
            self._pro.daily_basic,
            ts_code=ts_code,
            start_date=start_date,
            end_date=end_date,
        )

    def get_realtime_quote(self, ts_codes: list[str]) -> Optional[pd.DataFrame]:
        if not self._check_pro():
            return None
        return self._safe_call(ts.realtime_quote, ts_code=",".join(ts_codes))

    def check_connection(self) -> bool:
        df = self.get_daily("000001.SZ", "20240101", "20240110")
        return df is not None and not df.empty
```

- [ ] **Step 2: 重写 `modules/tushare_client.py` 委托给 TushareProvider**

```python
"""向后兼容的 TushareClient 包装器"""
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

    def get_daily(self, ts_code: str, start_date: str = "", end_date: str = "") -> Optional[pd.DataFrame]:
        return self._provider.get_daily(ts_code, start_date, end_date)

    def get_index_daily(self, ts_code: str, start_date: str = "", end_date: str = "") -> Optional[pd.DataFrame]:
        return self._provider.get_index_daily(ts_code, start_date, end_date)

    def get_realtime_quote(self, ts_code: str) -> Optional[pd.DataFrame]:
        return self._provider.get_realtime_quote([ts_code])

    def get_moneyflow(self, ts_code: str, start_date: str = "", end_date: str = "") -> Optional[pd.DataFrame]:
        return self._provider.get_moneyflow(ts_code, start_date, end_date)

    def get_stock_basic(self) -> Optional[pd.DataFrame]:
        return self._provider.get_stock_basic()

    def get_financial_data(self, ts_code: str) -> Optional[pd.DataFrame]:
        return self._provider.get_financial_data(ts_code)

    def get_trade_cal(self) -> Optional[pd.DataFrame]:
        return self._provider.get_trade_cal()

    def check_connection(self) -> bool:
        return self._provider.check_connection()
```

- [ ] **Step 3: Write test for TushareProvider**

```python
# tests/test_providers/test_tushare_provider.py
"""TushareProvider 测试（mock 环境，不依赖真实 API）"""
import os
import pytest
from modules.providers.tushare_provider import TushareProvider


def test_provider_name():
    p = TushareProvider(token="test_token_12345678901234567890123456789012345678901234567890123456")
    assert p.name == "tushare"


def test_provider_no_token():
    """没有 token 时 check_connection 返回 False"""
    os.environ.pop("TUSHARE_TOKEN", None)
    # 强制未配置模式
    p = TushareProvider(token="")
    assert p.check_connection() == False
```

- [ ] **Step 4: Run tests and commit**

```bash
python -m pytest tests/test_providers/ -v
git add modules/providers/tushare_provider.py modules/tushare_client.py
git commit -m "refactor: extract TushareProvider, TushareClient delegates to it"
```

---

### Task 3: MootdxProvider

**Files:**
- Create: `modules/providers/mootdx_provider.py`
- Test: `tests/test_providers/test_mootdx_provider.py`

- [ ] **Step 1: Write `modules/providers/mootdx_provider.py`**

```python
import logging
from typing import Optional

import pandas as pd

from modules.providers.base import DataSourceProvider
from modules.providers.code_utils import tushare_to_mootdx, mootdx_to_tushare

logger = logging.getLogger(__name__)


class MootdxProvider(DataSourceProvider):
    """Mootdx 数据源实现（免费，无需 API Key）"""

    def __init__(self):
        self._client = None

    @property
    def name(self) -> str:
        return "mootdx"

    def _get_client(self):
        if self._client is None:
            from mootdx.quotes import Quotes
            self._client = Quotes.factory(market="std")
        return self._client

    def get_daily(self, ts_code: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        try:
            client = self._get_client()
            mdx_code = tushare_to_mootdx(ts_code)
            market, code = mdx_code.split(".")
            market = int(market)

            bars = client.bars(
                symbol=code,
                frequency=9,  # 日线
                offset=0,
                start=int(start_date[:4]),
                market=market,
            )
            if bars is None or len(bars) == 0:
                return None

            df = bars.copy()
            df = df.rename(columns={
                "volume": "vol",
                "code": "ts_code",
                "date": "trade_date",
            })
            df["ts_code"] = ts_code
            df["trade_date"] = pd.to_datetime(df["trade_date"]).dt.strftime("%Y%m%d")

            # 过滤日期范围
            df = df[(df["trade_date"] >= start_date) & (df["trade_date"] <= end_date)]

            # 计算涨跌幅
            df["pct_chg"] = df["close"].pct_change() * 100
            df["pct_chg"] = df["pct_chg"].fillna(0)

            return df[["ts_code", "trade_date", "open", "high", "low", "close", "vol", "amount", "pct_chg"]]
        except Exception as e:
            logger.error(f"MootdxProvider get_daily error for {ts_code}: {e}")
            return None

    def get_stock_basic(self) -> Optional[pd.DataFrame]:
        try:
            from mootdx.quotes import Quotes
            client = Quotes.factory(market="std")
            # mootdx 不直接提供 stock_basic，转为使用 baostock 或返回空
            logger.warning("MootdxProvider does not support get_stock_basic")
            return None
        except Exception as e:
            logger.error(f"MootdxProvider get_stock_basic error: {e}")
            return None

    def get_moneyflow(self, ts_code: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        try:
            from mootdx.quotes import Quotes
            client = Quotes.factory(market="std")
            mdx_code = tushare_to_mootdx(ts_code)
            market, code = mdx_code.split(".")
            market = int(market)

            mf = client.moneyflow(market=market, symbol=code)
            if mf is None or len(mf) == 0:
                return None

            df = mf.copy()
            df["ts_code"] = ts_code
            return df
        except Exception as e:
            logger.error(f"MootdxProvider get_moneyflow error for {ts_code}: {e}")
            return None

    def get_financial_data(self, ts_code: str) -> Optional[pd.DataFrame]:
        logger.warning("MootdxProvider does not support get_financial_data")
        return None

    def get_trade_cal(self) -> Optional[pd.DataFrame]:
        logger.warning("MootdxProvider does not support get_trade_cal")
        return None

    def get_index_daily(self, ts_code: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        logger.warning("MootdxProvider does not support get_index_daily")
        return None

    def get_daily_basic(self, ts_code: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        logger.warning("MootdxProvider does not support get_daily_basic")
        return None

    def get_realtime_quote(self, ts_codes: list[str]) -> Optional[pd.DataFrame]:
        try:
            from mootdx.quotes import Quotes
            client = Quotes.factory(market="std")
            results = []
            for ts_code in ts_codes:
                mdx_code = tushare_to_mootdx(ts_code)
                market, code = mdx_code.split(".")
                market = int(market)
                quote = client.quote(market=market, symbol=code)
                if quote is not None and len(quote) > 0:
                    quote["ts_code"] = ts_code
                    results.append(quote)
            if results:
                return pd.concat(results, ignore_index=True)
            return None
        except Exception as e:
            logger.error(f"MootdxProvider get_realtime_quote error: {e}")
            return None

    def check_connection(self) -> bool:
        try:
            df = self.get_daily("000001.SZ", "20250101", "20250110")
            return df is not None and not df.empty
        except Exception:
            return False
```

- [ ] **Step 2: Write test for MootdxProvider**

```python
# tests/test_providers/test_mootdx_provider.py
import pytest
from modules.providers.mootdx_provider import MootdxProvider


def test_provider_name():
    p = MootdxProvider()
    assert p.name == "mootdx"


def test_check_connection_no_data():
    """无网络环境也能正常返回 False 而非抛异常"""
    p = MootdxProvider()
    result = p.check_connection()
    assert result in (True, False)
```

- [ ] **Step 3: Run tests and commit**

```bash
python -m pytest tests/test_providers/ -v
git add modules/providers/mootdx_provider.py tests/test_providers/test_mootdx_provider.py
git commit -m "feat: add MootdxProvider"
```

---

### Task 4: BaostockProvider

**Files:**
- Create: `modules/providers/baostock_provider.py`
- Test: `tests/test_providers/test_baostock_provider.py`

- [ ] **Step 1: Write `modules/providers/baostock_provider.py`**

```python
import logging
import threading
from typing import Optional

import pandas as pd

from modules.providers.base import DataSourceProvider
from modules.providers.code_utils import tushare_to_baostock

logger = logging.getLogger(__name__)


class BaostockProvider(DataSourceProvider):
    """Baostock 数据源实现（免费，需 login/logout，懒初始化）"""

    def __init__(self):
        self._logged_in = False
        self._lock = threading.Lock()

    @property
    def name(self) -> str:
        return "baostock"

    def _ensure_login(self):
        if not self._logged_in:
            with self._lock:
                if not self._logged_in:
                    import baostock as bs
                    lg = bs.login()
                    if lg.error_code != "0":
                        logger.error(f"Baostock login failed: {lg.error_msg}")
                        return False
                    self._logged_in = True
        return True

    def _ensure_logout(self):
        if self._logged_in:
            with self._lock:
                if self._logged_in:
                    import baostock as bs
                    bs.logout()
                    self._logged_in = False

    def _safe_query(self, query_func, *args, **kwargs):
        if not self._ensure_login():
            return None
        try:
            rs = query_func(*args, **kwargs)
            if rs.error_code != "0":
                logger.error(f"Baostock query error: {rs.error_msg}")
                return None
            return rs
        except Exception as e:
            logger.error(f"Baostock query exception: {e}")
            return None

    def get_daily(self, ts_code: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        import baostock as bs
        bs_code = tushare_to_baostock(ts_code)
        start = f"{start_date[:4]}-{start_date[4:6]}-{start_date[6:]}"
        end = f"{end_date[:4]}-{end_date[4:6]}-{end_date[6:]}"

        rs = self._safe_query(
            bs.query_history_k_data_plus,
            bs_code,
            "date,open,high,low,close,volume,amount,pctChg",
            start_date=start,
            end_date=end,
            frequency="d",
            adjustflag="2",  # 前复权
        )
        if rs is None:
            return None

        rows = []
        while rs.next():
            rows.append(rs.get_row_data())

        if not rows:
            return None

        df = pd.DataFrame(rows, columns=["trade_date", "open", "high", "low", "close", "vol", "amount", "pct_chg"])
        df["ts_code"] = ts_code
        for col in ["open", "high", "low", "close", "vol", "amount", "pct_chg"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        df["trade_date"] = df["trade_date"].str.replace("-", "")
        return df[["ts_code", "trade_date", "open", "high", "low", "close", "vol", "amount", "pct_chg"]]

    def get_stock_basic(self) -> Optional[pd.DataFrame]:
        import baostock as bs

        # 先查所有股票
        rs = self._safe_query(bs.query_all_stock, day="2026-01-01")
        if rs is None:
            return None

        rows = []
        while rs.next():
            rows.append(rs.get_row_data())

        if not rows:
            return None

        df = pd.DataFrame(rows, columns=["code", "trade_date", "code_name", "status", "type"])
        df = df[df["type"] == "1"]  # 只保留股票
        df["ts_code"] = df["code"].apply(
            lambda x: x.replace("sz.", "").replace("sh.", "") + "." + x[:2].upper()
        )
        df["name"] = df["code_name"]

        # 补充行业分类
        industry_map = {}
        industry_rs = self._safe_query(bs.query_stock_industry)
        if industry_rs:
            while industry_rs.next():
                row = industry_rs.get_row_data()
                code = row[0]
                industry_name = row[-1]
                industry_map[code] = industry_name

        df["industry"] = df["code"].map(industry_map)
        df["area"] = ""
        df["market"] = df["code"].apply(lambda x: x[:2].upper())
        df["list_date"] = df["trade_date"]

        return df[["ts_code", "name", "area", "industry", "market", "list_date"]]

    def get_moneyflow(self, ts_code: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        logger.warning("BaostockProvider does not support get_moneyflow yet")
        return None

    def get_financial_data(self, ts_code: str) -> Optional[pd.DataFrame]:
        logger.warning("BaostockProvider does not support get_financial_data yet")
        return None

    def get_trade_cal(self) -> Optional[pd.DataFrame]:
        import baostock as bs
        rs = self._safe_query(bs.query_trade_dates, start_date="1990-01-01", end_date="2026-12-31")
        if rs is None:
            return None
        rows = []
        while rs.next():
            rows.append(rs.get_row_data())
        df = pd.DataFrame(rows, columns=["trade_date", "is_open"])
        df["is_open"] = pd.to_numeric(df["is_open"], errors="coerce")
        df["trade_date"] = df["trade_date"].str.replace("-", "")
        return df

    def get_index_daily(self, ts_code: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        # 上证指数: sh.000001, 深证成指: sz.399001
        import baostock as bs
        bs_code = tushare_to_baostock(ts_code)
        start = f"{start_date[:4]}-{start_date[4:6]}-{start_date[6:]}"
        end = f"{end_date[:4]}-{end_date[4:6]}-{end_date[6:]}"

        rs = self._safe_query(
            bs.query_history_k_data_plus,
            bs_code,
            "date,open,high,low,close,volume,amount,pctChg",
            start_date=start,
            end_date=end,
            frequency="d",
            adjustflag="3",  # 不复权
        )
        if rs is None:
            return None
        rows = []
        while rs.next():
            rows.append(rs.get_row_data())
        if not rows:
            return None
        df = pd.DataFrame(rows, columns=["trade_date", "open", "high", "low", "close", "vol", "amount", "pct_chg"])
        df["ts_code"] = ts_code
        for col in ["open", "high", "low", "close", "vol", "amount", "pct_chg"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        df["trade_date"] = df["trade_date"].str.replace("-", "")
        return df[["ts_code", "trade_date", "open", "high", "low", "close", "vol", "amount", "pct_chg"]]

    def get_daily_basic(self, ts_code: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        logger.warning("BaostockProvider does not support get_daily_basic yet")
        return None

    def get_realtime_quote(self, ts_codes: list[str]) -> Optional[pd.DataFrame]:
        logger.warning("BaostockProvider does not support get_realtime_quote")
        return None

    def check_connection(self) -> bool:
        df = self.get_daily("000001.SZ", "20250101", "20250110")
        result = df is not None and not df.empty
        self._ensure_logout()
        return result
```

- [ ] **Step 2: Write test for BaostockProvider**

```python
# tests/test_providers/test_baostock_provider.py
import pytest
from modules.providers.baostock_provider import BaostockProvider


def test_provider_name():
    p = BaostockProvider()
    assert p.name == "baostock"


def test_check_connection_no_data():
    """无网络环境也能正常返回 False 而非抛异常"""
    p = BaostockProvider()
    result = p.check_connection()
    # cleanup: ensure logout
    p._ensure_logout()
    assert result in (True, False)
```

- [ ] **Step 3: Run tests and commit**

```bash
python -m pytest tests/test_providers/ -v
git add modules/providers/baostock_provider.py tests/test_providers/test_baostock_provider.py
git commit -m "feat: add BaostockProvider"
```

---

### Task 5: CompositeDataProvider

**Files:**
- Create: `modules/providers/composite.py`
- Modify: `modules/providers/__init__.py`
- Test: `tests/test_providers/test_composite.py`

- [ ] **Step 1: Write `modules/providers/composite.py`**

```python
import logging
from typing import Optional

import pandas as pd

from modules.providers.base import DataSourceProvider

logger = logging.getLogger(__name__)


class CompositeDataProvider(DataSourceProvider):
    """复合数据源提供者：按优先级依次尝试每个 provider，第一个成功就返回"""

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
```

- [ ] **Step 2: Update `modules/providers/__init__.py` with create_default_provider()**

```python
import os
import logging
from typing import Optional

from modules.providers.base import DataSourceProvider
from modules.providers.composite import CompositeDataProvider
from modules.providers.tushare_provider import TushareProvider
from modules.providers.mootdx_provider import MootdxProvider
from modules.providers.baostock_provider import BaostockProvider

logger = logging.getLogger(__name__)


def create_default_provider(token: Optional[str] = None) -> DataSourceProvider:
    """创建默认数据源提供者（自动检测配置并组装 Composite 链）"""
    data_mode = os.getenv("DATA_MODE", "websearch")
    providers = []

    # 1. 如果有 Tushare token，优先用 Tushare（JNB 模式）
    tushare_token = token or os.getenv("TUSHARE_TOKEN", "")
    if data_mode == "jnb" and tushare_token:
        providers.append(TushareProvider(token=tushare_token))
        logger.info("create_default_provider: TushareProvider added")

    # 2. mootdx 作为备选（免费，无需 Key）
    try:
        providers.append(MootdxProvider())
        logger.info("create_default_provider: MootdxProvider added")
    except Exception as e:
        logger.warning(f"create_default_provider: failed to init MootdxProvider: {e}")

    # 3. baostock 作为第二备选
    try:
        providers.append(BaostockProvider())
        logger.info("create_default_provider: BaostockProvider added")
    except Exception as e:
        logger.warning(f"create_default_provider: failed to init BaostockProvider: {e}")

    if not providers:
        logger.warning("create_default_provider: no data source providers available")
        raise RuntimeError("没有可用的数据源提供者，请安装 mootdx/baostock 或配置 Tushare token")

    return CompositeDataProvider(providers)


__all__ = [
    "DataSourceProvider",
    "CompositeDataProvider",
    "TushareProvider",
    "MootdxProvider",
    "BaostockProvider",
    "create_default_provider",
]
```

- [ ] **Step 3: Write test for CompositeDataProvider**

```python
# tests/test_providers/test_composite.py
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
```

- [ ] **Step 4: Run tests and commit**

```bash
python -m pytest tests/test_providers/ -v
git add modules/providers/composite.py modules/providers/__init__.py tests/test_providers/test_composite.py
git commit -m "feat: add CompositeDataProvider and create_default_provider factory"
```

---

### Task 6: 重构 DataSyncer 使用 Provider

**Files:**
- Modify: `modules/data_sync.py`
- Test: run existing tests to ensure no regression

- [ ] **Step 1: 修改 `modules/data_sync.py`，将 Tushare SDK 直调改为 Provider**

关键改动点：
- `__init__`：接受 `DataSourceProvider` 参数，默认调 `create_default_provider()`
- 移除 `ts.set_token()`、`ts.pro_api()`、`self.pro._DataApi__http_url` 等 Tushare 初始化代码
- 所有 `self.pro.xxx()` 改为 `self.provider.xxx()`

```python
# 文件顶部新增 import
from typing import Optional
from modules.providers import DataSourceProvider, create_default_provider

# class DataSyncer __init__ 改为:
class DataSyncer:
    def __init__(self, token: Optional[str] = None, provider: Optional[DataSourceProvider] = None):
        data_mode = os.getenv("DATA_MODE", "websearch")
        
        if provider:
            self.provider = provider
        else:
            try:
                self.provider = create_default_provider(token)
            except RuntimeError:
                if data_mode == "jnb":
                    raise ValueError(
                        "JNB 模式下需要配置 TUSHARE_TOKEN 和 TUSHARE_API_URL，"
                        "或安装 mootdx/baostock 作为备选。"
                    )
                raise
        
        # 保留 self.pro 向后兼容（某些子模块可能还在用）
        self.pro = getattr(self.provider, "_pro", None) if hasattr(self.provider, "_pro") else None
```

- [ ] **Step 2: 逐一替换 DataSyncer 中的 `self.pro.xxx()` 调用**

替换表（文件中的具体行需要逐个检查）：

| 原调用 | 替换为 |
|--------|--------|
| `self.pro.stock_basic()` | `self.provider.get_stock_basic()` |
| `self.pro.daily(ts_code=..., start_date=..., end_date=...)` | `self.provider.get_daily(ts_code, start_date, end_date)` |
| `self.pro.moneyflow(ts_code=..., start_date=..., end_date=...)` | `self.provider.get_moneyflow(ts_code, start_date, end_date)` |
| `self.pro.fina_indicator(ts_code=...)` | `self.provider.get_financial_data(ts_code)` |
| `self.pro.trade_cal(...)` | `self.provider.get_trade_cal()` |
| `self.pro.daily_basic(...)` | `self.provider.get_daily_basic(...)` |

- [ ] **Step 3: Run existing tests to verify no regression**

```bash
python -m pytest tests/test_data_sync.py tests/test_database.py tests/test_watchlist.py -v
```

Expected: all existing tests pass

```bash
git add modules/data_sync.py
git commit -m "refactor: DataSyncer uses DataSourceProvider instead of direct Tushare SDK"
```

- [ ] **Step 4: 更新 `setup_wizard.py` 的数据源连通性测试**

将 `test_jnb_connection()` 改为通用测试，测试所有已配置的 Provider：

```python
def test_data_source_connection():
    """测试当前配置的数据源是否可用"""
    from modules.providers import create_default_provider
    provider = create_default_provider()
    return provider.check_connection()
```

```bash
git add modules/setup_wizard.py
git commit -m "refactor: setup_wizard uses generic provider connection test"
```

---

### Task 7: 更新模块导出和 requirements

**Files:**
- Modify: `modules/__init__.py`
- Modify: `requirements.txt`

- [ ] **Step 1: 在 `modules/__init__.py` 中新增 Provider 导出**

```python
# 在现有 export 后追加
from modules.providers import (
    DataSourceProvider,
    CompositeDataProvider,
    TushareProvider,
    MootdxProvider,
    BaostockProvider,
    create_default_provider,
)
```

- [ ] **Step 2: 更新 `requirements.txt`**

```
mootdx>=1.0.0
baostock>=1.0.0
```

- [ ] **Step 3: 运行完整测试**

```bash
pip install mootdx baostock
python -m pytest tests/ -v
```

```bash
git add modules/__init__.py requirements.txt
git commit -m "feat: export providers from modules package, add mootdx/baostock deps"
```

---

### Task 8: 最终集成验证

- [ ] **Step 1: 运行全部测试，确认无回归**

```bash
python -m pytest tests/ -v 2>&1 | tail -30
```

预期结果：367 passed, 10 skipped（与改造前一致）

- [ ] **Step 2: 为新的 `test_providers/` 补充 pytest 配置**

在 `pyproject.toml` 或 `pytest.ini` 中确保 test_providers 被覆盖：

```bash
python -m pytest tests/test_providers/ -v
```

预期：至少 15+ passed（含 composite 9 + code_utils 5 + base 2 + provider specifics）

- [ ] **Step 3: Final commit**

```bash
git add -A
git commit -m "chore: final integration of multi-data-source provider layer"
```
