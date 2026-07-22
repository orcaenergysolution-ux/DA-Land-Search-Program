"""ICP-style densification of warp anchors using transmission-line geometry.

For each state:
  1. Extract AEMO PDF transmission polylines, classified by stroke colour
     -> voltage.
  2. Sample dense points along each polyline (page coords).
  3. Using current TPS (from aemo_overlays.json), project each sample to real
     (lat, lon).
  4. For each projected point, find the nearest OSM transmission line of the
     same voltage class within a tolerance, and snap to it.
  5. The pair (page_xy, snapped_lonlat) becomes a new anchor.
  6. Refit TPS with the densified anchor set.
  7. Iterate 2-3 times for convergence.
  8. Re-warp the PNG and remap markers (same as warp_aemo_pdfs.py).

Writes back to aemo_overlays.json with the new anchors + transform, then
re-runs the raster warp.
"""
from __future__ import annotations
import json
import math
from pathlib import Path
import numpy as np
import fitz
from scipy.interpolate import RBFInterpolator
from shapely.geometry import LineString, Point
from shapely.strtree import STRtree

ROOT = Path(__file__).parent.parent
INTERMEDIATE = ROOT / "data" / "intermediate"
PDF_DIR = ROOT / "data" / "inputs" / "aemo_maps"
OVERLAYS = INTERMEDIATE / "aemo_overlays.json"
TX_PATH = INTERMEDIATE / "transmission_lines.geojson"

STATE_PDF_STEM = {"NSW":"nsw-map","VIC":"vic-map","QLD":"qld-map","SA":"sa-map","TAS":"tas-map"}

# AEMO PDF stroke colour -> voltage (kV). Tolerant matching.
def colour_to_voltage(rgb: tuple[float, float, float]) -> float | None:
    if rgb is None or len(rgb) < 3:
        return None
    r, g, b = rgb[:3]
    # yellow 500
    if r > 0.85 and g > 0.85 and b < 0.3: return 500
    # orange 330
    if r > 0.85 and 0.4 < g < 0.7 and b < 0.25: return 330
    # pink/magenta 275
    if r > 0.85 and g < 0.3 and b > 0.4: return 275
    # red 132/110
    if r > 0.75 and g < 0.25 and b < 0.3: return 132
    # bright blue 220
    if r < 0.15 and g < 0.15 and b > 0.85: return 220
    # darker blue (sometimes used for 220)
    if r < 0.15 and 0.35 < g < 0.55 and 0.65 < b < 0.85: return 220
    # brown 66
    if 0.35 < r < 0.55 and 0.15 < g < 0.35 and b < 0.15: return 66
    # green DC link - ignore for now
    return None


def extract_pdf_polylines(pdf_path: Path) -> list[dict]:
    """Return list of {voltage, page_pts: [(x, y), ...]}."""
    doc = fitz.open(pdf_path)
    page = doc[0]
    out = []
    for d in page.get_drawings():
        v = colour_to_voltage(d.get("color") or ())
        if v is None or v < 66:
            continue
        items = d.get("items", [])
        # Build polyline from segment chain
        pts: list[tuple[float, float]] = []
        for it in items:
            if not it or len(it) < 2: continue
            op = it[0]
            if op == "l":  # line
                p1, p2 = it[1], it[2]
                p1 = (p1.x, p1.y) if hasattr(p1, "x") else tuple(p1)
                p2 = (p2.x, p2.y) if hasattr(p2, "x") else tuple(p2)
                if not pts or pts[-1] != p1:
                    pts.append(p1)
                pts.append(p2)
            elif op == "c":  # curve - take endpoints
                p4 = it[-1]
                p4 = (p4.x, p4.y) if hasattr(p4, "x") else tuple(p4)
                pts.append(p4)
            elif op == "re":  # rect - skip
                continue
        if len(pts) >= 2:
            out.append({"voltage": v, "page_pts": pts})
    doc.close()
    return out


