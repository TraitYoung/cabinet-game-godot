# Live2D 本地资源

网页使用 `pixi.js` 和 `untitled-pixi-live2d-engine/cubism`，支持 Cubism 3/4/5 的 `.model3.json` 模型。

## 安装资源

1. 从 [Live2D 官方网站](https://www.live2d.com/en/sdk/download/web/)下载 Cubism SDK for Web，将其中的 `live2dcubismcore.min.js` 放到 `core/`。
2. 将 Bina 的完整导出模型放到 `bina/`，保留模型内部文件的相对路径。需要入口 `.model3.json`、`.moc3` 和纹理；物理、动作、表情文件按模型提供的内容放入。
3. 打开 `/solo`，在侧栏「形象」填入 `/live2d/bina/bina.model3.json`，点击「加载模型」。入口文件名以实际导出文件为准。

目录示例：

```text
live2d/
  core/live2dcubismcore.min.js
  bina/
    bina.model3.json
    bina.moc3
    bina.physics3.json
    textures/...
    motions/...
    expressions/...
```

模型加载成功后自动适配画布，使用引擎的待机与鼠标注视能力；侧栏读取模型自身的动作和表情供预览。选择的路径保存在当前浏览器，点击「使用立绘」可清除。没有模型或加载失败时继续显示 Bina 定妆图。

可以使用[官方示例模型](https://www.live2d.com/en/download/sample-data/)验收渲染。示例仅用于技术验证，不代表 Bina 的正式形象。模型与 Core 使用各自的授权条款；第三方引擎的 MIT 许可不覆盖这些资源。本目录忽略 Core 和模型资产，安装部署时需要单独准备。

当前尚未接入 TTS、语音口型或对话自动触发表情。单张立绘需要完成拆图、补画和 Cubism 绑定后才能作为 Live2D 模型加载。

实现结构、运行命令与验收步骤见 [Bina Live2D 接入](../../../docs/Bina_Live2D.md)。
