// ============================================
// mobile_sdk_api_auto —— Jenkins 流水线
//
// 前提：
//   1. 宿主机已启动被测服务：docker compose up -d mock-sdk（监听 9000）
//   2. Jenkins 容器内装有 python3 / pip
//   3. 容器访问宿主机必须用 host.docker.internal（127.0.0.1 不通）
//   4. 需要安装插件：JUnit、Allure Jenkins Plugin
//
// 阶段：
//   1. 拉取代码
//   2. 等待被测服务就绪（健康检查，避免环境没起来就开跑）
//   3. 安装依赖
//   4. 执行 pytest（产出 JUnit + Allure 原始数据）
//   5. 报告归集（由 post 段发布）
// ============================================

pipeline {
    agent any

    environment {
        ENV = 'ci'
        BASE_URL = 'http://host.docker.internal:9000'
        PYPI = 'https://pypi.tuna.tsinghua.edu.cn/simple'
    }

    stages {
        stage('1. 拉取代码') {
            steps {
                git url: 'https://github.com/ada70495/mobile_sdk_api_auto.git', branch: 'main'
            }
        }

        stage('2. 等待被测服务就绪') {
            steps {
                sh '''
                    echo "等待被测服务：$BASE_URL/health"
                    for i in $(seq 1 30); do
                        if curl -fsS "$BASE_URL/health" >/dev/null 2>&1; then
                            echo "被测服务已就绪"
                            exit 0
                        fi
                        sleep 2
                    done
                    echo "被测服务未就绪，请先在宿主机执行：docker compose up -d mock-sdk"
                    exit 1
                '''
            }
        }

        stage('3. 安装依赖') {
            steps {
                sh '''
                    python3 -m pip install -q --break-system-packages -i $PYPI -r requirements.txt
                    python3 -m pip list | grep -Ei "pytest|requests|allure|loguru|flask" || true
                '''
            }
        }

        stage('4. 执行接口用例') {
            steps {
                sh '''
                    mkdir -p report
                    python3 -m pytest -p no:cacheprovider \\
                        --junitxml=report/pytest-junit-result.xml \\
                        --alluredir=report/allure_raw
                '''
            }
        }
    }

    post {
        always {
            junit testResults: 'report/pytest-junit-result.xml', allowEmptyResults: true
            allure includeProperties: false, jdk: '', results: [[path: 'report/allure_raw']]
        }
        success {
            echo '接口自动化全量回归通过'
        }
        failure {
            echo '接口自动化存在失败用例，触发告警（邮件/企业微信/钉钉）'
        }
    }
}
