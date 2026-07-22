"""Find land-for-sale listings close to high-voltage (66 kV) transmission lines.

Pipeline:
  1. Load 66 kV (or chosen voltage) lines from the existing transmission GeoJSON.
  2. Scrape Domain.com.au listings for a location via the Apify "Domain.com.au
     Real Estate Scraper" actor (no paid Domain API needed).
  3. Keep listings that are (a) within --max-distance of a target line and
     (b) >= --min-land square metres.
  4. Use the OpenStreetMap Overpass API to count nearby buildings ("neighbours")
     and keep only relatively isolated blocks.
  5. Sort cheapest -> most expensive and write a Markdown + CSV report.

Everything is configurable from the CLI. Pure stdlib, consistent with src/.

Setup (one-time):
  Get an Apify API token from https://console.apify.com/account/integrations
  then set it (PowerShell):
      $env:APIFY_TOKEN="apify_api_xxx"
  ...or pass --token on the command line.

COST NOTE: every run spends Apify credit. Keep --max-listings modest and target
specific suburbs with --locations to stay within budget. The raw scraped data is
saved to outputs/apify_raw_*.json so you never need to re-run just to inspect it.

Example:
    python src/find_properties.py --state VIC --locations "Bacchus Marsh:VIC,Gisborne:VIC" \
        --min-land 10000 --max-distance 200 --max-listings 100
"""
from __future__ import annotations
import argparse
import csv
import json
import math
import os
import re
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import quote
from urllib.error import HTTPError, URLError

ROOT = Path(__file__).parent.parent
LINES = ROOT / "data" / "intermediate" / "transmission_lines.geojson"
OUT_DIR = ROOT / "outputs"

APIFY_ACTOR = "2nxVAaCApCvbhJjoF"   # Domain.com.au Real Estate Scraper
APIFY_RUN_URL = f"https://api.apify.com/v2/acts/{APIFY_ACTOR}/run-sync-get-dataset-items"

OVERPASS_ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
]

# (south, west, north, east) - keeps only relevant line segments per state.
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


# --------------------------------------------------------------------------- geo
def haversine(lat1, lon1, lat2, lon2):
    r = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(min(1.0, math.sqrt(a)))


def point_seg_dist(plat, plon, alat, alon, blat, blon):
    """Distance (m) from point P to segment A-B via a local planar projection."""
    mx = 111320.0 * math.cos(math.radians(plat))   # metres per degree lon
    my = 110540.0                                   # metres per degree lat

    def xy(lat, lon):
        return ((lon - plon) * mx, (lat - plat) * my)

    px, py = 0.0, 0.0
    ax, ay = xy(alat, alon)
    bx, by = xy(blat, blon)
    dx, dy = bx - ax, by - ay
    seg2 = dx * dx + dy * dy
    if seg2 == 0.0:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / seg2))
    cx, cy = ax + t * dx, ay + t * dy
    return math.hypot(px - cx, py - cy)


# ----------------------------------------------------------------- line loading
def load_segments(voltages, tol, bbox):
    fc = json.loads(LINES.read_text(encoding="utf-8"))
    s, w, n, e = bbox
    segs = []
    grid = defaultdict(list)

    def cell(lat, lon):
        return (int(lat / 0.05), int(lon / 0.05))

    for feat in fc.get("features", []):
        v = feat.get("properties", {}).get("voltage_kv")
        if v is None or not any(abs(v - tv) <= tol for tv in voltages):
            continue
        coords = feat.get("geometry", {}).get("coordinates", [])
        props = feat.get("properties", {})
        for (lon1, lat1), (lon2, lat2) in zip(coords, coords[1:]):
            if max(lat1, lat2) < s - 0.1 or min(lat1, lat2) > n + 0.1:
                continue
            if max(lon1, lon2) < w - 0.1 or min(lon1, lon2) > e + 0.1:
                continue
            idx = len(segs)
            segs.append((lat1, lon1, lat2, lon2, props))
            for la, lo in ((lat1, lon1), (lat2, lon2)):
                grid[cell(la, lo)].append(idx)
    return segs, grid


