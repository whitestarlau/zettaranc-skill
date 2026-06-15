"""TushareProvider 测试（mock 环境，不依赖真实 API）"""
import os
import pytest
from modules.providers.tushare_provider import TushareProvider


def test_provider_name():
    p = TushareProvider(token="test_token_12345678901234567890123456789012345678901234567890123456")
    assert p.name == "tushare"


def test_provider_no_token():
    """没有有效的 DATA_MODE/token 时 check_connection 返回 False"""
    p = TushareProvider(token="")
    assert p.check_connection() == False
