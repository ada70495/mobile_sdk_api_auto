"""相册模块接口：文件夹创建/列表/重命名/删除，图片上传/列表/删除"""


class AlbumApi:
    def __init__(self, client):
        self.client = client

    # ---- 文件夹 ----
    def create_folder(self, name: str, sort: int = 0):
        return self.client.post("/album/folder/create", json={"name": name, "sort": sort})

    def list_folders(self):
        return self.client.get("/album/folder/list")

    def rename_folder(self, folder_id: int, name: str):
        return self.client.post("/album/folder/rename", json={"folder_id": folder_id, "name": name})

    def delete_folder(self, folder_id: int):
        return self.client.delete("/album/folder/delete", json={"folder_id": folder_id})

    # ---- 图片 ----
    def upload(self, folder_id: int, img_name: str, size_kb: int = 1024):
        return self.client.post(
            "/album/upload",
            json={"folder_id": folder_id, "img_name": img_name, "size_kb": size_kb},
        )

    def list_images(self, folder_id: int):
        return self.client.get("/album/image/list", params={"folder_id": folder_id})

    def delete(self, img_id: int):
        return self.client.delete("/album/delete", json={"img_id": img_id})
