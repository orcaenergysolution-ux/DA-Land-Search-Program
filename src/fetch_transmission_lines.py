"""Fetch high-voltage transmission lines from OpenStreetMap via Overpass API.

We pull every way tagged power=line with voltage >= 66 kV across the NEM
states. Output is a GeoJSON FeatureCollection with one LineString per way
plus voltage / operator metadata. Cached to data/intermediate/transmission_lines.geojson.

Overpass has rate limits and per-query result-size caps, so we split by state
bbox and merge.
"""
from __future__ import annotations
import json
import time
import sys
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import quote
from urllib.error import URLError, HTTPError

ROOT = Path(__file__).parent.parent
OUT = ROOT / "data" / "intermediate" / "transmission_lines.geojson"
SUB_OUT = ROOT / "data" / "intermediate" / "substations.geojson"

OVERPASS_ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
]

# (south, west, north, east) per chunk; large states split to avoid Overpass timeouts
STATE_BBOX = {
    "NSW_N": (-32.5, 140.9, -28.1, 153.7),
    "NSW_S": (-37.6, 140.9, -32.5, 153.7),
    "VIC": (-39.3, 140.9, -33.9, 150.0),
    "QLD_N":   (-19.5, 137.9, -10.0, 146.0),
    "QLD_NE":  (-19.5, 146.0, -10.0, 154.0),
    "QLD_C":   (-24.5, 137.9, -19.5, 152.0),
    "QLD_S":   (-29.2, 137.9, -24.5, 154.0),
    "SA_N":  (-32.0, 129.0, -25.9, 141.1),
    "SA_S":  (-38.5, 129.0, -32.0, 141.1),
    "TAS": (-43.7, 144.5, -39.5, 148.5),
}


def overpass(query: str, max_rounds: int = 3) -> dict | None:
    body = "data=" + quote(query)
    for round_i in range(max_rounds):
        for ep in OVERPASS_ENDPOINTS:
            try:
                req = Request(ep, data=body.encode("utf-8"), method="POST",
                              headers={"User-Agent": "nem-generation-map/0.1"})
                with urlopen(req, timeout=180) as r:
                    return json.loads(r.read().decode("utf-8"))
            except (HTTPError, URLError, TimeoutError) as e:
                msg = str(e)
                print(f"  {ep} -> {msg}, next endpoint", file=sys.stderr)
                # 429 -> back off harder
                wait = 15 if "429" in msg else 5
                time.sleep(wait)
        # all endpoints failed this round; back off then retry
        backoff = 30 * (round_i + 1)
        print(f"  All endpoints failed round {round_i+1}; sleeping {backoff}s", file=sys.stderr)
        time.sleep(backoff)
    return None


def fetch_lines_for_state(state: str) -> list[dict]:
    s, w, n, e = STATE_BBOX[state]
    bbox = f"{s},{w},{n},{e}"
    q = f"""
[out:json][timeout:180];
(
  way["power"="line"]["voltage"]({bbox});
  way["power"="cable"]["voltage"]["location"!="underground"]({bbox});
);
out geom;
"""
    print(f"\n{state} bbox={bbox} ...")
    data = overpass(q)
    if not data:
        return []
    features = []
    for el in data.get("elements", []):
        if el.get("type") != "way" or "geometry" not in el:
            continue
        tags = el.get("tags", {})
        voltage_raw = tags.get("voltage", "")
        # voltage may be "330000" or "330000;220000" - take max
        try:
            voltages = [int(v.strip()) for v in voltage_raw.replace(",", ";").split(";") if v.strip().isdigit()]
            voltage_kv = max(voltages) / 1000 if voltages else None
        except Exception:
            voltage_kv = None
        if voltage_kv is None or voltage_kv < 66:
            continue
        coords = [[p["lon"], p["lat"]] for p in el["geometry"]]
        features.append({
            "type": "Feature",
            "geometry": {"type": "LineString", "coordinates": coords},
            "properties": {
                "id": el["id"],
                "voltage_kv": voltage_kv,
                "operator": tags.get("operator", ""),
                "ref": tags.get("ref", ""),
                "name": tags.get("name", ""),
                "frequency": tags.get("frequency", ""),
                "circuits": tags.get("circuits", ""),
                "state": state,
            },
        })
    print(f"  -> {len(features)} lines")
    return features


def fetch_substations_for_state(state: str) -> list[dict]:
    s, w, n, e = STATE_BBOX[state]
    bbox = f"{s},{w},{n},{e}"
    q = f"""
[out:json][timeout:180];
(
  node["power"="substation"]["voltage"]({bbox});
  way["power"="substation"]["voltage"]({bbox});
);
out center;
"""
    print(f"  substations {state} ...")
    data = overpass(q)
    if not data:
        return []
    features = []
    for el in data.get("elements", []):
        tags = el.get("tags", {})
        v_raw = tags.get("voltage", "")
        try:
            voltages = [int(v.strip()) for v in v_raw.replace(",", ";").split(";") if v.strip().isdigit()]
            voltage_kv = max(voltages) / 1000 if voltages else None
        except Exception:
            voltage_kv = None
        if voltage_kv is None or voltage_kv < 66:
            continue
        if el["type"] == "node":
            lat, lon = el["lat"], el["lon"]
        elif "center" in el:
            lat, lon = el["center"]["lat"], el["center"]["lon"]
        else:
            continue
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [lon, lat]},
            "properties": {
                "voltage_kv": voltage_kv,
                "name": tags.get("name", ""),
                "operator": tags.get("operator", ""),
                "ref": tags.get("ref", ""),
                "state": state,
            },
        })
    print(f"    -> {len(features)} substations")
    return features


def main():
    all_lines: list[dict] = []
    all_subs: list[dict] = []
    # save progressively so partial failures aren't catastrophic
    for state in ["TAS", "SA_S", "SA_N", "VIC", "NSW_S", "NSW_N", "QLD_S", "QLD_C", "QLD_NE", "QLD_N"]:
        try:
            all_lines.extend(fetch_lines_for_state(state))
            all_subs.extend(fetch_substations_for_state(state))
        except Exception as e:
            print(f"  {state} failed: {e}", file=sys.stderr)
        # incremental save
        OUT.write_text(json.dumps({"type": "FeatureCollection", "features": all_lines}), encoding="utf-8")
        SUB_OUT.write_text(json.dumps({"type": "FeatureCollection", "features": all_subs}), encoding="utf-8")
        time.sleep(5)
    print(f"\nWrote {OUT}: {len(all_lines)} lines")
    print(f"Wrote {SUB_OUT}: {len(all_subs)} substations")


if __name__ == "__main__":
    main()
