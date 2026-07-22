"""Dig into the JS in the register list page for API endpoints."""
import re, json

text = open('scripts/vic_list_raw.html', encoding='utf-8').read()

# Find all script src URLs
scripts = re.findall(r'<script[^>]+src=["\']([^"\']+)["\']', text, re.I)
print(f'External scripts ({len(scripts)}):')
for s in scripts[:20]:
    print(f'  {s}')

# Find inline scripts and look for API config
inline = re.findall(r'<script(?:[^>]*)>(.*?)</script>', text, re.DOTALL | re.I)
print(f'\nInline script blocks: {len(inline)}')
for i, block in enumerate(inline):
    block = block.strip()
    if not block:
        continue
    # Look for fetch, XMLHttpRequest, or relevant API patterns
    if any(kw in block for kw in ['fetch(', 'XMLHttpRequest', 'ajax', 'axios', 'entitySet',
                                    'ministerial', 'permit', '_api/', 'OData', 'WebAPI',
                                    'getList', 'loadData', 'pageSize', 'totalCount']):
        print(f'\n--- Block {i} ({len(block)} chars) ---')
        print(block[:1000])
    # Also check for config objects with URLs
    elif 'endpointOrigin' in block or 'baseUrl' in block or 'apiUrl' in block:
        print(f'\n--- Config Block {i} ---')
        print(block[:500])

# Look for any fetch patterns anywhere
print('\n=== fetch() patterns ===')
for m in re.finditer(r'fetch\s*\(\s*([^)]{5,200})\)', text, re.DOTALL):
    t = m.group(1).strip()
    print(f'  {t[:150]}')

# Look for entity list / web template configuration
print('\n=== entityList / entitySet patterns ===')
for m in re.finditer(r'.{0,50}(?:entityList|entitySet|entityName|logicalName|listView).{0,100}', text, re.I):
    t = m.group().strip()
    if len(t) > 10:
        print(f'  {t[:200]}')

# Look for Power Pages specific markers
print('\n=== Power Pages markers ===')
for m in re.finditer(r'.{0,30}(?:powerpages|powerapp|dataverse|dynamics|msdynmkt|portal|Microsoft).{0,100}', text, re.I):
    t = m.group().strip()
    if len(t) > 5:
        print(f'  {t[:200]}')
        break  # Just first one

# Look for search/list configuration
print('\n=== Search/list config ===')
for m in re.finditer(r'(?:searchConfig|listConfig|gridConfig|tableConfig|filterConfig)\s*[=:]\s*(\{[^}]{0,500}\})', text, re.DOTALL):
    print(f'  {m.group()[:300]}')
