# Current Project Definition

Axiodrasil 是一款基于 **Godot 4.7.2（GDScript）** 开发的 2D 俯视角皇城与国家治理模拟游戏。

核心设计分为两个尺度：
1. **皇城管理（细尺度）**：玩家扮演「陛下」，在 2D 俯视角宫城中亲自走动、巡视、修缮/扩建宫署与城建地块，并与内阁大臣日常互动、旁听大臣之间的随机吐槽与议事。
2. **国家治理（粗尺度）**：通过正殿的舆图沙盘与奏折系统处理周边郡县与国政指标，国家层面的决策会具象反馈到皇城的物资、风貌与内阁对白中。

## 人物与世界观设定来源

- 内阁成员完整角色卡、口癖与节律设定保存在 `docs/characters/` 与 `docs/archive/bios/Axiodrasil_BIOS_V17.0.md`。
- 第一阶段原型优先实装 4 位核心代表：**Bina**、**Chizheng**、**Bit**、**Vinci**；后续按数据驱动模板逐步补齐其余内阁成员。
- `docs/`、`assets/bina-live2d/`、`assets/bina-tpose/` 为历史资料与视觉参考，已通过 `.gdignore` 隔离在 Godot 资源导入之外。

## 开发与 AI 协作规范（Godot 4.7.2）

- **引擎与环境**：Windows 原生运行 Godot `4.7.2-stable`（本机路径 `D:\Godot_v4.7.2-stable_mono_win64\Godot_v4.7.2-stable_mono_win64_console.exe`）。
- **脚本语言**：统一使用 **GDScript（Godot 4.x 语法）**，禁止使用 Godot 3.x 旧 API（如 `KinematicBody2D`、旧 `TileMap`、旧 `Tween`）。
- **强制静态类型**：所有 `.gd` 脚本必须为成员变量、函数参数和返回值标注明确类型（如 `var move_speed: float = 210.0`），确保错误在编译/加载期暴露。
- **数据驱动**：角色资料、作息日程、对话与双人互动台词统一放在 `scripts/data/` 或 `.tres` 资源中，禁止为单个内阁成员复制粘贴整套行为脚本。
- **场景引用安全**：尽量通过导出的节点引用、信号总线（`DialogueBus`）或显式节点路径交互，避免在深层 UI/场景里写脆弱的硬编码相对路径。
- **自检命令**：每次新增或修改脚本后，运行 Godot 无头校验命令确认项目能无报错加载：
  `& "D:\Godot_v4.7.2-stable_mono_win64\Godot_v4.7.2-stable_mono_win64_console.exe" --headless --path . --quit-after 10`
