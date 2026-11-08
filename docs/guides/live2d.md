# Bina Live2D 接入

本指南说明当前网页模型的加载、切换与检查。素材制作见[完整制作流程](live2d-workflow.md)，阶段证据见 [2026-11-06 记录](../reviews/2026-11-06-live2d.md) 和[模型资源](../../assets/bina-live2d/README.md)。

## 当前模型与能力

| 项目 | 当前行为 |
| --- | --- |
| 默认日常装 | `/live2d/bina-registered/bina.model3.json` |
| 工装 | `/live2d/bina-work/bina.model3.json` |
| 旧初版 | `/live2d/bina/bina.model3.json`，作为对照资源；浏览器旧默认设置会迁移到日常装新版 |
| 设置保存 | 浏览器 `bina-live2d-model`，刷新后恢复 |
| 回退立绘 | 日常装 `/bina/casual.jpeg`；工装 `/bina/work.png` |
| 已有交互 | 加载、待机、鼠标注视、动作与表情预览、缩放和画布适配 |
| 后续工作 | 口型、独立发丝物理与虹膜追踪精修、对话和情绪自动驱动、正式模型验收 |

两套服装已完成连续头部与颈部遮挡返工。已有加载和动作预览不代表全身比例、大角度动画或语音口型已完成验收。

## 前置与运行

按[根目录 README](../../README.md#本地开发)安装前端依赖。Core 需另行安装到 `frontend/public/live2d/core/`，下载命令、目录结构和授权说明统一见[运行资源说明](../../frontend/public/live2d/README.md)。替换模型时，保留 `.model3.json` 内纹理、动作和表情文件引用的相对关系。

在仓库根目录执行：

```bash
cd frontend
npm run dev
```

打开 `http://127.0.0.1:3000/solo`。侧栏“形象”可切换日常装与工装，选择动作和表情，或填写其他模型入口。选择“使用立绘”会清空模型路径；“恢复默认形象”恢复日常装模型和默认画面设置。

## 实现位置

| 文件 | 职责 |
| --- | --- |
| [Live2DAvatar.tsx](../../frontend/src/modules/embodiment/Live2DAvatar.tsx) | 加载 Core、按需导入引擎、创建画布、更新和释放模型 |
| [binaRig.ts](../../frontend/src/modules/embodiment/binaRig.ts) | 内置模型运行时动作幅度校正 |
| [SoloChatView.tsx](../../frontend/src/modules/solo-chat/SoloChatView.tsx) | 服装和模型选择、动作预览、加载状态与回退立绘 |
| [globals.css](../../frontend/app/globals.css) | 人物区域、缩放与房间样式 |

网页使用 PixiJS 8 与 `untitled-pixi-live2d-engine/cubism`，仅在浏览器加载运行时。模型必须使用可用的 WebGL 环境。组件卸载或切换模型时释放模型、ticker 监听和画布资源。

旧初版会限制转头、身体、视线及头发幅度，并保留嘴部开合下限；修复版使用作者设置的头部动作，单独降低身体与呼吸幅度。具体参数以 `binaRig.ts` 为准，不应把旧初版校正值套用于所有模型。

## 验证

前端静态检查见[开发与检查](development.md)。手动确认：

1. 新浏览器默认显示日常装模型，工装切换后刷新仍保持选择。
2. 动作和表情按钮有可见效果，鼠标注视和待机更新正常。
3. 改变窗口尺寸、侧栏开合及人物缩放，画布能够适配。
4. “使用立绘”后仍可聊天；填写错误模型路径时显示错误并保留立绘。
5. 重新加载有效模型后恢复，页面无未处理异常。

两套服装的浏览器回归脚本为 [check_bina_outfits.py](../../scripts/check_bina_outfits.py)。启动前端并安装 Playwright Chromium 后，在仓库根目录运行，缓存路径按本机调整：

```bash
PLAYWRIGHT_BROWSERS_PATH="$PWD/.devstack/playwright" .venv/bin/python scripts/check_bina_outfits.py
```

历史截图、资源引用检查与模型编辑器记录保存在 `assets/bina-live2d/`。每次新验收应记录所用模型版本、浏览器环境、检查范围和未完成项；素材静态像素检查不能代替动画验收。
