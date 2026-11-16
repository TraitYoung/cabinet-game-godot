"""构建 32x32 唐风全像素化皇城资产管线（纯本地 PIL，正交 3/4 统一透视）：
1. 13 位场内角色像素 Q 版小人 (`assets/characters/chibi/<id>.png`, 76x88 NEAREST 2x)
2. 18 件严格正交 3/4 唐风像素家具、茶亭、宫灯与园林树木精灵 (`assets/palace/props/<id>.png`)
3. 将莲池、戏台、预留地块、石桌方台、树池泥土与南宫门无缝融合绘制进宫城底图 (`assets/palace/palace_base.png`, 1600x1120) 及前景屋檐遮挡层 (`assets/palace/palace_front.png`, 1600x1120)

统一像素密度标准：1 艺术像素 (Texel) = 2x2 游戏世界像素（基于原生网格 2x NEAREST 放大）。

用法示例：
    python tools\\build_pixel_palace_assets.py --props-only --maps-only --overwrite
    python tools\\build_pixel_palace_assets.py --overwrite
"""

from __future__ import annotations

import argparse
import math
import random
from collections import deque
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

REPO_ROOT = Path(__file__).resolve().parent.parent
CHIBI_RAW_DIR = REPO_ROOT / "docs" / "media" / "cabinet-concepts" / "chibi-raw"

CHIBI_OUT_DIR = REPO_ROOT / "assets" / "characters" / "chibi"
PALACE_OUT_DIR = REPO_ROOT / "assets" / "palace"
PROPS_OUT_DIR = PALACE_OUT_DIR / "props"

NATIVE_W = 800
NATIVE_H = 560
WORLD_W = NATIVE_W * 2
WORLD_H = NATIVE_H * 2

OUTLINE_COLOR = (32, 24, 28, 255)
SHADOW_COLOR = (20, 16, 22, 82)

CHARACTER_IDS: list[str] = [
    "monarch",
    "bina",
    "chizheng",
    "bit",
    "vinci",
    "taki",
    "jean",
    "tianji",
    "fukucho",
    "planck",
    "boming",
    "qianjin",
    "jiafa",
]


def _px_rect(draw: ImageDraw.ImageDraw, x0: int, y0: int, x1: int, y1: int, fill: tuple[int, ...]) -> None:
    if x1 <= x0 or y1 <= y0:
        return
    draw.rectangle([x0, y0, x1 - 1, y1 - 1], fill=fill)


def _apply_1texel_outline(native_canvas: Image.Image, outline_col: tuple[int, int, int, int] = OUTLINE_COLOR) -> None:
    """对前景实体（alpha == 255）的 4-邻域透明像素绘制 1-texel 深紫褐外描边。"""
    gw, gh = native_canvas.size
    px = native_canvas.load()
    coords: list[tuple[int, int]] = []
    for y in range(gh):
        for x in range(gw):
            if px[x, y][3] >= 200:
                continue
            for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if 0 <= nx < gw and 0 <= ny < gh and px[nx, ny][3] >= 200:
                    coords.append((x, y))
                    break
    for ox, oy in coords:
        px[ox, oy] = outline_col


