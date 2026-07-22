"""Test the VIC permit matching logic on the cached Baddaginnie page."""
import sys
sys.path.insert(0, 'C:/projects/AEMO_map/src')
from fetch_vic_permits import _parse_permit_html, _match_permit, _norm, _pdf_mw

guid = '48f07100-e1b8-ee11-9078-002248922d75'

html = open('C:/projects/AEMO_map/scripts/baddaginnie_raw.html', encoding='utf-8', errors='replace').read()

info = _parse_permit_html(guid, html)
print('Parsed info:')
print(f'  app_no:    {info["app_no"]}')
print(f'  address:   {info["address"]}')
print(f'  mw:        {info["mw"]}')
print(f'  mwh:       {info["mwh"]}')
print(f'  pdf_links: {len(info["pdf_links"])}')
for l in info['pdf_links']:
    print(f'    {l[:100]}')

print()
target = _norm('Baddaginnie Solar Farm')
print(f'Target norm: "{target}"')
match = _match_permit(html, info['pdf_links'], info['address'], target)
print(f'Match result: {match}')

print()
print(f'MW from HTML: {info["mw"]} MW, {info["mwh"]} MWh')
if info['mw'] is None and info['pdf_links']:
    print(f'Trying PDF: {info["pdf_links"][0][:80]}...')
    mw, mwh = _pdf_mw(info['pdf_links'][0], guid)
    print(f'MW from PDF: {mw} MW, {mwh} MWh')
