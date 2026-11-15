"""生成中式隋唐风格皇宫概念设计图（支持本机 ComfyUI Z-Image / Flux.1 Dev 与火山方舟 Doubao-Seedream-5.5）。

用法示例：
    # 1. 使用 Doubao-Seedream-5.5（需在 .env 配置 ARK_API_KEY）
    python tools\\generate_palace_concepts.py --backend seedream

    # 2. 使用本机 ComfyUI Z-Image-Turbo（需先启动 ComfyUI: http://127.0.0.1:8188）
    python tools\\generate_palace_concepts.py --backend zimage

    # 3. 使用本机 ComfyUI Flux.1 Dev FP8（需先启动 ComfyUI: http://127.0.0.1:8188）
    python tools\\generate_palace_concepts.py --backend flux --only 02-suitang-palace-topdown-game

    # 4. 混合管线：Seedream 5.5 出母图 -> 本机 Flux.1 Dev FP8 精修
    python tools\\generate_palace_concepts.py --backend hybrid --denoise 0.35
"""

from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from flux_refine import refine_image as flux_refine_image
from seedream import generate_image as seedream_generate_image

COMFY_URL = "http://127.0.0.1:8188"
REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = REPO_ROOT / "docs" / "media" / "palace-concepts"

CONCEPTS = [
    {
        "name": "01-suitang-palace-aerial",
        "width": 1344,
        "height": 768,
        "seedream_size": "2560x1440",
        "seed": 2026111401,
        "prompt": (
            "Architectural concept art of a grand Sui and Tang dynasty Chinese imperial palace complex "
            "seen from a high 3/4 aerial isometric overview. Monumental Daming Palace Hanyuan Hall style: "
            "elevated white-stone rammed-earth terrace with grand ceremonial stone staircases, massive "
            "vermilion timber pillars, deep overhanging eaves with bold Dougong brackets, dark slate-gray "
            "ceramic tile roofs topped with golden Chiwen ridge ornaments, white plaster walls, symmetrical "
            "left and right covered corridors enclosing a lush central courtyard garden with a lotus pond "
            "and stone bridge. Warm golden morning sunlight, crisp architectural linework, richly detailed "
            "2D painted game environment design sheet, clean layout, no modern elements."
        ),
    },
    {
        "name": "02-suitang-palace-topdown-game",
        "width": 1280,
        "height": 768,
        "seedream_size": "2560x1536",
        "seed": 2026111402,
        "prompt": (
            "2D top-down RPG game environment map illustration in the cozy handcrafted spirit of Stardew Valley "
            "meets Sui and Tang dynasty Chinese imperial architecture. Overhead 3/4 top-down tilemap view of "
            "a walled palace courtyard: central grand hall at top with vermilion columns and sweeping gray-blue "
            "tiled roof, stone flagstone plaza with warm lantern posts, eastern wooden cabinet study wing, "
            "western artisan workshop courtyard with open stone plots, tranquil lotus pond and ginkgo trees in "
            "the center, southern arched palace gate at bottom. Crisp readable 2D game art, warm harmonious "
            "colors, clean walkable paths, no text, no UI."
        ),
    },
    {
        "name": "03-suitang-throne-sandbox-hall",
        "width": 1280,
        "height": 768,
        "seedream_size": "2560x1536",
        "seed": 2026111403,
        "prompt": (
            "2D painted game interior concept art of a Sui and Tang dynasty Chinese imperial council hall "
            "in high-angle top-down cutaway view. Thick vermilion lacquered wooden columns, white lime walls "
            "with subtle ink-wash landscape murals, dark polished stone floor, royal throne on a raised wooden "
            "dais at the north end, and in the center a large carved wooden tactical sandbox table displaying "
            "a relief map of surrounding mountains, rivers, and provinces. Warm glowing silk palace lanterns, "
            "scroll racks and desks along the sides, atmospheric cozy yet dignified 2D game art, no characters."
        ),
    },
    {
        "name": "04-suitang-west-courtyard-atelier",
        "width": 1280,
        "height": 768,
        "seedream_size": "2560x1536",
        "seed": 2026111404,
        "prompt": (
            "2D top-down 3/4 view game environment concept of a Sui and Tang dynasty imperial palace side "
            "courtyard housing a royal engineering workshop and an artist atelier. Gray brick and timber frame "
            "halls with upturned eaves, stone-paved yard with stone lanterns, carpenter workbench, pottery and "
            "ink-painting tables under an open wooden veranda, bamboo grove and autumn ginkgo tree, plus neatly "
            "marked empty stone foundation plots ready for new construction. Warm afternoon light, charming 2D "
            "hand-painted game art style, Stardew-like clarity, no text."
        ),
    },
]


