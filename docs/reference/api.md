# HTTP API 参考

本机后端默认地址为 `http://127.0.0.1:8000`。运行后可在 `/docs` 查看 FastAPI 生成的完整字段定义，或读取 `/openapi.json`。路由实现见 [modules/chat_api/routes.py](../../modules/chat_api/routes.py) 与[人物目录接口](../../modules/personas/routes.py)。

## 身份与请求标识

| 字段 | 作用 |
| --- | --- |
| `x-session-id` 请求头 | 选择一段聊天及其原始历史；聊天接口缺省生成新 ID |
| `x-memory-thread` 请求头 | 稳定用户记忆身份；缺省取 `AX_MEMORY_USER_ID` 或本地默认身份 |
| `x-trace-id` 请求头 | 可选追踪 ID；缺省由后端生成 |
| `request_id` 请求正文字段 | JSON/SSE 聊天的幂等 ID；重试同一回合时沿用 |
| `x-request-id` 请求头 | OpenAI 兼容聊天的幂等 ID |

会话 ID 和记忆身份是数据选择参数，不是认证凭据。默认部署仅供本机单用户使用。

## 接口目录

| 方法 | 路径 | 用途 |
| --- | --- | --- |
| GET | `/api/v1/health` | 轻量探活及当前模型配置；不调用模型，也不保证 Hindsight 健康 |
| GET | `/api/v1/chat/options` | 当前模型及思考档位选项 |
| POST | `/api/v1/chat` | 完成一个回合，返回回复、意图和追踪 |
| POST | `/api/v1/chat/stream` | 同一回合流程，完成后以 SSE 分块返回 |
| GET | `/api/v1/chat/requests/{request_id}` | 查询回合状态与已生成结果；需 `x-session-id` |
| POST | `/api/v1/chat/requests/{request_id}/cancel` | 尝试取消生成；需 `x-session-id` |
| GET | `/api/v1/chat/history` | 读取会话原始历史；需 `x-session-id` |
| POST | `/api/v1/chat/export` | 导出会话历史到 `output/chats/` |
| POST / GET | `/api/v1/presence` | 上报或读取当前在场会话 |
| GET | `/api/v1/proactive/pending` | 读取待处理主动消息，并标记为已消费 |
| POST | `/api/v1/attachments/ingest` | multipart `file`：提取文本或描述图片 |
| POST | `/api/v1/stt` | multipart `audio`：语音转写 |
| GET | `/api/v1/personas` | 当前人物目录，只发布 Bina |
| GET | `/api/v1/personas/{persona_id}` | 读取人物卡 |
| GET | `/api/v1/images/persona/{persona_id}` | 读取出图外貌配置 |
| POST | `/api/v1/images/generate` | 生成 Bina 图片；需配置模型服务 |
| GET | `/api/v1/images/file/{file_name}` | 读取已生成图片 |
| GET | `/v1/models` | OpenAI 兼容模型目录，只发布 `axiodrasil-bina` |
| POST | `/v1/chat/completions` | OpenAI 兼容聊天，仍执行 Bina 和 Hindsight 流程 |

## 聊天示例

下列请求会真实调用配置的模型和 Hindsight，并保存对话；离线回归命令见[开发与检查](../guides/development.md)。

```bash
curl -sS http://127.0.0.1:8000/api/v1/chat \
  -H 'Content-Type: application/json' \
  -H 'x-session-id: example-conversation' \
  -H 'x-memory-thread: example-user' \
  -d '{"text":"你好，Bina","request_id":"example-turn-001","strip_persona_prefix":true}'
```

`text` 长度为 1–12000 字符。可选 `model` 与 `reasoning_effort` 必须使用 `/api/v1/chat/options` 返回的值。`reasoning_effort` 可表示为 `off`、`low`、`high` 或 `max`，可用范围随后端配置变化。

`workflow_mode=dev_pipeline` 返回 410；`forced_persona`、`group_mode` 等字段为历史兼容字段，不恢复其他人物或群聊运行。

响应中的 `code` 提供稳定错误类别，`detail` 保留兼容的文字或验证信息。前端代理透传 `limit` 与后端状态码；网络不可达为 503，代理超时为 504。

## 回合状态与错误

状态包括 `generating`、`cancelled`、`failed`、`committing` 与 `completed`。取消成功后不会保存此回合的聊天和长期记忆；进入提交阶段后取消返回当前状态，提交继续。详细事务边界与恢复方式见[记忆与回合生命周期](memory.md)。

| 情况 | 行为 |
| --- | --- |
| 会话已有回合运行 | HTTP 409，避免基于旧历史生成 |
| 同一请求 ID 更换内容或记忆身份 | HTTP 409 |
| 请求已取消 | HTTP 409，不重新生成 |
| 模型选项无效 | HTTP 422 |
| 模型失败或回复为空 | HTTP 502，不保存成功回合 |
| Hindsight 召回失败 | HTTP 503，不进入生成 |
| Hindsight 写入失败 | HTTP 503，本地回合已保存；使用同一请求 ID 继续提交 |

SSE 在流已建立后以 `type=error` 事件报告失败，失败时不发 `done`。成功时先返回元信息，再发送 `delta` 和 `done`。

## OpenAI 兼容接入

客户端 Base URL 设置为 `http://127.0.0.1:8000/v1`，模型为 `axiodrasil-bina`。建议明确传入 `x-session-id`、`x-memory-thread` 和每轮唯一的 `x-request-id`。兼容接口使用最后一条非空用户消息；此前对话由服务端历史和 Hindsight 提供，不能将传入的整份 `messages` 列表视为唯一上下文来源。

旧 SillyTavern 群聊教程已移入[历史归档](../archive/SillyTavern_Integration.md)。
