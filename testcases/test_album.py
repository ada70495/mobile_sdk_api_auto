"""相册模块：文件夹创建 / 图片上传 / 图片删除"""
import os

import allure
import pytest
import yaml

from api.album_api import AlbumApi
from common.assert_handler import AssertHandler

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

with open(os.path.join(DATA_DIR, "album_data.yaml"), "r", encoding="utf-8") as _f:
    ALBUM_DATA = yaml.safe_load(_f)


@allure.feature("相册模块")
class TestAlbumApi:

    @allure.story("创建相册文件夹")
    @pytest.mark.parametrize(
        "case", ALBUM_DATA["create_folder"]["cases"], ids=lambda c: c["case_name"]
    )
    def test_create_folder(self, client, case):
        """相册文件夹创建：正常创建 + 空名称 + 名称超长"""
        resp = AlbumApi(client).create_folder(**case["json"])
        body = resp.json()

        a = AssertHandler()
        a.eq(body["code"], case["expect"]["code"], "业务码")
        if body["code"] == 200:
            a.eq(body["data"]["name"], case["json"]["name"], "相册名称一致")
            a.not_none(body["data"]["folder_id"], "返回 folder_id")
        else:
            a.contains(body["msg"], case["expect"]["msg"], "错误提示")
        a.finish()

    @allure.story("上传图片")
    @pytest.mark.parametrize(
        "case", ALBUM_DATA["upload_image"]["cases"], ids=lambda c: c["case_name"]
    )
    def test_upload_image(self, client, case):
        """图片上传：正常上传 + 越权访问他人相册"""
        resp = AlbumApi(client).upload(**case["json"])
        body = resp.json()

        a = AssertHandler()
        a.eq(body["code"], case["expect"]["code"], "业务码")
        if body["code"] == 200:
            a.eq(body["data"]["folder_id"], case["json"]["folder_id"], "归属相册正确")
            a.not_none(body["data"]["img_id"], "返回 img_id")
        else:
            a.contains(body["msg"], case["expect"]["msg"], "错误提示")
        a.finish()

    @allure.story("删除图片")
    def test_delete_image(self, client):
        """先上传再删除：验证删除成功 + 重复删除的幂等性（可重复执行）"""
        album = AlbumApi(client)

        created = album.upload(1001, "to_delete.jpg").json()
        img_id = created["data"]["img_id"]

        resp = album.delete(img_id)
        body = resp.json()
        a = AssertHandler()
        a.eq(body["code"], 200, "删除成功")
        a.eq(body["data"]["img_id"], img_id, "返回被删除的图片ID")
        a.finish()

        again = album.delete(img_id).json()
        a2 = AssertHandler()
        a2.eq(again["code"], 400, "重复删除返回400")
        a2.contains(again["msg"], "不存在", "错误提示")
        a2.finish()
