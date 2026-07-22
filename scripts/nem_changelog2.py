"""Extract 'Site name update' entries from the NEM Change Log — these are the
rename/alias records that create duplicates between NEM and state DA sources."""
import openpyxl, pathlib, json, re

NEM = pathlib.Path('C:/projects/AEMO_map/data/inputs/NEM Generation Information Apr 2026.xlsx')
wb  = openpyxl.load_workbook(NEM, data_only=True, read_only=True)
ws  = wb['Change Log']
rows = list(ws.iter_rows(values_only=True))

# Find header row
header = None
for i, r in enumerate(rows):
    if r[0] == 'Publication Date':
        header = r
        data_start = i + 1
        break

print(f'Header: {header}')
print(f'Data starts at row {data_start}')

# Find col indices
col = {v: i for i, v in enumerate(header) if v}
print(f'Columns: {col}')
print()

# Extract all 'Site name update' rows
renames = []
for r in rows[data_start:]:
    if r[col['Type of Change']] == 'Site name update':
        renames.append({
            'date':      r[col['Publication Date']],
            'region':    r[col['Region']],
            'new_name':  r[col['Site Name']],    # current (new) name
            'note':      r[col['Note']] or '',
            'duid':      r[col['DUID(s)']] or '',
        })

print(f'Total "Site name update" entries: {len(renames)}')
print()

# The 'Note' field often contains _x000D_ (XML carriage return) and embedded newlines.
# Clean it first, then try multiple regex patterns.
def clean_note(note):
    """Strip _x000D_, normalise whitespace."""
    s = (note or '').replace('_x000D_', '').replace('\r', ' ').replace('\n', ' ')
    return re.sub(r'\s+', ' ', s).strip()

PATTERNS = [
    # "Sitename Updated From X To Y"  /  "Site Name Updated From X To Y"
    re.compile(r'[Ss]ite\s*[Nn]ame\s+[Uu]pdated?\s+[Ff]rom\s+(.+?)\s+[Tt]o\s+(.+?)$', re.I),
    # "Sitename changed from X To Y"
    re.compile(r'[Ss]ite\s*[Nn]ame\s+[Cc]hanged\s+[Ff]rom\s+(.+?)\s+[Tt]o\s+(.+?)$', re.I),
    # "Updated From X To Y"  /  "Changed From X To Y"
    re.compile(r'(?:Updated|Changed)\s+[Ff]rom\s+(.+?)\s+[Tt]o\s+(.+?)$', re.I),
    # "from 'X' to 'Y'"  (with quotes)
    re.compile(r"[Ff]rom\s+['\"]?(.+?)['\"]?\s+[Tt]o\s+['\"]?(.+?)['\"]?$", re.I),
]

for rec in renames:
    note_clean = clean_note(rec['note'])
    rec['note_clean'] = note_clean
    rec['old_name'] = ''
    rec['new_name_from_note'] = ''
    for pat in PATTERNS:
        m = pat.search(note_clean)
        if m:
            rec['old_name']           = m.group(1).strip().strip("'\"")
            rec['new_name_from_note'] = m.group(2).strip().strip("'\"")
            break

# Diagnostics: how many parsed vs not
parsed   = [r for r in renames if r['old_name']]
unparsed = [r for r in renames if not r['old_name']]
print(f'Parsed old name: {len(parsed)},  unparsed (see note): {len(unparsed)}')
if unparsed:
    print('  Sample unparsed notes (up to 10):')
    for rec in unparsed[:10]:
        print(f'    note_clean: {rec["note_clean"][:150]!r}')
print()

# Print all renames
print('=== Site name updates (newest first) ===')
for rec in sorted(renames, key=lambda x: x['date'] or '', reverse=True):
    dt  = rec['date'].strftime('%Y-%m') if rec['date'] else '?'
    old = rec['old_name'] or '(see note)'
    new = rec['new_name']
    note = rec['note_clean'][:120] if not rec['old_name'] else ''
    print(f"  {dt}  [{rec['region']}]  '{old}'  ->  '{new}'  {note}")

# Now cross-check with projects.json
print()
print('=== Cross-check: old names still present in projects.json ===')
projects = json.loads(pathlib.Path('C:/projects/AEMO_map/data/intermediate/projects.json').read_text(encoding='utf-8'))

def norm(s):
    return re.sub(r'[^a-z0-9]', '', s.lower())

proj_names_norm = {norm(p['site_name']): p for p in projects}

hits = []
for rec in renames:
    old = rec['old_name']
    new = rec['new_name']
    if not old:
        continue
    old_in_proj = norm(old) in proj_names_norm
    new_in_proj = norm(new) in proj_names_norm
    if old_in_proj and new_in_proj:
        p_old = proj_names_norm[norm(old)]
        p_new = proj_names_norm[norm(new)]
        hits.append((old, new, p_old, p_new, rec))

print(f'Both old AND new name present (true duplicates): {len(hits)}')
for old, new, p_old, p_new, rec in hits:
    dt = rec['date'].strftime('%Y-%m') if rec['date'] else '?'
    print(f"\n  {dt} [{rec['region']}]")
    print(f"  OLD: '{old}'  src={p_old['source']}  MW={p_old.get('capacity_mw')}  state={p_old['state']}")
    print(f"  NEW: '{new}'  src={p_new['source']}  MW={p_new.get('capacity_mw')}  state={p_new['state']}")

# Old name only in projects (new name may exist under different name or not yet in NEM)
print()
print('=== Old name in projects but new name NOT found ===')
old_only = []
for rec in renames:
    old = rec['old_name']
    new = rec['new_name']
    if not old:
        continue
    if norm(old) in proj_names_norm and norm(new) not in proj_names_norm:
        p = proj_names_norm[norm(old)]
        old_only.append((old, new, p, rec))

print(f'Count: {len(old_only)}')
for old, new, p, rec in old_only:
    dt = rec['date'].strftime('%Y-%m') if rec['date'] else '?'
    print(f"  {dt} [{rec['region']}]  OLD in proj: '{old}'  src={p['source']}  | new name '{new}' NOT found")

# Save rename table as JSON for use in the pipeline
rename_map = {}
for rec in renames:
    if rec['old_name']:
        rename_map[rec['old_name'].lower()] = rec['new_name']

pathlib.Path('C:/projects/AEMO_map/data/inputs/nem_name_renames.json').write_text(
    json.dumps(rename_map, indent=2, ensure_ascii=False), encoding='utf-8'
)
print(f'\nSaved rename map ({len(rename_map)} entries) to data/inputs/nem_name_renames.json')

# Also print suggested exclusions for manual_exclusions.json
if hits:
    print()
    print('=== Suggested additions to manual_exclusions.json (old names to exclude) ===')
    excl_path = pathlib.Path('C:/projects/AEMO_map/data/inputs/manual_exclusions.json')
    existing = json.loads(excl_path.read_text(encoding='utf-8')) if excl_path.exists() else []
    existing_names_norm = {norm(e['site_name']) for e in existing}
    new_suggestions = []
    for old, new, p_old, p_new, rec in hits:
        if norm(old) not in existing_names_norm:
            new_suggestions.append({
                "site_name": old,
                "reason": f"NEM rename: '{old}' -> '{new}' ({rec['date'].strftime('%Y-%m') if rec['date'] else '?'}). Keep NEM name."
            })
            print(f'  ADD: "{old}" (was {p_old["source"]}, now "{new}" from {p_new["source"]})')
    if not new_suggestions:
        print('  (all duplicates already in exclusions list)')
