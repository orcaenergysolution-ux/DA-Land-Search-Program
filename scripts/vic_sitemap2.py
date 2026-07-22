"""Try sitemap with full browser headers."""
import urllib.request, re, gzip

BASE = 'https://www.planning.vic.gov.au'
FULL_HDRS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-AU,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Referer': f'{BASE}/',
    'sec-ch-ua': '"Chromium";v="124"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}

def fetch(url):
    req = urllib.request.Request(url, headers=FULL_HDRS)
    with urllib.request.urlopen(req, timeout=20) as resp:
        raw = resp.read()
        enc = resp.headers.get('Content-Encoding', '')
        ct = resp.headers.get('Content-Type', '')
        print(f'  Content-Type: {ct}  Encoding: {enc}  Size: {len(raw)}')
    if enc == 'gzip' or (raw[:2] == b'\x1f\x8b'):
        raw = gzip.decompress(raw)
    return raw.decode('utf-8', errors='replace')

for url in [
    f'{BASE}/sitemap.xml',
    f'{BASE}/robots.txt',
]:
    try:
        print(f'\nFetching: {url}')
        text = fetch(url)
        print(f'  Text size: {len(text)}')
        # Find permit URLs
        permit_urls = re.findall(r'https?://[^\s<>"\']+ministerial-permits/[^\s<>"\']+', text, re.I)
        print(f'  Permit URLs: {len(permit_urls)}')
        for u in permit_urls[:5]:
            print(f'    {u}')
        # Sub-sitemaps
        sub = re.findall(r'<loc>([^<]+)</loc>', text)
        print(f'  Total locs: {len(sub)}')
        for s in sub[:10]:
            if 'sitemap' in s.lower() or 'permit' in s.lower():
                print(f'    {s}')
    except urllib.error.HTTPError as e:
        print(f'  HTTP {e.code}: {e.reason}')
    except Exception as e:
        print(f'  ERR: {e}')
