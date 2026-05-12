import re

with open(r'd:\Desktop\MOD HOR\prototype\index.html', 'r', encoding='utf-8') as f:
    content = f.read()

scripts = re.findall(r'<script.*?>.*?</script>', content, re.DOTALL)
print(f"Found {len(scripts)} script tags:")
for i, s in enumerate(scripts):
    print(f"--- Script {i+1} ---")
    print(s)
