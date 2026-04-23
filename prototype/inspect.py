import sys

path = r'd:\Desktop\MOD HOR\prototype\js_dump.js'
try:
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    for i, line in enumerate(lines):
        if '//' in line and ('═' in line or '─' in line or '==' in line):
            print(f'{i}: {line.strip()}')
            
except Exception as e:
    print("Error:", e)
