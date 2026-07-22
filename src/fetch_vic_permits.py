"""
VIC Ministerial Permits scraper.

Fetches permit pages for VIC DA projects from planning.vic.gov.au and
extracts capacity (MW/MWh) + address.  Results are cached in
data/inputs/vic_permit_cache/ so each page is only fetched once.

Entry point:
    apply_vic_permit_data(projects, dry_run=False) -> int

Called from fetch_cer_da.main() after the VIC WFS merge.
"""
from __future__ import annotations

import gzip
import json
import pathlib
import re
import sys
import time
import urllib.request
import urllib.error
from typing import Optional

try:
    import pdfminer.high_level as _pdfminer
    _HAVE_PDFMINER = True
except ImportError:
    _HAVE_PDFMINER = False

ROOT       = pathlib.Path(__file__).resolve().parent.parent
CACHE_DIR  = ROOT / "data" / "inputs" / "vic_permit_cache"
INDEX_FILE = ROOT / "data" / "inputs" / "vic_permit_index.json"

CACHE_DIR.mkdir(parents=True, exist_ok=True)

BASE          = "https://www.planning.vic.gov.au"
SITEMAP_URL   = f"{BASE}/sitemap.xml"
PERMIT_PREFIX = f"{BASE}/planning-approvals/ministerial-permits-register/ministerial-permits/"
PERMIT_RE     = re.compile(
    r"https?://www\.planning\.vic\.gov\.au"
    r"/planning-approvals/ministerial-permits-register/ministerial-permits/"
    r"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})",
    re.I,
)

BROWSER_HDRS = {
    "User-Agent":      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-AU,en;q=0.9",
    "Accept-Encoding": "gzip, deflate",
    "Referer":         f"{BASE}/planning-approvals/ministerial-permits-register/ministerial-permits",
    "sec-fetch-dest":  "document",
    "sec-fetch-mode":  "navigate",
    "sec-fetch-site":  "same-origin",
    "Upgrade-Insecure-Requests": "1",
}

DELAY_S = 4.0   # seconds between requests to planning.vic.gov.au


# ── helpers ───────────────────────────────────────────────────────────────────

def _norm(s: str | None) -> str:
    return re.sub(r"[^a-z0-9 ]", " ", (s or "").lower()).strip()


def _fetch_raw(url: str, timeout: int = 30) -> bytes:
    req = urllib.request.Request(url, headers=BROWSER_HDRS)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read()
        enc = resp.headers.get("Content-Encoding", "")
    if enc == "gzip" or (raw[:2] == b"\x1f\x8b"):
        raw = gzip.decompress(raw)
    return raw


# ── Step 1: get all permit GUIDs from sitemap ─────────────────────────────────

def _get_all_guids() -> list[str]:
    """Return all permit GUIDs from planning.vic.gov.au sitemap (cached)."""
    sitemap_cache = CACHE_DIR / "_sitemap_guids.json"
    if sitemap_cache.exists():
        guids = json.loads(sitemap_cache.read_text(encoding="utf-8"))
        print(f"  [VIC permits] Loaded {len(guids)} permit GUIDs from sitemap cache")
        return guids

    print("  [VIC permits] Fetching sitemap...")
    try:
        raw = _fetch_raw(SITEMAP_URL)
        text = raw.decode("utf-8", errors="replace")
    except Exception as e:
        print(f"  [VIC permits] Sitemap fetch failed: {e}", file=sys.stderr)
        return []

    guids = list(dict.fromkeys(PERMIT_RE.findall(text)))
    print(f"  [VIC permits] Found {len(guids)} permit GUIDs in sitemap")
    sitemap_cache.write_text(json.dumps(guids), encoding="utf-8")
    return guids


# ── Step 2: parse permit page HTML ────────────────────────────────────────────

