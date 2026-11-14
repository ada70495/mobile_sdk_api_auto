# album_api_auto

相册后台接口的自动化测试工程，覆盖相册文件夹的创建、列表、重命名、删除，以及相册内图片的上传、查询、删除。
技术栈：Python 3.13 + requests + pytest + PyYAML + Allure + loguru，被测服务用 Flask 起在本地。

被测服务是仓库里的一个 Flask 应用（`mock_server/app.py`），8 个业务接口，带参数校验、权限判断和会话状态。
测试代码直接请求这个服务，克隆仓库、装好依赖就能跑，不依赖内网环境。当前用例 20 条。

## 环境要求

| 项 | 说明 |
| --- | --- |
| Python | 3.10 及以上（验证用的是 3.13） |
| 被测服务 | 仓库内 `mock_server/app.py`，默认监听 9000 端口 |
| Allure 命令行 | 可选。装了才能生成 HTML 报告，不装仍可跑用例，原始数据留在 `report/allure_raw` |

## 依赖与用途

| 包 | 用途 | 备注 |
| --- | --- | --- |
| `requests` | HTTP 请求 | 统一走 `common/request_handler.py` 的 Session |
| `PyYAML` | 读取环境配置和用例数据 | 数据层用 `yaml.safe_load` |
| `pytest` | 用例执行、参数化、fixture | `pytest.ini` 固定扫描路径与执行参数 |
| `allure-pytest` | 报告，附带请求/响应与软断言明细 | 需要 allure 命令行转 HTML |
| `pytest-rerunfailures` | 失败重跑 | 最多 2 次，间隔 1 秒 |
| `loguru` | 日志 | 控制台 + 按天切文件，10MB 轮转，保留 7 天 |
| `flask` | 起被测服务 | 仅 `mock_server` 使用，测试代码不依赖 |

安装：

```powershell
pip install -r requirements.txt
```

## 目录与职责

| 路径 | 职责 |
| --- | --- |
| `api/album_api.py` | 相册接口：文件夹四个操作 + 图片三个操作，只拼参数不做断言 |
| `common/conf_handler.py` | 读 `config/env.yaml`，用 `config/env_local.yaml` 深度覆盖，产出 `config` 单例 |
| `common/request_handler.py` | 请求封装：拼 URL、算签名、带 token、401 重登、记日志，产出 `client` 单例 |
| `common/logger_handler.py` | loguru 初始化，输出到 `report/logs/album_api_日期.log` |
| `common/assert_handler.py` | 软断言。一条用例里的多个检查点全部执行完再统一抛错 |
| `config/env.yaml` | local / ci 两套地址，外加 Mock 账号与签名密钥 |
| `data/album_data.yaml` | 创建文件夹与上传图片的用例参数、预期业务码和提示 |
| `testcases/conftest.py` | `client` fixture（session 级）、`prepared_env` fixture（复位数据并预置） |
| `testcases/test_album.py` | 只做三件事：读数据、调 api 层、写断言 |
| `mock_server/app.py` | 被测服务，8 个业务接口 + `/health` + `/__admin/reset` |
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

# 只跑某个场景
pytest testcases/test_album.py -k 重命名
```

正常输出结尾：

```
============================= 20 passed in 0.52s ==============================
```

服务单独起的时候，先确认它活着：

```powershell
curl http://127.0.0.1:9000/health
# {"service":"mock-album-api","sign_check":false,"status":"ok"}
```

## 一次请求的调用链

以「上传图片」为例：

```
testcases/test_album.py::test_upload_image
  → api/album_api.py::AlbumApi.upload(folder_id, img_name, size_kb)   拼 payload
  → common/request_handler.py::RequestHandler.send()                   算 X-Sign、带 Authorization、发请求、记日志
  → mock_server/app.py::album_upload()                                 校验相册归属、扩展名、大小，写内存状态
  → 返回 {"code":200,"data":{"img_id":2002,...}}
  → common/assert_handler.py::AssertHandler                            记录每个检查点，最后统一抛错
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
| `timeout` | 请求超时（秒） | 传进 `requests` |
| `sign_key` | 签名密钥 | 必须与服务端 `SIGN_KEY` 一致 |
| `account` | 登录账号 | Mock 服务的固定账号，不是真实凭据 |

生效顺序：`BASE_URL` / `ENV` 环境变量 → `config/env_local.yaml` → `config/env.yaml`。
`env_local.yaml` 用同样的结构，只写要覆盖的字段（`deep_merge` 递归合并，不需要写全）。

