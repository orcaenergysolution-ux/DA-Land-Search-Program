"""
Geocoder for the NEM project list.

Coordinate source priority (highest → lowest)
----------------------------------------------
  1. DA spatial (VIC_WFS / QLD_FS / TAS_FS / NSW_DA) and `manual`
       Set by fetch_cer_da.py / apply_manual_overrides.py before this script.
       Never overwritten here.
  2. GA — Geoscience Australia power stations register (facility-level GPS).
       Overwrites vision (PDF schematic positions are ±10–30 km).
       Does not overwrite DA/manual.
  3. Nominatim / suburb — OpenStreetMap text geocode.
       Overwrites vision (a specific location_desc or project name search is
       more accurate than a schematic PDF position).
       Does not overwrite GA or DA/manual.
  4. vision — AEMO PDF affine-transform position (last resort).
       Applied only when neither GA nor Nominatim finds the project.
       Stored in geocode_source = "vision".

If no source finds a project, lat/lon = null and the project is hidden from the
map (apply_manual_overrides.py may fill some of these in afterwards).

Re-running is safe: the Nominatim cache is persistent.

Usage:
    python src/geocode.py
"""
from __future__ import annotations
import json
import re
import time
import sys
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

ROOT = Path(__file__).parent.parent
INTERMEDIATE = ROOT / "data" / "intermediate"
PROJECTS = INTERMEDIATE / "projects.json"
CACHE = INTERMEDIATE / "geocode_cache.json"      # Nominatim cache only

# GA National Electricity Infrastructure — Major Power Stations layer
GA_POWER_URL = (
    "https://services.ga.gov.au/gis/rest/services"
    "/National_Electricity_Infrastructure/MapServer/1/query"
)

# Nominatim search bounding boxes (lon_min, lat_min, lon_max, lat_max)
AU_NEM_VIEWBOX = "129.0,-44.0,154.0,-10.0"
REGION_VIEWBOX = {
    "NSW1": "140.9,-37.6,153.7,-28.1",
    "VIC1": "140.9,-39.3,150.0,-33.9",
    "QLD1": "137.9,-29.2,153.6,-10.0",
    "SA1":  "129.0,-38.1,141.0,-25.9",
    "TAS1": "144.5,-43.8,148.7,-39.5",
}

# Suffixes stripped before name-matching against GA station names
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
    r"stage \d+|phase \d+|unit \d+|"
    r"\(.*?\)"
    r")\b",
    re.IGNORECASE,
)


def norm(s: str) -> str:
    """Normalise a name for fuzzy matching."""
    if not s:
        return ""
    s = str(s).lower()
    s = re.sub(r"[​\xa0]", " ", s)          # zero-width / nbsp
    # Expand common abbreviations before stripping tech suffixes so both
    # sides of a comparison (e.g. "Mt Millar" vs "Mount Millar") collapse
    # to the same string.
    s = re.sub(r"\bmt\b",   "mount",  s)
    s = re.sub(r"\bst\b",   "saint",  s)
    s = re.sub(r"\bno\.\b", "north",  s)
    s = _STRIP_RE.sub(" ", s)
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return " ".join(s.split())


# ── Tier 1: GA power station fetch ───────────────────────────────────────────

def fetch_ga_stations() -> dict[str, dict]:
    """
    Returns {normalised_name: {lat, lon, name, state, fuel, mw}} for every
    station in the GA National Electricity Infrastructure dataset.
    Paginates automatically (recordCount limit = 1000).
    """
    stations: dict[str, dict] = {}
    offset = 0
    while True:
        params = urlencode({
            "where": "1=1",
            "outFields": "NAME,STATE,PRIMARYFUELTYPE,GENERATIONMW",
            "returnGeometry": "true",
            "geometryPrecision": 6,
            "f": "geojson",
            "resultOffset": offset,
            "resultRecordCount": 1000,
        })
        url = f"{GA_POWER_URL}?{params}"
        req = Request(url, headers={"User-Agent": "nem-generation-map/0.1"})
        try:
            with urlopen(req, timeout=30) as r:
                data = json.loads(r.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError) as e:
            print(f"  GA fetch error: {e}", file=sys.stderr)
            break

        features = data.get("features", [])
        if not features:
            break
        for f in features:
            p = f.get("properties") or {}
            geom = f.get("geometry") or {}
            coords = geom.get("coordinates")
            if not coords:
                continue
            lon, lat = coords[0], coords[1]
            name = (p.get("name") or p.get("NAME") or "").strip()
            if not name:
                continue
            key = norm(name)
            stations[key] = {
                "lat": lat,
                "lon": lon,
                "ga_name": name,
                "ga_state": p.get("state") or p.get("STATE") or "",
                "ga_fuel": p.get("primaryfueltype") or p.get("PRIMARYFUELTYPE") or "",
                "ga_mw": p.get("generationmw") or p.get("GENERATIONMW"),
            }
        offset += len(features)
        if len(features) < 1000:
            break   # last page

    print(f"  Fetched {len(stations)} GA power stations")
    return stations


