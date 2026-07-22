"""
Fetch external renewable energy project data and merge into projects.json.

Sources implemented:
  1. CER  — Clean Energy Regulator committed/probable CSVs (national)
  2. NSW  — NSW Planning renewable energy DA tracker (HTML table)
  3. VIC  — DataVic WFS renewables_point (252 facilities with coordinates)
  4. QLD  — QLD Electricity Plants ArcGIS FeatureServer (~200 renewable projects)
  5. TAS  — TAS State Growth Generation+Storage MapServer + existing wind/hydro
  6. Capacity supplement — WRI GPPD + OSM + manual_capacities.json (fills MW gaps)

For each source:
  - If a project already exists (fuzzy name + state match):
      * Appends +TAG to source field (e.g. NEM+CER, NEM+VIC_DA)
      * Upgrades stage via STAGE_RANK (state DA sources are authoritative)
      * Fills lat/lon if project currently has no location
      * Fills location_desc if currently blank
  - If the project is new:
      * Adds a minimal project entry with lat/lon from the source

Sources NOT implemented (no accessible REST API found):
  SA — plan.sa.gov.au (403), energymining.sa.gov.au (403),
       SA EPA public register (403), SA CKAN (no spatial data for RE projects)
       → CER data already covers SA committed/probable projects.

Usage:
    python src/fetch_cer_da.py
    python src/fetch_cer_da.py --dry-run   # show counts, don't write
"""
from __future__ import annotations
import csv
import io
import json
import re
import sys
import time
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from fetch_capacity_supplement import apply_capacity_supplement
from fetch_vic_permits import apply_vic_permit_data
from fetch_qld_sara import apply_sara_decisions

ROOT = Path(__file__).parent.parent
INTERMEDIATE = ROOT / "data" / "intermediate"
PROJECTS_PATH = INTERMEDIATE / "projects.json"

# NEM region lookup — only the 5 NEM states; WA/NT are NOT part of NEM
NEM_STATES = {"NSW", "VIC", "QLD", "SA", "TAS"}
STATE_TO_REGION = {
    "NSW": "NSW1", "VIC": "VIC1", "QLD": "QLD1",
    "SA": "SA1", "TAS": "TAS1",
}

# ── Name normalisation ─────────────────────────────────────────────────────────
_STRIP_RE = re.compile(
    r"\b("
    r"power station|power plant|power|"
    r"solar farm|solar pv|solar and bess|solar|"
    r"wind farm|wind|"
    r"battery energy storage system|bess|battery storage|battery|"
    r"pumped hydro|pumped storage|hydro|"
    r"combined cycle gas turbine|ccgt|"
    r"open cycle gas turbine|ocgt|"
    r"gas turbine|gas fired|"
    r"biomass|landfill gas|"
    r"hybrid facility|hybrid power station|hybrid|"
    r"energy hub|renewable energy hub|energy park|"
    r"stage \d+|phase \d+|unit \d+|"
    r"\(.*?\)"
    r")\b",
    re.IGNORECASE,
)


def norm(s: str) -> str:
    if not s:
        return ""
    s = str(s).lower()
    s = re.sub(r"[​\xa0]", " ", s)
    s = re.sub(r"\bmt\b", "mount", s)
    s = re.sub(r"\bst\b", "saint", s)
    s = re.sub(r"\bno\.\b", "north", s)
    s = _STRIP_RE.sub(" ", s)
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return " ".join(s.split())


# ── Technology mapping ─────────────────────────────────────────────────────────
def map_tech(fuel: str) -> str:
    f = (fuel or "").lower().strip()
    if "solar"   in f: return "Solar"
    if "wind"    in f: return "Wind (Onshore)"
    if "hydro"   in f or "water" in f: return "Hydro"
    if "pumped"  in f: return "Pumped Hydro"
    if "biomass" in f: return "Biomass"
    if "biogas"  in f or "landfill" in f: return "Gas"
    if "battery" in f or "storage" in f: return "Battery"
    if "gas"     in f: return "Gas"
    return "Other"


def map_nsw_type(t: str) -> str:
    t = (t or "").lower()
    if "solar"        in t: return "Solar"
    if "wind"         in t: return "Wind (Onshore)"
    if "storage"      in t or "bess" in t: return "Battery"
    if "hydro"        in t: return "Hydro"
    if "transmission" in t: return "Other"
    return "Other"


def map_nsw_stage(status: str) -> str:
    s = (status or "").lower()
    if "operational" in s: return "Existing"
    if "approved"    in s: return "DA Approved"
    if "assessment"  in s: return "DA Submitted"
    if "withdrawn"   in s: return "Withdrawn"
    return "Unknown"


