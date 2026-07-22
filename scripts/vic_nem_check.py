"""Check if VIC_DA missing-cap projects appear in NEM under different names."""
import json, re, openpyxl

wb = openpyxl.load_workbook('data/inputs/NEM Generation Information Apr 2026.xlsx',
                             data_only=True, read_only=True)
ws = wb['Generator Information']
vic_nem = {}
for i, row in enumerate(ws.iter_rows(values_only=True)):
    if i < 4: continue
    if row[5] != 'VIC1': continue
    name = re.sub(r'[^a-z0-9 ]+', ' ', str(row[1] or '').lower()).strip()
    cap  = row[18] or row[16] or row[17]
    vic_nem[name] = cap
wb.close()

data = json.load(open('data/intermediate/projects.json', encoding='utf-8'))
missing = [p for p in data if 'VIC_DA' in (p.get('source') or '') and not p.get('capacity_mw')]

print(f'VIC NEM entries: {len(vic_nem)}')
print(f'VIC_DA missing cap: {len(missing)}')
print()

for p in missing:
    raw  = re.sub(r'[^a-z0-9 ]+', ' ', p['site_name'].lower()).strip()
    words = set(raw.split())
    candidates = [(n, c) for n, c in vic_nem.items() if len(set(n.split()) & words) >= 2]
    if candidates:
        best = max(candidates, key=lambda x: len(set(x[0].split()) & words))
        print(f'  CANDIDATE  {p["site_name"][:50]:50s} -> {best[0]} (cap={best[1]})')
    else:
        print(f'  no match   {p["site_name"][:50]:50s}')
