# 当前架构

本文对应 Bina 单人物实现。安装与启动见[项目 README](../../README.md)，未来任务见 [TODO](../../TODO.md)。

## 模块职责

| 路径 | 当前职责 |
| --- | --- |
| [main.py](../../main.py)、[app/factory.py](../../app/factory.py) | 入口、隔离应用装配、生命周期 |
| [modules/chat_api/routes.py](../../modules/chat_api/routes.py) | HTTP 请求与响应适配 |
| [config/settings.py](../../config/settings.py) | 启动配置快照与校验 |
| [modules/chat_api/service.py](../../modules/chat_api/service.py) | 统一回合入口、模型选项校验、上下文读取、生成与提交 |
| [agents/router.py](../../agents/router.py) | `solo_fast → bina → END`：交互状态与 Bina 回复 |
| [agents/proactive.py](../../agents/proactive.py) | 用户在场状态、空闲心跳和主动消息 |
| [infrastructure/container.py](../../infrastructure/container.py) | 环境配置、模型、聊天记录与情绪引擎实例 |
| [storage/chat_history.py](../../storage/chat_history.py) | SQLite 原始聊天记录及近期对话预算 |
| [storage/turn_requests.py](../../storage/turn_requests.py) | 请求状态、幂等提交与会话锁 |
| [memory/hindsight.py](../../memory/hindsight.py) | Hindsight bank、回复前 reflect 与回复后 retain |
| [memory/context_inject.py](../../memory/context_inject.py) | 拼装长期记忆、近期对话和当前输入 |
| [state/mood_engine.py](../../state/mood_engine.py) | 情绪漂移、交互提示和原子状态更新 |
| [modules/](../../modules/) | 附件、转写、搜索、出图、人物目录和接口适配 |
| [frontend/src/modules/solo-chat/](../../frontend/src/modules/solo-chat/) | Bina 聊天、会话、附件、录音及回合停止 |
| [frontend/src/modules/embodiment/](../../frontend/src/modules/embodiment/) | Live2D 加载、画布生命周期与动作校正 |
| [frontend/src/matrix/](../../frontend/src/matrix/) | 浏览器接口类型与客户端 |
| [frontend/app/api/](../../frontend/app/api/) | 历史、人物、在场状态等 Next 服务端转发 |

`Container` 为每个应用创建模型、历史、情绪、回合服务与主动消息实例；FastAPI 从应用状态获取服务，图节点在作用域内访问同一实例。`app/registry.py` 与 `app/matrix/` 仅保留旧适配器调用兼容，不再参与 HTTP 应用装配。

## 用户回合链路

1. 浏览器在 `/solo` 提交文字与已处理的附件内容；模型和思考档位随请求传入。
2. Next 将 `/api/v1/*` 转发给 FastAPI。其他前端 Route Handler 负责历史、人物等已有入口。
3. FastAPI 解析会话和稳定记忆身份，经统一异步入口 `TurnService.aexecute`，在工作线程调用 `execute`，获取会话锁、检查请求 ID。
4. 服务读取最近五轮对话，调用 Hindsight reflect 整理相关长期记忆。
5. Bina 图计算交互状态，拼装提示词并生成回复；模型错误和空回复作为失败返回。
6. 提交事务同时保存原始聊天与生成结果，再同步写入 Hindsight；完成后返回 JSON 或 SSE。

JSON 是当前前端主路径。SSE 仍在整轮完成后切块发送，生成期间发送心跳；它不是模型 token 的实时透传。取消、提交和重试约定见[记忆与回合生命周期](memory.md)。

## 数据与资源边界

SQLite 保存原始聊天、情绪状态与回合请求元数据；Hindsight 是唯一长期记忆系统。没有运行中的 L3、FTS、向量、Redis 或滚动摘要记忆实现。

人物外貌配置以 [bina.json](../../config/persona_visual/bina.json) 为准。Live2D 原图、工程与制作记录位于 `assets/bina-live2d/`、`assets/bina-tpose/`；浏览器加载 `frontend/public/live2d/` 下的导出文件。

摄像头访问、视觉理解、对话自动驱动 Live2D 与 TTS 口型仍属后续工作。已有模型加载、动作与表情预览不表示上述能力已经实现。

## 运行边界

默认前端、后端及 Hindsight 发布端口都绑定本机回环地址；当前采用本地单用户模式，没有远程用户鉴权方案。Compose 为 API 数据库单独挂载 `api-data` 卷，Hindsight 数据和模型缓存使用各自的卷。

开发命令及回归检查见[开发与检查](../guides/development.md)。多人物与旧记忆架构保存在[历史归档](../archive/README.md)。

## 前端职责

`SoloChatView` 组合界面与交互。回合状态由 `TurnLifecycle` 和 `useChatTurn` 管理；历史、附件、外貌和回复偏好分别由 `useConversationHistory`、`useAttachments`、`useAppearance` 与 `useChatPreferences` 管理。`BinaControls` 负责侧栏展示。

Next Route Handler 共用 `frontend/src/infra/proxy.ts`；浏览器请求共用 `frontend/src/matrix/http.ts`，保留后端状态码并将 JSON 错误转换为可读提示。`/api/v1/*` 继续通过 rewrite 转发，保留 SSE 行为。
