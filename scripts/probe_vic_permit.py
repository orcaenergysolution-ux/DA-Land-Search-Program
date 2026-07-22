import sys
sys.path.insert(0, 'src')
from fetch_cer_da import fetch_url
import re

url = 'https://www.planning.vic.gov.au/planning-approvals/ministerial-permits-register/ministerial-permits/48f07100-e1b8-ee11-9078-002248922d75'
try:
    raw = fetch_url(url).decode('utf-8', errors='replace')
    print(f'OK  {len(raw)} bytes')
    # Look for MW, MWh, capacity mentions
    for line in raw.splitlines():
        l = line.strip()
        if any(k in l for k in ['MW', 'MWh', 'capacity', 'Capacity', 'megawatt', 'Megawatt',
                                  'Baddaginnie', 'solar', 'Solar', 'location', 'Location']):
            clean = re.sub(r'<[^>]+>', '', l).strip()
            if clean:
                print(' ', clean[:120])
except Exception as e:
    print(f'ERR {type(e).__name__}: {e}')
