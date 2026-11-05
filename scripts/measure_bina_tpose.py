"""Measure the six original T-pose drawings from explicitly marked pixel landmarks."""

import base64
import csv
import hashlib
import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets/bina-tpose"
OUT = SOURCE / "measurements"

# Coordinates are manually observed on original pixels, not a fitted anatomy model.
# Left/right below refer to image coordinates, not the character's anatomy.
LANDMARKS = {
    "casual-front": {
        "crown": [764, 28], "chin": [765, 172], "sole": [765, 1009],
        "hairline": [764, 70], "hair_left": [677, 117], "hair_right": [850, 117],
        "cheek_left": [726, 128], "cheek_right": [805, 128],
        "pupil_left": [742, 117], "pupil_right": [789, 117],
        "eye_outer_left": [725, 113], "eye_inner_left": [753, 118],
        "eye_inner_right": [777, 118], "eye_outer_right": [805, 113],
        "eye_upper_left": [741, 111], "eye_lower_left": [741, 123],
        "eye_upper_right": [790, 111], "eye_lower_right": [790, 123],
        "brow_left": [741, 100], "brow_right": [790, 100],
        "nose": [765, 138], "mouth_left": [754, 150], "mouth_right": [776, 150],
        "mouth_center": [765, 151], "neck_left": [746, 181], "neck_right": [785, 181],
        "shoulder_left_estimate": [687, 219], "shoulder_right_estimate": [845, 219],
        "fingertip_left": [304, 225], "fingertip_right": [1225, 225],
        "wrist_left": [411, 230], "wrist_right": [1119, 230],
        "sweater_hem": [765, 506], "skirt_hem": [765, 538],
        "knee_left": [715, 671], "knee_right": [807, 671],
        "waist": None, "crotch": None,
    },
    "work-front": {
        "crown": [763, 29], "chin": [765, 173], "sole": [765, 1010],
        "hairline": None, "hair_left": [677, 116], "hair_right": [848, 116],
        "cheek_left": [727, 129], "cheek_right": [805, 129],
        "pupil_left": [742, 118], "pupil_right": [789, 118],
        "eye_outer_left": [725, 114], "eye_inner_left": [753, 119],
        "eye_inner_right": [777, 119], "eye_outer_right": [805, 114],
        "eye_upper_left": [741, 112], "eye_lower_left": [741, 124],
        "eye_upper_right": [790, 112], "eye_lower_right": [790, 124],
        "brow_left": [741, 101], "brow_right": [790, 101],
        "nose": [765, 139], "mouth_left": [754, 151], "mouth_right": [776, 151],
        "mouth_center": [765, 152], "neck_left": None, "neck_right": None,
        "shoulder_left_estimate": [686, 219], "shoulder_right_estimate": [845, 219],
        "fingertip_left": [305, 225], "fingertip_right": [1225, 225],
        "wrist_left": [418, 229], "wrist_right": [1111, 229],
        "belt_center": [765, 384], "belt_left": [695, 384], "belt_right": [837, 384],
        "crotch_seam": [764, 494], "knees": None,
    },
    "casual-back": {
        "crown": [764, 28], "chin": None, "sole": [765, 1009],
        "hair_left": [681, 115], "hair_right": [849, 115], "hair_bottom": [763, 188],
        "shoulder_left_estimate": [686, 219], "shoulder_right_estimate": [846, 219],
        "fingertip_left": [303, 227], "fingertip_right": [1231, 227],
        "wrist_left": [411, 230], "wrist_right": [1122, 230],
        "sweater_hem": [765, 505], "skirt_hem": [765, 541],
    },
    "work-back": {
        "crown": [764, 29], "chin": None, "sole": [765, 1009],
        "hair_left": [686, 114], "hair_right": [848, 114], "hair_bottom": [766, 177],
        "shoulder_left_estimate": [685, 219], "shoulder_right_estimate": [846, 219],
        "fingertip_left": [303, 225], "fingertip_right": [1230, 225],
        "wrist_left": [410, 229], "wrist_right": [1111, 229],
        "belt_center": [765, 386], "crotch_seam": [765, 496],
    },
    "casual-side": {
        "crown": [482, 49], "chin": [579, 267], "sole": [516, 1503],
        "back_skull_hair": [355, 171], "nose": [608, 203],
        "pupil": [566, 177], "mouth": [589, 230], "ear_center": [484, 192],
        "shoulder_estimate": [471, 357], "sweater_hem": [509, 760],
        "skirt_hem": [509, 820], "knee_estimate": [507, 1017],
        "heel": [413, 1487], "toe": [631, 1487],
    },
    "work-side": {
        "crown": [480, 34], "chin": [565, 242], "sole": [516, 1503],
        "back_skull_hair": [354, 159], "nose": [595, 184],
        "pupil": [556, 162], "mouth": [578, 210], "ear_center": [483, 181],
        "shoulder_estimate": [474, 323], "belt_center": [520, 571],
        "knee_estimate": None, "heel": [418, 1484], "toe": [626, 1484],
    },
}