def ga_match(project: dict, ga_stations: dict[str, dict]) -> dict | None:
    """
    Try to match a project to a GA power station.

    Rules (tightest to loosest):
      1. Exact normalised match on stripped site_name or location_desc.
         — if capacity is also known and differs >2×, skip (very unlikely same plant).
      2. Partial match: GA key fully contained in project string (or vice-versa)
         — both strings must be ≥ 2 words (avoids single-word false positives)
         — capacity must agree within 50 % (ratio 1/3 – 2.0).
      3. Word-overlap + capacity: ≥ 2 significant words shared between the
         un-stripped raw names AND capacity within 30 % (ratio 0.7 – 1.3).
         This catches cases where tech suffixes are stripped away leaving < 2 words
         (e.g. "Capital Wind Farm" → norm → "capital").

    State guard: GA station must be in the same state as the project.
    """
    proj_state = (project.get("state") or "").upper()

    # Map our state codes to GA state strings
    STATE_MAP = {
        "NSW": "New South Wales",
        "VIC": "Victoria",
        "QLD": "Queensland",
        "SA":  "South Australia",
        "TAS": "Tasmania",
        "WA":  "Western Australia",
        "NT":  "Northern Territory",
        "ACT": "Australian Capital Territory",
    }
    ga_state_full = STATE_MAP.get(proj_state, "")

    # Project capacity (MW) — may be None / zero
    try:
        proj_cap: float | None = float(project.get("capacity_mw") or 0) or None
    except (TypeError, ValueError):
        proj_cap = None

    def state_ok(sta: dict) -> bool:
        """True if GA station is in the same state as the project."""
        if not ga_state_full:
            return True   # unknown project state — don't filter
        return ga_state_full.lower() in (sta.get("ga_state") or "").lower()

    def cap_ratio(sta: dict) -> float | None:
        """project_cap / ga_mw, or None if either is unknown."""
        if proj_cap is None:
            return None
        try:
            ga_mw = float(sta.get("ga_mw") or 0) or None
        except (TypeError, ValueError):
            ga_mw = None
        if ga_mw is None:
            return None
        return proj_cap / ga_mw

    def cap_ok_loose(sta: dict) -> bool:
        """Capacity greater factor of 2 or less than 1/3 (or unknown) — used for exact name matches."""
        r = cap_ratio(sta)
        return r is None or (1 / 3 <= r ) or (r > 2)

    def cap_ok_mid(sta: dict) -> bool:
        """Capacity within 50 % (ratio 0.5) — used for partial name matches."""
        r = cap_ratio(sta)
        return r is None or (1/3 < r < 0.7) or ( 1.3 < r <=2 )

    def cap_ok_tight(sta: dict) -> bool:
        """Capacity within 30 % (ratio 0.7 – 1.3) — used for word-overlap matches."""
        r = cap_ratio(sta)
        return r is None or (0.7 <= r <= 1.3)

    def word_in_key(word: str, key: str) -> bool:
        """True if 'word' appears as a whole word within 'key'."""
        return (key == word
                or key.startswith(word + " ")
                or key.endswith(" " + word)
                or (" " + word + " ") in key)

    site = project.get("site_name") or ""
    loc  = project.get("location_desc") or ""
    candidates = [norm(site), norm(loc)]

    # ── Rule 1: exact normalised name match ──────────────────────────────────
    for c in candidates:
        if not c:
            continue
        if c in ga_stations:
            sta = ga_stations[c]
            if state_ok(sta) and cap_ok_loose(sta):
                return sta

    # ── Rule 2a: partial name match (substring, project ≥2 words) ───────────
    # GA key may be 1 word if it is long/specific (≥6 chars) — state guard
    # already prevents cross-state accidents.  No capacity check here: staged
    # projects (e.g. SF2 28 MW vs GA 313 MW total) have very different MWs.
    for c in candidates:
        if not c:
            continue
        c_words = c.split()
        if len(c_words) < 2:
            continue
        for key, sta in ga_stations.items():
            if not key or not state_ok(sta):
                continue
            key_words = key.split()
            # Single-word GA key: only accept if long enough to be specific.
            # Threshold is 5 chars so place names like "bango" (5) pass
            # while very short/generic tokens (≤4 chars) like "bay","oak" are skipped.
            if len(key_words) < 2 and len(key) < 5 and (key in c or c in key):
                continue   # GA name is single short word — too ambiguous
            if key in c or c in key:
                return sta

    # ── Rule 2b: project norm collapses to 1 word (tech suffixes stripped) ───
    # Example: "Capital Wind Farm" → norm → "capital" (≥4 chars)
    # Accepts if that word appears as a whole word inside a ≥2-word GA key
    # AND capacity is within ±30 %.
    for c in candidates:
        if not c:
            continue
        c_words = c.split()
        if len(c_words) != 1 or len(c) < 4:
            continue
        for key, sta in ga_stations.items():
            if not key or not state_ok(sta):
                continue
            key_words = key.split()
            if len(key_words) < 2:
                continue   # GA name also single word — too ambiguous
            if word_in_key(c, key) and cap_ok_tight(sta):
                return sta

    # ── Rule 3: location-word overlap + tight capacity match ─────────────────
    # Strips generic tech/function words so only place-specific words count.
    # Requires ≥2 location words shared AND capacity within ±30 %.
    TECH_WORDS = {
        "solar", "wind", "farm", "power", "station", "plant", "battery",
        "hydro", "gas", "coal", "bess", "storage", "energy", "generation",
        "pumped", "open", "cycle", "combined", "ccgt", "ocgt", "biomass",
        "landfill", "diesel", "turbine", "unit", "stage", "phase", "pv",
        "renewable", "hybrid", "peaker", "peaking",
    }
    STOPWORDS = {"the", "of", "and", "at", "in", "a", "an", "no", "st", "mt"}
    SKIP = TECH_WORDS | STOPWORDS

    for raw in (site, loc):
        if not raw:
            continue
        raw_words = {w for w in re.sub(r"[^a-z0-9]+", " ", raw.lower()).split()
                     if w not in SKIP and len(w) > 2}
        if len(raw_words) < 2:
            continue
        for key, sta in ga_stations.items():
            if not key or not state_ok(sta):
                continue
            key_raw = (sta.get("ga_name") or "")
            key_words = {w for w in re.sub(r"[^a-z0-9]+", " ", key_raw.lower()).split()
                         if w not in SKIP and len(w) > 2}
            if len(key_words) < 2:
                continue
            overlap = raw_words & key_words
            if len(overlap) >= 2 and cap_ok_tight(sta):
                return sta

    return None


