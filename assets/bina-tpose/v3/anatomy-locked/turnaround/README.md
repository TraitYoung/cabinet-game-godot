# Bina 正式采用形象：两套服装 T-pose 三视图

**采用状态：已批准。** 2026-11-08 用户确认：“很好，可以采用这一版的形象设计了”。正式采用范围为下表六张图，工装正面是人物比例、头部大小和线稿的主基准；两套服装后续建模与衍生素材以本组为准。采用记录与文件哈希见 [manifest.json](manifest.json)，配置入口见 [approved_design](../../../../../config/persona_visual/bina.json)。

2026-11-08 按用户要求，以[新工装正面](../bina-work-tpose-front.png)为人物身份、实际身体比例、头部大小、线稿与构图基准，已补齐工装背面、侧面及休闲装三视图，共新增五张。使用内置 `image_gen`，逐张生成并原样保存。旧图仅补充服装结构，不重新定义人物比例。

## 当前文件

| 服装 | 正面 | 背面 | 朝右侧面 |
| --- | --- | --- | --- |
| 工装 | [沿用基准 PNG](../bina-work-tpose-front.png) | [PNG](bina-work-tpose-back.png) | [PNG](bina-work-tpose-side.png) |
| 休闲装 | [PNG](bina-casual-tpose-front.png) | [PNG](bina-casual-tpose-back.png) | [PNG](bina-casual-tpose-side.png) |

本组六个文件均为 1254 × 1254 RGB PNG，单人、白色背景、完整全身。正背双臂水平展开；侧面保持真实 T-pose，手臂沿视线方向重叠。露肩与吊带位于角色右侧，金色耳夹位于左耳；工装腕表、裙衩与垂链位于左侧，侧视时遵循遮挡关系。

## 生成记录

- [工装背面提示词](prompts/work-back.txt)
- [工装侧面提示词](prompts/work-side.txt)
- [休闲装正面提示词](prompts/casual-front.txt)
- [休闲装背面初次尝试](prompts/casual-back.txt)：三张参考，两次连接失败，无输出。
- [休闲装背面最终提示词](prompts/casual-back-compact.txt)：使用工装背面与休闲正面两张直接参考，成功生成。
- [休闲装侧面提示词](prompts/casual-side.txt)：首次连接失败，服务恢复后同提示词重试成功。

来源顺序、尺寸和 SHA-256 见 [manifest.json](manifest.json)。已逐张目视核对单根呆毛、发色、头部大小、服装、姿势、全身入画和左右细节。本组没有像素后处理，也尚未重新进行人体标点测量。侧面轮廓与正背面并非精确配准，生成图不保证背景每个像素均为精确 `#FFFFFF`；“保持比例”以实际基准图为目标，不根据头身比数字重新拉伸人物。
