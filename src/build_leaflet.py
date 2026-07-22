"""
Build a standalone Leaflet HTML map with:
  - Filter sidebar (stage, state, technology, capacity range, search)
  - AEMO PDF underlays as toggleable raster layers (per state)
  - AEMO-style colour legend
  - Project markers sized by capacity, coloured by stage

Inputs (run order):
  build_map.py            -> projects.json
  render_aemo_overlays.py -> aemo_overlays.json + assets/{state}.png
  geocode.py              -> updates projects.json with real lat/lon

Output:
  nem_map.html  (self-contained except for Leaflet CDN + assets/*.png paths)
"""

from __future__ import annotations
import base64
import json
import math
from pathlib import Path

ROOT = Path(__file__).parent.parent
INTERMEDIATE = ROOT / "data" / "intermediate"
OUTPUTS = ROOT / "outputs"
OUTPUTS.mkdir(parents=True, exist_ok=True)

STAGE_COLOUR = {
    "Existing":      "#AFDEFF",   # blue        — operational
    "Retiring":      "#03529C",   # dark blue   — operating but closure announced
    "Commissioning": "#E879F9",   # fuchsia     — final testing before operation
    "Committed":     "#FF6BAB",   # pink        — under construction / financially committed
    "Anticipated":   "#D0EF5E",   # lime        — pre-registration
    "Application":   "#FDB878",   # orange      — application
    "Enquiry":       "#FFEF74",   # yellow      — enquiry
    "DA Approved":   "#4ADE80",   # green       — planning approved
    "DA Submitted":  "#A78BFA",   # purple      — planning under assessment
    "Expired":       "#2A3851",   # dark blue   — DA lapsed / currency expired
    "Withdrawn":     "#1c1c1c",   # dark        — withdrawn
    "Unknown":       "#8b8b8b",   # grey        — unknown
}
STAGE_ORDER = ["Existing", "Retiring", "Commissioning", "Committed", "Anticipated", "Application", "Enquiry", "DA Approved", "DA Submitted", "Expired", "Withdrawn", "Unknown"]
STATES = ["NSW", "VIC", "QLD", "SA", "TAS"]

# ── Proximity helpers (computed at build time, embedded in project data) ──────

def _pt_to_seg_km(plat: float, plon: float,
                  alat: float, alon: float,
                  blat: float, blon: float) -> float:
    """Minimum distance (km) from point P to line segment A→B.
    Uses equirectangular projection — accurate to <1% for segments <100 km."""
    cos_lat = math.cos(math.radians((alat + blat) / 2))
    km_per_deg_lat = 111.32
    km_per_deg_lon = 111.32 * cos_lat
    ax, ay = alon * km_per_deg_lon, alat * km_per_deg_lat
    bx, by = blon * km_per_deg_lon, blat * km_per_deg_lat
    px, py = plon * km_per_deg_lon, plat * km_per_deg_lat
    dx, dy = bx - ax, by - ay
    len2 = dx * dx + dy * dy
    if len2 == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / len2))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def _build_sub_list(substations_fc: dict) -> list[tuple]:
    """Return [(lat, lon, name, voltage_kv), …] for all substation points."""
    out = []
    for f in substations_fc.get("features", []):
        geom = f.get("geometry") or {}
        if geom.get("type") != "Point":
            continue
        lon, lat = geom["coordinates"][:2]
        p = f.get("properties") or {}
        out.append((lat, lon, p.get("name") or "", p.get("voltage_kv") or 0))
    return out


def _build_sub_grid(sub_list: list, cell: float = 0.5) -> dict:
    """Grid index of substations for fast nearest-neighbour lookup.
    cell=0.5° ≈ 50 km; searching ±1 cell covers ~150 km radius."""
    grid: dict[tuple, list] = {}
    for i, (lat, lon, *_) in enumerate(sub_list):
        key = (int(lat / cell), int(lon / cell))
        grid.setdefault(key, []).append(i)
    return grid


def _nearest_sub(lat: float, lon: float,
                 sub_list: list, sub_grid: dict,
                 cell: float = 0.5, max_km: float = 60.0) -> tuple | None:
    """Return the (lat, lon, name, kv) entry of the nearest substation
    within max_km, or None if none found."""
    row, col = int(lat / cell), int(lon / cell)
    search = max(1, int(max_km / (cell * 111.32)) + 1)
    best_d, best_idx = float("inf"), -1
    cos_lat = math.cos(math.radians(lat))
    for dr in range(-search, search + 1):
        for dc in range(-search, search + 1):
            for i in sub_grid.get((row + dr, col + dc), []):
                slat, slon = sub_list[i][:2]
                d = math.hypot((slat - lat) * 111.32,
                               (slon - lon) * 111.32 * cos_lat)
                if d < best_d:
                    best_d, best_idx = d, i
    return sub_list[best_idx] if best_idx >= 0 and best_d <= max_km else None


def _build_tx_grid(transmission_fc: dict, sub_list: list,
                   cell: float = 0.05) -> tuple[dict, list, list]:
    """Spatial grid index of transmission line vertices.
    Also derives endpoint-substation labels for unnamed features.

    Returns:
      grid       : (row,col) -> set of feature indices
      features   : list of GeoJSON feature dicts
      tx_names   : parallel list of display names (OSM name/ref, or
                   'SubA – SubB' inferred from endpoints, or '')
    """
    features = transmission_fc.get("features", [])
    grid: dict[tuple, set] = {}
    for fi, f in enumerate(features):
        for lon, lat in (f.get("geometry") or {}).get("coordinates", []):
            key = (int(lat / cell), int(lon / cell))
            grid.setdefault(key, set()).add(fi)

    # Pre-compute display names; derive endpoint-substation label for unnamed ways
    sub_grid = _build_sub_grid(sub_list)
    tx_names: list[str] = []
    for f in features:
        props = f.get("properties") or {}
        name = (props.get("n") or "").strip()
        if name:
            tx_names.append(name)
            continue
        # Unnamed: infer from nearest substation at each LineString endpoint
        coords = (f.get("geometry") or {}).get("coordinates", [])
        if len(coords) < 2:
            tx_names.append("")
            continue
        s_lon, s_lat = coords[0]
        e_lon, e_lat = coords[-1]
        s_sub = _nearest_sub(s_lat, s_lon, sub_list, sub_grid)
        e_sub = _nearest_sub(e_lat, e_lon, sub_list, sub_grid)
        s_name = (s_sub[2] or "").strip() if s_sub else ""
        e_name = (e_sub[2] or "").strip() if e_sub else ""
        if s_name and e_name and s_name != e_name:
            tx_names.append(f"{s_name} – {e_name}")
        elif s_name:
            tx_names.append(f"near {s_name}")
        elif e_name:
            tx_names.append(f"near {e_name}")
        else:
            tx_names.append("")
    return grid, features, tx_names


def nearby_substations(lat: float, lon: float,
                       sub_list: list, radius_km: float = 2.0) -> str:
    """Semicolon-separated list of substations within radius_km of (lat,lon).
    Format: 'Name (voltage kV, dist km)' sorted by distance. Empty if none."""
    hits = []
    dlat = radius_km / 111.32 + 0.01
    dlon = radius_km / (111.32 * math.cos(math.radians(lat))) + 0.01
    for slat, slon, name, kv in sub_list:
        if abs(slat - lat) > dlat or abs(slon - lon) > dlon:
            continue
        d = math.hypot((slat - lat) * 111.32,
                       (slon - lon) * 111.32 * math.cos(math.radians(lat)))
        if d <= radius_km:
            hits.append((d, name, kv))
    hits.sort()
    parts = []
    for d, name, kv in hits:
        kv_s = f"{int(kv)} kV" if kv else "? kV"
        parts.append(f"{name} ({kv_s}, {d:.1f} km)" if name else f"({kv_s}, {d:.1f} km)")
    return "; ".join(parts)


def nearby_tx_lines(lat: float, lon: float,
                    tx_grid: dict, tx_features: list, tx_names: list,
                    radius_km: float = 5.0, cell: float = 0.05) -> str:
    """Semicolon-separated list of transmission lines within radius_km.
    Uses OSM name/ref when available; falls back to 'SubA – SubB' derived
    from the nearest substation at each OSM way endpoint for unnamed lines.
    Groups by (voltage, display_name) so distinct lines are listed separately.
    Format: 'voltage kV – Name (min dist km)' sorted by distance."""
    row = int(lat / cell)
    col = int(lon / cell)
    search = max(1, int(radius_km / (cell * 111.32)) + 2)
    candidates: set[int] = set()
    for dr in range(-search, search + 1):
        for dc in range(-search, search + 1):
            key = (row + dr, col + dc)
            if key in tx_grid:
                candidates |= tx_grid[key]
    # min distance per (voltage, display_name) pair
    line_dist: dict[tuple, float] = {}
    for fi in candidates:
        f = tx_features[fi]
        kv   = (f.get("properties") or {}).get("v") or 0
        name = tx_names[fi]          # OSM name/ref, or derived "SubA – SubB", or ""
        key  = (kv, name)
        coords = f["geometry"]["coordinates"]
        for i in range(len(coords) - 1):
            alon, alat = coords[i]
            blon, blat = coords[i + 1]
            d = _pt_to_seg_km(lat, lon, alat, alon, blat, blon)
            if d < line_dist.get(key, float("inf")):
                line_dist[key] = d
    hits = [(d, kv, name) for (kv, name), d in line_dist.items() if d <= radius_km]
    hits.sort()
    # When a named/derived line exists at a voltage, suppress bare voltage-only
    # entries and vague "near SubX" entries at the same voltage
    # (OSM fragments mean multiple ways share the same physical line)
    authoritative = {kv for _, kv, nm in hits if nm and not nm.startswith("near ")}
    parts = []
    for d, kv, name in hits:
        if (not name or name.startswith("near ")) and kv in authoritative:
            continue
        kv_s = f"{int(kv)} kV" if kv else "? kV"
        label = f"{kv_s} – {name}" if name else kv_s
        parts.append(f"{label} ({d:.1f} km)")
    return "; ".join(parts)


