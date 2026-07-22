"""
VIC Ministerial Permits scraper.
Step 1: Extract all permit GUIDs from sitemap.
Step 2: For each permit page, get applicant name + address + PDF links.
Step 3: Match to VIC DA projects in projects.json.
Step 4: For matched permits, download PDFs and extract MW.

Run with:  python scripts/vic_scrape_permits.py [--max N] [--dry-run]
"""
import sys, re, json, time, gzip, os, pathlib, urllib.request, urllib.parse
import pdfminer.high_level as pdfminer_hl
import io

ROOT     = pathlib.Path(__file__).resolve().parent.parent
CACHE    = ROOT / 'scripts' / 'vic_permit_cache'
PROJECTS = ROOT / 'data' / 'intermediate' / 'projects.json'
OUT_JSON = ROOT / 'scripts' / 'vic_permit_data.json'

CACHE.mkdir(exist_ok=True)

BASE = 'https://www.planning.vic.gov.au'
SITEMAP_URL = f'{BASE}/sitemap.xml'

FULL_HDRS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-AU,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate',
    'Referer': f'{BASE}/planning-approvals/ministerial-permits-register',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'Cache-Control': 'no-cache',
    'Upgrade-Insecure-Requests': '1',
}


def fetch_raw(url: str, referer: str = None, timeout: int = 25) -> bytes:
    hdrs = {**FULL_HDRS}
    if referer:
        hdrs['Referer'] = referer
    req = urllib.request.Request(url, headers=hdrs)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read()
        enc = resp.headers.get('Content-Encoding', '')
    if enc == 'gzip' or (raw[:2] == b'\x1f\x8b'):
        raw = gzip.decompress(raw)
    return raw


def _norm(s: str) -> str:
    """Normalise name for fuzzy matching."""
    return re.sub(r'[^a-z0-9]', '', (s or '').lower())


# ── Step 1: Get all permit GUIDs from sitemap ─────────────────────────────────
def get_permit_guids() -> list[str]:
    print('Fetching sitemap...')
    text = fetch_raw(SITEMAP_URL).decode('utf-8', errors='replace')
    urls = re.findall(
        r'https?://www\.planning\.vic\.gov\.au/planning-approvals/ministerial-permits-register/ministerial-permits/([0-9a-f-]{36})',
        text, re.I
    )
    guids = list(dict.fromkeys(urls))  # deduplicate, preserve order
    print(f'  Found {len(guids)} permit GUIDs in sitemap')
    return guids


# ── Step 2: Parse a permit page ───────────────────────────────────────────────
def parse_permit_page(guid: str, html: str) -> dict:
    """Extract name, location, PDF URLs, and MW from permit HTML."""
    # Visible text (strip scripts/styles)
    stripped = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
    stripped = re.sub(r'<style[^>]*>.*?</style>',  '', stripped, flags=re.DOTALL)
    clean = re.sub(r'<[^>]+>', ' ', stripped)
    clean = re.sub(r'&amp;', '&', clean)
    clean = re.sub(r'\s+', ' ', clean).strip()

    # Application number
    app_no = ''
    m = re.search(r'PA\d{6,}', clean)
    if m:
        app_no = m.group()

    # Project name — from title block or heading near application number
    proj_name = ''
    # Look for "Solar Farm", "Wind Farm", "Battery" in project-name-like context
    name_m = re.search(
        r'(?:PA\d+[^\n]*?(?:Birdwood|Solar|Wind|Battery|BESS|Hydro|Energy|Power)[^\n]{0,80})',
        clean, re.I
    )
    if name_m:
        proj_name = name_m.group().strip()[:120]

    # Fallback: look for application name near breadcrumb
    title_m = re.search(r'Ministerial permit:\s*(PA\d+)', html)
    if title_m:
        app_no = app_no or title_m.group(1)

    # Document title may have project name
    doc_title_m = re.search(r'document\.title\s*=\s*"([^"]+)"', html)
    if doc_title_m:
        proj_name = proj_name or doc_title_m.group(1)

    # Address / location — look for VIC postcode pattern after "Address of Land:"
    address = ''
    addr_m = re.search(r'Address of Land:\s*([^\n]{10,150})', clean)
    if addr_m:
        address = addr_m.group(1).strip()
    else:
        # Fallback: VIC postcode
        addr_m2 = re.search(r'([A-Z][a-zA-Z\s\-,]{5,60}VIC\s+\d{4})', clean)
        if addr_m2:
            address = addr_m2.group(1).strip()

    # PDF links (Azure Blob Storage)
    pdf_links = re.findall(
        r'href=["\']('
        r'https://sftpbspomppprod01\.blob\.core\.windows\.net/[^"\']+\.pdf[^"\']*'
        r')["\']',
        html, re.I
    )

    # MW from page text
    mw = None
    mwh = None
    for m in re.finditer(r'([\d,]+(?:\.\d+)?)\s*MW(?:h)?', clean):
        val_str = m.group(1).replace(',', '')
        is_mwh = 'MWh' in m.group() or 'mwh' in m.group() or 'MWH' in m.group()
        try:
            val = float(val_str)
        except ValueError:
            continue
        # Context
        start = max(0, m.start() - 80)
        ctx = clean[start:m.end() + 30].lower()
        if any(k in ctx for k in ['capacity', 'solar', 'wind', 'battery', 'bess', 'generating', 'output', 'installe']):
            if is_mwh:
                if mwh is None:
                    mwh = val
            else:
                if mw is None:
                    mw = val

    return {
        'guid':     guid,
        'app_no':   app_no,
        'name':     proj_name,
        'address':  address,
        'pdf_links': pdf_links,
        'mw':       mw,
        'mwh':      mwh,
    }


