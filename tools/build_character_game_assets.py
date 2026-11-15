"""构建游戏内使用的角色资产：
1. 对话框高清胸像 (`assets/characters/portraits/<id>.png`, 384x384 RGBA/RGB PNG)
2. 场内 2.5 头身 Q 版全身小人精灵 (`assets/characters/chibi/<id>.png` 及 `monarch.png`, 200x240 透明背景 RGBA PNG)

用法示例：
    python tools\\build_character_game_assets.py --portraits-only
    python tools\\build_character_game_assets.py --chibi-only --workers 3
    python tools\\build_character_game_assets.py --only bina,chizheng,monarch --overwrite
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import threading
from pathlib import Path
from typing import Any

from PIL import Image

from seedream import generate_image

REPO_ROOT = Path(__file__).resolve().parent.parent
VISUALS_JSON = REPO_ROOT / "docs" / "characters" / "cabinet_visuals.json"
BINA_CONCEPT = (
    REPO_ROOT
    / "docs"
    / "media"
    / "v3-casual-closed-smile-2026-11-09"
    / "bina-casual-concept-airy-ends-v4.png"
)
CONCEPT_DIR = REPO_ROOT / "docs" / "media" / "cabinet-concepts"
CHIBI_RAW_DIR = CONCEPT_DIR / "chibi-raw"
PORTRAITS_OUT_DIR = REPO_ROOT / "assets" / "characters" / "portraits"
CHIBI_OUT_DIR = REPO_ROOT / "assets" / "characters" / "chibi"

PORTRAIT_SIZE = 384
CHIBI_CANVAS_W = 200
CHIBI_CANVAS_H = 240
CHIBI_FOOT_Y = 226
CHIBI_TARGET_H = 204

_PRINT_LOCK = threading.Lock()


def _safe_print(msg: str) -> None:
    with _PRINT_LOCK:
        print(msg, flush=True)


def _load_cabinet_specs() -> list[dict[str, Any]]:
    data = json.loads(VISUALS_JSON.read_text(encoding="utf-8"))
    specs: list[dict[str, Any]] = [
        {
            "id": "bina",
            "display_name": "Bina",
            "concept_path": BINA_CONCEPT,
            "chibi_extra": (
                "young woman, smoky rose-tea greige clavicle-length layered hair with pale champagne inner highlights, "
                "one slender curved crown ahoge, left hair tucked behind left ear with minimalist gold ear cuff, "
                "honey-amber rounded almond eyes, closed gentle smile, oatmeal cream-white off-shoulder knit top "
                "exposing thin mocha camisole strap on her right shoulder, charcoal high-waist tailored shorts, "
                "slim gold buckle belt, cream leather loafers"
            ),
        }
    ]
    for member in data.get("members", []):
        pid = member["persona_id"]
        order = int(member["order"])
        concept_path = CONCEPT_DIR / f"{order:02d}-{pid}-concept.png"
        canon = member.get("canon", {})
        specs.append(
            {
                "id": pid,
                "display_name": member["display_name"],
                "concept_path": concept_path,
                "chibi_extra": (
                    f"{canon.get('hair', '')}; {canon.get('eyes', '')}; "
                    f"{canon.get('default_outfit', '')}; {canon.get('props', '')}"
                ),
            }
        )
    return specs


def _detect_center_portrait_box(im: Image.Image) -> tuple[int, int, int, int]:
    """定位三栏概念图中央正面胸像的正方形裁切区域，自动识别中栏人物簇并避开分隔线与侧颜栏。"""
    rgb = im.convert("RGB")
    w, h = rgb.size
    px = rgb.load()
    bg = px[5, 5]

    def is_fg(x: int, y: int) -> bool:
        r, g, b = px[x, y]
        return abs(r - bg[0]) + abs(g - bg[1]) + abs(b - bg[2]) > 24

    # 识别真正的全高细分隔线（<= 4px 宽且贯穿 92%+ 高度、两侧多为背景）
    divider_xs: set[int] = set()
    for x in range(int(w * 0.22), int(w * 0.78)):
        hits = sum(1 for y in range(0, h, 8) if is_fg(x, y))
        if hits > (h // 8) * 0.92:
            left_empty = sum(1 for y in range(0, h, 24) if not is_fg(max(0, x - 6), y))
            right_empty = sum(1 for y in range(0, h, 24) if not is_fg(min(w - 1, x + 6), y))
            if left_empty > (h // 24) * 0.7 and right_empty > (h // 24) * 0.7:
                divider_xs.add(x)

    # 在眉眼额头带 (y: 0.14 ~ 0.28) 扫描前景密度，避开顶部武器、低马尾发束与下方宽肩，干净分离左/中/右三栏人物
    y_scan_0 = int(h * 0.14)
    y_scan_1 = int(h * 0.28)
    runs: list[tuple[int, int]] = []
    cur_start: int | None = None
    empty_streak = 0
    for x in range(int(w * 0.04), int(w * 0.96)):
        if x in divider_xs:
            cnt = 0
        else:
            cnt = sum(1 for y in range(y_scan_0, y_scan_1, 3) if is_fg(x, y))
        if cnt > 4:
            if cur_start is None:
                cur_start = x
            empty_streak = 0
        else:
            if cur_start is not None:
                empty_streak += 1
                if empty_streak >= 8:
                    end_x = x - empty_streak
                    if end_x - cur_start > int(w * 0.05):
                        runs.append((cur_start, end_x))
                    cur_start = None
                    empty_streak = 0
    if cur_start is not None:
        end_x = int(w * 0.96) - empty_streak
        if end_x - cur_start > int(w * 0.05):
            runs.append((cur_start, end_x))

    # 取中心最接近图像中线 (x = 0.48*w) 的人物簇作为中栏胸像
    if runs:
        head_x0, head_x1 = min(runs, key=lambda r: abs(((r[0] + r[1]) * 0.5) - w * 0.48))
    else:
        head_x0, head_x1 = int(w * 0.30), int(w * 0.66)

    # 计算该中心簇在 [0.002h .. 0.55h] 内的最高点 y_min
    y_min = h
    for x in range(head_x0, head_x1 + 1, 3):
        if x in divider_xs:
            continue
        for y in range(int(h * 0.002), int(h * 0.55), 2):
            if is_fg(x, y):
                if y < y_min:
                    y_min = y
                break
    if y_min >= h:
        y_min = 0

    # 确定安全左右硬边界，绝不越界切入左栏或右栏（以及分隔线）
    safe_left = 0
    safe_right = w
    for r in runs:
        if r[1] < head_x0:
            safe_left = max(safe_left, r[1] + 8)
        elif r[0] > head_x1:
            safe_right = min(safe_right, r[0] - 8)
    for dx in divider_xs:
        if dx < head_x0:
            safe_left = max(safe_left, dx + 6)
        elif dx > head_x1:
            safe_right = min(safe_right, dx - 6)

    head_w = head_x1 - head_x0
    cx = (head_x0 + head_x1) // 2
    desired_side = max(int(h * 0.62), int(head_w * 1.12))
    max_safe_side = max(128, safe_right - safe_left)
    side = min(desired_side, int(h * 0.68), max_safe_side)

    top = max(0, y_min - int(h * 0.02))
    if top + side > h:
        top = max(0, h - side)

    left = cx - side // 2
    if left < safe_left:
        left = safe_left
    if left + side > safe_right:
        left = max(safe_left, safe_right - side)

    return (left, top, left + side, top + side)


def build_portrait(spec: dict[str, Any], *, overwrite: bool) -> bool:
    pid = spec["id"]
    out_path = PORTRAITS_OUT_DIR / f"{pid}.png"
    if out_path.is_file() and out_path.stat().st_size > 0 and not overwrite:
        _safe_print(f"[SKIP-PORTRAIT] {out_path}")
        return False

    concept_path = Path(spec["concept_path"])
    if not concept_path.is_file():
        raise FileNotFoundError(f"概念设定图不存在: {concept_path}")

    PORTRAITS_OUT_DIR.mkdir(parents=True, exist_ok=True)
    with Image.open(concept_path) as im:
        box = _detect_center_portrait_box(im)
        cropped = im.crop(box).convert("RGBA")
        resized = cropped.resize((PORTRAIT_SIZE, PORTRAIT_SIZE), Image.Resampling.LANCZOS)
        resized.save(out_path, format="PNG")
    _safe_print(f"[PORTRAIT] {out_path} (crop={box})")
    return True


def _normalize_chibi_sprite(raw_path: Path, out_path: Path) -> None:
    """裁去透明空白并规范化为统一脚底基准线（y=226）的 200x240 RGBA 精灵图。"""
    with Image.open(raw_path) as src:
        rgba = src.convert("RGBA")
        w, h = rgba.size
        alpha = rgba.getchannel("A")
        min_a, _ = alpha.getextrema()

        # 若返回图意外不带透明通道，则按四角背景色做基础抠底
        if min_a > 240:
            px = rgba.load()
            bg = px[4, 4]
            for yy in range(h):
                for xx in range(w):
                    r, g, b, _a = px[xx, yy]
                    if abs(r - bg[0]) + abs(g - bg[1]) + abs(b - bg[2]) < 24:
                        px[xx, yy] = (r, g, b, 0)

        # 清理极低透明度边缘噪点，计算紧凑外接框
        alpha_clean = rgba.getchannel("A").point(lambda v: v if v >= 20 else 0)
        bbox = alpha_clean.getbbox()
        if not bbox:
            raise RuntimeError(f"Q 版精灵图透明裁切后为空: {raw_path}")

        trimmed = rgba.crop(bbox)
        tw, th = trimmed.size
        max_w = CHIBI_CANVAS_W - 12
        scale = min(CHIBI_TARGET_H / float(th), max_w / float(tw))
        new_w = max(1, int(round(tw * scale)))
        new_h = max(1, int(round(th * scale)))
        resized = trimmed.resize((new_w, new_h), Image.Resampling.LANCZOS)

        canvas = Image.new("RGBA", (CHIBI_CANVAS_W, CHIBI_CANVAS_H), (0, 0, 0, 0))
        paste_x = (CHIBI_CANVAS_W - new_w) // 2
        paste_y = CHIBI_FOOT_Y - new_h
        canvas.alpha_composite(resized, (paste_x, paste_y))
        out_path.parent.mkdir(parents=True, exist_ok=True)
        canvas.save(out_path, format="PNG")


def _build_chibi_prompt(spec: dict[str, Any]) -> str:
    if spec["id"] == "monarch":
        return (
            "Single isolated 2.5-head-tall chibi RPG game character sprite of a dignified handsome young "
            "Chinese Tang dynasty emperor standing full-body from head to boots in a 3/4 top-down game view "
            "facing slightly front-right. Wearing refined obsidian-navy and imperial gold dragon-embroidered "
            "Tang round-collar royal robes (yuanlingpao) with a jade-inlaid gold belt, a sleek dark gold-trimmed "
            "imperial topknot crown (zijinguan), warm composed smile with closed lips, black court boots. "
            "Crisp delicate 2D Japanese anime lineart, Kyoto Animation aesthetic, soft matte cel-shading, "
            "clean full-body silhouette on pure transparent background. Centered solo character, "
            "NO drop shadow under feet, NO ground, NO text, NO borders."
        )

    return (
        "Single isolated 2.5-head-tall cute chibi RPG game character sprite standing full-body from head to "
        "shoes in a 3/4 top-down game view facing slightly front-right, strictly faithful to the character "
        "identity, hairstyle, hair color, eye color, facial accessories, clothing details, colors, and "
        "signature props shown in Image 1. "
        f"Key details: {spec['chibi_extra']}. "
        "Crisp delicate 2D Japanese anime lineart, Kyoto Animation aesthetic, soft matte cel-shading, "
        "clean full-body outline on pure transparent background. Centered solo character ONLY, "
        "NO multi-panel layout, NO side profile, NO close-up bust, NO drop shadow under feet, NO ground, "
        "NO text, NO borders."
    )


def build_chibi(spec: dict[str, Any], *, overwrite: bool) -> bool:
    pid = spec["id"]
    out_path = CHIBI_OUT_DIR / f"{pid}.png"
    raw_path = CHIBI_RAW_DIR / f"{pid}-chibi-raw.png"

    if out_path.is_file() and out_path.stat().st_size > 0 and not overwrite:
        _safe_print(f"[SKIP-CHIBI] {out_path}")
        return False

    CHIBI_RAW_DIR.mkdir(parents=True, exist_ok=True)
    if not raw_path.is_file() or raw_path.stat().st_size == 0 or overwrite:
        prompt = _build_chibi_prompt(spec)
        ref_arg: list[Path] | None = None
        if spec.get("concept_path"):
            cpath = Path(spec["concept_path"])
            if not cpath.is_file():
                raise FileNotFoundError(f"参考图不存在: {cpath}")
            ref_arg = [cpath]
        _safe_print(f"[START-CHIBI] {pid} ({spec['display_name']})")
        info = generate_image(
            prompt,
            raw_path,
            size="2K",
            output_format="png",
            transparent=True,
            image=ref_arg,
            watermark=False,
        )
        _safe_print(f"[RAW-CHIBI] {info['out_path']} ({info['elapsed_sec']}s, {info['size']})")
    else:
        _safe_print(f"[USE-CACHED-RAW] {raw_path}")

    _normalize_chibi_sprite(raw_path, out_path)
    _safe_print(f"[OK-CHIBI] {out_path} ({CHIBI_CANVAS_W}x{CHIBI_CANVAS_H})")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="生成/裁切内阁全员游戏胸像与 2.5 头身 Q 版小人")
    parser.add_argument("--portraits-only", action="store_true", help="仅裁切生成 384x384 对话框胸像")
    parser.add_argument("--chibi-only", action="store_true", help="仅生成并规范化 2.5 头身 Q 版小人")
    parser.add_argument("--only", default=None, help="只处理指定角色 ID（逗号分隔，含 monarch）")
    parser.add_argument("--workers", type=int, default=3, help="Q 版小人并发生成数（默认 3）")
    parser.add_argument("--overwrite", action="store_true", help="覆盖已存在文件")
    args = parser.parse_args()

    cabinet_specs = _load_cabinet_specs()
    monarch_spec: dict[str, Any] = {
        "id": "monarch",
        "display_name": "陛下 (Monarch)",
        "concept_path": None,
        "chibi_extra": "",
    }
    all_chibi_specs = cabinet_specs + [monarch_spec]

    if args.only:
        wanted = {item.strip().lower() for item in args.only.split(",") if item.strip()}
        valid = {s["id"].lower() for s in all_chibi_specs}
        unknown = sorted(wanted - valid)
        if unknown:
            raise SystemExit(f"未知角色 ID: {', '.join(unknown)}")
        cabinet_specs = [s for s in cabinet_specs if s["id"].lower() in wanted]
        all_chibi_specs = [s for s in all_chibi_specs if s["id"].lower() in wanted]

    if not args.chibi_only:
        for spec in cabinet_specs:
            build_portrait(spec, overwrite=args.overwrite)

    if not args.portraits_only and all_chibi_specs:
        workers = max(1, min(args.workers, len(all_chibi_specs)))
        failures: list[tuple[str, str]] = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
            fmap = {
                pool.submit(build_chibi, spec, overwrite=args.overwrite): spec["id"]
                for spec in all_chibi_specs
            }
            for fut in concurrent.futures.as_completed(fmap):
                pid = fmap[fut]
                try:
                    fut.result()
                except Exception as exc:
                    failures.append((pid, str(exc)))
                    _safe_print(f"[ERR-CHIBI] {pid}: {exc}")
        if failures:
            raise SystemExit(1)


if __name__ == "__main__":
    main()
