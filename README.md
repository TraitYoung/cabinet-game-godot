# Axiodrasil · Bina 虚拟具身实验

Axiodrasil 是一个虚拟具身实验项目。当前唯一运行人物是 Bina，开发集中于她的虚拟形象、与用户的互动，以及支撑持续互动的记忆系统。

最终目标是让 Bina 在虚拟形象中获得持续的存在感，能够访问用户授权的摄像头，感知用户与环境，并结合对话和记忆与用户互动。

## 当前范围

- Bina 是唯一运行人物，所有聊天请求统一交给 Bina。
- 其他人物退化为文档设定，保存在 `docs/characters/`，旧 BIOS 和内阁设计属于历史资料。
- 当前攻坚虚拟形象的一致性、自然互动、主动互动，以及会话与长期记忆的连续性。
- 摄像头访问、视觉理解、视觉事件与记忆联动属于待实现目标。目前的自拍出图功能用于生成 Bina 的图片。

## 已有基础

| 方向 | 当前实现 |
|---|---|
| 聊天 | Bina 单聊界面、流式接口、单聊快速路径 |
| 输入 | 文字、附件、浏览器听写和服务端语音转写 |
| 虚拟形象 | Bina 统一外貌配置、ComfyUI 与 LoRA 定妆出图 |
| 互动状态 | 情绪状态、用户在场状态、主动消息机制 |
| 记忆 | SQLite 原始聊天记录；Hindsight 长期事实、偏好、更正与共同经历 |

摄像头实时采集、视觉理解尚未实现。前端已接入 Live2D 模型加载与动作、表情预览；已附带 Bina 自然站姿新版模型（T 姿参考生成身体，保留原图头部分层）；Cubism Core 需另行安装，对话自动驱动和语音口型尚未接入。已有模块的实际运行需要对应模型服务和本地配置。

## 技术与目录

后端使用 Python、FastAPI、LangGraph 和 Pydantic，前端使用 Next.js、React 和 TypeScript。SQLite 保存原始聊天记录和互动状态，Hindsight 保存长期记忆。聊天模型可通过环境变量选择 DeepSeek 或 Qwen。

| 路径 | 职责 |
|---|---|
| `main.py` | HTTP、流式聊天、附件和语音等接口 |
| `agents/` | Bina 对话图、快速路径和主动互动 |
| `frontend/src/modules/solo-chat/` | Bina 交互界面 |
| `frontend/src/modules/embodiment/` | Live2D 画布、模型加载与资源释放 |
| `modules/` | 聊天服务、角色目录、附件、语音与出图 |
| `memory/` | Hindsight 长期记忆适配和上下文拼装 |
| `storage/` | 本地原始聊天记录 |
| `state/` | 情绪状态 |
| `config/persona_visual/bina.json` | Bina 外貌配置真相源 |
| `assets/bina-tpose/` | Bina 日常装、工作装三视图原图与人工标点测量 |
| `assets/bina-live2d/` | Live2D 分件、可编辑工程、导出记录与页面截图 |
| `test_suite/` | 脚本化回归检查，部分历史测试属于旧内阁阶段 |
| `docs/characters/` | 已退役人物的文档设定 |

旧群聊、演示台和内阁记忆实现已删除。OpenAI 兼容模型目录仅发布 `axiodrasil-bina`。旧角色参数统一收敛为 Bina，开发流水线返回已归档状态。

## 联网搜索

`.env` 中设置 `AX_SEARCH_ENABLED=1`，Bina 会在用户要求搜索、核实或需要实时信息时调用 DeepSeek 官方 Search API，普通闲聊可直接回复。复用 `DEEPSEEK_API_KEY` 和 `DEEPSEEK_BASE_URL`，无须新密钥；设置 `AX_SEARCH_ENABLED=0` 关闭。修改配置后重启后端。

搜索使用 `POST /v1/tools/search`，每次取 5 条结果及摘要，每轮最多 3 次搜索。资料作为工具结果参与当前回复，思考模式保留 `reasoning_content`；回答中的来源链接可在对白和历史记录中打开。搜索失败会明确反馈给模型，不能作为成功检索处理。此功能不更改 Hindsight 配置。

