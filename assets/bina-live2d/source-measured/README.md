# 被否定的独立分件试稿

2026-11-06 尝试以测量文档定位生成的五官、头发和身体部件。该试稿未通过外貌检查：脸部偏离原图，五官与头发有拼接感，明暗与边缘也不连续。`material-report.json` 已标记为 rejected。

本目录保留生成输入、18 个分件、Layout 和拼装预览，仅用于复现与比较。`measurement-overlay.svg` 中的标点是原图目标坐标，不是对试稿重新测量的结果。

当前材料见 [source-registered](../source-registered/README.md)。其打包脚本会读取本目录的 `assembled-preview.png` 制作脸部对比图。

需要复现此失败尝试时，在仓库根目录使用 Windows PowerShell 5.1 执行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/prepare_bina_live2d_measured.ps1
```

复现成功仅表示文件可重新打包，不表示外貌或模型验收通过。
