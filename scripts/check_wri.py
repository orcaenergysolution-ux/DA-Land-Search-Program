"""Check WRI Global Power Plant Database coverage for missing-capacity projects."""
import sys, json, csv, re, io
sys.path.insert(0, 'src')
from fetch_cer_da import fetch_url

def norm(s):
    s = re.sub(r'[^a-z0-9]+', ' ', (s or '').lower()).strip()
    return ' '.join(s.split())

print('Fetching WRI database...')
raw = fetch_url('https://raw.githubusercontent.com/wri/global-power-plant-database/master/output_database/global_power_plant_database.csv')
text = raw.decode('utf-8', errors='replace')
reader = csv.DictReader(io.StringIO(text))

# Filter to Australia
aus_plants = {}
for row in reader:
    if row['country'] != 'AUS':
        continue
    name_norm = norm(row['name'])
    try:
        cap = float(row['capacity_mw']) if row['capacity_mw'] else None
    except ValueError:
        cap = None
    aus_plants[name_norm] = {
        'name': row['name'],
        'capacity_mw': cap,
        'fuel': row['primary_fuel'],
        'lat': row.get('latitude'),
        'lon': row.get('longitude'),
    }

print(f'WRI Australian plants: {len(aus_plants)}')
print()

# Load missing-capacity projects
data = json.load(open('data/intermediate/projects.json', encoding='utf-8'))

results = {'found': [], 'not_found': []}
for src_tag in ['VIC_DA', 'NSW_DA', 'QLD_DA']:
    missing = [p for p in data if src_tag in (p.get('source') or '') and not p.get('capacity_mw')]
    for p in missing:
        key = norm(p['site_name'])
        words = set(key.split())
        # Exact norm match first
        if key in aus_plants:
            results['found'].append((p['site_name'], aus_plants[key]['capacity_mw'], 'exact', src_tag))
            continue
        # Word-overlap (>=3 words in common, or >=2 if short name)
        threshold = 2 if len(words) <= 3 else 3
        candidates = [(n, v) for n, v in aus_plants.items()
                      if len(set(n.split()) & words) >= threshold]
        if candidates:
            best = max(candidates, key=lambda x: len(set(x[0].split()) & words))
            results['found'].append((p['site_name'], best[1]['capacity_mw'], f'fuzzy->{best[1]["name"]}', src_tag))
        else:
            results['not_found'].append((p['site_name'], src_tag))

print(f'Found in WRI: {len(results["found"])}')
for name, cap, method, src in results['found'][:20]:
    print(f'  {name[:50]:50s}  {str(cap):8s}  [{method[:40]}]  {src}')

print(f'\nNot found in WRI: {len(results["not_found"])}')
for name, src in results['not_found'][:20]:
    print(f'  {name[:50]:50s}  {src}')