```yaml
# config/env_local.yaml 示例（被 .gitignore 排除，不会进仓库）
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

账号也可以用 `SDK_USER` / `SDK_PWD` 覆盖，适合流水线按环境注入不同账号。

## 覆盖的接口

| 模块 | 方法 | 路径 | 主要校验 |
| --- | --- | --- | --- |
| 登录 | POST | `/user/login` | 用户名空 → 400；密码错 → 401 |
| 文件夹 | POST | `/album/folder/create` | 名称空、只有空格、超过 20 字、重名 409、排序值 0-100 |
| 文件夹 | GET | `/album/folder/list` | 返回 `total` 与 `list`，每项带 `image_count`，按 `sort` 排序 |
| 文件夹 | POST | `/album/folder/rename` | 相册不存在 404；重名 409 |
| 文件夹 | DELETE | `/album/folder/delete` | 不存在 404；相册内仍有图片 409 |
| 图片 | POST | `/album/upload` | 相册越权 403；名称空 400；扩展名白名单；大小上限 5120KB |
| 图片 | GET | `/album/image/list` | 相册不存在 403；返回 `total` 与 `list` |
| 图片 | DELETE | `/album/delete` | 不存在或已删除 400 |

业务码约定：HTTP 状态码统一 200，响应体 `code` 区分结果
（200 成功 / 400 参数非法 / 401 未登录或签名错误 / 403 越权 / 404 不存在 / 409 重复或状态冲突）。

## 用例清单

| 用例 | 条数 | 覆盖点 |
| --- | --- | --- |
| `test_create_folder` | 6 | 正常创建、名空、只有空格、26 字超限、重名 409、排序越界 |
| `test_list_folders` | 1 | 总数与列表长度一致、含图片数量、新建项可见 |
| `test_rename_folder` | 1 | 改名成功、列表中新名生效、旧名消失 |
| `test_rename_folder_not_exist` | 1 | 404 |
| `test_rename_folder_duplicate` | 1 | 409 |
| `test_delete_empty_folder` | 1 | 删除成功、列表移除 |
| `test_delete_folder_with_images` | 1 | 相册仍有图片 → 409 |
| `test_upload_image` | 5 | 正常、越权 403、名空、格式非白名单、超 5MB |
| `test_list_images` | 1 | 总数一致、刚上传的图片可见 |
| `test_list_images_folder_not_exist` | 1 | 403 |
| `test_delete_image` | 1 | 删除成功 + 重复删除 400 |

## 新增一条用例

### 只加场景，不改逻辑

在 `data/album_data.yaml` 对应接口下加一项，代码不动：

```yaml
# data/album_data.yaml
create_folder:
  uri: "/album/folder/create"
  method: "POST"
  cases:
    - case_name: "名称含 emoji-正常创建"
      json:
        name: "旅行📷"
        sort: 2
      expect:
        code: 200
```

```powershell
pytest testcases/test_album.py -k "emoji"
```

`expect.msg` 可选，写了就检查提示文案是否包含该关键字，不写只比业务码。

### 加一个新接口

四步：

1. `mock_server/app.py` 加路由和校验逻辑，并加进 `STATE` 与 `/__admin/reset`。
2. `api/album_api.py` 加方法，只拼参数：

```python
def move_image(self, img_id: int, folder_id: int):
    return self.client.post("/album/move", json={"img_id": img_id, "folder_id": folder_id})
