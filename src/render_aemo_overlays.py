"""
Render each AEMO state map PDF to PNG and compute a PDF->lat/lon transform.

Approach:
  1. Render the PDF at 2x DPI as PNG (PyMuPDF / fitz).
  2. Extract every text word with its page (x, y).
  3. Match against a small gazetteer of well-known towns / capitals visible on
     each state map. We need >= 2 well-separated anchors per PDF.
  4. Fit a 2-parameter axis-aligned affine: lat = a*y + b ; lon = c*x + d.
     (AEMO maps are north-up and not rotated, so we don't need shear/rotate.)
  5. Convert the PNG corners to lat/lon -> the overlay bounds for Leaflet.

Outputs:
  - assets/{state}.png            rendered PDF as raster
  - aemo_overlays.json            list of {state, image, bounds:[[s,w],[n,e]], anchors_used}
"""

from __future__ import annotations
import json
import re
from pathlib import Path
import fitz  # PyMuPDF
from statistics import median

ROOT = Path(__file__).parent.parent
AEMO_DIR = ROOT / "data" / "inputs" / "aemo_maps"
INTERMEDIATE = ROOT / "data" / "intermediate"
ASSETS = ROOT / "outputs" / "assets"
ASSETS.mkdir(parents=True, exist_ok=True)
INTERMEDIATE.mkdir(parents=True, exist_ok=True)

# Well-known town anchors for each state. Each tuple is (label, lat, lon).
# Labels must match what the PDF text extractor will see (single-word preferred;
# multi-word handled via phrase reassembly below).
ANCHORS: dict[str, list[tuple[str, float, float]]] = {
    "NSW": [
        ("Sydney",     -33.87, 151.21),
        ("Newcastle",  -32.93, 151.78),
        ("Wollongong", -34.42, 150.89),
        ("Wagga",      -35.12, 147.37),  # "Wagga Wagga" appears as 'Wagga' in the PDF tokens
        ("Tamworth",   -31.09, 150.93),
        ("Armidale",   -30.51, 151.67),
        ("Dubbo",      -32.25, 148.60),
        ("Albury",     -36.08, 146.92),
        ("Cooma",      -36.24, 149.13),
        ("Lithgow",    -33.48, 150.16),
        ("Orange",     -33.28, 149.10),
        ("Parkes",     -33.13, 148.18),
        ("Broken Hill",-31.95, 141.45),
    ],
    "VIC": [
        ("Melbourne", -37.81, 144.96),
        ("Geelong",   -38.15, 144.36),
        ("Bendigo",   -36.76, 144.28),
        ("Ballarat",  -37.56, 143.86),
        ("Mildura",   -34.21, 142.14),
        ("Horsham",   -36.72, 142.20),
        ("Shepparton",-36.38, 145.40),
        ("Wodonga",   -36.12, 146.89),
        ("Traralgon", -38.20, 146.54),
        ("Hamilton",  -37.74, 142.02),
    ],
    "QLD": [
        ("Brisbane",  -27.47, 153.03),
        ("Townsville",-19.26, 146.82),
        ("Cairns",    -16.92, 145.78),
        ("Mackay",    -21.14, 149.19),
        ("Rockhampton",-23.38,150.51),
        ("Gladstone", -23.85, 151.26),
        ("Bundaberg", -24.86, 152.35),
        ("Toowoomba", -27.56, 151.95),
        ("Mount Isa", -20.73, 139.49),
        ("Roma",      -26.57, 148.79),
        ("Longreach", -23.44, 144.25),
        ("Cooktown",  -15.47, 145.25),
    ],
    "SA": [
        ("Adelaide",       -34.93, 138.60),
        ("Whyalla",        -33.03, 137.56),
        ("Mount Gambier",  -37.83, 140.78),  # PDF may have just 'Gambier'
        ("Gambier",        -37.83, 140.78),
        ("Murray Bridge",  -35.12, 139.27),
        ("Port Lincoln",   -34.73, 135.86),
        ("Port Pirie",     -33.19, 138.02),
        ("Lincoln",        -34.73, 135.86),  # often 'Port Lincoln' shows as 'Lincoln'
        ("Lock",           -33.57, 135.75),
        ("Woomera",        -31.20, 136.83),
        ("Pimba",          -31.25, 136.81),
        ("Berri",          -34.28, 140.60),
        ("Keith",          -36.10, 140.36),
        ("Snowtown",       -33.78, 138.21),
        ("Kadina",         -33.96, 137.72),
        ("Olympic Dam",    -30.44, 136.89),
        ("Wudinna",        -33.04, 135.47),
    ],
    "TAS": [
        ("Hobart",     -42.88, 147.33),
        ("Launceston", -41.43, 147.16),
        ("Devonport",  -41.18, 146.35),
        ("Burnie",     -41.05, 145.91),
        ("Smithton",   -40.85, 145.12),
        ("Queenstown", -42.08, 145.55),
        ("Wynyard",    -40.99, 145.73),
        ("Ulverstone", -41.16, 146.18),
        ("George Town",-41.10, 146.83),
    ],
}