def _parse_permit_html(guid: str, html: str) -> dict:
    """Extract app_no, address, PDF URLs, and any inline MW from permit page."""
    # Strip scripts/styles for clean text
    stripped = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL)
    stripped = re.sub(r"<style[^>]*>.*?</style>",  "", stripped, flags=re.DOTALL)
    clean = re.sub(r"<[^>]+>", " ", stripped)
    clean = re.sub(r"&amp;", "&", clean)
    clean = re.sub(r"\s+", " ", clean).strip()

    # Application number
    app_m = re.search(r"(PA\d{6,}(?:-\d+)?)", clean)
    app_no = app_m.group(1) if app_m else ""

    # Address — stop at postcode or first double-space / "Program" / "Contact"
    address = ""
    addr_m = re.search(r"Address of Land:\s*([^\n]{10,250})", clean)
    if addr_m:
        raw_addr = addr_m.group(1).strip()
        # Trim at end of VIC postcode
        postcode_m = re.search(r"VIC\s+\d{4}", raw_addr)
        if postcode_m:
            raw_addr = raw_addr[:postcode_m.end()]
        # Or trim at first "Program" / "Contact" / double-space
        for stop in [" Program", " Contact", "  "]:
            idx = raw_addr.find(stop)
            if idx > 5:
                raw_addr = raw_addr[:idx]
        address = raw_addr.strip()
    if not address:
        addr_m2 = re.search(r"([A-Za-z][a-zA-Z0-9 ,\-]{10,60}VIC\s+\d{4})", clean)
        if addr_m2:
            address = addr_m2.group(1).strip()

    # PDF links (Azure Blob Storage — always accessible)
    pdf_links = re.findall(
        r'href=["\']('
        r'https://sftpbspomppprod01\.blob\.core\.windows\.net/applicationfiles/[^"\']+\.pdf[^"\']*'
        r')["\']',
        html, re.I,
    )

    # Inline MW/MWh from clean text
    mw = mwh = None
    for m in re.finditer(r"([\d,]+(?:\.\d+)?)\s*MW(h)?", clean, re.I):
        val_str = m.group(1).replace(",", "")
        is_mwh = bool(m.group(2))
        try:
            val = float(val_str)
        except ValueError:
            continue
        if val <= 0 or val > 50_000:
            continue
        start = max(0, m.start() - 100)
        ctx = clean[start:m.end() + 60].lower()
        if any(k in ctx for k in ["capacity", "solar", "wind", "battery", "bess",
                                    "generating", "install", "output", "proposal",
                                    "construction of"]):
            if is_mwh:
                mwh = mwh if mwh is not None else val
            else:
                mw  = mw  if mw  is not None else val

    return {
        "guid":      guid,
        "app_no":    app_no,
        "address":   address,
        "pdf_links": pdf_links[:2],   # keep officer report + planning permit
        "mw":        mw,
        "mwh":       mwh,
    }


# ── Step 3: extract MW from PDF ───────────────────────────────────────────────

def _pdf_mw(pdf_url: str, guid: str) -> tuple[Optional[float], Optional[float]]:
    """Download PDF (cached) and extract MW/MWh using pdfminer."""
    if not _HAVE_PDFMINER:
        return None, None

    fname = re.sub(r"[^\w\.\-]", "_", pdf_url.split("/")[-1])[:80]
    local = CACHE_DIR / f"{guid}_{fname}.pdf"

    if not local.exists():
        try:
            req = urllib.request.Request(
                pdf_url,
                headers={"User-Agent": BROWSER_HDRS["User-Agent"]},
            )
            with urllib.request.urlopen(req, timeout=90) as resp:
                data = resp.read()
            local.write_bytes(data)
        except Exception as e:
            print(f"  [VIC permits] PDF download failed: {e}", file=sys.stderr)
            return None, None

    try:
        text = _pdfminer.extract_text(str(local))
    except Exception as e:
        print(f"  [VIC permits] PDF parse failed: {e}", file=sys.stderr)
        return None, None

    # Strip lines that look like file paths (e.g. "File Path: M:\Projects\MD924 mwes\...")
    # — these can contain project codes like "MD924" followed by "mw..." causing false positives.
    text = re.sub(r"(?im)^.*(?:file\s*path|file\s*name|\\\\|[A-Z]:\\)[^\n]*$", "", text)

    mw = mwh = None
    for m in re.finditer(r"([\d,]+(?:\.\d+)?)\s*MW(h)?", text, re.I):
        val_str = m.group(1).replace(",", "")
        is_mwh = bool(m.group(2))
        try:
            val = float(val_str)
        except ValueError:
            continue
        if val <= 0 or val > 50_000:
            continue
        start = max(0, m.start() - 120)
        ctx = text[start:m.end() + 80].lower()
        if any(k in ctx for k in ["capacity", "solar", "wind", "battery", "bess",
                                    "generating", "install", "output", "proposal",
                                    "construction of", "nameplate", "rated"]):
            if is_mwh:
                mwh = mwh if mwh is not None else val
            else:
                mw  = mw  if mw  is not None else val
    return mw, mwh


