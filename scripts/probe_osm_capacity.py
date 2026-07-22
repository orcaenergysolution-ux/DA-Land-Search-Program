"""Check OSM Overpass for Australian renewable energy capacity data."""
import sys, json, re
sys.path.insert(0, 'src')
from fetch_cer_da import fetch_url

# Overpass query: Australian power plants with capacity tags
# (nw = nodes + ways; rel = relations excluded for speed)
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

import urllib.parse, urllib.request
url = 'https://overpass-api.de/api/interpreter'
data_enc = urllib.parse.urlencode({'data': OVERPASS_QUERY}).encode('utf-8')
req = urllib.request.Request(url, data=data_enc,
      headers={'User-Agent': 'AEMO-map-research/1.0 (research project)'})

print('Querying Overpass API...')
try:
    with urllib.request.urlopen(req, timeout=90) as r:
        result = json.loads(r.read())
    elements = result.get('elements', [])
    print(f'Got {len(elements)} elements')
    aus_plants = {}
    for el in elements:
        tags = el.get('tags', {})
        name = tags.get('name', '')
        if not name:
            continue
        # get capacity from various OSM tags
        cap_raw = (tags.get('plant:output:electricity') or
                   tags.get('generator:output:electricity') or
                   tags.get('capacity') or '')
        # parse MW from strings like "200 MW", "200MW", "200"
        m = re.search(r'([\d.]+)\s*(?:MW)?', cap_raw)
        cap = float(m.group(1)) if m else None
        country_tag = tags.get('addr:country', '')
        # centre point
        if 'center' in el:
            lat = el['center'].get('lat')
            lon = el['center'].get('lon')
        else:
            lat = el.get('lat'); lon = el.get('lon')
        aus_plants[name.lower()] = {'name': name, 'capacity_mw': cap, 'lat': lat, 'lon': lon, 'tags': tags}

    print(f'Named plants: {len(aus_plants)}')
    # filter to ones with capacity
    with_cap = {k: v for k, v in aus_plants.items() if v['capacity_mw']}
    print(f'With capacity: {len(with_cap)}')
    print('\nSample (first 10 with capacity):')
    for k, v in list(with_cap.items())[:10]:
        print(f'  {v["name"][:50]:50s}  {v["capacity_mw"]} MW')
except Exception as e:
    print(f'ERROR: {type(e).__name__}: {e}')
