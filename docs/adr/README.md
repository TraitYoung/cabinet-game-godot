# 架构决策记录

ADR 用来说明某项选择的背景、备选方案、决定和后果。它与操作指南、接口参考及阶段验收分开维护。

| 编号 | 决策 | 状态 |
| --- | --- | --- |
| [ADR-001](ADR-001-pain_level_calibration.md) | 痛感量化标尺与系统提示词约束 | 历史已采纳，原实施方式需结合当前代码理解 |

ADR-001 记录的是旧阶段模型解析与路由中的校准方法。当前 Bina 快速路径见 [agents/solo_fast.py](../../agents/solo_fast.py) 和 [agents/router.py](../../agents/router.py)，不能据原 ADR 推断当前仍使用多人物路由或模型化意图解析。

新增决策沿用递增编号，包含“状态、背景、决定、后果”；替代旧决策时保留旧记录并链接新记录。当前架构见[架构参考](../reference/architecture.md)。
