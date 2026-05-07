import re

path = r"d:\Desktop\MOD HOR\prototype\index.html"
with open(path, "r", encoding="utf-8") as f:
    html = f.read()

# Reemplaza onclick="..." por data-action="..."
new_html = re.sub(r'onclick="([^"]+)"', r'data-action="\1"', html)

with open(path, "w", encoding="utf-8") as f:
    f.write(new_html)

print("Reemplazo de onclick a data-action completado en index.html")
