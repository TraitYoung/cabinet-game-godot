"""使用本机 ComfyUI Flux.1 Dev FP8 对云端母图执行 Img2Img 精修与风格统一。

用法示例（确保本机 ComfyUI 已启动于 http://127.0.0.1:8188）：
    python tools\\flux_refine.py ^
        --input docs\\media\\palace-concepts\\seedream\\02-suitang-palace-topdown-game.png ^
        --prompt "2D hand-painted RPG game environment art, crisp clean brushwork, warm sunlight" ^
        --denoise 0.35 ^
        --out docs\\media\\palace-concepts\\refined\\02-suitang-palace-topdown-game.png
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path
from typing import Any

DEFAULT_COMFY_URL = "http://127.0.0.1:8188"
DEFAULT_CKPT = "flux1-dev-fp8.safetensors"


def _read_png_dimensions(path: Path) -> tuple[int, int] | None:
    """从 PNG 文件头读取宽高，避免额外引入 Pillow 依赖。"""
    data = path.read_bytes()[:24]
    if len(data) >= 24 and data[:8] == b"\x89PNG\r\n\x1a\n" and data[12:16] == b"IHDR":
        width = int.from_bytes(data[16:20], "big")
        height = int.from_bytes(data[20:24], "big")
        return width, height
    return None


def compute_refine_size(input_path: Path, max_long_edge: int = 1920) -> tuple[int, int]:
    """按原图纵横比计算适配 12GB 显存且对齐 16px 的精修分辨率。"""
    dims = _read_png_dimensions(input_path)
    if not dims:
        return 1920, 1152
    width, height = dims
    long_edge = max(width, height)
    if long_edge > max_long_edge:
        scale = max_long_edge / float(long_edge)
        width = int(round(width * scale))
        height = int(round(height * scale))
    aligned_w = max(512, (width // 16) * 16)
    aligned_h = max(512, (height // 16) * 16)
    return aligned_w, aligned_h


def _get_json(url: str) -> dict[str, Any]:
    with urllib.request.urlopen(url, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _post_json(url: str, payload: dict[str, Any]) -> dict[str, Any]:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def upload_image(comfy_url: str, image_path: Path) -> str:
    """通过 ComfyUI /upload/image 接口上传母图并返回服务端文件名。"""
    boundary = f"----CabinetBoundary{uuid.uuid4().hex}"
    mime_type, _ = mimetypes.guess_type(image_path.name)
    if not mime_type:
        mime_type = "image/png"
    file_bytes = image_path.read_bytes()

    parts = [
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="image"; filename="{image_path.name}"\r\n'
        f"Content-Type: {mime_type}\r\n\r\n".encode("utf-8"),
        file_bytes,
        f"\r\n--{boundary}\r\n"
        f'Content-Disposition: form-data; name="overwrite"\r\n\r\ntrue\r\n'
        f"--{boundary}--\r\n".encode("utf-8"),
    ]
    body = b"".join(parts)
    req = urllib.request.Request(
        f"{comfy_url.rstrip('/')}/upload/image",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        info = json.loads(resp.read().decode("utf-8"))
    return info["name"]


def build_flux_refine_workflow(
    *,
    input_image_name: str,
    prompt: str,
    width: int,
    height: int,
    seed: int,
    denoise: float,
    steps: int,
    guidance: float,
    prefix: str,
    ckpt_name: str = DEFAULT_CKPT,
) -> dict[str, Any]:
    return {
        "1": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": ckpt_name},
        },
        "2": {
            "class_type": "LoadImage",
            "inputs": {"image": input_image_name},
        },
        "3": {
            "class_type": "ImageScale",
            "inputs": {
                "image": ["2", 0],
                "upscale_method": "lanczos",
                "width": width,
                "height": height,
                "crop": "disabled",
            },
        },
        "4": {
            "class_type": "VAEEncode",
            "inputs": {"pixels": ["3", 0], "vae": ["1", 2]},
        },
        "5": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": prompt, "clip": ["1", 1]},
        },
        "6": {
            "class_type": "FluxGuidance",
            "inputs": {"conditioning": ["5", 0], "guidance": guidance},
        },
        "7": {
            "class_type": "ConditioningZeroOut",
            "inputs": {"conditioning": ["5", 0]},
        },
        "8": {
            "class_type": "KSampler",
            "inputs": {
                "seed": seed,
                "steps": steps,
                "cfg": 1.0,
                "sampler_name": "euler",
                "scheduler": "simple",
                "denoise": denoise,
                "model": ["1", 0],
                "positive": ["6", 0],
                "negative": ["7", 0],
                "latent_image": ["4", 0],
            },
        },
        "9": {
            "class_type": "VAEDecode",
            "inputs": {"samples": ["8", 0], "vae": ["1", 2]},
        },
        "10": {
            "class_type": "SaveImage",
            "inputs": {"filename_prefix": prefix, "images": ["9", 0]},
        },
    }


def _wait_for_images(comfy_url: str, prompt_id: str, timeout_sec: float = 300.0) -> list[dict[str, Any]]:
    deadline = time.time() + timeout_sec
    base = comfy_url.rstrip("/")
    while time.time() < deadline:
        history = _get_json(f"{base}/history/{prompt_id}")
        if prompt_id in history:
            entry = history[prompt_id]
            status = entry.get("status", {})
            if status.get("status_str") == "error":
                raise RuntimeError(f"ComfyUI 执行失败: {status}")
            outputs = entry.get("outputs", {})
            images: list[dict[str, Any]] = []
            for node_out in outputs.values():
                images.extend(node_out.get("images", []))
            if images:
                return images
        time.sleep(1.0)
    raise TimeoutError(f"Timed out waiting for ComfyUI prompt_id={prompt_id}")


def refine_image(
    input_path: str | Path,
    prompt: str,
    out_path: str | Path,
    *,
    comfy_url: str = DEFAULT_COMFY_URL,
    denoise: float = 0.35,
    steps: int = 20,
    guidance: float = 3.5,
    seed: int = 2026111501,
    max_long_edge: int = 1920,
    prefix: str = "cabinet-palace/refined",
) -> dict[str, Any]:
    """上传母图到 ComfyUI 并使用 Flux.1 Dev 执行低重绘精修。"""
    src = Path(input_path)
    if not src.is_file():
        raise FileNotFoundError(f"母图不存在: {src}")

    base = comfy_url.rstrip("/")
    try:
        _get_json(f"{base}/system_stats")
    except urllib.error.URLError as exc:
        raise RuntimeError(
            f"无法连接本机 ComfyUI ({base}): {exc}\n"
            "请先启动 ComfyUI: & D:\\AI\\ComfyUI\\Start-ComfyUI.ps1"
        ) from None

    t0 = time.time()
    uploaded_name = upload_image(base, src)
    width, height = compute_refine_size(src, max_long_edge=max_long_edge)
    workflow = build_flux_refine_workflow(
        input_image_name=uploaded_name,
        prompt=prompt,
        width=width,
        height=height,
        seed=seed,
        denoise=denoise,
        steps=steps,
        guidance=guidance,
        prefix=prefix,
    )
    queued = _post_json(f"{base}/prompt", {"prompt": workflow})
    images = _wait_for_images(base, queued["prompt_id"])
    first = images[0]
    query = urllib.parse.urlencode(
        {
            "filename": first["filename"],
            "subfolder": first.get("subfolder", ""),
            "type": first.get("type", "output"),
        }
    )
    dst = Path(out_path)
    dst.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(f"{base}/view?{query}", timeout=60) as resp:
        dst.write_bytes(resp.read())

    return {
        "input_path": str(src),
        "out_path": str(dst),
        "size": f"{width}x{height}",
        "denoise": denoise,
        "steps": steps,
        "elapsed_sec": round(time.time() - t0, 2),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="使用本机 Flux.1 Dev 对母图进行 Img2Img 精修")
    parser.add_argument("--input", required=True, help="云端 API 生成的母图路径")
    parser.add_argument("--prompt", required=True, help="精修提示词（控制画风与细节纹理）")
    parser.add_argument("--out", required=True, help="精修结果保存路径")
    parser.add_argument("--denoise", type=float, default=0.35, help="重绘幅度 0.25~0.50（默认 0.35）")
    parser.add_argument("--steps", type=int, default=20, help="采样步数（默认 20）")
    parser.add_argument("--guidance", type=float, default=3.5, help="FluxGuidance（默认 3.5）")
    parser.add_argument("--seed", type=int, default=2026111501, help="随机种子")
    parser.add_argument("--max-long-edge", type=int, default=1920, help="精修最大长边像素（默认 1920）")
    parser.add_argument("--comfy-url", default=DEFAULT_COMFY_URL, help="ComfyUI 服务地址")
    args = parser.parse_args()

    info = refine_image(
        args.input,
        args.prompt,
        args.out,
        comfy_url=args.comfy_url,
        denoise=args.denoise,
        steps=args.steps,
        guidance=args.guidance,
        seed=args.seed,
        max_long_edge=args.max_long_edge,
    )
    print(json.dumps(info, ensure_ascii=False))


if __name__ == "__main__":
    main()
