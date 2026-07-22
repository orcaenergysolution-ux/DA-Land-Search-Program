"""Read the Change Log tab from the NEM Generation Information file.
Extract all name changes / aliases that could cause duplicates."""
import openpyxl, pathlib, json, re

NEM = pathlib.Path('C:/projects/AEMO_map/data/inputs/NEM Generation Information Apr 2026.xlsx')
wb = openpyxl.load_workbook(NEM, data_only=True, read_only=True)

ws = wb['Change Log']
rows = list(ws.iter_rows(values_only=True))

print(f'Change Log: {len(rows)} rows')
print()

# Print first 5 rows to understand structure
print('=== First 10 rows (header + data) ===')
for r in rows[:10]:
    print(r)

print()
print('=== All non-empty rows ===')
for i, r in enumerate(rows):
    if any(v for v in r if v is not None):
        print(f'  [{i:3d}] {r}')
