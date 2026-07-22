"""Regenerate outputs/null_locations.csv and outputs/projects_all.csv from projects.json."""
import json, csv, pathlib

ROOT = pathlib.Path('C:/projects/AEMO_map')
projects = json.loads((ROOT / 'data/intermediate/projects.json').read_text(encoding='utf-8'))
print(f'Loaded {len(projects)} projects')

FIELDS = [
    'site_name','region','state','owner','technology','fuel',
    'capacity_mw','storage_mwh','unit_status','asset_type',
    'location_desc','stage','source','on_aemo_map','duid',
    'lat','lon','geocode_source','geocode_display','geocode_query',
    'sara_decision_date','hre_licence','hre_application_date',
]

# projects_all.csv
out_all = ROOT / 'outputs/projects_all.csv'
with open(out_all, 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction='ignore')
    w.writeheader()
    w.writerows(projects)
print(f'Wrote {out_all}  ({len(projects)} rows)')

# null_locations.csv
null_fields = ['site_name','state','capacity_mw','stage','technology','location_desc','source']
null_rows = [p for p in projects if not p.get('lat')]
with open(ROOT / 'outputs/null_locations.csv', 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=null_fields, extrasaction='ignore')
    w.writeheader()
    w.writerows(null_rows)
print(f'Wrote null_locations.csv  ({len(null_rows)} rows without coordinates)')

# Check Baddaginnie specifically
baddag = [p for p in projects if 'baddaginnie' in p.get('site_name','').lower()]
for p in baddag:
    print(f"\nBaddaginnie: MW={p.get('capacity_mw')} MWh={p.get('storage_mwh')} "
          f"loc='{p.get('location_desc')}' lat={p.get('lat')} src={p.get('source')}")
