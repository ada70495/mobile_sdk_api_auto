import pytest
import os

if __name__ == "__main__":
    # 执行全部pytest自动化用例
    pytest.main()
    # 调用allure命令，生成html可视化报告
    os.system("allure generate report/allure_raw -o report/allure_html --clean")
    print("接口自动化执行完成，Allure报告已生成到 report/allure_html 文件夹")