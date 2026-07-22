"""Probe VIC planning ministerial permits register for an accessible API."""
import sys, json, time
sys.path.insert(0, 'src')
from fetch_cer_da import fetch_url

BASE = 'https://www.planning.vic.gov.au'

endpoints = [
    # Power Pages / Dataverse OData endpoints
    f'{BASE}/_api/lists',
    f'{BASE}/_api/web/lists',
    f'{BASE}/api/data/v9.2/cr0e3_ministerialpermitrequests',
    f'{BASE}/_odata/ministerial-permits',
    # Search / list endpoints
    f'{BASE}/planning-approvals/ministerial-permits-register?format=json',
    f'{BASE}/planning-approvals/ministerial-permits-register/ministerial-permits?$format=json&$top=5',
    f'{BASE}/api/ministerial-permits?pageSize=5',
    # Common CMS REST endpoints
    f'{BASE}/api/content/ministerial-permits',
    f'{BASE}/_api/v2.0/search/query?querytext=baddaginnie&format=json',
    f'{BASE}/siteassets/api/ministerial-permits.json',
]

for url in endpoints:
    try:
        time.sleep(1)
        raw = fetch_url(url)
        print(f'OK   {url}')
        snippet = raw[:300].decode('utf-8', errors='replace').replace('\n', ' ')
        print(f'     {snippet[:200]}')
    except Exception as e:
        code = getattr(e, 'code', '?')
        print(f'{code}  {url}')
