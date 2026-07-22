"""
Fetch all QLD SARA decisions from platform.dsdmip.qld.gov.au/decisions,
filter for renewable energy projects, and save a lookup table:
  {norm_name: {"finalisedDate": "YYYY-MM-DD", "referenceNumber": "...", ...}}

The API returns ALL decisions (19k+) without server-side filtering,
so we paginate through everything and filter client-side.

Output: data/inputs/qld_sara_decisions.json
"""
import json, pathlib, re, time, urllib.request, urllib.parse
from datetime import date, datetime

ROOT      = pathlib.Path("C:/projects/AEMO_map")
OUT_FILE  = ROOT / "data/inputs/qld_sara_decisions.json"
PAGE_SIZE = 100
DELAY_S   = 0.3   # polite delay between requests

HDRS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
    "Accept":     "application/json, */*",
    "Referer":    "https://planning.dsdmip.qld.gov.au/",
}

# Keywords that indicate a renewable energy DA
ENERGY_RE = re.compile(
    r"\b(solar|wind|bess|battery|pumped.hydro|hydro|bioenergy|biomass|renewable|"
    r"energy storage|power station|photovoltaic|pv farm|wind turbine)\b",
    re.I,
)

def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9 ]", "", s.lower()).strip()

def fetch_page(page: int) -> dict:
    url = f"https://platform.dsdmip.qld.gov.au/decisions?page={page}&pageSize={PAGE_SIZE}"
    req = urllib.request.Request(url, headers=HDRS)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8", errors="replace"))

def is_energy(rec: dict) -> bool:
    text = " ".join([
        rec.get("natureOfDevelopment") or "",
        rec.get("proposalDetails") or "",
        rec.get("siteAddress") or "",
        rec.get("applicant") or "",
    ])
    return bool(ENERGY_RE.search(text))

def main():
    # Load first page to get total count
    print("Fetching page 1 to get total count...")
    first = fetch_page(1)
    d = first["data"]
    total      = d["totalCount"]
    per_page   = d["perPage"]
    total_pages = (total + per_page - 1) // per_page
    print(f"Total decisions: {total}  |  Pages: {total_pages}  |  Fetching all...")

    energy_hits = []

    for page in range(1, total_pages + 1):
        if page > 1:
            time.sleep(DELAY_S)
        try:
            data = fetch_page(page)
            results = data["data"].get("results") or []
        except Exception as e:
            print(f"  ERROR page {page}: {e}")
            continue

        for rec in results:
            if is_energy(rec):
                energy_hits.append(rec)

        if page % 25 == 0 or page == total_pages:
            print(f"  Page {page}/{total_pages}  —  energy matches so far: {len(energy_hits)}")

    print(f"\nTotal energy-related SARA decisions: {len(energy_hits)}")

    # Print sample
    print("\nSample (first 20):")
    for h in sorted(energy_hits, key=lambda x: x.get("finalisedDate") or "", reverse=True)[:20]:
        dt  = (h.get("finalisedDate") or "")[:10]
        ref = h.get("referenceNumber", "")
        app = (h.get("applicant") or "")[:40]
        nat = (h.get("natureOfDevelopment") or "")[:60]
        prop = (h.get("proposalDetails") or "")[:80]
        addr = (h.get("siteAddress") or "").replace("\r\n", " ")[:60]
        print(f"  {dt}  {ref:<20s}  {app:<40s}")
        print(f"         nature: {nat}")
        print(f"         proposal: {prop}")
        print(f"         addr: {addr}")
        print()

    # Save
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(
        json.dumps(energy_hits, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    print(f"Saved {len(energy_hits)} records to {OUT_FILE}")

if __name__ == "__main__":
    main()
