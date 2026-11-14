"""相机模块：分辨率/帧率配置、水印开关"""
import os

import allure
import pytest
import yaml

from api.camera_api import CameraApi
from common.assert_handler import AssertHandler

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

with open(os.path.join(DATA_DIR, "camera_data.yaml"), "r", encoding="utf-8") as _f:
    CAMERA_DATA = yaml.safe_load(_f)


@allure.feature("相机模块")
class TestCameraApi:

    @allure.story("拍摄参数设置")
    @pytest.mark.parametrize(
        "case", CAMERA_DATA["camera_param_set"]["cases"], ids=lambda c: c["case_name"]
    )
    def test_set_camera_param(self, client, case):
        """分辨率/帧率配置：正常设置 + 非法分辨率 + 帧率越界"""
        resp = CameraApi(client).set_param(**case["json"])
        body = resp.json()

        a = AssertHandler()
        a.eq(body["code"], case["expect"]["code"], "业务码")
        if body["code"] == 200:
            a.eq(body["data"]["resolution"], case["json"]["resolution"], "分辨率已生效")
            a.eq(body["data"]["fps"], case["json"]["fps"], "帧率已生效")
        else:
            a.contains(body["msg"], case["expect"]["msg"], "错误提示")
        a.finish()

    @allure.story("水印配置")
    @pytest.mark.parametrize(
        "case", CAMERA_DATA["watermark_config"]["cases"], ids=lambda c: c["case_name"]
    )
    def test_set_watermark(self, client, case):
        """水印开关：开启底部水印 + 关闭 + 位置非法"""
        resp = CameraApi(client).set_watermark(
            case["json"]["open"], case["json"].get("position", "bottom")
        )
        body = resp.json()

        a = AssertHandler()
        a.eq(body["code"], case["expect"]["code"], "业务码")
        if body["code"] == 200:
            a.eq(body["data"]["open"], case["json"]["open"], "开关状态已生效")
        else:
            a.contains(body["msg"], case["expect"]["msg"], "错误提示")
        a.finish()