def main():
    projects = json.loads((INTERMEDIATE / "projects.json").read_text(encoding="utf-8"))
    # prefer slim ≥132 kV version if present (much smaller)
    tx_slim = INTERMEDIATE / "transmission_lines.slim.geojson"
    tx_full = INTERMEDIATE / "transmission_lines.geojson"
    tx_path = tx_slim if tx_slim.exists() else tx_full
    transmission = json.loads(tx_path.read_text(encoding="utf-8")) if tx_path.exists() else {"type":"FeatureCollection","features":[]}
    sub_path = INTERMEDIATE / "substations.geojson"
    substations = json.loads(sub_path.read_text(encoding="utf-8")) if sub_path.exists() else {"type":"FeatureCollection","features":[]}
    rez_path = INTERMEDIATE / "rez.geojson"
    rez = json.loads(rez_path.read_text(encoding="utf-8")) if rez_path.exists() else {"type":"FeatureCollection","features":[]}
    manual_tx_path = INTERMEDIATE / "manual_tx_lines.geojson"
    manual_tx = json.loads(manual_tx_path.read_text(encoding="utf-8")) if manual_tx_path.exists() else {"type":"FeatureCollection","features":[]}

    # collect technologies for filter
    techs = sorted({(p.get("technology") or "Other").strip() or "Other" for p in projects})

    # ── Pre-compute proximity data (substations ≤2 km, TX lines ≤5 km) ──────
    print("Building proximity index ...")
    sub_list = _build_sub_list(substations)
    tx_grid, tx_features, tx_names = _build_tx_grid(transmission, sub_list)
    print(f"  {len(sub_list)} substations, {len(tx_features)} TX line features indexed")

    # compress projects to needed fields to keep HTML small
    slim = []
    null_slim = []   # projects with no location — exported for user to fix
    for p in projects:
        if p.get("lat") is None or p.get("lon") is None:
            null_slim.append({
                "n": p.get("site_name", ""),
                "s": p.get("stage", "Unknown"),
                "r": p.get("region", ""),
                "st": p.get("state", ""),
                "t": (p.get("technology") or "Other").strip() or "Other",
                "f": p.get("fuel", ""),
                "o": p.get("owner", ""),
                "c": p.get("capacity_mw") or 0,
                "mwh": p.get("storage_mwh"),
                "loc": p.get("location_desc", ""),
                "src": p.get("source", ""),
                "aemo": bool(p.get("on_aemo_map")),
            })
            continue
        slim.append({
            "n": p.get("site_name", ""),
            "s": p.get("stage", "Unknown"),
            "r": p.get("region", ""),
            "st": p.get("state", ""),
            "t": (p.get("technology") or "Other").strip() or "Other",
            "f": p.get("fuel", ""),
            "o": p.get("owner", ""),
            "c": p.get("capacity_mw") or 0,
            "mwh": p.get("storage_mwh"),
            "loc": p.get("location_desc", ""),
            "src": p.get("source", ""),
            "aemo": bool(p.get("on_aemo_map")),
            "g": p.get("geocode_source") or "",   # "GA", "Nominatim", or ""
            "gd": p.get("geocode_display", ""),   # address label for manual pins
            "lat": p["lat"], "lon": p["lon"],
            "sub2": nearby_substations(p["lat"], p["lon"], sub_list, radius_km=5.0),
            "tx5":  nearby_tx_lines(p["lat"], p["lon"], tx_grid, tx_features, tx_names, radius_km=5.0),
        })

    cap_max = max((p["c"] for p in slim if p["c"]), default=1000)

    # GA station names already represented as project markers — used to hide
    # duplicates in the GA featureLayer so the same station doesn't appear twice.
    ga_shown = sorted({
        p["geocode_display"]
        for p in projects
        if p.get("geocode_source") == "GA" and p.get("geocode_display")
    })

    # Embed technology icons as base64 data URIs → single self-contained HTML file
    img_dir = ROOT / "data" / "image"
    img_data = {}
    if img_dir.exists():
        for img_path in sorted(img_dir.glob("*.png")):
            b64 = base64.b64encode(img_path.read_bytes()).decode("ascii")
            img_data[img_path.name] = f"data:image/png;base64,{b64}"
    print(f"Embedded {len(img_data)} icons as base64")

    data_js = json.dumps({
        "projects": slim,
        "nullProjects": null_slim,
        "transmission": transmission,
        "substations": substations,
        "rez": rez,
        "manual_tx": manual_tx,
        "stages": STAGE_ORDER,
        "stageColour": STAGE_COLOUR,
        "states": STATES,
        "techs": techs,
        "capMax": cap_max,
        "gaShown": ga_shown,
        "imgData": img_data,
    })

    html = HTML_TEMPLATE.replace("__DATA__", data_js).replace("{null_count}", str(len(null_slim)))
    out = OUTPUTS / "nem_map.html"
    out.write_text(html, encoding="utf-8")
    print(f"Wrote {out}  ({len(slim)} markers)")


