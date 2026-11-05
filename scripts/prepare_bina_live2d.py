"""Package Bina's generated parts atlas as a PSD2Live Layout manifest."""

import json
from pathlib import Path

from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets/bina-live2d/source"

# Atlas cell, model rectangle, semantic tags; layers run from back to front.
PARTS = [
    ("back_hair", 0, (275, 85, 450, 475), ["hair", "back"]),
    ("body", 3, (180, 475, 640, 820), ["top"]),
    ("face", 1, (340, 150, 320, 370), ["face"]),
    ("eyewhite_right", 4, (376, 308, 100, 44), ["eye", "white", "right"]),
    ("eyewhite_left", 5, (524, 308, 100, 44), ["eye", "white", "left"]),
    ("iris_right", 6, (405, 303, 47, 55), ["eye", "iris", "right"]),
    ("iris_left", 7, (548, 303, 47, 55), ["eye", "iris", "left"]),
    ("eyelash_right", 8, (370, 300, 110, 52), ["eye", "lash", "right"]),
    ("eyelash_left", 9, (520, 300, 110, 52), ["eye", "lash", "left"]),
    ("brow_right", 10, (378, 275, 95, 16), ["brow", "right"]),
    ("brow_left", 11, (527, 275, 95, 16), ["brow", "left"]),
    ("nose", 13, (489, 377, 22, 30), ["nose"]),
    ("mouth", 12, (466, 427, 68, 46), ["mouth", "open"]),
    ("front_hair", 2, (275, 85, 450, 475), ["hair", "front"]),
    ("glasses", 14, (357, 102, 286, 110), ["headwear"]),
]


def main():
    atlas = Image.open(SOURCE / "parts-atlas.png").convert("RGBA")
    parts_dir = SOURCE / "parts"
    parts_dir.mkdir(exist_ok=True)
    preview = Image.new("RGBA", (1000, 1400))
    layers = []
    eye_masks = {}
    for name, cell, rect, tags in PARTS:
        col, row = cell % 4, cell // 4
        bounds = (round(col * atlas.width / 4), round(row * atlas.height / 4),
                  round((col + 1) * atlas.width / 4), round((row + 1) * atlas.height / 4))
        if row == 0:
            bounds = (bounds[0], 0, bounds[2], round(atlas.height * 0.28))
        elif row == 1:
            bounds = (bounds[0], round(atlas.height * 0.31), bounds[2], bounds[3])
        part = atlas.crop(bounds)
        # Discard near-transparent atlas padding before calculating part bounds.
        part.putalpha(part.getchannel("A").point(lambda value: 0 if value < 16 else value))
        part = part.crop(part.getchannel("A").point(lambda value: 255 if value > 64 else 0).getbbox())
        part.save(parts_dir / f"{name}.png")
        left, top, width, height = rect
        layers.append({
            "id": name, "name": name, "tags": tags,
            "image": {"path": f"parts/{name}.png", "width": part.width, "height": part.height},
            "rect": dict(zip(("left", "top", "width", "height"), rect)),
        })
        placed = Image.new("RGBA", preview.size)
        placed.alpha_composite(part.resize((width, height), Image.Resampling.LANCZOS), (left, top))
        if name.startswith("eyewhite_"):
            eye_masks[name.removeprefix("eyewhite_")] = placed.getchannel("A")
        if name.startswith("iris_"):
            placed.putalpha(ImageChops.multiply(placed.getchannel("A"), eye_masks[name.removeprefix("iris_")]))
        preview.alpha_composite(placed)
    manifest = {"format": "psd2live-layout", "version": 1, "name": "bina",
                "canvas": {"width": 1000, "height": 1400}, "layers": layers}
    (SOURCE / "bina.layout.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    preview.save(SOURCE / "assembled-preview.png")
    print(f"Prepared {len(layers)} layers: {SOURCE / 'bina.layout.json'}")


if __name__ == "__main__":
    main()