# ── Project matching ───────────────────────────────────────────────────────────
def find_match(name: str, state: str, cap_mw: float | None,
               projects: list[dict]) -> dict | None:
    """
    Fuzzy match an external project to an existing projects.json entry.
    Requires: same state + normalised name overlap + capacity within 3×.
    """
    key = norm(name)
    state = (state or "").upper()
    if not key:
        return None

    def cap_ok(p: dict) -> bool:
        if cap_mw is None:
            return True
        pc = p.get("capacity_mw")
        if not pc:
            return True
        try:
            r = float(cap_mw) / float(pc)
            return 1 / 3 <= r <= 3
        except (TypeError, ZeroDivisionError):
            return True

    candidates = [p for p in projects
                  if (p.get("state") or "").upper() == state or not state]

    # Pass 1: exact norm match
    for p in candidates:
        if norm(p.get("site_name") or "") == key and cap_ok(p):
            return p

    # Pass 2: substring (both ≥2 words)
    key_words = key.split()
    if len(key_words) >= 2:
        for p in candidates:
            pk = norm(p.get("site_name") or "")
            pw = pk.split()
            if len(pw) < 2:
                continue
            if key in pk and cap_ok(p):
                # Incoming name is a substring of existing — accept
                return p
            if pk in key and len(pw) >= 3 and cap_ok(p):
                # Existing stripped name is contained in incoming name.
                # Require ≥3 words so bare 2-word location names (e.g. "Upper Hunter")
                # don't accidentally match distinct projects like "Upper Hunter South".
                return p

    # Pass 3: external name is 1 word (≥5 chars) — check if any existing project
    # norm starts with that word (handles "Bango" matching "Bango 973", etc.)
    if len(key_words) == 1 and len(key) >= 5:
        for p in candidates:
            pk = norm(p.get("site_name") or "")
            pw = pk.split()
            if not pw:
                continue
            # existing project starts with the external 1-word key
            if pw[0] == key and cap_ok(p):
                return p

    return None


# ── HTTP helper ────────────────────────────────────────────────────────────────
def fetch_url(url: str, accept: str = "*/*") -> bytes:
    req = Request(url, headers={
        "User-Agent": "nem-generation-map/0.1 (contact: expenses.woodenduck@gmail.com)",
        "Accept": accept,
    })
    with urlopen(req, timeout=30) as r:
        return r.read()


# ── Source 1: CER ─────────────────────────────────────────────────────────────
CER_URLS = {
    "committed": "https://cer.gov.au/document/power-stations-and-projects-committed",
    "probable":  "https://cer.gov.au/document/power-stations-and-projects-probable",
}

# CER statuses that are already well-covered by NEM Gen Info → skip adding as new
CER_SKIP_IF_NEM_COVERED = {"committed"}   # probable are often missing from NEM


def fetch_cer(status: str) -> list[dict]:
    """Download and parse a CER project CSV. Returns list of dicts."""
    url = CER_URLS[status]
    print(f"  Fetching CER {status}: {url}")
    try:
        raw = fetch_url(url, accept="text/csv,*/*")
    except (HTTPError, URLError, TimeoutError) as e:
        print(f"  ERROR fetching CER {status}: {e}", file=sys.stderr)
        return []

    # Detect encoding (CER sometimes uses cp1252)
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = raw.decode("cp1252", errors="replace")

    rows = []
    reader = csv.DictReader(io.StringIO(text))
    # Normalise column names (strip whitespace, lowercase)
    for row in reader:
        clean = {k.strip().lower(): (v or "").strip() for k, v in row.items()}
        name    = clean.get("project name") or clean.get("power station name") or ""
        state   = (clean.get("state") or "").strip().upper()
        mw_str  = clean.get("mw capacity") or clean.get("installed capacity (mw)") or ""
        fuel    = clean.get("fuel source") or clean.get("fuel source(s)") or ""
        date    = clean.get("committed date (month/year)") or clean.get("accreditation start date") or ""

        if not name or state not in NEM_STATES:
            continue   # skip WA/NT (not NEM) and blank rows
        try:
            mw = float(mw_str) if mw_str else None
        except ValueError:
            mw = None

        rows.append({
            "name":   name,
            "state":  state,
            "mw":     mw,
            "tech":   map_tech(fuel),
            "fuel":   fuel,
            "date":   date,
            "status": status.capitalize(),   # "Committed" or "Probable"
            "_src":   "CER",
        })
    print(f"    Parsed {len(rows)} rows")
    return rows


# ── Source 2: NSW Planning DA tracker ─────────────────────────────────────────
NSW_URL = "https://www.planning.nsw.gov.au/policy-and-legislation/renewable-energy"

# Patterns for pulling data out of the NSW page JavaScript/JSON embed
_JSON_RE = re.compile(r'window\.__INITIAL_STATE__\s*=\s*(\{.*?\});', re.DOTALL)
_NEXT_DATA_RE = re.compile(r'<script[^>]+id=["\']__NEXT_DATA__["\'][^>]*>(\{.*?\})</script>', re.DOTALL)


class NswTableParser(HTMLParser):
    """Fallback HTML parser: grabs every <tr> in the page table."""
    def __init__(self):
        super().__init__()
        self.in_table = False
        self.in_row = False
        self.in_cell = False
        self.rows: list[list[str]] = []
        self._current_row: list[str] = []
        self._current_cell: list[str] = []
        self._depth = 0

    def handle_starttag(self, tag, attrs):
        attr_d = dict(attrs)
        if tag == "table":
            self.in_table = True
        if self.in_table and tag == "tr":
            self.in_row = True
            self._current_row = []
        if self.in_row and tag in ("td", "th"):
            self.in_cell = True
            self._current_cell = []

    def handle_endtag(self, tag):
        if tag == "table":
            self.in_table = False
        if self.in_table and tag == "tr":
            if self._current_row:
                self.rows.append(self._current_row)
            self.in_row = False
        if self.in_row and tag in ("td", "th"):
            self._current_row.append(" ".join(self._current_cell).strip())
            self.in_cell = False

    def handle_data(self, data):
        if self.in_cell:
            self._current_cell.append(data.strip())


