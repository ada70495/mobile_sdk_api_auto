"""本地被测服务：相册接口

启动：
    python mock_server/app.py
    $env:PORT=9001; python mock_server/app.py

环境变量：
    PORT         监听端口，默认 9000
    SIGN_CHECK   是否强制校验签名，默认 false
    SIGN_KEY     签名密钥，默认 mock-sign-key-2026

业务约定：HTTP 状态码统一 200，用响应体里的 code 区分结果
    200 成功 / 400 参数非法 / 401 未登录或签名错误 / 403 越权 / 404 资源不存在 / 409 重复或状态冲突
"""
import hashlib
import os

from flask import Flask, jsonify, request

app = Flask(__name__)
app.json.ensure_ascii = False

SIGN_CHECK = os.getenv("SIGN_CHECK", "false").strip().lower() in ("1", "true", "yes")
SIGN_KEY = os.getenv("SIGN_KEY", "mock-sign-key-2026")

ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".heic"}
MAX_SIZE_KB = 5120
MAX_NAME_LEN = 20


def init_state():
    return {
        "folders": {},       # 相册名 -> {folder_id, name, sort}
        "images": {},        # 图片 ID -> {img_id, folder_id, img_name, size_kb}
        "folder_seq": 1000,
        "image_seq": 2000,
    }


STATE = init_state()


def ok(data=None, msg="success"):
    return jsonify({"code": 200, "msg": msg, "data": data})


def fail(code, msg):
    return jsonify({"code": code, "msg": msg, "data": None})


def body():
    return request.get_json(silent=True) or {}


def find_folder(folder_id):
    return next((f for f in STATE["folders"].values() if f["folder_id"] == folder_id), None)


def make_sign(method, path, payload):
    """签名算法：方法 + 路径 + 按键排序的入参 + 密钥，做 MD5"""
    parts = [method.upper(), path]
    if isinstance(payload, dict):
        for key in sorted(payload):
            parts.append(f"{key}={payload[key]}")
    raw = "&".join(parts) + "&key=" + SIGN_KEY
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


@app.before_request
def check_sign():
    if not SIGN_CHECK:
        return None
    if request.path in ("/health", "/__admin/reset"):
        return None
    incoming = request.headers.get("X-Sign", "")
    payload = body() if request.method in ("POST", "PUT", "DELETE") else request.args.to_dict()
    if not incoming or incoming != make_sign(request.method, request.path, payload):
        return fail(401, "签名校验失败")
    return None


@app.get("/health")
def health():
    return jsonify({"status": "ok", "service": "mock-album-api", "sign_check": SIGN_CHECK})


@app.post("/__admin/reset")
def reset():
    global STATE
    STATE = init_state()
    return ok({"reset": True})


# ---------------- 用户 ----------------
@app.post("/user/login")
def login():
    data = body()
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    if not username:
        return fail(400, "用户名不能为空")
    if password != "123456":
        return fail(401, "用户名或密码错误")
    return ok({"token": "mock-token-testuser-2026", "user_id": 1001, "username": username})


# ---------------- 相册文件夹 ----------------
@app.post("/album/folder/create")
def album_folder_create():
    data = body()
    name = (data.get("name") or "").strip()
    if not name:
        return fail(400, "文件夹名称不能为空")
    if len(name) > MAX_NAME_LEN:
        return fail(400, f"文件夹名称超长（最多{MAX_NAME_LEN}个字符）")
    if name in STATE["folders"]:
        return fail(409, "相册名称已存在")
    sort = data.get("sort", 0)
    if not isinstance(sort, int) or isinstance(sort, bool) or not (0 <= sort <= 100):
        return fail(400, "排序值必须在 0-100 之间")
    STATE["folder_seq"] += 1
    folder_id = STATE["folder_seq"]
    STATE["folders"][name] = {"folder_id": folder_id, "name": name, "sort": sort}
    return ok({"folder_id": folder_id, "name": name, "sort": sort})


@app.get("/album/folder/list")
def album_folder_list():
    items = []
    for f in STATE["folders"].values():
        count = sum(1 for i in STATE["images"].values() if i["folder_id"] == f["folder_id"])
        items.append({**f, "image_count": count})
    items.sort(key=lambda x: (x["sort"], x["folder_id"]))
    return ok({"total": len(items), "list": items})


@app.post("/album/folder/rename")
def album_folder_rename():
    data = body()
    folder_id = data.get("folder_id")
    name = (data.get("name") or "").strip()
    target = find_folder(folder_id)
    if target is None:
        return fail(404, "相册不存在")
    if not name:
        return fail(400, "文件夹名称不能为空")
    if len(name) > MAX_NAME_LEN:
        return fail(400, f"文件夹名称超长（最多{MAX_NAME_LEN}个字符）")
    if name != target["name"] and name in STATE["folders"]:
        return fail(409, "相册名称已存在")
    STATE["folders"].pop(target["name"])
    target["name"] = name
    STATE["folders"][name] = target
    return ok({"folder_id": folder_id, "name": name})


@app.delete("/album/folder/delete")
def album_folder_delete():
    data = body()
    folder_id = data.get("folder_id")
    target = find_folder(folder_id)
    if target is None:
        return fail(404, "相册不存在")
    if any(i["folder_id"] == folder_id for i in STATE["images"].values()):
        return fail(409, "相册内仍有图片，请先清空")
    STATE["folders"].pop(target["name"])
    return ok({"folder_id": folder_id})


# ---------------- 相册内图片 ----------------
@app.post("/album/upload")
def album_upload():
    data = body()
    folder_id = data.get("folder_id")
    img_name = (data.get("img_name") or "").strip()
    if find_folder(folder_id) is None:
        return fail(403, "无权访问该相册")
    if not img_name:
        return fail(400, "图片名称不能为空")
    ext = os.path.splitext(img_name)[1].lower()
    if ext not in ALLOWED_EXT:
        return fail(400, "不支持的图片格式，仅支持 jpg/jpeg/png/heic")
    size_kb = data.get("size_kb", 1024)
    if not isinstance(size_kb, int) or isinstance(size_kb, bool):
        return fail(400, "图片大小必须为整数")
    if size_kb > MAX_SIZE_KB:
        return fail(400, f"图片大小超出限制（最大 {MAX_SIZE_KB}KB）")
    STATE["image_seq"] += 1
    img_id = STATE["image_seq"]
    STATE["images"][img_id] = {
        "img_id": img_id,
        "folder_id": folder_id,
        "img_name": img_name,
        "size_kb": size_kb,
    }
    return ok({"img_id": img_id, "folder_id": folder_id, "img_name": img_name})


@app.get("/album/image/list")
def album_image_list():
    folder_id = request.args.get("folder_id", type=int)
    if find_folder(folder_id) is None:
        return fail(403, "无权访问该相册")
    items = [i for i in STATE["images"].values() if i["folder_id"] == folder_id]
    return ok({"total": len(items), "list": items})


@app.delete("/album/delete")
def album_delete():
    data = body()
    img_id = data.get("img_id")
    if img_id not in STATE["images"]:
        return fail(400, "图片不存在或已删除")
    STATE["images"].pop(img_id)
    return ok({"img_id": img_id})


if __name__ == "__main__":
    port = int(os.getenv("PORT", "9000"))
    print(f"Mock 相册服务启动：http://0.0.0.0:{port}  签名校验={SIGN_CHECK}")
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