def main():
    OUT.mkdir(exist_ok=True)
    results = {}
    rows = []
    for name, pts in LANDMARKS.items():
        outfit, view = name.split("-")
        path = SOURCE / outfit / f"bina-{outfit}-tpose-{view}.png"
        size = Image.open(path).size
        stature = pts["sole"][1] - pts["crown"][1]
        metrics = {"illustrated_shod_height": stature}

        def vertical(label, a, b):
            if pts.get(a) and pts.get(b):
                metrics[label] = pts[b][1] - pts[a][1]

        def horizontal(label, a, b):
            if pts.get(a) and pts.get(b):
                metrics[label] = pts[b][0] - pts[a][0]

        vertical("head_height", "crown", "chin")
        vertical("face_height_hairline_to_chin", "hairline", "chin")
        horizontal("visible_face_width_at_cheeks", "cheek_left", "cheek_right")
        horizontal("hair_silhouette_width", "hair_left", "hair_right")
        horizontal("pupil_spacing", "pupil_left", "pupil_right")
        horizontal("left_eye_width", "eye_outer_left", "eye_inner_left")
        horizontal("right_eye_width", "eye_inner_right", "eye_outer_right")
        vertical("left_eye_opening_height", "eye_upper_left", "eye_lower_left")
        vertical("right_eye_opening_height", "eye_upper_right", "eye_lower_right")
        horizontal("mouth_width", "mouth_left", "mouth_right")
        horizontal("neck_width", "neck_left", "neck_right")
        horizontal("shoulder_width_estimate", "shoulder_left_estimate", "shoulder_right_estimate")
        horizontal("arm_span", "fingertip_left", "fingertip_right")
        vertical("eye_to_nose", "pupil_left", "nose")
        vertical("nose_to_mouth", "nose", "mouth_center")
        vertical("mouth_to_chin", "mouth_center", "chin")
        vertical("brow_to_eye", "brow_left", "pupil_left")
        horizontal("profile_depth_hair_to_nose", "back_skull_hair", "nose")
        horizontal("shoe_length", "heel", "toe")
        ratios = {f"{k}_over_stature": round(v / stature, 6) for k, v in metrics.items() if k != "illustrated_shod_height"}
        if "head_height" in metrics:
            ratios["head_count"] = round(stature / metrics["head_height"], 4)
        if "visible_face_width_at_cheeks" in metrics:
            fw = metrics["visible_face_width_at_cheeks"]
            for k in ["pupil_spacing", "left_eye_width", "right_eye_width", "mouth_width"]:
                ratios[f"{k}_over_face_width"] = round(metrics[k] / fw, 6)
            ratios["eye_opening_height_over_eye_width"] = round(metrics["left_eye_opening_height"] / metrics["left_eye_width"], 6)
            ratios["face_width_over_head_height"] = round(fw / metrics["head_height"], 6)
            if pts.get("hairline"):
                fh = metrics["face_height_hairline_to_chin"]
                ratios["face_height_over_face_width"] = round(fh / fw, 6)
                for label, point in [("eye", "pupil_left"), ("nose", "nose"), ("mouth", "mouth_center")]:
                    ratios[f"{label}_level_from_hairline_over_face_height"] = round((pts[point][1] - pts["hairline"][1]) / fh, 6)
            eye_y = pts["pupil_left"][1]
            # Eye-line origin works for both outfits without inventing the hidden hairline.
            face_coordinates = {k: [round((p[0] - 765) / fw, 6), round((p[1] - eye_y) / fw, 6)]
                                for k, p in pts.items() if p and k in ["chin", "hairline", "cheek_left", "cheek_right", "pupil_left", "pupil_right", "nose", "mouth_left", "mouth_right", "mouth_center", "brow_left", "brow_right"]}
        else:
            face_coordinates = {}
        origin_x = 765 if view != "side" else pts["crown"][0]
        normalized = {k: [round((p[0] - origin_x) / stature, 6), round((p[1] - pts["crown"][1]) / stature, 6)]
                      if p else None for k, p in pts.items()}
        results[name] = {"source": str(path.relative_to(ROOT)).replace('\\', '/'),
                         "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "image_size": size,
                         "landmarks_px": pts, "metrics_px": metrics, "ratios": ratios,
                         "normalized_by_stature": normalized, "face_coordinates_by_width_eye_origin": face_coordinates}
        for metric, value in metrics.items():
            rows.append([name, metric, value, round(value / stature, 6)])
        encoded = base64.b64encode(path.read_bytes()).decode()
        w, h = size
        svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}"><image width="{w}" height="{h}" href="data:image/png;base64,{encoded}"/>'
        for label, pt in pts.items():
            if not pt:
                continue
            x, y = pt
            svg += f'<circle cx="{x}" cy="{y}" r="2" fill="#ee2045"><title>{label}: ({x},{y})</title></circle>'
        guides = ["crown", "chin", "sole", "hairline", "pupil_left", "nose", "mouth_center", "belt_center", "skirt_hem"]
        for label in guides:
            if pts.get(label):
                y = pts[label][1]
                svg += f'<path d="M20 {y}H{w-20}" stroke="#007ba7" stroke-width="0.7" stroke-dasharray="4 4"/><text x="25" y="{max(15,y-5)}" font-family="sans-serif" font-size="13" fill="#006688">{label}: y={y}</text>'
        svg += '</svg>'
        (OUT / f"{name}-annotated.svg").write_text(svg, encoding="utf-8")
    output = {"method": "Manual pixel landmarks on all six original drawings; arithmetic is reproducible. Not automatic facial landmark detection.",
              "coordinate_convention": "Original pixels; x increases right, y increases down. Crown excludes ahoge and glasses. Stature includes shoes.",
              "estimated_uncertainty_px": {"front_face": 2, "front_body_visible": 4, "side_visible": 4, "shoulder_joint_estimate": 10},
              "occlusion": "null means obscured/unobservable. Back-view chin, work-front hairline and clothed anatomical waist/crotch are not inferred.",
              "model_mapping": "Use one uniform s=target_shod_height/source_shod_height; x'=center_x+(x-source_center_x)*s; y'=target_crown_y+(y-source_crown_y)*s. Never independently stretch head or facial features.",
              "views": results}
    (OUT / "proportions.json").write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    with (OUT / "measurements.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["view", "measurement", "pixels", "fraction_of_shod_stature"])
        writer.writerows(rows)
    # A standalone measurement artifact, not a change to the model or application.
    html = '<!doctype html><meta charset="utf-8"><title>Bina T-pose measurements</title><style>body{font:16px system-ui;max-width:1400px;margin:30px auto;padding:20px;background:#f6f5f2;color:#222}table{border-collapse:collapse}td,th{padding:8px 16px;border:1px solid #ccc}section{background:white;padding:20px;margin:20px 0}img{max-width:100%;max-height:800px}code{background:#eee}p{line-height:1.7}</style><h1>Bina 原始 T-pose 比例测量</h1><p>仅测量，不生成、不修改模型。坐标取原图像素，人工标点后计算；正面五官约 ±2 px，身体轮廓约 ±4 px。头顶不含呆毛和眼镜；全高包含鞋底。红点为已观测坐标，蓝线为关键高度；悬停红点可读坐标。遮挡点记为 null。</p><p>旧截图测量结果不作为依据。肩关节藏在宽松衣物内，仅估计；衣服下摆、腰带和裤缝不代表人体骨点。</p><table><tr><th>视图</th><th>全高 px</th><th>头高 px</th><th>头高/全高</th><th>头身数</th></tr>'
    for name, d in results.items():
        m, r = d["metrics_px"], d["ratios"]
        html += f'<tr><td>{name}</td><td>{m["illustrated_shod_height"]}</td><td>{m.get("head_height","遮挡")}</td><td>{r.get("head_height_over_stature","—")}</td><td>{r.get("head_count","—")}</td></tr>'
    html += '</table><p>侧面与正面的头身比并不完全相同，不能把三张图当成严格正交的工程图。以日常装正面作为日常模型的主基准，侧面提供轮廓和前后深度约束；工作装另行保留数据。</p><p>生成/绑定约束：全身统一等比缩放；脸部用瞳孔中线与脸宽归一化。不得单独放大头、拉长脸或移动五官来适配素材。</p>'
    for name, d in results.items():
        html += f'<section><h2>{name}</h2><img src="{name}-annotated.svg"><details><summary>全部测量值与比例</summary><pre>{json.dumps({"pixels":d["metrics_px"],"ratios":d["ratios"]},indent=2)}</pre></details></section>'
    (OUT / "index.html").write_text(html, encoding="utf-8")
    for name, d in results.items():
        print(name, json.dumps({"pixels": d["metrics_px"], "ratios": d["ratios"]}))


if __name__ == "__main__":
    main()
