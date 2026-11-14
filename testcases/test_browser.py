"""浏览器模块：网页收藏、缓存清理"""
import os

import allure
import pytest
import yaml

from api.browser_api import BrowserApi
from common.assert_handler import AssertHandler

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

with open(os.path.join(DATA_DIR, "browser_data.yaml"), "r", encoding="utf-8") as _f:
    BROWSER_DATA = yaml.safe_load(_f)


@allure.feature("浏览器模块")
class TestBrowserApi:

    @allure.story("网页收藏")
    @pytest.mark.parametrize(
        "case", BROWSER_DATA["browser_collect"]["cases"], ids=lambda c: c["case_name"]
    )
    def test_add_collect(self, client, case):
        """网页收藏：正常收藏 + URL 为空 + URL 缺少协议头"""
        resp = BrowserApi(client).collect(**case["json"])
        body = resp.json()

        a = AssertHandler()
        a.eq(body["code"], case["expect"]["code"], "业务码")
        if body["code"] == 200:
            a.eq(body["data"]["url"], case["json"]["url"], "收藏链接一致")
            a.not_none(body["data"]["collect_id"], "返回 collect_id")
        else:
            a.contains(body["msg"], case["expect"]["msg"], "错误提示")
        a.finish()

    @allure.story("缓存清理")
    @pytest.mark.parametrize(
        "case", BROWSER_DATA["browser_cache"]["cases"], ids=lambda c: c["case_name"]
    )
    def test_clear_cache(self, client, case):
        """缓存清理：全部/图片 + 非法缓存类型"""
        resp = BrowserApi(client).clear_cache(**case["json"])
        body = resp.json()

        a = AssertHandler()
        a.eq(body["code"], case["expect"]["code"], "业务码")
        if body["code"] == 200:
            a.eq(body["data"]["cleared"], case["json"]["cache_type"], "清理类型回显一致")
        else:
            a.contains(body["msg"], case["expect"]["msg"], "错误提示")
        a.finish()
