import os
import re

html_path = r"d:\Desktop\MOD HOR\prototype\index.html"
js_dump_path = r"d:\Desktop\MOD HOR\prototype\js_dump.js"

with open(html_path, "r", encoding="utf-8") as f:
    html = f.read()

start_idx = html.find('<script>')
if start_idx != -1:
    end_idx = html.find('</script>', start_idx)
    js_code = html[start_idx+8:end_idx]
    with open(js_dump_path, "w", encoding="utf-8") as f2:
        f2.write(js_code)
    print(f"Extracted JS: {len(js_code)} chars.")
else:
    print("No <script> found.")
