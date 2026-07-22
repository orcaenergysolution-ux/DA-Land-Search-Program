import sys
sys.path.insert(0, 'src')
from fetch_cer_da import fetch_url

urls = [
    ('VIC planning v2',   'https://www.planning.vic.gov.au/permits-and-applications/renewable-energy-facilities'),
    ('VIC DEECA energy',  'https://www.deeca.vic.gov.au/energy/renewable-energy'),
    ('VIC planning search','https://www.planning.vic.gov.au/search?q=renewable+energy+MW'),
    ('SA planning portal','https://www.saplanningportal.sa.gov.au/'),
    ('SA plan.sa.gov.au', 'https://plan.sa.gov.au/'),
    ('NSW planning RE',   'https://www.planning.nsw.gov.au/policy-and-legislation/renewable-energy'),
    ('QLD DSDM',         'https://www.business.qld.gov.au/industries/mining-energy-water/energy/electricity/generation/renewable-energy'),
]
for label, url in urls:
    try:
        raw = fetch_url(url)
        has_mw = b'MW' in raw or b'megawatt' in raw.lower()
        print(f'OK   [{label}]  {len(raw):>8} bytes  has_MW={has_mw}')
    except Exception as e:
        print(f'ERR  [{label}]  {type(e).__name__}: {str(e)[:70]}')
