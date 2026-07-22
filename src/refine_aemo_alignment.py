"""Refine AEMO PDF -> lat/lon affine transforms using OSM substations as anchors.

For each state PDF:
  1. Extract every word with its page (x, y) via PyMuPDF.
  2. Reassemble phrases.
  3. For each OSM substation in the state, look for its (or a variant of its)
     name in the PDF's phrase list. If found, that pairing gives us a new anchor:
     (page_x, page_y) <-> (real_lat, real_lon).
  4. Combine with the existing hand-coded town anchors.
  5. Fit affine with median-absolute-deviation outlier rejection.
  6. Recompute the PNG bounds and update aemo_overlays.json.

Honest note: AEMO maps are schematic. They reposition labels for readability.
A single affine cannot achieve 1-to-1 alignment with real geography. Adding
more anchors lowers the residual; it doesn't eliminate it.
"""
from __future__ import annotations
import json
import re
from pathlib import Path
from statistics import median
import fitz

ROOT = Path(__file__).parent.parent
INTERMEDIATE = ROOT / "data" / "intermediate"
PDF_DIR = ROOT / "data" / "inputs" / "aemo_maps"
OVERLAYS_PATH = INTERMEDIATE / "aemo_overlays.json"
SUBS_PATH = INTERMEDIATE / "substations.geojson"
OUT_OVERLAYS = INTERMEDIATE / "aemo_overlays.json"  # in-place

# Per-state PDF stem -> region
STATE_PDFS = {"NSW": "nsw-map", "VIC": "vic-map", "QLD": "qld-map",
              "SA": "sa-map", "TAS": "tas-map"}

# Existing town anchors (from render_aemo_overlays.py) — kept as a backbone
TOWN_ANCHORS: dict[str, list[tuple[str, float, float]]] = {
    "NSW": [("Sydney",-33.87,151.21),("Newcastle",-32.93,151.78),("Wollongong",-34.42,150.89),
            ("Wagga Wagga",-35.12,147.37),("Tamworth",-31.09,150.93),("Armidale",-30.51,151.67),
            ("Dubbo",-32.25,148.60),("Albury",-36.08,146.92),("Cooma",-36.24,149.13),
            ("Lithgow",-33.48,150.16),("Orange",-33.28,149.10),("Parkes",-33.13,148.18),
            ("Broken Hill",-31.95,141.45)],
    "VIC": [("Melbourne",-37.81,144.96),("Geelong",-38.15,144.36),("Bendigo",-36.76,144.28),
            ("Ballarat",-37.56,143.86),("Mildura",-34.21,142.14),("Horsham",-36.72,142.20),
            ("Shepparton",-36.38,145.40),("Wodonga",-36.12,146.89),("Traralgon",-38.20,146.54),
            ("Hamilton",-37.74,142.02)],
    "QLD": [("Brisbane",-27.47,153.03),("Townsville",-19.26,146.82),("Cairns",-16.92,145.78),
            ("Mackay",-21.14,149.19),("Rockhampton",-23.38,150.51),("Gladstone",-23.85,151.26),
            ("Bundaberg",-24.86,152.35),("Toowoomba",-27.56,151.95),("Roma",-26.57,148.79),
            ("Longreach",-23.44,144.25),("Cooktown",-15.47,145.25)],
    "SA":  [("Adelaide",-34.93,138.60),("Whyalla",-33.03,137.56),("Mount Gambier",-37.83,140.78),
            ("Murray Bridge",-35.12,139.27),("Port Pirie",-33.19,138.02),("Port Lincoln",-34.73,135.86),
            ("Lock",-33.57,135.75),("Woomera",-31.20,136.83),("Pimba",-31.25,136.81),
            ("Berri",-34.28,140.60),("Keith",-36.10,140.36),("Snowtown",-33.78,138.21),
            ("Kadina",-33.96,137.72),("Olympic Dam",-30.44,136.89),("Wudinna",-33.04,135.47)],
    "TAS": [("Hobart",-42.88,147.33),("Launceston",-41.43,147.16),("Devonport",-41.18,146.35),
            ("Burnie",-41.05,145.91),("Smithton",-40.85,145.12),("Queenstown",-42.08,145.55),
            ("Wynyard",-40.99,145.73),("Ulverstone",-41.16,146.18),("George Town",-41.10,146.83)],
}


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]+", " ", s.lower())).strip()