def build_zimage_workflow(prompt: str, width: int, height: int, seed: int, prefix: str) -> dict:
    return {
        "28": {
            "class_type": "UNETLoader",
            "inputs": {
                "unet_name": "z_image_turbo_int8_convrot.safetensors",
                "weight_dtype": "default",
            },
        },
        "30": {
            "class_type": "CLIPLoader",
            "inputs": {
                "clip_name": "qwen_3_4b_fp8_mixed.safetensors",
                "type": "lumina2",
                "device": "default",
            },
        },
        "29": {
            "class_type": "VAELoader",
            "inputs": {"vae_name": "ae.safetensors"},
        },
        "27": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": prompt, "clip": ["30", 0]},
        },
        "33": {
            "class_type": "ConditioningZeroOut",
            "inputs": {"conditioning": ["27", 0]},
        },
        "13": {
            "class_type": "EmptySD3LatentImage",
            "inputs": {"width": width, "height": height, "batch_size": 1},
        },
        "11": {
            "class_type": "ModelSamplingAuraFlow",
            "inputs": {"model": ["28", 0], "shift": 3},
        },
        "3": {
            "class_type": "KSampler",
            "inputs": {
                "seed": seed,
                "steps": 8,
                "cfg": 1,
                "sampler_name": "res_multistep",
                "scheduler": "simple",
                "denoise": 1,
                "model": ["11", 0],
                "positive": ["27", 0],
                "negative": ["33", 0],
                "latent_image": ["13", 0],
            },
        },
        "8": {
            "class_type": "VAEDecode",
            "inputs": {"samples": ["3", 0], "vae": ["29", 0]},
        },
        "9": {
            "class_type": "SaveImage",
            "inputs": {"filename_prefix": prefix, "images": ["8", 0]},
        },
    }


def build_flux_workflow(prompt: str, width: int, height: int, seed: int, prefix: str) -> dict:
    return {
        "1": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": "flux1-dev-fp8.safetensors"},
        },
        "2": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": prompt, "clip": ["1", 1]},
        },
        "3": {
            "class_type": "FluxGuidance",
            "inputs": {"conditioning": ["2", 0], "guidance": 3.5},
        },
        "4": {
            "class_type": "ConditioningZeroOut",
            "inputs": {"conditioning": ["2", 0]},
        },
        "5": {
            "class_type": "EmptySD3LatentImage",
            "inputs": {"width": width, "height": height, "batch_size": 1},
        },
        "6": {
            "class_type": "KSampler",
            "inputs": {
                "seed": seed,
                "steps": 20,
                "cfg": 1.0,
                "sampler_name": "euler",
                "scheduler": "simple",
                "denoise": 1.0,
                "model": ["1", 0],
                "positive": ["3", 0],
                "negative": ["4", 0],
                "latent_image": ["5", 0],
            },
        },
        "7": {
            "class_type": "VAEDecode",
            "inputs": {"samples": ["6", 0], "vae": ["1", 2]},
        },
        "8": {
            "class_type": "SaveImage",
            "inputs": {"filename_prefix": prefix, "images": ["7", 0]},
        },
    }


def _get_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _post_json(url: str, payload: dict) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _download_image(filename: str, subfolder: str, img_type: str, target: Path) -> None:
    query = urllib.parse.urlencode(
        {"filename": filename, "subfolder": subfolder, "type": img_type}
    )
    with urllib.request.urlopen(f"{COMFY_URL}/view?{query}", timeout=30) as resp:
        target.write_bytes(resp.read())


def wait_for_result(prompt_id: str, timeout_sec: float = 300.0) -> list[dict]:
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        history = _get_json(f"{COMFY_URL}/history/{prompt_id}")
        if prompt_id in history:
            outputs = history[prompt_id].get("outputs", {})
            images: list[dict] = []
            for node_out in outputs.values():
                images.extend(node_out.get("images", []))
            if images:
                return images
        time.sleep(1.0)
    raise TimeoutError(f"Timed out waiting for ComfyUI prompt_id={prompt_id}")


