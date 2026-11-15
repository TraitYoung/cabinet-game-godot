"""根据 `docs/characters/cabinet_visuals.json` 调用 Doubao-Seedream-5.5 批量生成内阁成员三栏概念设定图。

用法示例：
    python tools\\generate_cabinet_characters.py --tier all --workers 3
    python tools\\generate_cabinet_characters.py --only chizheng,bit,vinci,taki --workers 2
    python tools\\generate_cabinet_characters.py --tier 1 --overwrite
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import threading
from pathlib import Path
from typing import Any

from seedream import generate_image

REPO_ROOT = Path(__file__).resolve().parent.parent
VISUALS_JSON = REPO_ROOT / "docs" / "characters" / "cabinet_visuals.json"
OUT_DIR = REPO_ROOT / "docs" / "media" / "cabinet-concepts"

_PRINT_LOCK = threading.Lock()


def _safe_print(message: str) -> None:
    with _PRINT_LOCK:
        print(message, flush=True)


def load_members() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    data = json.loads(VISUALS_JSON.read_text(encoding="utf-8"))
    baseline = data.get("style_baseline", {})
    members = data.get("members", [])
    return baseline, members


def _process_member(
    member: dict[str, Any],
    *,
    canvas_size: str,
    overwrite: bool,
) -> tuple[str, str, dict[str, Any] | None]:
    persona_id = member["persona_id"]
    order = int(member["order"])
    out_path = OUT_DIR / f"{order:02d}-{persona_id}-concept.png"

    if out_path.is_file() and out_path.stat().st_size > 0 and not overwrite:
        _safe_print(f"[SKIP] {out_path}")
        return persona_id, "skipped", None

    _safe_print(f"[START] {order:02d}-{persona_id} ({member['display_name']}) -> {out_path.name}")
    info = generate_image(
        member["concept_prompt"],
        out_path,
        size=canvas_size,
        output_format="png",
        transparent=False,
        watermark=False,
    )
    _safe_print(
        f"[OK] {info['out_path']} ({info['elapsed_sec']}s, {info['size']}, {info['model']})"
    )
    return persona_id, "generated", info


def main() -> None:
    parser = argparse.ArgumentParser(description="批量生成内阁成员三栏概念设定图 (Seedream 5.5)")
    parser.add_argument(
        "--only",
        default=None,
        help="只生成指定角色 ID（逗号分隔，如 chizheng,bit,vinci）",
    )
    parser.add_argument(
        "--tier",
        choices=["1", "2", "3", "all"],
        default="all",
        help="按内阁梯队筛选生成（默认 all）",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=3,
        help="并发生成线程数（默认 3）",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="覆盖已存在的输出文件",
    )
    args = parser.parse_args()

    baseline, members = load_members()
    canvas_size = str(baseline.get("canvas_size", "2560x1440"))

    selected = members
    if args.tier != "all":
        tier_num = int(args.tier)
        selected = [m for m in selected if int(m.get("tier", 0)) == tier_num]

    if args.only:
        wanted = [item.strip().lower() for item in args.only.split(",") if item.strip()]
        valid_ids = {m["persona_id"].lower() for m in members}
        unknown = [item for item in wanted if item not in valid_ids]
        if unknown:
            raise SystemExit(
                f"未知角色 ID: {', '.join(unknown)}；可选: {', '.join(m['persona_id'] for m in members)}"
            )
        wanted_set = set(wanted)
        selected = [m for m in selected if m["persona_id"].lower() in wanted_set]

    if not selected:
        raise SystemExit("筛选后没有待生成的内阁成员。")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    worker_count = max(1, min(args.workers, len(selected)))

    failures: list[tuple[str, str]] = []
    generated_count = 0
    skipped_count = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=worker_count) as pool:
        future_map = {
            pool.submit(
                _process_member,
                member,
                canvas_size=canvas_size,
                overwrite=args.overwrite,
            ): member["persona_id"]
            for member in selected
        }
        for future in concurrent.futures.as_completed(future_map):
            persona_id = future_map[future]
            try:
                _, status, _ = future.result()
                if status == "generated":
                    generated_count += 1
                else:
                    skipped_count += 1
            except Exception as exc:
                failures.append((persona_id, str(exc)))
                _safe_print(f"[ERR] {persona_id}: {exc}")

    _safe_print(
        f"完成：新生成 {generated_count} 张，跳过 {skipped_count} 张，失败 {len(failures)} 张。"
    )
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
