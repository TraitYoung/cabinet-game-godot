# Bina V3 概念图与自然站姿母图（已归档）

**正式采用入口：** 2026-11-08 用户已确认[以新工装正面为基准的两套服装六视图](../../../../assets/bina-tpose/v3/anatomy-locked/turnaround/README.md)，后续建模按该组实际比例和外貌制作。

本目录四张完整图与 `drafts/` 中四张中间稿已于 2026-11-08 归档。它们是此前通过内置 `image_gen` 生成的概念与自然站姿过程参考，保留用于追溯发色、表情、服装和生成步骤；正式外貌与比例以已批准六视图为准。

## 身份与来源

[原始身份要求](prompts/identity-lock.txt)和[视觉唯一真相源](../../../../config/persona_visual/bina.json)定义本版身份：19 岁成年女性、烟玫瑰茶灰棕柔软羽毛状锁骨发、内弯发尾、法式空气刘海、浅香槟内层挑染、角色自身左侧挽耳与左耳几何金夹、单根弧形呆毛、明亮蜜糖琥珀圆杏眼、俏皮微笑单侧露一颗小虎牙。

保留原有两套服装，服装来源为 [V2 休闲概念图](../v2-approved-sources/bina-casual.jpeg)、[V2 工装概念图](../v2-approved-sources/bina-work.jpeg)及其[来源说明](../../README.md)。V2 发型与脸部不作为最新身份定义。画风保持细腻动漫线稿与柔和材质明暗。

165cm、约 7.3 头身是生成目标，不是测量结论；头身目标从头骨顶部至鞋底计算，不包含呆毛高度。

## 早期输出（过程参考）

| 内容 | 过程参考 | 实际提示词 |
| --- | --- | --- |
| 休闲装三合一概念图 | [PNG](bina-casual-concept.png) | 下方完整迭代序列 |
| 工装三合一概念图 | [PNG](bina-work-concept.png) | [work-concept.txt](prompts/work-concept.txt) |
| 休闲装独立自然站姿母图 | [PNG](bina-casual-standing.png) | [casual-standing.txt](prompts/casual-standing.txt) |
| 工装独立自然站姿母图 | [PNG](bina-work-standing.png) | [work-standing.txt](prompts/work-standing.txt) |

休闲概念图的实际迭代顺序为：[casual-concept.txt](prompts/casual-concept.txt) → [casual-concept-refine.txt](prompts/casual-concept-refine.txt) → [casual-concept-final.txt](prompts/casual-concept-final.txt) → [casual-concept-tooth.txt](prompts/casual-concept-tooth.txt) → [casual-concept-smile.txt](prompts/casual-concept-smile.txt)。后两步处理嘴角牙尖与微笑；文件名中的 `final` 不代表最后采用步骤。`drafts/` 仅保留过程稿，不作为交付候选。

概念图为 **1678 × 937 PNG**，保留暖浅奶油背景及三合一排版；母图为 **1024 × 1536 PNG**，采用单人完整全身、白色背景。输出为不透明 RGB 图像，不含透明背景，白底也不保证所有像素均为精确 `#FFFFFF`。实际尺寸、哈希与来源记录见 [manifest.json](manifest.json)。

## 后续参考

[V3 T-pose 版本记录](../../../../assets/bina-tpose/v3/README.md)保留后续各阶段生成图。当前正式采用版的形象设计已确认；比例尚未重新标点与测量，Live2D 重建继续按项目计划完成。
