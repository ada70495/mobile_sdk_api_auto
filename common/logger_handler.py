"""日志：控制台彩色输出 + 文件按天切割，保留 7 天"""
import os
import sys

from loguru import logger

LOG_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "report", "logs"
)


def _setup():
    os.makedirs(LOG_DIR, exist_ok=True)
    logger.remove()
    logger.add(
        sys.stdout,
        level="INFO",
        format="<green>{time:HH:mm:ss}</green> | <level>{level:8}</level> | {message}",
    )
    logger.add(
        os.path.join(LOG_DIR, "sdk_api_{time:YYYYMMDD}.log"),
        level="INFO",
        rotation="10 MB",
        retention="7 days",
        encoding="utf-8",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level:8} | {message}",
    )
    return logger


logger = _setup()
