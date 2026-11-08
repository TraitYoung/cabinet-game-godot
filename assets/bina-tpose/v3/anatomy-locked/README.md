# V2 身体与 V3 头部特征转移

**2026-11-08 已正式采用：** 本页新工装正面及以其为基准补齐的[两套服装六视图](turnaround/README.md)。工装正面为比例主基准，最终休闲装正面使用 `turnaround/` 中的版本。

2026-11-08 使用内置 `image_gen`，以 [V2 工装正面 T-pose](../../archive/v2/work/bina-work-tpose-front.png)为身体、比例、服装和线稿基准，仅请求应用 [V3 工装概念图](../../../../docs/media/archive/v3-design-drafts/bina-work-concept.png)的头部特征。

[生成图](bina-work-tpose-front.png)为 1254 × 1254 RGB PNG，单人正面 T-pose、白色背景。保留原图锁骨发轮廓，更新玫瑰茶灰棕发色、浅香槟内层高光、单根弧形呆毛、琥珀眼、单颗小虎牙和角色左耳金夹。以 V2 实际尺寸为准，没有为了数字上的 7.3 头身重新缩放身体。

[实际提示词](prompts/work-front.txt)与[来源及对照记录](manifest.json)已保存。输出原样复制，无像素后处理。

同尺寸对照中，肩线、臂展、腰线、腿部和鞋的位置保持一致；头部外的前景阈值掩膜交并比约为 99.50%，个别采样边缘存在 1–2 像素差异。这是生成稿，不能称为身体逐像素完全一致或经过认证的 100% 解剖锁定。背景也包含少量近白像素，未达到逐像素统一 `#FFFFFF`。

## 已归档过程稿

独立生成的 1024 × 1024 休闲装正面、实际提示词及当时对照结论已移至[试稿归档](../../archive/v3-casual-front-study/README.md)。正式休闲装正面使用[六视图中的版本](turnaround/bina-casual-tpose-front.png)。
