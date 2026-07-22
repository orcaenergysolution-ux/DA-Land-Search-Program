"""Parse the VIC ministerial permits register list page."""
import urllib.request, re, json, sys

BASE = 'https://www.planning.vic.gov.au'
url = f'{BASE}/planning-approvals/ministerial-permits-register/ministerial-permits'
req = urllib.request.Request(url, headers={
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-AU,en;q=0.9',
    'Referer': f'{BASE}/planning-approvals/ministerial-permits-register',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
})
with urllib.request.urlopen(req, timeout=20) as resp:
    raw = resp.read()

text = raw.decode('utf-8', errors='replace')
print(f'Page size: {len(text)} bytes')

# SPA markers
markers = ['React', '__NEXT_DATA__', 'angular', 'PowerApps', 'powerpages',
           'msdynmkt', 'dynamics', 'MicrosoftAjax', 'crm.dynamics', 'OData']
for m in markers:
    if m.lower() in text.lower():
        print(f'-> Found marker: {m}')

# Links with ministerial-permits in them
links = re.findall(r'href=["\']([^"\']*ministerial[^"\']*)["\']', text, re.I)
print(f'\nMinisterial links ({len(links)}):')
for l in links[:10]:
    print(f'  {l}')

# API / data endpoints
api_calls = re.findall(r'https?://[^\s"\'<>]+(?:api|odata|entity|data|query)[^\s"\'<>]*', text, re.I)
print(f'\nAPI endpoints ({len(api_calls)}):')
for a in api_calls[:10]:
    print(f'  {a}')

# Visible text
stripped = re.sub(r'<[^>]+>', '', text)
lines = [l.strip() for l in stripped.splitlines() if l.strip() and len(l.strip()) > 10]
print(f'\nFirst 40 text lines:')
for l in lines[:40]:
    print(f'  {l[:120]}')

# Save raw for inspection
with open('scripts/vic_list_raw.html', 'w', encoding='utf-8') as f:
    f.write(text)
print('\nSaved to scripts/vic_list_raw.html')
