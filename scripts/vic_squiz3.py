"""Properly extract search results from Squiz."""
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

PERMIT_PATTERN = re.compile(
    r'https?://www\.planning\.vic\.gov\.au/planning-approvals/ministerial-permits-register/ministerial-permits/([0-9a-f-]{36})',
    re.I
)

def squiz_search(query: str, num: int = 20) -> list[dict]:
    params = urllib.parse.urlencode({
        'collection': 'delwp-search-global-web',
        'query': query,
        'num_ranks': str(num),
    })
    url = f'{SQ_SEARCH}?{params}'
    req = urllib.request.Request(url, headers=HDRS)
    with urllib.request.urlopen(req, timeout=20) as resp:
        raw = resp.read()
        enc = resp.headers.get('Content-Encoding', '')
    if enc == 'gzip' or raw[:2] == b'\x1f\x8b':
        raw = gzip.decompress(raw)
    data = json.loads(raw.decode('utf-8'))

    # Navigate to result list
    packet = data.get('response', {}).get('resultPacket', {})
    results = packet.get('results', [])
    total = packet.get('totalMatching', 0)
    return results, total


# Test with known projects
test_queries = [
    'Baddaginnie Solar Farm ministerial permit',
    'Laceby Solar Farm ministerial permit',
    'Macorna Solar Farm ministerial permit',
]

for q in test_queries:
    results, total = squiz_search(q)
    print(f'\nQuery: "{q}"  -> {total} total matches, {len(results)} returned')
    for r in results[:5]:
        url = r.get('liveUrl', r.get('indexUrl', ''))
        title = r.get('title', '')
        m = PERMIT_PATTERN.search(url)
        guid = m.group(1) if m else 'NO_GUID'
        print(f'  [{guid}]  {title[:60]}  |  {url[:80]}')
    time.sleep(1)