def _add_ellipse_shadow(native_canvas: Image.Image, x0: int, y0: int, x1: int, y1: int) -> None:
    """在透明像素区域底部铺设紧贴轮廓的接地阴影。"""
    gw, gh = native_canvas.size
    shadow_layer = Image.new("RGBA", (gw, gh), (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(shadow_layer)
    sdraw.ellipse([x0, y0, x1, y1], fill=SHADOW_COLOR)
    px = native_canvas.load()
    spx = shadow_layer.load()
    for y in range(gh):
        for x in range(gw):
            if px[x, y][3] == 0 and spx[x, y][3] > 0:
                px[x, y] = spx[x, y]


def _save_pixel_2x(native_canvas: Image.Image, out_path: Path) -> None:
    gw, gh = native_canvas.size
    world_img = native_canvas.resize((gw * 2, gh * 2), Image.Resampling.NEAREST)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    world_img.save(out_path, format="PNG")


# ---------------------------------------------------------------------------
# 13 位角色像素小人转换（来自 chibi-raw，保留角色轮廓与特征）
# ---------------------------------------------------------------------------

def _flood_clear_opaque_bg(rgba: Image.Image, tolerance: int = 28) -> Image.Image:
    w, h = rgba.size
    px = rgba.load()
    corners = [(2, 2), (w - 3, 2), (2, h - 3), (w - 3, h - 3)]
    opaque_corners = [c for c in corners if px[c[0], c[1]][3] > 200]
    if not opaque_corners:
        return rgba
    alpha_ext = rgba.getchannel("A").getextrema()
    if alpha_ext[0] <= 20:
        return rgba

    bg_samples = [px[x, y][:3] for x, y in opaque_corners]
    bg_r = sum(c[0] for c in bg_samples) // len(bg_samples)
    bg_g = sum(c[1] for c in bg_samples) // len(bg_samples)
    bg_b = sum(c[2] for c in bg_samples) // len(bg_samples)

    visited = bytearray(w * h)
    q: deque[tuple[int, int]] = deque()
    for sx, sy in corners:
        q.append((sx, sy))
        visited[sy * w + sx] = 1

    while q:
        x, y = q.popleft()
        r, g, b, _a = px[x, y]
        if abs(r - bg_r) + abs(g - bg_g) + abs(b - bg_b) <= tolerance * 3:
            px[x, y] = (r, g, b, 0)
            for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if 0 <= nx < w and 0 <= ny < h:
                    idx = ny * w + nx
                    if not visited[idx]:
                        visited[idx] = 1
                        q.append((nx, ny))
    return rgba


def _bleed_rgb_into_transparent(rgba: Image.Image, passes: int = 4) -> Image.Image:
    w, h = rgba.size
    out = rgba.copy()
    for _ in range(passes):
        src = out.load()
        nxt = out.copy()
        dst = nxt.load()
        for y in range(h):
            for x in range(w):
                if src[x, y][3] > 10:
                    continue
                r_sum = g_sum = b_sum = cnt = 0
                for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                    if 0 <= nx < w and 0 <= ny < h:
                        pr, pg, pb, pa = src[nx, ny]
                        if pa > 10:
                            r_sum += pr
                            g_sum += pg
                            b_sum += pb
                            cnt += 1
                if cnt > 0:
                    dst[x, y] = (r_sum // cnt, g_sum // cnt, b_sum // cnt, 0)
        out = nxt
    return out


def _quantize_opaque_pixels(rgb: Image.Image, alpha_mask: Image.Image, colors: int = 24) -> Image.Image:
    w, h = rgb.size
    rgb_px = rgb.load()
    a_px = alpha_mask.load()
    fg_colors: list[tuple[int, int, int]] = []
    for y in range(h):
        for x in range(w):
            if a_px[x, y] >= 128:
                fg_colors.append(rgb_px[x, y])
    if not fg_colors:
        return rgb

    avg_r = sum(c[0] for c in fg_colors) // len(fg_colors)
    avg_g = sum(c[1] for c in fg_colors) // len(fg_colors)
    avg_b = sum(c[2] for c in fg_colors) // len(fg_colors)

    clean_rgb = rgb.copy()
    c_px = clean_rgb.load()
    for y in range(h):
        for x in range(w):
            if a_px[x, y] < 128:
                c_px[x, y] = (avg_r, avg_g, avg_b)

    return clean_rgb.quantize(
        colors=colors,
        method=Image.Quantize.FASTOCTREE,
        dither=Image.Dither.NONE,
    ).convert("RGB")


def _convert_raw_to_pixel_sprite(
    raw_path: Path,
    out_path: Path,
    target_world_size: tuple[int, int],
    *,
    colors: int = 24,
    foot_y_native: int,
    max_body_h_native: int,
) -> None:
    gw = target_world_size[0] // 2
    gh = target_world_size[1] // 2
    with Image.open(raw_path) as src:
        rgba = _flood_clear_opaque_bg(src.convert("RGBA"))

    alpha_clean = rgba.getchannel("A").point(lambda v: v if v >= 22 else 0)
    bbox = alpha_clean.getbbox()
    if not bbox:
        raise RuntimeError(f"裁切透明区域后图像为空: {raw_path}")
    trimmed = rgba.crop(bbox)
    tw, th = trimmed.size

    usable_w = max(8, gw - 2)
    scale = min(usable_w / float(tw), max_body_h_native / float(th))
    sw = max(4, int(round(tw * scale)))
    sh = max(4, int(round(th * scale)))

    work = trimmed.resize((sw * 4, sh * 4), Image.Resampling.LANCZOS)
    work_rgb = work.convert("RGB").filter(ImageFilter.MedianFilter(size=3))
    work_rgb = ImageEnhance.Contrast(work_rgb).enhance(1.12)
    work_rgb = ImageEnhance.Color(work_rgb).enhance(1.14)
    work_rgba = _bleed_rgb_into_transparent(Image.merge("RGBA", (*work_rgb.split(), work.getchannel("A"))), passes=4)

    native_rgb = work_rgba.convert("RGB").resize((sw, sh), Image.Resampling.BILINEAR)
    native_a = work_rgba.getchannel("A").resize((sw, sh), Image.Resampling.BILINEAR).point(
        lambda v: 255 if v >= 115 else 0
    )
    quant_rgb = _quantize_opaque_pixels(native_rgb, native_a, colors=colors)
    fg_rgba = Image.merge("RGBA", (*quant_rgb.split(), native_a))

    native_canvas = Image.new("RGBA", (gw, gh), (0, 0, 0, 0))
    native_canvas.alpha_composite(fg_rgba, (max(1, (gw - sw) // 2), max(1, foot_y_native - sh)))
    _apply_1texel_outline(native_canvas)
    _save_pixel_2x(native_canvas, out_path)


def build_pixel_characters(*, overwrite: bool) -> None:
    for cid in CHARACTER_IDS:
        raw_path = CHIBI_RAW_DIR / f"{cid}-chibi-raw.png"
        out_path = CHIBI_OUT_DIR / f"{cid}.png"
        if not raw_path.is_file():
            raise FileNotFoundError(f"缺少角色原始母图: {raw_path}")
        if out_path.is_file() and out_path.stat().st_size > 0 and not overwrite:
            print(f"[SKIP-CHAR] {out_path}")
            continue
        _convert_raw_to_pixel_sprite(
            raw_path,
            out_path,
            (76, 88),
            colors=24,
            foot_y_native=41,
            max_body_h_native=38,
        )
        print(f"[OK-CHAR] {out_path} (76x88, 2x pixel)")


# ---------------------------------------------------------------------------
# 严格正交 3/4 唐风像素家具、茶亭、宫灯与园林树木绘制器
# ---------------------------------------------------------------------------

def _draw_orthogonal_desk_frame(
    draw: ImageDraw.ImageDraw,
    x0: int,
    y_top: int,
    x1: int,
    y_front: int,
    y_foot: int,
    wood_ramp: tuple[tuple[int, int, int, int], ...],
    *,
    brass_fittings: bool = True,
    runner_color: tuple[int, int, int, int] | None = None,
) -> None:
    """绘制严格水平正交的 3/4 俯视桌案骨架：顶面、边沿亮线、前裙板抽屉与直立桌腿。"""
    c_dark, c_mid, c_top, c_hi = wood_ramp
    # 四条桌腿（后腿隐约露内脚，前腿实体落地）
    _px_rect(draw, x0 + 2, y_front, x0 + 6, y_foot, c_dark)
    _px_rect(draw, x1 - 6, y_front, x1 - 2, y_foot, c_dark)
    _px_rect(draw, x0 + 3, y_front, x0 + 5, y_foot - 1, c_mid)
    _px_rect(draw, x1 - 5, y_front, x1 - 3, y_foot - 1, c_mid)
    # 腿间下横枨
    _px_rect(draw, x0 + 6, y_foot - 4, x1 - 6, y_foot - 2, c_dark)

    # 桌案正面裙板与抽屉
    apron_b = min(y_foot - 4, y_front + 8)
    _px_rect(draw, x0 + 2, y_front, x1 - 2, apron_b, c_mid)
    _px_rect(draw, x0 + 2, apron_b - 1, x1 - 2, apron_b, c_dark)
    # 抽屉凹槽与铜环
    w = x1 - x0
    if w >= 40:
        mid = (x0 + x1) // 2
        for dx0, dx1 in [(x0 + 8, mid - 2), (mid + 2, x1 - 8)]:
            _px_rect(draw, dx0, y_front + 2, dx1, apron_b - 2, c_dark)
            _px_rect(draw, dx0 + 1, y_front + 3, dx1 - 1, apron_b - 3, c_mid)
            if brass_fittings:
                dcx = (dx0 + dx1) // 2
                _px_rect(draw, dcx - 1, y_front + 4, dcx + 1, y_front + 6, (220, 178, 72, 255))

    # 桌面台面（顶面 + 厚度前檐）
    _px_rect(draw, x0, y_top, x1, y_front - 1, c_top)
    _px_rect(draw, x0 + 1, y_top + 1, x1 - 1, y_front - 2, c_top)
    draw.line([x0 + 1, y_top, x1 - 2, y_top], fill=c_hi)
    # 桌面木纹条
    for py in range(y_top + 3, y_front - 3, 4):
        draw.line([x0 + 3, py, x1 - 4, py], fill=c_mid)
    # 桌沿厚度立边
    _px_rect(draw, x0, y_front - 2, x1, y_front, c_hi)
    _px_rect(draw, x0, y_front - 1, x1, y_front + 1, c_dark)

    if runner_color is not None:
        mid = (x0 + x1) // 2
        _px_rect(draw, mid - 7, y_top + 1, mid + 7, y_front, runner_color)
        draw.line([mid - 6, y_top + 1, mid - 6, y_front - 1], fill=(226, 186, 86, 255))
        draw.line([mid + 5, y_top + 1, mid + 5, y_front - 1], fill=(226, 186, 86, 255))


ROSEWOOD_RAMP = (
    (74, 38, 30, 255),
    (106, 54, 42, 255),
    (138, 74, 54, 255),
    (168, 98, 72, 255),
)
OAK_RAMP = (
    (96, 62, 36, 255),
    (132, 88, 52, 255),
    (168, 118, 72, 255),
    (196, 146, 94, 255),
)
WALNUT_RAMP = (
    (56, 40, 34, 255),
    (82, 58, 48, 255),
    (108, 78, 64, 255),
    (134, 100, 82, 255),
)


def _item_shadow(draw: ImageDraw.ImageDraw, x0: int, y0: int, x1: int, y1: int, col: tuple[int, int, int, int] = (72, 42, 26, 255)) -> None:
    """在桌面上为桌面器物下方添加 1px 接地投影，消除平面贴纸感。"""
    _px_rect(draw, x0 + 1, y1, x1 + 1, y1 + 1, col)
    _px_rect(draw, x1, y0 + 1, x1 + 1, y1 + 1, col)


def _draw_throne_dais() -> Image.Image:
    gw, gh = 80, 55
    img = Image.new("RGBA", (gw, gh), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # 1. 北侧千里江山三折屏风（x: 15..65, y: 4..30，带屏风顶冠饰）
    _px_rect(d, 15, 4, 65, 30, (86, 54, 34, 255))
    _px_rect(d, 16, 3, 64, 5, (186, 144, 54, 255))
    for px0, px1 in [(17, 31), (33, 47), (49, 63)]:
        _px_rect(d, px0, 6, px1, 28, (228, 216, 188, 255))
        d.polygon([(px0 + 1, 27), (px0 + 5, 16), (px1 - 2, 27)], fill=(124, 146, 134, 255))
        d.polygon([(px0 + 3, 27), ((px0 + px1) // 2, 10), (px1 - 1, 27)], fill=(86, 112, 102, 255))
        # 山顶松墨点缀
        d.point(((px0 + px1) // 2, 12), fill=(58, 78, 70, 255))
    _px_rect(d, 39, 8, 42, 11, (220, 92, 62, 255))

    # 2. 多级木陛高台、两侧雕栏与正中三道红毯丹陛阶梯
    _px_rect(d, 9, 28, 71, 48, (108, 52, 36, 255))
    _px_rect(d, 10, 28, 70, 42, (152, 84, 54, 255))
    d.line([10, 28, 69, 28], fill=(182, 110, 74, 255))
    _px_rect(d, 9, 42, 71, 48, (76, 36, 26, 255))
    for rx in range(12, 68, 5):
        if 27 <= rx <= 52:
            continue
        _px_rect(d, rx, 24, rx + 2, 29, (162, 92, 58, 255))
    _px_rect(d, 9, 25, 28, 27, (196, 134, 72, 255))
    _px_rect(d, 52, 25, 71, 27, (196, 134, 72, 255))
    for s in range(3):
        sy = 43 + s * 3
        _px_rect(d, 29, sy, 51, sy + 3, (186 - s * 16, 174 - s * 16, 158 - s * 16, 255))
        _px_rect(d, 33, sy, 47, sy + 3, (172 - s * 14, 38, 42, 255))
        d.line([34, sy, 34, sy + 2], fill=(224, 180, 74, 255))
        d.line([45, sy, 45, sy + 2], fill=(224, 180, 74, 255))

    # 3. 鎏金九龙御坐宝座（拱形龙首靠背 + 曲形扶手 + 锦绣坐垫）
    _px_rect(d, 28, 30, 52, 39, (172, 120, 34, 255))
    _px_rect(d, 31, 13, 49, 30, (226, 176, 62, 255))
    _px_rect(d, 33, 11, 47, 14, (242, 202, 92, 255))
    _px_rect(d, 38, 9, 42, 12, (250, 224, 132, 255))
    _px_rect(d, 33, 15, 47, 29, (166, 36, 42, 255))
    # 背板金龙纹
    _px_rect(d, 36, 17, 44, 24, (238, 194, 82, 255))
    _px_rect(d, 38, 19, 42, 22, (178, 44, 48, 255))
    # 扶手与朱红龙座垫
    _px_rect(d, 31, 28, 49, 34, (196, 46, 48, 255))
    _px_rect(d, 32, 29, 48, 31, (226, 78, 72, 255))
    _px_rect(d, 26, 24, 32, 34, (232, 182, 68, 255))
    _px_rect(d, 48, 24, 54, 34, (232, 182, 68, 255))
    _px_rect(d, 27, 23, 30, 25, (248, 214, 108, 255))
    _px_rect(d, 50, 23, 53, 25, (248, 214, 108, 255))

    # 4. 两侧立鹤香炉（S 形鹤颈 + 展翼炉身 + 朱顶 + 青烟）
    for cx, dir_s in [(16, 1), (63, -1)]:
        _px_rect(d, cx - 3, 37, cx + 4, 41, (166, 158, 144, 255))
        _px_rect(d, cx - 1, 31, cx + 2, 37, (96, 114, 98, 255))
        # 鹤身与展翅
        _px_rect(d, cx - 3, 27, cx + 4, 31, (124, 146, 128, 255))
        _px_rect(d, cx - 2, 26, cx + 3, 28, (154, 176, 156, 255))
        # 曲颈与丹顶
        d.line([cx + dir_s, 26, cx, 22], fill=(138, 160, 140, 255))
        _px_rect(d, cx - 1, 20, cx + 2, 22, (236, 94, 62, 255))
        d.point((cx, 17), fill=(224, 230, 232, 200))

    _apply_1texel_outline(img)
    _add_ellipse_shadow(img, 11, 49, 69, 53)
    return img


def _draw_sandbox_table() -> Image.Image:
    gw, gh = 90, 55
    img = Image.new("RGBA", (gw, gh), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    _draw_orthogonal_desk_frame(d, 6, 12, 84, 38, 51, ROSEWOOD_RAMP)

    # 沙盘槽内立体郡县山川地形（x: 11..79, y: 15..35）
    _px_rect(d, 10, 14, 80, 36, (88, 52, 38, 255))
    _px_rect(d, 11, 15, 79, 35, (158, 146, 108, 255))
    _px_rect(d, 13, 17, 37, 33, (108, 144, 82, 255))
    _px_rect(d, 48, 18, 77, 33, (120, 154, 90, 255))
    # 蜿蜒蓝水河道与浅滩高光
    for rx, ry in [(34, 16), (36, 19), (38, 22), (40, 25), (43, 28), (46, 31)]:
        _px_rect(d, rx, ry, rx + 5, ry + 4, (64, 128, 164, 255))
        _px_rect(d, rx + 1, ry + 1, rx + 3, ry + 2, (112, 178, 208, 255))
    # 北侧立体山峦
    for mx, mh in [(18, 5), (26, 7), (52, 6), (62, 8), (70, 5)]:
        d.polygon([(mx - 5, 22), (mx, 22 - mh), (mx + 5, 22)], fill=(124, 114, 92, 255))
        d.polygon([(mx - 3, 22), (mx, 22 - mh + 1), (mx + 1, 22)], fill=(164, 152, 124, 255))
        _px_rect(d, mx - 1, 22 - mh, mx + 2, 22 - mh + 2, (206, 196, 166, 255))
    # 微缩城池与小旗
    for cx, cy, fcol in [(24, 27, (212, 56, 52, 255)), (44, 21, (226, 182, 58, 255)), (64, 27, (68, 148, 216, 255))]:
        _px_rect(d, cx - 3, cy - 2, cx + 3, cy + 2, (196, 188, 172, 255))
        _px_rect(d, cx - 2, cy - 1, cx + 2, cy + 1, (148, 142, 130, 255))
        d.line([cx, cy - 6, cx, cy - 1], fill=(74, 48, 32, 255))
        _px_rect(d, cx + 1, cy - 6, cx + 4, cy - 3, fcol)

    # 四角精致小铜灯盏（石座 + 铜柱 + 暖光罩 + 小尖顶）
    for lx, ly in [(10, 13), (79, 13), (10, 35), (79, 35)]:
        _px_rect(d, lx - 1, ly - 4, lx + 2, ly + 1, (164, 128, 56, 255))
        _px_rect(d, lx - 2, ly - 8, lx + 3, ly - 4, (246, 194, 78, 255))
        _px_rect(d, lx - 1, ly - 7, lx + 2, ly - 5, (255, 242, 176, 255))
        _px_rect(d, lx - 2, ly - 9, lx + 3, ly - 8, (132, 86, 42, 255))

    _apply_1texel_outline(img)
    _add_ellipse_shadow(img, 8, 49, 82, 53)
    return img


def _draw_desk_chizheng() -> Image.Image:
    gw, gh = 75, 42
    img = Image.new("RGBA", (gw, gh), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    _draw_orthogonal_desk_frame(d, 5, 11, 70, 27, 38, ROSEWOOD_RAMP)
    sh = (82, 42, 30, 255)
    # 左侧成捆卷轴（带木轴头与红丝带）
    _item_shadow(d, 9, 13, 25, 23, sh)
    _px_rect(d, 9, 17, 25, 22, (226, 206, 152, 255))
    _px_rect(d, 10, 12, 24, 17, (240, 222, 170, 255))
    for rx in (9, 24):
        _px_rect(d, rx, 13, rx + 2, 16, (108, 62, 38, 255))
        _px_rect(d, rx, 18, rx + 2, 21, (108, 62, 38, 255))
    _px_rect(d, 16, 12, 18, 22, (176, 42, 40, 255))
    # 中央朱笔架 + 展开奏折
    _px_rect(d, 30, 7, 45, 13, (154, 40, 36, 255))
    _px_rect(d, 31, 9, 44, 12, (82, 42, 30, 255))
    for bx in (33, 37, 41):
        d.line([bx, 8, bx, 13], fill=(42, 36, 36, 255))
        d.point((bx, 13), fill=(214, 62, 54, 255))
    _item_shadow(d, 28, 15, 46, 24, sh)
    _px_rect(d, 28, 15, 46, 24, (246, 238, 214, 255))
    _px_rect(d, 31, 17, 43, 18, (64, 58, 54, 255))
    _px_rect(d, 31, 20, 40, 21, (188, 46, 42, 255))
    # 右侧碧玉官印（底座+玉玺+金绶带）与端砚
    _item_shadow(d, 49, 14, 57, 21, sh)
    _px_rect(d, 49, 17, 57, 21, (92, 54, 34, 255))
    _px_rect(d, 50, 13, 56, 18, (132, 192, 154, 255))
    _px_rect(d, 52, 12, 54, 14, (172, 224, 186, 255))
    _px_rect(d, 54, 18, 56, 21, (226, 182, 68, 255))
    _item_shadow(d, 59, 14, 66, 21, sh)
    _px_rect(d, 59, 14, 66, 21, (54, 56, 64, 255))
    _px_rect(d, 61, 16, 64, 19, (34, 36, 42, 255))
    _apply_1texel_outline(img)
    _add_ellipse_shadow(img, 7, 36, 68, 40)
    return img


def _draw_desk_bina() -> Image.Image:
    gw, gh = 75, 42
    img = Image.new("RGBA", (gw, gh), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    _draw_orthogonal_desk_frame(d, 5, 11, 70, 27, 38, OAK_RAMP)
    sh = (108, 70, 42, 255)
    # 左侧倾斜木质日程翻页牌
    _item_shadow(d, 10, 7, 22, 19, sh)
    _px_rect(d, 10, 7, 22, 19, (138, 86, 48, 255))
    _px_rect(d, 12, 9, 20, 17, (248, 240, 220, 255))
    d.line([13, 11, 19, 11], fill=(192, 104, 124, 255))
    d.line([13, 14, 18, 14], fill=(112, 96, 86, 255))
    # 中间青瓷茶盏（圆托盘+杯口高光）与椭圆形点心碟
    _item_shadow(d, 26, 13, 33, 20, sh)
    d.ellipse([25, 15, 34, 21], fill=(138, 194, 174, 255))
    _px_rect(d, 27, 13, 32, 18, (112, 172, 152, 255))
    _px_rect(d, 28, 14, 31, 16, (176, 214, 184, 255))
    _item_shadow(d, 35, 17, 47, 24, sh)
    d.ellipse([34, 16, 48, 24], fill=(238, 232, 216, 255), outline=(188, 182, 166, 255))
    _px_rect(d, 37, 18, 41, 21, (238, 182, 86, 255))
    _px_rect(d, 41, 19, 45, 22, (226, 160, 74, 255))
    d.point((39, 18), fill=(214, 58, 56, 255))
    # 白瓷细颈花瓶与樱粉花束
    _item_shadow(d, 47, 11, 53, 18, sh)
    _px_rect(d, 48, 13, 52, 18, (236, 240, 244, 255))
    _px_rect(d, 49, 11, 51, 14, (216, 224, 230, 255))
    _px_rect(d, 47, 6, 53, 11, (244, 158, 182, 255))
    d.point((48, 7), fill=(254, 216, 226, 255))
    d.point((52, 9), fill=(116, 168, 94, 255))
    # 右侧手账本
    _item_shadow(d, 55, 15, 65, 23, sh)
    _px_rect(d, 55, 15, 65, 23, (246, 238, 214, 255))
    _px_rect(d, 55, 15, 57, 23, (176, 94, 122, 255))
    _apply_1texel_outline(img)
    _add_ellipse_shadow(img, 7, 36, 68, 40)
    return img


def _draw_shelf_archives() -> Image.Image:
    gw, gh = 88, 43
    img = Image.new("RGBA", (gw, gh), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    _px_rect(d, 4, 4, 84, 40, (98, 62, 38, 255))
    _px_rect(d, 3, 2, 85, 7, (74, 82, 92, 255))
    d.line([4, 2, 83, 2], fill=(122, 130, 142, 255))
    draw_cols = [(164, 46, 44, 255), (218, 176, 78, 255), (72, 118, 152, 255), (226, 212, 178, 255)]
    for tier_y in (9, 18, 27):
        _px_rect(d, 7, tier_y, 81, tier_y + 7, (46, 30, 22, 255))
        for col_x in range(9, 78, 18):
            _px_rect(d, col_x - 2, tier_y - 1, col_x, tier_y + 8, (128, 84, 52, 255))
            for k in range(4):
                scol = draw_cols[(tier_y + col_x + k) % len(draw_cols)]
                _px_rect(d, col_x + k * 4, tier_y + 1, col_x + k * 4 + 3, tier_y + 6, scol)
                d.point((col_x + k * 4 + 1, tier_y + 2), fill=(250, 240, 216, 255))
    _px_rect(d, 6, 35, 82, 40, (124, 80, 50, 255))
    _px_rect(d, 42, 36, 46, 39, (218, 176, 72, 255))
    _apply_1texel_outline(img)
    _add_ellipse_shadow(img, 5, 38, 83, 42)
    return img


def _draw_desk_taki() -> Image.Image:
    gw, gh = 68, 38
    img = Image.new("RGBA", (gw, gh), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    _draw_orthogonal_desk_frame(d, 5, 10, 63, 24, 35, WALNUT_RAMP)
    sh = (62, 42, 34, 255)
    _px_rect(d, 9, 6, 27, 17, (72, 46, 36, 255))
    for i in range(5):
        col = (168, 42, 46, 255) if i % 2 == 0 else (48, 48, 56, 255)
        _px_rect(d, 10 + i * 3, 4, 12 + i * 3, 15, col)
        d.point((11 + i * 3, 6), fill=(236, 224, 192, 255))
    _item_shadow(d, 30, 14, 46, 21, sh)
    _px_rect(d, 30, 14, 46, 21, (242, 236, 222, 255))
    d.line([33, 12, 38, 19], fill=(186, 42, 42, 255))
    d.line([37, 12, 42, 19], fill=(32, 32, 38, 255))
    _item_shadow(d, 48, 14, 58, 17, sh)
    _px_rect(d, 48, 14, 58, 17, (212, 174, 72, 255))
    _px_rect(d, 50, 18, 60, 22, (118, 82, 54, 255))
    _apply_1texel_outline(img)
    _add_ellipse_shadow(img, 7, 33, 61, 37)
    return img


def _draw_shelf_lantai() -> Image.Image:
    gw, gh = 70, 44
    img = Image.new("RGBA", (gw, gh), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    _px_rect(d, 6, 4, 64, 41, (108, 68, 42, 255))
    _px_rect(d, 5, 3, 65, 6, (144, 96, 62, 255))
    book_cols = [(52, 86, 132, 255), (68, 112, 154, 255), (214, 204, 178, 255), (86, 132, 118, 255)]
    for tier_y in (8, 17, 26, 34):
        _px_rect(d, 9, tier_y, 61, tier_y + 7, (44, 28, 22, 255))
        for bx in range(10, 58, 4):
            bcol = book_cols[(tier_y + bx) % len(book_cols)]
            _px_rect(d, bx, tier_y + 1, bx + 3, tier_y + 6, bcol)
        for tx in (18, 34, 50):
            _px_rect(d, tx, tier_y + 5, tx + 3, tier_y + 8, (218, 182, 108, 255))
    _apply_1texel_outline(img)
    _add_ellipse_shadow(img, 7, 39, 63, 43)
    return img


def _draw_workbench_bit() -> Image.Image:
    gw, gh = 78, 45
    img = Image.new("RGBA", (gw, gh), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    _draw_orthogonal_desk_frame(d, 5, 13, 73, 30, 42, OAK_RAMP, brass_fittings=False)
    sh = (108, 70, 42, 255)
    # 后排悬挂工具架（凿/锯/扳手轮廓）
    _px_rect(d, 9, 5, 29, 15, (92, 62, 38, 255))
    for tx in (12, 17, 22, 26):
        _px_rect(d, tx, 7, tx + 2, 13, (176, 184, 194, 255))
        d.point((tx, 13), fill=(196, 146, 82, 255))
    # 铺开的青色工程蓝图
    _item_shadow(d, 24, 17, 52, 27, sh)
    _px_rect(d, 24, 17, 52, 27, (56, 114, 162, 255))
    d.rectangle([26, 19, 49, 25], outline=(196, 232, 252, 255))
    d.line([28, 22, 47, 22], fill=(196, 232, 252, 255))
    # 精密带齿黄铜齿轮
    _px_rect(d, 55, 16, 61, 22, (220, 176, 68, 255))
    _px_rect(d, 57, 15, 59, 23, (238, 200, 96, 255))
    _px_rect(d, 54, 18, 62, 20, (238, 200, 96, 255))
    _px_rect(d, 57, 18, 59, 20, (92, 62, 38, 255))
    _px_rect(d, 63, 19, 68, 24, (192, 148, 54, 255))
    # 左侧青铜卡尺
    _px_rect(d, 10, 19, 20, 21, (178, 186, 196, 255))
    _px_rect(d, 10, 21, 12, 24, (152, 160, 172, 255))
    _px_rect(d, 15, 21, 17, 24, (152, 160, 172, 255))
    _apply_1texel_outline(img)
    _add_ellipse_shadow(img, 7, 40, 71, 44)
    return img


def _draw_atelier_vinci() -> Image.Image:
    gw, gh = 65, 42
    img = Image.new("RGBA", (gw, gh), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    _draw_orthogonal_desk_frame(d, 4, 14, 44, 28, 39, OAK_RAMP, runner_color=(168, 54, 48, 255))
    for px, py, pcol in [
        (9, 17, (58, 118, 212, 255)),
        (15, 17, (68, 172, 98, 255)),
        (9, 22, (212, 68, 54, 255)),
        (15, 22, (236, 192, 68, 255)),
    ]:
        _px_rect(d, px, py, px + 4, py + 4, (226, 218, 202, 255))
        _px_rect(d, px + 1, py + 1, px + 3, py + 3, pcol)
    _px_rect(d, 31, 16, 40, 23, (238, 226, 192, 255))
    _px_rect(d, 31, 24, 41, 26, (112, 72, 44, 255))

    _px_rect(d, 48, 22, 51, 39, (124, 82, 48, 255))
    _px_rect(d, 58, 22, 61, 39, (124, 82, 48, 255))
    _px_rect(d, 53, 5, 56, 36, (112, 72, 42, 255))
    _px_rect(d, 47, 8, 62, 23, (152, 104, 62, 255))
    _px_rect(d, 48, 9, 61, 21, (242, 234, 210, 255))
    d.polygon([(49, 20), (54, 13), (60, 20)], fill=(96, 138, 108, 255))
    _px_rect(d, 57, 11, 59, 13, (228, 108, 68, 255))

    _apply_1texel_outline(img)
    _add_ellipse_shadow(img, 6, 37, 62, 41)
    return img


def _draw_shelf_qianjin() -> Image.Image:
    gw, gh = 36, 58
    img = Image.new("RGBA", (gw, gh), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    _px_rect(d, 6, 4, 32, 46, (108, 66, 42, 255))
    _px_rect(d, 5, 3, 33, 7, (142, 92, 58, 255))
    for row in range(6):
        ry = 9 + row * 6
        for col in range(4):
            cx = 8 + col * 6
            _px_rect(d, cx, ry, cx + 5, ry + 5, (148, 96, 62, 255))
            _px_rect(d, cx + 1, ry + 1, cx + 4, ry + 3, (224, 208, 172, 255))
            d.point((cx + 2, ry + 4), fill=(212, 174, 72, 255))
    # 石臼与药杵
    d.ellipse([3, 47, 12, 55], fill=(148, 152, 156, 255))
    _px_rect(d, 5, 47, 10, 50, (108, 112, 118, 255))
    d.line([8, 44, 11, 49], fill=(192, 196, 200, 255), width=2)
    # 煎药小泥炉与红火苗
    _px_rect(d, 14, 46, 23, 55, (124, 76, 54, 255))
    _px_rect(d, 15, 43, 22, 47, (54, 54, 58, 255))
    _px_rect(d, 17, 50, 20, 53, (242, 146, 54, 255))
    d.point((18, 51), fill=(255, 224, 118, 255))
    # 竹匾晒草药
    d.ellipse([24, 49, 34, 55], fill=(196, 166, 98, 255))
    d.ellipse([25, 50, 33, 54], fill=(92, 146, 78, 255))
    _apply_1texel_outline(img)
    _add_ellipse_shadow(img, 4, 52, 33, 56)
    return img


def _draw_stone_table() -> Image.Image:
    """圆润雕花青石圆桌 + 四只八角圆形石鼓凳 + 曲柄青瓷茶壶。"""
    gw, gh = 64, 44
    img = Image.new("RGBA", (gw, gh), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # 四只圆形石鼓凳（N/W/E/S）
    for sx, sy in [(26, 3), (7, 17), (45, 17), (26, 28)]:
        d.ellipse([sx, sy + 3, sx + 12, sy + 13], fill=(116, 120, 124, 255))
        d.ellipse([sx + 1, sy, sx + 11, sy + 8], fill=(182, 186, 188, 255), outline=(138, 142, 146, 255))
        _px_rect(d, sx + 4, sy + 9, sx + 8, sy + 11, (76, 80, 86, 255))
    # 中央雕花青石圆桌立柱与桌面
    _px_rect(d, 26, 23, 38, 36, (108, 112, 116, 255))
    _px_rect(d, 28, 24, 34, 35, (138, 142, 146, 255))
    d.ellipse([16, 11, 48, 30], fill=(154, 158, 162, 255))
    d.ellipse([17, 10, 47, 27], fill=(188, 192, 194, 255), outline=(128, 132, 136, 255))
    d.ellipse([20, 12, 44, 25], outline=(156, 150, 132, 255))
    # 青瓷提梁茶壶与三只小茶杯
    d.ellipse([28, 14, 35, 20], fill=(116, 178, 152, 255))
    d.arc([29, 11, 34, 16], 180, 360, fill=(148, 204, 178, 255))
    d.point((36, 16), fill=(116, 178, 152, 255))
    for cx, cy in [(24, 18), (37, 19), (32, 21)]:
        _px_rect(d, cx, cy, cx + 3, cy + 2, (162, 214, 188, 255))
    _apply_1texel_outline(img)
    _add_ellipse_shadow(img, 10, 35, 54, 42)
    return img


def _draw_desk_boming() -> Image.Image:
    gw, gh = 73, 40
    img = Image.new("RGBA", (gw, gh), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    _draw_orthogonal_desk_frame(d, 5, 10, 68, 25, 37, OAK_RAMP)
    sh = (108, 70, 42, 255)
    # 弧形白羽扇（圆润扇面 + 羽骨线 + 深木柄与红穗）
    _item_shadow(d, 9, 14, 19, 20, sh)
    d.polygon([(9, 18), (11, 13), (17, 12), (20, 16), (17, 20), (11, 20)], fill=(246, 244, 236, 255))
    d.line([14, 13, 16, 19], fill=(214, 212, 204, 255))
    d.line([16, 19, 20, 23], fill=(92, 62, 38, 255))
    d.point((20, 23), fill=(192, 52, 48, 255))
    # 围棋盘 + 黑白棋子
    _item_shadow(d, 23, 12, 43, 24, sh)
    _px_rect(d, 23, 12, 43, 24, (206, 166, 94, 255))
    for gx in range(25, 42, 4):
        d.line([gx, 13, gx, 22], fill=(124, 92, 48, 255))
    for gy in range(14, 23, 3):
        d.line([25, gy, 40, gy], fill=(124, 92, 48, 255))
    for wx, wy, scol in [
        (28, 15, (246, 246, 246, 255)),
        (36, 17, (36, 36, 42, 255)),
        (32, 20, (246, 246, 246, 255)),
        (38, 14, (36, 36, 42, 255)),
    ]:
        _px_rect(d, wx, wy, wx + 2, wy + 2, scol)
    # 锦囊匣与地图卷
    _item_shadow(d, 47, 12, 57, 19, sh)
    _px_rect(d, 47, 12, 57, 19, (62, 86, 142, 255))
    _px_rect(d, 51, 12, 53, 19, (192, 54, 48, 255))
    _item_shadow(d, 58, 14, 65, 22, sh)
    _px_rect(d, 58, 14, 65, 22, (236, 224, 186, 255))
    _apply_1texel_outline(img)
    _add_ellipse_shadow(img, 7, 35, 66, 39)
    return img


def _draw_desk_jiafa() -> Image.Image:
    gw, gh = 73, 40
    img = Image.new("RGBA", (gw, gh), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    _draw_orthogonal_desk_frame(d, 5, 10, 68, 25, 37, ROSEWOOD_RAMP)
    sh = (82, 42, 30, 255)
    _item_shadow(d, 10, 13, 27, 22, sh)
    _px_rect(d, 10, 13, 27, 22, (164, 114, 66, 255))
    for lx in range(12, 26, 3):
        d.line([lx, 15, lx, 20], fill=(78, 48, 30, 255))
    _item_shadow(d, 30, 15, 38, 21, sh)
    _px_rect(d, 30, 15, 38, 21, (48, 50, 56, 255))
    _px_rect(d, 32, 12, 36, 15, (148, 92, 52, 255))
    _item_shadow(d, 43, 12, 55, 22, sh)
    _px_rect(d, 43, 12, 55, 22, (242, 234, 212, 255))
    _px_rect(d, 56, 14, 65, 22, (234, 224, 198, 255))
    _px_rect(d, 45, 14, 53, 16, (176, 48, 44, 255))
    _apply_1texel_outline(img)
    _add_ellipse_shadow(img, 7, 35, 66, 39)
    return img


def _draw_desk_planck() -> Image.Image:
    gw, gh = 73, 40
    img = Image.new("RGBA", (gw, gh), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    _draw_orthogonal_desk_frame(d, 5, 10, 68, 25, 37, WALNUT_RAMP)
    sh = (62, 42, 34, 255)
    _item_shadow(d, 9, 12, 21, 18, sh)
    _px_rect(d, 9, 12, 21, 18, (152, 104, 58, 255))
    _px_rect(d, 11, 14, 19, 16, (226, 192, 118, 255))
    _item_shadow(d, 23, 13, 44, 23, sh)
    _px_rect(d, 23, 13, 44, 23, (244, 236, 214, 255))
    for gy in (15, 18, 21):
        d.line([25, gy, 41, gy], fill=(66, 62, 58, 255))
    _px_rect(d, 46, 5, 62, 18, (124, 82, 48, 255))
    _px_rect(d, 48, 7, 60, 15, (42, 50, 56, 255))
    d.line([50, 9, 57, 9], fill=(236, 236, 224, 255))
    d.line([50, 12, 55, 12], fill=(236, 236, 224, 255))
    _px_rect(d, 52, 19, 64, 23, (218, 178, 78, 255))
    _apply_1texel_outline(img)
    _add_ellipse_shadow(img, 7, 35, 66, 39)
    return img


def _draw_tea_pavilion() -> Image.Image:
    """严格正交 3/4 俯视角唐风飞檐茶亭（反宇飞檐凹曲线攒尖顶、斗拱、四朱柱、花窗美人靠、内设石茶几与南阶）。"""
    gw, gh = 84, 68
    img = Image.new("RGBA", (gw, gh), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # 1. 青石台基与南向踏步
    _px_rect(d, 8, 52, 76, 61, (142, 138, 130, 255))
    _px_rect(d, 9, 44, 75, 54, (186, 180, 168, 255))
    _px_rect(d, 13, 42, 71, 52, (154, 106, 64, 255))
    # 亭内圆形石茶几与茶盏
    d.ellipse([35, 41, 49, 49], fill=(188, 192, 194, 255), outline=(132, 136, 140, 255))
    _px_rect(d, 40, 40, 44, 43, (112, 176, 150, 255))

    for s in range(3):
        sy = 54 + s * 3
        col = (204 - s * 16, 198 - s * 16, 184 - s * 16, 255)
        _px_rect(d, 32, sy, 52, sy + 3, col)
    _px_rect(d, 30, 54, 33, 63, (156, 150, 140, 255))
    _px_rect(d, 51, 54, 54, 63, (156, 150, 140, 255))

    # 2. 檐下深影、美人靠花窗栏杆与四朱柱
    _px_rect(d, 13, 33, 71, 41, (54, 36, 32, 255))
    _px_rect(d, 13, 45, 32, 52, (156, 44, 38, 255))
    _px_rect(d, 52, 45, 71, 52, (156, 44, 38, 255))
    _px_rect(d, 15, 47, 30, 50, (206, 144, 78, 255))
    _px_rect(d, 54, 47, 69, 50, (206, 144, 78, 255))
    for px in (12, 68):
        _px_rect(d, px, 31, px + 4, 53, (168, 46, 38, 255))
        d.line([px + 1, 31, px + 1, 52], fill=(208, 72, 58, 255))
        _px_rect(d, px - 1, 51, px + 5, 54, (198, 192, 180, 255))

    # 3. 额枋斗拱与凹曲唐风飞檐攒尖顶（举折曲面 + 翘起角檐）
    _px_rect(d, 10, 31, 74, 34, (148, 38, 32, 255))
    for bx in range(15, 70, 8):
        _px_rect(d, bx, 31, bx + 4, 33, (216, 170, 68, 255))
    # 反宇曲面屋坡（顶部陡、翼角舒展外翘）
    for row in range(23):
        y = 9 + row
        t = row / 22.0
        half_w = int(round(4.0 + 36.0 * (t ** 1.28)))
        rx0 = max(2, 42 - half_w)
        rx1 = min(82, 42 + half_w)
        _px_rect(d, rx0, y, rx1, y + 1, (72, 80, 90, 255))
        for tx in range(rx0 + 2, rx1 - 1, 4):
            d.point((tx, y), fill=(98, 108, 120, 255))
            d.point((tx + 1, y), fill=(52, 58, 66, 255))
        # 四角脊棱高亮
        d.point((rx0, y), fill=(136, 146, 158, 255))
        d.point((rx1 - 1, y), fill=(136, 146, 158, 255))
    # 飞檐翘角（左右端向上挑起 2px）
    _px_rect(d, 2, 28, 7, 31, (98, 108, 120, 255))
    _px_rect(d, 77, 28, 82, 31, (98, 108, 120, 255))
    _px_rect(d, 4, 31, 80, 33, (88, 96, 108, 255))
    for wx in range(6, 78, 4):
        _px_rect(d, wx, 32, wx + 2, 34, (124, 132, 144, 255))
    # 鎏金宝顶
    _px_rect(d, 40, 4, 44, 9, (228, 182, 68, 255))
    _px_rect(d, 41, 2, 43, 5, (248, 216, 114, 255))

    _apply_1texel_outline(img)
    _add_ellipse_shadow(img, 8, 60, 76, 65)
    return img


def _draw_palace_lantern() -> Image.Image:
    gw, gh = 28, 48
    img = Image.new("RGBA", (gw, gh), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    _px_rect(d, 7, 41, 21, 45, (158, 152, 142, 255))
    _px_rect(d, 9, 38, 19, 42, (186, 180, 168, 255))
    _px_rect(d, 12, 23, 16, 38, (162, 46, 38, 255))
    d.line([13, 24, 13, 37], fill=(204, 68, 54, 255))
    _px_rect(d, 7, 10, 21, 23, (156, 44, 36, 255))
    _px_rect(d, 9, 12, 19, 21, (246, 188, 76, 255))
    _px_rect(d, 11, 14, 17, 19, (255, 232, 146, 255))
    d.line([14, 12, 14, 20], fill=(148, 42, 34, 255))
    _px_rect(d, 5, 8, 23, 11, (76, 84, 94, 255))
    _px_rect(d, 8, 5, 20, 8, (96, 104, 116, 255))
    _px_rect(d, 13, 3, 15, 5, (232, 184, 72, 255))
    _apply_1texel_outline(img)
    _add_ellipse_shadow(img, 6, 43, 22, 47)
    return img


def _draw_organic_leaf_puff(
    draw: ImageDraw.ImageDraw,
    cx: int,
    cy: int,
    r: int,
    c_dark: tuple[int, int, int, int],
    c_mid: tuple[int, int, int, int],
    c_lit: tuple[int, int, int, int],
    c_hi: tuple[int, int, int, int],
) -> None:
    """绘制带暗部底托、中灰体量与左上受光新月高光的有机像素叶簇。"""
    draw.ellipse([cx - r, cy - r + 1, cx + r, cy + r], fill=c_dark)
    draw.ellipse([cx - r, cy - r, cx + r - 1, cy + r - 2], fill=c_mid)
    r2 = max(2, r - 2)
    draw.ellipse([cx - r2 - 1, cy - r + 1, cx + r2 - 1, cy + r2 - 1], fill=c_lit)
    r3 = max(1, r // 2)
    draw.ellipse([cx - r2, cy - r + 1, cx - r2 + r3 + 1, cy - r + 2 + r3], fill=c_hi)


def _draw_tree_ginkgo() -> Image.Image:
    """手绘多层蓬松叶簇金秋银杏树（曲干分枝、14组有机叶团、无散点噪斑、落地生根）。"""
    gw, gh = 70, 75
    img = Image.new("RGBA", (gw, gh), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # 1. 苍劲主干与露根（bark texture + roots）
    _px_rect(d, 31, 42, 39, 70, (92, 56, 34, 255))
    _px_rect(d, 33, 43, 36, 69, (124, 80, 48, 255))
    d.line([34, 46, 34, 67], fill=(144, 96, 60, 255))
    _px_rect(d, 27, 68, 43, 71, (84, 50, 30, 255))
    _px_rect(d, 25, 70, 30, 72, (70, 42, 26, 255))
    _px_rect(d, 40, 70, 45, 72, (70, 42, 26, 255))
    d.line([33, 47, 20, 35], fill=(84, 50, 30, 255), width=3)
    d.line([37, 47, 50, 35], fill=(84, 50, 30, 255), width=3)

    # 2. 蓬松金杏叶簇（先画背阴底层，再逐层向上前方堆叠饱满叶团）
    ginkgo_ramp = (
        (146, 82, 20, 255),
        (198, 126, 28, 255),
        (234, 174, 48, 255),
        (250, 218, 96, 255),
    )
    back_puffs = [
        (16, 36, 9), (26, 39, 9), (44, 39, 9), (54, 36, 9),
        (13, 27, 8), (57, 27, 8), (35, 39, 10),
    ]
    mid_puffs = [
        (21, 30, 9), (35, 32, 10), (49, 30, 9),
        (20, 20, 8), (50, 20, 8), (35, 22, 10),
    ]
    top_puffs = [
        (26, 15, 7), (43, 15, 7), (35, 11, 8),
    ]
    for cx, cy, r in back_puffs:
        _draw_organic_leaf_puff(d, cx, cy, r, (124, 68, 16, 255), ginkgo_ramp[0], ginkgo_ramp[1], ginkgo_ramp[2])
    for cx, cy, r in mid_puffs:
        _draw_organic_leaf_puff(d, cx, cy, r, *ginkgo_ramp)
    for cx, cy, r in top_puffs:
        _draw_organic_leaf_puff(d, cx, cy, r, ginkgo_ramp[0], ginkgo_ramp[1], ginkgo_ramp[2], (254, 236, 144, 255))

    # 3. 树下少许飘落金叶
    for fx, fy in [(22, 70), (27, 72), (43, 71), (48, 69)]:
        _px_rect(d, fx, fy, fx + 2, fy + 1, (242, 188, 58, 255))

    _apply_1texel_outline(img)
    _add_ellipse_shadow(img, 18, 66, 52, 73)
    return img


def _draw_tree_willow() -> Image.Image:
    """手绘轻拂垂柳（曲折老树干、蓬松翠绿冠层、柔美交错弧线垂柳丝，彻底告别直线条）。"""
    gw, gh = 75, 80
    img = Image.new("RGBA", (gw, gh), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # 1. 微倾老树干与盘根
    _px_rect(d, 34, 42, 41, 74, (84, 54, 34, 255))
    _px_rect(d, 36, 44, 39, 73, (112, 74, 48, 255))
    _px_rect(d, 29, 72, 46, 76, (72, 46, 30, 255))

    # 2. 里层阴影垂柳幕帘（贴在树干后方与冠下阴影区）
    for sx, top_y, bot_y, bend in [
        (16, 32, 58, -2), (24, 28, 63, -1), (32, 30, 61, 0),
        (43, 30, 62, 1), (51, 28, 64, 2), (59, 32, 57, 2),
    ]:
        pts = [(sx, top_y), (sx + bend, (top_y + bot_y) // 2), (sx + bend, bot_y)]
        d.line(pts, fill=(40, 82, 44, 255), width=2)

    # 3. 上部蓬松翠柳冠层
    willow_ramp = (
        (42, 86, 46, 255),
        (64, 122, 60, 255),
        (94, 158, 76, 255),
        (134, 194, 96, 255),
    )
    for cx, cy, r in [(19, 30, 9), (56, 30, 9), (28, 23, 10), (47, 23, 10), (37, 16, 10), (37, 27, 10)]:
        _draw_organic_leaf_puff(d, cx, cy, r, *willow_ramp)

    # 4. 前层飘逸轻垂柳枝（弧形渐变长短交错丝帘，带嫩绿梢头）
    front_strands = [
        (13, 32, 56, -2, (58, 114, 56, 255), (94, 162, 78, 255)),
        (19, 28, 64, -1, (76, 138, 68, 255), (124, 188, 92, 255)),
        (26, 25, 66, -1, (88, 154, 74, 255), (138, 202, 102, 255)),
        (33, 27, 60, 0, (66, 126, 62, 255), (112, 178, 86, 255)),
        (41, 26, 63, 1, (92, 158, 78, 255), (140, 204, 104, 255)),
        (48, 25, 66, 1, (74, 136, 66, 255), (122, 186, 90, 255)),
        (55, 29, 62, 2, (62, 120, 58, 255), (106, 172, 84, 255)),
        (61, 33, 55, 2, (52, 104, 52, 255), (90, 154, 74, 255)),
    ]
    for sx, y0, y1, bend, col_main, col_tip in front_strands:
        ym = (y0 + y1) // 2
        d.line([(sx, y0), (sx + bend, ym), (sx + bend, y1 - 3)], fill=col_main, width=2)
        _px_rect(d, sx + bend, y1 - 3, sx + bend + 2, y1, col_tip)

    _apply_1texel_outline(img)
    _add_ellipse_shadow(img, 18, 71, 56, 78)
    return img


def build_pixel_props(*, overwrite: bool) -> None:
    builders = {
        "throne_dais": _draw_throne_dais,
        "sandbox_table": _draw_sandbox_table,
        "desk_chizheng": _draw_desk_chizheng,
        "desk_bina": _draw_desk_bina,
        "shelf_archives": _draw_shelf_archives,
        "desk_taki": _draw_desk_taki,
        "shelf_lantai": _draw_shelf_lantai,
        "workbench_bit": _draw_workbench_bit,
        "atelier_vinci": _draw_atelier_vinci,
        "shelf_qianjin": _draw_shelf_qianjin,
        "stone_table": _draw_stone_table,
        "desk_boming": _draw_desk_boming,
        "desk_jiafa": _draw_desk_jiafa,
        "desk_planck": _draw_desk_planck,
        "tea_pavilion": _draw_tea_pavilion,
        "palace_lantern": _draw_palace_lantern,
        "tree_willow": _draw_tree_willow,
        "tree_ginkgo": _draw_tree_ginkgo,
    }
    for pid, fn in builders.items():
        out_path = PROPS_OUT_DIR / f"{pid}.png"
        if out_path.is_file() and out_path.stat().st_size > 0 and not overwrite:
            print(f"[SKIP-PROP] {out_path}")
            continue
        native = fn()
        _save_pixel_2x(native, out_path)
        print(f"[OK-PROP] {out_path} ({native.width * 2}x{native.height * 2}, orthogonal pixel)")


# ---------------------------------------------------------------------------
# 800x560 原生像素级宫城底图（含融合绘制的莲池、戏台、预留地块与树池）与前景层
# ---------------------------------------------------------------------------

def _draw_pixel_grass(
    draw: ImageDraw.ImageDraw,
    rect: tuple[int, int, int, int],
    palette: list[tuple[int, int, int]],
    rng: random.Random,
    *,
    flower_density: float = 0.14,
) -> None:
    x0, y0, x1, y1 = rect
    _px_rect(draw, x0, y0, x1, y1, palette[0])
    for ty in range(y0, y1, 16):
        for tx in range(x0, x1, 16):
            bx1 = min(x1, tx + 16)
            by1 = min(y1, ty + 16)
            for _ in range(rng.randint(3, 6)):
                px = rng.randint(tx, max(tx, bx1 - 3))
                py = rng.randint(ty, max(ty, by1 - 2))
                pw = rng.randint(2, min(5, bx1 - px))
                ph = rng.randint(1, min(3, by1 - py))
                _px_rect(draw, px, py, px + pw, py + ph, palette[1])
            for _ in range(rng.randint(2, 5)):
                gx = rng.randint(tx + 1, max(tx + 1, bx1 - 3))
                gy = rng.randint(ty + 2, max(ty + 2, by1 - 2))
                col = palette[2] if rng.random() < 0.7 else palette[3]
                draw.point((gx, gy), fill=col)
                draw.point((gx - 1, gy - 1), fill=col)
                if gx + 1 < bx1:
                    draw.point((gx + 1, gy - 1), fill=palette[3])
            if rng.random() < flower_density and bx1 - tx >= 6 and by1 - ty >= 6:
                fx = rng.randint(tx + 2, bx1 - 3)
                fy = rng.randint(ty + 2, by1 - 3)
                petal = (236, 212, 118) if rng.random() < 0.55 else (232, 160, 172)
                draw.point((fx, fy), fill=(250, 244, 224))
                draw.point((fx - 1, fy), fill=petal)
                draw.point((fx + 1, fy), fill=petal)
                draw.point((fx, fy - 1), fill=petal)
                draw.point((fx, fy + 1), fill=petal)


def _draw_pixel_flagstones(
    draw: ImageDraw.ImageDraw,
    rect: tuple[int, int, int, int],
    shades: list[tuple[int, int, int]],
    seam: tuple[int, int, int],
    highlight: tuple[int, int, int],
    tile_w: int,
    tile_h: int,
    rng: random.Random,
    *,
    staggered: bool = True,
) -> None:
    x0, y0, x1, y1 = rect
    _px_rect(draw, x0, y0, x1, y1, seam)
    row = 0
    y = y0
    while y < y1:
        x_off = (tile_w // 2) if (staggered and row % 2 == 1) else 0
        x = x0 - x_off
        while x < x1:
            rx0 = max(x0, x)
            ry0 = max(y0, y)
            rx1 = min(x1, x + tile_w)
            ry1 = min(y1, y + tile_h)
            if rx1 - rx0 >= 3 and ry1 - ry0 >= 3:
                base_col = rng.choice(shades)
                _px_rect(draw, rx0, ry0, rx1 - 1, ry1 - 1, base_col)
                draw.line([rx0, ry0, rx1 - 2, ry0], fill=highlight)
                draw.line([rx0, ry0, rx0, ry1 - 2], fill=highlight)
                if rng.random() < 0.35 and rx1 - rx0 >= 6 and ry1 - ry0 >= 6:
                    sx = rng.randint(rx0 + 2, rx1 - 3)
                    sy = rng.randint(ry0 + 2, ry1 - 3)
                    draw.point((sx, sy), fill=seam)
                    if rng.random() < 0.5:
                        draw.point((sx + 1, sy), fill=shades[0])
            x += tile_w
        y += tile_h
        row += 1


def _draw_pixel_wood_floor(
    draw: ImageDraw.ImageDraw,
    rect: tuple[int, int, int, int],
    rng: random.Random,
) -> None:
    x0, y0, x1, y1 = rect
    seam = (84, 56, 36)
    planks = [(126, 86, 54), (136, 94, 60), (144, 102, 66), (118, 80, 50)]
    hi = (162, 118, 78)
    _px_rect(draw, x0, y0, x1, y1, seam)
    plank_h = 8
    plank_w = 32
    row = 0
    for y in range(y0, y1, plank_h):
        x_off = (plank_w // 3) * (row % 3)
        for x in range(x0 - x_off, x1, plank_w):
            rx0 = max(x0, x)
            ry0 = max(y0, y)
            rx1 = min(x1, x + plank_w)
            ry1 = min(y1, y + plank_h)
            if rx1 - rx0 >= 3 and ry1 - ry0 >= 3:
                col = rng.choice(planks)
                _px_rect(draw, rx0, ry0, rx1 - 1, ry1 - 1, col)
                draw.line([rx0, ry0, rx1 - 2, ry0], fill=hi)
                if rx1 - rx0 >= 10:
                    kx = rng.randint(rx0 + 3, rx1 - 5)
                    ky = (ry0 + ry1) // 2
                    draw.line([kx, ky, kx + 3, ky], fill=seam)
        row += 1


def _draw_pixel_bamboo_mat(draw: ImageDraw.ImageDraw, rect: tuple[int, int, int, int]) -> None:
    x0, y0, x1, y1 = rect
    _px_rect(draw, x0, y0, x1, y1, (68, 42, 34))
    _px_rect(draw, x0 + 1, y0 + 1, x1 - 1, y1 - 1, (142, 52, 46))
    _px_rect(draw, x0 + 3, y0 + 3, x1 - 3, y1 - 3, (194, 174, 118))
    for y in range(y0 + 4, y1 - 3, 2):
        draw.line([x0 + 3, y, x1 - 4, y], fill=(176, 154, 100))
    for x in range(x0 + 8, x1 - 4, 10):
        draw.line([x, y0 + 3, x, y1 - 4], fill=(158, 136, 86))


def _draw_pixel_lotus_medallion(draw: ImageDraw.ImageDraw, cx: int, cy: int) -> None:
    _px_rect(draw, cx - 12, cy - 12, cx + 12, cy + 12, (124, 116, 104))
    _px_rect(draw, cx - 11, cy - 11, cx + 11, cy + 11, (206, 198, 182))
    _px_rect(draw, cx - 9, cy - 9, cx + 9, cy + 9, (148, 140, 128))
    _px_rect(draw, cx - 7, cy - 7, cx + 7, cy + 7, (216, 208, 194))
    for dx, dy in [(-4, 0), (4, 0), (0, -4), (0, 4), (-3, -3), (3, -3), (-3, 3), (3, 3)]:
        _px_rect(draw, cx + dx - 1, cy + dy - 1, cx + dx + 2, cy + dy + 2, (172, 162, 146))
    _px_rect(draw, cx - 2, cy - 2, cx + 2, cy + 2, (214, 178, 92))


def _draw_pixel_dragon_carpet(draw: ImageDraw.ImageDraw, rect: tuple[int, int, int, int]) -> None:
    x0, y0, x1, y1 = rect
    _px_rect(draw, x0 - 1, y0, x1 + 1, y1 + 1, (38, 26, 24))
    _px_rect(draw, x0, y0, x1, y1, (216, 170, 68))
    _px_rect(draw, x0 + 2, y0 + 2, x1 - 2, y1 - 2, (152, 34, 38))
    _px_rect(draw, x0 + 4, y0 + 4, x1 - 4, y1 - 4, (204, 154, 62))
    _px_rect(draw, x0 + 5, y0 + 5, x1 - 5, y1 - 5, (140, 28, 32))
    cx = (x0 + x1) // 2
    for cy in range(y0 + 15, y1 - 10, 18):
        for r, col in [(6, (212, 164, 66)), (4, (166, 40, 42)), (2, (238, 202, 102))]:
            draw.polygon([(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)], fill=col)
    for fx in range(x0 + 2, x1 - 2, 2):
        draw.line([fx, y1, fx, y1 + 1], fill=(224, 188, 94))


def _bake_orthogonal_stage_into_base(draw: ImageDraw.ImageDraw) -> None:
    """将严格正交对齐草坪与石板路的「御苑小戏台」直接画进宫城底图 (x: 235..305, y: 276..334)。"""
    x0, y0, x1, y1 = 235, 276, 305, 334
    # 接地投影与青石围边台基
    _px_rect(draw, x0 - 2, y0 + 2, x1 + 3, y1 + 3, (46, 68, 38))
    _px_rect(draw, x0, y0, x1, y1, (98, 94, 86))
    _px_rect(draw, x0 + 1, y0 + 1, x1 - 1, y1 - 4, (176, 170, 158))
    # 台面暗石立面（南面）
    _px_rect(draw, x0 + 1, y1 - 6, x1 - 1, y1 - 1, (124, 118, 108))
    for bx in range(x0 + 6, x1 - 4, 8):
        draw.line([bx, y1 - 6, bx, y1 - 2], fill=(92, 88, 80))

    # 戏台暖木铺面与朱红低矮雕花栏杆（南向正中留 20px 宽踏步连接石板小径）
    _px_rect(draw, x0 + 4, y0 + 4, x1 - 4, y1 - 7, (148, 98, 56))
    for py in range(y0 + 7, y1 - 7, 4):
        draw.line([x0 + 4, py, x1 - 5, py], fill=(116, 74, 42))
    # 台面朱红祥云绒毯
    _px_rect(draw, x0 + 12, y0 + 10, x1 - 12, y1 - 13, (212, 168, 66))
    _px_rect(draw, x0 + 14, y0 + 12, x1 - 14, y1 - 15, (158, 36, 40))
    draw.polygon([(270, 297), (277, 304), (270, 311), (263, 304)], fill=(214, 170, 68))

    # 北/西/东与南侧左右矮栏 + 四角矮柱宫灯
    _px_rect(draw, x0 + 3, y0 + 2, x1 - 3, y0 + 5, (144, 46, 38))
    _px_rect(draw, x0 + 3, y0 + 2, x0 + 6, y1 - 6, (144, 46, 38))
    _px_rect(draw, x1 - 6, y0 + 2, x1 - 3, y1 - 6, (144, 46, 38))
    _px_rect(draw, x0 + 3, y1 - 9, 258, y1 - 6, (144, 46, 38))
    _px_rect(draw, 282, y1 - 9, x1 - 3, y1 - 6, (144, 46, 38))
    for lx, ly in [(x0 + 3, y0 + 1), (x1 - 6, y0 + 1), (x0 + 3, y1 - 10), (x1 - 6, y1 - 10)]:
        _px_rect(draw, lx, ly, lx + 3, ly + 4, (246, 198, 86))

    # 南向石阶（精准对齐下方 258..282 石板园路）
    for s in range(3):
        sy = y1 - 7 + s * 3
        shade = 198 - s * 16
        _px_rect(draw, 259, sy, 281, sy + 3, (shade, shade - 8, shade - 16))
    _px_rect(draw, 257, y1 - 7, 259, y1 + 2, (132, 126, 116))
    _px_rect(draw, 281, y1 - 7, 283, y1 + 2, (132, 126, 116))


def _bake_orthogonal_lotus_pond_into_base(draw: ImageDraw.ImageDraw, rng: random.Random) -> None:
    """将圆润石砌驳岸与叠山太湖石的「御苑莲池」融合绘制进宫城底图 (x: 456..564, y: 306..379)。"""
    x0, y0, x1, y1 = 456, 306, 564, 379
    # 草岸外圆角镶边与阴影
    _px_rect(draw, x0 + 2, y0 - 2, x1 - 2, y1 + 2, (56, 84, 44))
    _px_rect(draw, x0 - 2, y0 + 2, x1 + 2, y1 - 2, (56, 84, 44))
    _px_rect(draw, x0 + 2, y0, x1 - 2, y1, (104, 102, 94))
    _px_rect(draw, x0, y0 + 2, x1, y1 - 2, (104, 102, 94))
    _px_rect(draw, x0 + 2, y0 + 1, x1 - 2, y1 - 1, (176, 170, 156))
    _px_rect(draw, x0 + 1, y0 + 2, x1 - 1, y1 - 2, (176, 170, 156))
    # 内侧垂直石驳岸深度壁面（北侧石壁显露高差）
    _px_rect(draw, x0 + 4, y0 + 4, x1 - 4, y1 - 4, (112, 112, 108))
    _px_rect(draw, x0 + 5, y0 + 8, x1 - 5, y1 - 4, (44, 96, 110))

    # 分层碧绿池水（深水中心 -> 浅水岸边）
    _px_rect(draw, x0 + 8, y0 + 11, x1 - 8, y1 - 7, (56, 122, 134))
    _px_rect(draw, x0 + 14, y0 + 16, x1 - 14, y1 - 12, (68, 142, 152))
    # 岸边浅水高光与水平波纹
    draw.line([x0 + 6, y0 + 9, x1 - 7, y0 + 9], fill=(82, 156, 166))
    for _ in range(18):
        wx = rng.randint(x0 + 10, x1 - 20)
        wy = rng.randint(y0 + 12, y1 - 9)
        ww = rng.randint(4, 10)
        draw.line([wx, wy, wx + ww, wy], fill=(116, 186, 192))

    # 西侧亲水石阶观景台（对接 courtyard_pond (860, 690) -> native 430, 345）
    _px_rect(draw, x0 - 4, 334, x0 + 8, 354, (118, 114, 106))
    _px_rect(draw, x0 - 3, 335, x0 + 6, 353, (184, 178, 166))
    _px_rect(draw, x0 - 2, 336, x0 + 5, 352, (158, 152, 140))

    # 池角雕琢太湖石叠山（多圆弧石块）
    for rx, ry, rw, rh in [(462, 303, 14, 9), (542, 304, 16, 9), (468, 371, 14, 8), (538, 370, 16, 9)]:
        draw.ellipse([rx, ry, rx + rw, ry + rh], fill=(138, 134, 124))
        draw.ellipse([rx + 1, ry + 1, rx + rw - 2, ry + rh - 3], fill=(192, 188, 176))
        _px_rect(draw, rx + 4, ry + 4, rx + 7, ry + 6, (98, 94, 88))

    # 荷叶与粉白睡莲、红鲤鱼
    for lx, ly, has_lotus in [
        (476, 326, True),
        (488, 334, False),
        (518, 322, True),
        (536, 338, False),
        (502, 354, True),
        (532, 358, True),
        (480, 358, False),
    ]:
        draw.ellipse([lx - 5, ly - 3, lx + 5, ly + 3], fill=(56, 118, 54))
        draw.ellipse([lx - 4, ly - 2, lx + 3, ly + 2], fill=(94, 168, 82))
        if has_lotus:
            _px_rect(draw, lx - 2, ly - 3, lx + 2, ly, (244, 162, 182))
            draw.point((lx, ly - 2), fill=(252, 232, 148))
    for kx, ky in [(496, 342), (524, 348), (512, 330)]:
        _px_rect(draw, kx, ky, kx + 4, ky + 2, (226, 92, 54))
        draw.point((kx + 4, ky), fill=(244, 138, 86))


def _bake_construction_plots_into_base(draw: ImageDraw.ImageDraw) -> None:
    """将西偏院预留地块 A/B 直接融入青石板地基（含界石、夯土、砖垛木料与勘测木牌）。"""
    for cx, cy in [(87, 192), (182, 192)]:
        x0, y0, x1, y1 = cx - 26, cy - 21, cx + 26, cy + 21
        _px_rect(draw, x0, y0, x1, y1, (108, 108, 108))
        _px_rect(draw, x0 + 1, y0 + 1, x1 - 1, y1 - 1, (164, 162, 154))
        _px_rect(draw, x0 + 4, y0 + 4, x1 - 4, y1 - 4, (176, 144, 102))
        _px_rect(draw, x0 + 6, y0 + 6, x1 - 6, y1 - 6, (192, 158, 114))
        # 砖垛立体阴影 + 交错灰砖面
        _px_rect(draw, x0 + 7, y0 + 11, x0 + 19, y0 + 23, (128, 98, 66))
        _px_rect(draw, x0 + 6, y0 + 10, x0 + 18, y0 + 22, (124, 128, 134))
        _px_rect(draw, x0 + 6, y0 + 9, x0 + 18, y0 + 13, (152, 156, 162))
        for by in (13, 16, 19):
            draw.line([x0 + 7, y0 + by, x0 + 16, y0 + by], fill=(84, 88, 94))
        # 原木垛阴影 + 端面木纹圆环
        _px_rect(draw, x1 - 21, y0 + 9, x1 - 5, y0 + 20, (128, 98, 66))
        _px_rect(draw, x1 - 22, y0 + 8, x1 - 6, y0 + 19, (132, 86, 48))
        for ly in (9, 12, 15):
            draw.line([x1 - 21, y0 + ly, x1 - 7, y0 + ly], fill=(162, 110, 64))
            _px_rect(draw, x1 - 8, y0 + ly, x1 - 6, y0 + ly + 2, (214, 178, 124))
        # 四角木桩与麻绳围栏
        draw.line([x0 + 2, y0 + 2, x1 - 3, y0 + 2], fill=(168, 138, 86))
        draw.line([x0 + 2, y1 - 3, x1 - 3, y1 - 3], fill=(168, 138, 86))
        draw.line([x0 + 2, y0 + 2, x0 + 2, y1 - 3], fill=(168, 138, 86))
        draw.line([x1 - 3, y0 + 2, x1 - 3, y1 - 3], fill=(168, 138, 86))
        for px, py in [(x0 + 1, y0 + 1), (x1 - 4, y0 + 1), (x0 + 1, y1 - 4), (x1 - 4, y1 - 4)]:
            _px_rect(draw, px, py, px + 3, py + 4, (112, 68, 38))
        _px_rect(draw, cx - 5, y1 - 9, cx + 5, y1 - 3, (148, 48, 38))
        _px_rect(draw, cx - 4, y1 - 8, cx + 4, y1 - 4, (226, 206, 154))


def _bake_tree_planters_and_grounding(draw: ImageDraw.ImageDraw) -> None:
    """在底图上为草地树木绘制泥土树坑、为石板角树木绘制正交方石树池，使树干自然扎根。"""
    # 草坪上的 5 棵树（世界坐标，对应 palace.gd）-> 自然泥土树盘 + 落叶
    grass_tree_feet = [(1176, 680), (1136, 566), (406, 576), (410, 846), (1186, 846)]
    for gx, gy in grass_tree_feet:
        tx = gx // 2
        ty = gy // 2
        draw.ellipse([tx - 13, ty - 7, tx + 13, ty + 4], fill=(56, 86, 42))
        draw.ellipse([tx - 10, ty - 5, tx + 10, ty + 2], fill=(96, 74, 48))
        draw.ellipse([tx - 7, ty - 4, tx + 7, ty + 1], fill=(76, 56, 36))

    # 南宫广场东西角的 2 棵银杏（世界坐标）-> 正交方形汉白玉石树池
    stone_tree_feet = [(146, 966), (1456, 966)]
    for sx, sy in stone_tree_feet:
        tx = sx // 2
        ty = sy // 2
        _px_rect(draw, tx - 14, ty - 9, tx + 14, ty + 5, (104, 98, 90))
        _px_rect(draw, tx - 13, ty - 8, tx + 13, ty + 4, (186, 180, 166))
        _px_rect(draw, tx - 10, ty - 5, tx + 10, ty + 1, (92, 68, 44))
        _px_rect(draw, tx - 8, ty - 3, tx + 8, ty, (218, 164, 52))


def _draw_pixel_roof_strip(
    draw: ImageDraw.ImageDraw,
    x0: int,
    y0: int,
    x1: int,
    y1: int,
    *,
    with_chiwen: bool = False,
    with_plaque: bool = False,
) -> None:
    _px_rect(draw, x0, y0, x1, y1, (32, 24, 28))
    ridge_y = y0 + 2
    _px_rect(draw, x0 + 1, y0 + 1, x1 - 1, ridge_y + 2, (118, 126, 138))
    draw.line([x0 + 1, y0 + 1, x1 - 2, y0 + 1], fill=(154, 162, 174))
    slope_y0 = ridge_y + 2
    slope_y1 = y1 - 2
    _px_rect(draw, x0 + 1, slope_y0, x1 - 1, slope_y1, (64, 72, 82))
    for rx in range(x0 + 3, x1 - 2, 4):
        draw.line([rx, slope_y0, rx, slope_y1 - 1], fill=(92, 100, 112))
        draw.line([rx + 1, slope_y0, rx + 1, slope_y1 - 1], fill=(48, 54, 62))
    for rx in range(x0 + 2, x1 - 2, 4):
        _px_rect(draw, rx, slope_y1, rx + 2, y1 - 1, (104, 112, 124))
    draw.line([x0 + 1, y1 - 1, x1 - 2, y1 - 1], fill=(32, 24, 28))

    if with_chiwen and x1 - x0 >= 32:
        for cx in (x0 + 3, x1 - 6):
            _px_rect(draw, cx, y0 - 2, cx + 3, y0 + 2, (226, 178, 68))
            draw.point((cx + 1, y0 - 3), fill=(246, 212, 112))

    if with_plaque and x1 - x0 >= 36:
        mid = (x0 + x1) // 2
        _px_rect(draw, mid - 12, y1 - 5, mid + 12, y1 + 1, (44, 30, 24))
        _px_rect(draw, mid - 11, y1 - 4, mid + 11, y1, (216, 172, 68))
        _px_rect(draw, mid - 9, y1 - 3, mid + 9, y1 - 1, (26, 20, 22))


def _draw_north_facade(draw: ImageDraw.ImageDraw) -> None:
    _px_rect(draw, 20, 20, 780, 47, (32, 24, 28))
    _px_rect(draw, 34, 28, 766, 44, (214, 204, 188))
    _px_rect(draw, 34, 44, 766, 47, (132, 128, 120))
    draw.line([34, 44, 765, 44], fill=(168, 162, 152))

    for bx in range(44, 250, 32):
        _px_rect(draw, bx, 31, bx + 20, 41, (186, 178, 166))
        _px_rect(draw, bx + 2, 33, bx + 18, 39, (112, 82, 54))
        _px_rect(draw, bx + 4, 34, bx + 10, 38, (226, 214, 184))

    _px_rect(draw, 271, 28, 529, 44, (224, 214, 198))
    _px_rect(draw, 271, 39, 529, 44, (138, 40, 36))
    _px_rect(draw, 350, 29, 450, 42, (124, 92, 48))
    _px_rect(draw, 352, 31, 448, 40, (228, 218, 194))
    draw.polygon([(354, 40), (370, 33), (386, 40)], fill=(122, 140, 128))
    draw.polygon([(380, 40), (400, 31), (420, 40)], fill=(98, 118, 108))
    draw.polygon([(412, 40), (430, 34), (446, 40)], fill=(126, 144, 132))
    _px_rect(draw, 398, 32, 401, 34, (218, 92, 62))

    _px_rect(draw, 540, 39, 766, 44, (104, 68, 42))
    for wx in range(554, 750, 34):
        _px_rect(draw, wx, 30, wx + 22, 39, (122, 40, 34))
        _px_rect(draw, wx + 2, 31, wx + 20, 38, (228, 216, 180))
        for mx in range(wx + 5, wx + 19, 4):
            draw.line([mx, 31, mx, 37], fill=(138, 62, 44))

    _px_rect(draw, 30, 24, 770, 29, (152, 42, 34))
    for bx in range(36, 764, 16):
        _px_rect(draw, bx, 25, bx + 6, 28, (212, 166, 68))
        _px_rect(draw, bx + 2, 26, bx + 4, 28, (132, 36, 30))

    pillar_xs = list(range(36, 260, 32)) + list(range(274, 528, 32)) + list(range(544, 766, 32))
    for px in pillar_xs:
        _px_rect(draw, px, 26, px + 4, 45, (162, 46, 38))
        draw.line([px + 1, 26, px + 1, 44], fill=(198, 66, 54))
        _px_rect(draw, px - 1, 44, px + 5, 46, (176, 170, 158))

    _draw_pixel_roof_strip(draw, 20, 16, 262, 26, with_chiwen=False)
    _draw_pixel_roof_strip(draw, 262, 13, 538, 26, with_chiwen=True, with_plaque=True)
    _draw_pixel_roof_strip(draw, 538, 16, 780, 26, with_chiwen=False)


def _draw_horizontal_wall_base(
    draw: ImageDraw.ImageDraw,
    x0: int,
    y0: int,
    x1: int,
    y1: int,
    *,
    cap_left: bool = True,
    cap_right: bool = True,
) -> None:
    _px_rect(draw, x0, y0, x1, y1, (32, 24, 28))
    _px_rect(draw, x0 + 1, y0 + 1, x1 - 1, y1 - 3, (210, 202, 186))
    _px_rect(draw, x0 + 1, y1 - 3, x1 - 1, y1 - 1, (142, 136, 126))
    for px in range(x0 + 20, x1 - 16, 48):
        _px_rect(draw, px, y0 + 1, px + 3, y1 - 2, (152, 44, 38))
    if cap_left:
        _px_rect(draw, x0, y0, x0 + 4, y1, (158, 46, 38))
    if cap_right:
        _px_rect(draw, x1 - 4, y0, x1, y1, (158, 46, 38))


def _draw_vertical_wall_base(draw: ImageDraw.ImageDraw, x0: int, y0: int, x1: int, y1: int) -> None:
    _px_rect(draw, x0, y0, x1, y1, (32, 24, 28))
    _px_rect(draw, x0 + 1, y0 + 1, x1 - 1, y1 - 1, (186, 178, 164))
    _px_rect(draw, x0 + 2, y0 + 1, x1 - 2, y1 - 1, (76, 82, 92))
    mid_x = (x0 + x1) // 2
    draw.line([mid_x, y0 + 1, mid_x, y1 - 2], fill=(122, 128, 138))
    _px_rect(draw, x0, y0, x1, y0 + 3, (156, 46, 38))
    _px_rect(draw, x0, y1 - 3, x1, y1, (156, 46, 38))


def _draw_door_threshold(draw: ImageDraw.ImageDraw, x0: int, y0: int, x1: int, y1: int) -> None:
    _px_rect(draw, x0, y0, x1, y1, (188, 180, 164))
    mid_y = (y0 + y1) // 2
    _px_rect(draw, x0 + 4, mid_y - 1, x1 - 4, mid_y + 2, (124, 52, 38))
    _px_rect(draw, x0, mid_y - 2, x0 + 5, mid_y + 3, (148, 142, 132))
    _px_rect(draw, x1 - 5, mid_y - 2, x1, mid_y + 3, (148, 142, 132))
    for s in range(3):
        sy = y1 + s * 2
        shade = 196 - s * 14
        _px_rect(draw, x0 + 2, sy, x1 - 2, sy + 2, (shade, shade - 8, shade - 18))
        draw.line([x0 + 2, sy + 1, x1 - 3, sy + 1], fill=(108, 102, 94))


def build_pixel_palace_maps(*, overwrite: bool) -> None:
    base_out = PALACE_OUT_DIR / "palace_base.png"
    front_out = PALACE_OUT_DIR / "palace_front.png"
    if (
        not overwrite
        and base_out.is_file()
        and base_out.stat().st_size > 0
        and front_out.is_file()
        and front_out.stat().st_size > 0
    ):
        print(f"[SKIP-MAPS] {base_out} & {front_out}")
        return

    rng = random.Random(20261116)
    base_native = Image.new("RGBA", (NATIVE_W, NATIVE_H), (44, 72, 40, 255))
    bdraw = ImageDraw.Draw(base_native)

    # 1. 宫外草地与石板护城外道
    _draw_pixel_grass(
        bdraw,
        (0, 0, NATIVE_W, NATIVE_H),
        [(44, 72, 40), (54, 88, 48), (66, 104, 56), (80, 120, 66)],
        rng,
        flower_density=0.22,
    )
    _px_rect(bdraw, 14, 14, 786, 531, (106, 102, 94))
    _draw_pixel_flagstones(
        bdraw,
        (340, 515, 460, NATIVE_H),
        [(154, 146, 132), (164, 156, 142), (144, 136, 124)],
        (98, 92, 84),
        (182, 174, 158),
        16,
        10,
        rng,
    )

    # 2. 宫城大院青白条石地砖（x: 34..766, y: 34..512）
    _draw_pixel_flagstones(
        bdraw,
        (34, 34, 766, 512),
        [(164, 156, 142), (174, 166, 152), (156, 148, 134)],
        (106, 100, 90),
        (190, 182, 168),
        16,
        12,
        rng,
    )

    # 3. 中心御苑草坪与青石园路
    _px_rect(bdraw, 169, 249, 631, 451, (102, 96, 86))
    _px_rect(bdraw, 170, 250, 630, 450, (170, 162, 146))
    _draw_pixel_grass(
        bdraw,
        (173, 253, 627, 447),
        [(68, 110, 54), (78, 124, 62), (90, 138, 72), (104, 154, 82)],
        rng,
        flower_density=0.26,
    )
    # 园内青石漫步小径（连接戏台、石桌、莲池）
    _draw_pixel_flagstones(
        bdraw,
        (173, 338, 627, 358),
        [(154, 146, 132), (166, 158, 144)],
        (98, 92, 84),
        (184, 176, 160),
        12,
        10,
        rng,
    )
    _draw_pixel_flagstones(
        bdraw,
        (258, 253, 282, 447),
        [(154, 146, 132), (166, 158, 144)],
        (98, 92, 84),
        (184, 176, 160),
        12,
        10,
        rng,
    )
    # 石桌正交青石方台（无缝衔接御道与园路）
    _px_rect(bdraw, 331, 336, 374, 381, (108, 102, 92))
    _draw_pixel_flagstones(
        bdraw,
        (332, 337, 373, 380),
        [(172, 164, 150), (182, 174, 160)],
        (114, 108, 98),
        (198, 190, 176),
        10,
        10,
        rng,
        staggered=False,
    )

    # 4. 中轴御道与莲花地雕
    _draw_pixel_flagstones(
        bdraw,
        (372, 206, 428, 512),
        [(184, 176, 160), (194, 186, 170), (176, 168, 152)],
        (118, 110, 98),
        (212, 204, 188),
        14,
        12,
        rng,
    )
    _px_rect(bdraw, 371, 206, 373, 512, (120, 112, 100))
    _px_rect(bdraw, 427, 206, 429, 512, (120, 112, 100))
    _draw_pixel_lotus_medallion(bdraw, 400, 228)
    _draw_pixel_lotus_medallion(bdraw, 400, 348)

    # 融合绘制：御苑小戏台 + 御苑莲池
    _bake_orthogonal_stage_into_base(bdraw)
    _bake_orthogonal_lotus_pond_into_base(bdraw, rng)

    # 5. 议事正殿金砖、汉白玉丹陛高台与盘龙御毯
    _draw_pixel_flagstones(
        bdraw,
        (271, 34, 529, 195),
        [(74, 60, 54), (82, 66, 58), (68, 54, 48)],
        (46, 36, 32),
        (98, 80, 72),
        16,
        16,
        rng,
        staggered=False,
    )
    _px_rect(bdraw, 340, 46, 460, 84, (132, 124, 112))
    _px_rect(bdraw, 342, 46, 458, 80, (206, 198, 182))
    _px_rect(bdraw, 344, 48, 456, 78, (220, 212, 196))
    for step_i in range(3):
        sy = 79 + step_i * 2
        shade = 212 - step_i * 14
        _px_rect(bdraw, 356, sy, 444, sy + 2, (shade, shade - 8, shade - 16))
    _draw_pixel_dragon_carpet(bdraw, (376, 55, 424, 205))

    # 6. 东偏殿木地板与竹席地衣
    _draw_pixel_wood_floor(bdraw, (540, 34, 766, 220), rng)
    for mat_rect in [
        (565, 74, 645, 134),
        (665, 74, 745, 134),
        (548, 152, 610, 204),
        (686, 152, 756, 204),
    ]:
        _draw_pixel_bamboo_mat(bdraw, mat_rect)

    # 7. 西偏院粗砺青石地、工坊红砖坪、画坊木地台与融合绘制的预留地块 A/B
    _draw_pixel_flagstones(
        bdraw,
        (34, 34, 260, 240),
        [(120, 124, 128), (130, 134, 138), (112, 116, 120)],
        (78, 82, 86),
        (146, 150, 154),
        16,
        14,
        rng,
    )
    _draw_pixel_flagstones(
        bdraw,
        (56, 74, 136, 132),
        [(108, 72, 62), (118, 78, 66)],
        (64, 44, 38),
        (132, 92, 80),
        8,
        8,
        rng,
    )
    _draw_pixel_wood_floor(bdraw, (164, 76, 228, 132), rng)
    _bake_construction_plots_into_base(bdraw)

    # 茶亭底层青石院坪与树池接地
    _px_rect(bdraw, 58, 378, 138, 417, (124, 118, 108))
    _draw_pixel_flagstones(
        bdraw,
        (59, 379, 137, 416),
        [(172, 166, 152), (182, 174, 160)],
        (114, 108, 98),
        (198, 190, 176),
        13,
        9,
        rng,
        staggered=False,
    )
    _bake_tree_planters_and_grounding(bdraw)

    # 8. 墙体南向像素投影与立体北墙立面、隔墙底座、门洞踏步
    shadow_overlay = Image.new("RGBA", (NATIVE_W, NATIVE_H), (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(shadow_overlay)
    for sx0, sy0, sx1, sy1 in [
        (20, 47, 780, 51),
        (260, 206, 360, 211),
        (440, 206, 540, 211),
        (540, 230, 615, 235),
        (670, 230, 766, 235),
        (34, 250, 119, 255),
        (175, 250, 260, 255),
        (34, 526, 350, 531),
        (450, 526, 766, 531),
    ]:
        _px_rect(sdraw, sx0, sy0, sx1, sy1, (24, 18, 26, 84))
    base_native.alpha_composite(shadow_overlay)
    bdraw = ImageDraw.Draw(base_native)

    _draw_north_facade(bdraw)

    _draw_vertical_wall_base(bdraw, 20, 26, 34, 526)
    _draw_vertical_wall_base(bdraw, 766, 26, 780, 526)
    _draw_vertical_wall_base(bdraw, 260, 34, 271, 104)
    _draw_vertical_wall_base(bdraw, 260, 150, 271, 195)
    _draw_vertical_wall_base(bdraw, 529, 34, 540, 104)
    _draw_vertical_wall_base(bdraw, 529, 150, 540, 195)

    _draw_door_threshold(bdraw, 360, 195, 440, 206)
    _draw_door_threshold(bdraw, 615, 220, 670, 230)
    _draw_door_threshold(bdraw, 119, 240, 175, 250)
    _draw_door_threshold(bdraw, 350, 512, 450, 526)

    _draw_horizontal_wall_base(bdraw, 260, 195, 360, 206, cap_left=True, cap_right=True)
    _draw_horizontal_wall_base(bdraw, 440, 195, 540, 206, cap_left=True, cap_right=True)
    _draw_horizontal_wall_base(bdraw, 540, 220, 615, 230, cap_left=False, cap_right=True)
    _draw_horizontal_wall_base(bdraw, 670, 220, 766, 230, cap_left=True, cap_right=False)
    _draw_horizontal_wall_base(bdraw, 34, 240, 119, 250, cap_left=False, cap_right=True)
    _draw_horizontal_wall_base(bdraw, 175, 240, 260, 250, cap_left=True, cap_right=False)
    _draw_horizontal_wall_base(bdraw, 34, 512, 350, 526, cap_left=False, cap_right=True)
    _draw_horizontal_wall_base(bdraw, 450, 512, 766, 526, cap_left=True, cap_right=False)

    # 9. 前景屋檐遮挡层（z_index = 4）
    front_native = Image.new("RGBA", (NATIVE_W, NATIVE_H), (0, 0, 0, 0))
    fdraw = ImageDraw.Draw(front_native)

    _draw_pixel_roof_strip(fdraw, 258, 185, 362, 198)
    _draw_pixel_roof_strip(fdraw, 438, 185, 542, 198)
    _draw_pixel_roof_strip(fdraw, 356, 180, 444, 195, with_chiwen=True, with_plaque=True)
    _draw_pixel_roof_strip(fdraw, 258, 98, 273, 154)
    _draw_pixel_roof_strip(fdraw, 527, 98, 542, 154)

    _draw_pixel_roof_strip(fdraw, 538, 210, 617, 223)
    _draw_pixel_roof_strip(fdraw, 668, 210, 768, 223)
    _draw_pixel_roof_strip(fdraw, 612, 206, 673, 220, with_plaque=True)

    _draw_pixel_roof_strip(fdraw, 32, 230, 121, 243)
    _draw_pixel_roof_strip(fdraw, 173, 230, 262, 243)
    _draw_pixel_roof_strip(fdraw, 116, 226, 178, 240, with_plaque=True)

    _draw_pixel_roof_strip(fdraw, 20, 502, 352, 516)
    _draw_pixel_roof_strip(fdraw, 448, 502, 780, 516)
    _draw_pixel_roof_strip(fdraw, 342, 491, 458, 512, with_chiwen=True, with_plaque=True)
    for kx, ky in [(18, 500), (762, 500)]:
        _draw_pixel_roof_strip(fdraw, kx, ky - 4, kx + 20, ky + 12, with_chiwen=False)

    PALACE_OUT_DIR.mkdir(parents=True, exist_ok=True)
    _save_pixel_2x(base_native, base_out)
    _save_pixel_2x(front_native, front_out)
    print(f"[OK-BASE] {base_out} ({WORLD_W}x{WORLD_H}, orthogonal pixel)")
    print(f"[OK-FRONT] {front_out} ({WORLD_W}x{WORLD_H}, orthogonal pixel)")


def main() -> None:
    parser = argparse.ArgumentParser(description="生成正交 32x32 唐风全像素皇城地图、家具与人物资产")
    parser.add_argument("--chars-only", action="store_true", help="仅生成 13 位角色像素小人")
    parser.add_argument("--props-only", action="store_true", help="仅生成正交像素家具与景观")
    parser.add_argument("--maps-only", action="store_true", help="仅生成像素宫城底图与前景遮挡层")
    parser.add_argument("--overwrite", action="store_true", help="覆盖已存在文件")
    args = parser.parse_args()

    run_all = not (args.chars_only or args.props_only or args.maps_only)
    if run_all or args.chars_only:
        build_pixel_characters(overwrite=args.overwrite)
    if run_all or args.props_only:
        build_pixel_props(overwrite=args.overwrite)
    if run_all or args.maps_only:
        build_pixel_palace_maps(overwrite=args.overwrite)


if __name__ == "__main__":
    main()
