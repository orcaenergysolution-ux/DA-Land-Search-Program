"""Download AEMO Indicative REZ boundaries from Geoscience Australia ArcGIS Feature Service.

Source: AEMO Indicative Renewable Energy Zones 2021
ArcGIS item: https://www.arcgis.com/home/item.html?id=b1e8003e917d467c9ff434c556fa8f62
Copyright: Australian Energy Market Operator (AEMO)

Output: data/intermediate/rez.geojson
"""
from __future__ import annotations
import json
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from urllib.parse import urlencode

ROOT = Path(__file__).parent.parent
OUT = ROOT / "data" / "intermediate" / "rez.geojson"

# Official AEMO REZ Feature Service (Geoscience Australia hosted)
FEATURE_SERVICE = (
    "https://services1.arcgis.com/wfNKYeHsOyaFyPw3/arcgis/rest/services"
    "/Renewable_Energy_Zones/FeatureServer/1/query"
)

# ── REZ COLOURS ──────────────────────────────────────────────────────────────
# Edit the hex values below to change each zone's colour on the map.
# After editing, re-run:  python src/fetch_rez.py  then  python src/build_leaflet.py
# -----------------------------------------------------------------------------
REZ_COLOURS = {
    # Queensland
    "Q1": "#E6C5C1",
    "Q2": "#F3EECA",
    "Q3": "#DFE7D4",
    "Q4": "#CCD9EF",
    "Q5": "#DFD3E8",
    "Q6": "#FDD1A9",
    "Q7": "#FDFCA9",
    "Q8": "#A9FDDA",
    "Q9": "#F7E6FC",
    # New South Wales
    "N1": "#E6C5C1",
    "N2": "#F3EECA",
    "N3": "#DFE7D4",
    "N4": "#CCD9EF",
    "N5": "#DFD3E8",
    "N6": "#FDD1A9",
    "N7": "#FDFCA9",
    "N8": "#A9FDDA",
    # Victoria
    "V1": "#E6C5C1",
    "V2": "#F3EECA",
    "V3": "#DFE7D4",
    "V4": "#CCD9EF",
    "V5": "#DFD3E8",
    "V6": "#FDD1A9",
    # South Australia
    "S1": "#E6C5C1",
    "S2": "#F3EECA",
    "S3": "#DFE7D4",
    "S4": "#CCD9EF",
    "S5": "#DFD3E8",
    "S6": "#FDD1A9",
    "S7": "#FDFCA9",
    "S8": "#A9FDDA",
    "S9": "#F7E6FC",
    # Tasmania
    "T1": "#E6C5C1",
    "T2": "#F3EECA",
    "T3": "#DFE7D4",
    # Offshore Wind Zones
    "O1": "#B4FFE0",
    "O2": "#EEAFFF",
    "O3": "#D39AFF",
    "O4": "#FFF39C",
}
# ─────────────────────────────────────────────────────────────────────────────


def fetch_rez() -> dict:
    params = urlencode({
        "where": "1=1",
        "outFields": "*",
        "f": "geojson",
        "geometryPrecision": 4,
    })
    url = f"{FEATURE_SERVICE}?{params}"
    print(f"Fetching REZ boundaries from Geoscience Australia ArcGIS ...")
    req = Request(url, headers={"User-Agent": "nem-generation-map/0.1"})
    try:
        with urlopen(req, timeout=60) as r:
            data = json.loads(r.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError) as e:
        raise SystemExit(f"Failed to fetch REZ data: {e}")

    features = data.get("features", [])
    print(f"  Got {len(features)} REZ polygons")

    # Enrich with colour + type metadata
    for f in features:
        props = f.get("properties") or {}
        name = (props.get("Name") or props.get("name") or "").strip()
        # REZ ID prefix = first char of name (Q/N/V/S/T/O)
        rez_id = name.split()[0] if name else ""
        prefix = rez_id[0].upper() if rez_id else "?"
        rez_type = "Offshore" if prefix == "O" else "Onshore"
        props["rez_id"] = rez_id
        props["rez_name"] = name
        props["rez_type"] = rez_type
        props["state"] = {
            "Q": "QLD", "N": "NSW", "V": "VIC",
            "S": "SA", "T": "TAS", "O": "Offshore",
        }.get(prefix, "")
        props["fill"] = REZ_COLOURS.get(rez_id, "#98E600")
        f["properties"] = props

    return data


def main():
    data = fetch_rez()
    OUT.write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")
    n = len(data.get("features", []))
    print(f"Wrote {OUT}  ({n} REZs, {OUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
