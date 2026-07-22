"""
Review DUID capacity: compare projects.json capacity_mw against AEMO MMS
DUDETAIL MAXCAPACITY.

Steps:
  1. Download the latest DUDETAIL zip from NEMWeb MMSDM archive.
  2. Parse it to get the latest MAXCAPACITY, REGISTEREDCAPACITY and
     MAXSTORAGECAPACITY per DUID (latest EFFECTIVEDATE + VERSIONNO wins).
  3. Re-read the NEM Gen Info Excel to collect ALL DUIDs per station group
     (site_name + unit_status), then sum MAXCAPACITY across all units.
  4. Join to projects.json by site_name (case-insensitive) and unit_status.
  5. Write a review CSV — does NOT modify projects.json.

Output:  outputs/duid_capacity_review.csv

Usage:
    python scripts/review_duid_capacity.py
"""
from __future__ import annotations
import csv
import http.client
import io
import json
import re
import ssl
import sys
import zipfile
from pathlib import Path

import openpyxl

ROOT       = Path(__file__).resolve().parent.parent
NEM_FILE   = ROOT / "data" / "inputs" / "NEM Generation Information Apr 2026.xlsx"
PROJECTS   = ROOT / "data" / "intermediate" / "projects.json"
OUT_CSV    = ROOT / "outputs" / "duid_capacity_review.csv"

# Try months from most-recent backwards until we find one
MMSDM_BASE = "https://nemweb.com.au/Data_Archive/Wholesale_Electricity/MMSDM"
MONTHS_TO_TRY = [
    (2026, 4), (2026, 3), (2026, 2), (2026, 1),
    (2025, 12), (2025, 11), (2025, 10),
]

REGION_TO_STATE = {
    "NSW1": "NSW", "VIC1": "VIC", "QLD1": "QLD", "SA1": "SA", "TAS1": "TAS",
}


# ---------------------------------------------------------------------------
# 1. Download DUDETAIL
# ---------------------------------------------------------------------------

def _nemweb_get(path: str) -> bytes:
    """HTTPS GET from nemweb.com.au preserving %2523-encoded # in path."""
    ctx = ssl.create_default_context()
    conn = http.client.HTTPSConnection("nemweb.com.au", timeout=60, context=ctx)
    conn.request("GET", path, headers={"User-Agent": "AEMO_map/1.0"})
    r = conn.getresponse()
    data = r.read()
    conn.close()
    if r.status != 200:
        raise IOError(f"HTTP {r.status} for {path[:80]}")
    return data


def fetch_dudetail() -> dict[str, dict]:
    """Return {duid: {max_cap, reg_cap, storage_mwh}} using latest MMSDM month."""
    for year, month in MONTHS_TO_TRY:
        # NEMWeb directory uses %2523 (double-encoded #) in hrefs
        path = (
            f"/Data_Archive/Wholesale_Electricity/MMSDM/{year}/MMSDM_{year}_{month:02d}/"
            f"MMSDM_Historical_Data_SQLLoader/DATA/"
            f"PUBLIC_ARCHIVE%2523DUDETAIL%2523FILE01%2523{year}{month:02d}010000.zip"
        )
        print(f"  Trying DUDETAIL {year}-{month:02d} ...")
        try:
            data = _nemweb_get(path)
            print(f"  Downloaded {len(data):,} bytes")
            return _parse_dudetail_zip(data)
        except Exception as e:
            print(f"    Failed: {e}")
    raise RuntimeError("Could not download DUDETAIL from any recent month")


def _parse_dudetail_zip(data: bytes) -> dict[str, dict]:
    """
    Parse AEMO MMS DUDETAIL CSV (inside zip).
    MMS row format:
      I,PARTICIPANT_REGISTRATION,DUDETAIL,<ver>,EFFECTIVEDATE,DUID,VERSIONNO,...
      D,PARTICIPANT_REGISTRATION,DUDETAIL,<ver>,<effectivedate>,<duid>,<verno>,...
    Columns of interest: EFFECTIVEDATE(1), DUID(2), VERSIONNO(3),
      REGISTEREDCAPACITY(6), DISPATCHTYPE(8), MAXCAPACITY(9),
      MAXSTORAGECAPACITY(27).
    Returns {duid: {max_cap, reg_cap, storage_mwh}} keeping latest record.
    """
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        csv_name = next(n for n in zf.namelist() if n.upper().endswith(".CSV"))
        raw = zf.read(csv_name).decode("utf-8", errors="replace")

    header: list[str] = []
    records: dict[str, dict] = {}

    import csv as _csv
    reader = _csv.reader(io.StringIO(raw))
    for parts in reader:
        if not parts:
            continue
        row_type = parts[0].strip().upper()

        if row_type == "I" and len(parts) > 4:
            header = [h.strip().upper() for h in parts[4:]]

        elif row_type == "D" and header:
            values = parts[4:]
            if len(values) < len(header):
                continue
            row = dict(zip(header, values))

            duid      = row.get("DUID", "").strip()
            disp_type = row.get("DISPATCHTYPE", "").strip().upper()
            if not duid or disp_type == "LOAD":
                continue

            try:
                max_cap     = float(row.get("MAXCAPACITY", "") or 0)
                reg_cap     = float(row.get("REGISTEREDCAPACITY", "") or 0)
                storage_mwh = float(row.get("MAXSTORAGECAPACITY", "") or 0) or None
            except ValueError:
                continue

            eff_date = row.get("EFFECTIVEDATE", "").strip()
            try:
                version = int(float(row.get("VERSIONNO", 0) or 0))
            except ValueError:
                version = 0

            existing = records.get(duid)
            if existing is None or (eff_date, version) > (existing["_eff"], existing["_ver"]):
                records[duid] = {
                    "max_cap":     max_cap,
                    "reg_cap":     reg_cap,
                    "storage_mwh": storage_mwh,
                    "_eff":        eff_date,
                    "_ver":        version,
                }

    print(f"  Parsed {len(records)} DUIDs from DUDETAIL")
    return records


