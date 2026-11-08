# Bina T 姿参考与比例测量

2026-11-08 用户已正式采用[以新工装正面为基准的两套服装六视图](v3/anatomy-locked/turnaround/README.md)，后续建模以该组实际外貌和比例为准；新图尚待重新标点测量。[V3 版本入口](v3/README.md)保留正式资源导航，其余 V2/V3 三视图和试稿统一迁入[归档目录](archive/README.md)。

本目录原有的 `casual/`、`work/` 六张原图和 `measurements/` 全部属于**旧版白发形象 v0**，保留用于复现历史测量。以下命令、标点和误差口径仅适用于旧图，不能作为新版外貌或比例依据。

旧版测量基于原图人工标点后计算，不使用旧 Live2D 截图推断人体比例，也不自动修改模型。

## 文件与复现

- `measurements/proportions.json`：原图 SHA-256、像素标点、测量值与归一化比例。
- `measurements/measurements.csv`：各视图的像素测量及其占含鞋全高的比例。
- `measurements/index.html`：本地测量报告，引用六张带标点的 SVG。
- `measurements/*-annotated.svg`：内嵌原图的标点与辅助线，可独立查看。
- `measurements/overview.png`、`*-face-landmarks.png`：已有总览与面部标注图，不由下述脚本重新生成。

在仓库根目录使用 Python 3.13 执行：

```bash
python -m pip install -r assets/bina-live2d/requirements.txt
python scripts/measure_bina_tpose.py
```

脚本使用 Pillow 读取原图尺寸，并重新生成 JSON、CSV、六张 SVG 和 HTML。标点直接定义于脚本的 `LANDMARKS` 中；更换原图后需要重新核对标点。

## 测量口径

坐标以原图左上角为原点，向右为 x 正方向、向下为 y 正方向。头高从头顶到下巴，不含呆毛和眼镜；全高包含鞋底。正面五官估计误差约 ±2 px，身体与侧面可见轮廓约 ±4 px，衣物内肩关节位置约 ±10 px。被遮挡的发际线、下巴或人体骨点记为 `null`，衣物下摆、腰带和裤缝只作为可见标记。

旧版测量以日常装正面为主基准，侧面用于约束轮廓和深度，工作装保留独立数据。不同视图并非严格正交工程图。重建时按含鞋全高统一等比缩放；五官以瞳孔中线与脸宽归一化，不单独拉伸头部或移动五官来适配旧素材。

## 与 Live2D 初版的关系

旧版 Live2D 初版曾进行局部五官、头发与部件布局调整，以及网页端动作幅度校正；该阶段未按这六张原图完成全身重建。

`../bina-live2d/reference/` 保留早期 436×786 裁切参考、被否定的模型截图及其测量；`scripts/measure_bina_proportions.py` 仅用于复现该阶段 JSON 与 SVG。该图截到大腿，无法测量全身头身比，旧截图比较不作为后续建模基准。上述旧图与旧坐标均不适用于 V2 或 V3；新版需要重新标点和测量。