def sample_polyline(pts: list[tuple[float, float]], every: float = 6.0) -> list[tuple[float, float]]:
    """Sample points along a polyline (page units) every `every` units."""
    if len(pts) < 2: return list(pts)
    out = [pts[0]]
    carry = 0.0
    for i in range(1, len(pts)):
        x1, y1 = pts[i-1]; x2, y2 = pts[i]
        dx, dy = x2-x1, y2-y1
        seg_len = math.hypot(dx, dy)
        if seg_len < 1e-6: continue
        dist = carry
        while dist + every <= seg_len:
            dist += every
            t = dist / seg_len
            out.append((x1 + t*dx, y1 + t*dy))
        carry = (seg_len - dist) if dist > 0 else carry + seg_len
        if carry >= every:
            carry = 0
    if out[-1] != pts[-1]: out.append(pts[-1])
    return out


def build_osm_index(tx_features: list[dict], state: str) -> dict[int, tuple[STRtree, list[LineString]]]:
    """Group OSM transmission lines by voltage class, return STRtree per voltage."""
    by_v: dict[int, list[LineString]] = {}
    for f in tx_features:
        props = f.get("properties", {})
        v = props.get("voltage_kv") or 0
        st = props.get("state", "")
        # Filter to this state's region (state field may be 'NSW_N' etc)
        full = state
        if not (st == full or st.startswith(full + "_")):
            continue
        # snap to nearest voltage class
        cls = nearest_voltage_class(v)
        if cls is None: continue
        coords = f["geometry"]["coordinates"]
        if len(coords) < 2: continue
        by_v.setdefault(cls, []).append(LineString(coords))
    return {v: (STRtree(lines), lines) for v, lines in by_v.items() if lines}


def nearest_voltage_class(v: float) -> int | None:
    if v is None: return None
    if v >= 450: return 500
    if v >= 300: return 330
    if v >= 250: return 275
    if v >= 180: return 220
    if v >= 100: return 132
    if v >= 50:  return 66
    return None


def make_tps(anchors_real: np.ndarray, anchors_page: np.ndarray, smoothing: float = 2.0):
    """Fit forward (page->real) and inverse (real->page) TPS pairs."""
    rbf_lon = RBFInterpolator(anchors_page, anchors_real[:, 0], kernel="thin_plate_spline", smoothing=smoothing)
    rbf_lat = RBFInterpolator(anchors_page, anchors_real[:, 1], kernel="thin_plate_spline", smoothing=smoothing)
    return rbf_lon, rbf_lat


