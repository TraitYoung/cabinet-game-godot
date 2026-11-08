# 开发与检查

依赖安装、环境变量、Docker 和前后端启动命令统一维护在[项目 README](../../README.md#本地开发)。本文说明修改后如何验证。命令默认在仓库根目录执行。

## 统一质量门禁

使用 Python 3.13 和 Node.js 24，在仓库根目录执行：

```bash
.venv/bin/python -m pip install -r requirements-dev.txt
bash scripts/check_quality.sh
```

Ruff 的检查与格式范围由 `pyproject.toml` 的 include 指定，mypy 渐进覆盖配置、回合协议和数据库基础模块，不对未整理模块作无关格式化。CI 使用同一命令，另运行浏览器和 Windows 进程策略检查。

## 修改前

先阅读 [TODO](../../TODO.md) 确认当前范围，再查看[架构参考](../reference/architecture.md)定位模块。Bina 是唯一运行人物，Hindsight 是唯一长期记忆服务。旧 BIOS 和内阁设计见归档，不能据此恢复已退役运行功能。

现有 `.env`、数据库、模型服务和生成资源属于本地环境；离线检查使用临时数据库或模拟服务。

## 后端回归

激活项目虚拟环境后执行：

```bash
source .venv/bin/activate
python -m unittest discover -s test_suite -v
PYTHONPATH=. python test_suite/test_solo_fast.py
PYTHONPATH=. python test_suite/test_bina_first.py
```

针对取消、提交、会话互斥、情绪并发、历史预算和启动器归属的回归：

```bash
python -m unittest test_suite.test_quality_regressions -v
```

这些检查使用模拟模型和临时数据库。Compose 配置回归将实际清单与 `.env.example` 复制到临时目录，验证容器路径覆盖宿主路径，不依赖开发者的私有 `.env`。真实 Hindsight 验收使用 `scripts/check_hindsight_memory.py`，会调用模型并在独立测试 bank 中保存记忆，运行说明见[项目 README](../../README.md#真实验收)。

## 前端检查

在 `frontend/` 中执行：

```bash
npm run lint
npm run typecheck
npm test
npm run build
```

浏览器交互回归需要已启动的前端和 Playwright Chromium；安装步骤见根目录 README。在仓库根目录执行，缓存路径按本机安装位置调整：

```bash
PLAYWRIGHT_BROWSERS_PATH="$PWD/.devstack/playwright" .venv/bin/python scripts/check_frontend_interactions.py
```

每个浏览器场景使用独立上下文，可用 `--case test_timeout` 单独执行。脚本模拟接口和麦克风，覆盖会话历史、录音转写、停止/超时、提交重试、附件会话隔离和预览清理。它不验证真实模型回复的语义质量。

Live2D 服装和动作验证另用 `scripts/check_bina_outfits.py`，见[模型接入](live2d.md)。

## 启动器与持久化

```bash
bash -n start.sh stop.sh scripts/dev_stack.sh scripts/setup_linux_env.sh
python scripts/check_container_persistence.py
```

容器检查读取 Compose 中的数据库路径和卷映射，使用独立测试项目写入临时聊天与情绪状态，替换容器后再读取，最后清理本次测试卷。Docker 权限不足时使用：

```bash
sudo .venv/bin/python scripts/check_container_persistence.py
```

默认检查使用 API 镜像；镜像无法拉取时，可加 `--image ghcr.io/vectorize-io/hindsight:1.2.0`，用已缓存且含 Python 的镜像检查存储挂载。替代镜像验证不等于完整 API 镜像部署验收。

## 更新文档

功能变化更新指南和参考；任务进度更新根目录 TODO；检查证据按日期写入 `reviews/`。提交前执行 `git diff --check`，检查本地文档链接和命令所指文件存在，并明确记录没有运行的检查。

进程归属也可直接执行 `python scripts/check_process_ownership.py`，同一脚本支持 Windows/Linux。它只创建并结束临时测试进程，覆盖父子进程、孤儿进程、旧记录和 PID 复用；Windows 上还解析 PowerShell 入口。
