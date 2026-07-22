"""Fetch the Baddaginnie permit page with browser headers and extract all data."""
import urllib.request, re, json, sys

BASE = 'https://www.planning.vic.gov.au'
PERMIT_GUID = '48f07100-e1b8-ee11-9078-002248922d75'
url = f'{BASE}/planning-approvals/ministerial-permits-register/ministerial-permits/{PERMIT_GUID}'

print(f'Fetching: {url}')
req = urllib.request.Request(url, headers={
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-AU,en;q=0.9',
    'Referer': f'{BASE}/planning-approvals/ministerial-permits-register/ministerial-permits',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'Cache-Control': 'no-cache',
})
try:
    with urllib.request.urlopen(req, timeout=25) as resp:
        raw = resp.read()
    print(f'OK  {len(raw)} bytes')
except urllib.error.HTTPError as e:
    print(f'HTTP {e.code}: {e.reason}')
    sys.exit(1)

text = raw.decode('utf-8', errors='replace')

# Save raw
with open('scripts/baddaginnie_raw.html', 'w', encoding='utf-8') as f:
    f.write(text)
print('Saved to scripts/baddaginnie_raw.html')

# Extract visible text
stripped = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL)
stripped = re.sub(r'<style[^>]*>.*?</style>', '', stripped, flags=re.DOTALL)
clean = re.sub(r'<[^>]+>', ' ', stripped)
clean = re.sub(r'\s+', ' ', clean)

# Find MW/MWh mentions
print('\n=== MW/MWh capacity mentions ===')
for m in re.finditer(r'.{0,100}(?:MW|MWh|megawatt|capacity|Capacity).{0,100}', clean, re.I):
    t = m.group().strip()
    if len(t) > 5 and not t.startswith(('function', 'var ', 'const')):
        print(f'  {t[:200]}')

# Find address/location
print('\n=== Address/location ===')
for m in re.finditer(r'.{0,50}(?:Baddaginnie|VIC 36|address|Address|location|suburb|hectare|ha).{0,100}', clean, re.I):
    t = m.group().strip()
    if len(t) > 5:
        print(f'  {t[:200]}')

# PDF links
print('\n=== PDF / document links ===')
pdfs = re.findall(r'href=["\']([^"\']*\.pdf[^"\']*)["\']', text, re.I)
for p in pdfs:
    print(f'  {p}')

# Any /-/media/ links (Sitecore media library)
media = re.findall(r'href=["\']([^"\']*/-/media/[^"\']+)["\']', text, re.I)
for m in media[:10]:
    print(f'  MEDIA: {m}')

# GUIDs in the page (other permit links etc.)
guids = re.findall(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', text, re.I)
unique_g = list(dict.fromkeys(guids))
print(f'\nGUIDs in page: {len(unique_g)}')
for g in unique_g[:10]:
    print(f'  {g}')

# JSON blobs
print('\n=== JSON embedded ===')
for m in re.finditer(r'(?:window\.\w+|var \w+|const \w+|let \w+)\s*=\s*(\{.{20,2000}?\})\s*;', text, re.DOTALL):
    blob = m.group(1)
    try:
        d = json.loads(blob)
        print(json.dumps(d, indent=2)[:400])
        print('---')
    except Exception:
        pass
