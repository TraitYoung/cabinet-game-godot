# Bina 定妆出图（ComfyUI + LoRA）

参考邻舍.EXE：角色卡挂 **LoRA** → ComfyUI 工作流注入 `LoraLoader` → 聊天里要自拍时真的出图。

## 视觉真相源（SSOT）

**唯一外貌真相源：** [`config/persona_visual/bina.json`](../../config/persona_visual/bina.json)

| 字段 | 职责 |
|------|------|
| `canon` | 人读设定（发色/发型/眼睛/常服/禁忌）；BIOS 与角色卡只引用摘要 |
| `appearance_prompt` 等 | 出图用英文底词，必须与 `canon` 一致 |
| BIOS / SillyTavern 卡 | **不是**外貌真相源；冲突时以本 JSON 为准 |

## 前置

### Windows 本机独立部署

本机安装目录为 `D:\AI\ComfyUI`，使用官方稳定版 `v0.44.0`、Python 3.12 独立虚拟环境和 CUDA 13.0 版 PyTorch。模型为作者发布的 `Illustrious-XL-v1.1.safetensors`，约 6.94 GB，放在 `models/checkpoints/`。安装目录、模型、缓存与生成结果均位于仓库外，不提交 Git。

首次安装的等价命令如下；仅在目录尚不存在时执行，不能覆盖已有安装：

```powershell
git clone --depth 1 --branch v0.44.0 https://github.com/Comfy-Org/ComfyUI.git D:\AI\ComfyUI
python -m venv D:\AI\ComfyUI\.venv
Set-Location D:\AI\ComfyUI
.\.venv\Scripts\python.exe -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cu130
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

官方模型：[Illustrious XL v1.1](https://huggingface.co/OnomaAIResearch/Illustrious-XL-v1.1)。本次下载固定到作者仓库修订 `8d966ec810874502d56a22ec9130dab6ef74c5ff`，完整文件的 SHA-256 应为 `536863e9f0c13b0ce834e2f8a19ada425ee4f722c0ad3d0051ec7e6adaa8156c`。下载与分段校验脚本保存在本机 `D:\AI\setup\download_illustrious.py`；代理按实际运行端口配置，本机此次使用 `http://127.0.0.1:7897`，不要照搬失效的旧端口。

日常使用：