HTML_TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>NEM Generation Map</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<link rel="stylesheet" href="https://unpkg.com/esri-leaflet@3.0.12/dist/esri-leaflet.css">
<style>
  html,body { margin:0; padding:0; height:100%; font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif; }
  #app { display:flex; height:100%; }
  #sidebar {
    width: 340px; flex-shrink:0; height:100%; display:flex; flex-direction:column;
    background:#f8fafc; border-right:1px solid #e2e8f0; box-sizing:border-box;
  }
  #sidebar-header { padding:14px 16px 0; }
  #sidebar-tabs { display:flex; gap:0; border-bottom:1px solid #e2e8f0; margin-top:10px; }
  #sidebar-tabs button {
    flex:1; padding:8px 10px; font-size:12px; background:none; border:none; border-bottom:2px solid transparent;
    cursor:pointer; color:#64748b;
  }
  #sidebar-tabs button.active { color:#0f172a; border-bottom-color:#0f172a; font-weight:600; }
  .tab-panel { flex:1; overflow-y:auto; padding:12px 16px 24px; display:none; box-sizing:border-box; }
  .tab-panel.active { display:block; }
  #map { flex:1; }
  h1 { font-size:15px; margin:0 0 4px; }
  h2 { font-size:11px; text-transform:uppercase; letter-spacing:.04em; color:#475569; margin:14px 0 6px; }
  .meta { color:#64748b; font-size:11px; margin-bottom:8px; }
  .row { display:flex; align-items:center; gap:6px; font-size:12px; margin:2px 0; cursor:pointer; }
  .row input[type=checkbox] { margin:0; }
  .swatch { display:inline-block; width:10px; height:10px; border-radius:50%; }
  .count { color:#94a3b8; font-size:10px; margin-left:auto; }
  input[type=search], select, input[type=range] {
    width: 100%; box-sizing:border-box; padding:5px 7px; font-size:12px;
    border:1px solid #cbd5e1; border-radius:4px; background:white;
  }
  #search { margin-bottom:4px; }
  .range-row { display:flex; align-items:center; gap:6px; font-size:11px; color:#475569; }
  .range-row input { flex:1; }
  .legend-block { display:flex; align-items:center; gap:6px; font-size:11px; margin:2px 0; }
  .pill { display:inline-block; padding:1px 6px; font-size:10px; border-radius:8px; background:#e2e8f0; color:#334155; }
  details summary { cursor:pointer; font-size:11px; color:#475569; outline:none; padding:2px 0; }
  details > div { padding:2px 0 6px 4px; }
  button.reset { font-size:11px; padding:3px 8px; border:1px solid #cbd5e1; background:white; border-radius:4px; cursor:pointer; color:#334155; }
  button.reset:hover { background:#f1f5f9; }
  .btn-upload { font-size:11px; padding:3px 8px; border:2px solid #3b82f6; background:#eff6ff; border-radius:4px; cursor:pointer; color:#1d4ed8; font-weight:600; display:inline-flex; align-items:center; gap:4px; }
  .btn-upload:hover { background:#dbeafe; }
  /* Dashboard */
  .stat-grid { display:grid; grid-template-columns:1fr 1fr; gap:8px; margin-bottom:14px; }
  .stat-card { background:white; border:1px solid #e2e8f0; border-radius:6px; padding:8px 10px; }
  .stat-card .v { font-size:18px; font-weight:600; color:#0f172a; }
  .stat-card .l { font-size:10px; color:#64748b; text-transform:uppercase; letter-spacing:.04em; }
  .pipeline-table { width:100%; border-collapse:collapse; font-size:11px; }
  .pipeline-table th, .pipeline-table td { text-align:right; padding:4px 6px; border-bottom:1px solid #f1f5f9; }
  .pipeline-table th:first-child, .pipeline-table td:first-child { text-align:left; }
  .pipeline-table thead th { color:#64748b; font-weight:500; font-size:10px; text-transform:uppercase; }
  .pipeline-table tfoot td { font-weight:600; border-top:1px solid #cbd5e1; border-bottom:none; }
  .stage-cell { display:flex; align-items:center; gap:6px; }
  .bar-row td { padding:2px 6px; }
  .bar { height:14px; background:#e2e8f0; border-radius:2px; position:relative; }
  .bar > span { display:block; height:100%; border-radius:2px; }
  .bar-label { font-size:10px; color:#475569; display:flex; justify-content:space-between; margin-top:2px; }
  /* Dual-handle range slider */
  .dual-range { position:relative; height:24px; margin:4px 0 8px; }
  .dual-range-track {
    position:absolute; left:0; right:0; top:50%; transform:translateY(-50%);
    height:4px; background:#e2e8f0; border-radius:2px; pointer-events:none;
  }
  .dual-range-fill {
    position:absolute; top:50%; transform:translateY(-50%);
    height:4px; background:#0f172a; border-radius:2px; pointer-events:none;
  }
  .dual-range input[type=range] {
    position:absolute; width:100%; height:100%;
    pointer-events:none; appearance:none; -webkit-appearance:none;
    background:transparent; margin:0; padding:0; top:0; left:0;
  }
  .dual-range input[type=range]::-webkit-slider-runnable-track { background:transparent; }
  .dual-range input[type=range]::-webkit-slider-thumb {
    pointer-events:all; -webkit-appearance:none; appearance:none;
    width:16px; height:16px; border-radius:50%;
    background:#0f172a; border:2px solid white;
    box-shadow:0 1px 3px rgba(0,0,0,.35); cursor:pointer;
    margin-top:-6px;
  }
  .dual-range input[type=range]::-moz-range-track { background:transparent; }
  .dual-range input[type=range]::-moz-range-thumb {
    pointer-events:all; width:14px; height:14px; border-radius:50%;
    background:#0f172a; border:2px solid white;
    box-shadow:0 1px 3px rgba(0,0,0,.35); cursor:pointer; border:none;
  }
  .leaflet-popup-content { font-size:12px; }
  .leaflet-popup-content .pname { font-weight:600; font-size:13px; margin-bottom:4px; }
  .source-chip { font-size:10px; color:#64748b; }
</style>
</head>
<body>
<div id="app">
  <div id="sidebar">
   <div id="sidebar-header">
    <h1>NEM Generation Map</h1>
    <div class="meta" id="meta">—</div>
    <div id="sidebar-tabs">
      <button data-tab="filters" class="active">Filters</button>
      <button data-tab="dashboard">Dashboard</button>
    </div>
   </div>

   <div class="tab-panel active" id="tab-filters">
    <h2>Search</h2>
    <input id="search" type="search" placeholder="Name, owner, tech, stage, state, source…">

    <h2 style="display:flex;justify-content:space-between;align-items:center">Stage
      <span style="font-weight:normal;font-size:10px;letter-spacing:0">
        <a href="#" id="stage-all" style="color:#475569;text-decoration:none">all</a> ·
        <a href="#" id="stage-none" style="color:#475569;text-decoration:none">none</a>
      </span>
    </h2>
    <div id="stage-filter"></div>

    <h2>State</h2>
    <div id="state-filter"></div>

    <h2>Capacity (MW)</h2>
    <div style="font-size:11px;color:#475569;margin-bottom:4px">
      <span id="cap-lo">0</span> – <span id="cap-hi">—</span> MW
    </div>
    <div class="dual-range">
      <div class="dual-range-track"></div>
      <div id="cap-fill" class="dual-range-fill"></div>
      <input id="cap-min" type="range" min="0" value="0">
      <input id="cap-max" type="range" min="0" value="0">
    </div>

    <h2 style="display:flex;justify-content:space-between;align-items:center">Technology
      <span style="font-weight:normal;font-size:10px;letter-spacing:0">
        <a href="#" id="tech-all" style="color:#475569;text-decoration:none">all</a> ·
        <a href="#" id="tech-none" style="color:#475569;text-decoration:none">none</a>
      </span>
    </h2>
    <div id="tech-filter" style="max-height:160px;overflow-y:auto"></div>

    <h2>Network base layers</h2>
    <div class="meta" style="margin-bottom:4px">Geoscience Australia</div>
    <label class="row" style="padding-left:4px"><input type="checkbox" id="show-ga-power"> GA Power stations</label>
    <label class="row" style="padding-left:4px"><input type="checkbox" id="show-ga-lines" checked> GA Transmission lines</label>
    <label class="row"><input type="checkbox" id="show-transmission" checked> Transmission lines (OSM)</label>
    <label class="row"><input type="checkbox" id="show-substations"> Substations (≥66 kV)</label>
    <label class="row"><input type="checkbox" id="show-rez"> REZ boundaries (AEMO ISP 2021)</label>
    <label class="row"><input type="checkbox" id="show-manual-tx"> Transmission lines (Manual)</label>
    

    <h2 style="margin-top:18px">Other</h2>
    <label class="row"><input type="checkbox" id="only-aemo"> Only show projects on AEMO map</label>
    <label class="row"><input type="checkbox" id="only-geocoded"> Only show geocoded locations (GA or Nominatim)</label>

    <div style="margin-top:14px;display:flex;gap:6px;flex-wrap:wrap">
      <button class="reset" id="reset-btn">Reset filters</button>
      <button class="reset" id="export-btn">Export visible as CSV</button>
    </div>
    <div style="margin-top:6px;border-top:1px solid #e2e8f0;padding-top:8px;">
      <div style="font-size:10px;color:#64748b;margin-bottom:5px;">Missing locations workflow</div>
      <div style="display:flex;gap:6px;flex-wrap:wrap;align-items:center;">
        <button class="reset" id="export-null-btn" title="Download all projects with no location — fill in lat/lon and re-upload">&#8659; Export missing ({null_count})</button>
        <label class="btn-upload" id="upload-label" title="Upload a CSV with site_name + lat + lon columns to plot missing projects">&#8679; Upload fixed CSV<input type="file" id="upload-csv" accept=".csv" style="display:none"></label>
      </div>
      <div style="font-size:10px;color:#94a3b8;margin-top:4px;">Uploaded markers show as white circles. Add confirmed coords to manual_overrides.json to make permanent.</div>
    </div>

    <h2>Marker size</h2>
    <div class="meta">∝ log(capacity)</div>
   </div>

   <div class="tab-panel" id="tab-dashboard">
    <h2 style="margin-top:0">Currently visible</h2>
    <div class="stat-grid">
      <div class="stat-card"><div class="v" id="dash-count">—</div><div class="l">Projects</div></div>
      <div class="stat-card"><div class="v" id="dash-mw">—</div><div class="l">Total MW</div></div>
      <div class="stat-card"><div class="v" id="dash-mwh">—</div><div class="l">Storage MWh</div></div>
      <div class="stat-card"><div class="v" id="dash-aemo">—</div><div class="l">On AEMO map</div></div>
    </div>

    <h2>MW by stage</h2>
    <div id="dash-stage-bars"></div>

    <h2>Pipeline by stage × state (MW)</h2>
    <div style="overflow-x:auto">
      <table class="pipeline-table" id="dash-pipeline"></table>
    </div>

    <h2>MW by technology</h2>
    <div id="dash-tech-bars"></div>

    <div class="meta" style="margin-top:18px">Totals update as you change filters.</div>
   </div>
  </div>
  <div id="map"></div>
</div>

<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="https://unpkg.com/esri-leaflet@3.0.12/dist/esri-leaflet.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/OverlappingMarkerSpiderfier-Leaflet/0.2.6/oms.min.js"></script>
<script>
const DATA = __DATA__;
const HOME_VIEW = { center: [-30.0, 144.0], zoom: 5 };
const NEM_BOUNDS = L.latLngBounds([[-44, 128], [-9, 156]]);
const map = L.map('map', {
  preferCanvas: true,
  maxBounds: NEM_BOUNDS.pad(0.3),  // soft clamp - can't pan to Antarctica
  minZoom: 4,
  maxZoom: 14,
}).setView(HOME_VIEW.center, HOME_VIEW.zoom);

// Home / recenter control
const HomeControl = L.Control.extend({
  options: { position: 'topleft' },
  onAdd: function() {
    const c = L.DomUtil.create('div', 'leaflet-bar');
    const a = L.DomUtil.create('a', '', c);
    a.href = '#';
    a.title = 'Recenter on NEM';
    a.innerHTML = '⌂';
    a.style.fontSize = '18px';
    a.style.lineHeight = '26px';
    a.style.textAlign = 'center';
    L.DomEvent.on(a, 'click', e => {
      L.DomEvent.preventDefault(e);
      map.setView(HOME_VIEW.center, HOME_VIEW.zoom);
    });
    return c;
  },
});
map.addControl(new HomeControl());

// Per-state zoom shortcuts
const STATE_VIEW = {
  NSW: [[-32.5, 147], 6], VIC: [[-37, 145], 6], QLD: [[-22, 145], 5],
  SA:  [[-33, 138], 6], TAS: [[-42, 146.5], 7],
};
const StateZoomControl = L.Control.extend({
  options: { position: 'topleft' },
  onAdd: function() {
    const c = L.DomUtil.create('div', 'leaflet-bar');
    Object.entries(STATE_VIEW).forEach(([st, view]) => {
      const a = L.DomUtil.create('a', '', c);
      a.href = '#';
      a.title = `Zoom to ${st}`;
      a.textContent = st;
      a.style.fontSize = '10px';
      a.style.lineHeight = '26px';
      a.style.padding = '0 4px';
      a.style.minWidth = '24px';
      L.DomEvent.on(a, 'click', e => {
        L.DomEvent.preventDefault(e);
        map.setView(view[0], view[1]);
      });
    });
    return c;
  },
});
map.addControl(new StateZoomControl());
L.control.scale({ imperial: false, position: 'bottomright' }).addTo(map);
L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
  attribution: '&copy; OpenStreetMap &copy; CARTO',
  maxZoom: 19,
}).addTo(map);

// --- Transmission lines (OSM) ---
function txStyle(f) {
  const v = f.properties.v || f.properties.voltage_kv || 0;
  // AEMO-aligned voltage palette
  let color = '#999';
  if (v >= 500) color = '#fde047';        // yellow 500 kV
  else if (v >= 330) color = '#f59e0b';   // orange 330 kV
  else if (v >= 275) color = '#ec4899';   // pink/magenta 275 kV
  else if (v >= 220) color = '#1d4ed8';   // blue 220 kV
  else if (v >= 132) color = '#dc2626';   // red 132/110 kV
  else if (v >= 66)  color = '#7c2d12';   // brown 66 kV
  return { color, weight: v >= 275 ? 1.6 : 1.1, opacity: 0.75 };
}
const transmissionLayer = L.geoJSON(DATA.transmission, {
  style: txStyle,
  onEachFeature: (f, l) => {
    const p = f.properties;
    const v = p.v || p.voltage_kv;
    const n = p.n || p.name;
    const o = p.o || p.operator;
    l.bindTooltip(`${v} kV${n ? ' • ' + n : ''}${o ? ' • ' + o : ''}`);
  },
}).addTo(map);
transmissionLayer.bringToBack();

const substationLayer = L.geoJSON(DATA.substations, {
  pointToLayer: (f, latlng) => L.circleMarker(latlng, {
    radius: 2.5, color: '#475569', weight: 1, fillColor: '#cbd5e1', fillOpacity: 0.8,
  }),
  onEachFeature: (f, l) => {
    const p = f.properties;
    l.bindTooltip(`${p.name || 'Substation'} • ${p.voltage_kv} kV`);
  },
});

// --- Manual transmission lines ---
const manualTxLayer = L.geoJSON(DATA.manual_tx, {
  style: f => {
    const v = (f.properties || {}).voltage_kv || 0;
    let color = '#999';
    if      (v >= 500) color = '#fde047';
    else if (v >= 330) color = '#f59e0b';
    else if (v >= 275) color = '#ec4899';
    else if (v >= 220) color = '#1d4ed8';
    else if (v >= 132) color = '#dc2626';
    else if (v >=  66) color = '#7c2d12';
    return { color, weight: v >= 275 ? 1.6 : 1.1, opacity: 0.85, dashArray: '8 4' };
  },
  onEachFeature: (f, l) => {
    const p = f.properties || {};
    const label = [
      p.voltage_kv ? `${p.voltage_kv} kV` : '',
      p.name || '',
      p.notes || '',
    ].filter(Boolean).join(' — ');
    l.bindTooltip(`Manual: ${label || 'transmission line'}`);
  },
});

// --- GA technology filter mapping ---
// Maps our normalised technology categories → ArcGIS WHERE clause for GA power stations.
// Categories not listed (Battery, Storage, Hybrid) have no GA equivalent — show all for context.
const TECH_TO_GA_WHERE = {
  'Solar':           "PRIMARYFUELTYPE = 'Solar'",
  'Solar Thermal':   "PRIMARYFUELTYPE = 'Solar' AND GENERATIONTYPE LIKE '%Thermal%'",
  'Wind (Onshore)':  "PRIMARYFUELTYPE = 'Wind'",
  'Wind (Offshore)': "PRIMARYFUELTYPE = 'Wind'",
  'Hydro':           "PRIMARYFUELTYPE = 'Water' AND GENERATIONTYPE NOT LIKE '%Pumped%'",
  'Pumped Hydro':    "PRIMARYFUELTYPE = 'Water' AND GENERATIONTYPE LIKE '%Pumped%'",
  'OCGT':            "GENERATIONTYPE LIKE '%Open Cycle%'",
  'CCGT':            "GENERATIONTYPE LIKE '%Combined Cycle%'",
  'Coal':            "PRIMARYFUELTYPE = 'Coal'",
  'Biomass':         "PRIMARYFUELTYPE IN ('Biomass','Biogas')",
  'Gas':             "PRIMARYFUELTYPE IN ('Natural Gas','Gas','Compressed Natural Gas','Coal Seam Methane','Distillate','Diesel')",
};

function updateGaFilter() {
  if (!map.hasLayer(gaPowerLayer)) return;   // only filter when layer is visible
  const selTechs = [...document.querySelectorAll('#tech-filter input:checked')].map(e => e.dataset.value);
  const allTechN  = document.querySelectorAll('#tech-filter input').length;
  let techWhere = '1=1';
  if (selTechs.length < allTechN && selTechs.length > 0) {
    // Build OR clause from only the selected techs that have GA equivalents.
    // Techs with no GA equivalent (Battery, Hybrid, etc.) contribute nothing.
    // If none of the selected techs have a GA equivalent → show nothing (1=0).
    const clauses = [...new Set(selTechs.filter(t => TECH_TO_GA_WHERE[t]).map(t => TECH_TO_GA_WHERE[t]))];
    techWhere = clauses.length === 0 ? '1=0'
      : clauses.length === 1 ? clauses[0]
      : '(' + clauses.join(' OR ') + ')';
  }
  const capMinV = +document.getElementById('cap-min').value;
  const capMaxV = +document.getElementById('cap-max').value;
  const parts = [techWhere];
  if (capMinV > 0) parts.push(`GENERATIONMW >= ${capMinV}`);
  if (capMaxV < DATA.capMax) parts.push(`GENERATIONMW <= ${capMaxV}`);
  gaPowerLayer.setWhere(parts.join(' AND '));
}

function gaLayerToggle(layerId, layer) {
  document.getElementById(layerId).addEventListener('change', e => {
    if (e.target.checked) { layer.addTo(map); if (layerId === 'show-ga-power') updateGaFilter(); renderLegend(); }
    else { map.removeLayer(layer); renderLegend(); }
  });
}

// --- Geoscience Australia Electricity Infrastructure ---
// Three featureLayers so we can apply custom colours/icons client-side.
// Layer 2: Transmission Lines — coloured by CAPACITYKV to match the OSM palette above.
const GA_INFRA_URL = 'https://services.ga.gov.au/gis/rest/services/National_Electricity_Infrastructure/MapServer';
const gaLinesLayer = L.esri.featureLayer({
  url: GA_INFRA_URL + '/2',
  attribution: '&copy; <a href="https://www.ga.gov.au">Geoscience Australia</a>',
  style: f => {
    const p = f.properties || {};
    const v = p.capacitykv || p.CAPACITYKV || 0;
    let color = '#999';
    if      (v >= 500) color = '#fde047';
    else if (v >= 330) color = '#f59e0b';
    else if (v >= 275) color = '#ec4899';
    else if (v >= 220) color = '#1d4ed8';
    else if (v >= 132) color = '#dc2626';
    else if (v >=  66) color = '#7c2d12';
    return { color, weight: v >= 275 ? 1.8 : 1.2, opacity: 0.8 };
  },
  onEachFeature: (f, l) => {
    const p = f.properties || {};
    const v = p.capacitykv || p.CAPACITYKV || '?';
    const n = p.name || p.NAME || '';
    l.bindTooltip(`GA: ${v} kV${n ? ' • ' + n : ''}`);
  },
});

// ── GA POWER STATION TECHNOLOGY COLOURS ──────────────────────────────────────
// Uses the same technology names as project markers so the technology filter
// applies uniformly to both project markers and GA power stations.
// ─────────────────────────────────────────────────────────────────────────────
const GA_IMG = DATA.imgData;   // filename → base64 data URI (self-contained)
const TECH_COLOUR = {
  'Solar':              '#f59e0b',
  'Solar Thermal':      '#f59e0b',
  'Solar and Storage':  '#f59e0b',
  'Wind (Onshore)':     '#3b82f6',
  'Wind (Offshore)':    '#0ea5e9',
  'Wind and Storage':   '#3b82f6',
  'Hydro':              '#06b6d4',
  'Pumped Hydro':       '#0284c7',
  'Battery':            '#10b981',
  'Battery Storage':    '#10b981',
  'Hybrid':             '#a855f7',
  'OCGT':               '#f97316',
  'CCGT':               '#ea580c',
  'Coal':               '#374151',
  'Biomass':            '#16a34a',
  'Gas':                '#fb923c',
  'Other':              '#6b7280',
};

// Icon HTML using the same TECH_TO_IMG lookup as project markers
function gaIcon(tech, size) {
  const imgFile = TECH_TO_IMG[tech];
  if (imgFile)
    return `<img src="${GA_IMG[imgFile]}" style="width:${size}px;height:${size}px;display:block;object-fit:contain">`;
  return `<div style="width:${size}px;height:${size}px;border-radius:50%;background:${TECH_COLOUR[tech] || '#6b7280'};opacity:0.7"></div>`;
}

// Map GA fuel/generation fields → project technology names
function gaFuelCategory(fuel, genType) {
  const f = (fuel || '').toLowerCase();
  const g = (genType || '').toLowerCase();
  if (f === 'solar') return 'Solar';
  if (f === 'wind')  return 'Wind (Onshore)';
  if (f === 'water') {
    if (g.includes('pumped')) return 'Pumped Hydro';
    return 'Hydro';
  }
  if (f === 'coal' || f === 'fossil') return 'Coal';
  if (f === 'biomass' || f === 'biogas') return 'Biomass';
  if (f === 'distillate' || f === 'diesel' || f === 'fuel oil') return 'Gas';
  // Gas subtypes — check generationtype first
  if (g.includes('combined cycle')) return 'CCGT';
  if (g.includes('open cycle') || g.includes('open cycle gas turbine')) return 'OCGT';
  if (f === 'natural gas' || f === 'gas' || f === 'compressed natural gas' || f === 'coal seam methane') return 'Gas';
  return 'Other';
}

// Station names already shown as project markers — suppress duplicates in GA layer
const GA_ALREADY_SHOWN = new Set(DATA.gaShown);

// Layer 1: Major Power Stations — coloured by fuel category
const gaPowerLayer = L.esri.featureLayer({
  url: GA_INFRA_URL + '/1',
  attribution: '&copy; <a href="https://www.ga.gov.au">Geoscience Australia</a>',
  pointToLayer: (f, latlng) => {
    const p = f.properties || {};
    const name = (p.name || p.NAME || '').trim();
    // Skip stations already shown as project markers
    if (GA_ALREADY_SHOWN.has(name)) {
      return L.circleMarker(latlng, { radius: 0, opacity: 0, fillOpacity: 0, interactive: false });
    }
    const cat   = gaFuelCategory(p.primaryfueltype || p.PRIMARYFUELTYPE, p.generationtype || p.GENERATIONTYPE);
    const color = TECH_COLOUR[cat] || TECH_COLOUR['Other'];
    const mw    = p.generationmw || p.GENERATIONMW || 0;
    const size  = markerSizePx(mw);   // same log scale as project markers
    const iSize = Math.round(size * 0.62);
    // GA-only stations: plain icon, no coloured background
    // Coloured backgrounds are reserved for NEM+KCI project markers only
    return L.marker(latlng, {
      icon: L.divIcon({
        className: '',
        html: `<div style="width:${size}px;height:${size}px;
                    display:flex;align-items:center;justify-content:center;
                    filter:drop-shadow(0 1px 2px rgba(0,0,0,0.35));cursor:pointer">
                 ${gaIcon(cat, iSize)}
               </div>`,
        iconSize:    [size, size],
        iconAnchor:  [size / 2, size / 2],
        popupAnchor: [0, -size / 2],
      }),
      title: name,
    });
  },
  onEachFeature: (f, l) => {
    const p = f.properties || {};
    const fuel = p.primaryfueltype || p.PRIMARYFUELTYPE || '';
    const genType = p.generationtype || p.GENERATIONTYPE || '';
    const cat = gaFuelCategory(fuel, genType);
    const color = TECH_COLOUR[cat] || TECH_COLOUR['Other'];
    const mw = p.generationmw || p.GENERATIONMW;
    const tip = [p.name || p.NAME, mw ? mw + ' MW' : '', cat].filter(Boolean).join(' • ');
    l.bindTooltip(tip || 'Power Station');
    l.bindPopup(`
      <div style="font-family:system-ui;font-size:12px;min-width:170px">
        <div style="font-weight:600;font-size:13px;margin-bottom:4px">${p.name || p.NAME || 'Power Station'}</div>
        <div><b>Technology:</b> <span style="color:${color};font-weight:600">${cat}</span></div>
        ${genType ? '<div><b>Type:</b> ' + genType + '</div>' : ''}
        ${fuel ? '<div><b>Fuel:</b> ' + fuel + (p.primarysubfueltype||p.PRIMARYSUBFUELTYPE ? ' / ' + (p.primarysubfueltype||p.PRIMARYSUBFUELTYPE) : '') + '</div>' : ''}
        ${mw ? '<div><b>Capacity:</b> ' + mw + ' MW</div>' : ''}
        ${(p.owner||p.OWNER) ? '<div><b>Owner:</b> ' + (p.owner||p.OWNER) + '</div>' : ''}
        ${(p.state||p.STATE) ? '<div><b>State:</b> ' + (p.state||p.STATE) + '</div>' : ''}
        <div style="color:#888;font-size:10px;margin-top:4px">Source: Geoscience Australia</div>
      </div>`);
  },
});

// Layer 0: Substations (GA)
const gaSubLayer = L.esri.featureLayer({
  url: GA_INFRA_URL + '/0',
  attribution: '&copy; <a href="https://www.ga.gov.au">Geoscience Australia</a>',
  pointToLayer: (f, latlng) => L.circleMarker(latlng, {
    radius: 3, color: '#475569', weight: 1, fillColor: '#0E73B8', fillOpacity: 0.9,
  }),
  onEachFeature: (f, l) => {
    const p = f.properties || {};
    const kv = p.capacitykv || p.CAPACITYKV || '';
    l.bindTooltip(`GA Substation: ${p.name || p.NAME || ''}${kv ? ' • ' + kv + ' kV' : ''}`);
  },
});

// --- REZ boundaries ---
const rezLabelLayer = L.layerGroup();   // permanent labels at polygon centroids
const rezLayer = L.geoJSON(DATA.rez, {
  style: f => {
    const p = f.properties || {};
    const fill = p.fill || '#e5e7eb';
    return { color: fill, weight: 1.2, fillColor: fill, fillOpacity: 0.25 };
  },
  onEachFeature: (f, l) => {
    const p = f.properties || {};
    const name  = p.rez_name || p.Name || '';
    const state = p.state || '';
    const type  = p.rez_type || '';
    const id    = p.rez_id   || '';
    const fill  = p.fill     || '#6b7280';
    l.bindTooltip(`<b>${name}</b><br>${state}${type === 'Offshore' ? ' • Offshore Wind Zone' : ' • REZ'}`, { sticky: true });
    l.bindPopup(`
      <div style="font-family:system-ui;font-size:12px;min-width:160px">
        <div style="font-weight:600;font-size:13px;margin-bottom:4px">${id} — ${name}</div>
        <div><b>State:</b> ${state}</div>
        <div><b>Type:</b> ${type}</div>
        <div style="color:#888;font-size:10px;margin-top:4px">Source: AEMO ISP 2021 (Geoscience Australia)</div>
      </div>`);
    // Label inside the polygon — placed at bounding-box centre
    if (id) {
      const bounds = l.getBounds ? l.getBounds() : null;
      if (bounds && bounds.isValid()) {
        const centre = bounds.getCenter();
        rezLabelLayer.addLayer(L.marker(centre, {
          icon: L.divIcon({
            className: '',
            html: `<div style="
                font-size:11px;font-weight:600;
                color:#414d60;
                white-space:nowrap;
                text-shadow:0 0 4px white,0 0 4px white,0 0 4px white;
                transform:translate(-50%,-50%);
                pointer-events:none">${id}</div>`,
            iconSize:   [0, 0],
            iconAnchor: [0, 5],
          }),
          interactive: false,
          zIndexOffset: -200,
        }));
      }
    }
  },
});

// --- Markers ---
// ── Project marker icons ──────────────────────────────────────────────────────
// Maps our normalised technology → image file in ../data/image/
// Technologies without an image fall back to a small dot.
const TECH_TO_IMG = {
  'Solar':           'sun.png',
  'Solar Thermal':   'sun.png',
  'Wind (Onshore)':  'wind.png',
  'Wind (Offshore)': 'wind.png',
  'Hydro':           'hydro.png',
  'Pumped Hydro':    'pumphydro.png',
  'OCGT':            'ocgt.png',
  'CCGT':            'ccgt.png',
  'Coal':            'coal.png',
  'Biomass':         'biomass.png',
  'Battery':            'battery.png',
  'Battery Storage':    'battery.png',
  'Storage':            'battery.png',
  'Solar and Storage':  'sun.png',
  'Wind and Storage':   'wind.png',
  'Gas':                'ocgt.png',
  // Hybrid, Other → no image → coloured dot fallback
};

// Stage label shown in tooltip / legend (maps our internal stages → user-facing terms)
const STAGE_LABEL = {
  'Existing':      'Existing',
  'Retiring':      'Retiring (Announced Withdrawal)',
  'Commissioning': 'Commissioning',
  'Committed':     'Committed',
  'Anticipated':   'Pre-registration',
  'DA Approved':  'DA Approved',
  'DA Submitted': 'DA Submitted',
  'Application':  'Application',
  'Enquiry':      'Enquiry',
  'Expired':      'Expired',
  'Withdrawn':    'Withdrawn',
  'Unknown':      'Unknown',
};

function markerSizePx(cap) {
  // Icon size scales log with capacity: 20 px (small) → 36 px (large)
  if (!cap || cap <= 0) return 20;
  return Math.max(20, Math.min(36, 20 + Math.log10(cap + 1) * 5));
}

function projectIcon(tech, stage, cap, geocodeSrc) {
  const colour  = DATA.stageColour[stage] || DATA.stageColour['Unknown'];
  const size    = markerSizePx(cap);
  const imgFile = TECH_TO_IMG[tech];
  const iSize   = Math.round(size * 0.62);

  // Suburb/QLD_FS/manual estimated locations → dashed border to signal "approximate"
  const borderStyle = (geocodeSrc === 'suburb' || geocodeSrc === 'QLD_FS' || geocodeSrc === 'manual') ? 'dashed' : 'solid';
  const bg = `background:${colour}80;border:2px ${borderStyle} ${colour};`;

  const inner = imgFile
    ? `<img src="${GA_IMG[imgFile]}" style="width:${iSize}px;height:${iSize}px;object-fit:contain;display:block">`
    : `<div style="width:${iSize}px;height:${iSize}px;border-radius:50%;background:${colour};opacity:0.7"></div>`;

  return L.divIcon({
    className: '',
    html: `<div style="width:${size}px;height:${size}px;border-radius:50%;${bg}
                display:flex;align-items:center;justify-content:center;
                box-shadow:0 1px 4px rgba(0,0,0,0.22);cursor:pointer">${inner}</div>`,
    iconSize:   [size, size],
    iconAnchor: [size / 2, size / 2],
    popupAnchor:[0, -size / 2],
  });
}

// --- Overlapping marker spiderfy ---
const oms = new OverlappingMarkerSpiderfier(map, {
  nearbyDistance: 10,
  keepSpiderfied: true,
  legWeight: 2,
  legColors: { usual: '#94a3b8', highlighted: '#0f172a' },
});
oms.addListener('click', m => m.openPopup());
oms.addListener('spiderfy',   ms => ms.forEach(m => m.setOpacity(1)));
oms.addListener('unspiderfy', ms => ms.forEach(m => m.setOpacity(1)));

const markers = DATA.projects.map(p => {
  const m = L.marker([p.lat, p.lon], { icon: projectIcon(p.t, p.s, p.c, p.g) });
  m._p = p;
  const label = STAGE_LABEL[p.s] || p.s;
  m.bindTooltip(`${p.n} — ${p.c ? p.c.toFixed(0) : '?'} MW — ${label}`);
  m.bindPopup(() => popupHtml(p));
  oms.addMarker(m);
  return m;
});
const markerLayer = L.layerGroup(markers).addTo(map);

// Default layers on at startup
gaLinesLayer.addTo(map);
gaPowerLayer.addTo(map);
gaSubLayer.addTo(map);   // substations always on — no toggle
updateGaFilter();

function popupHtml(p) {
  const colour = DATA.stageColour[p.s] || DATA.stageColour["Unknown"];
  const label  = STAGE_LABEL[p.s] || p.s;
  const aemoBadge = p.aemo ? `<span class="pill" style="background:${colour}20;color:${colour}">on AEMO map</span>` : '';
  const geoLabel = p.g === 'suburb'
    ? `<span style="color:#b45309">&#9992; Estimated location (suburb-level only)</span>`
    : p.g === 'QLD_FS'
    ? `<span style="color:#b45309">&#9992; Approximate location (QLD cadastre centroid)</span>`
    : p.g === 'manual'
    ? `<span style="color:#b45309">&#9992; Manually placed location (approximate)</span>`
    : p.g ? `Location: ${p.g}` : '';
  const geoSrc = p.g
    ? `<div style="color:#64748b;font-size:10px;margin-top:2px">${geoLabel}</div>`
    : `<div style="color:#b45309;font-size:11px">Location not geocoded — hidden until geocode.py is run</div>`;
  return `
    <div class="pname">${escapeHtml(p.n)}</div>
    <div><b>Stage:</b> <span style="color:${colour};font-weight:600">${label}</span> ${aemoBadge}</div>
    <div><b>Capacity:</b> ${p.c ? p.c.toFixed(1) : '?'} MW${p.mwh ? ` / ${p.mwh} MWh` : ''}</div>
    <div><b>State:</b> ${p.st} (${p.r})</div>
    <div><b>Technology:</b> ${escapeHtml(p.t)}${p.f ? ' / ' + escapeHtml(p.f) : ''}</div>
    <div><b>Owner:</b> ${escapeHtml(p.o)}</div>
    ${(p.g === 'manual' && p.gd) ? `<div><b>Location:</b> ${escapeHtml(p.gd)}</div>` : p.loc ? `<div><b>Location:</b> ${escapeHtml(p.loc)}</div>` : ''}
    ${geoSrc}
    <div class="source-chip" style="margin-top:4px">Source: ${p.src}</div>
  `;
}
function escapeHtml(s){ return (s||'').replace(/[&<>"]/g, c=>({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;"})[c]); }

// --- Sidebar UI ---
function counts(field) {
  const c = {};
  DATA.projects.forEach(p => { c[p[field]] = (c[p[field]]||0) + 1; });
  return c;
}
const stageCounts = counts('s');
const stateCounts = counts('st');
const techCounts  = counts('t');

function makeCheckboxes(containerId, items, colourFn, defaults) {
  const el = document.getElementById(containerId);
  items.forEach(it => {
    const id = `${containerId}-${it.value}`;
    const row = document.createElement('label');
    row.className = 'row';
    row.innerHTML = `
      <input type="checkbox" id="${id}" data-value="${it.value}" ${defaults.has(it.value) ? 'checked' : ''}>
      ${colourFn ? `<span class="swatch" style="background:${colourFn(it.value)}"></span>` : ''}
      <span>${it.label}</span>
      <span class="count">${it.count||''}</span>`;
    el.appendChild(row);
  });
}
const stageDefaults = new Set(DATA.stages.filter(s => s !== 'Existing' && s !== 'Withdrawn' && s !== 'Expired'));
makeCheckboxes('stage-filter',
  DATA.stages.map(s => ({value:s, label:s, count:stageCounts[s]||0})),
  v => DATA.stageColour[v], stageDefaults);
makeCheckboxes('state-filter',
  DATA.states.map(s => ({value:s, label:s, count:stateCounts[s]||0})),
  null, new Set(DATA.states));
makeCheckboxes('tech-filter',
  DATA.techs.map(t => ({value:t, label:t, count:techCounts[t]||0})),
  null, new Set(DATA.techs));

// Stage all / none
document.getElementById('stage-all').addEventListener('click', e => {
  e.preventDefault();
  document.querySelectorAll('#stage-filter input').forEach(el => el.checked = true);
  applyFilters();
});
document.getElementById('stage-none').addEventListener('click', e => {
  e.preventDefault();
  document.querySelectorAll('#stage-filter input').forEach(el => el.checked = false);
  applyFilters();
});
// Tech all / none
document.getElementById('tech-all').addEventListener('click', e => {
  e.preventDefault();
  document.querySelectorAll('#tech-filter input').forEach(el => el.checked = true);
  applyFilters(); updateGaFilter();
});
document.getElementById('tech-none').addEventListener('click', e => {
  e.preventDefault();
  document.querySelectorAll('#tech-filter input').forEach(el => el.checked = false);
  applyFilters(); updateGaFilter();
});

const capMin = document.getElementById('cap-min');
const capMax = document.getElementById('cap-max');
capMin.max = DATA.capMax;
capMax.max = DATA.capMax;
capMax.value = DATA.capMax;
function updateCapLabels() {
  document.getElementById('cap-lo').textContent = (+capMin.value).toLocaleString();
  document.getElementById('cap-hi').textContent = (+capMax.value >= DATA.capMax)
    ? DATA.capMax.toLocaleString() + '+'
    : (+capMax.value).toLocaleString();
  const pMin = +capMin.value / DATA.capMax * 100;
  const pMax = +capMax.value / DATA.capMax * 100;
  const fill = document.getElementById('cap-fill');
  fill.style.left  = pMin + '%';
  fill.style.width = (pMax - pMin) + '%';
}
updateCapLabels();
capMin.addEventListener('input', () => {
  if (+capMin.value > +capMax.value) capMax.value = capMin.value;
  updateCapLabels(); applyFilters(); updateGaFilter();
});
capMax.addEventListener('input', () => {
  if (+capMax.value < +capMin.value) capMin.value = capMax.value;
  updateCapLabels(); applyFilters(); updateGaFilter();
});

document.getElementById('search').addEventListener('input', applyFilters);
document.querySelectorAll('#tech-filter input').forEach(el =>
  el.addEventListener('change', () => { applyFilters(); updateGaFilter(); }));
document.getElementById('only-aemo').addEventListener('change', applyFilters);
document.getElementById('only-geocoded').addEventListener('change', applyFilters);
document.querySelectorAll('#stage-filter input, #state-filter input').forEach(el =>
  el.addEventListener('change', applyFilters));
document.getElementById('show-transmission').addEventListener('change', e => {
  if (e.target.checked) { transmissionLayer.addTo(map); transmissionLayer.bringToBack(); }
  else map.removeLayer(transmissionLayer);
});
document.getElementById('show-substations').addEventListener('change', e => {
  if (e.target.checked) substationLayer.addTo(map);
  else map.removeLayer(substationLayer);
});
document.getElementById('show-rez').addEventListener('change', e => {
  if (e.target.checked) {
    rezLayer.addTo(map); rezLayer.bringToBack();
    rezLabelLayer.addTo(map);
  } else {
    map.removeLayer(rezLayer);
    map.removeLayer(rezLabelLayer);
  }
});
document.getElementById('show-manual-tx').addEventListener('change', e => {
  if (e.target.checked) manualTxLayer.addTo(map);
  else map.removeLayer(manualTxLayer);
});
gaLayerToggle('show-ga-power', gaPowerLayer);
gaLayerToggle('show-ga-lines', gaLinesLayer);

document.getElementById('reset-btn').addEventListener('click', () => {
  document.querySelectorAll('#stage-filter input').forEach(el => el.checked = stageDefaults.has(el.dataset.value));
  document.querySelectorAll('#state-filter input').forEach(el => el.checked = true);
  document.getElementById('search').value = '';
  document.querySelectorAll('#tech-filter input').forEach(el => el.checked = true);
  capMin.value = 0; capMax.value = DATA.capMax; updateCapLabels();
  document.getElementById('only-aemo').checked = false;
  document.getElementById('only-geocoded').checked = false;
  window.applyFilters();
  updateGaFilter();   // reset GA to show all power stations
});

// --- CSV export ---
function csvEscape(v) {
  if (v == null) return '';
  const s = String(v);
  if (/[",\n\r]/.test(s)) return '"' + s.replace(/"/g, '""') + '"';
  return s;
}
document.getElementById('export-btn').addEventListener('click', () => {
  const cols = [
    ['site_name','n'], ['state','st'], ['region','r'], ['stage','s'],
    ['capacity_mw','c'], ['storage_mwh','mwh'], ['technology','t'], ['fuel','f'],
    ['owner','o'], ['location_desc','loc'], ['lat','lat'], ['lon','lon'],
    ['on_aemo_map','aemo'], ['geocode_source','g'], ['source','src'],
    ['substation_within_5km','sub2'], ['transmission_within_5km','tx5'],
  ];
  const vis = markers.filter(m => markerLayer.hasLayer(m)).map(m => m._p);
  const header = cols.map(c => c[0]).join(',');
  const rows = vis.map(p => cols.map(c => csvEscape(p[c[1]])).join(','));
  const csv = '﻿' + header + '\n' + rows.join('\n');
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  const ts = new Date().toISOString().replace(/[:T]/g,'-').slice(0,16);
  a.href = url;
  a.download = `nem_projects_${ts}_${vis.length}.csv`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
});

// --- Export missing locations ---
const NULL_COLS = [
  ['site_name','n'], ['state','st'], ['region','r'], ['stage','s'],
  ['capacity_mw','c'], ['storage_mwh','mwh'], ['technology','t'], ['fuel','f'],
  ['owner','o'], ['location_desc','loc'], ['source','src'], ['on_aemo_map','aemo'],
  ['lat',''], ['lon',''],
];
document.getElementById('export-null-btn').addEventListener('click', () => {
  const nullProjects = DATA.nullProjects || [];
  const header = NULL_COLS.map(c => c[0]).join(',');
  const rows = nullProjects.map(p =>
    NULL_COLS.map(c => c[1] ? csvEscape(p[c[1]]) : '').join(',')
  );
  const csv = '﻿' + header + '\n' + rows.join('\n');
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  const ts = new Date().toISOString().replace(/[:T]/g,'-').slice(0,16);
  a.href = url;
  a.download = `nem_missing_locations_${ts}.csv`;
  document.body.appendChild(a); a.click();
  document.body.removeChild(a); URL.revokeObjectURL(url);
});

// --- Upload fixed CSV and add markers ---
let uploadedLayer = null;
document.getElementById('upload-csv').addEventListener('change', function() {
  const file = this.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = e => {
    const lines = e.target.result.replace(/\r\n/g,'\n').replace(/\r/g,'\n').split('\n');
    if (lines.length < 2) return;
    // Parse header — strip BOM
    const hdr = lines[0].replace(/^﻿/,'').split(',').map(h => h.trim().toLowerCase());
    const iName = hdr.indexOf('site_name');
    const iLat  = hdr.indexOf('lat');
    const iLon  = hdr.indexOf('lon');
    const iSt   = hdr.indexOf('state');
    const iStg  = hdr.indexOf('stage');
    const iCap  = hdr.indexOf('capacity_mw');
    const iTech = hdr.indexOf('technology');
    if (iName < 0 || iLat < 0 || iLon < 0) {
      alert('CSV must contain columns: site_name, lat, lon');
      return;
    }
    function parseRow(line) {
      // Handles quoted fields
      const out = []; let cur = '', inQ = false;
      for (let i = 0; i < line.length; i++) {
        const ch = line[i];
        if (ch === '"') { if (inQ && line[i+1] === '"') { cur += '"'; i++; } else inQ = !inQ; }
        else if (ch === ',' && !inQ) { out.push(cur); cur = ''; }
        else cur += ch;
      }
      out.push(cur);
      return out;
    }
    if (uploadedLayer) { map.removeLayer(uploadedLayer); uploadedLayer = null; }
    uploadedLayer = L.layerGroup().addTo(map);
    let added = 0, skipped = 0;
    for (let i = 1; i < lines.length; i++) {
      if (!lines[i].trim()) continue;
      const cols = parseRow(lines[i]);
      const lat = parseFloat(cols[iLat]);
      const lon = parseFloat(cols[iLon]);
      if (isNaN(lat) || isNaN(lon)) { skipped++; continue; }
      const name  = cols[iName]  || '';
      const state = iSt  >= 0 ? (cols[iSt]  || '') : '';
      const stage = iStg >= 0 ? (cols[iStg] || '') : '';
      const cap   = iCap >= 0 ? parseFloat(cols[iCap]) || 0 : 0;
      const tech  = iTech >= 0 ? (cols[iTech] || '') : '';
      const r = Math.max(5, Math.min(18, 5 + Math.log2(Math.max(1, cap)) * 1.5));
      const marker = L.circleMarker([lat, lon], {
        radius: r, color: '#000', weight: 2,
        fillColor: '#ffffff', fillOpacity: 0.85, dashArray: '4 3',
      });
      marker.bindPopup(`<b>${name}</b><br>${stage} · ${tech} · ${cap} MW<br>${state}<br><i style="color:#888">User-placed location</i>`);
      uploadedLayer.addLayer(marker);
      added++;
    }
    this.value = '';   // reset so same file can be re-uploaded
    alert(`Added ${added} markers from uploaded CSV. ${skipped} rows skipped (no valid lat/lon).`);
  };
  reader.readAsText(file, 'utf-8');
});

// legendDiv must be declared before applyFilters() is called, so renderLegend()
// can safely guard with `if (!legendDiv) return` rather than hitting TDZ.
let legendDiv = null;

function applyFilters() {
  const stages = new Set([...document.querySelectorAll('#stage-filter input:checked')].map(e => e.dataset.value));
  const states = new Set([...document.querySelectorAll('#state-filter input:checked')].map(e => e.dataset.value));
  const selectedTechs = new Set([...document.querySelectorAll('#tech-filter input:checked')].map(e => e.dataset.value));
  const allTechCount = document.querySelectorAll('#tech-filter input').length;
  const techFiltered = selectedTechs.size < allTechCount;
  const q = document.getElementById('search').value.trim().toLowerCase();
  const capMinV = +capMin.value;
  const capMaxV = +capMax.value;
  const onlyAemo = document.getElementById('only-aemo').checked;
  const onlyGeo = document.getElementById('only-geocoded').checked;

  let shown = 0;
  markers.forEach(m => {
    const p = m._p;
    let ok = stages.has(p.s) && states.has(p.st);
    if (ok && techFiltered) ok = selectedTechs.has(p.t);
    if (ok && q) ok = (
      p.n.toLowerCase().includes(q) ||
      (p.o||'').toLowerCase().includes(q) ||
      (p.loc||'').toLowerCase().includes(q) ||
      (p.t||'').toLowerCase().includes(q) ||
      (p.s||'').toLowerCase().includes(q) ||
      (p.st||'').toLowerCase().includes(q) ||
      (p.src||'').toLowerCase().includes(q) ||
      (p.r||'').toLowerCase().includes(q)
    );
    if (ok && (capMinV > 0 || capMaxV < DATA.capMax)) {
      const c = p.c || 0;
      ok = c >= capMinV && c <= capMaxV;
    }
    if (ok && onlyAemo) ok = p.aemo;
    if (ok && onlyGeo) ok = !!p.g;
    if (ok) { if (!markerLayer.hasLayer(m)) markerLayer.addLayer(m); shown++; }
    else { if (markerLayer.hasLayer(m)) markerLayer.removeLayer(m); }
  });
  document.getElementById('meta').textContent =
    `${shown.toLocaleString()} of ${DATA.projects.length.toLocaleString()} projects shown`;

  // Hide GA layers while a search query is active — they are not searchable
  // and clutter the result. Restore them when search is cleared.
  // Hide GA power/lines layers while a search is active — not searchable and clutter results.
  // GA substations always stay visible regardless of search.
  const gaSearchHide = !!q;
  if (gaSearchHide) {
    if (map.hasLayer(gaPowerLayer)) map.removeLayer(gaPowerLayer);
    if (map.hasLayer(gaLinesLayer)) map.removeLayer(gaLinesLayer);
  } else {
    if (document.getElementById('show-ga-power').checked && !map.hasLayer(gaPowerLayer)) { gaPowerLayer.addTo(map); updateGaFilter(); }
    if (document.getElementById('show-ga-lines').checked && !map.hasLayer(gaLinesLayer)) gaLinesLayer.addTo(map);
  }
  renderLegend();
}
// --- Tabs ---
document.querySelectorAll('#sidebar-tabs button').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('#sidebar-tabs button').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById('tab-' + btn.dataset.tab).classList.add('active');
    if (btn.dataset.tab === 'dashboard') renderDashboard();
  });
});

// --- Dashboard ---
function fmtMW(v) {
  if (v >= 1000) return (v/1000).toFixed(1) + ' GW';
  return Math.round(v).toLocaleString() + ' MW';
}
function fmtMWh(v) {
  if (!v) return '—';
  if (v >= 1000) return (v/1000).toFixed(1) + ' GWh';
  return Math.round(v).toLocaleString();
}
function visibleProjects() {
  return markers.filter(m => markerLayer.hasLayer(m)).map(m => m._p);
}
function renderDashboard() {
  const vis = visibleProjects();
  const totalMW = vis.reduce((s, p) => s + (p.c || 0), 0);
  const totalMWh = vis.reduce((s, p) => s + (p.mwh || 0), 0);
  const onAemo = vis.filter(p => p.aemo).length;

  document.getElementById('dash-count').textContent = vis.length.toLocaleString();
  document.getElementById('dash-mw').textContent = fmtMW(totalMW);
  document.getElementById('dash-mwh').textContent = fmtMWh(totalMWh);
  document.getElementById('dash-aemo').textContent = onAemo.toLocaleString();

  // MW by stage horizontal bars
  const byStage = {}; DATA.stages.forEach(s => byStage[s] = 0);
  vis.forEach(p => { byStage[p.s] = (byStage[p.s]||0) + (p.c||0); });
  const maxStage = Math.max(1, ...Object.values(byStage));
  const stageEl = document.getElementById('dash-stage-bars');
  stageEl.innerHTML = DATA.stages.filter(s => byStage[s] > 0).map(s => `
    <div style="margin-bottom:6px">
      <div class="bar-label"><span style="color:${DATA.stageColour[s]};font-weight:600">${STAGE_LABEL[s]||s}</span><span>${fmtMW(byStage[s])}</span></div>
      <div class="bar"><span style="width:${(byStage[s]/maxStage*100).toFixed(1)}%;background:${DATA.stageColour[s]}"></span></div>
    </div>
  `).join('');

  // Pipeline table stage x state
  const pipeline = {};
  DATA.stages.forEach(s => { pipeline[s] = {}; DATA.states.forEach(st => pipeline[s][st] = 0); });
  vis.forEach(p => { if (pipeline[p.s] && p.st in pipeline[p.s]) pipeline[p.s][p.st] += (p.c||0); });
  const colTotal = {}; DATA.states.forEach(st => colTotal[st] = 0);
  let grand = 0;
  let html = '<thead><tr><th>Stage</th>';
  DATA.states.forEach(st => html += `<th>${st}</th>`);
  html += '<th>Total</th></tr></thead><tbody>';
  DATA.stages.forEach(s => {
    const rowTot = DATA.states.reduce((a,st) => a + pipeline[s][st], 0);
    if (rowTot === 0) return;
    html += `<tr><td><span class="stage-cell"><span class="swatch" style="background:${DATA.stageColour[s]}"></span>${STAGE_LABEL[s]||s}</span></td>`;
    DATA.states.forEach(st => {
      const v = pipeline[s][st];
      colTotal[st] += v; grand += v;
      html += `<td>${v ? Math.round(v).toLocaleString() : '—'}</td>`;
    });
    html += `<td><b>${Math.round(rowTot).toLocaleString()}</b></td></tr>`;
  });
  html += '</tbody><tfoot><tr><td>Total</td>';
  DATA.states.forEach(st => html += `<td>${Math.round(colTotal[st]).toLocaleString()}</td>`);
  html += `<td>${Math.round(grand).toLocaleString()}</td></tr></tfoot>`;
  document.getElementById('dash-pipeline').innerHTML = html;

  // MW by technology (top 10)
  const byTech = {};
  vis.forEach(p => { byTech[p.t] = (byTech[p.t]||0) + (p.c||0); });
  const techs = Object.entries(byTech).filter(([,v]) => v>0).sort((a,b)=>b[1]-a[1]).slice(0, 10);
  const maxTech = Math.max(1, ...techs.map(t=>t[1]));
  document.getElementById('dash-tech-bars').innerHTML = techs.map(([t,v]) => `
    <div style="margin-bottom:6px">
      <div class="bar-label"><span>${escapeHtml(t)}</span><span>${fmtMW(v)}</span></div>
      <div class="bar"><span style="width:${(v/maxTech*100).toFixed(1)}%;background:#475569"></span></div>
    </div>
  `).join('');
}

// re-render dashboard whenever filters change AND the dashboard tab is open
const origApply = applyFilters;
applyFilters = function() {
  origApply();
  if (document.querySelector('#sidebar-tabs button[data-tab="dashboard"].active')) renderDashboard();
};
applyFilters();

// --- Legend (rebuilt whenever layers are toggled) ---
function renderLegend() {
  if (!legendDiv) return;
  let h = '<div style="font-weight:600;margin-bottom:4px">Project stage</div>';
  DATA.stages.forEach(s => {
    const colour = DATA.stageColour[s];
    const label  = STAGE_LABEL[s] || s;
    const dot = `<span style="display:inline-flex;width:14px;height:14px;border-radius:50%;background:${colour}80;border:2px solid ${colour};flex-shrink:0"></span>`;
    h += `<div class="legend-block">${dot}<span>${label}</span></div>`;
  });
  h += '<div style="font-weight:600;margin:8px 0 4px">Transmission (kV)</div>';
  const tx = [['500','#fde047'],['330','#f59e0b'],['275','#ec4899'],['220','#1d4ed8'],['132/110','#dc2626'],['66','#7c2d12']];
  tx.forEach(([v,c]) => {
    h += `<div class="legend-block"><span style="display:inline-block;width:14px;height:3px;background:${c};margin-right:6px"></span>${v} kV</div>`;
  });
  // Technology icon legend — always shown
  const TECH_LEGEND = [
    { label: 'Solar / Solar Thermal',  img: 'sun.png'       },
    { label: 'Solar + Storage',        img: 'sun.png'       },
    { label: 'Wind',                   img: 'wind.png'      },
    { label: 'Wind + Storage',         img: 'wind.png'      },
    { label: 'Hydro',                  img: 'hydro.png'     },
    { label: 'Pumped Hydro',           img: 'pumphydro.png' },
    { label: 'Battery / Storage',      img: 'battery.png'   },
    { label: 'OCGT',                   img: 'ocgt.png'      },
    { label: 'CCGT',                   img: 'ccgt.png'      },
    { label: 'Biomass',                img: 'biomass.png'   },
    { label: 'Coal',                   img: 'coal.png'      },
    { label: 'Gas',                    img: 'ocgt.png'      },
    { label: 'Hybrid / Other',         img: null            },
  ];
  h += '<div style="font-weight:600;margin:8px 0 4px">Technology</div>';
  TECH_LEGEND.forEach(({ label, img }) => {
    const icon = img
      ? `<img src="${GA_IMG[img]}" style="width:16px;height:16px;object-fit:contain;display:block">`
      : `<div style="width:12px;height:12px;border-radius:50%;background:#8b8b8b;opacity:0.7;margin:2px"></div>`;
    h += `<div class="legend-block" style="margin:2px 0;align-items:center">
      <div style="width:18px;height:18px;display:flex;align-items:center;justify-content:center;flex-shrink:0">${icon}</div>
      <span style="margin-left:2px">${label}</span>
    </div>`;
  });
  legendDiv.innerHTML = h;
}

const legend = L.control({position:'bottomleft'});
legend.onAdd = function() {
  legendDiv = L.DomUtil.create('div');
  legendDiv.style.cssText = 'background:white;padding:8px 12px;border:1px solid #cbd5e1;border-radius:4px;box-shadow:0 1px 3px rgba(0,0,0,.15);font-size:11px;font-family:system-ui;max-height:80vh;overflow-y:auto';
  renderLegend();
  return legendDiv;
};
legend.addTo(map);
</script>
</body>
</html>
"""


if __name__ == "__main__":
    main()
