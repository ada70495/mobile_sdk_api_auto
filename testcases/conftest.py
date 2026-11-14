"""全局 fixture：请求客户端、登录、测试数据准备"""
import os
import sys

import pytest

# 保证从任意目录运行都能 import 项目内的包
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from api.album_api import AlbumApi
from common.conf_handler import config
from common.logger_handler import logger
from common.request_handler import RequestHandler


@pytest.fixture(scope="session")
def client() -> RequestHandler:
    """全 session 共用一个 Session 和一个 token"""
    c = RequestHandler()
    logger.info(f"测试环境：{config.summary()}")
    yield c
    c.close()


@pytest.fixture(scope="session", autouse=True)
def prepared_env(client):
    """环境自愈：复位 Mock 数据 → 登录 → 预置基础数据

    预置内容：
        相册 1001「自动化测试相册」
        图片 2001「seed.jpg」
    这样上传/删除用例不依赖执行顺序，单独运行也能通过。
    """
    logger.info("=== 测试环境准备开始 ===")

    resp = client.post("/__admin/reset")
    assert resp.json()["code"] == 200, "Mock 服务复位失败，请确认 mock_server 已启动且地址正确"

    login_data = client.login()
    assert login_data.get("token") or login_data.get("data", {}).get("token"), f"登录失败：{login_data}"

    r1 = AlbumApi(client).create_folder("自动化测试相册")
    assert r1.json()["code"] == 200, f"预置相册失败：{r1.json()}"
    folder_id = r1.json()["data"]["folder_id"]

    r2 = AlbumApi(client).upload(folder_id, "seed.jpg")
    assert r2.json()["code"] == 200, f"预置图片失败：{r2.json()}"
    img_id = r2.json()["data"]["img_id"]

    logger.info(f"预置数据完成：folder_id={folder_id} img_id={img_id}")
    yield
    logger.info("=== 测试环境准备结束 ===")
