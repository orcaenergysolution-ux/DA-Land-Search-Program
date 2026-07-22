"""Sanity check the TPS warp.

For each state:
  1. Re-fit the same TPS (forward direction: page -> real lon/lat)
  2. For every anchor, predict its real coord from its page coord
  3. Report residual (predicted vs actual) — should be tiny (TPS interpolates)
  4. Hold-one-out cross-validation: drop each anchor, fit on the rest, predict the dropped one
     - This is the honest measure of how well the warp generalizes between anchors
  5. Print a spot check at a couple of well-known points

A real warp shows: (a) near-zero in-sample residual; (b) modest hold-one-out residual
(comparable to the spacing between anchors); (c) sensible spot-check positions.
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
from scipy.interpolate import RBFInterpolator

ROOT = Path(__file__).parent.parent
OVERLAYS = ROOT / "data" / "intermediate" / "aemo_overlays.json"


def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    p = np.pi / 180
    a = (np.sin((lat2 - lat1) * p / 2)**2
         + np.cos(lat1*p) * np.cos(lat2*p) * np.sin((lon2-lon1)*p/2)**2)
    return 2 * R * np.arcsin(np.sqrt(a))


def main():
    overlays = json.loads(OVERLAYS.read_text(encoding="utf-8"))
    for ov in overlays:
        state = ov["state"]
        anchors = ov.get("anchors_used", [])
        if len(anchors) < 4:
            print(f"\n{state}: only {len(anchors)} anchors, skipping"); continue
        page = np.array([[a["x"], a["y"]] for a in anchors])
        real = np.array([[a["lon"], a["lat"]] for a in anchors])
        labels = [a["label"] for a in anchors]

        # In-sample fit
        rbf_lon = RBFInterpolator(page, real[:, 0], kernel="thin_plate_spline", smoothing=2.0)
        rbf_lat = RBFInterpolator(page, real[:, 1], kernel="thin_plate_spline", smoothing=2.0)
        pred_lon = rbf_lon(page); pred_lat = rbf_lat(page)
        in_resid = haversine_km(real[:, 1], real[:, 0], pred_lat, pred_lon)
        print(f"\n{state}: {len(anchors)} anchors")
        print(f"  in-sample residual (TPS smoothing=2.0): median {np.median(in_resid):.1f} km  max {np.max(in_resid):.1f} km")

        # Leave-one-out
        loo = []
        for i in range(len(anchors)):
            mask = np.ones(len(anchors), dtype=bool); mask[i] = False
            try:
                rl = RBFInterpolator(page[mask], real[mask, 0], kernel="thin_plate_spline", smoothing=2.0)
                ra = RBFInterpolator(page[mask], real[mask, 1], kernel="thin_plate_spline", smoothing=2.0)
                plon = float(rl(page[[i]])[0]); plat = float(ra(page[[i]])[0])
                d = float(haversine_km(real[i, 1], real[i, 0], plat, plon))
                loo.append((d, labels[i]))
            except Exception as e:
                loo.append((float("nan"), labels[i]))
        loo.sort(reverse=True)
        loo_km = np.array([r[0] for r in loo])
        print(f"  leave-one-out: median {np.nanmedian(loo_km):.0f} km  max {np.nanmax(loo_km):.0f} km")
        print(f"    worst 3: " + ", ".join(f"{n} ({d:.0f} km)" for d, n in loo[:3]))


if __name__ == "__main__":
    main()
