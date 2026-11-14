# mobile_sdk_api_auto

移动端 SDK 后台接口的自动化测试工程，覆盖相册、相机、浏览器、DJ 音乐播放器四块业务。

被测服务是仓库里的一个 Flask 应用（`mock_server/app.py`），实现了 13 个业务接口，
带参数校验、权限判断和服务端状态。测试代码直接请求这个服务，所以克隆仓库、装好依赖就能跑，
不需要连公司内网。当前用例 31 条。

## 环境要求

| 项 | 说明 |
| --- | --- |
| Python | 3.10 及以上（开发和验证用的是 3.13） |
| 操作系统 | Windows / macOS / Linux 均可，脚本不依赖特定 shell |
| 被测服务 | 仓库内 `mock_server/app.py`，默认监听 9000 端口 |
| Allure 命令行 | 可选。装了才能生成 HTML 报告，不装仍可跑用例，原始数据留在 `report/allure_raw` |

## 依赖与用途

| 包 | 用途 | 备注 |
| --- | --- | --- |
| `requests` | HTTP 请求 | 统一走 `common/request_handler.py` 里的 Session |
| `PyYAML` | 读取环境配置和用例数据 | 数据层用 `yaml.safe_load`，不做额外解析 |
| `pytest` | 用例执行、参数化、fixture | `pytest.ini` 里固定了扫描路径和执行参数 |
| `allure-pytest` | 报告，附带请求/响应与软断言明细 | 需要 allure 命令行转 HTML |
| `pytest-rerunfailures` | 失败重跑 | 配置为最多 2 次，间隔 1 秒 |
| `loguru` | 日志 | 控制台 + 按天切文件，10MB 轮转，保留 7 天 |
| `flask` | 起被测服务 | 仅 mock_server 使用，测试代码不依赖 |

安装：

```powershell
pip install -r requirements.txt
```

## 目录与职责

| 路径 | 职责 |
| --- | --- |
| `api/album_api.py` | 相册接口：建文件夹、上传、删除。方法只拼参数，不做断言 |
| `api/camera_api.py` | 相机接口：分辨率/帧率、水印 |
| `api/browser_api.py` | 浏览器接口：网页收藏、缓存清理 |
| `api/dj_api.py` | DJ 接口：歌单、播放、音量、均衡器、播放模式 |
| `common/conf_handler.py` | 读 `config/env.yaml`，用 `config/env_local.yaml` 做深度覆盖，产出 `config` 单例 |
| `common/request_handler.py` | 请求封装：拼 URL、算签名、带 token、401 重登、记日志，产出 `client` 单例 |
| `common/logger_handler.py` | loguru 初始化，输出到 `report/logs/sdk_api_日期.log` |
| `common/assert_handler.py` | 软断言。一条用例里的多个检查点全部执行完再统一抛错 |
| `config/env.yaml` | local / ci 两套地址，外加 Mock 账号 |
| `data/*.yaml` | 用例参数与预期，按模块分四个文件 |
| `testcases/conftest.py` | `client` fixture（session 级）、`prepared_env` fixture（复位数据并预置） |
| `testcases/test_*.py` | 只做三件事：读数据、调 api 层、写断言 |
| `mock_server/app.py` | 被测服务，13 个业务接口 + `/health` + `/__admin/reset` |
| `run.py` | 起服务、跑用例、生成报告的入口 |
| `Jenkinsfile` / `docker-compose.yml` | 流水线和容器编排 |

`api` 和 `common` 的分界：`api` 只描述「哪个接口、传什么」，`common` 只负责「怎么发出去、怎么记录」。

## 跑起来

```powershell
# 方式一：一条命令（自动起服务、跑完自动关）
python run.py

# 方式二：分开执行，方便看日志
python mock_server/app.py      # 终端 1，保持前台运行
pytest                          # 终端 2

# 只跑某个模块
pytest testcases/test_dj.py
```

正常输出结尾是：

```
============================= 31 passed in 0.72s ==============================
```

服务单独起的时候，先确认它活着：

```powershell
curl http://127.0.0.1:9000/health
# {"service":"mock-sdk-api","sign_check":false,"status":"ok"}
```

## 一次请求的调用链

以「上传图片」为例：