def extract_phrases(pdf: Path) -> list[dict]:
    doc = fitz.open(pdf)
    page = doc[0]
    words = []
    for w in page.get_text("words"):
        x0, y0, x1, y1, txt = w[0], w[1], w[2], w[3], w[4]
        words.append({"text": txt, "x": (x0+x1)/2, "y": (y0+y1)/2, "x0": x0, "x1": x1})
    doc.close()
    words.sort(key=lambda w: (round(w["y"]/2)*2, w["x"]))
    phrases = []
    cur = None
    for w in words:
        if cur is None: cur = {**w, "text": w["text"]}; continue
        if abs(w["y"] - cur["y"]) <= 3 and w["x0"] - cur["x1"] <= 12:
            cur["text"] += " " + w["text"]; cur["x1"] = w["x1"]; cur["x"] = (w["x"] + cur["x"]) / 2
        else:
            phrases.append(cur); cur = {**w, "text": w["text"]}
    if cur: phrases.append(cur)
    return phrases


def find_anchors(state: str, phrases: list[dict], osm_subs: list[dict]) -> list[tuple[str, float, float, float, float, str]]:
    """Return list of (name, real_lat, real_lon, page_x, page_y, source)."""
    # build index: normalized phrase text -> position(s)
    phrase_index: dict[str, list[dict]] = {}
    for p in phrases:
        n = norm(p["text"])
        if n: phrase_index.setdefault(n, []).append(p)
    # also allow partial matches: full phrase contains anchor text as a substring
    all_phrases_normed = [(norm(p["text"]), p) for p in phrases]

    found: list[tuple[str, float, float, float, float, str]] = []
    seen_names: set[str] = set()

    def add(name: str, lat: float, lon: float, p: dict, src: str) -> None:
        key = name.lower()
        if key in seen_names: return
        seen_names.add(key)
        found.append((name, lat, lon, p["x"], p["y"], src))

    # 1. Town anchors (high-trust)
    for name, lat, lon in TOWN_ANCHORS.get(state, []):
        n = norm(name)
        if n in phrase_index:
            add(name, lat, lon, phrase_index[n][0], "town")
            continue
        # fallback: any phrase ENDING WITH or STARTING WITH this name
        for ph_n, ph in all_phrases_normed:
            if ph_n == n or ph_n.startswith(n + " ") or ph_n.endswith(" " + n):
                add(name, lat, lon, ph, "town")
                break

    # 2. OSM substations
    for s in osm_subs:
        nm = (s["properties"].get("name") or "").strip()
        if not nm or len(nm) < 3: continue
        n = norm(nm)
        # try exact match in phrase index
        if n in phrase_index:
            add(nm, s["geometry"]["coordinates"][1], s["geometry"]["coordinates"][0],
                phrase_index[n][0], "osm")
            continue
        # try matching with common suffixes/prefixes stripped
        n_stripped = re.sub(r"\b(substation|terminal|switching\s*station|sw\s*stn|ts|zs|bsp)\b",
                            "", n).strip()
        if n_stripped and len(n_stripped) >= 4 and n_stripped in phrase_index:
            add(nm, s["geometry"]["coordinates"][1], s["geometry"]["coordinates"][0],
                phrase_index[n_stripped][0], "osm")

    return found


