# Bina 方案 A · v2 T-pose 参考（已归档）

2026-11-08 归档。此组保留生成来源与服装演变记录，当前正式采用资源见[最终六视图](../../v3/anatomy-locked/turnaround/README.md)。

基于已定稿概念图和自然站姿母图生成两套服装的正面、背面、侧面参考，每张一个视图。这里的 T-pose 是**生成参考，尚未经用户批准**，不代表已完成 Live2D 重建。

## 来源

- [视觉设定唯一真相源](../../../../config/persona_visual/bina.json)。
- 休闲装：[概念图](../../../../docs/media/archive/v2-approved-sources/bina-casual.jpeg)、[自然站姿母图](../../../../docs/media/archive/v2-approved-sources/bina-casual-standing.jpg)。
- 工装：[概念图](../../../../docs/media/archive/v2-approved-sources/bina-work.jpeg)、[自然站姿母图](../../../../docs/media/archive/v2-approved-sources/bina-work-standing.jpg)。
- [定稿资源说明](../../../../docs/media/README.md)。

母图提供角色身份、比例和服装依据；概念图补充服装结构。保留冷茶棕层次锁骨发、琥珀金圆杏眼及各自服装，不引用旧版白发 T-pose 作为外貌参考。

## 文件

| 服装与视图 | 生成参考 | 实际提示词 |
| --- | --- | --- |
| 休闲装正面 | [PNG](casual/bina-casual-tpose-front.png) | [提示词](prompts/casual-front.txt) |
| 休闲装背面 | [PNG](casual/bina-casual-tpose-back.png) | [提示词](prompts/casual-back.txt) |
| 休闲装侧面 | [PNG](casual/bina-casual-tpose-side.png) | [提示词](prompts/casual-side.txt) |
| 工装正面 | [PNG](work/bina-work-tpose-front.png) | [提示词](prompts/work-front.txt) |
| 工装背面 | [PNG](work/bina-work-tpose-back.png) | [提示词](prompts/work-back.txt) |
| 工装侧面 | [PNG](work/bina-work-tpose-side.png) | [提示词](prompts/work-side.txt) |

使用内置 `image_gen`，逐张生成。六张均为 **1254 × 1254 RGB PNG**，原样保存。白色背景，无地面阴影、文字或网格；背景存在轻微近白像素，并非逐像素 `#FFFFFF` 或透明通道。保留完整头顶、双手及鞋底，正面和背面双臂水平展开，侧面统一朝画面右侧，手臂沿视线方向重叠。实际文件元数据、来源顺序与提示词哈希见 [manifest.json](manifest.json)。

## 使用限制

已逐张目视核对身份、服装、姿势和左右细节，尚待用户审阅。母图未展示的服装背面结构由生成补全；独立生成的视图不保证严格正交或天然同尺度。

本版尚未重新标点或测量。[旧版测量目录](../../measurements/)、旧测量脚本中的 `LANDMARKS` 以及白发版比例数据仅供历史复现，不能直接套用到这些图。后续建模应从正式采用图重新标点，再计算比例。
