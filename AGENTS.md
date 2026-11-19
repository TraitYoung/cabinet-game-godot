# Current Project Definition

Axiodrasil 是一款基于 **TypeScript + React + Vite + PixiJS v8** 开发的 2D 俯视角皇城与国家治理模拟游戏（原生适配 **WSL2 开发 + 浏览器硬件加速渲染**，原 Godot 原型已归档在 `archive/godot-prototype` 分支）。

核心设计分为两个尺度：
1. **皇城管理（细尺度）**：玩家扮演「陛下」，在 2D 俯视角宫城中亲自走动、巡视、修缮/扩建宫署与城建地块，并与内阁大臣日常互动、旁听大臣之间的随机吐槽与议事。
2. **国家治理（粗尺度）**：通过正殿的舆图沙盘与奏折系统处理周边郡县与国政指标，国家层面的决策会具象反馈到皇城的物资、风貌与内阁对白中。

## 人物与世界观设定来源

- 内阁成员完整角色卡、口癖与节律设定保存在 `docs/characters/` 与 `docs/archive/bios/Axiodrasil_BIOS_V17.0.md`。
- 全阁 12 位核心与二/三等成员（Bina、Chizheng、Bit、Vinci、Taki、Jean、Tianji、Fukucho、Planck、Boming、Qianjin、Jiafa）已通过数据驱动结构实装。
- `docs/`、`assets/bina-live2d/`、`assets/bina-tpose/` 为历史资料、Live2D 模型与视觉参考；Vite 插件仅将 `assets/palace/` 与 `assets/characters/` 的 PNG 资源暴露与打包至 `/game-assets/`。

## 开发与 AI 协作规范（Web 栈）

- **技术栈**：**TypeScript (strict) + React 19 + Vite 8 + PixiJS v8**，测试使用 **Vitest**，包管理器使用 **pnpm**。
- **WSL2 + 浏览器工作流**：推荐在 WSL2 内部文件系统运行 `pnpm dev`（`vite --host`，监听 `5173`），并在 Windows 本机浏览器访问 `http://localhost:5173` 获得硬件加速 WebGL2 与中文输入法支持。
- **强制静态类型**：启用 `"strict": true`、`noUnusedLocals`、`noUnusedParameters`，禁止随意使用 `any`。
- **数据驱动**：角色资料、作息日程、对话、拌嘴与宫城布局统一放在 `src/data/`（`cabinetDatabase.ts`、`palaceLayout.ts`、`smallCourtyardLayout.ts`），禁止为单个内阁成员复制粘贴行为逻辑。
- **渲染与 UI 边界**：60fps 模拟、寻路与 PixiJS 渲染保留在 `src/game/` 中，React (`src/ui/`) 仅接收节流后的快照与对话框事件，禁止每帧触发 React 重渲染。
- **自检命令**：每次新增或修改代码后，运行类型检查、单元测试与构建确认无误：
  `pnpm exec tsc --noEmit && pnpm test && pnpm run build`
