# Bina 自然站姿素材

这版以原始日常装正面 T 姿为参考，由内置 imagegen 生成新的自然站姿。肩线、袖笼、袖子褶皱、衣服垂坠和放松手部均重新绘制。直接旋转 T 姿袖子的版本已被否定。

- `standing-master-v1.png`：生成母图，1536 × 1024，保留生成器输出的 RGBA 透明度。
- `prompt.txt`：实际使用的完整提示词。
- `parts/head/`：从 `source-registered/parts/` 原样复制的头部与颈部分件，SHA-256 逐文件一致。
- `bina.layout.json`：母图身体与原图头部分件的导入清单。
- `../standing-pose.json`：参考图与生成母图哈希、身体裁切多边形及原图保留图层。

## 模型组装

使用 PSD2Live 3.6.7 导入 `bina.layout.json` 并执行 `rig_generate`。对 `standing_master` 执行 `source_split_polygon`，使用 `standing-pose.json` 的 `generated_body_polygon`，分成 `standing_body` 和 `generated_head_reference`；删除后者，保留原图头部、头发与颈部。

保存到 `../bina-registered.psd2live`，导出 Cubism 工程及网页资源。导出文件的 `bina.layout` 前缀在打包时统一为 `bina`，网页资源位于 `frontend/public/live2d/bina-registered/`。

身体目前是一块连续网格，避免再次通过旋转分件改变肩部外观；整体呼吸和身体运动保留，独立手臂动作尚未绑定。嘴部继续保留原画闭嘴轮廓，没有口型内层。

浏览器已检查桌面与手机加载、三组动作、四种表情、刷新及立绘选择保持。实际页面截图与检查记录见上级目录的 `registered-browser-*`。
