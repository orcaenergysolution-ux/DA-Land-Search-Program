"""Append markers with pixel positions (x_pct, y_pct) into aemo_vision_extracts_v2.json."""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
EXTRACTS = ROOT / "data" / "intermediate" / "aemo_vision_extracts_v2.json"


def append(state: str, markers: list[dict]) -> None:
    if EXTRACTS.exists():
        d = json.loads(EXTRACTS.read_text(encoding="utf-8"))
    else:
        d = {"states_completed": [], "markers": []}
    before = len(d["markers"])
    d["markers"] = [m for m in d["markers"] if m.get("state") != state]
    removed = before - len(d["markers"])
    d["markers"].extend(markers)
    if state not in d["states_completed"]:
        d["states_completed"].append(state)
    EXTRACTS.write_text(json.dumps(d, indent=2), encoding="utf-8")
    print(f"{state}: +{len(markers)} (replaced {removed}); total={len(d['markers'])}")
