import re
import json

with open('d:/Desktop/MOD HOR/prototype/index.html', encoding='utf-8') as f:
    html = f.read()

handlers = re.findall(r'\bon[a-z]+=\"([^\"]+)\"', html)
funcs = set()
for h in handlers:
    m = re.search(r'([a-zA-Z0-9_]+)\(', h)
    if m:
        funcs.add(m.group(1))

with open('d:/Desktop/MOD HOR/prototype/funcs_output.json', 'w') as f:
    json.dump(sorted(list(funcs)), f)