1. 双击 `D:\AI\ComfyUI\Start-ComfyUI.cmd`，或在 PowerShell 执行 `& D:\AI\ComfyUI\Start-ComfyUI.ps1`。
2. 打开 `http://127.0.0.1:8188`，加载已保存的 `Bina-V3-base-test` 工作流。也可以将 `user/default/workflows/Bina-V3-base-test.json` 拖入界面。
3. 点击运行；图片保存在 `D:\AI\ComfyUI\output\bina-local\`。生成的 PNG 内嵌工作流，可拖回 ComfyUI 复现。
4. 用完双击 `Stop-ComfyUI.cmd`，或执行 `& D:\AI\ComfyUI\Stop-ComfyUI.ps1`。停止脚本核验进程路径和创建时间后才停止进程树，不接管其他程序占用的端口。

服务在后台运行，仅监听 `127.0.0.1:8188`；没有设置开机自启。启动日志为安装目录下的 `local-stdout.log`、`local-stderr.log`。需要前台排错时，先停止后台实例，再执行：

```powershell
Set-Location D:\AI\ComfyUI
.\.venv\Scripts\python.exe main.py --listen 127.0.0.1 --port 8188 --disable-auto-launch
```

测试工作流按 V3 设定提取简短外貌标签，使用 832 × 1216、28 步、CFG 5.5、`dpmpp_2m` / `karras`，不加载角色 LoRA。界面默认随机种子，切到 `fixed` 可复现指定种子。不要直接照搬完整的长篇外貌正文和加权负向词：本机测试中，完整提示词组合出现了明显的过饱和与粗线条，简短提示词对照能正常出图。该工作流验证底模出图能力，不代表已经锁定 Bina 的脸、服装或参考图细节，也不替代已批准的 V3 资源。

本机完整依赖清单为 `D:\AI\ComfyUI\requirements-local.lock.txt`，安装来源与哈希记录为 `local-deployment.json`，真实出图验收记录为 `D:\AI\deployment-report.json`。2026-11-10 已在 RTX 5070 Laptop GPU（约 12GB 显存）上验证 CUDA 实算、模型发现、HTTP 首页和 GPU 出图；最后一次 832 × 1216、28 步测试在模型已加载时用时约 14 秒。启动脚本的重复启动与进程树停止也经过验证。当前实例保留运行以便试用。

项目的聊天自动出图另需配置下方环境变量并准备真实的 Bina LoRA。当前角色配置中的 `bina.safetensors` 是待准备的文件名，不能视为模型已存在。本次独立部署不更改项目 `.env`，不启用聊天自动出图。

### Z-Image-Turbo 试用

本机另外安装了 [Z-Image-Turbo](https://huggingface.co/Tongyi-MAI/Z-Image-Turbo) 的 [ComfyUI 官方 INT8 工作流](https://docs.comfy.org/tutorials/image/z-image/z-image-turbo)。为适配约 12GB 显存，使用 `Comfy-Org/Z-Image-Turbo` 提供的 INT8 convrot 扩散模型和 FP8 mixed 文本编码器，不是 BF16 原始精度版本。三个文件合计约 12.17 GB：

| 安装路径（相对于 ComfyUI） | 文件 |
| --- | --- |
| `models/diffusion_models/` | `z_image_turbo_int8_convrot.safetensors` |
| `models/text_encoders/` | `qwen_3_4b_fp8_mixed.safetensors` |
| `models/vae/` | `ae.safetensors` |

在同一个 ComfyUI 界面加载 `Bina-Z-Image-Turbo-INT8` 工作流；也可拖入 `D:\AI\ComfyUI\user\default\workflows\Bina-Z-Image-Turbo-INT8.json`。使用 832 × 1216、8 步、CFG 1、`res_multistep` / `simple`、AuraFlow shift 3，参数来自官方模板。Turbo 工作流采用零化负向条件，不沿用 SDXL 的 CFG 5.5 和加权负向提示词。

提示词按 V3 设定组织为自然语言，图片输出至 `D:\AI\ComfyUI\output\bina-zimage-turbo\`。该工作流是文生图，没有输入 V3 参考图，也未加载 Bina LoRA，不能视为已锁定角色形象。

官方打包文件固定到修订 `6fc90a3b1b653e935a0d175e260736de25b84df5`。下载与 SHA-256 校验脚本为 `D:\AI\setup\download_zimage_turbo.py`，模型来源及校验记录为 `D:\AI\z-image-turbo-models.json`；API 工作流位于 `D:\AI\workflows\bina-zimage-turbo-api.json`。这些本机资源均不提交 Git。

2026-11-10 在同一台 RTX 5070 Laptop GPU 上完成两次真实出图，种子分别为 `20261110`、`20261111`：首次从旧模型释放后加载并生成约 12.05 秒，后续一次约 8.08 秒。时间包含队列轮询开销，仅代表这两次 832 × 1216、8 步测试，不是跨模型统一基准。图片为 `test_00001_.png`、`test_00002_.png`，请求、系统信息和完整历史记录见 `D:\AI\zimage-test-report.json`。图像已人工查看；耳饰、挑染和服装细节仍与 V3 参考存在差异。

#### V3 参考图图生图

另存了 `Bina-Z-Image-Turbo-Reference` 工作流。它将已保留的 V3 发尾空气感修订版 v4 三栏图原样复制到 `D:\AI\ComfyUI\input\bina-v3-airy-ends-v4.png`，再通过 `LoadImage → ImageScale → VAEEncode` 生成初始潜空间，替代文生图中的空潜空间。推理尺寸为 1664 × 944，不裁剪原图；沿用 INT8 模型、FP8 编码器、8 步、CFG 1 和官方采样参数，没有额外安装模型。

在界面加载 `Bina-Z-Image-Turbo-Reference`，确认 `LoadImage` 选择上述参考图，修改 `KSampler` 的 `denoise` 比较重绘强度。默认是 `0.35`，界面种子默认随机；对照测试固定为 `20261110`。该方法主要保留并重绘原图构图，不是独立的身份参考适配器，也不能据此声称换姿势、换场景后仍能锁定 Bina。

2026-11-10 完成两次真实测试并查看结果：`denoise=0.35` 约 16.16 秒，`denoise=0.60` 约 12.12 秒，时间包含轮询开销。前者较好保留布局与外貌，后者袖型、站姿和耳饰变化更明显；两张的耳夹细节均未完全保持。这只是各一次的样图结果，不代表整体成功率。

输出为 `D:\AI\ComfyUI\output\bina-zimage-reference\denoise-035_00001_.png` 和 `denoise-060_00001_.png`，内嵌对应工作流。参考图来源与 SHA-256 记录在 `D:\AI\zimage-reference-source.json`，完整请求与执行历史见 `D:\AI\zimage-reference-report.json`。可导入工作流为 `user/default/workflows/Bina-Z-Image-Turbo-Reference.json`，API 版本为 `D:\AI\workflows\bina-zimage-reference-api.json`。原始 V3 文件与项目角色配置均未改动，这些结果不替代已批准的形象资源。

上述 Z-Image-Turbo 工作流需要独立的扩散模型、文本编码器和 VAE 加载节点。项目现有 `modules/image_gen/workflow.py` 仍是 SDXL checkpoint 工作流，仅修改 `AX_COMFYUI_CKPT` 不能将聊天自动出图切换到 Z-Image-Turbo。

### 从仓库调用本机 ComfyUI 生成素材

ComfyUI 保持安装在 `D:\AI\ComfyUI`，**不移动、不复制进仓库**：模型权重约 19 GB（Illustrious-XL 6.94 GB + Z-Image-Turbo 三件套 12.17 GB）、虚拟环境里写死了解释器路径、目录本身是上游 Git 仓库（`v0.44.0`），搬进工作树既撑大仓库，也会和项目代码互相干扰。仓库只通过 HTTP API 连接它。

连接代码在 [`modules/comfyui/client.py`](../../modules/comfyui/client.py)（`ComfyClient`：提交、轮询、取图），生成素材的命令行入口是 [`scripts/generate_bina_assets.py`](../../scripts/generate_bina_assets.py)，默认端点 `http://127.0.0.1:8188`。

