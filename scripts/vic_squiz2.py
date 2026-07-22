"""Use Squiz search to find permit URLs for VIC DA projects."""
import urllib.request, urllib.parse, re, json, gzip, time

BASE = 'https://www.planning.vic.gov.au'
SQ_SEARCH = 'https://delwp2-search.squiz.cloud/s/search.json'

HDRS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'application/json,*/*',
    'Accept-Language': 'en-AU,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate',
    'Referer': f'{BASE}/planning-approvals/ministerial-permits-register/ministerial-permits',
}

def squiz_search(query: str, num: int = 20) -> list[dict]:
    params = urllib.parse.urlencode({
        'collection': 'delwp-search-global-web',
        'query': query,
        'num_ranks': str(num),
        'profile': '_default',
    })
    url = f'{SQ_SEARCH}?{params}'
    req = urllib.request.Request(url, headers=HDRS)
    with urllib.request.urlopen(req, timeout=20) as resp:
        raw = resp.read()
        enc = resp.headers.get('Content-Encoding', '')
    if enc == 'gzip' or raw[:2] == b'\x1f\x8b':
        raw = gzip.decompress(raw)
    return json.loads(raw.decode('utf-8'))


# Test with Baddaginnie
print('=== Search: Baddaginnie Solar Farm ===')
result = squiz_search('Baddaginnie Solar Farm')
print(f'Total matching: {result.get("total_matching", "?")}')
print(f'Result structure keys: {list(result.keys())}')

# Dig into results
results_data = result.get('results', result.get('response', {}))
print(f'results_data type: {type(results_data)}')
if isinstance(results_data, dict):
    print(f'  keys: {list(results_data.keys())}')
    inner = results_data.get('results', results_data.get('resultsSummary', []))
    for r in (inner if isinstance(inner, list) else [])[:5]:
        print(f'  URL: {r.get("liveUrl", r.get("url", "?"))}')
        print(f'  Title: {r.get("title", "?")}')
elif isinstance(results_data, list):
    for r in results_data[:5]:
        print(f'  {r}')

# Print raw structure
print('\nFull JSON (first 2000 chars):')
print(json.dumps(result, indent=2)[:2000])
