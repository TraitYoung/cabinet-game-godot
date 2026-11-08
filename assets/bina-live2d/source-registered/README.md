# Bina 原图坐标分层材料

2026-11-06，针对五官不像原图、头发与脸部有拼接感的问题返工。当前材料直接拆分日常装正面原图的可见像素，所有部件保留原始位置与尺寸。内置 imagegen 仅生成前景遮罩及被遮挡的皮肤底层，未采用独立生成的五官或头发。

## 查看结果

- [脸部对比](face-comparison.png)：左为原图，中为被否定的独立分件拼装，右为本次原图分层合成；放大仅用于检查。
- [完整合成预览](assembled-preview.png)：透明 PNG，1536 × 1024。
- [部件目录](parts)：24 个透明 PNG，包括五官、虹膜、头发、镜框、脸部底层、躯干、袖子、手、裙子、腿。
- [PSD2Live Layout](bina.layout.json)：原图坐标下的裁切偏移、尺寸、顺序与标签。
- [检查记录](material-report.json)：原图哈希、测量基准及实际执行的像素检查。
- [生成提示词](prompts.txt)：遮罩与底层补绘实际使用的提示词。

文件名中的 left/right 沿用测量文档的画面左右；Layout 语义标签换算为人物自身左右。

## 分层与校验

原图为 `../../bina-tpose/casual/bina-casual-tpose-front.png`，测量来自 `../../bina-tpose/measurements/proportions.json`。画布和整体缩放为原始 1536 × 1024、1:1，裁切只是存储方式，没有逐个缩放或挪动五官。

`matte-generated.png` 用作前景遮罩。打包时进一步去掉与画布外缘连通的近白背景，并恢复被遮罩误判为透明的镜片后方头发。`underpaint-generated.png` 只有脸部区域进入隐藏皮肤底层，静止状态完全被原图部件覆盖；其身体部分未被使用。

检查重新载入源图、生成输入并重新合成分件：全部不透明像素与原图 RGB 差异计数为 **0**，分层合成透明度与抠图基准相同。半透明边缘 RGB 会受合成舍入影响，不宣称逐像素无损；该检查也不等同于外轮廓或动画验收。

Windows PowerShell 5.1，在仓库根目录复现（使用系统自带 .NET System.Drawing，无额外包）：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/prepare_bina_registered.ps1
```

脚本使用仓库中的生成结果，不再次请求 imagegen。对比面板另引用 `../source-measured/assembled-preview.png` 作为被否定版本。输入尺寸、原图哈希、空部件、分层透明度或不透明像素复合不符时脚本报错。

## 当前边界

这套材料已导入 `../bina-registered.psd2live` 并重新绑定，网页默认模型为 `frontend/public/live2d/bina-registered/bina.model3.json`。原画嘴部在工程中标为脸部细节，保留原轮廓；没有口腔内层，暂不生成口型。身体现已改用 [参考 T 姿生成的自然站姿](../source-standing/README.md)，当前目录继续提供原图头部与颈部分件。原图头高只有 144 px，本次优先保留原画外貌，不把插值放大称作新增细节。

五官层包含少量相邻皮肤，发片切口需随变形测试进一步精修。已提供隐藏脸部底层；袖口、裙下、腿部连接处仍需补画重叠区域。嘴部尚无口腔内层。静态合成一致不代表大角度转头、眨眼、张嘴时已经无缝，不能直接将自动绑定结果当作正式模型。