def nearest_line(lat, lon, segs, grid, max_dist):
    c_lat, c_lon = int(lat / 0.05), int(lon / 0.05)
    seen = set()
    best, best_props = None, None
    for dla in (-1, 0, 1):
        for dlo in (-1, 0, 1):
            for idx in grid.get((c_lat + dla, c_lon + dlo), ()):
                if idx in seen:
                    continue
                seen.add(idx)
                a_lat, a_lon, b_lat, b_lon, props = segs[idx]
                d = point_seg_dist(lat, lon, a_lat, a_lon, b_lat, b_lon)
                if best is None or d < best:
                    best, best_props = d, props
    if best is not None and best <= max_dist:
        return best, best_props
    return None, None


# ------------------------------------------------------------------- overpass
def overpass(query, timeout=25):
    """Query Overpass, trying each mirror once. Fails fast: these are bulk
    lookups, so a slow mirror must not stall the whole run (returns None)."""
    body = "data=" + quote(query)
    for ep in OVERPASS_ENDPOINTS:
        try:
            req = Request(ep, data=body.encode("utf-8"), method="POST",
                          headers={"User-Agent": "nem-property-finder/0.1"})
            with urlopen(req, timeout=timeout) as r:
                return json.loads(r.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError) as e:
            print(f"  overpass {ep} -> {e}", file=sys.stderr)
            time.sleep(1)
    return None


def neighbour_count(lat, lon, radius):
    q = f"""[out:json][timeout:60];
(way["building"](around:{radius},{lat},{lon});
 relation["building"](around:{radius},{lat},{lon}););
out count;"""
    data = overpass(q)
    if not data:
        return None
    for el in data.get("elements", []):
        if el.get("type") == "count":
            tags = el.get("tags", {})
            return int(tags.get("total", tags.get("ways", 0)))
    return 0


# --------------------------------------------------------------------- apify
def _apify_get(url):
    with urlopen(Request(url, headers={"Content-Type": "application/json"}),
                 timeout=120) as r:
        return json.loads(r.read().decode())


def apify_run(token, actor_input):
    """Start the actor asynchronously, poll until it finishes, then return its
    dataset items. Avoids the ~300 s cap of the sync endpoint so large multi-town
    scrapes complete reliably."""
    start = (f"https://api.apify.com/v2/acts/{APIFY_ACTOR}/runs?token={token}")
    req = Request(start, data=json.dumps(actor_input).encode(), method="POST",
                  headers={"Content-Type": "application/json"})
    try:
        with urlopen(req, timeout=60) as r:
            run = json.loads(r.read().decode())["data"]
    except HTTPError as e:
        sys.exit(f"ERROR from Apify: {e} {e.read().decode(errors='ignore')}")
    except URLError as e:
        sys.exit(f"ERROR contacting Apify: {e}")

    run_id, ds = run["id"], run["defaultDatasetId"]
    print(f"  run {run_id} started; polling ...", file=sys.stderr)
    while True:
        time.sleep(10)
        st = _apify_get(f"https://api.apify.com/v2/actor-runs/{run_id}?token={token}"
                        )["data"]["status"]
        if st in ("SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"):
            print(f"  run {st}", file=sys.stderr)
            break
    if st != "SUCCEEDED":
        sys.exit(f"Apify run ended with status {st}.")
    return _apify_get(f"https://api.apify.com/v2/datasets/{ds}/items"
                      f"?token={token}&format=json&clean=true")


def build_input(args, locations):
    body = {
        "mode": "location",
        "locations": locations,
        "listingType": args.listing_type,
        "sortBy": "list-date",
        "dateRange": args.date_range,
        "includeSurrounding": args.include_surrounding,
        "includeNearbySchools": False,
        "includePriceHistory": False,
        "includePcaInsights": False,
        "maxListings": args.max_listings,
        "maxPages": args.max_pages,
        "proxyConfiguration": {
            "useApifyProxy": True,
            "apifyProxyGroups": ["RESIDENTIAL"],
            "apifyProxyCountry": "AU",
        },
    }
    # Scrape-side filters cut Apify credit by skipping irrelevant listings.
    if args.property_types:
        body["propertyTypes"] = args.property_types       # e.g. ["land","rural"]
    if args.min_price:
        body["priceMin"] = args.min_price
    if args.max_price:
        body["priceMax"] = args.max_price
    return body


