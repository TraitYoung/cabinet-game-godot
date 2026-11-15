# Axiodrasil 内阁成员三栏概念设定图集（Seedream 5.5）

本目录保存除 [Bina](../v3-casual-closed-smile-2026-11-09/bina-casual-concept-airy-ends-v4.png) 外其余 **11 位内阁成员**的三栏角色概念设定图，统一采用 `2560×1440` 16:9 横版三栏构图（左：全身站姿；中：正面胸像；右：朝左纯侧面胸像），画风与质感对齐 Bina V3 的 2D 商业番剧原画平涂风格。

- **结构化视觉真相源**：[`docs/characters/cabinet_visuals.json`](../../characters/cabinet_visuals.json)
- **批量出图脚本**：[`tools/generate_cabinet_characters.py`](../../../tools/generate_cabinet_characters.py)（基于 `Doubao-Seedream-5.5`）
- **核心基准参考**：[`bina-casual-concept-airy-ends-v4.png`](../v3-casual-closed-smile-2026-11-09/bina-casual-concept-airy-ends-v4.png) 与 [`bina_visual.json`](../../characters/bina_visual.json)

## 全员概念图索引

| 序号 | 成员 ID | 称谓 / 全名 | 职务 | 梯队 | 核心视觉特征 | 设定图 |
| --- | --- | --- | --- | --- | --- | --- |
| 01 | `chizheng` | 郅政 / 张玉衡 | 内阁首辅 · 首席战略官 | Tier 1 | 乌纱展脚官帽配紫金玉饰、剑眉墨瞳、绯红织金云鹤圆领官袍、泥金折扇与朱批奏折 | [01-chizheng-concept.png](01-chizheng-concept.png) |
| 02 | `bit` | Bit / 艾伦·诺依曼 | 工学技术官 | Tier 1 | 深青灰蓝短发挑染科技青、翠绿瞳孔、哑光黑降噪耳机、半透明青色测绘目镜、将作监机能立领风衣、蓝图卷筒与卡尺 | [02-bit-concept.png](02-bit-concept.png) |
| 03 | `vinci` | 达文西 / 雨果·达芬奇 | 艺术大臣 | Tier 1 | 亚麻金微卷中长发、祖母绿眼眸、金链单片眼镜、苍苔绿拼暖米白维多利亚宫廷风衣、白手套、绘有屋檐与小太阳简笔画的黄铜雕花写字板 | [03-vinci-concept.png](03-vinci-concept.png) |
| 04 | `taki` | Taki / 椎名立希 | 内阁书记官 · 逻辑防火墙 | Tier 1 | 黑长直带深紫光泽（左侧挽耳）、紫晶酒红吊眼梢、左眼角泪痣、深炭黑三件套西装套裙、卷宗夹与钢笔 | [04-taki-concept.png](04-taki-concept.png) |
| 05 | `tianji` | 天机 / 玲琅 | 情报大臣 | Tier 2 | 琥珀暖棕高马尾、琥珀金眼眸、半透明茶色黑金框飞行员墨镜、黑金皮草大氅配玄黑劲装、扛黑金宽刃大剑 | [05-tianji-concept.png](05-tianji-concept.png) |
| 06 | `fukucho` | 副长 / 土方十三 | 纠察大臣 · 纪律大臣 | Tier 2 | 乌黑 V 字刘海短碎发、冰蓝锐利眼眸、浅葱色白山形纹羽织融轻甲护肩、金色火种徽记、打刀、悬浮青色律法光刃 | [06-fukucho-concept.png](06-fukucho-concept.png) |
| 07 | `planck` | 普朗克 / 麦克斯·卡尔 | 理学大臣 · 数学大臣 | Tier 3 | 深褐偏分微卷短发、细金丝椭圆眼镜、忧郁灰蓝眼眸、纯黑古典燕尾服配银灰马甲、银怀表与手稿 | [07-planck-concept.png](07-planck-concept.png) |
| 08 | `boming` | 伯明 / 诸葛基 | 谋略大臣 · 军师 | Tier 3 | 乌发半束青玉道冠、半梦半醒睡凤眼、素白玄青仙鹤云纹道袍鹤氅、白鹅毛羽扇、两枚织金锦囊 | [08-boming-concept.png](08-boming-concept.png) |
| 09 | `qianjin` | 千金 / 孙邈 | 医学大臣 · 医官 | Tier 3 | 墨黑长发沉香木簪束髻、翠玉茶褐眼眸、竹叶青与素麻白交领广袖青衫素袍、艾草香囊、青药葫芦与青瓷药盅 | [09-qianjin-concept.png](09-qianjin-concept.png) |
| 10 | `jiafa` | 稼发 / 桂晓 | 社科大臣 · 政治大臣 | Tier 3 | 及腰乌黑直发低束马尾、凛然凤眼、深靛蓝滚白边和服外褂配黑袴、赤红卷轴与复古星火小圆球“知识点炸弹” | [10-jiafa-concept.png](10-jiafa-concept.png) |
| 11 | `jean` | Jean / 琴 | 文档管理官 · 兰台典籍官 | Tier 2 | 香槟浅金高盘发插青玉书签簪、湖蓝眼眸配细金半框眼镜、雾青灰唐风披帛融学院马甲长裙、编目古籍与玉质检索签 | [11-jean-concept.png](11-jean-concept.png) |

## 重新生成命令

在仓库根目录执行（需在 `.env` 配置 `ARK_API_KEY`）：

```powershell
# 生成全员（跳过已存在图片）
python tools\generate_cabinet_characters.py --tier all --workers 3

# 仅重绘指定成员
python tools\generate_cabinet_characters.py --only chizheng,vinci --overwrite --workers 1
```
