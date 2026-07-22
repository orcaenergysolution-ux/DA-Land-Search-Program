"""Helper to append per-state vision-extracted markers to aemo_vision_extracts.json.

Used overnight while the assistant streams markers through. Keep this file even
after extraction is done — it's the canonical writer for the JSON store.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
EXTRACTS = ROOT / "data" / "intermediate" / "aemo_vision_extracts.json"


def append(state: str, markers: list[dict]) -> None:
    if EXTRACTS.exists():
        d = json.loads(EXTRACTS.read_text(encoding="utf-8"))
    else:
        d = {"states_completed": [], "markers": []}
    # remove any prior markers for this state (idempotent rerun)
    before = len(d["markers"])
    d["markers"] = [m for m in d["markers"] if m.get("state") != state]
    removed = before - len(d["markers"])
    d["markers"].extend(markers)
    if state not in d["states_completed"]:
        d["states_completed"].append(state)
    EXTRACTS.write_text(json.dumps(d, indent=2), encoding="utf-8")
    print(f"{state}: +{len(markers)} markers (replaced {removed}); total={len(d['markers'])}")


if __name__ == "__main__":
    # called via importlib by the assistant during extraction
    pass