```

3. `data/` 里加 `uri` + `method` + `cases`（如果需要参数化）。
4. `testcases/` 里加用例，断言写完整（成功校验返回字段，失败校验业务码和提示）。

需要新的校验维度（响应头、落库、并发）时，才动 `testcases` 里的断言代码。

### 断言怎么写

`AssertHandler` 是软断言：一条用例里多个检查点都会执行，最后统一抛错，失败信息汇总在一条消息里。

```python
a = AssertHandler()
a.eq(body["code"], case["expect"]["code"], "业务码")
a.contains(body["msg"], "不能为空", "错误提示")
a.not_none(body["data"]["folder_id"], "返回 folder_id")
a.gt(body["data"]["total"], 0, "总数")
a.finish()
```

`finish()` 必须调用，否则失败不会抛出。

## 关于签名

请求头带 `X-Sign`，客户端和服务端各实现一次，必须一致：

```
sign = MD5( METHOD + path + 按键排序的 "k=v" 拼接 + "&key=" + sign_key )
```

- 客户端：`common/request_handler.py::make_sign()`
- 服务端：`mock_server/app.py::make_sign()`

服务端由环境变量 `SIGN_CHECK` 控制是否强制校验，默认 `false`。本地默认关掉，排查用例失败时不必先怀疑签名；
要验证签名链路时打开：

```powershell
$env:SIGN_CHECK = "true"; python mock_server/app.py
```

打开后如果两端 `sign_key` 不一致，所有请求会返回 401「签名校验失败」。

## 测试数据与状态

服务端在内存里维护 `folders`、`images` 和两个递增序号：

| 计数器 | 起始值 | 第一个成功创建得到的 ID |
| --- | --- | --- |
| `folder_seq` | 1000 | 1001 |
| `image_seq` | 2000 | 2001 |

`POST /__admin/reset` 把状态恢复初始值。`conftest.py` 的 `prepared_env` 在 session 开始时做三件事：

1. 调 reset 复位；
2. 登录拿 token；
3. 预置相册 1001「自动化测试相册」和图片 2001「seed.jpg」。

所以用例里的 `folder_id: 1001` 有依据，且「删除仍有图片的相册」能稳定得到 409。
用例不依赖执行顺序——单条跑、重复跑、失败重跑都不会因为数据被删而失败。

需要新依赖数据时，优先在 `prepared_env` 里加，不要在用例之间传递产出。破坏性用例（改名、删除）自己造数据。

## 报告与日志

```powershell
pytest
allure generate report/allure_raw -o report/allure_html --clean
allure open report/allure_html
```

- 控制台：每条用例的软断言明细（`[PASS]` / `[FAIL] 期望= 实际=`）
- 日志：`report/logs/album_api_YYYYMMDD.log`，含完整请求体、响应体、状态码
- Allure：按 feature/story 分组，失败用例可定位到具体断言

`report/` 整个目录在 `.gitignore` 里，不会污染仓库。

## CI

**Docker Compose**

```powershell
docker compose up -d mock-album        # 只起被测服务
docker compose run --rm api-test       # 起服务 + 跑用例
docker compose down
```

两个容器在同一 compose 网络里，用例容器的 `BASE_URL` 指向服务名 `http://mock-album:9000`，
不走 `host.docker.internal`。

**Jenkins**

`Jenkinsfile` 分四段：拉代码 → 轮询 `/health` 等服务就绪 → 装依赖 → 执行 pytest。
服务没起来直接失败，不会出现「环境没起、用例全红、以为是代码问题」。
被测服务在宿主机跑时用 `host.docker.internal:9000`，报告由 `post` 段发布 JUnit + Allure。

## 排错对照

| 现象 | 原因 | 处理 |
| --- | --- | --- |
| `ConnectionError` / `prepared_env` 里 reset 失败 | 被测服务没起 | `python mock_server/app.py`，或改用 `python run.py` |
| 所有请求 401「签名校验失败」 | `SIGN_CHECK=true` 但两端 `sign_key` 不一致 | 对齐 `config/env.yaml` 的 `sign_key` 与服务端 `SIGN_KEY` |
| 401 且反复重登 | 账号密码错 | 检查 `account`、`SDK_USER` / `SDK_PWD` |
| `ModuleNotFoundError: No module named 'api'` | 直接 `python testcases/test_xxx.py` 执行 | 用 `pytest` 从项目根目录跑，`conftest.py` 已补 `sys.path` |
| 「删除仍有图片」用例返回 200 | 预置数据没跑（相册里没有图片） | 确认 `prepared_env` 执行成功，或手动调 `/__admin/reset` 后重跑 |
| 「重名」用例失败 | 预置相册名被改过 | 预置名固定为「自动化测试相册」，改成别的名字要同步 `data/album_data.yaml` |
| `allure` 命令找不到 | 只装了 `allure-pytest`，没装命令行 | 装 allure 命令行；用例本身不受影响 |

## 已知限制

- Mock 服务状态在内存里，重启即清空；多进程并发（`pytest-xdist`）会互相覆盖状态，当前按串行设计。
- 断言用 `AssertHandler` 而不是原生 `assert`，失败信息是自定义汇总格式；IDE 无法跳转到失败行。
- 图片上传只校验名称、扩展名和大小，没有真正解析图片内容，也没有分片上传和断点续传。
- 相册列表一次返回全部，没有实现分页。
