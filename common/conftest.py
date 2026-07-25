import pytest
from common.logger_handler import logger
from common.request_handler import api

@pytest.fixture(scope="session", autouse=True)
def init_token():
    # session级别：所有用例执行前只登录一次，全局复用token
    api.get_new_token()
    yield
    # 全部用例跑完执行后置
    logger.info("接口自动化全部用例执行完毕，建议手动清理测试脏数据")