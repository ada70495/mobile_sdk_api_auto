# ============================================
# 企业级接口自动化测试 - Jenkins 流水线脚本 (Jenkinsfile)
# 流水线执行流程（CI持续集成）：
#   1. 拉取Git仓库最新代码
#   2. 调用Docker启动 Mock + Redis 测试环境
#   3. 执行 Newman 运行 Postman 接口集合
#   4. 执行 Python pytest 脚本（双链路校验）
#   5. 解析 JUnit 报告 + 发布 HTML 报告
#   6. 销毁容器，清理测试环境
# ============================================

pipeline {
    agent any

    tools {
        // 在Jenkins全局工具配置中新增名为 Node18 的Node.js
        nodejs 'Node18'
    }

    stages {
        stage('1. 拉取Git仓库代码') {
            steps {
                // 替换为你的Git仓库地址（Gitee/GitHub）
                git url: '你的Git仓库地址', branch: 'main'
            }
        }

        stage('2. Docker启动Mock+Redis测试环境') {
            steps {
                sh '''
                    # 一键启动 WireMock(评论Mock) + Redis(缓存依赖)
                    docker compose up -d
                    # 等待容器服务完全启动就绪
                    sleep 5
                '''
            }
        }

        stage('3. 执行Newman运行Postman接口集合') {
            steps {
                sh '''
                    # 安装newman及HTML报告插件
                    npm install -g newman newman-reporter-htmlextra
                    mkdir -p report
                    # 执行Postman集合，生成 HTML报告 + JUnit的xml结果
                    newman run postman/blog-api-test.postman_collection.json \\
                        -e postman/local-dev.postman_environment.json \\
                        -r cli,html,junit \\
                        --reporter-html-export ./report/newman_report.html \\
                        --reporter-junit-export ./report/newman-junit-result.xml
                '''
            }
        }

        stage('4. 执行Python pytest脚本') {
            steps {
                sh '''
                    # 创建虚拟环境并安装依赖
                    python -m venv .venv
                    . .venv/bin/activate
                    pip install -r pytest_case/requirements.txt
                    # 执行pytest接口用例
                    pytest pytest_case/test_blog_api.py -v
                '''
            }
        }
    }

    post {
        always {
            // 无论成功失败都执行：
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
            // 3. 销毁Mock+Redis容器，清理测试环境，避免残留数据影响下轮构建
            sh 'docker compose down'
        }
        success {
            echo "✅ 自动化回归全部用例通过"
        }
        failure {
            echo "❌ 接口自动化用例失败，触发告警（邮件/企业微信/钉钉）"
        }
    }
}
