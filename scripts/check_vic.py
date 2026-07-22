import json
data = json.loads(open('data/intermediate/projects.json', encoding='utf-8').read())
vic_da = [p for p in data if 'VIC_DA' in (p.get('source') or '')]
has_cap = [p for p in vic_da if p.get('capacity_mw')]
no_cap  = [p for p in vic_da if not p.get('capacity_mw')]
print(f'VIC_DA total: {len(vic_da)}  |  with capacity: {len(has_cap)}  |  missing: {len(no_cap)}')
print()
print('--- Missing capacity (VIC_DA only, no NEM match) ---')
for p in no_cap[:40]:
    name = p['site_name']
    stage = p['stage']
    tech = p['technology']
    print(f'  {name[:50]:50s}  {stage:15s}  {tech}')
