# 唐长安大明宫真实考古图纸、复原模型与实景参考库

本目录收录自 Wikimedia Commons 获取的公开授权（CC0 / CC BY / CC BY-SA）大明宫考古总平面图、1:15 微缩复原模型实拍、博物馆木结构模型与遗址公园实景，供后续使用 `tools/seedream.py --image ...` 出图时作为真实历史建筑与空间比例依据。

## 关键考古空间与建筑参数（供提示词与关卡布局对齐）

- **整体格局**：平面呈「南宽北窄」梯形，占地约 3.2 平方公里，中轴严格对称，由南向北依次为：**丹凤门 → 外朝（含元殿）→ 中朝（宣政殿 + 中书/门下省）→ 内朝（紫宸殿、延英殿）→ 后苑（太液池、麟德殿）**。
- **含元殿（外朝正殿）**：建于龙首原高大夯土台基之上，呈**「凹」字形组合**——主殿面阔 11 间、进深 4 间（四周副阶周匝），前方左右对称配置**翔鸾阁**（东）与**栖凤阁**（西）及飞廊，殿前设**三条并行龙尾道台阶**。
- **宣政殿与两省**：位于含元殿北侧第二道宫墙之内，东侧紧邻门下省、弘文馆、史馆，西侧为中书省、殿中省、御史台。
- **紫宸殿（内朝正殿）**：位于宣政殿正北高地，以北进入内庭与皇家园林区。
- **麟德殿（宴会别殿）**：位于太液池西侧，由**前殿、中殿、后殿**前后毗连组成，两侧对称设**郁仪楼、结邻楼**与亭廊。
- **丹凤门（正南门）**：大明宫正南门，标志性的**一字排开五门道**城台与重檐庑殿门楼。
- **太液池**：分东西两池，西池中筑**蓬莱山**等仙山岛屿。

## 参考图索引（全部已本地验证）

| 文件 | 类型 | 画面内容与出图用途 | 授权 |
| --- | --- | --- | --- |
| [01-plan-ruins-zh.png](01-plan-ruins-zh.png) | 考古总平面图（中文） | 含丹凤门、含元殿、宣政殿、中书/门下省、紫宸殿、麟德殿、太液池完整平面方位；适合锁定俯视角地图空间关系 | CC0 |
| [02-plan-ruins-en.png](02-plan-ruins-en.png) | 考古总平面图（英文） | 同上英文标注版，适合直接喂给英文提示词生图参考 | CC0 |
| [03-palace-map-karta.jpg](03-palace-map-karta.jpg) | 宫城分区示意平面图 | 带水系、道路、殿宇屋顶标记的分区简图（含 500m 比例尺） | CC BY-SA 4.0 |
| [04-palace-model-overview-01.jpg](04-palace-model-overview-01.jpg) | 1:15 微缩模型实拍 | 大明宫遗址公园 1:15 彩绘建筑群模型（近景为麟德殿三连殿与双楼，远景为大明宫宫群）；最适合做唐风瓦顶、红柱白墙与连廊细节参考 | CC BY 2.0 |
| [05-palace-model-overview-02.jpg](05-palace-model-overview-02.jpg) | 1:15 微缩模型实拍 | 夯土宫墙、重楼宫门、院落重重屋宇的俯瞰群落实拍；适合俯视角宫城/值房/偏院参考 | CC BY 2.0 |
| [06-hanyuan-hall-model.jpg](06-hanyuan-hall-model.jpg) | 含元殿台基遗址实景 | 含元殿遗址夯土砖包多层大台基与坡道现状实景 | CC BY 2.0 |
| [07-hanyuan-hall-cg-restoration.jpg](07-hanyuan-hall-cg-restoration.jpg) | 含元殿复原 CG | 含元殿主殿、左右翔鸾/栖凤双阁与多层高台斜坡龙尾道的立体复原关系 | CC BY-SA 4.0 |
| [08-hanyuan-hall-base-model.jpg](08-hanyuan-hall-base-model.jpg) | 含元殿基址浮雕模型 | 清楚展示 11×4 柱网、「凹」字平面与双龙尾道基址结构 | CC BY-SA 4.0 |
| [09-zichen-hall-model.jpg](09-zichen-hall-model.jpg) | 紫宸殿钢架立面剪影 | 遗址原址 1:1 钢架屋脊、鸱吻与斗拱比例轮廓参考 | CC BY 2.0 |
| [10-linde-hall-model-01.jpg](10-linde-hall-model-01.jpg) | 麟德殿博物馆木质模型 | 前中后三殿毗连、双楼、回廊与台基栏杆的建筑结构细节 | CC BY-SA 3.0 |
| [11-danfeng-gate-real.jpg](11-danfeng-gate-real.jpg) | 丹凤门复原实景 | 经典五门道丹凤门城台、斗拱与庑殿顶正面比例参考 | CC BY 2.0 |
| [12-taiye-pool-real.jpg](12-taiye-pool-real.jpg) | 太液池实景 | 池岸石块、垂柳与池中蓬莱仙山岛景致参考 | CC BY-SA 3.0 |

完整来源 URL 与字节元数据见 [sources.json](sources.json)。

## 依据真实参考图出图示例

```powershell
# 示例 1：以真实 1:15 微缩建筑模型 + 平面图作为双参考，用 Seedream 5.5 出唐风俯视宫城图
python tools/seedream.py `
  --image docs/media/references/daming-palace/04-palace-model-overview-01.jpg docs/media/references/daming-palace/01-plan-ruins-zh.png `
  --prompt "严格参考图1的唐代大明宫红柱白墙灰瓦与连廊建筑制式、以及图2的大明宫中轴对称平面布局，绘制2D 3/4俯视角游戏地图插画，含丹凤门、含元殿凹字高台、东门下省值房、西工坊与太液池，无文字" `
  --size 2K `
  --out docs/media/palace-concepts/seedream/02-daming-authentic.png

# 示例 2：以丹凤门实景为参考，直接导出透明底建筑素材
python tools/seedream.py `
  --image docs/media/references/daming-palace/11-danfeng-gate-real.jpg `
  --prompt "参考丹凤门五门道城台与唐代庑殿顶制式，绘制2D手绘游戏用南宫门建筑素材，正面微俯视角，干净构图" `
  --transparent `
  --size 2K `
  --out docs/media/palace-concepts/seedream/prop-danfeng-gate.png
```