STATE_FROM_FILE = {"nsw": "NSW", "vic": "VIC", "qld": "QLD", "sa": "SA", "tas": "TAS"}

# Fallback geographic bounds per state — used when anchor fit is degenerate.
# (s, n, w, e)
STATE_BOUNDS = {
    "NSW": (-37.5, -28.0, 140.9, 153.7),
    "VIC": (-39.3, -33.9, 140.9, 150.0),
    "QLD": (-29.2, -10.0, 137.9, 154.0),
    "SA":  (-38.5, -25.9, 129.0, 141.1),
    "TAS": (-43.7, -39.5, 144.5, 148.5),
}


def file_state(p: Path) -> str:
    stem = p.stem.lower()
    for k, v in STATE_FROM_FILE.items():
        if k in stem:
            return v
    return ""


def extract_text_positions(pdf_path: Path) -> list[dict]:
    """Word-level positions for a single-page PDF."""
    doc = fitz.open(pdf_path)
    page = doc[0]
    words = []
    for w in page.get_text("words"):  # (x0, y0, x1, y1, "word", block, line, idx)
        x0, y0, x1, y1, txt = w[0], w[1], w[2], w[3], w[4]
        words.append({
            "text": txt,
            "x": (x0 + x1) / 2,
            "y": (y0 + y1) / 2,
        })
    doc.close()
    return words


def reconstruct_phrases(words: list[dict], max_gap_x: float = 12, max_gap_y: float = 3) -> list[dict]:
    """Cheap phrase rebuilder: cluster horizontally adjacent words on same baseline."""
    words = sorted(words, key=lambda w: (round(w["y"]/2)*2, w["x"]))
    out = []
    cur = None
    for w in words:
        if cur is None:
            cur = {"text": w["text"], "x": w["x"], "y": w["y"], "x0": w["x"], "x1": w["x"]}
            continue
        if (abs(w["y"] - cur["y"]) <= max_gap_y and w["x"] - cur["x1"] <= max_gap_x):
            cur["text"] = cur["text"] + " " + w["text"]
            cur["x1"] = w["x"]
            cur["x"] = (cur["x0"] + cur["x1"]) / 2
            continue
        out.append(cur)
        cur = {"text": w["text"], "x": w["x"], "y": w["y"], "x0": w["x"], "x1": w["x"]}
    if cur is not None:
        out.append(cur)
    return out


def find_anchors(state: str, phrases: list[dict]) -> list[tuple[str, float, float, float, float]]:
    """Return list of (label, lat, lon, page_x, page_y) for anchors found on the page."""
    found = []
    seen_labels = set()
    for label, lat, lon in ANCHORS.get(state, []):
        ll = label.lower()
        candidates = [p for p in phrases if p["text"].lower() == ll]
        if not candidates:
            candidates = [p for p in phrases if p["text"].lower().startswith(ll + " ")]
        if not candidates:
            continue
        # Some labels (e.g. 'Sydney') can appear multiple times across the map; pick the
        # one whose y is most consistent with other anchors. For now, take median position.
        mx = median(c["x"] for c in candidates)
        my = median(c["y"] for c in candidates)
        if label in seen_labels:
            continue
        seen_labels.add(label)
        found.append((label, lat, lon, mx, my))
    return found


def _lsq(xs, ys):
    n = len(xs)
    if n < 2: return None
    sx = sum(xs); sy = sum(ys); sxx = sum(x*x for x in xs); sxy = sum(x*y for x,y in zip(xs,ys))
    denom = (n*sxx - sx*sx)
    if abs(denom) < 1e-9:
        return None
    slope = (n*sxy - sx*sy) / denom
    intercept = (sy - slope*sx) / n
    return slope, intercept


