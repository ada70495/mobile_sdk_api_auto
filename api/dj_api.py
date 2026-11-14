"""DJ 音乐播放器模块接口：歌单 / 播放 / 音量 / 均衡器 / 播放模式"""


class DjApi:
    def __init__(self, client):
        self.client = client

    def playlist(self):
        return self.client.get("/dj/playlist")

    def play(self, song_id: int):
        return self.client.post("/dj/play", json={"song_id": song_id})

    def set_volume(self, volume: int):
        return self.client.post("/dj/volume", json={"volume": volume})

    def set_eq(self, mode: str):
        return self.client.post("/dj/eq", json={"mode": mode})

    def set_play_mode(self, mode: str):
        return self.client.post("/dj/play_mode", json={"mode": mode})