# ---------------------------------------------------------------------------
# 2. Read NEM Gen Info: collect all DUIDs per (site_name, unit_status)
# ---------------------------------------------------------------------------

def _to_float(x):
    if x is None or x == "":
        return None
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def read_nem_duids() -> dict[tuple, list[str]]:
    """
    Returns {(site_name_lower, unit_status_lower): [duid1, duid2, ...]}
    One entry per NEM Gen Info row that has a non-empty DUID.
    """
    wb = openpyxl.load_workbook(NEM_FILE, data_only=True, read_only=True)
    ws = wb["Generator Information"]
    mapping: dict[tuple, list[str]] = {}
    for i, row in enumerate(ws.iter_rows(values_only=True)):
        if i < 4:
            continue
        region = row[5]
        if not region or region not in REGION_TO_STATE:
            continue
        site = str(row[1] or "").strip()
        duid = str(row[12] or "").strip()
        unit_status = str(row[20] or "").strip().rstrip("*").strip().lower()
        if unit_status.startswith("committed"):
            unit_status = "committed"
        if not site or not duid:
            continue
        key = (site.lower(), unit_status)
        mapping.setdefault(key, [])
        if duid not in mapping[key]:
            mapping[key].append(duid)
    wb.close()
    return mapping


# ---------------------------------------------------------------------------
# 3. Build comparison and write review CSV
# ---------------------------------------------------------------------------

def main():
    print("\n=== DUID capacity review ===")
    print("Fetching DUDETAIL from NEMWeb...")
    mms = fetch_dudetail()

    print("Reading NEM Gen Info DUIDs...")
    nem_duids = read_nem_duids()  # {(site_lower, status_lower): [duids]}

    print("Loading projects.json...")
    projects = json.loads(PROJECTS.read_text(encoding="utf-8"))

    rows = []
    no_duid    = 0
    no_mms     = 0
    matched    = 0

    for p in projects:
        if "NEM" not in (p.get("source") or ""):
            continue  # only NEM-sourced projects have DUIDs

        site       = p.get("site_name", "")
        state      = p.get("state", "")
        stage      = p.get("stage", "")
        unit_status = p.get("unit_status", "").lower()
        if unit_status.startswith("committed"):
            unit_status = "committed"

        cur_cap    = p.get("capacity_mw") or 0
        key        = (site.lower(), unit_status)
        duids      = nem_duids.get(key, [])

        if not duids:
            no_duid += 1
            continue

        # Sum MAXCAPACITY and REGISTEREDCAPACITY across all units
        mms_max_total     = 0.0
        mms_reg_total     = 0.0
        mms_storage_total = 0.0
        found_duids       = []
        missing_duids     = []
        for d in duids:
            rec = mms.get(d)
            if rec:
                mms_max_total     += rec["max_cap"]
                mms_reg_total     += rec["reg_cap"]
                mms_storage_total += rec["storage_mwh"] or 0
                found_duids.append(d)
            else:
                missing_duids.append(d)

        if not found_duids:
            no_mms += 1
            continue

        matched  += 1
        diff      = round(mms_max_total - cur_cap, 2)
        pct_diff  = round(diff / cur_cap * 100, 1) if cur_cap else None
        cur_mwh   = p.get("storage_mwh") or 0
        mwh_diff  = round(mms_storage_total - cur_mwh, 2) if mms_storage_total else None

        rows.append({
            "site_name":            site,
            "state":                state,
            "stage":                stage,
            "current_capacity_mw":  cur_cap,
            "mms_max_cap_mw":       round(mms_max_total, 2),
            "mms_reg_cap_mw":       round(mms_reg_total, 2),
            "difference_mw":        diff,
            "pct_difference":       pct_diff,
            "current_storage_mwh":  cur_mwh or "",
            "mms_storage_mwh":      round(mms_storage_total, 2) if mms_storage_total else "",
            "storage_diff_mwh":     mwh_diff if mwh_diff is not None else "",
            "duids_matched":        "|".join(found_duids),
            "duids_missing":        "|".join(missing_duids),
            "flag":                 (
                "INCREASE" if diff > 1 else
                "DECREASE" if diff < -1 else
                "OK"
            ),
        })

    # Sort: largest absolute difference first
    rows.sort(key=lambda r: abs(r["difference_mw"]), reverse=True)

    # Write CSV
    if rows:
        cols = list(rows[0].keys())
        with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=cols)
            w.writeheader()
            w.writerows(rows)
        print(f"\nWrote {OUT_CSV}")

    # Summary
    increases = sum(1 for r in rows if r["flag"] == "INCREASE")
    decreases = sum(1 for r in rows if r["flag"] == "DECREASE")
    ok        = sum(1 for r in rows if r["flag"] == "OK")
    print(f"\nResults:")
    print(f"  Matched:            {matched}")
    print(f"  No DUIDs in NEM:    {no_duid}")
    print(f"  DUIDs not in MMS:   {no_mms}")
    print(f"  INCREASE (>1 MW):   {increases}")
    print(f"  DECREASE (<-1 MW):  {decreases}")
    print(f"  OK (within ±1 MW):  {ok}")
    print(f"\nReview {OUT_CSV} before making any changes.")
    print("To apply updates, run:  python scripts/apply_duid_capacity.py")


if __name__ == "__main__":
    main()
