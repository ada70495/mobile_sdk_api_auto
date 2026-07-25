import pytest
from common.conf_handler import read_yaml
from common.request_handler import api
import os

data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data/browser_data.yaml")
browser_data = read_yaml(data_path)

class TestBrowserApi:
    @pytest.mark.parametrize("case", browser_data["browser_collect"]["cases"], ids=lambda x:x["case_name"])
    def test_add_collect(self, case):
        """浏览器收藏新增接口测试"""
        res = api.send(browser_data["browser_collect"]["method"], browser_data["browser_collect"]["uri"], json=case["json"])
        assert res["code"] == case["expect"]["code"]

    @pytest.mark.parametrize("case", browser_data["browser_cache"]["cases"], ids=lambda x:x["case_name"])
    def test_clear_cache(self, case):
        """浏览器缓存清理接口测试"""
        res = api.send(browser_data["browser_cache"]["method"], browser_data["browser_cache"]["uri"], json=case["json"])
        assert res["code"] == case["expect"]["code"]