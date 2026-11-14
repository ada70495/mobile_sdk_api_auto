"""相册模块：文件夹创建/列表/重命名/删除，图片上传/列表/删除"""
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
        """名称空、只有空格、超长、重名、排序越界"""
        resp = AlbumApi(client).create_folder(**case["json"])
        body = resp.json()

        a = AssertHandler()
        a.eq(body["code"], case["expect"]["code"], "业务码")
        if body["code"] == 200:
            a.eq(body["data"]["name"], case["json"]["name"], "相册名称一致")
            a.not_none(body["data"]["folder_id"], "返回 folder_id")
            a.eq(body["data"]["sort"], case["json"].get("sort", 0), "排序值一致")
        else:
            a.contains(body["msg"], case["expect"]["msg"], "错误提示")
        a.finish()

    @allure.story("查询相册列表")
    def test_list_folders(self, client):
        album = AlbumApi(client)
        album.create_folder("列表校验相册", sort=5)

        resp = album.list_folders()
        body = resp.json()

        a = AssertHandler()
        a.eq(body["code"], 200, "业务码")
        a.eq(body["data"]["total"], len(body["data"]["list"]), "total 与列表长度一致")
        a.gt(body["data"]["total"], 0, "相册总数")
        names = [f["name"] for f in body["data"]["list"]]
        a.contains(names, "列表校验相册", "新建相册出现在列表中")
        for f in body["data"]["list"]:
            a.not_none(f.get("image_count"), "列表项包含图片数量")
        a.finish()

    @allure.story("重命名相册")
    def test_rename_folder(self, client):
        album = AlbumApi(client)
        created = album.create_folder("待重命名相册").json()
        folder_id = created["data"]["folder_id"]

        resp = album.rename_folder(folder_id, "已重命名相册")
        body = resp.json()

        a = AssertHandler()
        a.eq(body["code"], 200, "业务码")
        a.eq(body["data"]["name"], "已重命名相册", "返回新名称")

        names = [f["name"] for f in album.list_folders().json()["data"]["list"]]
        a.contains(names, "已重命名相册", "列表中已是新名称")
        a.eq("待重命名相册" in names, False, "列表中不应再有旧名称")
        a.finish()

    @allure.story("重命名不存在的相册")
    def test_rename_folder_not_exist(self, client):
        resp = AlbumApi(client).rename_folder(999999, "任意名称")
        body = resp.json()

        a = AssertHandler()
        a.eq(body["code"], 404, "业务码")
        a.contains(body["msg"], "不存在", "错误提示")
        a.finish()

    @allure.story("重命名为已存在的名称")
    def test_rename_folder_duplicate(self, client):
        album = AlbumApi(client)
        created = album.create_folder("重名测试相册").json()
        folder_id = created["data"]["folder_id"]

        resp = album.rename_folder(folder_id, "自动化测试相册")
        body = resp.json()

        a = AssertHandler()
        a.eq(body["code"], 409, "业务码")
        a.contains(body["msg"], "已存在", "错误提示")
        a.finish()

    @allure.story("删除空相册")
    def test_delete_empty_folder(self, client):
        album = AlbumApi(client)
        created = album.create_folder("待删除空相册").json()
        folder_id = created["data"]["folder_id"]

        resp = album.delete_folder(folder_id)
        body = resp.json()

        a = AssertHandler()
        a.eq(body["code"], 200, "删除成功")
        a.eq(body["data"]["folder_id"], folder_id, "返回被删除的相册ID")

        names = [f["name"] for f in album.list_folders().json()["data"]["list"]]
        a.eq("待删除空相册" in names, False, "删除后列表中不应再有该相册")
        a.finish()

    @allure.story("删除仍有图片的相册")
    def test_delete_folder_with_images(self, client):
        # 预置数据：相册 1001 下有一张图片 2001
        resp = AlbumApi(client).delete_folder(1001)
        body = resp.json()

        a = AssertHandler()
        a.eq(body["code"], 409, "业务码")
        a.contains(body["msg"], "仍有图片", "错误提示")
        a.finish()

    @allure.story("上传图片")
    @pytest.mark.parametrize(
        "case", ALBUM_DATA["upload_image"]["cases"], ids=lambda c: c["case_name"]
    )
    def test_upload_image(self, client, case):
        """格式白名单、大小上限、越权访问"""
        resp = AlbumApi(client).upload(**case["json"])
        body = resp.json()

        a = AssertHandler()
        a.eq(body["code"], case["expect"]["code"], "业务码")
        if body["code"] == 200:
            a.eq(body["data"]["folder_id"], case["json"]["folder_id"], "归属相册正确")
            a.not_none(body["data"]["img_id"], "返回 img_id")
            a.eq(body["data"]["img_name"], case["json"]["img_name"], "图片名称一致")
        else:
            a.contains(body["msg"], case["expect"]["msg"], "错误提示")
        a.finish()

    @allure.story("查询相册内图片")
    def test_list_images(self, client):
        album = AlbumApi(client)
        album.upload(1001, "list_check.png", size_kb=512)

        resp = album.list_images(1001)
        body = resp.json()

        a = AssertHandler()
        a.eq(body["code"], 200, "业务码")
        a.eq(body["data"]["total"], len(body["data"]["list"]), "total 与列表长度一致")
        a.gt(body["data"]["total"], 0, "图片总数")
        names = [i["img_name"] for i in body["data"]["list"]]
        a.contains(names, "list_check.png", "刚上传的图片在列表中")
        a.finish()

    @allure.story("查询不存在相册的图片")
    def test_list_images_folder_not_exist(self, client):
        resp = AlbumApi(client).list_images(999999)
        body = resp.json()

        a = AssertHandler()
        a.eq(body["code"], 403, "业务码")
        a.contains(body["msg"], "无权访问", "错误提示")
        a.finish()

    @allure.story("删除图片")
    def test_delete_image(self, client):
        """先上传再删除，同时验证重复删除的幂等性"""
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
