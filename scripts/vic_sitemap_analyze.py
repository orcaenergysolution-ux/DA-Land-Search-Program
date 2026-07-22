"""Find where energy-project GUIDs sit in the sitemap ordering."""
import json, re

guids = json.loads(open('data/inputs/vic_permit_cache/_sitemap_guids.json').read())
print(f'Total GUIDs: {len(guids)}')

# Find Baddaginnie
baddag = '48f07100-e1b8-ee11-9078-002248922d75'
if baddag in guids:
    idx = guids.index(baddag)
    print(f'Baddaginnie at index: {idx} (of {len(guids)})')

# What GUID patterns appear at different positions?
print('\nGUID patterns by position (every 200):')
for i in range(0, len(guids), 200):
    g = guids[i]
    # Extract version nibbles (position 2 of UUID = version indicator)
    parts = g.split('-')
    print(f'  [{i:4d}] {g[:20]}...  pattern={parts[2] if len(parts)>2 else "?"}')

# Count 'ee11', 'ef11', 'ed11' (newer energy-era GUIDs)
newer = [g for g in guids if re.search(r'[e-f][d-f]11', g[14:18], re.I)]
print(f'\nNewer GUIDs (ed/ee/ef11 pattern): {len(newer)}')
if newer:
    first_idx = guids.index(newer[0])
    last_idx  = guids.index(newer[-1])
    print(f'  First at index {first_idx}, last at {last_idx}')
    print(f'  First 3: {newer[:3]}')
    print(f'  Last 3:  {newer[-3:]}')
