# Bina 仓库对应关系

项目：[TraitYoung/alive-bina](https://github.com/TraitYoung/alive-bina)。原生工具：[PSD2Live 3.6.7](https://github.com/tsunehimatoi/psd2live/releases/tag/v3.6.7)。以工作区 `README.md`、`TODO.md`、`AGENTS.md` 和当前工具参数为准；Bina 是唯一运行人物。

路径相对用户提供的仓库根目录，不硬编码本机用户名。完整实际制作记录在仓库 `docs/guides/live2d-workflow.md`。

| 阶段 | 依据 |
| --- | --- |
| 人物原画与外貌定义 | `frontend/public/bina/`、`config/persona_visual/bina.json` |
| T-pose 六视图 | `assets/bina-tpose/{casual,work}/` |
| 实际人工标点 | `scripts/measure_bina_tpose.py` 的 `LANDMARKS` |
| 比例与源图哈希 | `assets/bina-tpose/measurements/proportions.json` |
| 完整头部生成候选 | `assets/bina-live2d/head-revision/`，未用于最终可见脸部 |
| 最终原图脸部 | `assets/bina-live2d/source-registered/` |
| 原图分层复现脚本 | `scripts/prepare_bina_registered.ps1` |
| 站姿母图与实际提示词 | `assets/bina-live2d/source-standing/` |
| 身体裁切/头部保留记录 | `assets/bina-live2d/standing-pose.json` |
| 当前头部返工与工程 | `assets/bina-live2d/face-revision/README.md`、`bina-{casual,work}-face-v2.psd2live`、`.cmo3`、`.can3` |
| 当前重建脚本 | `scripts/build_bina_faces.py`；读取已保存的分层 PNG，经原生编辑器绑定和导出 |
| 工装母图与早期分层 | `assets/bina-live2d/source-work/`，14 层硬切版本属于返工前对照 |
| 网页入口 | `frontend/public/live2d/bina-registered/bina.model3.json` |
| 工装网页入口 | `frontend/public/live2d/bina-work/bina.model3.json` |
| 返工前后近景与导出 | `assets/bina-live2d/face-revision/{casual,work}-{before,after}-0.png`、`*-export.json` |
| 导出与浏览器记录 | `assets/bina-live2d/registered-generation-report.json`、`registered-browser-verification.json` |

已接受：原图测量约束外貌；原图头部/颈部原位分层；参考 T-pose 重新生成站姿身体。

当前头部 v2 进一步使用各自母图的连续头部、柔边眼眉与隐藏皮肤，修复硬切块、眨眼与颈部遮挡。鼻口、头发和配饰共享连续表面；独立发丝物理、虹膜追踪和口型尚未完成。原图分层静态像素检查不延伸为 v2 全部像素不变或完整动态验收结论。

未采用：`head-revision/head-master.png` 是完整头部候选；`source-measured/` 是被否定的独立五官拼装；`reference/rejected-standing-rotation.json` 是被否定的袖子旋转方案。文件存在不代表可以恢复使用。

日常装正面为 1536 × 1024。头顶 `(764,28)`，下巴 `(765,172)`，鞋底 y=1009；含鞋全高 981 px、头高 144 px、头身数 6.8125。脸宽 79 px、瞳距 47 px、眼宽 28 px、开合高度 12 px、嘴宽 22 px、颈宽 39 px。数值仅适用于这张参考图，具体坐标/误差查测量 JSON。

```bash
# 原图六视图测量重建，会更新测量产物
.venv/bin/python scripts/measure_bina_tpose.py
# 前端代码改变时
npm --prefix frontend run lint
npm --prefix frontend run build
# 本地服务
bash start.sh
```

原图分层使用 Windows PowerShell 5.1 / System.Drawing，在仓库根目录运行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/prepare_bina_registered.ps1
```

本机曾使用 `.devstack/tools/psd2live/` 及其官方 `mcp_proxy.py`。这些是忽略的本地工具，不保证克隆仓库后存在；安装/启动见 `assets/bina-live2d/README.md`。按当前 schema 调用，令牌只留在进程/环境，不写入 skill。

站姿组装：导入 `source-standing/bina.layout.json` → `rig_generate` → 按 `standing-pose.json` 裁出 `standing_body` → 删除生成头部 → 保留 16 个原图头部/颈部图层 → 保存工程 → 导出 → 核对前缀和相对引用。

当前身体为连续网格，未绑定独立手臂动作。嘴部用 `face/detail` 保留原画闭嘴轮廓，没有口腔内层，不宣称具备口型。

## 头部接缝返工续接

通用步骤见 [seam-repair.md](seam-repair.md)。Bina 本轮实际使用 PSD2Live 3.6.7 MCP，未操作官方 Cubism Editor；`.cmo3` 为导出工程。

- 头部参考裁切是原图 `(665,0,210,200)`；原始补画、实际提示词、210 × 200 重采样和眼眉区域 SVG 均在 `face-revision/`。
- 差异分层使用 `material_peel`，参数与工装 alpha 修复笔触见该目录说明；这些坐标和阈值不是其他角色的默认值。
- 连续头部绑定 `DeformFaceNinePose`，眼眉保留局部开合/表情；颈部补画在原画可见颈部后面。浏览器旧脸部限幅已移除，身体倍率保留。
- 原生近景覆盖 `ParamAngleX/Y=±30`、眨眼、侧倾和组合姿态；数值是 SDK 参数，不是实测角度。真实网页覆盖两套服装、刷新、动作表情和手机显示。

```bash
# 先启动本地编辑器并设置当前 PSD2LIVE_MCP_TOKEN；非默认端口另设 endpoint
NO_PROXY=127.0.0.1,localhost .venv/bin/python scripts/build_bina_faces.py
PLAYWRIGHT_BROWSERS_PATH="$PWD/.devstack/playwright-current" .venv/bin/python scripts/check_bina_outfits.py
# 默认构建受本机端口权限限制时，本轮通过的生产构建命令
cd frontend && npm exec -- next build --webpack
```

重建脚本会替换两套网页资源，并在 `.devstack/face-revision/runtime-before/` 首次备份旧资源。前述站姿组装步骤属于头部 v2 之前的历史阶段，不能直接导出旧工程覆盖现有返工。
