import pytest
from common.conf_handler import read_yaml
from common.request_handler import api
import os

data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data/camera_data.yaml")
camera_data = read_yaml(data_path)

class TestCameraApi:
    @pytest.mark.parametrize("case", camera_data["camera_param_set"]["cases"], ids=lambda x:x["case_name"])
    def test_set_camera_param(self, case):
        """相机分辨率、帧率参数配置接口测试"""
        res = api.send(camera_data["camera_param_set"]["method"], camera_data["camera_param_set"]["uri"], json=case["json"])
        assert res["code"] == case["expect"]["code"]

    @pytest.mark.parametrize("case", camera_data["watermark_config"]["cases"], ids=lambda x:x["case_name"])
    def test_set_watermark(self, case):
        """相机水印开关配置测试"""
        res = api.send(camera_data["watermark_config"]["method"], camera_data["watermark_config"]["uri"], json=case["json"])
        assert res["code"] == case["expect"]["code"]