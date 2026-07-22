"""Probe global/national renewable energy databases for Australian capacity data."""
import sys, json
sys.path.insert(0, 'src')
from fetch_cer_da import fetch_url

sources = [
    ('WRI GPPD (GitHub)',
     'https://raw.githubusercontent.com/wri/global-power-plant-database/master/output_database/global_power_plant_database.csv'),
    ('ARENA projects API',
     'https://arena.gov.au/api/projects/?format=json&page_size=100'),
    ('OpenElectricity facilities',
     'https://api.openelectricity.org.au/v4/facilities/?network=NEM&limit=500'),
    ('OpenNEM facilities',
     'https://api.opennem.org.au/facilities/?network_region=VIC1&limit=500'),
]

for label, url in sources:
    try:
        raw = fetch_url(url)
        print(f'OK   [{label}]  {len(raw):>9} bytes')
        # peek first 300 chars
        snippet = raw[:300].decode('utf-8', errors='replace').replace('\n', ' ')
        print(f'     {snippet[:200]}')
    except Exception as e:
        print(f'ERR  [{label}]  {type(e).__name__}: {str(e)[:80]}')
    print()