```
testcases/test_album.py::test_upload_image
  → api/album_api.py::AlbumApi.upload(folder_id, img_name)     拼 payload
  → common/request_handler.py::RequestHandler.send()            算 X-Sign、带 Authorization、发请求、记日志
  → mock_server/app.py::album_upload()                          校验 folder_id 归属，写内存状态
  → 返回 {"code":200,"data":{"img_id":2001,...}}
  → common/assert_handler.py::AssertHandler                    记录每个检查点，最后统一抛错
```

排查问题按这条链自上而下看，日志里每一步都有对应的 `-->` / `<--` 记录。

## 配置

`config/env.yaml`：

```yaml
current_env: "local"

local:
  base_url: "http://127.0.0.1:9000"
  timeout: 10
  sign_key: "mock-sign-key-2026"

ci:
  base_url: "http://host.docker.internal:9000"
  timeout: 15
  sign_key: "mock-sign-key-2026"

account:
  username: "testuser"
  password: "123456"
```

| 字段 | 含义 | 说明 |
| --- | --- | --- |
| `current_env` | 默认生效的环境名 | 可被 `ENV` 环境变量覆盖 |
| `base_url` | 接口根地址 | 可被 `BASE_URL` 覆盖，CI 里用这个注入 |
| `timeout` | 请求超时（秒） | 传进 `requests.session.request` |
| `sign_key` | 签名密钥 | 必须与服务端 `SIGN_KEY` 一致 |
| `account` | 登录账号 | Mock 服务的固定账号，不是真实凭据 |

生效顺序：`BASE_URL` / `ENV` 环境变量 → `config/env_local.yaml` → `config/env.yaml`。
`env_local.yaml` 用同样的结构，只写要覆盖的字段即可（`deep_merge` 递归合并，不需要写全）。

```yaml
# config/env_local.yaml 示例（该文件被 .gitignore 排除，不会进仓库）
local:
  base_url: "http://127.0.0.1:9001"
account:
  username: "your_name"
  password: "your_password"
```

切环境：

```powershell
$env:ENV = "ci"
$env:BASE_URL = "http://127.0.0.1:9001"
pytest
```

账号也可以用 `SDK_USER` / `SDK_PWD` 覆盖，适合流水线里按环境注入不同账号。

## 新增一条用例

### 只加场景，不改逻辑

在对应 `data/*.yaml` 里加一项即可，代码不用动：

```yaml
# data/album_data.yaml
create_folder:
  uri: "/album/folder/create"
  method: "POST"
  cases:
    - case_name: "相册名称只有空格-参数异常"
      json:
        name: "   "
        sort: 1
      expect:
        code: 400
        msg: "不能为空"
```

`expect.msg` 是可选的，写了就会检查提示文案是否包含该关键字，不写只比业务码。

```powershell
pytest testcases/test_album.py -k "只有空格"
```

### 加一个新接口

四步：

1. `mock_server/app.py` 加路由和校验逻辑。要判断入参就必须自己写，这是选 Flask 而不是静态 Mock 工具的原因。
2. `api/` 下对应模块加一个方法，只拼参数：

```python
def rename_folder(self, folder_id: int, new_name: str):
    return self.client.post("/album/folder/rename",
                            json={"folder_id": folder_id, "new_name": new_name})
```

3. `data/` 里加一段 `uri` + `method` + `cases`。
4. `testcases/` 里加一个参数化用例，断言写完整（成功校验返回字段，失败校验业务码和文案）。

如果新接口需要新的校验维度（比如要断言响应头、要检查数据库落库），才需要动 `testcases` 里的断言代码。

## 关于签名

请求头带 `X-Sign`，算法在客户端和服务端各实现一次，必须保持一致：

```
sign = MD5( METHOD + path + 按键排序的 "k=v" 拼接 + "&key=" + sign_key )
```

- 客户端：`common/request_handler.py::make_sign()`
- 服务端：`mock_server/app.py::make_sign()`

服务端由环境变量 `SIGN_CHECK` 控制是否强制校验，默认 `false`。本地默认关掉，是因为排查用例失败时
不应该先怀疑签名；要验证签名链路时打开：

```powershell
$env:SIGN_CHECK = "true"; python mock_server/app.py
```

打开后如果客户端 `sign_key` 和服务端 `SIGN_KEY` 不一致，所有请求会返回 401「签名校验失败」。
真实接入网关前，这一段是必查项。