```powershell
# 1. 启动本机 ComfyUI（已在运行会原样返回）
& D:\AI\ComfyUI\Start-ComfyUI.ps1

# 2. 确认连接、显卡与可用模型
python scripts\generate_bina_assets.py --check

# 3. 文生图：沿用工作流内的提示词，只换种子
python scripts\generate_bina_assets.py --seed 20261111 --name bina-casual

# 4. 换场景：直接给正向提示词，可一次出多张（种子依次 +1）
python scripts\generate_bina_assets.py --prompt "1girl, solo, young adult woman, cream cardigan, sitting by a window, ..." --count 2

# 5. 参考图重绘：保留已有美术图的构图与配色，只调 denoise
python scripts\generate_bina_assets.py --workflow D:\AI\workflows\bina-zimage-reference-api.json `
  --ref-image docs\media\v3-casual-closed-smile-2026-11-09\bina-casual-concept-airy-ends-v4.png `
  --denoise 0.45 --seed 20261111 --name bina-ref
```

脚本可覆盖工作流文件、正/负向提示词、宽高、步数、CFG、denoise、种子、张数和参考图；改尺寸时自动改写空潜空间节点（文生图）或 `ImageScale` 节点（参考图重绘）。参考图按内容哈希复制到 `D:\AI\ComfyUI\input\`，不改动原图。

结果写到 `output/bina-assets/<name>-<seed>.png`，同名 `.json` 记录图片 SHA-256、种子、步数、CFG、denoise、完整提示词、工作流文件哈希与参考图来源；该目录不进 Git。ComfyUI 自己的 `output/bina-assets/` 下也保留一份，PNG 内嵌工作流，可拖回界面复现。

2026-11-11 实测（RTX 5070 Laptop，12.8 GB 显存，ComfyUI v0.44.0）：`--check` 正确枚举 `Illustrious-XL-v1.1.safetensors`、`z_image_turbo_int8_convrot.safetensors`、`qwen_3_4b_fp8_mixed.safetensors` 与 `ae.safetensors`；文生图 832 × 1216、8 步、种子 `20261111` 冷启动到落盘 29 秒（含模型加载）；参考图重绘 `denoise=0.45`、1664 × 944 一次成功。两张图都已人工查看，可作为试做素材，但不替代已批准的形象资源。

注意：

- 这是调用已部署的 ComfyUI 生成素材，不是聊天自动出图。聊天里要自拍仍需 `AX_IMAGE_GEN_ENABLED=1`、`AX_COMFYUI_CKPT` 指向本机底模，以及真实的 Bina LoRA（`models/loras/bina.safetensors` 目前不存在），见下方「项目接入前置条件」。
- 项目自带工作流只支持 checkpoint 结构；Z-Image-Turbo 的 UNET / CLIP / VAE 三分支工作流只能按 `D:\AI\workflows\*.json` 重放。
- 这些图没有加载角色 LoRA，不能视为已锁定 Bina 形象；进入正式资源前仍需人工挑选。

### 项目接入前置条件

1. 本机安装并启动 [ComfyUI](https://github.com/comfyanonymous/ComfyUI)，默认 `http://127.0.0.1:8188`
2. 准备好 **Bina 专用 LoRA**（你自己训练或购买），放入：
   `ComfyUI/models/loras/bina.safetensors`（文件名可改）
