"""Analyze VIC register list HTML for API endpoints and permit data."""
import re

text = open('scripts/vic_list_raw.html', encoding='utf-8').read()
print(f'Total size: {len(text)} bytes')

# Look for GUIDs anywhere in the page
guids = re.findall(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', text, re.I)
print(f'\nGUIDs found: {len(guids)}')
if guids:
    for g in guids[:5]:
        print(f'  {g}')

# Look for any iframe or embed
iframes = re.findall(r'<iframe[^>]+>', text, re.I)
print(f'\niframes ({len(iframes)}):')
for i in iframes[:5]:
    print(f'  {i[:200]}')

# Power Pages / Dynamics / OData markers
markers = ['api/data', '_odata', 'OData', 'EntitySet', 'PowerApps', 'powerpages',
           'modeldriven', 'microsoftdynamics', 'dynamics365', 'crm', 'msdyn']
for marker in markers:
    hits = [m.group().strip() for m in re.finditer(r'.{0,80}' + re.escape(marker) + r'.{0,80}', text, re.I)]
    if hits:
        print(f'\n== {marker} ==')
        for h in hits[:3]:
            print(f'  {h[:150]}')

# Any data URLs with permit/register
urls = re.findall(r'https?://[^\s"\'<>]{20,200}', text)
permit_urls = [u for u in urls if any(k in u.lower() for k in ['permit', 'register', 'renew', 'energy', 'solar', 'wind'])]
print(f'\nPermit-related URLs ({len(permit_urls)}):')
for u in list(dict.fromkeys(permit_urls))[:10]:
    print(f'  {u[:140]}')

# JavaScript API calls
js_api = re.findall(r'fetch\s*\(\s*["\']([^"\']+)["\']', text)
js_xhr = re.findall(r'XMLHttpRequest[^;]{0,200}open\([^)]+["\']([^"\']+)["\']', text, re.DOTALL)
print(f'\nfetch() calls ({len(js_api)}): {js_api[:5]}')
print(f'XHR calls ({len(js_xhr)}): {js_xhr[:5]}')

# Squiz search config
m = re.search(r'globalThis\.cms\s*=\s*\{([^}]{1,3000})', text, re.DOTALL)
if m:
    print(f'\nSquiz CMS config:\n{m.group(1)[:600]}')
