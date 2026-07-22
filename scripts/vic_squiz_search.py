"""
Try the Squiz Cloud search engine used by planning.vic.gov.au to find
all ministerial permit pages (which contain the GUID in their URL).
"""
import urllib.request, urllib.parse, re, json, time

SQUIZ_BASE = 'https://delwp2-search.squiz.cloud'
PLANNING_BASE = 'https://www.planning.vic.gov.au'

# Squiz Funnelback search — common query patterns
search_queries = [
    # Look for permit pages
    f'{SQUIZ_BASE}/s/search.json?collection=dpltd-web&query=ministerial+permits+solar+wind+battery&num_ranks=50',
    f'{SQUIZ_BASE}/s/search.json?collection=dpltd-web&query=ministerial+permits+register&num_ranks=50',
    f'{PLANNING_BASE}/api/search?q=ministerial+permits&format=json',
    # Try Squiz with site-specific collection
    f'{SQUIZ_BASE}/s/search.json?collection=planning-vic&query=solar+wind+battery+permit&num_ranks=50',
    f'{SQUIZ_BASE}/s/search.json?query=ministerial+permits+solar&num_ranks=50',
]

# Also try the Power Pages API
PP_ENDPOINTS = [
    f'{PLANNING_BASE}/_api/cr0e3_ministerialpermitrequests?$select=cr0e3_name,cr0e3_capacity&$top=5',
    f'{PLANNING_BASE}/_api/cr0e3_ministerialpermitrequests?$top=5',
    f'{PLANNING_BASE}/api/data/v9.2/cr0e3_ministerialpermitrequests?$top=5',
    f'{PLANNING_BASE}/_api/lists/GetByTitle(\'MinisterialPermits\')/items?$top=5',
]

HDRS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-AU,en;q=0.9',
    'Referer': f'{PLANNING_BASE}/planning-approvals/ministerial-permits-register/ministerial-permits',
}

print('=== Squiz / search endpoints ===')
for url in search_queries:
    try:
        req = urllib.request.Request(url, headers=HDRS)
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read()
        print(f'OK  ({len(raw)} bytes)  {url[:100]}')
        try:
            d = json.loads(raw)
            print(f'  JSON: {str(d)[:300]}')
        except Exception:
            text = raw.decode('utf-8', errors='replace')
            guids = re.findall(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', text)
            print(f'  GUIDs: {len(guids)}  Text preview: {text[:200]}')
    except urllib.error.HTTPError as e:
        print(f'HTTP {e.code}  {url[:100]}')
    except Exception as e:
        print(f'ERR  {type(e).__name__}: {e}  {url[:80]}')
    time.sleep(2)

print()
print('=== Power Pages / Dynamics API endpoints ===')
for url in PP_ENDPOINTS:
    try:
        req = urllib.request.Request(url, headers={**HDRS, 'Accept': 'application/json'})
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read()
        print(f'OK  ({len(raw)} bytes)  {url[:100]}')
        print(f'  {raw[:300].decode("utf-8", errors="replace")}')
    except urllib.error.HTTPError as e:
        print(f'HTTP {e.code}  {url[:100]}')
    except Exception as e:
        print(f'ERR  {type(e).__name__}: {e}  {url[:80]}')
    time.sleep(1)