# ── Tier 2: Nominatim ────────────────────────────────────────────────────────

def clean_loc(s: str) -> str:
    if not s:
        return ""
    # Collapse newlines to commas so multi-line addresses become single-line
    s = re.sub(r"[\r\n]+", ", ", s)
    s = s.strip().replace("\xa0", " ")
    # Strip leading directional distance ("12km East of ...")
    s = re.sub(
        r"\b\d+\s*km\s*(north|south|east|west|north[- ]?east|north[- ]?west"
        r"|south[- ]?east|south[- ]?west)\s+of\s+",
        "", s, flags=re.IGNORECASE,
    )
    return " ".join(s.split()).rstrip(".,;:- ")


def _loc_lines(raw: str) -> list[str]:
    """Split a raw location_desc on newlines and return cleaned non-empty lines."""
    return [clean_loc(l) for l in re.split(r"[\r\n]+", raw) if l.strip()]


def _suburb_from_address(loc: str, state: str) -> str | None:
    """Try to extract just the suburb/town from a full street address.

    'Lot 315 Bower Road, Australia Plains, SA' -> 'Australia Plains, SA'
    'Para Substation 132kV'                    -> None  (no usable suburb)
    """
    # Last comma-separated token that looks like a place name (not lot/road/substation)
    SKIP_WORDS = re.compile(
        r"\b(lot|lots|road|rd|street|st|avenue|ave|drive|dr|highway|hwy|lane|ln"
        r"|substation|terminal|kv|mw|grid|stage|phase|unit|block|section"
        r"|offshore|onshore|tbc|tbk|located|windfarm|wind farm)\b",
        re.IGNORECASE,
    )
    parts = [p.strip() for p in loc.split(",")]
    # Walk from the end; first part that has no address/infra keywords is the suburb
    for part in reversed(parts):
        part = part.strip()
        if not part or len(part) < 3:
            continue
        # Skip parts that are purely a state abbreviation or postcode
        if re.fullmatch(r"[A-Z]{2,3}|\d{4}", part):
            continue
        if not SKIP_WORDS.search(part):
            return f"{part}, {state}, Australia" if state else f"{part}, Australia"
    return None


