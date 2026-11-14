# mobile_sdk_api_auto

移动端 SDK 后台接口自动化测试框架 —— 覆盖 **相册 / 相机 / 浏览器 / DJ 音乐播放器** 四大业务模块。

一套可在本地和 CI 里**真实跑通**的分层架构：为了解决"脱敏域名 + 无被测服务 = 只能看不能跑"的问题，仓库内自带一个 Flask 被测服务（`mock_server/`），
启动后 31 条用例全部可直接执行，覆盖正向流程、参数校验、权限越权、幂等与边界值。

---

## 一、技术栈

| 类别 | 选型 |
| --- | --- |
| 语言 | Python 3.10+ |
| 请求层 | requests（Session 会话复用） |
| 用例框架 | pytest + YAML 数据驱动 |
| 报告 | Allure + JUnit XML |
| 稳定性 | pytest-rerunfailures（失败自动重跑） |
| 日志 | loguru（控制台 + 按天切割文件） |
| 被测服务 | Flask（自建，13 个业务接口） |
| 持续集成 | Jenkins Pipeline + Docker Compose |

## 二、目录结构

```
mobile_sdk_api_auto/
├── api/                    # 接口层：一个模块一个类，只描述接口，不做断言
│   ├── album_api.py        #   相册：建文件夹 / 上传 / 删除
│   ├── camera_api.py       #   相机：分辨率帧率 / 水印
│   ├── browser_api.py      #   浏览器：收藏 / 清缓存
│   └── dj_api.py           #   DJ：歌单 / 播放 / 音量 / 均衡器 / 播放模式
├── common/                 # 公共层
│   ├── conf_handler.py     #   多环境配置（env.yaml + env_local.yaml 深度覆盖）
│   ├── logger_handler.py   #   日志（loguru）
│   ├── request_handler.py  #   请求封装：签名 + token + 401 自动重登重试
│   └── assert_handler.py   #   软断言：一条用例多个断言全跑完再统一失败
├── config/
│   ├── env.yaml            #   local / ci 双环境（入库）
│   └── env_local.yaml      #   本地私有账号密钥（.gitignore 排除）
├── data/                   # YAML 数据层：参数与代码解耦
│   ├── album_data.yaml
│   ├── camera_data.yaml
│   ├── browser_data.yaml
│   └── dj_data.yaml
├── testcases/              # 用例层：只做调用 + 断言
│   ├── conftest.py         #   client / 环境自愈 fixture
│   ├── test_album.py
│   ├── test_camera.py
│   ├── test_browser.py
│   └── test_dj.py
├── mock_server/
│   └── app.py              #   本地被测服务（含数据复位接口）
├── report/                 # 运行产物（.gitignore 排除）
├── run.py                  # 一键执行：拉服务 → 跑用例 → 生成报告
├── pytest.ini
├── requirements.txt
├── docker-compose.yml
└── Jenkinsfile
```

## 三、接口覆盖

被测服务共 13 个业务接口（HTTP 状态码统一 200，用响应体 `code` 区分业务结果）：

| 模块 | 接口 | 说明 | 关键校验 |
| --- | --- | --- | --- |
| 用户 | `POST /user/login` | 登录换取 token | 用户名空 → 400，密码错 → 401 |
| 相册 | `POST /album/folder/create` | 创建相册文件夹 | 名称空 → 400，超 20 字 → 400，重名 → 409 |
| 相册 | `POST /album/upload` | 上传图片 | 相册不存在 → 403（越权拦截） |
| 相册 | `DELETE /album/delete` | 删除图片 | 已删除/不存在 → 400（幂等） |
| 相机 | `POST /camera/param/set` | 分辨率 + 帧率 | 分辨率仅 720P/1080P/4K；fps 15–60 |
| 相机 | `POST /camera/watermark` | 水印开关 | open 必须布尔；位置仅 bottom/top |
| 浏览器 | `POST /browser/collect` | 网页收藏 | URL 空 → 400；必须以 http/https 开头 |
| 浏览器 | `POST /browser/cache/clear` | 缓存清理 | 类型仅 all/image/cookie |
| DJ | `GET /dj/playlist` | 歌单查询 | — |
| DJ | `POST /dj/play` | 播放歌曲 | 歌曲不存在 → 404 |
| DJ | `POST /dj/volume` | 音量调节 | 0–100 整数，越界 → 400 |
| DJ | `POST /dj/eq` | 均衡器 | normal/rock/jazz/vocal |
| DJ | `POST /dj/play_mode` | 播放模式 | sequence/loop/single/random |

