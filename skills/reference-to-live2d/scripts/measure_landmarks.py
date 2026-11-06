#!/usr/bin/env python3
"""Calculate reference proportions from reviewed pixel landmarks; requires Pillow."""

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image


VERTICAL = {
    "head_height": ("crown", "chin"),
    "face_height_hairline_to_chin": ("hairline", "chin"),
    "left_eye_opening_height": ("eye_upper_left", "eye_lower_left"),
    "right_eye_opening_height": ("eye_upper_right", "eye_lower_right"),
    "eye_to_nose": ("pupil_left", "nose"),
    "nose_to_mouth": ("nose", "mouth_center"),
    "mouth_to_chin": ("mouth_center", "chin"),
    "brow_to_eye": ("brow_left", "pupil_left"),
}
HORIZONTAL = {
    "visible_face_width_at_cheeks": ("cheek_left", "cheek_right"),
    "hair_silhouette_width": ("hair_left", "hair_right"),
    "pupil_spacing": ("pupil_left", "pupil_right"),
    "left_eye_width": ("eye_outer_left", "eye_inner_left"),
    "right_eye_width": ("eye_inner_right", "eye_outer_right"),
    "mouth_width": ("mouth_left", "mouth_right"),
    "neck_width": ("neck_left", "neck_right"),
    "shoulder_width_estimate": ("shoulder_left_estimate", "shoulder_right_estimate"),
    "arm_span": ("fingertip_left", "fingertip_right"),
    "profile_depth_hair_to_nose": ("back_skull_hair", "nose"),
    "shoe_length": ("heel", "toe"),
}


def measure_view(view, root):
    source = root / view["source"]
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    if view.get("sha256") and view["sha256"] != digest:
        raise ValueError(f"Source changed; review landmarks before measuring: {source}")
    with Image.open(source) as image:
        size = list(image.size)
    points = view["landmarks_px"]
    height = points["sole"][1] - points["crown"][1]
    if height <= 0:
        raise ValueError(f"Crown must be above the sole: {source}")
    metrics = {"illustrated_shod_height": height}
    for axis, pairs in ((1, VERTICAL), (0, HORIZONTAL)):
        for name, (a, b) in pairs.items():
            if points.get(a) is not None and points.get(b) is not None:
                metrics[name] = points[b][axis] - points[a][axis]
    ratios = {
        f"{key}_over_stature": round(value / height, 6)
        for key, value in metrics.items()
        if key != "illustrated_shod_height"
    }
    head = metrics.get("head_height")
    if head:
        ratios["head_count"] = round(height / head, 4)
    face = metrics.get("visible_face_width_at_cheeks")
    if face:
        for key in ("pupil_spacing", "left_eye_width", "right_eye_width", "mouth_width"):
            if key in metrics:
                ratios[f"{key}_over_face_width"] = round(metrics[key] / face, 6)
        if head:
            ratios["face_width_over_head_height"] = round(face / head, 6)
        face_height = metrics.get("face_height_hairline_to_chin")
        if face_height:
            ratios["face_height_over_face_width"] = round(face_height / face, 6)
            for label, point in (("eye", "pupil_left"), ("nose", "nose"), ("mouth", "mouth_center")):
                if points.get(point) is not None:
                    ratios[f"{label}_level_from_hairline_over_face_height"] = round(
                        (points[point][1] - points["hairline"][1]) / face_height, 6
                    )
    if metrics.get("left_eye_width") and "left_eye_opening_height" in metrics:
        ratios["eye_opening_height_over_eye_width"] = round(
            metrics["left_eye_opening_height"] / metrics["left_eye_width"], 6
        )
    return {
        "source": view["source"],
        "sha256": digest,
        "image_size": size,
        "landmarks_px": points,
        "metrics_px": metrics,
        "ratios": ratios,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="JSON containing views with source and landmarks_px")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Base for source image paths")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source = json.loads(args.input.read_text(encoding="utf-8"))
    result = {
        "method": "Arithmetic on supplied reviewed pixel landmarks; no automatic landmark detection.",
        "coordinate_convention": source.get(
            "coordinate_convention",
            "Original pixels; x right, y down. Crown excludes ahoge/glasses; stature includes shoes.",
        ),
        "views": {name: measure_view(view, args.root) for name, view in source["views"].items()},
    }
    for key in ("estimated_uncertainty_px", "occlusion"):
        if key in source:
            result[key] = source[key]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Measured {len(result['views'])} views -> {args.output}")


if __name__ == "__main__":
    main()
