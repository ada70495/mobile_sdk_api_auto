import pytest
from common.conf_handler import read_yaml
from common.request_handler import api
import os

# 读取相册测试yaml用例文件
data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data/album_data.yaml")
album_data = read_yaml(data_path)

class TestAlbumApi:
    # 用例依赖标记：给创建文件夹打标记，后续上传依赖它
    @pytest.mark.dependency(name="create_folder")
    @pytest.mark.parametrize("case", album_data["create_folder"]["cases"], ids=lambda x:x["case_name"])
    def test_create_folder(self, case):
        """测试创建相册文件夹，业务流程第一步"""
        res = api.send(album_data["create_folder"]["method"], album_data["create_folder"]["uri"], json=case["json"])
        assert res["code"] == case["expect"]["code"]

    # 依赖上面创建文件夹的用例，保证业务流程顺序：建文件夹→上传图片
    @pytest.mark.dependency(depends=["create_folder"])
    @pytest.mark.parametrize("case", album_data["upload_image"]["cases"], ids=lambda x:x["case_name"])
    def test_upload_image(self, case):
        """测试图片上传，依赖文件夹创建完成"""
        res = api.send(album_data["upload_image"]["method"], album_data["upload_image"]["uri"], json=case["json"])
        assert res["code"] == case["expect"]["code"]

    @pytest.mark.parametrize("case", album_data["delete_image"]["cases"], ids=lambda x:x["case_name"])
    def test_delete_image(self, case):
        """测试图片删除"""
        res = api.send(album_data["delete_image"]["method"], album_data["delete_image"]["uri"], json=case["json"])
        assert res["code"] == case["expect"]["code"]