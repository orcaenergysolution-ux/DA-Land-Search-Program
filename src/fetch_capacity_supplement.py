"""
Capacity supplement for DA projects missing MW/MWh data.

Sources (applied in priority order — highest-priority wins):
  1. manual_capacities.json  — hand-curated overrides (highest priority)
  2. WRI Global Power Plant Database (exact normalised-name match only)
  3. OSM Overpass API         (exact normalised-name match only)

Only fills gaps — never overwrites an existing non-None capacity value.
Called from fetch_cer_da.main() after all source merges are done.
"""

from __future__ import annotations
import csv, io, json, re, sys, urllib.parse, urllib.request
from pathlib import Path

ROOT = Path(__file__).parent.parent

# ── helpers ──────────────────────────────────────────────────────────────────

def _norm(s: str | None) -> str:
    """Normalise a project name for fuzzy-free exact matching."""
    s = re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()
    return " ".join(s.split())


def _to_float(x) -> float | None:
    try:
        return float(x) if x else None
    except (TypeError, ValueError):
        return None


# ── Source 1: manual_capacities.json ─────────────────────────────────────────

def _load_manual(path: Path) -> dict[str, dict]:
    """Returns {norm_name: {mw, mwh, location_desc, reason}} from the manual overrides file."""
    if not path.exists():
        return {}
    entries = json.loads(path.read_text(encoding="utf-8"))
    out = {}
    for e in entries:
        key = _norm(e.get("site_name", ""))
        if key:
            out[key] = {
                "mw":           _to_float(e.get("capacity_mw")),
                "mwh":          _to_float(e.get("storage_mwh")),
                "location_desc": e.get("location_desc") or None,
                "reason":       e.get("reason", "manual"),
            }
    return out


# ── Source 2: WRI Global Power Plant Database ─────────────────────────────────

WRI_URL = (
    "https://raw.githubusercontent.com/wri/global-power-plant-database"
    "/master/output_database/global_power_plant_database.csv"
)


def _load_wri() -> dict[str, dict]:
    """Download WRI GPPD and return {norm_name: {mw, lat, lon}} for AUS plants."""
    try:
        req = urllib.request.Request(
            WRI_URL,
            headers={"User-Agent": "AEMO-map-research/1.0"},
        )
        with urllib.request.urlopen(req, timeout=30) as r:
            text = r.read().decode("utf-8", errors="replace")
        reader = csv.DictReader(io.StringIO(text))
        out = {}
        for row in reader:
            if row.get("country") != "AUS":
                continue
            key = _norm(row.get("name", ""))
            cap = _to_float(row.get("capacity_mw"))
            if key and cap:
                out[key] = {
                    "mw":  cap,
                    "mwh": None,
                    "lat": _to_float(row.get("latitude")),
                    "lon": _to_float(row.get("longitude")),
                }
        return out
    except Exception as e:
        print(f"  [capacity-supplement] WRI fetch failed: {e}", file=sys.stderr)
        return {}


# ── Source 3: OpenStreetMap Overpass API ──────────────────────────────────────

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
OVERPASS_QUERY = """
[out:json][timeout:60];
area["ISO3166-1"="AU"]->.au;
(
  nw["power"="plant"]["plant:output:electricity"](area.au);
  nw["power"="plant"]["generator:output:electricity"](area.au);
  nw["power"="plant"]["capacity"](area.au);
);
out tags center qt 1000;
""".strip()


def _load_osm() -> dict[str, dict]:
    """Query Overpass API and return {norm_name: {mw}} for Australian plants."""
    try:
        data_enc = urllib.parse.urlencode({"data": OVERPASS_QUERY}).encode("utf-8")
        req = urllib.request.Request(
            OVERPASS_URL, data=data_enc,
            headers={"User-Agent": "AEMO-map-research/1.0"},
        )
        with urllib.request.urlopen(req, timeout=90) as r:
            result = json.loads(r.read())
        out = {}
        for el in result.get("elements", []):
            tags = el.get("tags", {})
            name = tags.get("name", "").strip()
            if not name:
                continue
            cap_raw = (
                tags.get("plant:output:electricity") or
                tags.get("generator:output:electricity") or
                tags.get("capacity") or ""
            )
            m = re.search(r"([\d.]+)\s*(?:MW)?", cap_raw)
            cap = _to_float(m.group(1)) if m else None
            if "center" in el:
                lat = _to_float(el["center"].get("lat"))
                lon = _to_float(el["center"].get("lon"))
            else:
                lat = _to_float(el.get("lat"))
                lon = _to_float(el.get("lon"))
            key = _norm(name)
            if key and cap:
                out[key] = {"mw": cap, "mwh": None, "lat": lat, "lon": lon}
        return out
    except Exception as e:
        print(f"  [capacity-supplement] OSM fetch failed: {e}", file=sys.stderr)
        return {}


# ── Main entry point ──────────────────────────────────────────────────────────

def apply_capacity_supplement(projects: list[dict], dry_run: bool = False) -> int:
    """
    Fill missing capacity_mw / storage_mwh on projects.
    Returns the number of projects updated.
    """
    manual_path = ROOT / "data" / "inputs" / "manual_capacities.json"

    print("\n=== Capacity supplement ===")

    # Build lookup tables (priority: manual > WRI > OSM)
    print("  Loading manual overrides...", end=" ", flush=True)
    manual = _load_manual(manual_path)
    print(f"{len(manual)} entries")

    print("  Loading WRI GPPD...", end=" ", flush=True)
    wri = _load_wri()
    print(f"{len(wri)} AUS plants")

    print("  Loading OSM Overpass...", end=" ", flush=True)
    osm = _load_osm()
    print(f"{len(osm)} AUS plants")

    # Merged lookup: manual wins, then WRI, then OSM
    lookup: dict[str, dict] = {}
    for src_dict, label in [(osm, "OSM"), (wri, "WRI"), (manual, "manual")]:
        for key, val in src_dict.items():
            lookup[key] = {**val, "_label": label}

    # Apply to projects
    updated = 0
    for p in projects:
        missing_mw   = p.get("capacity_mw") is None
        missing_mwh  = p.get("storage_mwh") is None
        missing_loc  = not p.get("location_desc")
        if not (missing_mw or missing_mwh or missing_loc):
            continue

        key = _norm(p.get("site_name", ""))
        hit = lookup.get(key)
        if not hit:
            continue

        changed = False
        if missing_mw and hit.get("mw") is not None:
            if not dry_run:
                p["capacity_mw"] = hit["mw"]
            changed = True
        if missing_mwh and hit.get("mwh") is not None:
            if not dry_run:
                p["storage_mwh"] = hit["mwh"]
            changed = True
        # Also fill location_desc if blank and manual entry has one
        if not p.get("location_desc") and hit.get("location_desc"):
            if not dry_run:
                p["location_desc"] = hit["location_desc"]
            changed = True

        if changed:
            updated += 1
            src_label = p.get("source", "")
            print(f"    [{hit['_label']}] {p['site_name'][:55]:55s} "
                  f"mw={hit.get('mw')} mwh={hit.get('mwh')}  ({src_label})")

    print(f"  Supplement filled capacity for {updated} projects")
    return updated
