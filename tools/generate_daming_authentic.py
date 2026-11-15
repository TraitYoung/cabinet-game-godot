"""依据真实唐大明宫考古平面图、1:15 复原微缩模型与遗址实景图，调用 Doubao-Seedream-5.5 出图。

用法：
    python tools\\generate_daming_authentic.py
    python tools\\generate_daming_authentic.py --only 01-daming-palace-authentic-map
"""

from __future__ import annotations

import argparse
from pathlib import Path

from seedream import generate_image

REPO_ROOT = Path(__file__).resolve().parent.parent
REF_DIR = REPO_ROOT / "docs" / "media" / "references" / "daming-palace"
OUT_DIR = REPO_ROOT / "docs" / "media" / "palace-concepts" / "daming-authentic"

ITEMS = [
    {
        "name": "01-daming-palace-authentic-map",
        "size": "2560x1536",
        "transparent": False,
        "refs": [
            "01-plan-ruins-zh.png",
            "04-palace-model-overview-01.jpg",
            "05-palace-model-overview-02.jpg",
        ],
        "prompt": (
            "2D 3/4 top-down RPG game environment map illustration strictly faithful to the real "
            "Tang dynasty Daming Palace archaeological plan in Image 1 and the authentic Tang architectural "
            "materials, grey ceramic tile roofs, vermilion timber columns, white plaster walls, and rammed-earth "
            "terraces shown in Images 2 and 3. Central north-south axis from south to north: five-portal Danfeng Gate "
            "at the bottom, stone-paved ceremonial plaza, elevated Hanyuan Hall with symmetrical Xiangluan and Qifeng "
            "flanking pavilions and dragon-tail staircases, eastern Chancellery cabinet courtyard, western artisan "
            "workshop and construction plots, and Taiye Pond with willow trees at the back. Cozy handcrafted 2D game "
            "art clarity, walkable stone paths, no modern buildings, no text, no labels."
        ),
    },
    {
        "name": "02-hanyuan-hall-authentic",
        "size": "2560x1440",
        "transparent": False,
        "refs": [
            "07-hanyuan-hall-cg-restoration.jpg",
            "08-hanyuan-hall-base-model.jpg",
            "04-palace-model-overview-01.jpg",
        ],
        "prompt": (
            "2D hand-painted architectural game concept art of Tang dynasty Daming Palace Hanyuan Hall, "
            "faithfully following the multi-tier rammed-earth terrace, U-shaped courtyard composition, twin parallel "
            "dragon-tail staircases, and 11-bay main hall flanked by Xiangluan and Qifeng pavilions shown in Images 1 and 2, "
            "rendered with the authentic Tang dark grey ceramic tile roofs, golden Chiwen ridge ornaments, vermilion "
            "timber colonnades, Dougong brackets, and white lime plaster walls from Image 3. Warm golden morning sunlight, "
            "clean 2D game environment illustration, no modern elements, no text."
        ),
    },
    {
        "name": "03-asset-danfeng-gate",
        "size": "2K",
        "transparent": True,
        "refs": [
            "11-danfeng-gate-real.jpg",
            "05-palace-model-overview-02.jpg",
        ],
        "prompt": (
            "Isolated 2D hand-painted RPG game building sprite of Tang dynasty Daming Palace Danfeng Gate seen from "
            "a 3/4 top-down game angle, strictly faithful to the five-portal battered earthen-masonry gate base, "
            "five red-studded wooden gate doors, upper timber gallery with vermilion columns and Dougong brackets, "
            "and dark grey hipped ceramic tile roof with golden Chiwen ridge ornaments shown in Images 1 and 2. "
            "Clean standalone architectural asset on pure transparent background, no tourists, no modern fences, no text."
        ),
    },
    {
        "name": "04-asset-linde-hall",
        "size": "2K",
        "transparent": True,
        "refs": [
            "10-linde-hall-model-01.jpg",
            "04-palace-model-overview-01.jpg",
        ],
        "prompt": (
            "Isolated 2D hand-painted RPG game building sprite of Tang dynasty Daming Palace Linde Hall complex "
            "seen from a 3/4 top-down game angle, strictly matching the connected front, middle, and rear triple "
            "halls, symmetrical flanking two-story pavilions (Yuyi and Jielin towers), covered corridors, and "
            "stone terrace balustrades in Image 1, colored in the authentic vermilion timber, white plaster walls, "
            "and dark grey ceramic tile roofs from Image 2. Clean standalone game asset on transparent background, "
            "crisp readable linework, no display case, no text."
        ),
    },
]


def main() -> None:
    parser = argparse.ArgumentParser(description="依据大明宫真实资料通过 Seedream 5.5 出图")
    parser.add_argument("--only", default=None, help="只生成指定 name 的单张图片")
    parser.add_argument("--overwrite", action="store_true", help="覆盖已存在的输出文件")
    args = parser.parse_args()

    selected = ITEMS
    if args.only:
        selected = [item for item in ITEMS if item["name"] == args.only]
        if not selected:
            valid = ", ".join(item["name"] for item in ITEMS)
            raise SystemExit(f"未找到 '{args.only}'，可选: {valid}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for item in selected:
        ref_paths = [REF_DIR / r for r in item["refs"]]
        out_path = OUT_DIR / f"{item['name']}.png"
        if out_path.is_file() and out_path.stat().st_size > 0 and not args.overwrite:
            print(f"[SKIP] {out_path}", flush=True)
            continue
        info = generate_image(
            item["prompt"],
            out_path,
            size=item["size"],
            output_format="png",
            transparent=item["transparent"],
            image=ref_paths,
            watermark=False,
        )
        print(
            f"[OK] {info['out_path']} ({info['elapsed_sec']}s, {info['size']}, "
            f"transparent={item['transparent']}, refs={len(ref_paths)})",
            flush=True,
        )


if __name__ == "__main__":
    main()
