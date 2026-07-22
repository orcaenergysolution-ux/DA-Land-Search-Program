"""Try to find VIC planning portal sitemap to get all permit URLs/GUIDs."""
import urllib.request, re, gzip, io

BASE = 'https://www.planning.vic.gov.au'
HDRS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'en-AU,en;q=0.9',
}

def fetch(url):
    req = urllib.request.Request(url, headers=HDRS)
    with urllib.request.urlopen(req, timeout=20) as resp:
        raw = resp.read()
        enc = resp.headers.get('Content-Encoding', '')
    if enc == 'gzip' or raw[:2] == b'\x1f\x8b':
        raw = gzip.decompress(raw)
    return raw.decode('utf-8', errors='replace')

sitemap_urls = [
    f'{BASE}/sitemap.xml',
    f'{BASE}/sitemap_index.xml',
    f'{BASE}/sitemap-0.xml',
    f'{BASE}/robots.txt',
    # Squiz CMS typical paths
    f'{BASE}/__sitemap/sitemap.xml',
    f'{BASE}/planning-approvals/ministerial-permits-register/ministerial-permits/sitemap.xml',
]

for url in sitemap_urls:
    try:
        text = fetch(url)
        print(f'OK  {len(text)} bytes  {url}')
        # For robots.txt, look for Sitemap: lines
        if 'robots.txt' in url:
            for line in text.splitlines():
                if 'sitemap' in line.lower():
                    print(f'  {line}')
        else:
            # Look for ministerial permit URLs in sitemap
            permit_urls = re.findall(r'<loc>(https?://[^<]*ministerial-permits/[^<]+)</loc>', text, re.I)
            print(f'  Permit URLs found: {len(permit_urls)}')
            for u in permit_urls[:5]:
                print(f'    {u}')
            # Also show total URL count
            all_locs = re.findall(r'<loc>([^<]+)</loc>', text)
            print(f'  Total <loc> entries: {len(all_locs)}')
            # Show sitemap index entries
            sub_sitemaps = re.findall(r'<sitemap>.*?<loc>([^<]+)</loc>', text, re.DOTALL)
            if sub_sitemaps:
                print(f'  Sub-sitemaps ({len(sub_sitemaps)}):')
                for s in sub_sitemaps[:10]:
                    print(f'    {s}')
    except urllib.error.HTTPError as e:
        print(f'HTTP {e.code}  {url}')
    except Exception as e:
        print(f'ERR  {type(e).__name__}: {e}  {url[:80]}')
