"""Rebuild the seam-repaired Bina heads using the native PSD2Live editor."""

import importlib.util
import json
from pathlib import Path
import shutil


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets/bina-live2d/face-revision"
POSES = [
    {},
    {"ParamEyeLOpen": 0.5, "ParamEyeROpen": 0.5},
    {"ParamEyeLOpen": 0, "ParamEyeROpen": 0},
    {"ParamAngleX": -30},
    {"ParamAngleX": 30},
    {"ParamAngleY": 30},
    {"ParamAngleY": -30},
    {"ParamAngleX": 20, "ParamAngleY": 15, "ParamEyeLOpen": 0.2, "ParamEyeROpen": 0.2},
    {"ParamAngleZ": 10},
]


def build(client, outfit):
    folder = SOURCE / outfit
    layout = json.loads((folder / "bina.layout.json").read_text())
    client.edit("project_import_layout", path=str(folder / "bina.layout.json"), discard_unsaved=True)
    for suffix, side in (("left", "right"), ("right", "left")):
        for prefix, role in (("eye", "eyewhite"), ("closed", "eye_close"), ("brow", "eyebrow")):
            client.edit("layer_classify", layer_id=f"{prefix}_{suffix}", role=role, side=side)
    client.edit("settings_update", changes={
        "seeThroughEyes": False, "seeThroughBrows": False,
        "featureDisplacementEnabled": False, "mouthOutlineEnabled": False,
        "physicsEyeJelly": False, "meshMaxEdgeDistance": 8,
        "meshInteriorDensity": 12, "meshOuterMargin": 1,
        "rigTuning": {
            "faceContour": 0, "eyeFarShrink": 0, "eyeNearGrow": 0,
            "eyeShift": 0, "eyeTilt": 0, "eyeTiltStretch": 0,
            "featurePlane": 0, "browLift": 10,
        },
    })
    client.edit("rig_generate")
    objects = client.call("workspace_inspect", {"scope": "objects", "limit": 64})[0]["items"]
    meshes = {item["layerId"]: item["target"] for item in objects if "layerId" in item}
    client.edit("object_edit_appearance", edits=[{
        "action": "bind", "kind": "mesh", "id": meshes["head"].split(":", 1)[1],
        "parent_id": "DeformFaceNinePose", "space": "canvas",
    }])
    changes = []
    for suffix, side in (("left", "R"), ("right", "L")):
        parameter = f"ParamEye{side}Open"
        for prefix, values in (("eye", ((0, 0), (0.03, 1), (1, 1))),
                               ("closed", ((0, 1), (0.03, 0), (1, 0)))):
            for value, opacity in values:
                changes.append({"op": "set", "target": meshes[f"{prefix}_{suffix}"],
                                "key": {parameter: value}, "channels": {"opacity": opacity}})
    client.edit("keyform_apply", changes=changes)
    project = SOURCE / f"bina-{outfit}-face-v2.psd2live"
    client.edit("project_save_as", path=str(project))
    _, images = client.call("view_render_poses", {
        "viewport": {"mode": "canvas_rect", "left": 650, "top": 0, "width": 230, "height": 235},
        "include_layer_ids": [layer["id"] for layer in layout["layers"]],
        "poses": POSES, "columns": 3, "target_long_edge": 1800, "background": "checkerboard",
    })
    for index, image in enumerate(images):
        (SOURCE / f"{outfit}-after-{index}.png").write_bytes(image)
    export = ROOT / ".devstack/face-revision/export" / outfit
    report = client.edit("project_export_model", output_directory=str(export))
    runtime = ROOT / "frontend/public/live2d" / ("bina-work" if outfit == "work" else "bina-registered")
    backup = ROOT / ".devstack/face-revision/runtime-before" / outfit
    if not backup.exists():
        shutil.copytree(runtime, backup)
    for artifact in report["files"]:
        source = Path(artifact["path"])
        if source.suffix in (".cmo3", ".can3") or source.name.endswith(".psd2live.json"):
            destination = SOURCE / source.name.replace("bina.layout", f"bina-{outfit}-face-v2")
        else:
            destination = runtime / str(source.relative_to(export)).replace("bina.layout", "bina")
        destination.parent.mkdir(parents=True, exist_ok=True)
        if source.suffix == ".json":
            destination.write_text(source.read_text().replace("bina.layout", "bina"))
        else:
            shutil.copyfile(source, destination)
        artifact["path"] = str(destination.relative_to(ROOT))
    report.update(outfit=outfit, source=str(project.relative_to(ROOT)), poses=POSES,
                  limitations=["Shared head/hair surface; no separate hair physics or iris tracking",
                               "Closed original mouth; no lip sync"])
    (SOURCE / f"{outfit}-export.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(f"Exported {outfit} head repair to {runtime.relative_to(ROOT)}", flush=True)


def main():
    spec = importlib.util.spec_from_file_location("psd2live_proxy", ROOT / ".devstack/tools/psd2live/mcp_proxy.py")
    proxy = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(proxy)
    with proxy.Client(timeout=180) as client:
        for outfit in ("work", "casual"):
            build(client, outfit)


if __name__ == "__main__":
    main()
