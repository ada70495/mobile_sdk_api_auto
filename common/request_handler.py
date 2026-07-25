import requests
import hashlib
from common.logger_handler import logger
from common.conf_handler import *

class RequestBase:
    def __init__(self):
        # session保持会话，自动携带cookie，复用连接
        self.session = requests.Session()
        # 全局token，从配置读取
        self.token = env_data["token"]
        # 签名密钥
        self.sign_key = env_data["sign_key"]

    def get_sign(self, params):
        """
        生成接口MD5签名，适配后端验签规则
        规则：参数字典value排序拼接 + 密钥 做md5
        """
        sign_str = "".join(sorted([str(v) for v in params.values()])) + self.sign_key
        return hashlib.md5(sign_str.encode()).hexdigest()

    def get_new_token(self):
        """登录接口，重新获取token，写入yaml配置全局生效"""
        login_url = f"{BASE_URL}/user/login"
        payload = env_data["user"]
        res = self.session.post(login_url, json=payload).json()
        new_token = res["data"]["token"]
        # 更新内存+配置文件
        env_data["token"] = new_token
        write_yaml(CONFIG_PATH, env_data)
        self.token = new_token
        logger.info("Token刷新成功，已更新到配置文件")

    def send(self, method, uri, json=None, params=None):
        """统一请求入口，所有接口调用此方法"""
        url = BASE_URL + uri
        # 请求头携带鉴权token
        headers = {"Authorization": f"Bearer {self.token}"}
        # GET参数需要加签名
        if params:
            params["sign"] = self.get_sign(params)

        try:
            # 发起请求
            response = self.session.request(method, url, headers=headers, json=json, params=params, timeout=10)
            res = response.json()
            # 捕获token过期（code=401），自动刷新重试一次
            if res.get("code") == 401:
                logger.warning("检测到Token失效，执行自动刷新并重试接口")
                self.get_new_token()
                headers["Authorization"] = f"Bearer {self.token}"
                response = self.session.request(method, url, headers=headers, json=json, params=params, timeout=10)
                res = response.json()
            # 打印完整请求响应日志
            logger.info(f"【请求】{url} 参数:{json} 响应:{res}")
            return res
        except Exception as e:
            logger.error(f"接口请求异常：{e}")
            raise

# 全局请求实例，所有用例共用
api = RequestBase()