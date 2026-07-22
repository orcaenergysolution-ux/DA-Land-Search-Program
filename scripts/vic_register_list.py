"""
Try to access VIC ministerial permits register list — look for JSON API,
search endpoints, or a downloadable index that maps project names to permit GUIDs.
"""
import sys, re, time, json
sys.path.insert(0, 'src')
from fetch_cer_da import fetch_url

BASE = 'https://www.planning.vic.gov.au'

candidates = [
    f'{BASE}/planning-approvals/ministerial-permits-register',
    f'{BASE}/planning-approvals/ministerial-permits-register/ministerial-permits',
    # Sitecore content delivery endpoints (common in VIC Govt sites)
    f'{BASE}/api/sitecore/GetItems?path=ministerial-permits&format=json',
    f'{BASE}/-/media/ministerial-permits.json',
    # Power Pages entity list OData
    f'{BASE}/ministerialpermitrequests?$select=cr0e3_name,cr0e3_capacity&$format=json',
]

for url in candidates:
    try:
        time.sleep(3)
        raw = fetch_url(url)
        print(f'OK  ({len(raw)} bytes)  {url}')
        # Check for JSON
        try:
            d = json.loads(raw)
            print('  -> Valid JSON:', str(d)[:200])
        except Exception:
            # Look for embedded data or permit links
            text = raw.decode('utf-8', errors='replace')
            # GUID pattern used in permit URLs
            guids = re.findall(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', text)
            if guids:
                print(f'  -> Found {len(guids)} GUIDs: {guids[:3]}')
            # PDF links
            pdfs = re.findall(r'href=["\']([^"\']*\.pdf)["\']', text, re.I)
            if pdfs:
                print(f'  -> Found {len(pdfs)} PDFs: {pdfs[:3]}')
    except Exception as e:
        code = getattr(e, 'code', type(e).__name__)
        print(f'{code}  {url}')