def fetch_nsw_da() -> list[dict]:
    """Scrape the NSW Planning renewable energy project tracker.

    The page contains two HTML structures for each project:
      1. A simple 4-column table row (all 194 projects — name, type, status).
      2. A hidden dialog table (105 projects) with full details including
         Location, Generating Capacity (MW), Storage Capacity (MW/MWh),
         and Approval date.

    We parse dialog tables first (richest data), then supplement with
    the simple table for projects that don't have a dialog section.
    """
    print(f"  Fetching NSW Planning DA tracker: {NSW_URL}")
    try:
        raw = fetch_url(NSW_URL, accept="text/html,*/*")
    except (HTTPError, URLError, TimeoutError) as e:
        print(f"  ERROR fetching NSW page: {e}", file=sys.stderr)
        return []

    try:
        html = raw.decode("utf-8", errors="replace")
    except Exception:
        html = raw.decode("latin-1", errors="replace")

    # ── Step 1: parse dialog detail sections (richest data) ───────────────────
    # Each dialog has a <caption>Full details for entry NAME</caption>
    # followed by key→value table rows.
    DIALOG_RE = re.compile(
        r'<caption>Full details for entry ([^<]+)</caption>(.*?)</table>',
        re.DOTALL,
    )
    KV_RE = re.compile(
        r'<th>\s*<p>([^<]+)</p>\s*</th>\s*<td>\s*<p>(.*?)</p>',
        re.DOTALL,
    )

    dialog_rows: dict[str, dict] = {}
    for m in DIALOG_RE.finditer(html):
        proj_name = m.group(1).strip()
        tbody = m.group(2)
        kv = {
            k.strip(): re.sub(r"<[^>]+>", "", v).strip()
            for k, v in KV_RE.findall(tbody)
        }

        # Capacity: "1400 MW" or "N/A"
        mw_str = kv.get("Generating Capacity (MW)", "")
        try:
            mw = float(re.sub(r"[^\d.]", "", mw_str)) if mw_str and mw_str != "N/A" else None
        except ValueError:
            mw = None

        # Storage: "200 MW / 400 MWh" or "500MW/2000MWh" — extract both MW and MWh
        mwh_str = kv.get("Storage Capacity (MW/MWh)", "")
        mwh: float | None = None
        mwh_m = re.search(r"([\d,]+)\s*MWh", mwh_str, re.IGNORECASE)
        if mwh_m:
            try:
                mwh = float(mwh_m.group(1).replace(",", ""))
            except ValueError:
                pass
        # For storage-only projects (no Generating Capacity field), extract MW from
        # the storage string: "200 MW / 400 MWh" → mw=200
        if mw is None and mwh_str:
            mw_s = re.search(r"([\d,]+)\s*MW\b", mwh_str, re.IGNORECASE)
            if mw_s:
                try:
                    mw = float(mw_s.group(1).replace(",", ""))
                except ValueError:
                    pass

        # Location suburb (e.g. "Moulamein") — use as estimated geocode hint
        loc_raw = kv.get("Location", "")
        location = loc_raw.strip() if loc_raw and loc_raw.strip() not in ("N/A", "") else ""

        dialog_rows[proj_name] = {
            "name":       proj_name,
            "state":      "NSW",
            "tech":       map_nsw_type(kv.get("Project type", "")),
            "status_raw": kv.get("Status", ""),
            "mw":         mw,
            "mwh":        mwh,
            "location":   location,
            "_src":       "NSW_DA",
        }

    # ── Step 2: simple loop-index rows for projects without dialog data ────────
    # Format: <tr data-loop-index="NAME"><td>NAME</td><td>TYPE</td><td>STATUS</td>…
    LOOP_RE = re.compile(
        r'data-loop-index="([^"]+)"[^>]*>\s*<td>([^<]*)</td>\s*<td>([^<]*)</td>\s*<td>([^<]*)</td>',
    )

    projects_out: list[dict] = list(dialog_rows.values())   # dialog-sourced first
    seen_names = set(dialog_rows.keys())

    for m in LOOP_RE.finditer(html):
        name   = m.group(1).strip()
        ptype  = m.group(3).strip()    # group(2) = repeated name cell
        status = m.group(4).strip()
        if name in seen_names:
            continue                   # already have richer dialog data
        seen_names.add(name)
        projects_out.append({
            "name":       name,
            "state":      "NSW",
            "tech":       map_nsw_type(ptype),
            "status_raw": status,
            "mw":         None,
            "mwh":        None,
            "location":   "",
            "_src":       "NSW_DA",
        })

    if projects_out:
        loc_count = sum(1 for r in projects_out if r.get("location"))
        print(f"    Parsed {len(projects_out)} rows "
              f"({len(dialog_rows)} with full details, {loc_count} with location)")
        return projects_out

    print("  WARNING: could not parse NSW page — page may be JS-rendered", file=sys.stderr)
    return []


