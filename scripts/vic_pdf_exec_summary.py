"""Extract executive summary and all numeric capacity values from Baddaginnie PDF."""
import re
import pdfminer.high_level as pdfminer

pdf = r'scripts/48f07100-e1b8-ee11-9078-002248922d75_PA2402710 Baddaginnie Solar Farm Officer Report REDACTED.pdf'
text = pdfminer.extract_text(pdf)

print(f'Total chars: {len(text)}')
print()

# Find the executive summary section
exec_m = re.search(r'EXECUTIVE SUMMARY.{0,8000}', text, re.IGNORECASE | re.DOTALL)
if exec_m:
    print('=== EXECUTIVE SUMMARY ===')
    print(exec_m.group()[:3000])
else:
    print('No EXECUTIVE SUMMARY found')

# All numeric mentions near MW/MWh
print('\n=== All numeric MW/MWh mentions ===')
for m in re.finditer(r'[\d,\.]+\s*(?:MW|MWh|megawatt|kilowatt|KW|GW)', text, re.IGNORECASE):
    # Get context
    start = max(0, m.start() - 80)
    end = min(len(text), m.end() + 80)
    ctx = text[start:end].replace('\n', ' ').strip()
    print(f'  VALUE: {m.group()!r}  CONTEXT: {ctx[:200]}')
print()

# Print first 2000 chars of document
print('=== Start of document ===')
print(text[:3000])
