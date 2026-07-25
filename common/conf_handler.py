import yaml
import os

# 获取当前文件绝对路径
BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# 公共模板配置路径（上传GitHub）
CONFIG_PATH = os.path.join(BASE_PATH, "config/env.yaml")
# 本地私有配置路径
LOCAL_CONFIG_PATH = os.path.join(BASE_PATH, "config/XXX.yaml")

def read_yaml(path):
    """通用yaml读取函数"""
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def write_yaml(path, data):
    """通用yaml写入函数，用于更新token"""
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, ensure_ascii=False)

# 逻辑：本地有私有配置优先读私有配置，没有就读公共模板
if os.path.exists(LOCAL_CONFIG_PATH):
    env_data = read_yaml(LOCAL_CONFIG_PATH)
else:
    env_data = read_yaml(CONFIG_PATH)

# 获取当前选中环境
ENV = env_data["current_env"]
# 提取对应环境的接口根地址
BASE_URL = env_data[ENV]["base_url"]