def _extract_nsw_from_json(data, _depth=0) -> list[dict]:
    """Recursively search JSON for arrays that look like project lists."""
    if _depth > 10:
        return []
    if isinstance(data, list) and len(data) > 5:
        if isinstance(data[0], dict):
            keys = set(data[0].keys())
            # Looks like a project list if it has name+status or name+capacity
            if any(k in keys for k in ("projectName", "name", "project_name")):
                return [_nsw_row_from_json(r) for r in data if isinstance(r, dict)]
    if isinstance(data, dict):
        for v in data.values():
            result = _extract_nsw_from_json(v, _depth + 1)
            if result:
                return result
    return []


def _nsw_row_from_json(r: dict) -> dict:
    name   = r.get("projectName") or r.get("name") or r.get("project_name") or ""
    ptype  = r.get("type") or r.get("projectType") or ""
    loc    = r.get("location") or r.get("suburb") or r.get("lga") or ""
    mw     = r.get("capacity") or r.get("capacityMw") or r.get("mw")
    mwh    = r.get("storage") or r.get("storageMwh") or r.get("mwh")
    status = r.get("status") or r.get("projectStatus") or ""
    date   = r.get("approvalDate") or r.get("approval_date") or r.get("date") or ""
    try:
        mw = float(mw) if mw else None
    except (TypeError, ValueError):
        mw = None
    try:
        mwh = float(mwh) if mwh else None
    except (TypeError, ValueError):
        mwh = None
    return {
        "name": name, "state": "NSW", "location": loc,
        "mw": mw, "mwh": mwh, "tech": map_nsw_type(ptype),
        "status_raw": status, "date": date, "_src": "NSW_DA",
    }


# ── Source 3: VIC Open Data — Renewables Facility Centre Points ───────────────
VIC_WFS_URL = (
    "https://opendata.maps.vic.gov.au/geoserver/wfs"
    "?service=WFS&version=2.0.0&request=GetFeature"
    "&typeNames=open-data-platform:renewables_point"
    "&outputFormat=application/json"
)


def vic_stage(approval: str, construction: str) -> str:
    """Derive stage from VIC WFS approval_status + construction_status."""
    a = (approval    or "").lower()
    c = (construction or "").lower()
    if "constructed" == c or "operating" in a:
        return "Existing"
    if "under construction" in c:
        return "Committed"
    if "approved" in a and "not constructed" in c:
        return "DA Approved"
    if "under consideration" in a or "referred" in a:
        return "DA Submitted"
    return "Unknown"


def map_vic_type(t: str) -> str:
    t = (t or "").lower()
    if "solar"  in t: return "Solar"
    if "wind"   in t: return "Wind (Onshore)"
    if "battery" in t: return "Battery"
    return "Other"


