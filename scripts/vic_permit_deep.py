"""Fetch VIC permit page, extract location + PDF links, then parse PDF for MW."""
import sys, re, time, urllib.request, json
sys.path.insert(0, 'src')
from fetch_cer_da import fetch_url

PERMIT_URL = ('https://www.planning.vic.gov.au/planning-approvals/'
              'ministerial-permits-register/ministerial-permits/'
              '48f07100-e1b8-ee11-9078-002248922d75')

print('Fetching permit page...')
time.sleep(2)
raw = fetch_url(PERMIT_URL).decode('utf-8', errors='replace')
print(f'  Got {len(raw)} bytes')

# ── 1. Location/address ───────────────────────────────────────────────────────
print('\n=== All visible text snippets (stripped HTML) ===')
# Remove scripts and styles first
stripped = re.sub(r'<script[^>]*>.*?</script>', '', raw, flags=re.DOTALL)
stripped = re.sub(r'<style[^>]*>.*?</style>',  '', stripped, flags=re.DOTALL)
# Get all text nodes
texts = re.findall(r'>([^<]{5,})<', stripped)
seen = set()
for t in texts:
    t = t.strip()
    if t and t not in seen and not t.startswith(('function','var ','const ','//','/*')):
        seen.add(t)
        if any(k in t for k in ['MW', 'MWh', 'megawatt', 'Baddaginnie', 'capacity',
                                  'hectare', 'ha', 'address', 'location', 'VIC 36',
                                  'solar', 'Solar', '50', '100', '150', '200']):
            print(f'  [{t[:150]}]')

# ── 2. PDF links ──────────────────────────────────────────────────────────────
print('\n=== PDF / document links ===')
pdf_links = re.findall(r'href=["\']([^"\']*\.pdf[^"\']*)["\']', raw, re.IGNORECASE)
for link in pdf_links:
    print(f'  {link}')

# ── 3. JSON blobs in page ─────────────────────────────────────────────────────
print('\n=== Embedded JSON ===')
for m in re.finditer(r'(?:window\.\w+|var \w+)\s*=\s*(\{.*?\});', raw, re.DOTALL):
    blob = m.group(1)
    if len(blob) > 50:
        try:
            d = json.loads(blob)
            print(json.dumps(d, indent=2)[:400])
        except Exception:
            pass
