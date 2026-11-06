# Bina 工装 Live2D

使用 `reference-to-live2d` skill，以 `assets/bina-tpose/work/` 的正面、侧面为设计参考，由内置 imagegen 生成完整自然站姿，再从同一母图原位拆层。没有旋转 T-pose 袖子，也没有加入日常装头上的眼镜。

工装保留短夹克、衬衫与领带、橙色肩部织带及腰带、工装裤、挂件、右侧腕带和运动鞋。肩线、袖子褶皱与放松双手按自然站姿重新绘制。

## 素材和工程

- `standing-master-v1.png`：1536 × 1024 RGBA 生成原件，保留生成 alpha。
- `prompt.txt`：实际使用的完整提示词。
- `reference-measurements.json`：三张工装 T-pose 的原图哈希、人工标点及重算比例；这些是参考图数据，不冒充生成图的实际测量值。
- `generation.json`：参考图、生成图哈希与组装方法。
- `parts/`、`bina.layout.json`：14 个图层及原图坐标。
- `rig-preview-0.png`：原生编辑器中的静态模型预览。
- `../bina-work.psd2live`、`../bina-work.cmo3`、`../bina-work.can3`：可编辑工程和动画工程。
- 网页入口：`frontend/public/live2d/bina-work/bina.model3.json`。

工装的可见头部和身体都来自同一张生成母图，避免独立生成五官造成拼接。隐藏皮肤底层复用同一人物已有的底层，位于可见图层之后。

眼睛保留为完整眼部纹理，包含虹膜；不把虹膜挖出后再用存在透明孔洞的眼白作裁剪遮罩。眨眼仍绑定眼睛开合参数，未绑定独立虹膜视线。嘴部用 `face/detail` 保留闭嘴轮廓，没有口腔内层。

身体目前为连续网格，支持整体待机、呼吸和身体运动，独立手臂动作尚未绑定。

## 重建

依赖项目 Python 环境、PSD2Live 3.6.7 与其官方 `mcp_proxy.py`；本地工具安装及 MCP 启动见上级目录说明。分层脚本使用 Windows PowerShell 5.1 和 System.Drawing。

在仓库根目录运行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/prepare_bina_work.ps1
```

启动 PSD2Live 本地 MCP 后，将本次令牌放入环境变量，不写入源码：

```bash
export PSD2LIVE_MCP_TOKEN='<本次本地工具令牌>'
NO_PROXY=127.0.0.1,localhost .venv/bin/python scripts/build_bina_work.py
```

脚本导入工装 Layout、绑定、保存独立工程并打包到 `frontend/public/live2d/bina-work/`，不会覆盖日常装模型。

## 使用与验收

打开 `/solo`，在侧栏“形象”中点击“工装”或“日常装”。浏览器保存选择，工装加载失败时使用工装母图作静态后备。

前端代码检查与构建已通过。真实网页检查覆盖两套服装切换、刷新保持、Blink/Nod/Shake、四种表情和手机画布，未出现页面异常；12 个关联资源均存在并正常加载。

```bash
PLAYWRIGHT_BROWSERS_PATH="$PWD/.devstack/playwright-current" \
  .venv/bin/python scripts/check_bina_outfits.py
```

浏览器缓存路径可按本机实际安装位置替换。截图与记录位于上级目录的 `work-browser-desktop.png`、`work-browser-mobile.png`、`work-browser-verification.json`，导出记录为 `work-generation-report.json`。
