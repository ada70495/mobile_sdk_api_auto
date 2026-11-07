// ============================================
// 企业级接口自动化测试 - Jenkins 流水线脚本 (Jenkinsfile)
// 适用场景：本地单机 Docker 化 CI（方案B：容器内本地 Git 仓库作为代码源）
//
// 前提：
//   1. 宿主机 Docker Desktop 已运行 blog-mock(WireMock, 8080)、blog-redis(6379)
//   2. Jenkins 容器内已安装 node/npm/newman、python3/pip
//   3. 代码已同步到容器内 /src/blog_auto_test
//   4. 注意：容器访问宿主机服务必须用 host.docker.internal（127.0.0.1 不通）
//
// 流水线五个阶段：
//   1. 拉取代码         —— 从容器内 Git 仓库检出源码
//   2. 准备测试环境     —— 注册 WireMock 规则 + 初始化 Redis 测试数据（关键：让流水线自愈）
//   3. Newman 执行      —— 跑 Postman 集合，产出 HTML + JUnit 报告
//   4. pytest 执行      —— 跑 Python 用例，产出 JUnit 报告
//   5. 报告归集         —— Jenkins 解析 JUnit、发布 HTML
// ============================================

pipeline {
    agent any

    stages {
        stage('1. 拉取Git仓库代码') {
            steps {
                // 方案B：容器内本地仓库（等效内网 Git 服务器）
                // 若网络可直接访问 GitHub，换成 https://github.com/ada70495/mobile_sdk_api_auto.git 即可
                git url: 'file:///src/blog_auto_test', branch: 'main'
            }
        }

        stage('2. 准备测试环境（注册Mock规则 + 初始化Redis数据）') {
            steps {
                sh '''
                    echo "=== 注册 WireMock 文章接口规则 ==="
                    curl -s -X POST -H "Content-Type: application/json; charset=UTF-8" \\
                        --data-binary @postman/mock_rule_posts.json \\
                        http://host.docker.internal:8080/__admin/mappings
                    echo ""
                    echo "=== 注册 WireMock 评论接口规则 ==="
                    curl -s -X POST -H "Content-Type: application/json; charset=UTF-8" \\
                        --data-binary @postman/mock_rule.json \\
                        http://host.docker.internal:8080/__admin/mappings
                    echo ""
                    echo "=== 初始化 Redis 测试数据 ==="
                    python3 -c "
import redis
r = redis.Redis(host='host.docker.internal', port=6379, db=0, decode_responses=True)
r.set('token_user_1', 'user_1_token_abc123')
print('Redis token_user_1 =', r.get('token_user_1'))
"
                '''
            }
        }

        stage('3. 执行Newman运行Postman接口集合') {
            steps {
                sh '''
                    mkdir -p report
                    newman run postman/blog-api-test.postman_collection.json \\
                        -e postman/ci-docker.postman_environment.json \\
                        -r cli,junit,htmlextra \\
                        --reporter-htmlextra-export report/newman_report.html \\
                        --reporter-junit-export report/newman-junit-result.xml
                '''
            }
        }

        stage('4. 执行Python pytest脚本') {
            steps {
                sh '''
                    # 容器内访问宿主机服务统一用 host.docker.internal
                    export BASE_URL=http://host.docker.internal:8080
                    export MOCK_URL=http://host.docker.internal:8080
                    export REDIS_HOST=host.docker.internal
                    export REDIS_PORT=6379
                    # 安装依赖（--break-system-packages 适配 Debian 系统 Python）
                    python3 -m pip install -q --break-system-packages \\
                        -i https://pypi.tuna.tsinghua.edu.cn/simple \\
                        -r pytest_case/requirements.txt
                    # 进入用例目录执行，-c 指定本项目配置，避免被根目录其他 pytest.ini 干扰
                    cd pytest_case && python3 -m pytest test_blog_api.py -v -c pytest.ini \\
                        --junitxml=../report/pytest-junit-result.xml
                '''
            }
        }
    }

    post {
        always {
            // 收集 Newman 与 pytest 两份 JUnit 报告
            junit testResults: 'report/*-junit-result.xml', allowEmptyResults: true
            publishHTML target: [
                allowMissing: true,
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
