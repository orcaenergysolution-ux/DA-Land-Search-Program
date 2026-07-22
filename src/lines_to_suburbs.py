"""Derive the list of towns/suburbs a transmission network passes through.

Walks the 66 kV (or chosen voltage) line path from the existing GeoJSON, samples
one point per grid cell, and reverse-geocodes each via the free OpenStreetMap
Nominatim API to get the suburb/town name. Outputs a deduped 'Suburb:STATE' list
that find_properties.py reads with --locations-file.

Nominatim policy: <= 1 request/second, descriptive User-Agent, cache results.
This script honours all three (results cached to data/intermediate/).

Example:
    python src/lines_to_suburbs.py --state VIC --voltages 66
    python src/find_properties.py --state VIC --locations-file data/intermediate/lines_suburbs_VIC.txt \
        --property-types land,rural --min-land 10000 --max-distance 300
"""
from __future__ import annotations
import argparse
import json
import sys
import time
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from urllib.error import HTTPError, URLError

ROOT = Path(__file__).parent.parent
LINES = ROOT / "data" / "intermediate" / "transmission_lines.geojson"
CACHE = ROOT / "data" / "intermediate" / "reverse_geocode_cache.json"

NOMINATIM = "https://nominatim.openstreetmap.org/reverse"
UA = "nem-property-finder/0.1 (66kV proximity tool)"

STATE_BBOX = {
    "VIC": (-39.3, 140.9, -33.9, 150.1),
    "NSW": (-37.6, 140.9, -28.1, 153.7),
    "QLD": (-29.2, 137.9, -10.0, 154.0),
    "SA":  (-38.5, 129.0, -25.9, 141.1),
    "TAS": (-43.7, 144.5, -39.5, 148.5),
    "WA":  (-35.2, 112.9, -13.7, 129.1),
    "NT":  (-26.0, 129.0, -10.9, 138.1),
    "ACT": (-35.95, 148.7, -35.1, 149.5),
}

STATE_NAMES = {   # Nominatim 'state' -> our code
    "Victoria": "VIC", "New South Wales": "NSW", "Queensland": "QLD",
    "South Australia": "SA", "Tasmania": "TAS", "Western Australia": "WA",
    "Northern Territory": "NT", "Australian Capital Territory": "ACT",
}


def sample_points(voltages, tol, bbox, cell):
    """One representative (lat, lon) per grid cell touched by a target line."""
    fc = json.loads(LINES.read_text(encoding="utf-8"))
    s, w, n, e = bbox
    seen = {}
    for feat in fc.get("features", []):
        v = feat.get("properties", {}).get("voltage_kv")
        if v is None or not any(abs(v - tv) <= tol for tv in voltages):
            continue
        for lon, lat in feat.get("geometry", {}).get("coordinates", []):
            if not (s <= lat <= n and w <= lon <= e):
                continue
            key = (round(lat / cell), round(lon / cell))
            if key not in seen:
                seen[key] = (lat, lon)
    return list(seen.values())


def load_cache():
    if CACHE.exists():
        return json.loads(CACHE.read_text(encoding="utf-8"))
    return {}


def reverse(lat, lon, cache):
    key = f"{lat:.4f},{lon:.4f}"
    if key in cache:
        return cache[key]
    q = urlencode({"format": "jsonv2", "lat": lat, "lon": lon,
                   "zoom": 14, "addressdetails": 1})
    req = Request(f"{NOMINATIM}?{q}", headers={"User-Agent": UA})
    try:
        with urlopen(req, timeout=30) as r:
            data = json.loads(r.read().decode())
        addr = data.get("address", {})
    except (HTTPError, URLError, TimeoutError) as ex:
        print(f"  geocode {key} -> {ex}", file=sys.stderr)
        addr = {}
    cache[key] = addr
    time.sleep(1.1)   # Nominatim: max 1 req/sec
    return addr


def pick_place(addr):
    for k in ("suburb", "town", "village", "city", "hamlet", "municipality",
              "locality", "county"):
        if addr.get(k):
            return addr[k]
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--state", default="VIC", choices=sorted(STATE_BBOX))
    ap.add_argument("--voltages", default="66", help="Comma list of kV (default 66).")
    ap.add_argument("--voltage-tol", type=float, default=0.5)
    ap.add_argument("--cell", type=float, default=0.10,
                    help="Grid cell size in degrees (~11 km at 0.10). Bigger = fewer "
                         "geocode calls but coarser coverage. 0.05 ~= 6 km (slower).")
    ap.add_argument("--max-points", type=int, default=800,
                    help="Safety cap on reverse-geocode calls (default 800).")
    ap.add_argument("--out", default=None, help="Output locations file path.")
    args = ap.parse_args()

    voltages = [float(v) for v in args.voltages.split(",") if v.strip()]
    out = Path(args.out) if args.out else (
        ROOT / "data" / "intermediate" / f"lines_suburbs_{args.state}.txt")

    pts = sample_points(voltages, args.voltage_tol, STATE_BBOX[args.state], args.cell)
    print(f"{len(pts)} grid points along {voltages} kV lines in {args.state}.",
          file=sys.stderr)
    if len(pts) > args.max_points:
        print(f"Capping to {args.max_points} (raise --cell to reduce, or --max-points "
              f"to allow more). ~{args.max_points}s at 1 req/sec.", file=sys.stderr)
        pts = pts[:args.max_points]
    else:
        print(f"~{len(pts)}s to geocode at 1 req/sec.", file=sys.stderr)

    cache = load_cache()
    places = {}   # name -> state code
    try:
        for i, (lat, lon) in enumerate(pts, 1):
            addr = reverse(lat, lon, cache)
            name = pick_place(addr)
            st = STATE_NAMES.get(addr.get("state", ""), args.state)
            if name and st == args.state:
                places.setdefault(name, st)
            if i % 25 == 0:
                print(f"  {i}/{len(pts)} points, {len(places)} towns so far",
                      file=sys.stderr)
                CACHE.write_text(json.dumps(cache), encoding="utf-8")  # checkpoint
    finally:
        CACHE.write_text(json.dumps(cache), encoding="utf-8")

    lines = [f"{name}:{st}" for name, st in sorted(places.items())]
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nWrote {out}: {len(lines)} towns/suburbs near {voltages} kV lines.")
    print("Feed it to the finder with:  --locations-file " + str(out))


if __name__ == "__main__":
    main()
