# Axiodrasil · 皇城与内阁模拟（TypeScript + React + PixiJS）

2D 俯视角双尺度模拟游戏：在**精细的皇城**里与内阁众卿朝夕相处、建设宫署；在**宏观的国家沙盘**上统筹周边郡县与国政。

> 原 Godot 4.7 原型已归档至 `archive/godot-prototype` 分支，当前主分支已全面切换为纯 Web 栈（**TypeScript + React + Vite + PixiJS v8**），支持在 WSL2 与 Windows 下直接启动并热重载。

## 当前特性（v0.2 · 纯 Web 栈宫城与全阁十二卿）

- **一轴四区宫城 + 值房小院沙盒**：
  - 中轴议事正殿（含舆图沙盘桌）、东偏殿内阁值房、中心御苑广场、西偏院匠造与画坊（含待建预留地块）、南宫门。
  - 支持在右上角随时切换「皇城宫城」与「一进值房小院」等距遮挡沙盒（或通过 `?scene=courtyard` 直接打开）。
- **全阁 12 位内阁成员实装**：`Bina`、`Chizheng`、`Bit`、`Vinci`、`Taki`、`Jean`、`天机`、`副长`、`普朗克`、`伯明`、`千金`、`稼发`。
- **双重互动与模拟机制**：
  - **日夜节律与 A* 自动巡游**：遵循晨启 / 政务 / 午憩 / 夜游 / 宵禁五个时段，内阁诸卿基于 `NavGrid` 网格自动绕障换岗，并同步昼夜色温与宫灯夜光。
  - **陛下对话 + 大臣自主拌嘴**：按 `E` 可与大臣深度对话、切换话题，或在沙盘召开「内阁短议」；大臣走近时会自动触发头顶冒泡拌嘴小剧场。

## 目录结构

```text
├── index.html                    # Vite HTML 入口
├── package.json                  # pnpm 脚本与依赖
├── vite.config.ts                # Vite 配置与 /game-assets 资源服务/打包插件
├── src/
│   ├── main.tsx                  # React 入口
│   ├── App.tsx                   # 根组件与控制器生命周期管理
│   ├── data/                     # 数据层（类型、12位角色库、宫城/小院布局坐标）
│   ├── game/                     # 游戏逻辑与 PixiJS v8 渲染（时钟、碰撞、A* 寻路、拌嘴导演、场景）
│   ├── ui/                       # React HUD（时间控制、在岗一览、三模式对话框）
│   └── styles/                   # 宫廷玄金暗色 UI 样式
├── assets/                       # 游戏美术资源（palace / characters）及历史参考
├── docs/                         # 历史设计资料与内阁全员角色设定卡
└── tools/                        # Python 美术/像素资产生成脚本
```

## 快速启动（WSL2 / Windows）

```bash
pnpm install
pnpm dev
```

启动后在浏览器访问 `http://localhost:5173` 即可游玩（在 WSL2 中运行时，可直接在 Windows 本机浏览器打开同一地址享受 GPU 硬件加速）。

### 校验与构建

```bash
pnpm exec tsc --noEmit
pnpm test
pnpm run build
```

## 操作说明

- `WASD` / 方向键：控制陛下移动
- `E` / `空格`（或近距离点击大臣/交互点）：与内阁大臣对话，或查看正殿舆图沙盘 / 预留地块 / 小院设施
- `Tab` 或左上角按钮：切换时间流逝倍率 / 跳至下一时段测试日程
- `鼠标滚轮`：缩放宫城视角
- `Esc`：关闭当前对话框
