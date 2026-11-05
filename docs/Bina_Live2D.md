# Bina Live2D 接入

## 当前实现

Bina 的网页形象使用 PixiJS 8.22.0 与 `untitled-pixi-live2d-engine` 1.4.0。通过 Cubism Modern 入口加载 `.model3.json` 模型，模型所用的 Cubism 功能还需要匹配的 Core 版本。

已实现模型加载、待机更新、鼠标注视、动作组与表情预览、画布尺寸适配，以及现有人物缩放和夜色效果。模型路径保存在当前浏览器的 `bina-live2d-model` 中，刷新后恢复。默认加载 `/live2d/bina/bina.model3.json`；手动切回立绘或加载失败时显示 Bina 静态立绘。点击「恢复默认形象」重新加载内置模型。

已从 Bina 定妆图生成透明分件素材，并通过 PSD2Live 3.6.7 的本地 MCP 自动绑定第一版模型。模型包含 20 个参数、4 组动作、4 种表情和头发物理。可编辑 `.psd2live`、`.cmo3` 工程、原始部件及重建说明见 [模型资源](../assets/bina-live2d/README.md)。当前仍需精修分件边缘与大角度转头。TTS 口型、对话状态与情绪自动驱动不在本次实现中。

## 代码位置

| 文件 | 职责 |
| --- | --- |
| [Live2DAvatar.tsx](../frontend/src/modules/embodiment/Live2DAvatar.tsx) | 加载 Core，按需导入引擎，创建 WebGL 画布，绑定 ticker，适配尺寸并在卸载时销毁模型和应用 |
| [SoloChatView.tsx](../frontend/src/modules/solo-chat/SoloChatView.tsx) | 形象区域、模型路径设置、加载状态、动作与表情预览 |
| [globals.css](../frontend/app/globals.css) | Live2D 画布布局、形象缩放和夜色样式 |
| [资源说明](../frontend/public/live2d/README.md) | Core 和模型的安装目录 |

Core 先通过浏览器脚本加载，随后组件动态导入 PixiJS 和引擎，避免服务端执行依赖浏览器的运行时。模型使用当前应用的 ticker 更新；动作和表情列表直接读取模型定义，不预设额外的动作名称。

## 安装与运行

在仓库根目录执行：

```bash
cd frontend
npm ci
npm run dev
```

从 [Live2D 官方下载页](https://www.live2d.com/en/sdk/download/web/)取得 Cubism SDK for Web，把 `live2dcubismcore.min.js` 放入 `frontend/public/live2d/core/`。仓库已包含 Bina 的完整模型导出目录 `frontend/public/live2d/bina/`。本次本地安装使用官方 CDN 的 Core 5.1.0：

```bash
mkdir -p public/live2d/core
curl -fL https://cubism.live2d.com/sdk-web/cubismcore/live2dcubismcore.min.js -o public/live2d/core/live2dcubismcore.min.js
```

打开 `http://127.0.0.1:3000/solo`，页面会默认加载 Bina 模型。也可在「形象」页签填写其他模型路径并点击「加载模型」。点击「使用立绘」可清除模型路径；再次点击「加载模型」会重新创建模型实例。

Core 与额外安装的模型仍被 Git 忽略，Bina 初版运行资源已纳入仓库。部署时另行安装 Core，并遵循各自的许可；引擎的 MIT 许可不覆盖 Core 和模型素材。

## 示例模型与手动验收

也可以从[官方示例](https://www.live2d.com/en/download/sample-data/)获取已绑定模型。若将 Haru 的完整模型目录放入 `frontend/public/live2d/sample/`，入口为 `/live2d/sample/Haru.model3.json`。示例仅用于验证渲染，不作为 Bina 的正式形象。

1. 新浏览器默认加载 Bina Live2D；选择「使用立绘」后确认静态图和聊天界面可用。
2. 加载完整模型，确认状态变为「Live2D 已就绪」，画布显示模型且待机持续更新。
3. 在模型画布内移动鼠标，确认视线跟随；点击侧栏动作与表情按钮，确认对应效果。
4. 调整人物缩放、侧栏开合、窗口宽度和房间氛围，确认模型适配画布且显示正常。
5. 刷新页面，确认模型路径恢复；切回立绘并刷新，确认不再加载模型。
6. 填写不存在的模型路径，确认显示加载错误并保留立绘；重新填写正确路径后可加载。

## 检查与验收

在 `frontend/` 中执行：

```bash
npm run lint
npx tsc --noEmit
npm run build
```

本机 Next.js 16.2.1 的 Turbopack 构建遇到已有 Google Fonts 的查询解析错误，改用官方 Webpack 模式构建通过：

```bash
npx next build --webpack
npm run start
```

2026-11-05 已使用 Chromium 与软件 WebGL 对 Bina 初版进行真实页面验收：默认加载、待机画面变化、Blink/Nod/Shake 动作、四种表情、立绘与 Live2D 选择持久化、恢复默认模型及手机尺寸适配均通过，无页面异常。结果见 [验收记录](../assets/bina-live2d/browser-verification.json)，画面见 [桌面截图](../assets/bina-live2d/browser-desktop.png) 与 [手机截图](../assets/bina-live2d/browser-mobile.png)。

WebGL 为 Live2D 必需能力，组件限制使用 WebGL 并允许软件渲染，避免 PixiJS 回退到不支持的 Canvas 渲染器。模型按可见绘制范围设置锚点，适配画布时保留动作余量。销毁时先释放模型及其 ticker 监听，再销毁应用，避免切换立绘时访问已销毁的 ticker。

## 后续工作

继续精修 Bina 第一版分件和绑定，将待机、倾听、思考、回应等互动状态映射到模型已有的动作与表情。语音口型在接入 TTS 音频后实现。
