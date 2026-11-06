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

摄像头实时采集、视觉理解尚未实现。前端已接入 Live2D 模型加载与动作、表情预览；已附带 Bina 自动绑定初版模型；Cubism Core 需另行安装，对话自动驱动和语音口型尚未接入。已有模块的实际运行需要对应模型服务和本地配置。

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

需要 Python 3.13、Node.js。先填写 `.env` 并启动记忆服务。

```bash
docker compose up -d hindsight
```

单独运行后端时使用 `AX_HINDSIGHT_URL=http://127.0.0.1:8888`，已部署远程服务可设置 `AX_HINDSIGHT_API_KEY`。安装并启动后端。

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

在另一个终端启动前端。

```bash
cd frontend
npm ci
npm run dev
```

打开 `http://127.0.0.1:3000/solo`。主界面以 Bina 形象为中心，下方提供最近对白、文字、附件和语音输入；聊天记录通过抽屉查看。右侧可收起的侧栏提供交互状态、人物缩放、暖光/夜色背景、字幕与 Enter 发送设置。默认加载 `frontend/public/live2d/bina/bina.model3.json`，包含待机、眨眼、点头、摇头和表情预览；可编辑工程与制作流程见 [Bina 模型资源](assets/bina-live2d/README.md)。模型加载失败或手动切回立绘时使用 `frontend/public/bina/casual.jpeg`；「形象」页签支持加载 Live2D 模型，并预览模型提供的动作与表情。渲染使用 PixiJS 8 和 `untitled-pixi-live2d-engine`，仅在浏览器端按需加载，模型路径保存在当前浏览器。Core 与模型安装步骤见 [Live2D 资源说明](frontend/public/live2d/README.md)。侧栏「设置」可选择回复模型与思考档位（默认、关闭、低、高、最高），浏览器会保存选择，并从下一轮聊天生效。可用模型由 `/api/v1/chat/options` 返回；当前 DeepSeek 支持 Flash、Pro 和环境变量配置的默认模型，其他服务沿用配置模型。选择仅影响 Bina 的回复，不更改 Hindsight 记忆模型。

Linux/WSL 也可在启动 Hindsight 后使用 `bash start.sh` 与 `bash stop.sh` 启停前后端。出图配置见 `docs/Bina_Image_Gen.md`；Live2D 架构、资源安装与验收步骤见 [Bina Live2D 接入](docs/Bina_Live2D.md)。

## 检查

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

Python 依赖见 `requirements.txt`，前端依赖与锁文件位于 `frontend/`。前端已配置 ESLint，后端尚未统一配置格式化和 lint。

## 文档约定

针对脸部拼接失真，新分层材料及对比图见 [Bina 原图坐标分层](assets/bina-live2d/source-registered/README.md)。Windows 下运行 `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/prepare_bina_registered.ps1` 可复现 24 个 PNG 部件、Layout 和像素校验，依赖系统自带 .NET System.Drawing。此批材料已检查静态还原，尚待绑定及动态验收。

本轮完成项、验证范围和后续绑定工作见 [2026-11-06 Live2D 素材返工进度](docs/Bina_Live2D_Progress_2026-11-06.md)。

Live2D 的内置模型已调整五官与部件布局，并增加运行时动作幅度校正。六张原始 T 姿图的比例测量与复现命令见 [T 姿参考说明](assets/bina-tpose/README.md)；测量结果尚未用于按全身比例重建模型，正式模型验收仍待完成。

当前开发计划见 `TODO.md`。历史多 Agent 介绍见 `docs/历史项目说明.md`，旧内阁、软件工程流水线和角色扩展文档用于追溯。新功能与设计以 Bina 的虚拟具身、互动和记忆目标为准。
