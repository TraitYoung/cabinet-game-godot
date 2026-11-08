# Bina 项目文档

Axiodrasil 当前仅运行 Bina，开发围绕虚拟具身、互动和记忆展开。摄像头采集与视觉理解仍在计划阶段。项目范围以[根目录 README](../README.md) 和 [TODO](../TODO.md) 为准。

## 阅读入口

| 要完成的事 | 文档 |
| --- | --- |
| 安装依赖、配置环境并启动服务 | [README：本地开发](../README.md#本地开发) |
| 了解当前模块与请求链路 | [架构参考](reference/architecture.md) |
| 调用聊天、历史、取消与查询接口 | [HTTP API](reference/api.md) |
| 理解会话身份、Hindsight 和提交边界 | [记忆与回合生命周期](reference/memory.md) |
| 修改代码并验证 | [开发与检查](guides/development.md) |
| 安装或更换 Live2D 模型 | [Live2D 接入](guides/live2d.md) |
| 从参考图制作模型 | [Live2D 制作流程](guides/live2d-workflow.md) |
| 查看 Bina 视觉定稿、站姿母图与废稿归档 | [角色视觉参考图](media/README.md) · [废稿归档](media/archive/README.md) |
| 配置 ComfyUI 与 Bina 自拍 | [出图指南](guides/image-generation.md) |
| 查看近期整改证据 | [代码质量检查与修复](reviews/2026-11-06-code-quality.md) |
| 查看可维护性整改 | [问题记录](reviews/2026-11-08-maintainability.md)与[解决汇报](reviews/2026-11-08-maintainability-resolution.md) |
| 查看下一阶段任务 | [TODO](../TODO.md) |

## 目录分类

| 目录 | 放什么 | 维护方式 |
| --- | --- | --- |
| `guides/` | 为完成具体任务而写的操作步骤 | 功能或命令变化时更新 |
| `reference/` | 当前架构、接口、存储和行为约定 | 与源码同步 |
| `adr/` | 有背景、选择理由和后果的架构决策 | 记录决策状态；变更时注明替代关系 |
| `reviews/` | 带日期的检查、实验、验收和阶段记录 | 保留当时证据，追加后续结论 |
| `archive/` | 已退出当前范围的架构、BIOS、集成与规划 | 供追溯，不作为启动或实现依据 |
| `characters/` | 已退役人物的历史设定 | 仅文档，保留此固定路径 |
| `media/` | [Bina 正式采用六视图与过程参考](media/README.md)及[历史/废稿归档](media/archive/README.md) | 标注用途与采用状态，不代替运行资源 |

入门说明集中在根目录 README，开发计划集中在根目录 TODO，避免重复维护同一份安装步骤或任务列表。模型原图、可编辑工程、提示词和验收产物继续保存在仓库 `assets/`；浏览器运行资源位于 `frontend/public/`。

## 编写约定

- 当前指南和参考使用主题名称，例如 `live2d.md`、`memory.md`；检查记录使用 `YYYY-MM-DD-topic.md`。
- 指南说明前置条件、执行目录、步骤和验证方式；参考文档说明当前事实及其源码位置。
- 阶段记录区分“已实现”“已验证”“计划中”，不能把静态素材检查写成动画验收，也不能把模拟服务回归写成真实模型验收。
- 旧设计退出当前范围后移入 `archive/`，在入口处标明历史状态；历史角色继续放在 `characters/`。
- 使用相对链接。移动文档时同时更新 README、TODO、资源说明和脚本中的引用。

本轮交付包含 Q01–Q09 质量修复、M01–M10 可维护性整改和文档分类；实现与验收汇总见[解决汇报](reviews/2026-11-08-maintainability-resolution.md)。

历史资料入口见[归档索引](archive/README.md)，现有决策见 [ADR 索引](adr/README.md)。
