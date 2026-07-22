"""Find LAND PARCELS near transmission lines - on-market or not.

Unlike find_properties.py (which only sees advertised listings), this scans the
Vicmap cadastre: every land parcel in Victoria, whether or not it is for sale.
Free - no Apify credit, no API key.

Source: Victorian Government open data WFS
  https://opendata.maps.vic.gov.au/geoserver/wfs   layer open-data-platform:v_parcel_mp

How it works:
  1. Load the target-voltage lines from transmission_lines.geojson.
  2. Tile the corridor along those lines and pull parcels per tile. The server
     caps a response at 5000 features but reports the true total, so any tile
     that would truncate is split into quarters and re-fetched.
  3. Parcel area is computed from the polygon (the cadastre has no area field).
  4. Keep parcels >= --min-land whose boundary comes within --max-distance of a line.
  5. Optionally count nearby buildings (Overpass) to favour isolated blocks.

Output: outputs/parcels_<STATE>_<stamp>.md / .csv, closest-to-line first.

Note: the cadastre has no owner names or contact details - those are not open
data. Use the SPI / lot-plan in the report for a title search if needed.

Example:
    python src/find_parcels.py --state VIC --min-land 10000 --max-distance 200
    python src/find_parcels.py --max-tiles 40 --no-neighbours     # quick test
"""
from __future__ import annotations
import argparse
import csv
import json
import math
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from urllib.error import HTTPError, URLError

sys.path.insert(0, str(Path(__file__).parent))
import find_properties as fp   # reuse geo helpers, Overpass, state bboxes

ROOT = Path(__file__).parent.parent
OUT_DIR = ROOT / "outputs"
STATE_DIR = ROOT / "data" / "intermediate"

WFS = "https://opendata.maps.vic.gov.au/geoserver/wfs"
LAYER = "open-data-platform:v_parcel_mp"
SERVER_CAP = 5000          # GeoServer max features per response
UA = {"User-Agent": "nem-parcel-finder/0.1"}


# ------------------------------------------------------------------ geometry
def ring_area_m2(ring, lat0):
    """Shoelace area of a lon/lat ring, projected locally to metres."""
    mx = 111320.0 * math.cos(math.radians(lat0))
    my = 110540.0
    s = 0.0
    for (x1, y1), (x2, y2) in zip(ring, ring[1:]):
        s += (x1 * mx) * (y2 * my) - (x2 * mx) * (y1 * my)
    return abs(s) / 2.0


def geom_area_m2(geom):
    """Area of a Polygon/MultiPolygon in m2 (outer rings minus holes)."""
    if not geom:
        return 0.0
    t = geom.get("type")
    polys = geom["coordinates"] if t == "MultiPolygon" else [geom["coordinates"]]
    total = 0.0
    for poly in polys:
        if not poly:
            continue
        lat0 = poly[0][0][1]
        total += ring_area_m2(poly[0], lat0)
        for hole in poly[1:]:
            total -= ring_area_m2(hole, lat0)
    return total