def fetch_vic_da() -> list[dict]:
    """Fetch VIC renewable energy facilities from the DataVic WFS endpoint."""
    print(f"  Fetching VIC WFS: {VIC_WFS_URL[:80]}...")
    try:
        raw = fetch_url(VIC_WFS_URL, accept="application/json,*/*")
    except (HTTPError, URLError, TimeoutError) as e:
        print(f"  ERROR fetching VIC WFS: {e}", file=sys.stderr)
        return []

    try:
        data = json.loads(raw.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        print(f"  ERROR parsing VIC WFS JSON: {e}", file=sys.stderr)
        return []

    rows = []
    for f in data.get("features", []):
        props = f.get("properties") or {}
        geom  = f.get("geometry")  or {}
        coords = geom.get("coordinates")   # [lon, lat]
        name   = (props.get("name") or "").strip().title()   # WFS names are ALLCAPS
        ptype  = props.get("type") or ""
        appr   = props.get("approval_status") or ""
        cons   = props.get("construction_status") or ""
        if not name:
            continue
        lat = float(coords[1]) if coords and len(coords) >= 2 else None
        lon = float(coords[0]) if coords and len(coords) >= 2 else None
        rows.append({
            "name":    name,
            "state":   "VIC",
            "mw":      None,           # WFS doesn't include capacity
            "tech":    map_vic_type(ptype),
            "stage":   vic_stage(appr, cons),
            "location": "",
            "_src":    "VIC_DA",
            "_lat":    lat,
            "_lon":    lon,
        })
    print(f"    Parsed {len(rows)} rows")
    return rows


# ── Source 4: QLD Electricity Plants (ArcGIS FeatureServer) ──────────────────
QLD_FS_URL = (
    "https://services1.arcgis.com/vkTwD8kHw2woKBqV/arcgis/rest/services"
    "/Queensland_Electricity_Plants/FeatureServer/0/query"
    "?where=1%3D1&outFields=*&f=geojson&resultRecordCount=1000"
)

# Only renewable fuel types (exclude coal, gas, diesel, etc.)
QLD_RENEWABLE_FUELS = {
    "Solar", "Wind", "Hydro", "Pumped hydro", "Battery storage",
    "Bioenergy", "Solar thermal",
}


def qld_stage(status: str) -> str:
    s = (status or "").strip().lower()
    if "existing" in s:       return "Existing"
    if "under construction" in s: return "Committed"
    if "proposed" in s:       return "DA Approved"
    if "decommissioned" in s: return "Withdrawn"
    return "Unknown"


def map_qld_type(fuel: str) -> str:
    f = (fuel or "").lower()
    if "solar" in f:                     return "Solar"
    if "wind" in f:                      return "Wind (Onshore)"
    if "pumped" in f:                    return "Pumped Hydro"
    if "hydro" in f:                     return "Hydro"
    if "battery" in f or "storage" in f: return "Battery"
    if "bioenergy" in f or "biomass" in f: return "Biomass"
    return "Other"


def fetch_qld_da() -> list[dict]:
    """Fetch QLD renewable energy projects from the QLD Electricity Plants FeatureServer."""
    print(f"  Fetching QLD Electricity Plants FeatureServer...")
    try:
        raw = fetch_url(QLD_FS_URL, accept="application/json,*/*")
    except (HTTPError, URLError, TimeoutError) as e:
        print(f"  ERROR fetching QLD FeatureServer: {e}", file=sys.stderr)
        return []
    try:
        data = json.loads(raw.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        print(f"  ERROR parsing QLD FeatureServer JSON: {e}", file=sys.stderr)
        return []

    rows = []
    for f in data.get("features", []):
        props = f.get("properties") or {}
        fuel_cat  = (props.get("FuelCategory") or "").strip()
        fuel_type = (props.get("FuelType") or "").strip()
        if fuel_cat != "Renewable" or fuel_type not in QLD_RENEWABLE_FUELS:
            continue

        name   = (props.get("Name") or "").strip()
        status = props.get("Status") or ""
        if not name:
            continue

        try:
            cap = float(props["Capacity"]) if props.get("Capacity") else None
        except (TypeError, ValueError):
            cap = None
        try:
            lat = float(props["Lat"]) if props.get("Lat") else None
            lon = float(props["Long"]) if props.get("Long") else None
        except (TypeError, ValueError):
            lat = lon = None

        rows.append({
            "name":     name,
            "state":    "QLD",
            "mw":       cap,
            "tech":     map_qld_type(fuel_type),
            "stage":    qld_stage(status),
            "location": props.get("LGA") or "",
            "_src":     "QLD_DA",
            "_lat":     lat,
            "_lon":     lon,
        })
    print(f"    Parsed {len(rows)} renewable rows")
    return rows


# ── Source 5: TAS State Growth — Generation+Storage + existing wind/hydro ─────
TAS_GEN_STORAGE_URL = (
    "https://data.stategrowth.tas.gov.au/ags/rest/services/ReCFIT"
    "/Generation_and_Storage/MapServer/0/query?where=1%3D1&outFields=*&f=geojson"
)
TAS_WIND_URL = (
    "https://data.stategrowth.tas.gov.au/ags/rest/services/Hosted"
    "/Existing_Wind_Farms/FeatureServer/0/query?where=1%3D1&outFields=*&f=geojson"
)
TAS_HYDRO_URL = (
    "https://data.stategrowth.tas.gov.au/ags/rest/services/Hosted"
    "/Existing_Hydro/FeatureServer/0/query?where=1%3D1&outFields=*&f=geojson"
)

# Status codes used in the Generation_and_Storage layer
# OP = Operational, AP = Approved, SA = State Assessment, EP = Early Planning
def tas_stage(status_type: str) -> str:
    s = (status_type or "").upper()
    if s == "OP": return "Existing"
    if s == "AP": return "DA Approved"
    if s == "SA": return "DA Submitted"
    if s == "EP": return "Application"
    return "Unknown"


def map_tas_type(tech: str) -> str:
    t = (tech or "").upper()
    if t == "WI": return "Wind (Onshore)"
    if t == "PH": return "Pumped Hydro"
    if t == "HY": return "Hydro"
    if t == "SO": return "Solar"
    if t == "BA": return "Battery"
    return "Other"


def fetch_tas_da() -> list[dict]:
    """Fetch TAS renewable energy projects from TAS State Growth feature services."""
    rows: list[dict] = []
    seen_norms: set[str] = set()

    # ── Layer 0: Generation+Storage projects (26 records, includes lat/lon) ──
    print(f"  Fetching TAS Generation+Storage MapServer...")
    try:
        raw  = fetch_url(TAS_GEN_STORAGE_URL, accept="application/json,*/*")
        data = json.loads(raw.decode("utf-8"))
        for f in data.get("features", []):
            props = f.get("properties") or {}
            name  = (props.get("Name") or "").strip()
            if not name:
                continue
            try:
                cap = float(props["CapacityMW"]) if props.get("CapacityMW") else None
            except (TypeError, ValueError):
                cap = None
            try:
                lat = float(props["Lat"])  if props.get("Lat")  else None
                lon = float(props["Long"]) if props.get("Long") else None
            except (TypeError, ValueError):
                lat = lon = None
            rows.append({
                "name":     name,
                "state":    "TAS",
                "mw":       cap,
                "tech":     map_tas_type(props.get("Technology_Type")),
                "stage":    tas_stage(props.get("Status_Type")),
                "location": "",
                "_src":     "TAS_DA",
                "_lat":     lat,
                "_lon":     lon,
            })
            seen_norms.add(norm(name))
        print(f"    Parsed {len(rows)} Gen+Storage rows")
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as e:
        print(f"  ERROR fetching TAS Gen+Storage: {e}", file=sys.stderr)

    # ── Existing wind and hydro (separate hosted layers, have geometry coords) ──
    extra_count = 0
    for url, tech_label in [
        (TAS_WIND_URL,  "Wind (Onshore)"),
        (TAS_HYDRO_URL, "Hydro"),
    ]:
        try:
            raw  = fetch_url(url, accept="application/json,*/*")
            data = json.loads(raw.decode("utf-8"))
            for f in data.get("features", []):
                props  = f.get("properties") or {}
                geom   = f.get("geometry")   or {}
                coords = geom.get("coordinates")    # [lon, lat] for Point
                name   = (props.get("name") or "").strip()
                if not name or norm(name) in seen_norms:
                    continue   # already covered by Gen+Storage layer
                try:
                    cap = float(props["reg_cap"]) if props.get("reg_cap") else None
                except (TypeError, ValueError):
                    cap = None
                lat = float(coords[1]) if coords and len(coords) >= 2 else None
                lon = float(coords[0]) if coords and len(coords) >= 2 else None
                rows.append({
                    "name":     name,
                    "state":    "TAS",
                    "mw":       cap,
                    "tech":     tech_label,
                    "stage":    "Existing",
                    "location": "",
                    "_src":     "TAS_DA",
                    "_lat":     lat,
                    "_lon":     lon,
                })
                seen_norms.add(norm(name))
                extra_count += 1
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as e:
            print(f"  ERROR fetching TAS existing ({tech_label}): {e}", file=sys.stderr)
    print(f"    Added {extra_count} existing wind/hydro rows (not in Gen+Storage)")
    print(f"    Total TAS: {len(rows)} rows")
    return rows


# ── NSW DA status → stage mapping ─────────────────────────────────────────────
def nsw_to_stage(status_raw: str) -> str | None:
    """Map a NSW DA status string to a stage value. Returns None if status
    doesn't warrant a stage change (e.g. already Operational → Existing)."""
    s = (status_raw or "").lower()
    if "operational" in s: return "Existing"
    if "approved"    in s: return "DA Approved"
    if "assessment"  in s: return "DA Submitted"
    if "withdrawn"   in s: return "Withdrawn"
    return None


# ── Merge engine ───────────────────────────────────────────────────────────────
def make_new_project(row: dict) -> dict:
    src = row["_src"]
    if src == "CER":
        stage = "Committed" if row["status"] == "Committed" else "Anticipated"
        return {
            "site_name":     row["name"],
            "region":        STATE_TO_REGION.get(row["state"], ""),
            "state":         row["state"],
            "owner":         "",
            "technology":    row["tech"],
            "fuel":          row.get("fuel", ""),
            "capacity_mw":   row["mw"],
            "storage_mwh":   None,
            "unit_status":   "",
            "asset_type":    "Project",
            "location_desc": "",
            "stage":         stage,
            "source":        "CER",
            "on_aemo_map":   False,
            "duid":          "",
            "lat": None, "lon": None,
            "geocode_source": None,
        }
    elif src == "NSW_DA":
        status_raw = row.get("status_raw", "")
        stage = map_nsw_stage(status_raw)
        return {
            "site_name":     row["name"],
            "region":        "NSW1",
            "state":         "NSW",
            "owner":         "",
            "technology":    row["tech"],
            "fuel":          "",
            "capacity_mw":   row["mw"],
            "storage_mwh":   row.get("mwh"),
            "unit_status":   "",
            "asset_type":    "Project",
            "location_desc": row.get("location", ""),
            "stage":         stage,
            "source":        "NSW_DA",
            "on_aemo_map":   False,
            "duid":          "",
            "lat": None, "lon": None,
            "geocode_source": None,
        }
    else:
        # VIC_DA, QLD_DA, TAS_DA — all carry lat/lon from their service
        src = row["_src"]
        region_map = {"VIC_DA": "VIC1", "QLD_DA": "QLD1", "TAS_DA": "TAS1"}
        state_map  = {"VIC_DA": "VIC",  "QLD_DA": "QLD",  "TAS_DA": "TAS"}
        lat = row.get("_lat")
        lon = row.get("_lon")
        geo_src = _GEOCODE_SRC_LABEL.get(src, src) if lat is not None else None
        return {
            "site_name":      row["name"],
            "region":         region_map.get(src, ""),
            "state":          state_map.get(src, ""),
            "owner":          "",
            "technology":     row["tech"],
            "fuel":           "",
            "capacity_mw":    row["mw"],
            "storage_mwh":    None,
            "unit_status":    "",
            "asset_type":     "Project",
            "location_desc":  row.get("location", ""),
            "stage":          row.get("stage", "Unknown"),
            "source":         src,
            "on_aemo_map":    False,
            "duid":           "",
            "lat":            lat,
            "lon":            lon,
            "geocode_source": geo_src,
            "geocode_display": row["name"] if lat is not None else "",
        }


# Stage rank — higher = more specific/certain. Used to avoid downgrading.
STAGE_RANK: dict[str | None, int] = {
    "Existing": 8, "Commissioning": 7, "Committed": 6, "Anticipated": 5,
    "DA Approved": 4, "DA Submitted": 3,
    "Application": 2, "Enquiry": 1, "Unknown": 0, None: 0, "": 0,
}

# Sources that carry authoritative stage + coordinates (like VIC WFS)
STATE_DA_SOURCES = {"VIC_DA", "QLD_DA", "TAS_DA"}

# Geocode label used per source
_GEOCODE_SRC_LABEL = {
    "VIC_DA": "VIC_WFS",
    "QLD_DA": "QLD_FS",
    "TAS_DA": "TAS_FS",
}


def merge_rows(rows: list[dict], projects: list[dict],
               dry_run: bool = False) -> tuple[int, int, int]:
    """
    Returns (added, updated, skipped).
    updated = source tag added, location_desc/storage_mwh filled, or stage upgraded
    """
    added = updated = skipped = 0
    for row in rows:
        match = find_match(row["name"], row["state"], row.get("mw"), projects)
        if match:
            changed = False
            src = row["_src"]

            # ── Source tag ──
            existing_src = match.get("source") or ""
            # Map _src to the tag string appended to the source field
            tag = src   # e.g. "CER", "NSW_DA", "VIC_DA", "QLD_DA", "TAS_DA"
            if tag not in existing_src:
                if not dry_run:
                    match["source"] = (existing_src + "+" + tag) if existing_src else tag
                changed = True

            # ── Stage upgrade ──
            cur_stage  = match.get("stage") or "Unknown"
            new_stage: str | None = None

            if src in STATE_DA_SOURCES:
                # NEM unit_status is authoritative — never let a state DA source
                # overwrite it.  KCI stage ("Enquiry") is only a default and
                # should be upgradeable by a real DA record.
                existing_src = match.get("source") or ""
                has_nem = "NEM" in existing_src
                if has_nem:
                    new_stage = None   # NEM stage wins
                else:
                    # KCI-only or DA-only — apply DA stage if it's an upgrade.
                    new_stage = row.get("stage") or "Unknown"
                    # Never set Existing on a merged (existing KCI) project from a
                    # DA source alone. If truly operational it would be in NEM Gen Info.
                    # DA "Existing" on a merged record is likely a sibling-project
                    # norm() collision (e.g. "Wellington North Solar Farm" Operational
                    # matching "Wellington North BESS" via stripped name).
                    if new_stage == "Existing":
                        new_stage = None
                    elif STAGE_RANK.get(new_stage, 0) <= STAGE_RANK.get(cur_stage, 0):
                        new_stage = None   # would not be an upgrade — skip
            elif src == "NSW_DA":
                # Always recompute NSW DA stage so the mapping stays current.
                # Don't overwrite a stage that NEM itself assigned (Existing/Committed/Anticipated)
                # — only protect it if the project actually came from NEM.
                NEM_STAGES = {"Existing", "Committed", "Anticipated"}
                has_nem = "NEM" in (match.get("source") or "")
                if cur_stage not in NEM_STAGES or not has_nem:
                    candidate = nsw_to_stage(row.get("status_raw", ""))
                    # Only NEM "In Service" can confirm a project is Existing.
                    # Block NSW DA setting Existing if:
                    #   - no NEM source at all (norm() collision risk: a sibling
                    #     project's Operational DA row lands on a different project,
                    #     e.g. "Wellington North Solar Farm" → "Wellington North BESS")
                    #   - NEM source present but unit_status ≠ "in service"
                    if candidate == "Existing":
                        if not has_nem or \
                                (match.get("unit_status") or "").lower() != "in service":
                            candidate = None
                    new_stage = candidate
            elif src == "CER":
                # CER is more informative than the KCI default (Enquiry/Unknown).
                # Apply when NEM is not the source (NEM is always authoritative)
                # and the CER stage is actually an upgrade in rank.
                has_nem = "NEM" in (match.get("source") or "")
                if not has_nem:
                    cer_stage = "Committed" if row.get("status") == "Committed" else "Anticipated"
                    if STAGE_RANK.get(cer_stage, 0) > STAGE_RANK.get(cur_stage, 0):
                        new_stage = cer_stage

            if new_stage and new_stage != cur_stage:
                if not dry_run:
                    match["stage"] = new_stage
                changed = True

            # ── Coordinates from state DA sources ────────────────────────────────
            # Apply if the project has no location OR only a coarse geocode.
            # DA spatial datasets carry facility-level GPS and should override
            # vision coordinates (±10–30 km schematic PDF position) as well as
            # suburb centroids.
            if src in STATE_DA_SOURCES and row.get("_lat") is not None:
                no_loc    = match.get("lat") is None
                is_coarse = match.get("geocode_source") in {"suburb", "vision"}
                if no_loc or is_coarse:
                    if not dry_run:
                        match["lat"] = row["_lat"]
                        match["lon"] = row["_lon"]
                        match["geocode_source"] = _GEOCODE_SRC_LABEL.get(src, src)
                        match["geocode_display"] = row["name"]
                    changed = True

            # ── Fill location_desc if blank ──
            loc = row.get("location", "")
            if loc and not (match.get("location_desc") or "").strip():
                if not dry_run:
                    match["location_desc"] = loc
                changed = True

            # ── Fill capacity_mw if blank ──
            row_mw = row.get("mw")
            if row_mw and not match.get("capacity_mw"):
                if not dry_run:
                    match["capacity_mw"] = row_mw
                changed = True

            # ── Fill storage_mwh if blank ──
            mwh = row.get("mwh")
            if mwh and not match.get("storage_mwh"):
                if not dry_run:
                    match["storage_mwh"] = mwh
                changed = True

            if changed:
                updated += 1
            else:
                skipped += 1
        else:
            # New project
            if not row.get("name") or len(row["name"]) < 4:
                skipped += 1
                continue
            # Skip NSW DA rows with no capacity and transmission/Other tech
            if row.get("_src") == "NSW_DA" and not row.get("mw") and row.get("tech") == "Other":
                skipped += 1
                continue
            # Skip CER rows outside NEM states
            if row.get("_src") == "CER" and row.get("state") not in NEM_STATES:
                skipped += 1
                continue
            if not dry_run:
                projects.append(make_new_project(row))
            added += 1

    return added, updated, skipped


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    dry_run = "--dry-run" in sys.argv
    if dry_run:
        print("DRY RUN — no files will be written\n")

    projects: list[dict] = json.loads(PROJECTS_PATH.read_text(encoding="utf-8"))
    print(f"Loaded {len(projects)} existing projects\n")

    # ── One-time fix: VIC projects were wrongly tagged "NSW_DA" due to a bug ──
    fixed = 0
    for p in projects:
        src = p.get("source") or ""
        if p.get("state") == "VIC" and "NSW_DA" in src and "VIC_DA" not in src:
            # Remove the wrong NSW_DA tag and replace with VIC_DA
            p["source"] = src.replace("NSW_DA", "VIC_DA")
            fixed += 1
    if fixed:
        print(f"Fixed source tag on {fixed} VIC projects (NSW_DA -> VIC_DA)\n")

    total_added = total_updated = total_skipped = 0

    # ── CER ──
    print("=== CER ===")
    for status in ("committed", "probable"):
        rows = fetch_cer(status)
        if rows:
            a, u, s = merge_rows(rows, projects, dry_run)
            print(f"    {status}: +{a} new  ~{u} updated  {s} skipped")
            total_added += a; total_updated += u; total_skipped += s

    # ── NSW ──
    print("\n=== NSW Planning DA ===")
    nsw_rows = fetch_nsw_da()
    if nsw_rows:
        a, u, s = merge_rows(nsw_rows, projects, dry_run)
        print(f"  NSW DA: +{a} new  ~{u} updated  {s} skipped")
        total_added += a; total_updated += u; total_skipped += s

    # ── VIC ──
    print("\n=== VIC Open Data (renewables_point WFS) ===")
    vic_rows = fetch_vic_da()
    if vic_rows:
        a, u, s = merge_rows(vic_rows, projects, dry_run)
        print(f"  VIC DA: +{a} new  ~{u} updated  {s} skipped")
        total_added += a; total_updated += u; total_skipped += s

    # ── VIC ministerial permit supplement (capacity + address from permit pages/PDFs) ──
    apply_vic_permit_data(projects, dry_run=dry_run)

    # ── QLD ──
    print("\n=== QLD Electricity Plants (ArcGIS FeatureServer) ===")
    qld_rows = fetch_qld_da()
    if qld_rows:
        a, u, s = merge_rows(qld_rows, projects, dry_run)
        print(f"  QLD DA: +{a} new  ~{u} updated  {s} skipped")
        total_added += a; total_updated += u; total_skipped += s

    # ── QLD SARA decisions — approval dates + expiry check ──
    apply_sara_decisions(projects, dry_run=dry_run)

    # ── TAS ──
    print("\n=== TAS State Growth (Generation+Storage + existing wind/hydro) ===")
    tas_rows = fetch_tas_da()
    if tas_rows:
        a, u, s = merge_rows(tas_rows, projects, dry_run)
        print(f"  TAS DA: +{a} new  ~{u} updated  {s} skipped")
        total_added += a; total_updated += u; total_skipped += s

    # ── Summary ──
    print(f"\nTotal: +{total_added} added  ~{total_updated} updated  {total_skipped} skipped")
    print(f"Projects after merge: {len(projects)}")

    # ── Capacity supplement (WRI + OSM + manual overrides) ──
    apply_capacity_supplement(projects, dry_run=dry_run)

    # ── Manual exclusions ──
    excl_path = ROOT / "data" / "inputs" / "manual_exclusions.json"
    if excl_path.exists():
        exclusions = json.loads(excl_path.read_text(encoding="utf-8"))
        excl_names = {e["site_name"].strip().lower() for e in exclusions}
        before = len(projects)
        projects = [p for p in projects if p.get("site_name", "").strip().lower() not in excl_names]
        removed = before - len(projects)
        if removed:
            print(f"Manual exclusions: removed {removed} project(s) (see data/inputs/manual_exclusions.json)")

    if not dry_run:
        PROJECTS_PATH.write_text(
            json.dumps(projects, indent=2, default=str), encoding="utf-8"
        )
        print(f"Wrote {PROJECTS_PATH}")
    else:
        print("(dry-run: nothing written)")


if __name__ == "__main__":
    main()
