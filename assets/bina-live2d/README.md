# Bina Live2D 第一版

2026-11-06 新增[原图坐标分层材料](source-registered/README.md)：针对五官与头发拼接失真，按日常装正面原图原位拆成 24 层，可见颜色来自原图，静态不透明像素复合差异为 0。[对比图](source-registered/face-comparison.png)展示原图、被否定版本与本次结果。该材料尚未重新绑定；下述 `.psd2live`、Cubism 工程及网页模型仍为已有初版。

以 `frontend/public/bina/casual.jpeg` 为外貌参考，通过 imagegen 生成透明分件图，再由 PSD2Live 3.6.7 自动绑定、导出。当前为自动制作的初版，分件边缘、转头轮廓与服装细节可继续在工程中精修。

## 文件

- `source/parts-atlas.png`：生成的原始 4×4 部件图。
- `source/parts/`：参与绑定的 15 个独立部件。
- `source/bina.layout.json`：部件位置、绘制顺序和语义标签。
- `source/assembled-preview.png`：绑定前的拼装预览。
- `bina.psd2live`：可继续编辑的 PSD2Live 工程。
- `bina.cmo3`、`bina.can3`：导出的 Cubism 工程与动画工程。
- `bina.psd2live.json`、`generation-report.json`：导出与参数记录。
- `browser-desktop.png`：浏览器中的实际页面截图。
- `browser-mobile.png`：手机尺寸下的实际页面截图。
- `browser-verification.json`：浏览器交互检查结果与资源响应记录。
- 网页运行资源位于 `frontend/public/live2d/bina/`，入口为 `bina.model3.json`。

## 重新打包素材

当前分件布局已缩小头发、脸部与眼部等区域并重新导出模型。这是初版局部调整；完整三视图原图与人工比例测量见 [T 姿参考说明](../bina-tpose/README.md)，后续全身重建以该处数据为准。`reference/` 中的裁切图、旧截图及比例记录仅保留早期调整依据，不代表当前比例验收结果。

在仓库根目录执行，使用 Python 3.13：

```bash
.devstack/tools/uv pip install --python .venv/bin/python -r assets/bina-live2d/requirements.txt
.venv/bin/python scripts/prepare_bina_live2d.py
```

脚本按固定部件图裁切、对齐素材，生成 Layout 清单与拼装预览，不调用图片生成服务，也不重新绑定模型。

## 继续编辑

使用 [PSD2Live 3.6.7](https://github.com/tsunehimatoi/psd2live/releases/tag/v3.6.7) 打开 `bina.psd2live`。本次本地工具安装于 `.devstack/tools/psd2live/`，通过官方 `mcp_proxy.py` 连接 MCP 完成了导入、自动绑定、保存和导出。工具安装目录被 Git 忽略，不随仓库克隆。

Linux x86_64 便携版的安装命令（仓库根目录执行）：

```bash
mkdir -p .devstack/downloads .devstack/tools/psd2live
curl -fL https://github.com/tsunehimatoi/psd2live/releases/download/v3.6.7/PSD2Live-3.6.7-linux-x64.tar.gz -o .devstack/downloads/PSD2Live-3.6.7-linux-x64.tar.gz
curl -fL https://github.com/tsunehimatoi/psd2live/releases/download/v3.6.7/SHA256SUMS.txt -o .devstack/downloads/SHA256SUMS.txt
(cd .devstack/downloads && awk '$2 ~ /linux-x64.tar.gz$/ {print}' SHA256SUMS.txt | sha256sum -c -)
tar -xzf .devstack/downloads/PSD2Live-3.6.7-linux-x64.tar.gz -C .devstack/tools/psd2live --strip-components=1
curl -fL https://raw.githubusercontent.com/tsunehimatoi/psd2live/v3.6.7/mcp_proxy.py -o .devstack/tools/psd2live/mcp_proxy.py
```

需要启动独立 MCP 服务时，在仓库根目录运行：

```bash
.devstack/tools/psd2live/bin/PSD2Live mcp --port 23871 --store "$PWD/.devstack/psd2live-workspace" --profile full
```

该命令打印本次连接的令牌。另一个终端设置 `PSD2LIVE_MCP_TOKEN` 为该令牌后，可用官方代理操作；`--edit` 自动携带当前工程状态：

```bash
export NO_PROXY=127.0.0.1,localhost
.venv/bin/python .devstack/tools/psd2live/mcp_proxy.py call workspace_overview
.venv/bin/python .devstack/tools/psd2live/mcp_proxy.py call project_open '{"path":"/绝对路径/assets/bina-live2d/bina.psd2live"}' --edit
```

重新从素材创建工程时，使用 `project_import_layout` 导入 `source/bina.layout.json`，再调用 `rig_generate`。导出的文件名取自输入文件名，替换网页资源时同时核对 `.model3.json` 中的相对引用。

当前包含 20 个参数，4 组动作（Idle、Blink、Nod、Shake），4 种表情（Smile、Sad、Angry、Surprised）及头发物理。TTS 口型与聊天自动驱动尚未接入。

网页对内置模型应用 `frontend/src/modules/embodiment/binaRig.ts` 中的幅度校正：在动作、鼠标跟随和物理叠加后收小转头、身体、视线及头发运动，关闭眼球弹性，并保留默认嘴型轮廓。校正仅作用于内置模型路径，不改变其他导入模型或原始 Cubism 工程。当前属于运行时修正；大角度转头仍需要在源工程中精修网格和遮挡。

## 已完成的验收

2026-11-05，Chromium + 软件 WebGL：默认模型加载、待机画面变化、三组手动动作、四种表情、切换立绘后刷新、恢复默认模型、Live2D 选择刷新恢复、手机尺寸画布适配均通过，无页面异常。全部 12 个模型关联资源存在。

2026-11-05 本次提交前复核：前端 `npm run lint`、`npx tsc --noEmit` 与默认 `npm run build`（Turbopack）通过；六张原始 T 姿图的哈希、尺寸及 12 个模型资源引用检查通过。页面截图与交互记录沿用已有验收材料，本次未重新执行浏览器交互验收。历史环境的 Webpack 构建方式见 [接入说明](../../docs/Bina_Live2D.md)。

![桌面实测](browser-desktop.png)
