"""
Apply MMS DUDETAIL capacity updates to projects.json.

Reads outputs/duid_capacity_review.csv and for every row that has a
mms_max_cap_mw value, overwrites the project's capacity_mw.
Where mms_storage_mwh is also present, overwrites storage_mwh.

Only updates NEM-sourced projects (those with a duid). Does NOT touch
KCI-only, CER, or DA-only projects.

Usage:
    python scripts/apply_duid_capacity.py
"""
from __future__ import annotations
import csv
import json
from pathlib import Path

ROOT       = Path(__file__).resolve().parent.parent
REVIEW_CSV = ROOT / "outputs" / "duid_capacity_review.csv"
PROJECTS   = ROOT / "data" / "intermediate" / "projects.json"


def main():
    if not REVIEW_CSV.exists():
        print(f"ERROR: {REVIEW_CSV} not found — run review_duid_capacity.py first.")
        return

    # Load review CSV
    review_rows = list(csv.DictReader(REVIEW_CSV.open(encoding="utf-8")))

    # Build lookup: (site_name_lower, state) -> {mms_max_cap, mms_storage_mwh}
    # Where a site appears more than once (different unit_status), keep the
    # entry with the largest mms_max_cap (most complete record).
    lookup: dict[tuple, dict] = {}
    for r in review_rows:
        mms_cap = r.get("mms_max_cap_mw", "").strip()
        if not mms_cap:
            continue
        key = (r["site_name"].strip().lower(), r["state"].strip())
        mms_cap_f = float(mms_cap)
        existing = lookup.get(key)
        if existing is None or mms_cap_f > existing["mms_cap"]:
            mms_storage = r.get("mms_storage_mwh", "").strip()
            lookup[key] = {
                "mms_cap":     mms_cap_f,
                "mms_storage": float(mms_storage) if mms_storage else None,
            }

    print(f"Review rows with MMS capacity: {len(lookup)}")

    # Load and update projects
    projects = json.loads(PROJECTS.read_text(encoding="utf-8"))

    cap_updated     = 0
    storage_updated = 0
    not_found       = 0

    for p in projects:
        if "NEM" not in (p.get("source") or ""):
            continue
        key = (p.get("site_name", "").strip().lower(), p.get("state", "").strip())
        rec = lookup.get(key)
        if not rec:
            continue

        old_cap = p.get("capacity_mw")
        new_cap = rec["mms_cap"]
        if old_cap != new_cap:
            p["capacity_mw"] = round(new_cap, 2)
            cap_updated += 1
            print(f"  MW  {p['site_name']}: {old_cap} -> {new_cap}")

        if rec["mms_storage"] is not None:
            old_mwh = p.get("storage_mwh")
            new_mwh = round(rec["mms_storage"], 2)
            if old_mwh != new_mwh:
                p["storage_mwh"] = new_mwh
                storage_updated += 1
                print(f"  MWh {p['site_name']}: {old_mwh} -> {new_mwh}")

    print(f"\nUpdated capacity_mw:  {cap_updated} projects")
    print(f"Updated storage_mwh:  {storage_updated} projects")

    PROJECTS.write_text(json.dumps(projects, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {PROJECTS}")
    print("\nNext: python src/apply_manual_overrides.py && python src/build_leaflet.py")


if __name__ == "__main__":
    main()