def project_queries(p: dict) -> list[str]:
    state   = p.get("state") or ""
    raw_loc = (p.get("location_desc") or "").strip()
    loc     = clean_loc(raw_loc)
    site    = (p.get("site_name") or "").strip()
    site_core = _STRIP_RE.sub(" ", site).strip(" -–—,.")
    site_core = " ".join(site_core.split())

    queries: list[str] = []

    # 1. Full cleaned location_desc as one query
    if loc:
        queries.append(f"{loc}, {state}, Australia" if state else f"{loc}, Australia")

    # 2. Each individual line of a multi-line location_desc (last line first —
    #    it's usually "Suburb, STATE POSTCODE")
    if "\n" in raw_loc or "\r" in raw_loc:
        for line in reversed(_loc_lines(raw_loc)):
            if len(line) > 3:
                queries.append(f"{line}, {state}, Australia" if state else f"{line}, Australia")

    # 3. Suburb extracted from a full street address ("Lot X Road, Suburb, SA")
    suburb_q = _suburb_from_address(loc, state) if loc else None
    if suburb_q:
        queries.append(suburb_q)

    # 4. Project site name queries
    if site_core and site_core.lower() not in (loc.lower() if loc else ""):
        queries.append(f"{site_core}, {state}, Australia" if state else f"{site_core}, Australia")
    if site and site_core != site:
        queries.append(f"{site}, {state}, Australia" if state else f"{site}, Australia")

    seen, out = set(), []
    for q in queries:
        k = q.lower()
        if k not in seen and len(q) > 5:
            seen.add(k)
            out.append(q)
    return out