def fit(anchors, drop_threshold_factor=3.0):
    """Axis-aligned least squares with iterative outlier rejection.

    Returns (a, b, c, d), inliers_used.
    """
    def lsq(xs, ys):
        n = len(xs); sx = sum(xs); sy = sum(ys); sxx = sum(x*x for x in xs); sxy = sum(x*y for x,y in zip(xs,ys))
        denom = n*sxx - sx*sx
        if abs(denom) < 1e-9: return None
        slope = (n*sxy - sx*sy) / denom
        intercept = (sy - slope*sx) / n
        return slope, intercept

    def do_fit(a):
        ys = [r[4] for r in a]; xs = [r[3] for r in a]
        lats = [r[1] for r in a]; lons = [r[2] for r in a]
        lat_fit = lsq(ys, lats); lon_fit = lsq(xs, lons)
        if not lat_fit or not lon_fit: return None
        return (lat_fit[0], lat_fit[1], lon_fit[0], lon_fit[1])

    current = anchors
    for _ in range(4):
        if len(current) < 3: break
        params = do_fit(current)
        if not params: return None, current
        a, b, c, d = params
        resids = []
        for r in current:
            pred_lat = a*r[4] + b; pred_lon = c*r[3] + d
            resids.append(max(abs(pred_lat - r[1]), abs(pred_lon - r[2])))
        med = median(resids); mad = median([abs(r - med) for r in resids]) or 0.05
        threshold = max(0.4, med + drop_threshold_factor * mad)
        keep = [r for r, res in zip(current, resids) if res <= threshold]
        if len(keep) == len(current):
            break
        current = keep
    params = do_fit(current)
    return params, current


def main():
    overlays = json.loads(OVERLAYS_PATH.read_text(encoding="utf-8"))
    subs = json.loads(SUBS_PATH.read_text(encoding="utf-8"))["features"]
    subs_by_state: dict[str, list[dict]] = {}
    for s in subs:
        st = s["properties"].get("state", "")
        # state in geojson is the chunk name (NSW_N etc) - map back
        for full in ["NSW","VIC","QLD","SA","TAS"]:
            if st == full or st.startswith(full + "_"):
                subs_by_state.setdefault(full, []).append(s)

    for ov in overlays:
        state = ov["state"]
        pdf = PDF_DIR / f"{STATE_PDFS[state]}.pdf"
        if not pdf.exists():
            print(f"  {state}: missing PDF")
            continue
        phrases = extract_phrases(pdf)
        anchors = find_anchors(state, phrases, subs_by_state.get(state, []))
        print(f"\n{state}: {len(anchors)} anchors ({sum(1 for a in anchors if a[5]=='town')} towns + {sum(1 for a in anchors if a[5]=='osm')} osm)")
        if len(anchors) < 3:
            print(f"  too few anchors")
            continue
        params, inliers = fit(anchors)
        if not params:
            print(f"  fit failed")
            continue
        a, b, c, d = params
        residuals = []
        for r in inliers:
            pred_lat = a*r[4] + b; pred_lon = c*r[3] + d
            residuals.append(max(abs(pred_lat - r[1]), abs(pred_lon - r[2])))
        max_res = max(residuals); med_res = median(residuals)
        page_w, page_h = ov["page_w"], ov["page_h"]
        # new bounds from corner transform
        n_lat = a*0 + b; s_lat = a*page_h + b
        w_lon = c*0 + d; e_lon = c*page_w + d
        south, north = sorted([n_lat, s_lat]); west, east = sorted([w_lon, e_lon])
        old_max_res = ov.get("max_residual_deg") or 99
        print(f"  inliers={len(inliers)}/{len(anchors)}  median={med_res*111:.0f} km  max={max_res*111:.0f} km (was {old_max_res*111:.0f} km)")
        ov["transform"] = {"a": a, "b": b, "c": c, "d": d}
        ov["bounds"] = [[south, west], [north, east]]
        ov["max_residual_deg"] = max_res
        ov["median_residual_deg"] = med_res
        ov["anchors_used"] = [{"label": r[0], "lat": r[1], "lon": r[2],
                               "x": r[3], "y": r[4], "source": r[5]} for r in inliers]
        ov["used_fallback_bounds"] = False

    OUT_OVERLAYS.write_text(json.dumps(overlays, indent=2), encoding="utf-8")
    print(f"\nWrote {OUT_OVERLAYS}")


if __name__ == "__main__":
    main()