# ------------------------------------------------------------- field extraction
# Area mentions in free text: "1,100m2", "1,100m²", mojibake "1,100m<U+FFFD>",
# "2.5 ha", "5 acres", "4000 sqm", "1.2 hectares".
AREA_RE = re.compile(
    r"(\d[\d,]*(?:\.\d+)?)\s*"
    r"(hectares?|ha|acres?|ac|m2|m²|m�|sqm|sq\.?\s*m|square\s*met(?:re|er)s?)",
    re.I,
)


def price_low(display):
    """Lower numeric price from a Domain price.display string; None if undisclosed.
    For ranges ('$600,000 - $660,000') the lower bound is used for sorting."""
    if not isinstance(display, str):
        return None
    m = re.search(r"\$\s*([\d,]+(?:\.\d+)?)\s*([mMkK]?)", display)
    if not m:
        return None
    num = float(m.group(1).replace(",", ""))
    suf = m.group(2).lower()
    if suf == "m":
        num *= 1_000_000
    elif suf == "k":
        num *= 1_000
    return num if num > 1000 else None   # ignore stray small numbers


def land_from_text(*texts):
    """Largest land area (m2) mentioned in the given texts, or None.
    Land size is not a structured field in this scraper - it only appears in
    description/headline prose, so this is a best-effort parse."""
    best = None
    for t in texts:
        if not t:
            continue
        for num, unit in AREA_RE.findall(t):
            val = float(num.replace(",", ""))
            u = unit.lower()
            if u.startswith("hect") or u == "ha":
                val *= 10000            # hectares -> m2
            elif u.startswith("ac"):
                val *= 4046.86          # acres -> m2
            # else already m2/sqm
            if best is None or val > best:
                best = val
    return best


def land_sqm(listing):
    """Land area in m2. Prefers the structured landSize/landSizeUnit fields the
    scraper provides (present on most listings); falls back to a text parse."""
    raw = listing.get("landSize")
    if raw not in (None, "", 0):
        try:
            val = float(raw)
        except (TypeError, ValueError):
            val = None
        if val:
            unit = (listing.get("landSizeUnit") or "m2").lower()
            if unit in ("ha", "hectare", "hectares"):
                val *= 10000
            elif unit in ("ac", "acre", "acres"):
                val *= 4046.86
            return val
    return land_from_text(listing.get("description"), listing.get("headline"))


def slugify(text):
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", (text or "").lower())).strip("-")


def extract(listing):
    coords = listing.get("coordinates") or {}
    addr = listing.get("address") or {}
    lat, lon = coords.get("latitude"), coords.get("longitude")
    full_addr = addr.get("full") or addr.get("street") or ""
    pid = listing.get("propertyId") or ""
    # Domain canonical URL = slug of the full address + the property id
    url = f"https://www.domain.com.au/{slugify(full_addr)}-{pid}" if pid else ""
    return {
        "id": pid,
        "address": addr.get("street") or full_addr,
        "suburb": addr.get("suburb", ""),
        "lat": float(lat) if lat is not None else None,
        "lon": float(lon) if lon is not None else None,
        "land": land_sqm(listing),
        "type": listing.get("propertyType", ""),
        "price": price_low((listing.get("price") or {}).get("display")),
        "display_price": (listing.get("price") or {}).get("display", ""),
        "url": url,
    }


