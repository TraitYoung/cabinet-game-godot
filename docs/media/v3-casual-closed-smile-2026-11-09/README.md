# Bina V3 休闲装去 AI 塑料感与闭口微笑基准图 (2026-11-09)

本目录记录 2026-11-09 针对“嘴角牙齿贴片瑕疵”与“AI 过度渲染塑料油腻感”重构提示词后的基准生成图。

## 当前保留的三栏概念图

2026-11-09 用户确认保留发尾空气感修订图 v4，并要求提交至 GitHub。本目录保留各修订阶段、实际提示词与生成记录；修复前原图按要求仅在本地归档。

新增[发尾空气感修订图 v4](bina-casual-concept-airy-ends-v4.png)：以整洁发型版 v3 为参考，仅在发尾增加少量轻盈层次和发束间隙，保持整齐轮廓与贴颈内弯。实际提示词见[发尾修订提示词](concept-airy-ends-v4-prompt.txt)，来源、尺寸和哈希见[生成记录](concept-airy-ends-v4-manifest.json)。v3 保留供对照，v4 已获用户确认。

新增[整洁发型修订图 v3](bina-casual-concept-tidy-hair-v3.png)：以面部修订图 v2 为参考，按用户要求整理三栏碎发与飘散发束，收拢为顺重力垂落、贴颈内弯的整洁发型，保留单根呆毛。实际提示词见[发型修订提示词](concept-tidy-hair-v3-prompt.txt)，尺寸、来源及哈希见[生成记录](concept-tidy-hair-v3-manifest.json)。v2 仍保留供对照，v3 待用户审阅。

2026-11-09 用户要求保留面部修订图，并归档修复前的三栏原图。修订图减小了中间头像的倾斜角度，协调眼线、面部中轴和双眼透视，保留闭嘴微笑。

- [面部修订图](bina-casual-concept-face-fixed-v2.png)：1672 × 941 PNG。
- [实际修复提示词](concept-face-fixed-v2-prompt.txt)与[生成记录](concept-face-fixed-v2-manifest.json)。
- [修复前原图、提示词和生成记录](../archive/v3-casual-concept-before-face-fix-2026-11-09/README.md)：已归档，仅作过程对照（本地保留，不上传 GitHub）。

下方独立角色图及其生成记录仍保留在本目录。

## 解决的问题
1. **嘴部瑕疵根治**：彻底消除原提示词强制要求单侧小虎牙所导致的深色孔洞与白色三角贴片，改为干净自然的微抿微笑弧线。
2. **去 AI 塑料感 / 转向 2D 动漫手绘质感**：
   - 负向词压制 `plastic skin`, `oily face`, `3D CGI render`, `over-rendered`；
   - 正向词引入 `Kyoto Animation aesthetic`, `crisp delicate lineart`, `soft matte cel-shading`；
   - 彻底摆脱泛滥的油腻高光与杂乱噪点，呈现通透清爽的二次元商业番剧原画质感。

## 归档文件
- `bina-casual-closed-smile.png`：生成原图（1024 × 1536 PNG）
- `prompt.txt`：正向提示词
- `negative_prompt.txt`：负向提示词
- `manifest.json`：生成元数据与校验哈希
