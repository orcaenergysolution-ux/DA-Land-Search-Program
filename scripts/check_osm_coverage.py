"""Check OSM Overpass coverage for all missing-capacity DA projects."""
import sys, json, re, urllib.parse, urllib.request
sys.path.insert(0, 'src')
from fetch_cer_da import fetch_url

def norm(s):
    s = re.sub(r'[^a-z0-9]+', ' ', (s or '').lower()).strip()
    return ' '.join(s.split())

OVERPASS_QUERY = """
[out:json][timeout:60];
area["ISO3166-1"="AU"]->.au;
(
  nw["power"="plant"]["plant:output:electricity"](area.au);
  nw["power"="plant"]["generator:output:electricity"](area.au);
  nw["power"="plant"]["capacity"](area.au);
);
out tags center qt 1000;
""".strip()

url = 'https://overpass-api.de/api/interpreter'
data_enc = urllib.parse.urlencode({'data': OVERPASS_QUERY}).encode('utf-8')
req = urllib.request.Request(url, data=data_enc, headers={'User-Agent':'AEMO-map/1.0'})

print('Fetching OSM data...')
with urllib.request.urlopen(req, timeout=90) as r:
    result = json.loads(r.read())

osm = {}
for el in result.get('elements', []):
    tags = el.get('tags', {})
    name = tags.get('name', '').strip()
    if not name: continue
    cap_raw = (tags.get('plant:output:electricity') or
               tags.get('generator:output:electricity') or
               tags.get('capacity') or '')
    m = re.search(r'([\d.]+)\s*(?:MW)?', cap_raw)
    cap = float(m.group(1)) if m else None
    if 'center' in el:
        lat, lon = el['center'].get('lat'), el['center'].get('lon')
    else:
        lat, lon = el.get('lat'), el.get('lon')
    osm[norm(name)] = {'name': name, 'capacity_mw': cap, 'lat': lat, 'lon': lon}

print(f'OSM plants: {len(osm)}  with capacity: {sum(1 for v in osm.values() if v["capacity_mw"])}')
print()

data = json.load(open('data/intermediate/projects.json', encoding='utf-8'))
totals = {'found_exact':0, 'found_fuzzy':0, 'not_found':0}

for src_tag in ['VIC_DA', 'NSW_DA', 'QLD_DA', 'TAS_DA']:
    missing = [p for p in data if src_tag in (p.get('source') or '') and not p.get('capacity_mw')]
    if not missing:
        continue
    found_e, found_f, not_f = 0, 0, 0
    for p in missing:
        key = norm(p['site_name'])
        words = set(key.split()) - {'farm','project','solar','wind','bess','battery','energy','power','station'}
        if key in osm and osm[key]['capacity_mw']:
            found_e += 1
            totals['found_exact'] += 1
        else:
            # word overlap (meaningful words only)
            threshold = 1 if len(words) <= 1 else 2
            candidates = [(n, v) for n, v in osm.items()
                          if v['capacity_mw'] and
                          len(set(n.split()) & words) >= threshold and
                          len(set(n.split()) & words) >= len(words) * 0.5]
            if candidates:
                found_f += 1
                totals['found_fuzzy'] += 1
            else:
                not_f += 1
                totals['not_found'] += 1
    print(f'{src_tag}: {len(missing)} missing  -> exact={found_e}  fuzzy={found_f}  still_missing={not_f}')

print(f'\nOverall: exact={totals["found_exact"]}  fuzzy={totals["found_fuzzy"]}  still_missing={totals["not_found"]}')
