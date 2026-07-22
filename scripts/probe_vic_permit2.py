import sys, re, json
sys.path.insert(0, 'src')
from fetch_cer_da import fetch_url

url = 'https://www.planning.vic.gov.au/planning-approvals/ministerial-permits-register/ministerial-permits/48f07100-e1b8-ee11-9078-002248922d75'
raw = fetch_url(url).decode('utf-8', errors='replace')

# 1. Find all text with numbers near MW
print('=== MW/MWh occurrences ===')
for m in re.finditer(r'.{0,60}(?:MW|megawatt|Megawatt|capacity|Capacity).{0,60}', raw):
    clean = re.sub(r'<[^>]+>', '', m.group()).strip()
    if clean and len(clean) > 5:
        print(' ', clean[:150])

print()
print('=== JSON data blobs ===')
# Look for JSON embedded in the page (common in CMS-backed portals)
for m in re.finditer(r'(\{[^{}]{20,500}\})', raw):
    blob = m.group(1)
    if any(k in blob for k in ['"capacity"', '"mw"', '"MW"', '"power"', '"output"', '"area"', '"hectare"']):
        try:
            parsed = json.loads(blob)
            print(' JSON:', json.dumps(parsed, indent=2)[:300])
        except Exception:
            pass

print()
print('=== API hints ===')
# Look for API URLs or data endpoints
for m in re.finditer(r'(https?://[^\s"\'<>]+(?:api|json|data|query)[^\s"\'<>]*)', raw, re.IGNORECASE):
    print(' ', m.group(1)[:120])

print()
print('=== Location / address ===')
for m in re.finditer(r'.{0,30}(?:Baddaginnie|VIC 36|address|Address|location|Location|suburb|Suburb).{0,80}', raw):
    clean = re.sub(r'<[^>]+>', '', m.group()).strip()
    if clean:
        print(' ', clean[:150])
