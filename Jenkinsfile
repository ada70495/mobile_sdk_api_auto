# ============================================
# 企业级接口自动化测试 - Jenkins 流水线脚本 (Jenkinsfile)
# 适用场景：本地单机练习 / 内网CI服务器
#   前提：宿主机 Docker Desktop 已运行 blog-mock(8080)、blog-redis(6379)
#   前提：Jenkins 容器内已安装 node/npm/newman、python3/pip
#   注意：Jenkins容器内访问宿主机服务要用 host.docker.internal（不能用 127.0.0.1）
# 流水线执行流程：
#   1. 拉取 GitHub 仓库最新代码
#   2. 执行 Newman 运行 Postman 接口集合（CI-Docker环境），生成 HTML + JUnit 报告
#   3. 执行 Python pytest 脚本（环境变量指向宿主机服务）
#   4. Jenkins 解析 JUnit 报告、发布 HTML 报告
# ============================================

pipeline {
    agent any

    stages {
        stage('1. 拉取Git仓库代码') {
            steps {
                // 换成自己的仓库地址即可
                git url: 'https://github.com/ada70495/mobile_sdk_api_auto.git', branch: 'main'
            }
        }

        stage('2. 执行Newman运行Postman接口集合') {
            steps {
                sh '''
                    # 确保报告目录存在
                    mkdir -p report
                    # 执行Postman集合（使用CI环境文件，Mock地址指向宿主机）
                    newman run postman/blog-api-test.postman_collection.json \\
                        -e postman/ci-docker.postman_environment.json \\
                        -r cli,junit,htmlextra \\
                        --reporter-htmlextra-export report/newman_report.html \\
                        --reporter-junit-export report/newman-junit-result.xml
                '''
            }
        }

        stage('3. 执行Python pytest脚本') {
            steps {
                sh '''
                    # 容器内访问宿主机Redis/Mock：使用 host.docker.internal
                    export REDIS_HOST=host.docker.internal
                    export MOCK_URL=http://host.docker.internal:8080
                    # 安装Python依赖（首次较慢，之后秒装）
                    python3 -m pip install -q -r pytest_case/requirements.txt
                    # 执行pytest接口用例（-c 指定本项目配置，避免被仓库根目录其他项目的pytest.ini干扰）
                    python3 -m pytest pytest_case/test_blog_api.py -v -c pytest_case/pytest.ini
                '''
            }
        }
    }

    post {
        always {
            // 1. 解析JUnit的xml，Jenkins页面展示用例通过/失败数量
            junit testResults: 'report/newman-junit-result.xml', allowEmptyResults: true
            // 2. 发布HTML可视化报告
            publishHTML target: [
                allowMissing: false,
                alwaysLinkToLastBuild: true,
                keepAll: true,
                reportDir: 'report',
                reportFiles: 'newman_report.html',
                reportName: 'Postman接口自动化测试报告'
            ]
        }
        success {
            echo "✅ 自动化回归全部用例通过"
        }
        failure {
            echo "❌ 接口自动化用例失败，触发告警（邮件/企业微信/钉钉）"
        }
    }
}
