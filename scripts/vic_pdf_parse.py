"""Download and parse VIC permit PDFs to extract capacity (MW)."""
import urllib.request, re, sys, os, subprocess
import urllib.parse

PDFS = [
    'https://sftpbspomppprod01.blob.core.windows.net/applicationfiles/48f07100-e1b8-ee11-9078-002248922d75_PA2402710%20Baddaginnie%20Solar%20Farm%20Officer%20Report%20REDACTED.pdf',
    'https://sftpbspomppprod01.blob.core.windows.net/applicationfiles/48f07100-e1b8-ee11-9078-002248922d75_PA2402710-Baddaginnie%20Solar%20Farm-Planning%20permit-Form%204-%20071124.pdf',
]

for pdf_url in PDFS:
    fname = urllib.parse.unquote(pdf_url.split('/')[-1])
    local = f'scripts/{fname}'
    print(f'\nDownloading: {fname}')
    try:
        req = urllib.request.Request(pdf_url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        })
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = resp.read()
        with open(local, 'wb') as f:
            f.write(data)
        print(f'  Saved {len(data):,} bytes -> {local}')

        # Try to extract text with pdfminer or PyMuPDF
        extracted = False
        try:
            import pdfminer.high_level as pdfminer
            text = pdfminer.extract_text(local)
            print(f'  Text length: {len(text)} chars')

            # Find MW/MWh
            print('  === Capacity mentions ===')
            for m in re.finditer(r'.{0,80}(?:MW|MWh|megawatt|Megawatt|capacity|Capacity|generating|output).{0,80}', text):
                t = m.group().strip()
                if len(t) > 10 and any(c.isdigit() for c in t):
                    print(f'    {t[:200]}')
            extracted = True
        except ImportError:
            pass

        if not extracted:
            try:
                import fitz  # PyMuPDF
                doc = fitz.open(local)
                text = ''
                for page in doc:
                    text += page.get_text()
                print(f'  Text length: {len(text)} chars (PyMuPDF)')
                for m in re.finditer(r'.{0,80}(?:MW|MWh|megawatt|capacity|generating).{0,80}', text, re.I):
                    t = m.group().strip()
                    if len(t) > 10 and any(c.isdigit() for c in t):
                        print(f'    {t[:200]}')
                extracted = True
            except ImportError:
                pass

        if not extracted:
            print('  No PDF parser available (pdfminer/PyMuPDF not installed)')
            print('  Try: pip install pdfminer.six or pip install pymupdf')

    except Exception as e:
        print(f'  Error: {e}')
