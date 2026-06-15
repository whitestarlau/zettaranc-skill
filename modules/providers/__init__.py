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
    """创建默认数据源提供者（自动检测配置并组装 Composite 链）

    优先级：Tushare（JNB 模式）→ Mootdx → Baostock
    无 Tushare token 时自动跳过，仅用免费数据源。
    """
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
        raise RuntimeError(
            "没有可用的数据源提供者。请安装 mootdx/baostock（pip install mootdx baostock，或 uv pip install mootdx baostock）"
            "或配置 Tushare token。"
        )

    return CompositeDataProvider(providers)


__all__ = [
    "DataSourceProvider",
    "CompositeDataProvider",
    "TushareProvider",
    "MootdxProvider",
    "BaostockProvider",
    "create_default_provider",
]
