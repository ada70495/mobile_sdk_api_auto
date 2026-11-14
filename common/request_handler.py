"""请求封装：Session 复用 + MD5 签名 + token 自动携带 + 失效重试 + 全量日志"""
import hashlib

import requests
from requests import Response

from common.conf_handler import config
from common.logger_handler import logger


class RequestHandler:
    def __init__(self, base_url: str = None, timeout: int = None, sign_key: str = None):
        self.base_url = (base_url or config.base_url).rstrip("/")
        self.timeout = timeout or config.timeout
        self.sign_key = sign_key or config.sign_key
        self.session = requests.Session()
        self.token = ""

    def make_sign(self, method: str, path: str, payload: dict = None) -> str:
        """签名算法（与服务端一致）：方法 + 路径 + 按键排序的入参 + 密钥，做 MD5"""
        parts = [method.upper(), path]
        if isinstance(payload, dict):
            for key in sorted(payload):
                parts.append(f"{key}={payload[key]}")
        raw = "&".join(parts) + "&key=" + self.sign_key
        return hashlib.md5(raw.encode("utf-8")).hexdigest()

    def login(self, username: str = None, password: str = None) -> dict:
        """登录并把 token 写进实例，后续请求自动携带"""
        username = username or config.username
        password = password or config.password
        resp = self.send(
            "POST", "/user/login", json={"username": username, "password": password}, _auth=False
        )
        data = resp.json()
        if data.get("code") == 200:
            self.token = data["data"]["token"]
            logger.info(f"登录成功 user={username} token={self.token}")
        else:
            logger.error(f"登录失败 code={data.get('code')} msg={data.get('msg')}")
        return data

    def _headers(self, method: str, path: str, payload: dict) -> dict:
        headers = {
            "Content-Type": "application/json",
            "X-Sign": self.make_sign(method, path, payload),
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def send(self, method: str, path: str, json=None, params=None, _auth: bool = True, **kwargs) -> Response:
        """统一请求入口"""
        url = self.base_url + path
        payload = json if json is not None else (params or {})
        headers = self._headers(method, path, payload)
        if not _auth:
            headers.pop("Authorization", None)

        logger.info(f"--> {method.upper()} {path} | json={json} | params={params}")
        resp = self.session.request(
            method.upper(), url, headers=headers, json=json, params=params, timeout=self.timeout
        )
        logger.info(f"<-- {resp.status_code} | {resp.text[:400]}")

        # token 失效自动重登并重试一次
        if _auth and self.token:
            try:
                body = resp.json()
            except ValueError:
                body = {}
            if body.get("code") == 401:
                logger.warning("业务码 401，token 可能失效，重新登录后重试一次")
                self.token = ""
                self.login()
                headers = self._headers(method, path, payload)
                resp = self.session.request(
                    method.upper(), url, headers=headers, json=json, params=params, timeout=self.timeout
                )
                logger.info(f"<-- 重试 {resp.status_code} | {resp.text[:400]}")
        return resp

    def get(self, path, **kwargs) -> Response:
        return self.send("GET", path, **kwargs)

    def post(self, path, **kwargs) -> Response:
        return self.send("POST", path, **kwargs)

    def put(self, path, **kwargs) -> Response:
        return self.send("PUT", path, **kwargs)

    def delete(self, path, **kwargs) -> Response:
        return self.send("DELETE", path, **kwargs)

    def close(self):
        self.session.close()


client = RequestHandler()