3. 准备底模 checkpoint（默认配置为 SDXL 名，可按本机文件改）

## 定妆配置

编辑 [`config/persona_visual/bina.json`](../../config/persona_visual/bina.json)：

| 字段 | 含义 |
|------|------|
| `canon` | 中文定妆正文（SSOT） |
| `loras[].path` | 相对 `models/loras/` 的文件名 |
| `loras[].weight` | 强度，常见 0.6–0.9 |
| `loras[].trigger_word` | 训练时的触发词（必填才锁得住脸） |
| `appearance_prompt` | 外貌底词（须对齐 `canon`） |
| `selfie_prompt` | 自拍构图标签 |
| `negative_prompt` | 负向 |

也可用环境变量覆盖单个 LoRA：

```bash
AX_IMAGE_GEN_ENABLED=1
AX_COMFYUI_URL=http://127.0.0.1:8188
AX_COMFYUI_CKPT=你的底模.safetensors
AX_BINA_LORA=bina.safetensors
AX_BINA_LORA_TRIGGER=bina_char
AX_BINA_LORA_WEIGHT=0.85
```

## 使用

1. Linux 栈：`./start.sh`（后端 :8000）
2. ComfyUI 保持运行
3. Solo 对 Bina 说：「发一张自拍给我」
4. 回复文案后会附 `![Bina selfie](/api/v1/images/file/...)` ，前端直接显示图

手动调试：

```bash
curl -s http://127.0.0.1:8000/api/v1/images/persona/bina
curl -s -X POST http://127.0.0.1:8000/api/v1/images/generate \
  -H 'Content-Type: application/json' \
  -d '{"persona_id":"bina","mode":"selfie"}'
```

## 说明

- 一致性主要靠 **LoRA + trigger**；只改提示词不够。
- 当前工作流是 CheckpointLoaderSimple + LoraLoader（SDXL 系）；若你用 Anima/UNET 工作流，可后续再加自定义 workflow JSON。
- 生成文件落在 `data/generated/`（或 `AX_IMAGE_OUT_DIR`）。
