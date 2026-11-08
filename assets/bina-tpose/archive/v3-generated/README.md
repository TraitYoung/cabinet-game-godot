# 早期 V3 三视图生成候选（已归档）

2026-11-08 归档。以下六张未被采用，正式入口为[已批准六视图](../../v3/anatomy-locked/turnaround/README.md)。

以下六张是基于 [V3 概念图与自然站姿母图](../../../../docs/media/archive/v3-design-drafts/README.md)生成的较早候选，保留原提示词与来源，不属于此次正式采用的六视图。

身份以[用户原始要求](../../../../docs/media/archive/v3-design-drafts/prompts/identity-lock.txt)和[视觉唯一真相源](../../../../config/persona_visual/bina.json)为准。休闲装参考[概念图](../../../../docs/media/archive/v3-design-drafts/bina-casual-concept.png)与[母图](../../../../docs/media/archive/v3-design-drafts/bina-casual-standing.png)；工装参考[概念图](../../../../docs/media/archive/v3-design-drafts/bina-work-concept.png)与[母图](../../../../docs/media/archive/v3-design-drafts/bina-work-standing.png)。

| 服装与视图 | 生成参考 | 实际提示词 |
| --- | --- | --- |
| 休闲装正面 | [PNG](casual/bina-casual-tpose-front.png) | [提示词](prompts/casual-front.txt) |
| 休闲装背面 | [PNG](casual/bina-casual-tpose-back.png) | [提示词](prompts/casual-back.txt) |
| 休闲装侧面 | [PNG](casual/bina-casual-tpose-side.png) | [提示词](prompts/casual-side.txt) |
| 工装正面 | [PNG](work/bina-work-tpose-front.png) | [提示词](prompts/work-front.txt) |
| 工装背面 | [PNG](work/bina-work-tpose-back.png) | [提示词](prompts/work-back.txt) |
| 工装侧面 | [PNG](work/bina-work-tpose-side.png) | [提示词](prompts/work-side.txt) |

每图一个完整视图，保留呆毛、头发、手部与鞋底；正背双臂水平展开，侧面统一朝画面右侧，与 V2 方向保持一致。侧面可见的是角色右侧，左耳饰与左腕表可能被遮挡，不应为了显示配饰而改换左右。

六张均为 **1254 × 1254 PNG**，采用白色背景、不透明 RGB，不含透明通道；背景不保证逐像素等于 `#FFFFFF`。实际尺寸、哈希、来源及生成记录见 [manifest.json](manifest.json)。

## 历史候选检查与测量口径

已逐张目视核对新版内弯发型、玫瑰茶棕色调、单根呆毛、左侧挽耳与金夹、单颗小虎牙、服装及左右不对称细节。侧面轮廓与衣摆高度尚未与正背面精确配准；独立生成的视图不保证严格正交或天然同尺度。

约 7.3 头身是生成目标，不是测量认证，呆毛不计入头高。新图尚未重新标点与测量；上级 `measurements/`、旧测量脚本中的 `LANDMARKS` 和 V0 白发图坐标只供历史复现，不得套用到 V3。后续应从正式采用的六视图重新标点，再计算比例。
