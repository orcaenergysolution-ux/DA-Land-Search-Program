import json

for state in ['NSW', 'QLD', 'SA', 'VIC', 'TAS']:
    with open('data/intermediate/tier_c_' + state.lower() + '.json') as f:
        projects = json.load(f)
    print('=== ' + state + ' (' + str(len(projects)) + ' projects) ===')
    for p in projects:
        loc = (p['location_desc'] or '(no location)')[:80]
        name = p['site_name']
        stage = p['stage']
        cap = str(p['capacity_mw'])
        print('  - ' + name + ' [' + stage + '] ' + cap + ' MW | ' + loc)
    print()
