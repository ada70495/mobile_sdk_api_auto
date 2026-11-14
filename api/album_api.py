"""相册模块接口：文件夹创建 / 图片上传 / 图片删除"""


class AlbumApi:
    def __init__(self, client):
        self.client = client

    def create_folder(self, name: str, sort: int = 1):
        return self.client.post("/album/folder/create", json={"name": name, "sort": sort})

    def upload(self, folder_id: int, img_name: str):
        return self.client.post("/album/upload", json={"folder_id": folder_id, "img_name": img_name})

    def delete(self, img_id: int):
        return self.client.delete("/album/delete", json={"img_id": img_id})