def nominatim(query: str, region: str | None) -> dict | None:
    params = {
        "q": query,
        "format": "json",
        "limit": "1",
        "countrycodes": "au",
        "viewbox": REGION_VIEWBOX.get(region or "", AU_NEM_VIEWBOX),
        "bounded": "1",
    }
    url = "https://nominatim.openstreetmap.org/search?" + urlencode(params)
    req = Request(url, headers={
        "User-Agent": "nem-generation-map/0.1 (contact: expenses.woodenduck@gmail.com)",
        "Accept-Language": "en-AU,en;q=0.9",
    })
    try:
        with urlopen(req, timeout=20) as r:
            data = json.loads(r.read().decode("utf-8"))
            if data:
                d = data[0]
                return {
                    "lat": float(d["lat"]),
                    "lon": float(d["lon"]),
                    "display_name": d.get("display_name", ""),
                }
    except (HTTPError, URLError, TimeoutError, ValueError) as e:
        print(f"  nominatim err: {e}", file=sys.stderr)
    return None


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    projects: list[dict] = json.loads(PROJECTS.read_text(encoding="utf-8"))
    cache: dict = {}
    if CACHE.exists():
        cache = json.loads(CACHE.read_text(encoding="utf-8"))
    print(f"Loaded {len(projects)} projects, {len(cache)} cached Nominatim queries")

    # Strip stale approximate coords from any previous run
    for p in projects:
        p.pop("lat_approx", None)
        p.pop("lon_approx", None)
        p.pop("geocoded", None)          # replaced by geocode_source

    # Fully-trusted sources: DA spatial datasets and manual pins are
    # facility-level GPS — more accurate than GA, Nominatim, or vision.
    # geocode.py never overwrites these.
    TRUSTED = {"VIC_WFS", "QLD_FS", "TAS_FS", "manual", "NSW_DA", "QLD_DA"}

    # Vision priority: vision is the fallback of last resort.
    # Both GA and Nominatim should be given the chance to replace the
    # schematic ±10–30 km PDF position with a real geocode.  If neither
    # finds anything, the vision coords are restored at the end.

    # ── Tier 1: GA matching ──
    print("\nTier 1: matching against GA power stations ...")
    ga_stations = fetch_ga_stations()
    ga_hits = 0
    unmatched: list[dict] = []
    for p in projects:
        # Keep high-accuracy DA/manual coordinates — don't attempt GA overwrite
        if p.get("geocode_source") in TRUSTED:
            continue
        # Save vision coords as fallback before clearing (GA or Nominatim may
        # find something better; if not, these are restored at the end)
        if p.get("geocode_source") == "vision":
            p["_vision_lat"] = p.get("lat")
            p["_vision_lon"] = p.get("lon")
        hit = ga_match(p, ga_stations)
        if hit:
            p["lat"] = hit["lat"]
            p["lon"] = hit["lon"]
            p["geocode_source"] = "GA"
            p["geocode_display"] = hit["ga_name"]
            p.pop("_vision_lat", None)
            p.pop("_vision_lon", None)
            ga_hits += 1
        else:
            # Clear coords so Nominatim gets a fair shot
            p["lat"] = None
            p["lon"] = None
            p["geocode_source"] = None
            unmatched.append(p)
    print(f"  GA matched: {ga_hits}/{len(projects)}")

    # ── Tier 2: Nominatim for remaining ──
    # Includes former vision projects (vision backup saved in _vision_lat/_vision_lon).
    # GA-matched projects are already done and not in unmatched.
    nom_candidates = unmatched
    print(f"\nTier 2: Nominatim for {len(nom_candidates)} unmatched projects ...")
    DELAY = 1.05
    unique_queries: list[tuple[str, str]] = []
    seen: set[str] = set()
    for p in nom_candidates:
        for q in project_queries(p):
            k = q.lower()
            if k not in cache and k not in seen:
                seen.add(k)
                unique_queries.append((q, p.get("region", "")))

    nom_hits = nom_misses = 0
    last_save = time.time()
    for i, (q, region) in enumerate(unique_queries):
        res = nominatim(q, region)
        cache[q.lower()] = res
        if res:
            nom_hits += 1
        else:
            nom_misses += 1
        if (i + 1) % 25 == 0 or i == len(unique_queries) - 1:
            print(f"  [{i+1}/{len(unique_queries)}] hits={nom_hits} misses={nom_misses}  last={q[:80]}")
        if time.time() - last_save > 30:
            CACHE.write_text(json.dumps(cache, indent=2), encoding="utf-8")
            last_save = time.time()
        time.sleep(DELAY)

    CACHE.write_text(json.dumps(cache, indent=2), encoding="utf-8")

    # Apply Nominatim cache to unmatched projects
    # Distinguish suburb-level (location-based query matched) from project-name matches.
    nom_applied = nom_suburb = 0
    for p in nom_candidates:
        state     = p.get("state") or ""
        site      = (p.get("site_name") or "").strip()
        site_core = _STRIP_RE.sub(" ", site).strip(" -–—,.")
        site_core = " ".join(site_core.split())
        # Site-name queries — if one of these matched, accuracy is Nominatim
        site_qs = {q.lower() for q in [
            f"{site_core}, {state}, Australia" if state else f"{site_core}, Australia",
            f"{site}, {state}, Australia" if state else f"{site}, Australia",
        ] if q}

        for q in project_queries(p):
            r = cache.get(q.lower())
            if r:
                p["lat"] = r["lat"]
                p["lon"] = r["lon"]
                # Location-based queries (loc_desc lines, suburb extraction) are
                # town-level accuracy; site-name queries are project-level.
                is_suburb = q.lower() not in site_qs
                p["geocode_source"]  = "suburb" if is_suburb else "Nominatim"
                p["geocode_display"] = r.get("display_name", "")
                p["geocode_query"]   = q
                nom_applied += 1
                if is_suburb:
                    nom_suburb += 1
                break

    # Restore vision coordinates as last-resort fallback for projects that
    # neither GA nor Nominatim could locate.  Vision is the lowest-priority
    # geocode source; if any better source was found above it stays.
    vision_restored = 0
    for p in projects:
        if "_vision_lat" in p:
            if p.get("lat") is None:
                # Neither GA nor Nominatim found this project — fall back to PDF position
                p["lat"] = p["_vision_lat"]
                p["lon"] = p["_vision_lon"]
                p["geocode_source"] = "vision"
                vision_restored += 1
            p.pop("_vision_lat", None)
            p.pop("_vision_lon", None)

    null_count = sum(1 for p in projects if p.get("lat") is None)
    print(f"\nSummary:")
    print(f"  GA matched:        {ga_hits}")
    print(f"  Nominatim matched: {nom_applied - nom_suburb}  (project-name geocode)")
    print(f"  Suburb matched:    {nom_suburb}  (location_desc suburb — dashed border on map)")
    print(f"  Vision restored:   {vision_restored}  (PDF position kept — no GA/Nominatim match)")
    print(f"  No location:       {null_count}  (hidden from map)")

    PROJECTS.write_text(json.dumps(projects, indent=2, default=str), encoding="utf-8")
    print(f"\nWrote {PROJECTS}")


if __name__ == "__main__":
    main()
