# 多数据源 Provider 抽象层设计

## 概述

为 zettaranc-skill 引入 DataSourceProvider 抽象层，将当前硬编码的 Tushare 数据源调用抽取为统一接口，
新增 mootdx 和 baostock 作为备选/互补数据源，通过 CompositeDataProvider 实现自动回退链。

## 背景

当前架构：`DataSyncer` 和 `TushareClient` 各自独立初始化 Tushare SDK，没有数据源抽象层。
`DATA_MODE=jnb` 依赖 Tushare API Key（需要代理中转），`DATA_MODE=websearch` 则没有数据源。

mootdx 和 baostock 是免费、无需 API Key 的 A 股数据源，可作为 Tushare 的补充或备选。

## 架构

```
DataSourceProvider (ABC)
├── TushareProvider      — 从现有 TushareClient 抽取
├── MootdxProvider       — 新增，免费，无需认证
├── BaostockProvider     — 新增，需 bs.login/bs.logout
└── CompositeDataProvider — 按优先级链式回退
```

代码路径：`modules/providers/`（新增子包）

## Provider 接口

```python
class DataSourceProvider(ABC):
    def get_daily(self, ts_code, start_date, end_date) -> pd.DataFrame | None
    def get_stock_basic(self) -> pd.DataFrame | None
    def get_moneyflow(self, ts_code, start_date, end_date) -> pd.DataFrame | None
    def get_financial_data(self, ts_code) -> pd.DataFrame | None
    def get_trade_cal(self) -> pd.DataFrame | None
    def get_index_daily(self, ts_code, start_date, end_date) -> pd.DataFrame | None
    def get_daily_basic(self, ts_code, start_date, end_date) -> pd.DataFrame | None
    def get_realtime_quote(self, ts_codes) -> pd.DataFrame | None
    def check_connection(self) -> bool
    @property
    def name(self) -> str
```

所有方法返回统一列名格式（Tushare 兼容），None 或空 DataFrame 表示"该源无数据"。

## CompositeDataProvider

```python
class CompositeDataProvider(DataSourceProvider):
    def __init__(self, providers: list[DataSourceProvider]):
        self._providers = providers  # 按优先级排列

    # 每个方法：依次尝试 providers，第一个返回有效数据的就停止
```

默认优先级链：
- JNB 模式（有 Tushare token）：`[TushareProvider, MootdxProvider, BaostockProvider]`
- 无 Tushare token：`[MootdxProvider, BaostockProvider]`

## ts_code 格式转换

| 数据源 | 格式 | 示例 |
|--------|------|------|
| Tushare | XXXXXX.SZ/SH | 000001.SZ |
| mootdx | 市场代码(1/0) + XXXXXX | 1.000001 |
| baostock | sz/sh.XXXXXX | sz.000001 |

`code_utils.py` 提供双向转换，每个 Provider 内部自行处理，对上层透明。

## DataSyncer 改动

- `DataSyncer.__init__()` 不再直接初始化 Tushare SDK
- 接收 `DataSourceProvider` 参数，默认调用 `create_default_provider()`
- 所有 `self.pro.xxx()` 改为 `self.provider.xxx()`
- 移除 `self.pro` 和 `self.token` 的直接 Tushare 依赖

## TushareClient 向后兼容

`TushareClient` 保留，内部委托给 `TushareProvider`，现有引用不受影响。

## 文件变更清单

### 新增文件
| 文件 | 说明 |
|------|------|
| `modules/providers/__init__.py` | 导出 + `create_default_provider()` |
| `modules/providers/base.py` | `DataSourceProvider` ABC |
| `modules/providers/code_utils.py` | ts_code 格式转换 |
| `modules/providers/tushare_provider.py` | Tushare 实现 |
| `modules/providers/mootdx_provider.py` | mootdx 实现 |
| `modules/providers/baostock_provider.py` | baostock 实现 |
| `modules/providers/composite.py` | CompositeDataProvider |

### 修改文件
| 文件 | 改动 |
|------|------|
| `modules/data_sync.py` | DataSyncer 改调 provider |
| `modules/tushare_client.py` | 内部委托给 TushareProvider |
| `modules/__init__.py` | 新增 export |
| `modules/setup_wizard.py` | test_jnb_connection → test_data_source |
| `requirements.txt` | 追加 motoox, baostock |

### 新增测试
| 文件 | 说明 |
|------|------|
| `tests/test_providers/test_base.py` | ABC 接口验证 |
| `tests/test_providers/test_composite.py` | Composite 回退逻辑 |
| `tests/test_providers/test_code_utils.py` | 代码转换 |

## 约束

1. 不改 indicator 层和 strategy 层——它们只从 SQLite 读数据
2. baostock 懒初始化，不拖慢 import
3. 向后兼容：现有 API 不破坏
4. 无需 API Key 也能用
