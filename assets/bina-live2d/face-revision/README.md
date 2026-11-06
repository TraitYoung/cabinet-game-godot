# Bina 两套头部接缝返工 · v2

当前网页的日常装与工装已使用本目录的头部工程。身体纹理沿用原工程，保留原画可见五官、鼻口、头发和配饰；imagegen 只提供眼眉后方皮肤和颈部遮挡补画。

## 修改与边界

- 将互不重叠的矩形切块改为连续头部底图，以及从原图差异提取的柔边眼睛、眉毛。
- 头发、脸部轮廓、鼻口与配饰合并为连续表面，共享 `DeformFaceNinePose`，取消额外轮廓形变和五官位移，避免分件沿不同变形链开裂。
- 日常装重新绑定眨眼；两套都增加闭眼线及末段显隐切换，避免眨眼露出眼部矩形孔洞。闭眼线是原生 SVG 绘制，不是原画中已有的素材。
- 增加颈部、工装领口的遮挡重叠，原画可见颈部另层保留。
- 网页不再对新版头部套用旧版的 9% 转头倍率或最低嘴部开合补丁；连续身体的呼吸、身体动作倍率继续保留。

目前以头部连续性为优先：**头发不再独立摆动，虹膜暂不独立追踪，闭嘴原画不具备口型**。不是完整高自由度头部绑定；恢复独立发丝需要重新拆层并补画发下遮挡，不能直接启用旧物理。原图头高约 144 px，补画输出和 SVG 放大都不意味着原画细节分辨率提高。

本轮通过已有 PSD2Live 3.6.7 的原生 MCP 操作修改工程，未操作官方 Cubism Editor。`.cmo3` 是导出的可继续精修工程。

## 文件与制作方法

- `*-head-reference.png`：原图在 `(665, 0, 210, 200)` 的原生编辑器裁切。工装来自 `source-work/standing-master-v1.png`，日常装来自 `source-registered/source-cutout.png`。
- `*-underpaint-generated.png`、`prompts.txt`：实际 imagegen 输出与完整发送提示词；保留生成 alpha。
- `*-underpaint-registered.png`：由编辑器 `material_preview(size=210)` 重采样回 210 × 200；不是新增原画细节，也不宣称生成图逐像素注册完全相同。
- `work/`、`casual/`：实际参与绑定的 PNG、Layout、眼眉区域 SVG 和闭眼 SVG。身体、原始颈部从旧工程原样导出；`neck.png` 是额外遮挡补画。
- `bina-*-face-v2.psd2live`、`.cmo3`、`.can3`：原生工程及导出工程。
- `*-before-0.png`、`*-after-0.png`：编辑器实际渲染的返工前后近景；前后网格的姿态与镜头见导出记录，不能当作同像素差分。
- `*-export.json`：实际导出资源、姿态参数及能力边界。

分层使用原生 `material_peel`，按 `eye_left/right-region.svg` 和 `brow_left/right-region.svg` 顺序从同一母图提取。参数为 `threshold=[5,22]`、`grow=0`、`core=2`、`close=1`、`band=5`、`color_match=true`，每次以上一次的底图继续提取。头部底图裁切为 210 × 192，原生橡皮在 `(101,211)`、半径 35 处移除原图下段颈部，使独立颈部可以在后方重叠。

工装原图的内部 alpha 部分小于 255，差异提取后出现了透明皮肤孔洞；`work/alpha-repair-gestures.json` 保存实际原生逐像素修复笔触，颜色取自该服装补画的对应像素，只修复眼眉区域的隐藏皮肤。

## 重建与验证

重建使用已保存的分层 PNG，不重新调用生成器。先按上级目录说明启动 PSD2Live MCP，设置当前服务的 `PSD2LIVE_MCP_TOKEN`；非默认端口另设 `PSD2LIVE_MCP_ENDPOINT`。脚本会替换两套网页资源，首次替换前将旧资源备份到忽略目录 `.devstack/face-revision/runtime-before/`。

```bash
NO_PROXY=127.0.0.1,localhost .venv/bin/python scripts/build_bina_faces.py
PLAYWRIGHT_BROWSERS_PATH="$PWD/.devstack/playwright-current" .venv/bin/python scripts/check_bina_outfits.py
npm --prefix frontend run lint
cd frontend && npm exec -- next build --webpack
```

2026-11-06 实测：编辑器静止、半闭眼、闭眼、左右转头、抬低头、侧倾和组合姿态；转头使用 SDK 参数 `ParamAngleX=±30`、`ParamAngleY=±30`，不是实际空间旋转角度测量。脸部矩形孔洞和分件裂缝较旧版明显改善，闭眼皮肤仍可继续精修。

真实 Chromium 检查通过两套服装切换、刷新保持、Blink/Nod/Shake、四种表情、手机显示，无页面异常；截图与资源状态见上级目录 `work-browser-*`。在独立生产预览 3007 验证后，又在重启后的常用入口 3000 复核通过。Lint、TypeScript 与 Webpack 生产构建通过；默认 Turbopack 构建因环境禁止创建临时监听端口而失败。