## 测试数据与状态

服务端在内存里维护 `folders`、`images`、`collections`、`camera`、`dj`，用递增序号生成 ID：

| 计数器 | 起始值 | 第一个成功创建得到的 ID |
| --- | --- | --- |
| `folder_seq` | 1000 | 1001 |
| `image_seq` | 2000 | 2001 |
| `collect_seq` | 3000 | 3001 |

`POST /__admin/reset` 把状态恢复初始值。`conftest.py` 的 `prepared_env` 在 session 开始时做三件事：

1. 调 reset 复位；
2. 登录拿 token；
3. 预置一个相册（1001）和一张图片（2001）。

这样 `data/album_data.yaml` 里写死的 `folder_id: 1001`、`img_id: 2001` 就有依据，
用例不依赖执行顺序——单独跑一条、重复跑、失败重跑都不会因为数据被删而失败。

写新用例时如果依赖已有数据，优先在上述预置里加，不要在用例内部用前一条用例的产出。

## 报告与日志

```powershell
pytest                                        # 用例结果在控制台，Allure 原始数据在 report/allure_raw
allure generate report/allure_raw -o report/allure_html --clean
allure open report/allure_html
```

- 控制台：每条用例的软断言明细（`[PASS]` / `[FAIL] 期望= 实际=`）
- 日志：`report/logs/sdk_api_YYYYMMDD.log`，含完整请求体、响应体、耗时前的状态码
- Allure：按 feature/story 分组，失败用例可以定位到具体断言

`report/` 整个目录在 `.gitignore` 里，不会污染仓库。

## CI

**Docker Compose**

```powershell
docker compose up -d mock-sdk        # 只起被测服务
docker compose run --rm api-test     # 起服务 + 跑用例
docker compose down
```

两个容器在同一个 compose 网络里，用例容器的 `BASE_URL` 直接指向服务名 `http://mock-sdk:9000`，
不走 `host.docker.internal`。

**Jenkins**

`Jenkinsfile` 分四段：拉代码 → 轮询 `/health` 等服务就绪 → 装依赖 → 执行 pytest。
服务没起来直接失败，不会出现「环境没起、用例全红、以为是代码问题」。
被测服务在宿主机跑时用 `host.docker.internal:9000`，报告由 `post` 段发布 JUnit + Allure。

## 排错对照

| 现象 | 原因 | 处理 |
| --- | --- | --- |
| `ConnectionError` / `prepared_env` 里 reset 失败 | 被测服务没起 | `python mock_server/app.py`，或改用 `python run.py` |
| 所有请求返回 401「签名校验失败」 | `SIGN_CHECK=true` 但两端 `sign_key` 不一致 | 对齐 `config/env.yaml` 的 `sign_key` 和服务端 `SIGN_KEY` |
| 所有请求返回 401「token 可能失效」并反复重登 | 账号密码错 | 检查 `account`、`SDK_USER` / `SDK_PWD` |
| `ModuleNotFoundError: No module named 'common'` | 直接 `python testcases/test_xxx.py` 执行 | 用 `pytest` 从项目根目录跑；`conftest.py` 里补了 `sys.path`，pytest 路径下正常 |
| 断言 `folder_id` 不是 1001 | 前面有用例先创建过相册，序号已往后走 | 调 `POST /__admin/reset` 复位，或改用 `prepared_env` 预置的 ID |
| `allure` 命令找不到 | 只装了 `allure-pytest` 插件，没装命令行 | 装 allure 命令行后重跑生成步骤，用例本身不受影响 |
| 失败用例被自动重跑后仍失败 | 重跑配置为 2 次，属预期 | 看 Allure 里最终那次失败的断言内容 |

## 已知限制

- Mock 服务状态在内存里，重启即清空；多进程并发跑（`pytest-xdist`）会互相覆盖状态，当前按串行设计。
- 断言用 `AssertHandler` 而不是 pytest 原生 `assert`，所以失败信息是自定义汇总格式；如果想让 IDE 跳转到失败行，可以改成原生 `assert`。
- 用户名/密码类接口只校验固定账号，没有实现真实的用户表和多租户隔离。
- 报告依赖本地 allure 命令行，没做「没有命令行时自动降级输出 HTML」的兜底。
