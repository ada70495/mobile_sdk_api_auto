"""浏览器模块接口：网页收藏 / 缓存清理"""


class BrowserApi:
    def __init__(self, client):
        self.client = client

    def collect(self, url: str, title: str):
        return self.client.post("/browser/collect", json={"url": url, "title": title})

    def clear_cache(self, cache_type: str = "all"):
        return self.client.post("/browser/cache/clear", json={"cache_type": cache_type})
