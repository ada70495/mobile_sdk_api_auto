"""本地被测服务：移动端 SDK 接口（相册 / 相机 / 浏览器 / DJ 音乐播放器）

替代公司内网的脱敏测试环境，让整套用例在本地、在 CI 里都能真实跑通。

启动：
    python mock_server/app.py
    $env:PORT=9001; python mock_server/app.py       # PowerShell 改端口

环境变量：
    PORT         监听端口，默认 9000
    SIGN_CHECK   是否强制校验签名，默认 false（线上开启）
    SIGN_KEY     签名密钥，默认 mock-sign-key-2026

业务约定：HTTP 状态码统一 200，用响应体里的 code 区分业务结果
    200 成功 / 400 参数非法 / 401 未登录或签名错误 / 403 越权 / 404 资源不存在 / 409 重复
"""
import hashlib
import os

from flask import Flask, jsonify, request

app = Flask(__name__)
app.json.ensure_ascii = False

SIGN_CHECK = os.getenv("SIGN_CHECK", "false").strip().lower() in ("1", "true", "yes")
SIGN_KEY = os.getenv("SIGN_KEY", "mock-sign-key-2026")

RESOLUTIONS = {"720P", "1080P", "4K"}
CACHE_TYPES = {"all", "image", "cookie"}
EQ_MODES = {"normal", "rock", "jazz", "vocal"}
PLAY_MODES = {"sequence", "loop", "single", "random"}
WATERMARK_POSITIONS = {"bottom", "top"}

SONGS = [
    {"song_id": 1, "name": "夜航", "artist": "Mock Band", "duration": 214},
    {"song_id": 2, "name": "霓虹", "artist": "Mock Band", "duration": 188},
    {"song_id": 3, "name": "晚风", "artist": "Mock Band", "duration": 240},
    {"song_id": 4, "name": "回声", "artist": "Mock Band", "duration": 196},
]


def init_state():
    """每次 reset 回到初始状态，保证用例可重复执行"""
    return {
        "folders": {},
        "images": {},
        "folder_seq": 1000,
        "image_seq": 2000,
        "collect_seq": 3000,
        "collections": {},
        "camera": {},
        "dj": {"volume": 50, "eq": "normal", "play_mode": "sequence", "playing": None},
    }


STATE = init_state()


def ok(data=None, msg="success"):
    return jsonify({"code": 200, "msg": msg, "data": data})


def fail(code, msg):
    return jsonify({"code": code, "msg": msg, "data": None})


def body():
    return request.get_json(silent=True) or {}


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
    return jsonify({"status": "ok", "service": "mock-sdk-api", "sign_check": SIGN_CHECK})


@app.post("/__admin/reset")
def reset():
    """测试数据复位，供 conftest 在整轮执行前调用"""
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


# ---------------- 相册 ----------------
@app.post("/album/folder/create")
def album_folder_create():
    data = body()
    name = (data.get("name") or "").strip()
    if not name:
        return fail(400, "文件夹名称不能为空")
    if len(name) > 20:
        return fail(400, "文件夹名称超长（最多20个字符）")
    if name in STATE["folders"]:
        return fail(409, "相册名称已存在")
    STATE["folder_seq"] += 1
    folder_id = STATE["folder_seq"]
    STATE["folders"][name] = {"folder_id": folder_id, "name": name, "sort": data.get("sort", 0)}
    return ok({"folder_id": folder_id, "name": name})


@app.post("/album/upload")
def album_upload():
    data = body()
    folder_id = data.get("folder_id")
    img_name = (data.get("img_name") or "").strip()
    if not any(f["folder_id"] == folder_id for f in STATE["folders"].values()):
        return fail(403, "无权访问该相册")
    if not img_name:
        return fail(400, "图片名称不能为空")
    STATE["image_seq"] += 1
    img_id = STATE["image_seq"]
    STATE["images"][img_id] = {"img_id": img_id, "folder_id": folder_id, "img_name": img_name}
    return ok({"img_id": img_id, "folder_id": folder_id})


