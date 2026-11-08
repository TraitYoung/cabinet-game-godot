# 可维护性整改解决汇报 · 2026-11-08

对应[可维护性检查 M01–M10](2026-11-08-maintainability.md)。十项均已完成实现和相应验证。项目继续只运行 Bina，长期记忆仍仅由 Hindsight 提供。

## 逐项结果

| 编号 | 解决结果 | 主要实现 | 验证证据 |
| --- | --- | --- | --- |
| M01 | Linux、Windows、PowerShell 和 WSL 入口共用进程归属策略 | [processes.py](../../infrastructure/processes.py)、[启动器](../../launcher/stack.py)、[PowerShell 入口](../../scripts/dev_stack.ps1) | 真实 Linux 与 Windows 临时进程验收，覆盖旧记录、PID 复用、同名其他进程、子进程和孤儿进程；Windows PowerShell 5.1 解析通过 |
| M02 | 主动消息与用户回合共享会话锁；保存失败不通知 | [ProactiveAgent](../../agents/proactive.py)、[commit_notice](../../modules/chat_api/service.py) | 忙会话拒绝生成；成功提交后才通知；失败不发送；来源为 `proactive`，不将系统标记作为用户事实写入 Hindsight |
| M03 | 所有入口使用一个异步回合协调器，取消中的 SQLite 操作离开事件循环 | [aexecute](../../modules/chat_api/service.py)、[HTTP 适配](../../modules/chat_api/routes.py) | JSON/SSE/适配器取消回归；数据库持锁时心跳仍运行；取消存储异常不替换原取消异常；历史和导出使用同步路由线程 |
| M04 | 集中连接和迁移，定义请求状态及版本化结果格式 | [database.py](../../storage/database.py)、[turns.py](../../schemas/turns.py)、[请求存储](../../storage/turn_requests.py) | 旧表重复迁移、附加可空列、旧结果格式、未知版本拒绝及事务回滚通过；请求结果使用显式字段和 `version=1` |
| M05 | 拆分前端异步生命周期和侧栏展示 | [回合状态机](../../frontend/src/modules/solo-chat/turnLifecycle.ts)、[hooks](../../frontend/src/modules/solo-chat/)、[BinaControls](../../frontend/src/modules/solo-chat/BinaControls.tsx) | 14 项前端单测、13 项独立浏览器场景；覆盖成功、取消、提交中、已完成恢复、状态未知、超时、附件切换和卸载 |
| M06 | 工厂创建独立应用和依赖，不再返回同一个全局 app | [factory.py](../../app/factory.py)、[Container](../../infrastructure/container.py)、[入口](../../main.py) | 两个应用使用相同会话/请求 ID，模型、历史、情绪和在场状态仍隔离；导入不读取或校验真实配置，不启动任务 |
| M07 | 共用 JSON 代理和浏览器错误读取 | [proxy.ts](../../frontend/src/infra/proxy.ts)、[http.ts](../../frontend/src/matrix/http.ts) | 直接测试代理：保留 400/409/422/503、透传 limit/身份/正文、区分网络/超时/取消与无效响应；界面不显示原始 JSON 包装 |
| M08 | 运行配置通过统一 Settings 快照解析、校验和注入 | [settings.py](../../config/settings.py)、[Container](../../infrastructure/container.py) | 多套配置隔离、布尔值、数值边界、旧 LLM 别名、base URL 规范化和密钥隐藏通过；核心服务不再自行读取进程环境 |
| M09 | 共享回合协议，修正当前接口描述，收敛注册表用途 | [turns.py](../../schemas/turns.py)、[路由](../../modules/chat_api/routes.py)、[兼容注册表](../../app/registry.py) | OpenAPI 不再宣称内阁路由或多人物能力；历史字段仍接受但始终回复 Bina，开发流水线仍返回 410；注册表不参与当前 HTTP 装配 |
| M10 | 提供固定开发工具、统一门禁及 CI；拆除测试间的全局清理和场景依赖 | [质量命令](../../scripts/check_quality.sh)、[pyproject](../../pyproject.toml)、[CI](../../.github/workflows/quality.yml) | Ruff、mypy、55 项 Python 单测、14 项 Node 单测、前端 lint/类型/生产构建通过；浏览器用例可通过 `--case` 独立运行 |

## 实现边界

- 取消与本地提交的原有事务边界保留：生成阶段可取消；进入提交阶段后继续完成或沿用请求 ID 恢复。外部模型线程仍可能等待返回，但不再让同步数据库等待阻塞事件循环。
- 主动消息在持有会话锁后才生成和保存，记录明确来源。它不构造一条虚假的用户事实写入 Hindsight；用户后续回应仍走正常长期记忆流程。
- `Settings.load()` 只在应用启动或首次使用时读取配置；导入模块不读取本地秘密配置。模型、情绪、记忆、上传、转写、搜索、出图与风格参数使用同一应用的快照，修改需重启。
- 数据库升级自动且幂等，保留原始聊天；来源列兼容旧 `[proactive]` 记录。SQL 使用显式列名，额外可空列不会破坏请求插入。
- 旧端口、整数 PID、旧版 JSON 记录不再授权终止进程。手动启动的服务应在所属终端管理；`-ForceKillPort` 会明确拒绝。Windows 前端在 WSL 中使用项目虚拟环境的进程管理入口。
- 依赖注入只围绕当前应用服务，没有引入大型框架；旧 registry/ports 仅保留外部适配器兼容。

## 验证清单

| 检查 | 结果 |
| --- | --- |
| `bash scripts/check_quality.sh` | 通过：Ruff lint/格式、mypy 渐进检查、Linux 真实进程策略、55 项 Python 单测、Shell 语法、前端 lint/类型、14 项 Node 单测、生产构建 |
| `scripts/check_frontend_interactions.py` | 13 个独立 Chromium 场景通过；`test_timeout`、`test_stop_completed` 另行单独通过 |
| `scripts/check_process_ownership.py` | Linux 与真实 Windows Python 均通过；Windows 同时验证 PowerShell 入口可解析 |
| `scripts/check_container_persistence.py --image ghcr.io/vectorize-io/hindsight:1.2.0` | 独立测试卷验证集中迁移后的聊天与情绪数据跨容器保留；使用缓存镜像，不等同于完整 API 镜像部署 |
| 文档链接与 `git diff --check` | 已核对，无缺失本地目标与空白错误 |

## 检查范围与限制

Python 类型检查按 `pyproject.toml` 渐进覆盖配置、回合协议和数据库基础模块；未宣称全仓库已达到严格类型检查。CI 已配置 Linux 完整检查及 Windows 进程策略任务，本次证明来自本机执行，尚未在远端 GitHub Actions 运行。

模型回复与记忆语义回归使用模拟服务和临时数据库，没有进行真实外部模型或真实 Hindsight bank 的语义验收。Windows 已验证进程策略和 PowerShell 解析，未进行 GUI、模型服务和所有 Windows 启动场景的完整端到端验收。

本次临时前端在验证后停止。代码、回归检查与文档作为同一次交付提交到仓库；GitHub Actions 的运行结果以远端检查为准，本记录列出本机验收证据。此次交付不发布或部署服务。