def densify(ring, step_m=50.0):
    """Yield points along a ring, inserting extras so long edges aren't skipped."""
    for (x1, y1), (x2, y2) in zip(ring, ring[1:]):
        yield (y1, x1)
        d = fp.haversine(y1, x1, y2, x2)
        n = int(d // step_m)
        for i in range(1, n + 1):
            f = i / (n + 1)
            yield (y1 + (y2 - y1) * f, x1 + (x2 - x1) * f)


def geom_points(geom, step_m=50.0):
    t = geom.get("type")
    polys = geom["coordinates"] if t == "MultiPolygon" else [geom["coordinates"]]
    for poly in polys:
        for ring in poly:
            yield from densify(ring, step_m)


def centroid(geom):
    xs, ys, n = 0.0, 0.0, 0
    t = geom.get("type")
    polys = geom["coordinates"] if t == "MultiPolygon" else [geom["coordinates"]]
    for poly in polys:
        for x, y in poly[0]:
            xs += x
            ys += y
            n += 1
    return (ys / n, xs / n) if n else (None, None)


# ----------------------------------------------------------------------- wfs
def wfs_tile(w, s, e, n, retries=2):
    """Parcels intersecting a bbox. Returns (features, truncated_total_or_None)."""
    url = (f"{WFS}?service=WFS&version=2.0.0&request=GetFeature&typeNames={LAYER}"
           f"&outputFormat=application/json&srsName=EPSG:4326"
           f"&bbox={w},{s},{e},{n},EPSG:4326&count={SERVER_CAP}")
    for attempt in range(retries):
        try:
            with urlopen(Request(url, headers=UA), timeout=60) as r:
                d = json.loads(r.read().decode())
            matched = d.get("numberMatched")
            feats = d.get("features", [])
            if isinstance(matched, int) and matched > len(feats):
                return feats, matched
            return feats, None
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as ex:
            if attempt == retries - 1:
                print(f"    tile {w:.3f},{s:.3f} failed: {ex}", file=sys.stderr)
                return [], None
            time.sleep(3 * (attempt + 1))
    return [], None


def fetch_recursive(w, s, e, n, depth=0, max_depth=4):
    """Fetch a tile, splitting into quarters when the server truncates."""
    feats, truncated = wfs_tile(w, s, e, n)
    if truncated and depth < max_depth:
        mx, my = (w + e) / 2, (s + n) / 2
        out = []
        for (a, b, c, d_) in ((w, s, mx, my), (mx, s, e, my),
                              (w, my, mx, n), (mx, my, e, n)):
            out.extend(fetch_recursive(a, b, c, d_, depth + 1, max_depth))
        return out
    return feats


# --------------------------------------------------------------------- tiles
def buildings_in_bbox(w, s, e, n):
    """Centroids of every building in a bbox, in one Overpass call.
    Far cheaper than querying per parcel: one lookup covers a whole tile."""
    q = (f"[out:json][timeout:60];\n"
         f'(way["building"]({s},{w},{n},{e});\n'
         f' relation["building"]({s},{w},{n},{e});\n'
         f' node["building"]({s},{w},{n},{e}););\n'
         f"out center;")
    d = fp.overpass(q, timeout=20)
    if not d:
        return None
    pts = []
    for el in d.get("elements", []):
        if "center" in el:
            pts.append((el["center"]["lat"], el["center"]["lon"]))
        elif "lat" in el:
            pts.append((el["lat"], el["lon"]))
    return pts


GEOCACHE = STATE_DIR / "town_geocode_cache.json"


def geocode_town(name, state, cache, say):
    """Town centre via free OSM Nominatim search. Cached; 1 req/sec."""
    key = f"{name}|{state}"
    if key in cache:
        return cache[key]
    q = urlencode({"q": f"{name}, {state}, Australia", "format": "json", "limit": 1})
    pt = None
    try:
        with urlopen(Request(f"https://nominatim.openstreetmap.org/search?{q}",
                             headers=UA), timeout=30) as r:
            d = json.loads(r.read().decode())
        if d:
            pt = {"lat": float(d[0]["lat"]), "lon": float(d[0]["lon"])}
    except Exception as ex:
        say(f"  could not locate '{name}': {ex}")
    cache[key] = pt
    time.sleep(1.1)
    return pt


def tiles_near_towns(tiles, tile, points, radius_m):
    """Keep only tiles whose centre is within radius of one of the towns."""
    margin = tile * 111000 * 0.75      # tile half-diagonal, so edge tiles count
    keep = []
    for tx, ty in tiles:
        clat, clon = (ty + 0.5) * tile, (tx + 0.5) * tile
        for p in points:
            if fp.haversine(clat, clon, p["lat"], p["lon"]) <= radius_m + margin:
                keep.append((tx, ty))
                break
    return keep


def corridor_tiles(voltages, tol, bbox, tile):
    """Deduped tiles covering the line corridor."""
    fc = json.loads(fp.LINES.read_text(encoding="utf-8"))
    s, w, n, e = bbox
    cells = set()
    for feat in fc.get("features", []):
        v = feat.get("properties", {}).get("voltage_kv")
        if v is None or not any(abs(v - tv) <= tol for tv in voltages):
            continue
        for lon, lat in feat.get("geometry", {}).get("coordinates", []):
            if not (s <= lat <= n and w <= lon <= e):
                continue
            cells.add((int(math.floor(lon / tile)), int(math.floor(lat / tile))))
    return sorted(cells)


# -------------------------------------------------------------------- report
def write_reports(rows, args, stamp):
    OUT_DIR.mkdir(exist_ok=True)
    md = OUT_DIR / f"parcels_{args.state}_{stamp}.md"
    cs = OUT_DIR / f"parcels_{args.state}_{stamp}.csv"
    volt = "/".join(str(int(v)) for v in args.voltages)
    lines = [
        f"# Land parcels near {volt} kV lines - {args.state}",
        "",
        f"_Generated {stamp} UTC from the Vicmap cadastre (free open data)._",
        "",
        f"Criteria: area >= {args.min_land:,.0f} m2, boundary within "
        f"{args.max_distance:.0f} m of a {volt} kV line"
        + (f", <= {args.max_neighbors} buildings within {args.neighbor_radius:.0f} m."
           if args.max_neighbors >= 0 else "."),
        "",
        f"**{len(rows)} parcels** (closest to the line first). These are land parcels, "
        "not listings - most are NOT for sale.",
        "",
        "| # | Area (m2) | Area (ha) | Dist (m) | Neighbours | SPI / Lot-Plan | Map |",
        "|---|-----------|-----------|----------|------------|----------------|-----|",
    ]
    for i, r in enumerate(rows, 1):
        nb = "?" if r["neighbours"] is None else r["neighbours"]
        ident = r["spi"] or (f"Lot {r['lot']} {r['plan']}".strip() if r["lot"] or r["plan"] else "-")
        gmap = f"https://www.google.com/maps/search/?api=1&query={r['lat']:.6f},{r['lon']:.6f}"
        lines.append(f"| {i} | {r['area']:,.0f} | {r['area']/10000:.2f} | {r['dist']:.0f} | "
                     f"{nb} | {ident} | [open]({gmap}) |")
    md.write_text("\n".join(lines), encoding="utf-8")

    with cs.open("w", newline="", encoding="utf-8") as f:
        wcsv = csv.writer(f)
        wcsv.writerow(["rank", "area_m2", "area_ha", "dist_to_line_m", "neighbours",
                       "spi", "lot", "plan", "lga_code", "parcel_pfi",
                       "lat", "lon", "line_voltage_kv", "google_maps"])
        for i, r in enumerate(rows, 1):
            wcsv.writerow([i, f"{r['area']:.0f}", f"{r['area']/10000:.3f}",
                           f"{r['dist']:.0f}",
                           "" if r["neighbours"] is None else r["neighbours"],
                           r["spi"], r["lot"], r["plan"], r["lga"], r["pfi"],
                           f"{r['lat']:.6f}", f"{r['lon']:.6f}", r["line_v"],
                           f"https://www.google.com/maps/search/?api=1&"
                           f"query={r['lat']:.6f},{r['lon']:.6f}"])
    print(f"\nWrote {md}\nWrote {cs}")
    return md.name, cs.name


# ---------------------------------------------------------------------- main
def scan(args, progress=None, segs=None, grid=None):
    """Run the parcel scan. `progress` is an optional callback(str).
    Pass pre-loaded segs/grid to skip re-parsing the line GeoJSON (used by the
    Streamlit app, which caches them across reruns)."""
    def say(m):
        if progress:
            progress(m)      # caller handles its own printing
        else:
            print(m, file=sys.stderr)

    voltages = args.voltages
    bbox = fp.STATE_BBOX[args.state]
    if segs is None or grid is None:
        say(f"Loading {'/'.join(str(int(v)) for v in voltages)} kV lines for {args.state}...")
        segs, grid = fp.load_segments(voltages, args.voltage_tol, bbox)
    say(f"  {len(segs):,} line segments.")
    if not segs:
        raise RuntimeError("No matching line segments.")

    tiles = corridor_tiles(voltages, args.voltage_tol, bbox, args.tile)

    # Optional: restrict the scan to the area around named towns.
    towns = getattr(args, "towns", None)
    if towns:
        cache = json.loads(GEOCACHE.read_text(encoding="utf-8")) if GEOCACHE.exists() else {}
        pts = []
        say(f"Locating {len(towns)} town(s)...")
        for entry in towns:
            nm, st = (entry.split(":", 1) + [args.state])[:2] if ":" in entry \
                else (entry, args.state)
            p = geocode_town(nm.strip(), st.strip(), cache, say)
            if p:
                pts.append(p)
                say(f"  {nm.strip()} -> {p['lat']:.3f}, {p['lon']:.3f}")
        GEOCACHE.parent.mkdir(parents=True, exist_ok=True)
        GEOCACHE.write_text(json.dumps(cache), encoding="utf-8")
        if not pts:
            raise RuntimeError("None of those towns could be located - check the spelling.")
        before = len(tiles)
        tiles = tiles_near_towns(tiles, args.tile, pts, args.town_radius * 1000)
        say(f"  {len(tiles)} tiles within {args.town_radius:.0f} km of those towns "
            f"(out of {before} state-wide).")
        if not tiles:
            raise RuntimeError(
                f"No {'/'.join(str(int(v)) for v in voltages)} kV lines within "
                f"{args.town_radius:.0f} km of those towns. Try a bigger radius.")

    if args.max_tiles:
        tiles = tiles[:args.max_tiles]
    say(f"  {len(tiles):,} tiles to scan (~{args.tile*111:.0f} km each).")

    target = getattr(args, "max_results", 0) or 0
    if target:
        say(f"  Will stop as soon as {target} matching parcels are found.")

    seen, survivors, stop = set(), [], False
    for i, (tx, ty) in enumerate(tiles, 1):
        w, s = tx * args.tile, ty * args.tile
        t0 = time.time()
        feats = fetch_recursive(w, s, w + args.tile, s + args.tile)
        found_before = len(survivors)
        for ft in feats:
            p = ft.get("properties", {}) or {}
            pfi = p.get("parcel_pfi") or p.get("parcel_ufi")
            if pfi in seen:
                continue
            geom = ft.get("geometry")
            if not geom:
                continue
            area = geom_area_m2(geom)
            if area < args.min_land:
                continue
            best = None
            for lat, lon in geom_points(geom, args.step):
                d, props = fp.nearest_line(lat, lon, segs, grid, args.max_distance)
                if d is not None and (best is None or d < best[0]):
                    best = (d, props)
                    if d < 1:
                        break
            if best is None:
                continue
            seen.add(pfi)
            clat, clon = centroid(geom)
            rec = {
                "pfi": pfi, "area": area, "dist": best[0],
                "line_v": (best[1] or {}).get("voltage_kv", ""),
                "spi": p.get("parcel_spi", ""), "lot": p.get("parcel_lot_number", ""),
                "plan": p.get("parcel_plan_number", ""), "lga": p.get("parcel_lga_code", ""),
                "lat": clat, "lon": clon, "neighbours": None,
            }
            survivors.append(rec)
            if target and len(survivors) >= target:
                say(f"  Found the requested {target} parcels - stopping early.")
                stop = True
                break
        if stop:
            break
        # Report every tile: dense areas can take many seconds, and silence
        # makes the program look frozen.
        say(f"  tile {i}/{len(tiles)} - {len(feats)} parcels checked, "
            f"+{len(survivors)-found_before} match ({len(survivors)} total, "
            f"{time.time()-t0:.1f}s)")

    say(f"{len(survivors)} parcels match area + distance.")

    # Neighbours run as a separate, visible phase. Overpass is rate-limited and
    # sometimes very slow, so doing this inline would stall the tile scan with
    # no output and look like a freeze.
    if args.max_neighbors >= 0 and survivors:
        groups = {}
        for r in survivors:
            key = (int(math.floor(r["lon"] / args.tile)),
                   int(math.floor(r["lat"] / args.tile)))
            groups.setdefault(key, []).append(r)
        say(f"Checking neighbours across {len(groups)} area(s) "
            f"(one map lookup each, not one per parcel)...")
        kept, failed = [], 0
        margin = args.neighbor_radius / 111000.0 * 1.2
        for k, ((tx, ty), items) in enumerate(groups.items(), 1):
            w, s = tx * args.tile, ty * args.tile
            pts = buildings_in_bbox(w - margin, s - margin,
                                    w + args.tile + margin, s + args.tile + margin)
            for r in items:
                if pts is None:
                    r["neighbours"] = None
                    failed += 1
                else:
                    r["neighbours"] = sum(
                        1 for blat, blon in pts
                        if fp.haversine(r["lat"], r["lon"], blat, blon)
                        <= args.neighbor_radius)
                if r["neighbours"] is None or r["neighbours"] <= args.max_neighbors:
                    kept.append(r)
            say(f"  area {k}/{len(groups)} - {len(kept)} kept so far")
            time.sleep(1)
        if failed:
            say(f"  note: {failed} could not be checked (map service busy) - kept anyway.")
        survivors = kept

    say(f"{len(survivors)} parcels matched.")
    survivors.sort(key=lambda r: r["dist"])
    return survivors


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--state", default="VIC", choices=sorted(fp.STATE_BBOX),
                    help="Only VIC has cadastre wired up so far.")
    ap.add_argument("--voltages", default="66")
    ap.add_argument("--voltage-tol", type=float, default=0.5)
    ap.add_argument("--min-land", type=float, default=10000.0)
    ap.add_argument("--max-distance", type=float, default=200.0)
    ap.add_argument("--tile", type=float, default=0.02,
                    help="Tile size in degrees (~2.2 km at 0.02). Bigger tiles mean "
                         "fewer requests but dense city tiles then take far longer.")
    ap.add_argument("--step", type=float, default=50.0,
                    help="Boundary sampling step in metres (default 50).")
    ap.add_argument("--max-tiles", type=int, default=0, help="Limit tiles (0 = all).")
    ap.add_argument("--max-results", type=int, default=100,
                    help="Stop once this many parcels are found (default 100, 0 = no limit).")
    ap.add_argument("--towns", default="",
                    help="Comma list of towns to search around, e.g. "
                         "'Gisborne:VIC,Kilmore:VIC'. Empty = the whole state.")
    ap.add_argument("--town-radius", type=float, default=10.0,
                    help="Kilometres around each town to search (default 10).")
    ap.add_argument("--max-neighbors", type=int, default=10)
    ap.add_argument("--neighbor-radius", type=float, default=150.0)
    ap.add_argument("--no-neighbours", dest="max_neighbors", action="store_const",
                    const=-1, help="Skip the neighbour check (much faster).")
    args = ap.parse_args()
    args.voltages = [float(v) for v in args.voltages.split(",") if v.strip()]
    args.towns = [t.strip() for t in args.towns.split(",") if t.strip()]

    if args.state != "VIC":
        sys.exit("Cadastral scan currently supports VIC only (Vicmap open data).")

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M")
    rows = scan(args)
    write_reports(rows, args, stamp)
    print(f"{len(rows)} parcels.")


if __name__ == "__main__":
    main()
