"""Add Baddaginnie to the permit index from its cached HTML."""
import sys
sys.path.insert(0, 'C:/projects/AEMO_map/src')
from fetch_vic_permits import (
    _parse_permit_html, _match_permit, _pdf_mw, _load_index, _save_index, _norm
)

guid = '48f07100-e1b8-ee11-9078-002248922d75'
cache_f = f'C:/projects/AEMO_map/data/inputs/vic_permit_cache/{guid}.html'

html = open(cache_f, encoding='utf-8', errors='replace').read()
info = _parse_permit_html(guid, html)
print('Parsed:', info['app_no'], info['address'])
print('PDF links:', len(info['pdf_links']))

# Match
target = _norm('Baddaginnie Solar Farm')
matched = _match_permit(html, info['pdf_links'], info['address'], target)
print(f'Match Baddaginnie: {matched}')

if matched:
    mw, mwh = info['mw'], info['mwh']
    if (mw is None) and info['pdf_links']:
        print('Getting MW from PDF...')
        mw, mwh = _pdf_mw(info['pdf_links'][0], guid)
    info['mw'] = mw
    info['mwh'] = mwh
    info['matched_names'] = [target]
    print(f'MW={mw}, MWh={mwh}')

    idx = _load_index()
    idx[guid] = info
    _save_index(idx)
    print('Saved to index.')
