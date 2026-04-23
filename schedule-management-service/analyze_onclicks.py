import re

with open("d:/Desktop/MOD HOR/prototype/index.html", "r", encoding="utf-8") as f:
    html = f.read()

onclicks = re.findall(r'onclick="([^"]+)"', html)

from collections import Counter
for call, count in Counter(onclicks).most_common():
    print(f"{count}: {call}")
