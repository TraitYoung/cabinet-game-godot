"""Build/export Bina's work model through the installed PSD2Live MCP proxy."""

import importlib.util
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets/bina-live2d"
SOURCE = ASSETS / "source-work"
EXPORT = ROOT / ".devstack/work-export"
RUNTIME = ROOT / "frontend/public/live2d/bina-work"


def main():
    spec = importlib.util.spec_from_file_location(
        "psd2live_proxy", ROOT / ".devstack/tools/psd2live/mcp_proxy.py"
    )
    proxy = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(proxy)
    layout = json.loads((SOURCE / "bina.layout.json").read_text(encoding="utf-8"))
    with proxy.Client(timeout=180) as client:
        client.edit("project_import_layout", path=str(SOURCE / "bina.layout.json"))
        for layer, side in (("eye_left", "right"), ("eye_right", "left")):
            client.edit("layer_classify", layer_id=layer, role="eyewhite", side=side)
        client.edit("rig_generate")
        client.edit("project_save_as", path=str(ASSETS / "bina-work.psd2live"))
        report = client.edit("project_export_model", output_directory=str(EXPORT))
        _, previews = client.call("view_render_model", {
            "viewport": {"mode": "canvas_rect", "left": 530, "top": 0, "width": 480, "height": 1024},
            "include_layer_ids": [layer["id"] for layer in layout["layers"]],
            "target_long_edge": 1200,
            "background": "checkerboard",
        })
    for index, preview in enumerate(previews):
        (SOURCE / f"rig-preview-{index}.png").write_bytes(preview)
    for artifact in report["files"]:
        source = Path(artifact["path"])
        relative = str(source.relative_to(EXPORT)).replace("bina.layout", "bina")
        if source.suffix in (".cmo3", ".can3") or source.name.endswith(".psd2live.json"):
            destination = ASSETS / source.name.replace("bina.layout", "bina-work")
        else:
            destination = RUNTIME / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        if source.suffix == ".json":
            destination.write_text(source.read_text(encoding="utf-8").replace("bina.layout", "bina"), encoding="utf-8")
        else:
            shutil.copyfile(source, destination)
        artifact["path"] = str(destination.relative_to(ROOT))
    report.update(source="assets/bina-live2d/source-work/bina.layout.json", pose="standing", outfit="work")
    (ASSETS / "work-generation-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Exported work model to {RUNTIME}")


if __name__ == "__main__":
    main()
