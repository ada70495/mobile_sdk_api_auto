"""一键执行：拉起本地被测服务 → 跑全部用例 → 生成 Allure 报告

用法：
    python run.py                  # 全部用例
    python run.py testcases/test_dj.py    # 只跑某个模块
"""
import os
import shutil
import subprocess
import sys
import time

import requests

ROOT = os.path.dirname(os.path.abspath(__file__))
MOCK_PORT = os.getenv("PORT", "9000")
MOCK_URL = f"http://127.0.0.1:{MOCK_PORT}"


def start_mock():
    """本地 Mock 未启动时自动拉起子进程"""
    try:
        requests.get(f"{MOCK_URL}/health", timeout=1)
        print(f"[Mock] 服务已在运行：{MOCK_URL}")
        return None
    except Exception:
        pass

    print(f"[Mock] 启动本地被测服务：{MOCK_URL}")
    proc = subprocess.Popen(
        [sys.executable, os.path.join(ROOT, "mock_server", "app.py")],
        cwd=ROOT,
        env={**os.environ, "PORT": MOCK_PORT},
    )
    for _ in range(30):
        try:
            requests.get(f"{MOCK_URL}/health", timeout=1)
            print("[Mock] 启动成功")
            return proc
        except Exception:
            time.sleep(1)
    proc.terminate()
    raise RuntimeError("Mock 服务启动失败，请手动执行：python mock_server/app.py")


def gen_report():
    allure = shutil.which("allure")
    if not allure:
        print("[报告] 未检测到 allure 命令，跳过 HTML 生成（原始数据在 report/allure_raw）")
        return
    rc = subprocess.call(
        [allure, "generate", "report/allure_raw", "-o", "report/allure_html", "--clean"], cwd=ROOT
    )
    if rc == 0:
        print("[报告] 已生成：report/allure_html/index.html")
    else:
        print("[报告] 生成失败，请检查 allure 安装")


def main():
    os.chdir(ROOT)
    mock_proc = start_mock()
    try:
        args = sys.argv[1:] or []
        rc = subprocess.call([sys.executable, "-m", "pytest", *args], cwd=ROOT)
        gen_report()
        print(f"[结果] pytest 退出码 = {rc}")
        sys.exit(rc)
    finally:
        if mock_proc:
            mock_proc.terminate()
            print("[Mock] 服务已关闭")


if __name__ == "__main__":
    main()