接口参数与按成功请求计费规则见 [DeepSeek Search & Fetch 官方文档](https://api-docs.deepseek.com/guides/search/)。离线验证：`python -m unittest test_suite.test_web_search -v`。

## Hindsight 本机部署

复制 `.env.example` 为 `.env`，填写 `DEEPSEEK_API_KEY`。本机 Compose 使用 Hindsight 1.2.0，复用该密钥，向量与重排使用本地多语言模型。

```bash
docker compose up -d
```

Bina 后端为 `http://127.0.0.1:8000`，Hindsight API 为 `http://127.0.0.1:8888`，记忆管理界面为 `http://127.0.0.1:9999`。第一次启动需要下载镜像、模型及 Python 依赖，可查看启动状态。

```bash
docker compose ps
docker compose logs -f api
```

记忆和模型缓存使用 `hindsight-data`、`hindsight-models` 命名卷。常规 `docker compose down` 保留数据，`down -v` 会删除这些卷。

### 记忆身份与写入时序

浏览器沿用已有稳定的 `x-memory-thread`，新建聊天仅改变 `x-session-id`。直接调用 API 时，缺省使用 `.env` 的 `AX_MEMORY_USER_ID`，适用于当前本地单用户模式。不同记忆身份使用独立的 Hindsight bank。

每轮回复前，Hindsight 的 `reflect` 内部召回并解析当前事实、旧事实与经历，再把结果交给 Bina。原始聊天记录写入轻量 SQLite 聊天记录表。回复完成后同步调用 `retain`，等待事实提取结束才返回成功或 SSE `done`，保证紧接着新建会话时可以读取刚写入的记忆。这样会增加每轮请求的等待时间与模型调用量。

长期记忆服务不可用时返回明确的错误，写入失败时本地仍保留聊天记录。旧的 L3、向量、FTS5、内阁记忆、Redis 缓存和滚动摘要代码已移除。SQLite 聊天记录继续兼容已有 `chat_turns` 表。

### 真实验收

以下脚本通过真实聊天接口调用 Bina 和 Hindsight，逐项检查跨会话偏好、事实更正、共同经历。每个请求都使用新的会话 ID，整轮测试使用独立记忆身份。测试记忆保留在独立 bank 中供管理界面检查。

```bash
docker compose exec api python scripts/check_hindsight_memory.py
```

## 本地开发

需要 Python 3.13、Node.js 20.9 以上版本和可用的 Docker Compose。WSL 内使用 Linux 版 Python、Node.js 和 npm。

Debian 13 可先安装系统依赖，再运行环境初始化脚本。脚本创建 `.venv`、安装 Python 依赖、按锁文件安装前端依赖，并在配置不存在时创建 `.env` 和 `frontend/.env.local`，不会覆盖已有配置。

```bash
sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-pip python3-dev build-essential nodejs npm curl ca-certificates
bash scripts/setup_linux_env.sh
```

Hindsight 需要运行中的 Docker 引擎。使用 Docker Desktop 时启动它并启用当前 WSL 发行版的集成；也可在 Debian 内安装原生 Docker：

```bash
sudo apt-get install -y docker.io docker-compose
sudo systemctl enable --now docker
sudo docker compose up -d hindsight
```

普通用户没有 Docker socket 权限时，Docker 命令加 `sudo`。使用本机后端时，`.env` 设置 `AX_HINDSIGHT_URL=http://127.0.0.1:8888`。真实密钥只写入 `.env`。先填写配置并启动记忆服务。

```bash
docker compose up -d hindsight
```

单独运行后端时使用 `AX_HINDSIGHT_URL=http://127.0.0.1:8888`，已部署远程服务可设置 `AX_HINDSIGHT_API_KEY`。安装并启动后端。

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.lock.txt
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

在另一个终端启动前端。

```bash
cd frontend
npm ci
npm run dev
```

打开 `http://127.0.0.1:3000/solo`。主界面以 Bina 形象为中心，下方提供最近对白、文字、附件和语音输入；聊天记录通过抽屉查看。右侧可收起的侧栏提供交互状态、人物缩放、暖光/夜色背景、字幕与 Enter 发送设置。默认加载 `frontend/public/live2d/bina-registered/bina.model3.json`，包含待机、眨眼、点头、摇头和表情预览；可编辑工程与制作流程见 [Bina 模型资源](assets/bina-live2d/README.md)。模型加载失败或手动切回立绘时使用 `frontend/public/bina/casual.jpeg`；「形象」页签支持加载 Live2D 模型，并预览模型提供的动作与表情。渲染使用 PixiJS 8 和 `untitled-pixi-live2d-engine`，仅在浏览器端按需加载，模型路径保存在当前浏览器。Core 与模型安装步骤见 [Live2D 资源说明](frontend/public/live2d/README.md)。侧栏「设置」可选择回复模型与思考档位（默认、关闭、低、高、最高），浏览器会保存选择，并从下一轮聊天生效。可用模型由 `/api/v1/chat/options` 返回；当前 DeepSeek 支持 Flash、Pro 和环境变量配置的默认模型，其他服务沿用配置模型。选择仅影响 Bina 的回复，不更改 Hindsight 记忆模型。

Linux/WSL 也可在启动 Hindsight 后使用 `bash start.sh` 与 `bash stop.sh` 启停前后端。出图配置见 `docs/Bina_Image_Gen.md`；Live2D 架构、资源安装与验收步骤见 [Bina Live2D 接入](docs/Bina_Live2D.md)。

Linux 启动脚本优先使用终端中的 `AX_DB_PATH`，其次读取 `.env` 中的路径，均未设置时使用 `~/.axiodrasil/axiodrasil_core.db`。原生 Docker 的 socket 权限不足时，脚本会通过 `sudo` 执行 Compose，可能提示输入本机密码。

## 检查

两套 Live2D 已完成一轮[脸部接缝返工](assets/bina-live2d/face-revision/README.md)，连续头部底图替代矩形切块，日常装重新绑定眨眼，并补齐颈部遮挡。新版可编辑工程、原图与补画、动作近景和重建脚本均已保存；头发目前共享头部变形，独立发丝物理与虹膜追踪尚未重做。

网页侧栏“形象”中可切换日常装和工装 Live2D，选择在刷新后保留。[工装版说明](assets/bina-live2d/source-work/README.md)包含母图、实际提示词、14 层 Layout、可编辑工程和重建命令。启动前端并安装 Playwright Chromium 后，运行 `PLAYWRIGHT_BROWSERS_PATH="$PWD/.devstack/playwright-current" .venv/bin/python scripts/check_bina_outfits.py` 检查两套服装切换、动作表情与手机显示；浏览器缓存路径按本机安装位置调整。

离线回归使用官方客户端类型及模拟响应，不调用外部模型。真实语义验收使用上面的脚本。

```bash
python -m unittest discover -s test_suite -v
PYTHONPATH=. python test_suite/test_solo_fast.py
PYTHONPATH=. python test_suite/test_bina_first.py
```

使用 Docker 时可以通过 `docker compose exec api` 执行上述 Python 命令。

```bash
cd frontend
npm run lint
npm run build
```

前端交互回归使用 Playwright Chromium 和模拟聊天、历史与麦克风，不调用外部模型。先启动前端，再在项目根目录运行：

```bash
PLAYWRIGHT_BROWSERS_PATH="$PWD/.devstack/playwright" .venv/bin/python scripts/check_frontend_interactions.py --base-url http://127.0.0.1:3000
```

检查覆盖切换会话时的过期历史、发送期间的历史刷新、取消录音、正常转写及取消转写后的迟到结果。Chromium 安装步骤见下文。

Python 直接依赖见 `requirements.txt`，已验证的 Python 3.13 完整版本锁定在 `requirements.lock.txt`（含 Live2D 素材工具的 Pillow）。更新依赖后运行检查，再用 `python -m pip freeze > requirements.lock.txt` 更新锁文件。前端依赖与锁文件位于 `frontend/`。前端已配置 ESLint，后端尚未统一配置格式化和 lint。

浏览器验证和 PDF 工具还需要 Playwright Chromium。Linux 首次安装时补齐系统库：

```bash
source .venv/bin/activate
sudo .venv/bin/python -m playwright install-deps chromium
export PLAYWRIGHT_BROWSERS_PATH="$PWD/.devstack/playwright"
python -m playwright install chromium
```

后续运行 Playwright 工具时沿用该 `PLAYWRIGHT_BROWSERS_PATH`。Bina Live2D 还需要本地 Cubism Core；安装位置与授权说明见 `frontend/public/live2d/README.md`。

前端将 TypeScript ESLint 的间接依赖 `minimatch` 固定为 `11.0.5`，修复 [GHSA-g3hv-75wg-m249](https://github.com/advisories/GHSA-g3hv-75wg-m249)。更新 TypeScript ESLint 后，可在确认其自带安全版本时移除 `package.json` 中的定向 override；不要通过降级 Next.js 处理审计提示。

## 文档约定

从 T-pose 绘制、原图比例测量、完整头部候选与原位分层，到参考生成自然站姿身体、Live2D 组装和浏览器验收，见 [Bina 完整制作流程](docs/Bina_Live2D_Workflow.md)。可复用 skill 位于 [skills/reference-to-live2d](skills/reference-to-live2d/SKILL.md)，安装到本机 skills 目录后使用 `$reference-to-live2d` 调用。

针对脸部拼接失真，新分层材料及对比图见 [Bina 原图坐标分层](assets/bina-live2d/source-registered/README.md)。Windows 下运行 `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/prepare_bina_registered.ps1` 可复现 24 个 PNG 部件、Layout 和像素校验，依赖系统自带 .NET System.Drawing。原图头部分层与新生成的自然站姿身体已合并到当前模型，见 [站姿素材与制作记录](assets/bina-live2d/source-standing/README.md)。

本轮完成项、验证范围和后续绑定工作见 [2026-11-06 Live2D 素材返工进度](docs/Bina_Live2D_Progress_2026-11-06.md)。

Live2D 的内置模型已调整五官与部件布局，并增加运行时动作幅度校正。六张原始 T 姿图的比例测量与复现命令见 [T 姿参考说明](assets/bina-tpose/README.md)；测量结果尚未用于按全身比例重建模型，正式模型验收仍待完成。

当前开发计划见 `TODO.md`。历史多 Agent 介绍见 `docs/历史项目说明.md`，旧内阁、软件工程流水线和角色扩展文档用于追溯。新功能与设计以 Bina 的虚拟具身、互动和记忆目标为准。
