"""Probe Global Energy Monitor trackers for Australian capacity data."""
import sys, json, re, io
sys.path.insert(0, 'src')
from fetch_cer_da import fetch_url

# GEM tracker index page to find current download URLs
gem_urls = [
    ('GEM Solar tracker',
     'https://globalenergymonitor.org/wp-content/uploads/2025/01/Global-Solar-Power-Tracker-Jan-2025.xlsx'),
    ('GEM Wind tracker',
     'https://globalenergymonitor.org/wp-content/uploads/2025/01/Global-Wind-Power-Tracker-Jan-2025.xlsx'),
    ('GEM BESS tracker',
     'https://globalenergymonitor.org/wp-content/uploads/2025/01/Global-Battery-Storage-Power-Tracker-Jan-2025.xlsx'),
    ('GEM Solar 2024',
     'https://globalenergymonitor.org/wp-content/uploads/2024/09/Global-Solar-Power-Tracker-September-2024.xlsx'),
    ('GEM Wind 2024',
     'https://globalenergymonitor.org/wp-content/uploads/2024/09/Global-Wind-Power-Tracker-September-2024.xlsx'),
]

for label, url in gem_urls:
    try:
        raw = fetch_url(url)
        print(f'OK   [{label}]  {len(raw):>9} bytes')
    except Exception as e:
        print(f'ERR  [{label}]  {type(e).__name__}: {str(e)[:80]}')
