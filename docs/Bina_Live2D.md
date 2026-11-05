# Bina Live2D 接入

## 当前实现

Bina 的网页形象使用 PixiJS 8.22.0 与 `untitled-pixi-live2d-engine` 1.4.0。通过 Cubism Modern 入口加载 `.model3.json` 模型，模型所用的 Cubism 功能还需要匹配的 Core 版本。

已实现模型加载、待机更新、鼠标注视、动作组与表情预览、画布尺寸适配，以及现有人物缩放和夜色效果。模型路径保存在当前浏览器的 `bina-live2d-model` 中，刷新后恢复。没有选择模型或加载失败时显示 Bina 静态立绘。

Bina 的正式 Live2D 模型尚未制作。现有定妆图不能直接作为 Live2D 模型；需要拆图、补画，并在 Cubism Editor 中完成变形器和参数绑定。TTS 口型、对话状态与情绪自动驱动不在本次实现中。

## 代码位置

| 文件 | 职责 |
| --- | --- |
| [Live2DAvatar.tsx](../frontend/src/modules/embodiment/Live2DAvatar.tsx) | 加载 Core，按需导入引擎，创建 WebGL 画布，绑定 ticker，适配尺寸并在卸载时销毁模型和应用 |
| [SoloChatView.tsx](../frontend/src/modules/solo-chat/SoloChatView.tsx) | 形象区域、模型路径设置、加载状态、动作与表情预览 |
| [globals.css](../frontend/app/globals.css) | Live2D 画布布局、形象缩放和夜色样式 |
| [资源说明](../frontend/public/live2d/README.md) | Core 和模型的安装目录 |

Core 先通过浏览器脚本加载，随后组件动态导入 PixiJS 和引擎，避免服务端执行依赖浏览器的运行时。模型使用当前应用的 ticker 更新；动作和表情列表直接读取模型定义，不预设 Bina 尚未制作的动作名称。

## 安装与运行

在仓库根目录执行：

```bash
cd frontend
npm ci
npm run dev
```

从 [Live2D 官方下载页](https://www.live2d.com/en/sdk/download/web/)取得 Cubism SDK for Web，把 `live2dcubismcore.min.js` 放入 `frontend/public/live2d/core/`。将完整模型导出目录放入 `frontend/public/live2d/bina/`，保留入口文件引用的相对路径。

打开 `http://127.0.0.1:3000/solo`，在「形象」页签填写 `/live2d/bina/bina.model3.json` 并点击「加载模型」，入口文件名按实际导出结果填写。点击「使用立绘」可清除模型路径；再次点击「加载模型」会重新创建模型实例。

Core 与模型资产已被 Git 忽略，不会随克隆仓库安装。部署时需要另行放入相应文件，并遵循各自的许可；引擎的 MIT 许可不覆盖 Core 和模型素材。

## 示例模型与手动验收

正式模型制作期间，可以从[官方示例](https://www.live2d.com/en/download/sample-data/)获取已绑定模型。若将 Haru 的完整模型目录放入 `frontend/public/live2d/sample/`，入口为 `/live2d/sample/Haru.model3.json`。示例仅用于验证渲染，不作为 Bina 的正式形象。

1. 未设置模型时，确认页面显示定妆图，聊天界面可用。
2. 加载完整模型，确认状态变为「Live2D 已就绪」，画布显示模型且待机持续更新。
3. 在模型画布内移动鼠标，确认视线跟随；点击侧栏动作与表情按钮，确认对应效果。
4. 调整人物缩放、侧栏开合、窗口宽度和房间氛围，确认模型适配画布且显示正常。
5. 刷新页面，确认模型路径恢复；切回立绘并刷新，确认不再加载模型。
6. 填写不存在的模型路径，确认显示加载错误并保留立绘；重新填写正确路径后可加载。

## 已完成的检查

2026-11-05 完成以下检查：

- `cd frontend && npm run lint`：通过。
- `cd frontend && npx tsc --noEmit`：通过。
- `cd frontend && npm run build`：通过；构建需要下载项目已有 Google Fonts。
- 本机官方 Haru 示例的 25 个引用资源完整性：通过。
- 本机 Cubism Core 5.1.0 创建并更新 Haru 模型：通过，读取到 42 个参数、84 个绘制对象。这项检查不包含 WebGL 渲染。

浏览器画面与交互验收尚未完成；此前浏览器工具不可用，随后共享页面显示浏览器错误页。上述编译和 Core 检查不替代手动画面验收。

## 后续工作

制作 Bina 的分层原画和绑定模型后，先按上述步骤验收正式模型，再将待机、倾听、思考、回应等互动状态映射到模型已有的动作与表情。语音口型在接入 TTS 音频后实现。
