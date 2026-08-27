from pathlib import Path
import base64, gzip, json, re

p = Path('index.html')
s = p.read_text(encoding='utf-8')

m = re.search(r'<script id="payload" type="text/plain">(.*?)</script>', s, re.S)
if not m:
    raise SystemExit('compressed payload not found')

encoded = m.group(1).strip()
raw = gzip.decompress(base64.b64decode(encoded)).decode('utf-8')
data = json.loads(raw)
plain = json.dumps(data, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')

start, end = m.span()
s = s[:start] + '<script id="embedded-json" type="application/json">' + plain + '</script>' + s[end:]

s = re.sub(
    r"async function decode\(\)\{.*?\}",
    "function decode(){return Promise.resolve(JSON.parse(document.getElementById('embedded-json').textContent))}",
    s,
    count=1,
    flags=re.S,
)

if 'DecompressionStream' in s or 'atob(' in s:
    raise SystemExit('compression code still remains')
if 'id="embedded-json"' not in s:
    raise SystemExit('embedded JSON script missing')

# Round-trip validation before writing.
m2 = re.search(r'<script id="embedded-json" type="application/json">(.*?)</script>', s, re.S)
json.loads(m2.group(1))

p.write_text(s, encoding='utf-8')
print('converted index.html to plain embedded JSON')
print('size:', p.stat().st_size)