# ── Step 3: Extract MW from PDF ───────────────────────────────────────────────
def extract_mw_from_pdf(pdf_url: str, pdf_local: pathlib.Path) -> tuple[float | None, float | None]:
    """Download PDF if needed; extract MW/MWh from text."""
    if not pdf_local.exists():
        try:
            req = urllib.request.Request(pdf_url, headers={
                'User-Agent': FULL_HDRS['User-Agent'],
            })
            with urllib.request.urlopen(req, timeout=90) as resp:
                data = resp.read()
            pdf_local.write_bytes(data)
        except Exception as e:
            print(f'    PDF download error: {e}')
            return None, None

    try:
        text = pdfminer_hl.extract_text(str(pdf_local))
    except Exception as e:
        print(f'    PDF parse error: {e}')
        return None, None

    mw = mwh = None
    for m in re.finditer(r'([\d,]+(?:\.\d+)?)\s*(MW(?:h)?|megawatt)', text, re.I):
        val_str = m.group(1).replace(',', '')
        unit = m.group(2).lower()
        try:
            val = float(val_str)
        except ValueError:
            continue
        if val <= 0 or val > 100_000:
            continue
        start = max(0, m.start() - 120)
        ctx = text[start:m.end() + 80].lower()
        is_mwh = unit in ('mwh', 'megawatt hour', 'megawatt-hour')
        if any(k in ctx for k in ['capacity', 'solar', 'wind', 'battery', 'bess', 'generating',
                                    'output', 'install', 'nameplate', 'rated', 'proposal']):
            if is_mwh:
                if mwh is None:
                    mwh = val
            else:
                if mw is None:
                    mw = val
    return mw, mwh


# ── Step 4: Match permit to VIC DA project ────────────────────────────────────
def load_vic_da_names() -> list[str]:
    projects = json.loads(PROJECTS.read_text(encoding='utf-8'))
    return [p['site_name'] for p in projects if p.get('source', '').startswith('VIC')]


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    max_pages = int(sys.argv[sys.argv.index('--max') + 1]) if '--max' in sys.argv else 9999
    dry_run = '--dry-run' in sys.argv

    # Load existing results
    if OUT_JSON.exists():
        results = json.loads(OUT_JSON.read_text(encoding='utf-8'))
        done_guids = {r['guid'] for r in results}
        print(f'Loaded {len(results)} cached results')
    else:
        results = []
        done_guids = set()

    # Get all permit GUIDs
    guids = get_permit_guids()

    # Load VIC DA project names for quick matching
    vic_names_norm = {_norm(n): n for n in load_vic_da_names()}

    fetched = 0
    for guid in guids:
        if guid in done_guids:
            continue
        if fetched >= max_pages:
            break

        page_url = f'{BASE}/planning-approvals/ministerial-permits-register/ministerial-permits/{guid}'
        cache_file = CACHE / f'{guid}.html'

        # Use cache
        if cache_file.exists():
            html = cache_file.read_text(encoding='utf-8', errors='replace')
        else:
            if dry_run:
                print(f'  [dry-run] Would fetch: {guid}')
                done_guids.add(guid)
                continue
            try:
                time.sleep(3.5)
                raw = fetch_raw(page_url, referer=f'{BASE}/planning-approvals/ministerial-permits-register/ministerial-permits')
                html = raw.decode('utf-8', errors='replace')
                cache_file.write_text(html, encoding='utf-8')
                print(f'  Fetched  {guid}  ({len(html):,} bytes)')
                fetched += 1
            except urllib.error.HTTPError as e:
                print(f'  HTTP {e.code}  {guid}')
                done_guids.add(guid)
                continue
            except Exception as e:
                print(f'  ERR {type(e).__name__}: {e}  {guid}')
                done_guids.add(guid)
                continue

        info = parse_permit_page(guid, html)

        # Check if this matches a VIC DA project
        if info['name']:
            norm_name = _norm(info['name'])
            for vic_norm, vic_orig in vic_names_norm.items():
                if vic_norm in norm_name or norm_name in vic_norm or \
                   _norm(vic_orig.replace(' Solar Farm', '').replace(' Wind Farm', '')) in norm_name:
                    info['matched_project'] = vic_orig
                    print(f'  MATCH: {vic_orig} -> {info["name"][:60]}  MW={info["mw"]}  addr={info["address"][:50]}')
                    break

        results.append(info)
        done_guids.add(guid)

    # Save
    OUT_JSON.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f'\nSaved {len(results)} permit records to {OUT_JSON}')

    # Summary of matched projects
    matched = [r for r in results if r.get('matched_project')]
    print(f'Matched {len(matched)} VIC DA projects:')
    for r in matched:
        print(f'  {r["matched_project"]:50s}  MW={r["mw"]}  addr={r["address"][:50]}')


if __name__ == '__main__':
    main()
