# ============================================
# 企业级接口自动化测试 - Python pytest 脚本
# 测试目标：
#   1. 被测接口：JSONPlaceholder 公开博客API（永久免费，无密钥限制）
#   2. Mock接口：本地WireMock模拟的下游评论接口
#   3. Redis依赖：读取被测业务缓存的用户token
# 运行命令: pytest test_blog_api.py -v
# ============================================

import requests          # HTTP请求库
import redis             # Redis操作库
import pytest            # 测试框架

# ---------- 测试环境地址配置 ----------
BASE_URL = "https://jsonplaceholder.typicode.com"   # 被测博客API（免费公开）
MOCK_URL = "http://127.0.0.1:8080"                  # 本地WireMock模拟评论接口
REDIS_HOST = "127.0.0.1"                            # Redis容器地址
REDIS_PORT = 6379                                   # Redis端口

# ---------- 连接Redis（Docker容器启动） ----------
r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)


def test_get_blog_post():
    """用例1：测试获取博客文章详情接口"""
    # 1. 读取Redis缓存中的用户token（模拟被测业务依赖缓存）
    token = r.get("token_user_1")
    print(f"从Redis读取用户token: {token}")

    # 2. 调用被测博客接口
    resp = requests.get(f"{BASE_URL}/posts/1", timeout=10)

    # 3. 断言：状态码 + 业务字段（双重断言）
    assert resp.status_code == 200, f"状态码异常: {resp.status_code}"
    data = resp.json()
    assert data["id"] == 1, "文章ID断言失败"
    assert data["userId"] == 1, "作者ID断言失败"
    print(f"文章标题: {data['title'][:20]}...")


def test_get_mock_comments():
    """用例2：测试Mock模拟的下游评论接口（下游后端未开发，先Mock）"""
    # 1. 调用本地WireMock模拟的评论接口
    resp = requests.get(f"{MOCK_URL}/api/comments?postId=1", timeout=10)

    # 2. 断言：Mock接口正常返回
    assert resp.status_code == 200, f"Mock接口状态码异常: {resp.status_code}"
    data = resp.json()
    assert "mock模拟的评论内容" in data[0]["body"], "Mock返回内容断言失败"
    print(f"Mock评论内容: {data[0]['body']}")


if __name__ == "__main__":
    # 直接运行脚本时执行全部用例
    pytest.main(["-v", "-s", __file__])
