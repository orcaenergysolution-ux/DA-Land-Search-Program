"""Find the API that populates permit detail pages."""
import re, json

text = open('scripts/baddaginnie_raw.html', encoding='utf-8').read()

print(f'Page size: {len(text)}')

# External scripts
scripts = re.findall(r'<script[^>]+src=["\']([^"\']+)["\']', text, re.I)
print(f'\nExternal scripts ({len(scripts)}):')
for s in scripts:
    print(f'  {s}')

# ALL inline script blocks - filter for interesting ones
inline = re.findall(r'<script(?:[^>]*)>(.*?)</script>', text, re.DOTALL | re.I)
print(f'\nInline script blocks: {len(inline)}')
for i, block in enumerate(inline):
    block = block.strip()
    if not block:
        continue
    if len(block) > 20:
        print(f'\n--- Block {i} ({len(block)} chars) ---')
        print(block[:2000])

# All fetch/XHR patterns
print('\n=== fetch() calls ===')
for m in re.finditer(r'fetch\s*\(([^)]{5,300})\)', text, re.DOTALL):
    print(f'  {m.group(1).strip()[:200]}')

# API URL patterns
print('\n=== URL patterns ===')
api_urls = re.findall(r'["\'](/(?:api|_api|odata|data)[^"\']{5,200})["\']', text)
for u in api_urls[:20]:
    print(f'  {u}')