@app.delete("/album/delete")
def album_delete():
    data = body()
    img_id = data.get("img_id")
    if img_id not in STATE["images"]:
        return fail(400, "图片不存在或已删除")
    STATE["images"].pop(img_id)
    return ok({"img_id": img_id})


# ---------------- 相机 ----------------
@app.post("/camera/param/set")
def camera_param_set():
    data = body()
    resolution = data.get("resolution")
    fps = data.get("fps")
    if resolution not in RESOLUTIONS:
        return fail(400, "不支持的分辨率，可选 720P/1080P/4K")
    if not isinstance(fps, int) or isinstance(fps, bool) or not (15 <= fps <= 60):
        return fail(400, "帧率超出合法范围（15-60）")
    STATE["camera"]["resolution"] = resolution
    STATE["camera"]["fps"] = fps
    return ok({"resolution": resolution, "fps": fps})


@app.post("/camera/watermark")
def camera_watermark():
    data = body()
    open_flag = data.get("open")
    position = data.get("position")
    if not isinstance(open_flag, bool):
        return fail(400, "open 必须为布尔值")
    if open_flag and position not in WATERMARK_POSITIONS:
        return fail(400, "水印位置仅支持 bottom/top")
    STATE["camera"]["watermark"] = {"open": open_flag, "position": position}
    return ok({"open": open_flag, "position": position})


# ---------------- 浏览器 ----------------
@app.post("/browser/collect")
def browser_collect():
    data = body()
    url = (data.get("url") or "").strip()
    title = (data.get("title") or "").strip()
    if not url:
        return fail(400, "链接地址不能为空")
    if not url.startswith(("http://", "https://")):
        return fail(400, "链接格式不正确，必须以 http/https 开头")
    STATE["collect_seq"] += 1
    collect_id = STATE["collect_seq"]
    STATE["collections"][collect_id] = {"collect_id": collect_id, "url": url, "title": title}
    return ok({"collect_id": collect_id, "url": url})


@app.post("/browser/cache/clear")
def browser_cache_clear():
    data = body()
    cache_type = data.get("cache_type")
    if cache_type not in CACHE_TYPES:
        return fail(400, "不支持的缓存类型，可选 all/image/cookie")
    return ok({"cleared": cache_type})


# ---------------- DJ 音乐播放器 ----------------
@app.get("/dj/playlist")
def dj_playlist():
    return ok({"total": len(SONGS), "list": SONGS})


@app.post("/dj/play")
def dj_play():
    data = body()
    song_id = data.get("song_id")
    song = next((s for s in SONGS if s["song_id"] == song_id), None)
    if song is None:
        return fail(404, "歌曲不存在")
    STATE["dj"]["playing"] = song_id
    return ok({"song_id": song_id, "playing": True, "duration": song["duration"]})


@app.post("/dj/volume")
def dj_volume():
    data = body()
    volume = data.get("volume")
    if not isinstance(volume, int) or isinstance(volume, bool) or not (0 <= volume <= 100):
        return fail(400, "音量必须在 0-100 之间")
    STATE["dj"]["volume"] = volume
    return ok({"volume": volume})


@app.post("/dj/eq")
def dj_eq():
    data = body()
    mode = data.get("mode")
    if mode not in EQ_MODES:
        return fail(400, "均衡器模式仅支持 normal/rock/jazz/vocal")
    STATE["dj"]["eq"] = mode
    return ok({"mode": mode})


@app.post("/dj/play_mode")
def dj_play_mode():
    data = body()
    mode = data.get("mode")
    if mode not in PLAY_MODES:
        return fail(400, "播放模式仅支持 sequence/loop/single/random")
    STATE["dj"]["play_mode"] = mode
    return ok({"mode": mode})


if __name__ == "__main__":
    port = int(os.getenv("PORT", "9000"))
    print(f"Mock SDK 服务启动：http://0.0.0.0:{port}  签名校验={SIGN_CHECK}")
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
