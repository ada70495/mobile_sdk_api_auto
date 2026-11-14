"""DJ 音乐播放器模块：歌单 / 播放 / 音量 / 均衡器 / 播放模式"""
import os

import allure
import pytest
import yaml

from api.dj_api import DjApi
from common.assert_handler import AssertHandler

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


with open(os.path.join(DATA_DIR, "dj_data.yaml"), "r", encoding="utf-8") as _f:
    DJ_DATA = yaml.safe_load(_f)


def cases_of(key):
    return DJ_DATA[key]["cases"]


@allure.feature("DJ音乐播放器")
class TestDjApi:

    @allure.story("歌单查询")
    @pytest.mark.parametrize("case", cases_of("dj_playlist"), ids=lambda c: c["case_name"])
    def test_playlist(self, client, case):
        resp = DjApi(client).playlist()
        body = resp.json()
        data = body["data"]

        a = AssertHandler()
        a.eq(body["code"], case["expect"]["code"], "业务码")
        a.eq(data["total"], case["expect"]["total"], "歌曲总数")
        a.eq(len(data["list"]), data["total"], "列表长度与total一致")
        a.gt(len(data["list"]), 0, "歌单非空")
        a.finish()

    @allure.story("播放控制")
    @pytest.mark.parametrize("case", cases_of("dj_play"), ids=lambda c: c["case_name"])
    def test_play(self, client, case):
        resp = DjApi(client).play(case["json"]["song_id"])
        body = resp.json()

        a = AssertHandler()
        a.eq(body["code"], case["expect"]["code"], "业务码")
        if body["code"] == 200:
            a.eq(body["data"]["playing"], case["expect"]["playing"], "播放状态")
            a.eq(body["data"]["song_id"], case["json"]["song_id"], "播放的歌曲ID")
            a.gt(body["data"]["duration"], 0, "歌曲时长大于0")
        else:
            a.contains(body["msg"], case["expect"]["msg"], "错误提示")
        a.finish()

    @allure.story("音量调节")
    @pytest.mark.parametrize("case", cases_of("dj_volume"), ids=lambda c: c["case_name"])
    def test_volume(self, client, case):
        resp = DjApi(client).set_volume(case["json"]["volume"])
        body = resp.json()

        a = AssertHandler()
        a.eq(body["code"], case["expect"]["code"], "业务码")
        if body["code"] == 200:
            a.eq(body["data"]["volume"], case["json"]["volume"], "音量已生效")
        else:
            a.contains(body["msg"], case["expect"]["msg"], "错误提示")
        a.finish()

    @allure.story("均衡器")
    @pytest.mark.parametrize("case", cases_of("dj_eq"), ids=lambda c: c["case_name"])
    def test_eq(self, client, case):
        resp = DjApi(client).set_eq(case["json"]["mode"])
        body = resp.json()

        a = AssertHandler()
        a.eq(body["code"], case["expect"]["code"], "业务码")
        if body["code"] == 200:
            a.eq(body["data"]["mode"], case["json"]["mode"], "均衡器模式已生效")
        else:
            a.contains(body["msg"], case["expect"]["msg"], "错误提示")
        a.finish()

    @allure.story("播放模式")
    @pytest.mark.parametrize("case", cases_of("dj_play_mode"), ids=lambda c: c["case_name"])
    def test_play_mode(self, client, case):
        resp = DjApi(client).set_play_mode(case["json"]["mode"])
        body = resp.json()

        a = AssertHandler()
        a.eq(body["code"], case["expect"]["code"], "业务码")
        if body["code"] == 200:
            a.eq(body["data"]["mode"], case["json"]["mode"], "播放模式已生效")
        else:
            a.contains(body["msg"], case["expect"]["msg"], "错误提示")
        a.finish()
