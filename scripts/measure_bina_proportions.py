"""Record manually located reference landmarks and derive rig proportions."""

import base64
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets/bina-live2d/reference"

# Pixel landmarks on the user's 436 x 786 T-pose; x follows the viewer's left/right.
POINTS = {
    "crown": [220, 28], "hairline": [220, 87], "chin": [221, 230],
    "cheek_left": [154, 165], "cheek_right": [282, 165],
    "pupil_left": [186, 154], "pupil_right": [256, 154],
    "eye_outer_left": [164, 150], "eye_inner_left": [205, 153],
    "eye_inner_right": [236, 153], "eye_outer_right": [278, 150],
    "brow_left": [185, 131], "brow_right": [257, 131],
    "nose_tip": [220, 181], "mouth_left": [207, 199],
    "mouth_right": [236, 199], "mouth_center": [221, 200],
    "hair_left": [94, 164], "hair_right": [340, 164],
    "shoulder_left": [112, 262], "shoulder_right": [328, 262],
    "shoulder_mid": [220, 260], "skirt_hem": [220, 744],
    "neck_left": [193, 241], "neck_right": [247, 241],
}


def main():
    face_w, face_h, head_h, body_h = 128, 143, 202, 484
    scale = 705 / body_h  # Existing model: shoulder y=550, skirt hem y=1255.
    normalized = {name: {"x": round((x - 218) / face_w, 4),
                          "y": round((y - 87) / face_h, 4)}
                  for name, (x, y) in POINTS.items()}
    target = {name: [round(500 + (x - 220) * scale, 2),
                     round(550 + (y - 260) * scale, 2)]
              for name, (x, y) in POINTS.items()}
    data = {
        "source": "t-pose.png", "image_size": [436, 786],
        "method": "Manual landmarks; ratios calculated from pixel coordinates, not biometric detection",
        "uncertainty_px": {"facial_landmarks": 3, "hair_and_clothing": 5, "shoulders": 8},
        "definitions": {"head_height": "crown to chin, excluding ahoge and glasses",
                        "face_height": "central hairline to chin",
                        "body_anchor_span": "shoulder baseline to skirt hem; not full body height",
                        "shoulder_width": "estimated anatomical shoulder points; T-pose arms excluded"},
        "landmarks_px": POINTS, "face_normalized_landmarks": normalized,
        "measurements_px": {"head_height": head_h, "hair_width": 246,
                            "face_width_at_cheeks": face_w, "face_height": face_h,
                            "pupil_distance": 70, "eye_width_left": 41, "eye_width_right": 42,
                            "mouth_width": 29, "neck_width": 54, "shoulder_width_estimate": 216,
                            "shoulder_to_skirt_hem": body_h, "eye_to_nose": 27,
                            "nose_to_mouth": 19, "mouth_to_chin": 30},
        "ratios": {"face_height_over_width": round(face_h / face_w, 4),
                   "pupil_distance_over_face_width": round(70 / face_w, 4),
                   "eye_width_over_face_width": round(41.5 / face_w, 4),
                   "mouth_width_over_face_width": round(29 / face_w, 4),
                   "eye_line_from_hairline_over_face_height": round(67 / face_h, 4),
                   "nose_line_from_hairline_over_face_height": round(94 / face_h, 4),
                   "mouth_line_from_hairline_over_face_height": round(113 / face_h, 4),
                   "head_height_over_body_anchor_span": round(head_h / body_h, 4)},
        "rejected_screenshot": {"head_height_px": 264, "shoulder_to_skirt_hem_px": 402,
                                "head_over_body_anchor_span": round(264 / 402, 4),
                                "relative_head_oversize_percent": round(((264 / 402) / (head_h / body_h) - 1) * 100, 1),
                                "head_scale_at_fixed_body": round((head_h / body_h) / (264 / 402), 4)},
        "model_target": {"canvas": [1000, 1400], "body_scale": scale,
                         "mapping": "x=500+(reference_x-220)*scale; y=550+(reference_y-260)*scale",
                         "landmarks": target},
        "limitation": "Reference ends at thighs: full stature and conventional total head count cannot be measured.",
    }
    (OUT / "proportions.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    encoded = base64.b64encode((OUT / "t-pose.png").read_bytes()).decode()
    marks = []
    for name, (x, y) in POINTS.items():
        marks.append(f'<circle cx="{x}" cy="{y}" r="2" fill="#e53451"/>')
    lines = [("crown", 28), ("hairline", 87), ("eyes", 154), ("nose", 181),
             ("mouth", 200), ("chin", 230), ("shoulders", 260), ("skirt hem", 744)]
    for name, y in lines:
        marks.append(f'<path d="M80 {y}H430" stroke="#087eaa" stroke-width="0.7" stroke-dasharray="3 2"/>')
        marks.append(f'<text x="438" y="{y+3}" font-size="9" fill="#087eaa">{name}: y={y}</text>')
    marks.append('<path d="M220 10V760" stroke="#087eaa" stroke-width="0.7" stroke-dasharray="3 2"/>')
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="900" viewBox="0 0 1100 900">'
           '<rect width="1100" height="900" fill="white"/>'
           '<text x="30" y="30" font-size="21" font-family="sans-serif">Bina T-pose: measured proportions (436 x 786 px)</text>'
           f'<g transform="translate(20 65)"><image width="436" height="786" href="data:image/png;base64,{encoded}"/>'
           + ''.join(marks) + '</g>')
    rows = ["Manual landmark estimates: face +/-3 px", "Head: crown to chin; ahoge excluded",
            "Face: hairline to chin = 143 px", "Face width at cheeks = 128 px",
            "Pupil distance = 70 px (54.7% face width)", "Mean eye width = 41.5 px (32.4%)",
            "Mouth width = 29 px (22.7%)", "Hairline -> eyes: 67 px (46.9% face height)",
            "Eyes -> nose -> mouth -> chin: 27 / 19 / 30 px", "Head height / shoulder-to-hem = 202 / 484 = 0.4174",
            "Rejected screenshot: 264 / 402 = 0.6567", "Relative head oversize: +57.4% at fixed body scale",
            "Required head scale: 0.6355 at fixed body scale", "Thigh crop: full-body head count unavailable"]
    for i, row in enumerate(rows):
        svg += f'<text x="590" y="{100+i*38}" font-family="sans-serif" font-size="14" fill="#222">{row.replace("&", "&amp;").replace("<", "&lt;")}</text>'
    svg += '</svg>'
    (OUT / "proportions.svg").write_text(svg, encoding="utf-8")
    print(json.dumps({"ratios": data["ratios"], "comparison": data["rejected_screenshot"], "target": target}, indent=2))


if __name__ == "__main__":
    main()