# ------------------------------------------------------------------------ report
def write_reports(rows, args, stamp):
    OUT_DIR.mkdir(exist_ok=True)
    md = OUT_DIR / f"property_candidates_{args.state}_{stamp}.md"
    csv_path = OUT_DIR / f"property_candidates_{args.state}_{stamp}.csv"

    lines = [
        f"# Land near {'/'.join(str(int(v)) for v in args.voltages)} kV lines - {args.state}",
        "",
        f"_Generated {stamp} UTC._  Criteria: land >= {args.min_land:,.0f} m2, "
        f"within {args.max_distance:.0f} m of a target line, "
        f"<= {args.max_neighbors} buildings within {args.neighbor_radius:.0f} m.",
        "",
        f"**{len(rows)} matching listings** (cheapest first).",
        "",
        "| # | Price | Land (m2) | Dist to line (m) | Neighbours | Type | Address | Link |",
        "|---|-------|-----------|------------------|-----------|------|---------|------|",
    ]
    for i, r in enumerate(rows, 1):
        price = f"${r['price']:,.0f}" if r["price"] else (r["display_price"] or "Undisclosed")
        nb = "?" if r["neighbours"] is None else r["neighbours"]
        land = f"{r['land']:,.0f}" if r["land"] is not None else "?"
        lines.append(
            f"| {i} | {price} | {land} | {r['dist']:.0f} | {nb} | "
            f"{r['type']} | {r['address']}, {r['suburb']} | [view]({r['url']}) |"
        )
    md.write_text("\n".join(lines), encoding="utf-8")

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        wcsv = csv.writer(f)
        wcsv.writerow(["rank", "price", "display_price", "land_m2", "dist_to_line_m",
                       "neighbours", "type", "address", "suburb", "lat", "lon",
                       "line_voltage_kv", "line_name", "url"])
        for i, r in enumerate(rows, 1):
            wcsv.writerow([i, r["price"] or "", r["display_price"],
                           "" if r["land"] is None else f"{r['land']:.0f}",
                           f"{r['dist']:.0f}", "" if r["neighbours"] is None else r["neighbours"],
                           r["type"], r["address"], r["suburb"], r["lat"], r["lon"],
                           r["line_v"], r["line_name"], r["url"]])
    print(f"\nWrote {md}\nWrote {csv_path}")