def process_state(state: str, overlay: dict, tx_features: list[dict],
                  snap_tol_deg: float = 0.5, iters: int = 3) -> dict:
    pdf = PDF_DIR / f"{STATE_PDF_STEM[state]}.pdf"
    if not pdf.exists():
        print(f"  {state}: missing PDF"); return overlay

    base_anchors = overlay.get("anchors_used", [])
    if len(base_anchors) < 4:
        print(f"  {state}: too few base anchors"); return overlay

    print(f"\n=== {state} === starting with {len(base_anchors)} anchors")

    # Extract AEMO PDF polylines
    polys = extract_pdf_polylines(pdf)
    by_v: dict[int, list[list[tuple[float, float]]]] = {}
    for p in polys:
        by_v.setdefault(p["voltage"], []).append(p["page_pts"])
    print("  AEMO PDF polylines by voltage:",
          {v: sum(len(pp) for pp in p) for v, p in sorted(by_v.items())},
          "total polylines:", sum(len(p) for p in by_v.values()))

    # Build OSM index
    osm_idx = build_osm_index(tx_features, state)
    print("  OSM lines by voltage in state:",
          {v: len(lines) for v, (tree, lines) in sorted(osm_idx.items())})

    if not osm_idx:
        print("  no OSM lines for state; aborting")
        return overlay

    # Initialise anchors
    real = np.array([[a["lon"], a["lat"]] for a in base_anchors])
    page = np.array([[a["x"], a["y"]] for a in base_anchors])

    for it in range(iters):
        rbf_lon, rbf_lat = make_tps(real, page)

        # Sample AEMO polylines, project to real, snap to OSM
        new_anchors: list[tuple[float, float, float, float]] = []  # (lon, lat, px, py)
        for v, polylines in by_v.items():
            if v not in osm_idx:
                # fallback to nearest class with OSM data
                cands = sorted(osm_idx.keys(), key=lambda x: abs(x - v))
                if not cands: continue
                ov = cands[0]
            else:
                ov = v
            tree, lines = osm_idx[ov]
            for poly in polylines:
                sampled = sample_polyline(poly, every=6.0)
                if not sampled: continue
                pts = np.array(sampled)
                pred_lon = rbf_lon(pts); pred_lat = rbf_lat(pts)
                for i, (px, py) in enumerate(sampled):
                    plon = float(pred_lon[i]); plat = float(pred_lat[i])
                    pt = Point(plon, plat)
                    # candidates within tolerance
                    cand_idx = tree.query(pt.buffer(snap_tol_deg))
                    if len(cand_idx) == 0: continue
                    best_d = float("inf"); best_pt = None
                    for ci in cand_idx:
                        line = lines[ci]
                        d = line.distance(pt)
                        if d < best_d:
                            best_d = d
                            best_pt = line.interpolate(line.project(pt))
                    if best_pt is None: continue
                    if best_d > snap_tol_deg: continue
                    new_anchors.append((best_pt.x, best_pt.y, px, py))

        print(f"  iter {it+1}: {len(new_anchors)} new snap anchors from AEMO/OSM line matching")
        if not new_anchors: break

        # Decimate to avoid redundant anchors crowding one segment.
        # Bin by page (x, y) at coarse grid and keep one per bin.
        bin_size = 5.0
        seen = {}
        for lon, lat, px, py in new_anchors:
            key = (int(px / bin_size), int(py / bin_size))
            if key not in seen:
                seen[key] = (lon, lat, px, py)
        decimated = list(seen.values())
        print(f"    decimated to {len(decimated)} anchors after spatial binning")

        # Combine with base anchors
        all_real = np.vstack([real[:len(base_anchors)], np.array([[d[0], d[1]] for d in decimated])])
        all_page = np.vstack([page[:len(base_anchors)], np.array([[d[2], d[3]] for d in decimated])])
        real, page = all_real, all_page
        print(f"    total anchors: {len(real)}")

    # Save expanded anchor list
    new_anchor_list = []
    for i in range(len(real)):
        if i < len(base_anchors):
            new_anchor_list.append(base_anchors[i])
        else:
            new_anchor_list.append({
                "label": "icp_snap", "lat": float(real[i, 1]), "lon": float(real[i, 0]),
                "x": float(page[i, 0]), "y": float(page[i, 1]), "source": "icp"
            })

    # Final fit metrics
    rbf_lon, rbf_lat = make_tps(real, page)
    pred_lon = rbf_lon(page); pred_lat = rbf_lat(page)
    err = np.sqrt((pred_lon - real[:, 0])**2 + (pred_lat - real[:, 1])**2)
    median_km = float(np.median(err) * 111)
    max_km = float(np.max(err) * 111)
    print(f"  final fit: {len(real)} anchors  median residual {median_km:.1f} km  max {max_km:.1f} km")

    overlay = dict(overlay)
    overlay["anchors_used"] = new_anchor_list
    overlay["icp_anchors_added"] = len(new_anchor_list) - len(base_anchors)
    return overlay


def main():
    overlays = json.loads(OVERLAYS.read_text(encoding="utf-8"))
    tx = json.loads(TX_PATH.read_text(encoding="utf-8"))["features"]
    print(f"Loaded {len(tx)} OSM transmission features")
    new = []
    for ov in overlays:
        st = ov.get("state")
        if st in STATE_PDF_STEM:
            new.append(process_state(st, ov, tx))
        else:
            new.append(ov)
    OVERLAYS.write_text(json.dumps(new, indent=2), encoding="utf-8")
    print(f"\nWrote {OVERLAYS}")


if __name__ == "__main__":
    main()