运维接口：`GET /health`（健康检查）、`POST /__admin/reset`（测试数据复位）。

## 四、本地运行

```powershell
# 1. 安装依赖
pip install -r requirements.txt

# 2. 一键跑（自动拉起被测服务 → 执行用例 → 生成 Allure 报告）
python run.py

# 或者：先单独起服务，再跑用例
python mock_server/app.py          # 另开一个终端，默认 9000 端口
pytest                             # 走 pytest.ini 配置
```

只跑某个模块：

```powershell
pytest testcases/test_dj.py
```

打开报告：`report/allure_html/index.html`（执行 `allure generate` 后生成）。

## 五、环境切换与配置

`config/env.yaml` 只放脱敏/本地的地址，真实账号密钥写 `config/env_local.yaml`（已在 `.gitignore` 中排除）。

```yaml
current_env: "local"
local:
  base_url: "http://127.0.0.1:9000"
  timeout: 10
  sign_key: "mock-sign-key-2026"
ci:
  base_url: "http://host.docker.internal:9000"
```

优先级：**环境变量 `BASE_URL` / `ENV` > `env_local.yaml` 覆盖 > `env.yaml`**，所以 CI 不需要改代码：

```powershell
$env:ENV="ci"; $env:BASE_URL="http://host.docker.internal:9000"; pytest
```

账号支持 `SDK_USER` / `SDK_PWD` 环境变量覆盖，便于在流水线里注入。

## 六、签名机制

请求头 `X-Sign`，算法与服务端完全一致：

```
sign = MD5( METHOD + path + 按键排序的 "k=v" 拼接 + "&key=" + sign_key )
```

- 客户端：`common/request_handler.py::make_sign()`
- 服务端：`mock_server/app.py::make_sign()`

服务端通过环境变量 `SIGN_CHECK` 控制是否强制校验，**本地默认关闭**（`SIGN_CHECK=false`）方便调试；
对接真实网关或做安全回归时 `SIGN_CHECK=true` 打开，链路即可双向验证。

## 七、持续集成

**Docker Compose**：一个命令拉起被测服务 + 执行用例

```powershell
docker compose up -d mock-sdk           # 只起服务
docker compose run --rm api-test        # 跑全量用例
docker compose down
```

**Jenkins**：`Jenkinsfile` 五阶段流水线

1. 拉取代码
2. 等待被测服务就绪（`/health` 轮询，环境没起来直接失败，避免误报）
3. 安装依赖
4. 执行 pytest（产出 JUnit + Allure 原始数据）
5. 报告归集（JUnit 趋势 + Allure 报告发布）

## 八、设计要点

1. **分层解耦**：`api` 描述接口、`data` 管参数、`testcases` 只管调用与断言，改接口只改一处。
2. **环境自愈**：`conftest.py` 每次执行前调用 `/__admin/reset` 复位数据并预置基础相册/图片，
   用例不依赖执行顺序，单条运行、重复运行、失败重跑都不会脏数据。
3. **鉴权闭环**：Session 复用 + token 自动携带 + 业务码 401 自动重登并重试一次，用例不用关心登录。
4. **软断言**：`AssertHandler` 让一条用例的多个校验点全部执行完再汇总失败，失败信息一次看全。
5. **数据驱动**：新增用例只需在 YAML 里加一条 `case`，不改代码。
6. **可观测**：每次请求/响应全量落日志（`report/logs/sdk_api_日期.log`），失败原因可直接定位。

## 九、安全说明

仓库内所有域名、账号、密钥均为本地 Mock 服务的固定值，不含公司任何真实环境信息；
真实配置通过 `config/env_local.yaml` 或环境变量注入，不入库。