# ── Step 4: build / update the permit index ───────────────────────────────────

def _load_index() -> dict[str, dict]:
    """Load cached permit data keyed by guid."""
    if INDEX_FILE.exists():
        return json.loads(INDEX_FILE.read_text(encoding="utf-8"))
    return {}


def _save_index(index: dict) -> None:
    INDEX_FILE.write_text(json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8")


def _priority_guids(all_guids: list[str]) -> list[str]:
    """
    Return GUIDs sorted so we scan newest permits first.

    Dynamics 365 GUIDs embed a time component in bytes 4-6 of the
    third group.  Newer energy DA permits (2020+) have patterns like
    ec11, ed11, ee11, ef11, f011, f111 in the third group, while old
    2018-era residential permits have e811, e911.

    Strategy: split into "newer" (≥ec11) and "older", scan newer first
    in REVERSE sitemap order (most recent at the end of the sitemap).
    """
    import re as _re
    newer, older = [], []
    for g in all_guids:
        parts = g.split("-")
        grp3 = parts[2] if len(parts) > 2 else ""
        # ec11 and above are likely 2020+ permits
        if _re.match(r"[e-f][c-f][0-9a-f]{2}", grp3, _re.I):
            newer.append(g)
        else:
            older.append(g)
    # Newer group reversed (most recent last in sitemap → first in reversed)
    return list(reversed(newer)) + list(reversed(older))


def _match_permit(html: str, pdf_links: list[str], address: str,
                  target_norm: str) -> bool:
    """
    Return True if this permit page appears to be for `target_norm`.

    Matches on:
      1. Distinctive words from the project name in the PDF filenames
         (most reliable — filenames always contain the project name)
      2. Distinctive words in the full visible page text
      3. Distinctive suburb/location word in the address field
    """
    # Build list of "distinctive" words (skip generic terms)
    SKIP = {"farm", "solar", "wind", "battery", "bess", "energy", "power",
            "project", "stage", "park", "station", "plant", "hub",
            "extension", "expansion", "renewable", "generation", "storage"}
    words = [w for w in target_norm.split() if len(w) > 3 and w not in SKIP]
    if not words:
        # Fallback: use all words including short ones
        words = [w for w in target_norm.split() if len(w) > 2]
    if not words:
        return False

    # 1. Check PDF URL filenames (most reliable)
    pdf_text = " ".join(_norm(url) for url in pdf_links)
    if pdf_text and all(w in pdf_text for w in words):
        return True

    # 2. Check full page text (strip HTML first to reduce noise)
    stripped = re.sub(r"<[^>]+>", " ", html)
    stripped = re.sub(r"\s+", " ", stripped)
    page_norm = _norm(stripped)
    if all(w in page_norm for w in words):
        return True

    # 3. Check address specifically (suburb name often in project name)
    addr_norm = _norm(address)
    if addr_norm and all(w in addr_norm for w in words[:1]):
        return True

    return False


def _scrape_missing(target_norm_names: set[str], index: dict,
                     max_pages: int = 400) -> None:
    """
    Fetch permit pages we haven't seen yet, stopping once:
      - all target project names are found, OR
      - we've fetched max_pages new pages.

    Prioritises newest permits (energy-era GUIDs, reverse sitemap order).
    """
    all_guids = _get_all_guids()
    guids     = _priority_guids(all_guids)
    fetched   = 0
    remaining = set(target_norm_names)

    # Remove already-matched targets from 'remaining'
    for rec in index.values():
        for n in rec.get("matched_names", []):
            remaining.discard(n)

    if not remaining:
        return  # nothing to do

    print(f"  [VIC permits] Need to find {len(remaining)} VIC project(s); "
          f"scanning up to {max_pages} permit pages (newest-first)...")

    done_guids = set(index.keys())

    for guid in guids:
        if not remaining:
            break
        if fetched >= max_pages:
            break
        if guid in done_guids:
            continue

        page_url = f"{PERMIT_PREFIX}{guid}"
        cache_f  = CACHE_DIR / f"{guid}.html"

        # Use disk cache (never re-download a cached page)
        if cache_f.exists():
            html = cache_f.read_text(encoding="utf-8", errors="replace")
        else:
            try:
                time.sleep(DELAY_S)
                raw  = _fetch_raw(page_url)
                html = raw.decode("utf-8", errors="replace")
                cache_f.write_text(html, encoding="utf-8")
                fetched += 1
            except urllib.error.HTTPError as e:
                index[guid] = {"guid": guid, "error": e.code}
                done_guids.add(guid)
                _save_index(index)
                continue
            except Exception as e:
                index[guid] = {"guid": guid, "error": str(e)}
                done_guids.add(guid)
                continue

        info = _parse_permit_html(guid, html)

        # Try to match against remaining VIC DA project names
        matched = []
        for target in list(remaining):
            if _match_permit(html, info["pdf_links"], info["address"], target):
                matched.append(target)
                remaining.discard(target)

        if matched:
            # Get MW from PDF if not already in HTML
            mw, mwh = info["mw"], info["mwh"]
            if (mw is None or mwh is None) and info["pdf_links"]:
                pdf_mw, pdf_mwh = _pdf_mw(info["pdf_links"][0], guid)
                mw  = mw  if mw  is not None else pdf_mw
                mwh = mwh if mwh is not None else pdf_mwh

            info["mw"]  = mw
            info["mwh"] = mwh
            info["matched_names"] = matched
            print(f"  [VIC permits] MATCH {matched}  MW={mw}  MWh={mwh}  addr={info['address'][:50]}")
        else:
            info["matched_names"] = []

        index[guid] = info
        done_guids.add(guid)

    _save_index(index)
    if remaining:
        print(f"  [VIC permits] {len(remaining)} project(s) not yet found "
              f"(index has {len(index)} records; run again to scan more)")


# ── Public API ────────────────────────────────────────────────────────────────

def apply_vic_permit_data(projects: list[dict], dry_run: bool = False,
                           scrape_missing: bool = False) -> int:
    """
    Fill capacity_mw, storage_mwh, and location_desc for VIC DA projects
    using the cached ministerial permit index.  Returns the count updated.

    scrape_missing=False (default, pipeline mode):
        Only uses the pre-built index — no live HTTP requests.
        Run scripts/run_vic_permit_scraper.py separately to build the cache.

    scrape_missing=True (explicit mode):
        Fetches up to 400 new permit pages for unmatched projects.
    """
    vic_da = [p for p in projects
              if "VIC" in p.get("source", "") and p.get("state") == "VIC"
              and (p.get("capacity_mw") is None
                   or p.get("storage_mwh") is None
                   or not p.get("location_desc"))]

    if not vic_da:
        return 0

    print(f"\n=== VIC Ministerial Permits supplement ({len(vic_da)} projects need data) ===")

    # Build lookup from index
    index = _load_index()

    # Map norm-name → record
    name_to_rec: dict[str, dict] = {}
    for rec in index.values():
        for nm in rec.get("matched_names", []):
            name_to_rec[nm] = rec

    if scrape_missing:
        # Which targets still need scraping?
        need_scrape: set[str] = set()
        for p in vic_da:
            nm = _norm(p.get("site_name", ""))
            if nm and nm not in name_to_rec:
                need_scrape.add(nm)

        if need_scrape:
            _scrape_missing(need_scrape, index)
            # Rebuild lookup after scraping
            name_to_rec = {}
            for rec in index.values():
                for nm in rec.get("matched_names", []):
                    name_to_rec[nm] = rec
    else:
        cached = sum(1 for rec in index.values() if rec.get("matched_names"))
        print(f"  Using cached index ({len(index)} records, {cached} matches). "
              f"Run run_vic_permit_scraper.py to expand.")

    # Apply to projects
    updated = 0
    for p in vic_da:
        nm  = _norm(p.get("site_name", ""))
        rec = name_to_rec.get(nm)
        if not rec:
            continue

        # MW consistency guard: if the permit has a MW value and the project already
        # has one, they should be within 3× of each other.  A large mismatch means
        # the permit was matched to the wrong project (e.g. a 4.95 MW connection
        # permit matching a 225 MW wind farm); skip it entirely in that case.
        permit_mw  = rec.get("mw")
        project_mw = p.get("capacity_mw")
        if permit_mw and project_mw:
            ratio = permit_mw / project_mw
            if not (1 / 3 <= ratio <= 3):
                continue   # mismatched permit — skip

        # MWh sanity guard: permit documents sometimes contain large numbers
        # (fees, areas, lot numbers) that get mistakenly parsed as MWh.
        # Reject any MWh value that is more than 20× the project's or permit's MW,
        # whichever is known.
        permit_mwh = rec.get("mwh")
        ref_mw = project_mw or permit_mw
        if permit_mwh and ref_mw and permit_mwh > ref_mw * 20:
            permit_mwh = None   # discard bogus value

        changed = False
        if p.get("capacity_mw") is None and permit_mw is not None:
            if not dry_run:
                p["capacity_mw"] = permit_mw
            changed = True
        if p.get("storage_mwh") is None and permit_mwh is not None:
            if not dry_run:
                p["storage_mwh"] = permit_mwh
            changed = True
        if not p.get("location_desc") and rec.get("address"):
            addr = rec["address"]
            # Only use address if it looks like a land address (regional/rural),
            # not a Melbourne metro office (postcode 3000-3299 or known inner suburbs).
            # Multi-match records often have the applicant's office as the land address.
            postcode_m = re.search(r"\b(3\d{3})\b", addr)
            is_metro = False
            if postcode_m:
                pc = int(postcode_m.group(1))
                is_metro = (3000 <= pc <= 3299)  # Melbourne metro postcodes
            # Also flag if address contains known office-area suburb names
            OFFICE_SUBURBS = {
                "docklands", "richmond", "carlton", "south yarra", "brunswick",
                "footscray", "north melbourne", "ivanhoe", "balwyn", "flemington",
                "south melbourne", "st kilda", "collingwood", "fitzroy", "abbotsford",
                "hawthorn", "prahran", "malvern",
                "heidelberg", "heidelberg west", "heidelberg heights",
                "box hill", "glen waverley", "mount waverley", "burwood",
            }
            addr_lower = addr.lower()
            if any(s in addr_lower for s in OFFICE_SUBURBS):
                is_metro = True
            # For multi-match records, only use address if it's clearly regional
            is_multi = len(rec.get("matched_names", [])) > 1
            if not is_metro and (not is_multi or len(rec.get("matched_names", [])) == 1):
                if not dry_run:
                    p["location_desc"] = addr
            changed = True

        if changed:
            updated += 1
            print(f"  [VIC permits] {p['site_name'][:55]:55s} "
                  f"mw={rec.get('mw')} mwh={rec.get('mwh')} "
                  f"addr={rec.get('address', '')[:40]}")

    print(f"  VIC permit supplement filled data for {updated} projects")
    return updated
