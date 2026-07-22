"""Audit capacity coverage across all DA sources."""
import json
from collections import Counter

data = json.load(open('data/intermediate/projects.json', encoding='utf-8'))
print(f'Total projects: {len(data)}\n')

da_src_tags = ['NSW_DA', 'VIC_DA', 'QLD_DA', 'TAS_DA', 'CER']
for src in da_src_tags:
    projects = [p for p in data if src in (p.get('source') or '')]
    has_mw  = [p for p in projects if p.get('capacity_mw')]
    no_mw   = [p for p in projects if not p.get('capacity_mw')]
    has_mwh = [p for p in projects if p.get('storage_mwh')]
    print(f'{src:10s}  n={len(projects):3d}  MW present={len(has_mw):3d}  MW missing={len(no_mw):3d}  MWh present={len(has_mwh):3d}')
    if no_mw:
        for p in no_mw[:5]:
            print(f'           missing MW: {p["site_name"][:55]}  {p["stage"]}')
        if len(no_mw) > 5:
            print(f'           ... and {len(no_mw)-5} more')
    print()
