"""Doubao-Seedream-5.5 (火山方舟 Ark API) 图像生成工具。

自动读取仓库根目录 `.env` 中的 `ARK_API_KEY`、`ARK_BASE_URL`、`SEEDREAM_MODEL`。
既可作为模块导入，也可直接作为 CLI 使用：
    python tools/seedream.py --prompt "中式隋唐宫殿俯视角游戏场景" --out docs/media/test.png
    python tools/seedream.py --prompt "中式石灯笼游戏资产" --transparent --out docs/media/lantern.png
"""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"
DEFAULT_MODEL = "doubao-seedream-5-5-261028"


def load_dotenv(env_path: Path | None = None) -> None:
    """将 `.env` 中的键值对加载到环境变量（不覆盖已存在的环境变量）。"""
    path = env_path or (REPO_ROOT / ".env")
    if not path.is_file():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def _encode_image_input(image_ref: str | Path) -> str:
    if isinstance(image_ref, str) and (
        image_ref.startswith("http://")
        or image_ref.startswith("https://")
        or image_ref.startswith("data:image/")
    ):
        return image_ref
    img_path = Path(image_ref)
    if not img_path.is_file():
        raise FileNotFoundError(f"参考图不存在: {img_path}")
    mime_type, _ = mimetypes.guess_type(img_path.name)
    if not mime_type or not mime_type.startswith("image/"):
        mime_type = "image/png"
    encoded = base64.b64encode(img_path.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def get_config() -> tuple[str, str, str]:
    load_dotenv()
    api_key = os.environ.get("ARK_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError(
            "未检测到 ARK_API_KEY。请在仓库根目录 `.env` 中配置 ARK_API_KEY=..."
        )
    base_url = os.environ.get("ARK_BASE_URL", DEFAULT_BASE_URL).strip().rstrip("/")
    model = os.environ.get("SEEDREAM_MODEL", DEFAULT_MODEL).strip()
    return api_key, base_url, model


def generate_image(
    prompt: str,
    out_path: str | Path,
    *,
    size: str = "2K",
    output_format: str = "png",
    transparent: bool = False,
    image: str | Path | list[str | Path] | None = None,
    watermark: bool = False,
    model: str | None = None,
    timeout_sec: float = 180.0,
) -> dict[str, Any]:
    """调用 Doubao-Seedream API 生成单张图片并保存到 `out_path`。"""
    api_key, base_url, default_model = get_config()
    target = Path(out_path)
    target.parent.mkdir(parents=True, exist_ok=True)

    fmt = "png" if transparent else output_format
    payload: dict[str, Any] = {
        "model": model or default_model,
        "prompt": prompt,
        "size": size,
        "response_format": "url",
        "output_format": fmt,
        "watermark": watermark,
    }
    if transparent:
        payload["background"] = "transparent"
    if image is not None:
        if isinstance(image, list):
            payload["image"] = [_encode_image_input(item) for item in image]
        else:
            payload["image"] = _encode_image_input(image)

    endpoint = f"{base_url}/images/generations"
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        endpoint,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )

    t0 = time.time()
    result: dict[str, Any] | None = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
                result = json.loads(resp.read().decode("utf-8"))
            break
        except urllib.error.HTTPError as exc:
            err_body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Seedream API 请求失败 ({exc.code}): {err_body}") from None
        except (urllib.error.URLError, OSError) as exc:
            if attempt == 2:
                raise RuntimeError(f"Seedream API 网络请求失败: {exc}") from None
            time.sleep(2.0 * (attempt + 1))
    assert result is not None

    items = result.get("data") or []
    if not items:
        raise RuntimeError(f"Seedream API 未返回图像数据: {result}")

    first = items[0]
    if "url" in first and first["url"]:
        with urllib.request.urlopen(first["url"], timeout=timeout_sec) as img_resp:
            target.write_bytes(img_resp.read())
    elif "b64_json" in first and first["b64_json"]:
        target.write_bytes(base64.b64decode(first["b64_json"]))
    else:
        raise RuntimeError(f"Seedream API 返回项缺少 url / b64_json: {first}")

    return {
        "out_path": str(target),
        "model": result.get("model", payload["model"]),
        "size": first.get("size", size),
        "elapsed_sec": round(time.time() - t0, 2),
        "usage": result.get("usage"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="调用 Doubao-Seedream-5.5 生成图像")
    parser.add_argument("--prompt", required=True, help="正向提示词")
    parser.add_argument("--out", required=True, help="输出图片路径")
    parser.add_argument("--size", default="2K", help="尺寸规格，如 2K、4K 或 2560x1440")
    parser.add_argument("--format", default="png", choices=["png", "jpeg"], help="输出格式")
    parser.add_argument("--transparent", action="store_true", help="输出原生 RGBA 透明背景 PNG")
    parser.add_argument("--image", nargs="*", default=None, help="可选参考图路径或 URL（图生图/编辑）")
    parser.add_argument("--model", default=None, help="覆盖 .env 中的 SEEDREAM_MODEL")
    parser.add_argument("--watermark", action="store_true", help="保留水印（默认关闭）")
    args = parser.parse_args()

    image_arg: str | list[str] | None = None
    if args.image:
        image_arg = args.image[0] if len(args.image) == 1 else args.image

    info = generate_image(
        args.prompt,
        args.out,
        size=args.size,
        output_format=args.format,
        transparent=args.transparent,
        image=image_arg,
        watermark=args.watermark,
        model=args.model,
    )
    print(json.dumps(info, ensure_ascii=False))


if __name__ == "__main__":
    main()
