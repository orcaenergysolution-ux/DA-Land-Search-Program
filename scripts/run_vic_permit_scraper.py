"""
Standalone runner for the VIC ministerial permit scraper.
Fetches permit pages newest-first, matching against VIC DA projects.
Run this once (or periodically) to build the cache.
Usage:
    python scripts/run_vic_permit_scraper.py [--max N]
"""
import sys, json
sys.path.insert(0, 'C:/projects/AEMO_map/src')

from fetch_vic_permits import (
    _get_all_guids, _priority_guids, _parse_permit_html, _match_permit,
    _pdf_mw, _load_index, _save_index, _norm,
    CACHE_DIR, INDEX_FILE, PERMIT_PREFIX, DELAY_S, _fetch_raw,
)
import urllib.error, time, pathlib, re

PROJECTS_JSON = pathlib.Path('C:/projects/AEMO_map/data/intermediate/projects.json')
MAX_PAGES = int(sys.argv[sys.argv.index('--max') + 1]) if '--max' in sys.argv else 300

# Load VIC DA projects
projects = json.loads(PROJECTS_JSON.read_text(encoding='utf-8'))
vic_da = [p for p in projects if p.get('state') == 'VIC' and 'VIC' in p.get('source', '')]
vic_norm_map = {_norm(p['site_name']): p['site_name'] for p in vic_da}
print(f'VIC DA projects: {len(vic_norm_map)}')

# Load existing index
index = _load_index()
matched_so_far = set()
for rec in index.values():
    matched_so_far.update(rec.get('matched_names', []))

remaining = set(vic_norm_map.keys()) - matched_so_far
print(f'Already matched: {len(matched_so_far)}, Remaining: {len(remaining)}')

if not remaining:
    print('All VIC DA projects already matched!')
    sys.exit(0)

# Get GUIDs in priority order (newest first)
all_guids = _get_all_guids()
guids = _priority_guids(all_guids)
done_guids = set(index.keys())
fetched = 0

print(f'\nScanning up to {MAX_PAGES} new permit pages...\n')

for guid in guids:
    if not remaining:
        print('All targets matched!')
        break
    if fetched >= MAX_PAGES:
        print(f'Reached {MAX_PAGES} page limit.')
        break
    if guid in done_guids:
        continue

    cache_f = CACHE_DIR / f'{guid}.html'

    if cache_f.exists():
        html = cache_f.read_text(encoding='utf-8', errors='replace')
        from_cache = True
    else:
        try:
            time.sleep(DELAY_S)
            raw = _fetch_raw(f'{PERMIT_PREFIX}{guid}')
            html = raw.decode('utf-8', errors='replace')
            cache_f.write_text(html, encoding='utf-8')
            fetched += 1
            from_cache = False
            sys.stdout.write(f'\r  Fetched {fetched} new pages, {len(remaining)} targets remaining...  ')
            sys.stdout.flush()
        except urllib.error.HTTPError as e:
            index[guid] = {'guid': guid, 'error': e.code}
            done_guids.add(guid)
            if fetched % 20 == 0:
                _save_index(index)
            continue
        except Exception as e:
            index[guid] = {'guid': guid, 'error': str(e)}
            done_guids.add(guid)
            continue

    info = _parse_permit_html(guid, html)

    matched = []
    for target in list(remaining):
        if _match_permit(html, info['pdf_links'], info['address'], target):
            matched.append(target)
            remaining.discard(target)

    if matched:
        mw, mwh = info['mw'], info['mwh']
        if (mw is None or mwh is None) and info['pdf_links']:
            pdf_mw, pdf_mwh = _pdf_mw(info['pdf_links'][0], guid)
            mw  = mw  if mw  is not None else pdf_mw
            mwh = mwh if mwh is not None else pdf_mwh
        info['mw']  = mw
        info['mwh'] = mwh
        info['matched_names'] = matched
        orig_names = [vic_norm_map[n] for n in matched]
        print(f'\n  MATCH: {orig_names}')
        print(f'         MW={mw}  MWh={mwh}  addr={info["address"][:60]}')
    else:
        info['matched_names'] = []

    index[guid] = info
    done_guids.add(guid)

    # Save every 50 pages
    if (fetched % 50 == 0 and fetched > 0) or matched:
        _save_index(index)

_save_index(index)
print(f'\n\nDone. Index has {len(index)} records.')
matched_total = sum(1 for r in index.values() if r.get('matched_names'))
print(f'Matched permits: {matched_total}')
print(f'Unmatched VIC DA projects ({len(remaining)}):')
for n in sorted(remaining):
    print(f'  {vic_norm_map[n]}')
