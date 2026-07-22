"""Try Squiz search for VIC permit pages, and inspect the register list HTML."""
import urllib.request, urllib.parse, re, json, gzip

BASE = 'https://www.planning.vic.gov.au'
FULL_HDRS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-AU,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate',
    'Referer': f'{BASE}/planning-approvals/ministerial-permits-register/ministerial-permits',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'Upgrade-Insecure-Requests': '1',
}

def fetch(url, accept='text/html,*/*'):
    hdrs = {**FULL_HDRS, 'Accept': accept}
    req = urllib.request.Request(url, headers=hdrs)
    with urllib.request.urlopen(req, timeout=20) as resp:
        raw = resp.read()
        enc = resp.headers.get('Content-Encoding', '')
    if enc == 'gzip' or (raw[:2] == b'\x1f\x8b'):
        raw = gzip.decompress(raw)
    return raw

# 1. Try Squiz search for specific project names
print('=== Squiz search for permit pages ===')
sq_base = 'https://delwp2-search.squiz.cloud/s/search.json'
for query in ['Baddaginnie Solar Farm', 'ministerial permit solar farm 2024']:
    q = urllib.parse.urlencode({'collection': 'delwp-search-global-web', 'query': query, 'num_ranks': '10'})
    url = f'{sq_base}?{q}'
    try:
        raw = fetch(url, accept='application/json,*/*')
        text = raw.decode('utf-8', errors='replace')
        print(f'OK  {url[:100]}')
        try:
            d = json.loads(text)
            results = d.get('results', {}).get('results', [])
            for r in results[:5]:
                print(f'  {r.get("liveUrl", "")}  {r.get("title", "")}')
        except Exception:
            print(f'  {text[:200]}')
    except urllib.error.HTTPError as e:
        print(f'HTTP {e.code}  {url[:100]}')

# 2. Look at the register list page content more carefully
print('\n=== Register list page body ===')
text = open('scripts/vic_list_raw.html', encoding='utf-8').read()

# Find the main content area - look for any table/list with permit names
# Squiz Matrix often embeds data in data-attributes or JSON-LD
json_ld = re.findall(r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', text, re.DOTALL | re.I)
print(f'JSON-LD blocks: {len(json_ld)}')
for jl in json_ld[:3]:
    print(f'  {jl[:300]}')

# Data attributes
data_attrs = re.findall(r'data-(?:permit|guid|id|name|project)[^=]*=["\']([^"\']+)["\']', text, re.I)
print(f'data-* attributes with permit/guid/project: {len(data_attrs)}')
for d in data_attrs[:10]:
    print(f'  {d}')

# Look for any <li> or <tr> that might be a permit row
rows = re.findall(r'<(?:li|tr)[^>]*class=["\'][^"\']*permit[^"\']*["\'][^>]*>(.*?)</(?:li|tr)>', text, re.DOTALL | re.I)
print(f'permit rows: {len(rows)}')
for r in rows[:3]:
    print(f'  {r[:200]}')

# Look for any iframe or embed from Power Apps / Dynamics
iframes = re.findall(r'<iframe[^>]+src=["\']([^"\']+)["\']', text, re.I)
print(f'iframes: {iframes}')

# Content sections
content_divs = re.findall(r'<div[^>]*id=["\']([^"\']+)["\'][^>]*>(.*?)</div>', text, re.DOTALL | re.I)
for cid, cdiv in content_divs:
    if any(k in cid.lower() for k in ['content', 'main', 'body', 'permit', 'list']):
        clean = re.sub(r'<[^>]+>', ' ', cdiv).strip()
        if len(clean) > 20:
            print(f'\nDiv #{cid}: {clean[:200]}')
