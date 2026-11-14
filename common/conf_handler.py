"""配置读取

优先级：显式传入 env > 环境变量 ENV > env.yaml 里的 current_env
本地私有配置 config/env_local.yaml 存在时做深度覆盖（该文件不入库，用于放真实账号/密钥）
"""
import os

import yaml

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_DIR = os.path.join(PROJECT_ROOT, "config")
ENV_FILE = os.path.join(CONFIG_DIR, "env.yaml")
LOCAL_ENV_FILE = os.path.join(CONFIG_DIR, "env_local.yaml")


def read_yaml(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def deep_merge(base, override):
    """递归合并：override 覆盖 base，dict 逐层合并"""
    result = dict(base or {})
    for key, value in (override or {}).items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


class Config:
    def __init__(self, env=None):
        data = read_yaml(ENV_FILE)
        if os.path.exists(LOCAL_ENV_FILE):
            data = deep_merge(data, read_yaml(LOCAL_ENV_FILE))
        self._data = data
        self.env = env or os.getenv("ENV") or data.get("current_env", "local")
        if self.env not in data:
            raise ValueError(f"环境 {self.env} 未定义，可选：{[k for k in data if k not in ('current_env', 'account')]}")
        self._env = data[self.env]

    @property
    def base_url(self) -> str:
        # CI 常用注入方式：环境变量 BASE_URL 优先
        return os.getenv("BASE_URL") or self._env["base_url"]

    @property
    def timeout(self) -> int:
        return self._env.get("timeout", 10)

    @property
    def sign_key(self) -> str:
        return self._env.get("sign_key", "")

    @property
    def account(self) -> dict:
        return self._data.get("account", {})

    @property
    def username(self) -> str:
        return os.getenv("SDK_USER") or self.account.get("username", "")

    @property
    def password(self) -> str:
        return os.getenv("SDK_PWD") or self.account.get("password", "")

    def summary(self) -> str:
        return f"ENV={self.env} BASE_URL={self.base_url} TIMEOUT={self.timeout}"


config = Config()