def fit_axis_aligned(anchors: list[tuple[str, float, float, float, float]]
                    ) -> tuple[tuple[float, float, float, float], list[tuple[str, float, float, float, float]]] | None:
    """Fit lat = a*y + b ; lon = c*x + d using least squares with simple outlier rejection.

    Drops anchors whose residual exceeds 2.5 * median residual (after a first-pass fit),
    then refits. Requires >=2 anchors after rejection and >= some range in both x and y.
    Returns ((a,b,c,d), inliers) or None.
    """
    if len(anchors) < 2:
        return None

    def fit(anchors):
        ys = [a[4] for a in anchors]
        xs = [a[3] for a in anchors]
        lats = [a[1] for a in anchors]
        lons = [a[2] for a in anchors]
        lat_fit = _lsq(ys, lats)
        lon_fit = _lsq(xs, lons)
        if not lat_fit or not lon_fit: return None
        a, b = lat_fit; c, d = lon_fit
        return a, b, c, d

    f = fit(anchors)
    if not f: return None
    if len(anchors) >= 4:
        a, b, c, d = f
        residuals = []
        for lbl, la, lo, x, y in anchors:
            r = max(abs(a*y + b - la), abs(c*x + d - lo))
            residuals.append((r, (lbl, la, lo, x, y)))
        residuals.sort()
        med = residuals[len(residuals)//2][0]
        threshold = max(0.3, 2.5 * med)
        inliers = [t for r, t in residuals if r <= threshold]
        if len(inliers) >= 3:
            f = fit(inliers)
            if not f: return None
            return f, inliers
    return f, anchors


def render_pdf_png(pdf_path: Path, out_png: Path, scale: float = 2.0) -> tuple[int, int, float, float]:
    """Render single-page PDF to PNG. Returns (img_w, img_h, page_w, page_h)."""
    doc = fitz.open(pdf_path)
    page = doc[0]
    mat = fitz.Matrix(scale, scale)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    pix.save(str(out_png))
    pw, ph = page.rect.width, page.rect.height
    doc.close()
    return pix.width, pix.height, pw, ph


def main():
    overlays = []
    for pdf_path in sorted(AEMO_DIR.glob("*-map.pdf")):
        state = file_state(pdf_path)
        if not state:
            continue
        print(f"\n== {pdf_path.name}  state={state}")

        # extract text + find anchors
        words = extract_text_positions(pdf_path)
        phrases = reconstruct_phrases(words)
        anchors = find_anchors(state, phrases)
        print(f"   {len(words)} words, {len(phrases)} phrases, {len(anchors)} anchors:")
        for lbl, la, lo, x, y in anchors:
            print(f"     {lbl:20s} ({x:.0f},{y:.0f}) -> ({la:.3f},{lo:.3f})")

        if len(anchors) < 2:
            print("   SKIP: need at least 2 anchors")
            continue

        fitres = fit_axis_aligned(anchors)
        if not fitres:
            print("   SKIP: fit failed")
            continue
        (a, b, c, d), inliers = fitres
        if len(inliers) < len(anchors):
            print(f"   outlier rejection: {len(anchors)}->{len(inliers)} inliers")

        # render PNG
        out_png = ASSETS / f"{state.lower()}.png"
        img_w, img_h, page_w, page_h = render_pdf_png(pdf_path, out_png)
        print(f"   rendered {out_png.name} {img_w}x{img_h} (page {page_w:.0f}x{page_h:.0f})")

        # corners
        n_lat = a*0 + b
        s_lat = a*page_h + b
        w_lon = c*0 + d
        e_lon = c*page_w + d
        south, north = sorted([n_lat, s_lat])
        west, east = sorted([w_lon, e_lon])

        # sanity: if extrapolated bounds are degenerate, fall back to known state bbox
        FB_SOUTH, FB_NORTH, FB_WEST, FB_EAST = STATE_BOUNDS[state]
        lat_span = north - south
        lon_span = east - west
        fb_lat = FB_NORTH - FB_SOUTH
        fb_lon = FB_EAST - FB_WEST
        used_fallback = False
        if lat_span < 0.3 * fb_lat or lon_span < 0.3 * fb_lon or lat_span > 3 * fb_lat or lon_span > 3 * fb_lon:
            print(f"   bounds look bad (lat_span={lat_span:.2f} lon_span={lon_span:.2f}) — using fallback state bbox")
            south, north, west, east = FB_SOUTH, FB_NORTH, FB_WEST, FB_EAST
            used_fallback = True
        bounds = [[south, west], [north, east]]
        print(f"   bounds: S {south:.2f}  N {north:.2f}  W {west:.2f}  E {east:.2f}")

        # residuals at inliers
        residuals = []
        for lbl, la, lo, x, y in inliers:
            pred_lat = a*y + b
            pred_lon = c*x + d
            residuals.append((lbl, pred_lat - la, pred_lon - lo))
        max_res = max(max(abs(r[1]), abs(r[2])) for r in residuals) if residuals else None
        if max_res is not None:
            print(f"   max anchor residual: {max_res:.3f} degrees (~{max_res*111:.1f} km)")

        overlays.append({
            "state": state,
            "image": f"assets/{state.lower()}.png",
            "bounds": bounds,
            "anchors_used": [{"label": l, "lat": la, "lon": lo, "x": x, "y": y} for l, la, lo, x, y in inliers],
            "max_residual_deg": max_res,
            "transform": {"a": a, "b": b, "c": c, "d": d},
            "page_w": page_w, "page_h": page_h,
            "img_w": img_w, "img_h": img_h,
            "used_fallback_bounds": used_fallback,
        })

    out = INTERMEDIATE / "aemo_overlays.json"
    out.write_text(json.dumps(overlays, indent=2), encoding="utf-8")
    print(f"\nWrote {out} with {len(overlays)} overlays")


if __name__ == "__main__":
    main()
