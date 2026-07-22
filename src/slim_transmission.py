"""Filter transmission_lines.geojson to AEMO-relevant backbone and shrink size.

- Drop ways with voltage < 132 kV (66 kV distribution = noise on a state map).
- Round coordinates to 4 d.p. (~11 m precision — well within AEMO map accuracy).
- Drop unused properties.
"""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent
SRC = ROOT / "data" / "intermediate" / "transmission_lines.geojson"
OUT = ROOT / "data" / "intermediate" / "transmission_lines.slim.geojson"

MIN_KV = 66


def main():
    d = json.loads(SRC.read_text(encoding="utf-8"))
    slim = []
    for f in d["features"]:
        v = (f.get("properties") or {}).get("voltage_kv") or 0
        if v < MIN_KV:
            continue
        coords = [[round(x, 4), round(y, 4)] for x, y in f["geometry"]["coordinates"]]
        slim.append({
            "type": "Feature",
            "geometry": {"type": "LineString", "coordinates": coords},
            "properties": {
                "v": v,
                "n": f["properties"].get("name", "") or f["properties"].get("ref", ""),
                "o": f["properties"].get("operator", ""),
            },
        })
    OUT.write_text(json.dumps({"type": "FeatureCollection", "features": slim}, separators=(",", ":")), encoding="utf-8")
    print(f"In: {len(d['features'])}  Out: {len(slim)}  Size: {OUT.stat().st_size//1024} KB")


if __name__ == "__main__":
    main()
