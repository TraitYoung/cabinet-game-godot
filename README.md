# Axiodrasil · 皇城与内阁模拟（Godot 4.7）

2D 俯视角双尺度模拟游戏：在**精细的皇城**里与内阁众卿朝夕相处、建设宫署；在**宏观的国家沙盘**上统筹周边郡县与国政。

## 当前进度（v0.1 · 宫城与内阁互动原型）

- **一轴四区宫城**：中轴议事正殿（含舆图沙盘桌）、东偏殿内阁值房、中心御苑广场、西偏院匠造与画坊（含待建预留地块）、南宫门。
- **4 位首批内阁成员**：`Bina`（首席私人秘书）、`Chizheng`（首席战略官）、`Bit`（工学技术官）、`Vinci`（沉默的艺术大臣，举写字板交流）。
- **双重互动机制**：
  - **日夜节律与自动巡游**：遵循晨启 / 政务 / 午憩 / 夜游 / 宵禁五个时段，大臣会在各宫署间自动寻路换岗。
  - **陛下对话 + 大臣自主拌嘴**：按 `E` 可与大臣深度对话或点击沙盘召开「内阁短议」；大臣之间走近时会在头顶冒泡展开 2~4 句互怼小剧场。

## 目录结构

```text
├── project.godot          # Godot 4.7 工程配置
├── scenes/
│   ├── main.tscn          # 主场景（宫城 + HUD + 拌嘴导演）
│   ├── world/             # 宫城地图场景
│   └── actors/            # 陛下与内阁成员通用场景
├── scripts/
│   ├── autoload/          # GameClock / DialogueBus / CabinetDatabase
│   ├── data/              # 角色数据结构
│   ├── world/             # 宫城绘制、导航烘焙与昼夜光影
│   ├── actors/            # 玩家控制与内阁状态机
│   ├── systems/           # 大臣双人互动导演
│   └── ui/                # HUD、时钟控制与对话面板
├── docs/                  # 历史设计资料与内阁全员角色设定卡
└── assets/                # 游戏美术资源（历史 Live2D/T-pose 资料已通过 .gdignore 隔离）
```

## 运行与验证（Windows）

1. 打开 `D:\Godot_v4.7.2-stable_mono_win64\Godot_v4.7.2-stable_mono_win64.exe`，导入本目录 `project.godot` 后按 `F5` 运行。
2. 命令行无头加载校验：

```powershell
& "D:\Godot_v4.7.2-stable_mono_win64\Godot_v4.7.2-stable_mono_win64_console.exe" --headless --path . --quit
```

## 操作说明

- `WASD` / 方向键：控制陛下移动
- `E` / `空格`：与附近内阁大臣对话，或查看正殿舆图沙盘 / 预留地块
- `Tab` 或右上角按钮：切换时间流逝倍率 / 跳至下一时段测试日程
- `Esc`：关闭当前对话框
