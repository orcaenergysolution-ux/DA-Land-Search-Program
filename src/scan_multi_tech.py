"""Scan NEM Gen Info for sites where multiple different technologies are grouped
under the same site name. These are candidates for the same summation bug as
Mortlake Energy Hub / New England Solar Farm / Eraring Big Battery."""
import sys
from collections import defaultdict
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent))
from build_map import to_float, norm_name, REGION_TO_STATE, NEM_FILE, normalise_tech
import openpyxl

wb = openpyxl.load_workbook(NEM_FILE, data_only=True, read_only=True)
ws = wb["Generator Information"]

sites = defaultdict(list)

for i, row in enumerate(ws.iter_rows(values_only=True)):
    if i < 4:
        continue
    region = row[5]
    if not region or region not in REGION_TO_STATE:
        continue
    site = str(row[1] or "").strip()
    if not site:
        continue
    status = (row[20] or "").strip().rstrip("*").strip()
    if status.lower().startswith("committed"):
        status = "Committed"
    tech = normalise_tech((row[9] or "").strip())
    cap = to_float(row[18]) or to_float(row[16]) or to_float(row[17])
    duid = str(row[12] or "")
    sites[norm_name(site)].append({
        "site_name": site, "tech": tech, "status": status,
        "cap": cap or 0, "duid": duid,
    })

print("Sites with multiple different technologies in NEM:")
print("-" * 90)
found = 0
for key, units in sorted(sites.items()):
    techs = set(u["tech"] for u in units)
    if len(techs) < 2:
        continue
    total = sum(u["cap"] for u in units)
    name = units[0]["site_name"]
    print(f"{name}  |  total={total:.1f} MW  |  techs={sorted(techs)}")
    for u in sorted(units, key=lambda x: x["tech"]):
        print(f"    {u['tech']:25s} {u['status']:22s} {u['cap']:8.2f} MW  duid={u['duid']}")
    found += 1

print(f"\nTotal: {found} sites with mixed technologies")
