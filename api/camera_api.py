"""相机模块接口：分辨率/帧率配置 / 水印开关"""


class CameraApi:
    def __init__(self, client):
        self.client = client

    def set_param(self, resolution: str, fps: int):
        return self.client.post("/camera/param/set", json={"resolution": resolution, "fps": fps})

    def set_watermark(self, open_flag: bool, position: str = "bottom"):
        return self.client.post("/camera/watermark", json={"open": open_flag, "position": position})
