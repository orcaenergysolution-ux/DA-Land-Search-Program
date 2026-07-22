"""Debug the 7 NSW_DA projects with missing MW capacity."""
import sys, re, json
sys.path.insert(0, 'src')
from fetch_cer_da import fetch_url

MISSING_NSW = {
    'homebush battery energy storage system',
    'hume battery energy storage system',
    'liddell battery and bayswater ancillary works',
    'moree battery energy storage sysytem',
    'penrith hv',
    # find the other 2
}

URL = 'https://www.planning.nsw.gov.au/policy-and-legislation/renewable-energy'
print('Fetching NSW page...')
raw = fetch_url(URL).decode('utf-8', errors='replace')

DIALOG_RE = re.compile(
    r'<caption>Full details for entry ([^<]+)</caption>(.*?)</table>',
    re.DOTALL,
)
KV_RE = re.compile(
    r'<th>\s*<p>([^<]+)</p>\s*</th>\s*<td>\s*<p>(.*?)</p>',
    re.DOTALL,
)

def strip_html(s):
    return re.sub(r'<[^>]+>', '', s).strip()

for m in DIALOG_RE.finditer(raw):
    proj_name = m.group(1).strip()
    body = m.group(2)
    kv = {strip_html(k): strip_html(v) for k, v in KV_RE.findall(body)}

    name_low = proj_name.lower()
    # Check if this is one of our missing projects or if it has no MW
    mw_str = kv.get('Generating Capacity (MW)', '')
    mw = None
    if mw_str and mw_str != 'N/A':
        try: mw = float(re.sub(r'[^\d.]', '', mw_str))
        except ValueError: pass

    if mw is None and kv:
        # print all keys for this project
        print(f'\n--- {proj_name} ---')
        for k, v in kv.items():
            if v and v != 'N/A':
                print(f'  {k}: {v}')
