import logging
import os
from datetime import datetime

def get_logger():
    # 拼接日志存放路径
    log_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "report/logs")
    # 不存在则自动创建文件夹
    os.makedirs(log_path, exist_ok=True)
    # 日志文件按每日命名
    log_file = os.path.join(log_path, f"{datetime.now().strftime('%Y%m%d')}.log")

    # 初始化日志对象
    logger = logging.getLogger("api_auto")
    logger.setLevel(logging.INFO)
    # 防止重复添加日志处理器
    if not logger.handlers:
        # 文件日志：落地到本地文件
        fh = logging.FileHandler(log_file, encoding="utf-8")
        # 控制台日志：终端打印
        sh = logging.StreamHandler()
        # 日志格式：时间-级别-信息
        fmt = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        fh.setFormatter(fmt)
        sh.setFormatter(fmt)
        logger.addHandler(fh)
        logger.addHandler(sh)
    return logger

# 全局日志实例，全项目统一调用
logger = get_logger()