# --------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--state", default="VIC", choices=sorted(STATE_BBOX),
                    help="State for line matching + default scrape location (default VIC).")
    ap.add_argument("--locations", default="",
                    help="Comma list of 'Suburb:STATE' to scrape, e.g. 'Gisborne:VIC,Sunbury:VIC'. "
                         "If omitted, scrapes the whole --state (can be costly).")
    ap.add_argument("--locations-file", default="",
                    help="Path to a file with one 'Suburb:STATE' per line (e.g. the output "
                         "of lines_to_suburbs.py). Merged with --locations.")
    ap.add_argument("--min-land", type=float, default=10000.0,
                    help="Minimum land area in square metres (default 10000).")
    ap.add_argument("--include-unknown-land", action="store_true",
                    help="Keep listings whose land size could not be parsed from text "
                         "(shown as '?'). Off by default.")
    ap.add_argument("--max-distance", type=float, default=200.0,
                    help="Max distance in metres from a target line (default 200).")
    ap.add_argument("--voltages", default="66",
                    help="Comma list of line voltages (kV) to target (default 66).")
    ap.add_argument("--voltage-tol", type=float, default=0.5,
                    help="Tolerance (kV) when matching line voltage (default 0.5).")
    ap.add_argument("--max-neighbors", type=int, default=10,
                    help="Max nearby buildings allowed (default 10). -1 skips the check.")
    ap.add_argument("--neighbor-radius", type=float, default=150.0,
                    help="Radius (m) for counting neighbouring buildings (default 150).")
    ap.add_argument("--property-types", default="land,rural",
                    help="Comma list of scrape-side property types to cut credit use. "
                         "Valid: house,apartment,townhouse,villa,land,rural,commercial,other. "
                         "Default 'land,rural'. Add 'house' to include acreage-with-a-dwelling. "
                         "Use '' for no filter (most expensive).")
    ap.add_argument("--min-price", type=int, default=None, help="Apify priceMin filter.")
    ap.add_argument("--max-price", type=int, default=None, help="Apify priceMax filter.")
    ap.add_argument("--listing-type", default="buy", help="Apify listingType (default buy).")
    ap.add_argument("--date-range", default="6months", help="Apify dateRange (default 6months).")
    ap.add_argument("--no-surrounding", dest="include_surrounding", action="store_false",
                    help="Do NOT include surrounding suburbs. Recommended with a dense "
                         "--locations-file to avoid duplicate listings and wasted credit.")
    ap.set_defaults(include_surrounding=True)
    ap.add_argument("--max-listings", type=int, default=100,
                    help="Apify maxListings cap - controls cost (default 100).")
    ap.add_argument("--max-pages", type=int, default=0, help="Apify maxPages (0 = unlimited).")
    ap.add_argument("--token", default=os.environ.get("APIFY_TOKEN", ""),
                    help="Apify API token (or set APIFY_TOKEN env var).")
    ap.add_argument("--from-raw", default="",
                    help="Reprocess a saved apify_raw_*.json instead of scraping. "
                         "Free - lets you re-tune --min-land/--max-distance/neighbours offline.")
    args = ap.parse_args()

    if not args.token and not args.from_raw:
        sys.exit("ERROR: provide --token or set APIFY_TOKEN (see module docstring).")

    args.voltages = [float(v) for v in args.voltages.split(",") if v.strip()]
    args.property_types = [t.strip() for t in args.property_types.split(",") if t.strip()]
    bbox = STATE_BBOX[args.state]

    # build scrape locations from --locations and/or --locations-file
    raw_locs = [p.strip() for p in args.locations.split(",")]
    if args.locations_file:
        for ln in Path(args.locations_file).read_text(encoding="utf-8").splitlines():
            ln = ln.strip()
            if ln and not ln.startswith("#"):
                raw_locs.append(ln)
    locations, seen_loc = [], set()
    for part in raw_locs:
        if not part or part in seen_loc:
            continue
        seen_loc.add(part)
        if ":" in part:
            sub, st = part.split(":", 1)
            locations.append({"suburb": sub.strip(), "state": st.strip()})
        else:
            locations.append({"suburb": part, "state": args.state})
    if not locations:
        locations = [{"state": args.state}]
        print(f"WARNING: scraping all of {args.state} (no locations given). "
              f"Capped at --max-listings={args.max_listings} to limit cost.", file=sys.stderr)
    else:
        print(f"{len(locations)} locations to scrape.", file=sys.stderr)

    print(f"Loading {args.voltages} kV line segments for {args.state} ...", file=sys.stderr)
    segs, grid = load_segments(args.voltages, args.voltage_tol, bbox)
    print(f"  {len(segs)} segments", file=sys.stderr)
    if not segs:
        sys.exit("No matching line segments - check --voltages / the GeoJSON.")

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M")
    OUT_DIR.mkdir(exist_ok=True)
    if args.from_raw:
        items = json.loads(Path(args.from_raw).read_text(encoding="utf-8"))
        print(f"  reprocessing {len(items)} saved listings from {args.from_raw}",
              file=sys.stderr)
    else:
        print(f"Scraping Domain via Apify (maxListings={args.max_listings}) ...",
              file=sys.stderr)
        items = apify_run(args.token, build_input(args, locations))
        raw_path = OUT_DIR / f"apify_raw_{args.state}_{stamp}.json"
        raw_path.write_text(json.dumps(items, indent=2), encoding="utf-8")
        print(f"  {len(items)} listings scraped -> {raw_path}", file=sys.stderr)

    seen_ids = set()
    near = []
    skipped_no_geo = skipped_small = 0
    for listing in items:
        r = extract(listing)
        if r["id"] in seen_ids:
            continue
        seen_ids.add(r["id"])
        if r["lat"] is None or r["lon"] is None:
            skipped_no_geo += 1
            continue
        if r["land"] is None:
            if not args.include_unknown_land:
                skipped_small += 1
                continue
        elif r["land"] < args.min_land:
            skipped_small += 1
            continue
        dist, props = nearest_line(r["lat"], r["lon"], segs, grid, args.max_distance)
        if dist is None:
            continue
        r["dist"] = dist
        r["line_v"] = (props or {}).get("voltage_kv", "")
        r["line_name"] = (props or {}).get("name", "")
        near.append(r)

    print(f"\n{len(near)} pass land+distance "
          f"(skipped {skipped_no_geo} without coords, {skipped_small} too small).",
          file=sys.stderr)

    rows = []
    for r in near:
        if args.max_neighbors < 0:
            r["neighbours"] = None
        else:
            r["neighbours"] = neighbour_count(r["lat"], r["lon"], args.neighbor_radius)
            time.sleep(1)
            if r["neighbours"] is not None and r["neighbours"] > args.max_neighbors:
                continue
        rows.append(r)

    rows.sort(key=lambda r: (r["price"] is None, r["price"] or 0.0))
    write_reports(rows, args, stamp)
    print(f"{len(rows)} final candidates.")


if __name__ == "__main__":
    main()