def run_comfyui(backend: str, items: list[dict], out_dir: Path) -> None:
    try:
        stats = _get_json(f"{COMFY_URL}/system_stats")
        devices = stats.get("devices", [])
        gpu_name = devices[0].get("name", "unknown") if devices else "unknown"
        print(f"Connected to ComfyUI at {COMFY_URL} (device: {gpu_name}, backend: {backend})")
    except urllib.error.URLError as exc:
        raise SystemExit(
            f"无法连接本机 ComfyUI ({COMFY_URL}): {exc}\n"
            "请先运行: & D:\\AI\\ComfyUI\\Start-ComfyUI.ps1"
        )

    out_dir.mkdir(parents=True, exist_ok=True)
    builder = build_flux_workflow if backend == "flux" else build_zimage_workflow
    for item in items:
        name = item["name"]
        workflow = builder(
            prompt=item["prompt"],
            width=item["width"],
            height=item["height"],
            seed=item["seed"],
            prefix=f"cabinet-palace/{backend}/{name}",
        )
        t0 = time.time()
        queued = _post_json(f"{COMFY_URL}/prompt", {"prompt": workflow})
        prompt_id = queued["prompt_id"]
        images = wait_for_result(prompt_id)
        first = images[0]
        out_path = out_dir / f"{name}.png"
        _download_image(first["filename"], first.get("subfolder", ""), first.get("type", "output"), out_path)
        elapsed = time.time() - t0
        print(f"[OK] {out_path} ({elapsed:.1f}s)")


def run_seedream(items: list[dict], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for item in items:
        name = item["name"]
        out_path = out_dir / f"{name}.png"
        info = seedream_generate_image(
            item["prompt"],
            out_path,
            size=item.get("seedream_size", "2K"),
            output_format="png",
            watermark=False,
        )
        print(f"[OK] {info['out_path']} ({info['elapsed_sec']}s, {info['size']}, {info['model']})")


def run_hybrid(
    items: list[dict],
    master_dir: Path,
    refined_dir: Path,
    *,
    denoise: float,
    max_long_edge: int,
    regenerate_master: bool,
) -> None:
    master_dir.mkdir(parents=True, exist_ok=True)
    refined_dir.mkdir(parents=True, exist_ok=True)
    for item in items:
        name = item["name"]
        master_path = master_dir / f"{name}.png"
        if regenerate_master or not master_path.is_file():
            info_m = seedream_generate_image(
                item["prompt"],
                master_path,
                size=item.get("seedream_size", "2K"),
                output_format="png",
                watermark=False,
            )
            print(f"[MASTER] {info_m['out_path']} ({info_m['elapsed_sec']}s, {info_m['size']}, {info_m['model']})")
        else:
            print(f"[MASTER-CACHED] {master_path}")

        refined_path = refined_dir / f"{name}.png"
        info_r = flux_refine_image(
            master_path,
            item["prompt"],
            refined_path,
            comfy_url=COMFY_URL,
            denoise=denoise,
            steps=20,
            guidance=3.5,
            seed=item["seed"],
            max_long_edge=max_long_edge,
            prefix=f"cabinet-palace/refined/{name}",
        )
        print(f"[REFINED] {info_r['out_path']} ({info_r['elapsed_sec']}s, {info_r['size']}, denoise={denoise})")


def main() -> None:
    parser = argparse.ArgumentParser(description="生成皇宫概念设计图")
    parser.add_argument(
        "--backend",
        choices=["zimage", "flux", "seedream", "hybrid"],
        default="zimage",
        help="出图后端：zimage、flux、seedream，或 hybrid（Seedream 母图 + Flux 本地精修）",
    )
    parser.add_argument("--only", default=None, help="只生成指定 name 的单张概念图")
    parser.add_argument("--out-dir", default=None, help="自定义输出目录")
    parser.add_argument("--denoise", type=float, default=0.35, help="hybrid 模式下 Flux 精修重绘幅度（默认 0.35）")
    parser.add_argument("--max-long-edge", type=int, default=1920, help="hybrid 模式下精修最大长边像素（默认 1920）")
    parser.add_argument("--regenerate-master", action="store_true", help="hybrid 模式下强制重跑云端母图")
    args = parser.parse_args()

    items = CONCEPTS
    if args.only:
        items = [c for c in CONCEPTS if c["name"] == args.only]
        if not items:
            valid = ", ".join(c["name"] for c in CONCEPTS)
            raise SystemExit(f"未找到概念图 '{args.only}'，可选: {valid}")

    if args.out_dir:
        target_dir = Path(args.out_dir)
    elif args.backend == "zimage":
        target_dir = OUT_DIR
    elif args.backend == "hybrid":
        target_dir = OUT_DIR / "refined"
    else:
        target_dir = OUT_DIR / args.backend

    if args.backend == "seedream":
        run_seedream(items, target_dir)
    elif args.backend == "hybrid":
        run_hybrid(
            items,
            OUT_DIR / "seedream",
            target_dir,
            denoise=args.denoise,
            max_long_edge=args.max_long_edge,
            regenerate_master=args.regenerate_master,
        )
    else:
        run_comfyui(args.backend, items, target_dir)


if __name__ == "__main__":
    main()
