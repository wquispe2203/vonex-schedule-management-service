import re

file_path = r'd:\Desktop\MOD HOR\prototype\js\usuarios.js'
with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

print("--- TOP LEVEL ANALYSIS OF usuarios.js ---")
for i, line in enumerate(lines):
    stripped = line.strip()
    if not stripped:
        continue
    if stripped.startswith('//') or stripped.startswith('/*') or stripped.startswith('*'):
        continue
    # Check if the line starts at column 0 and doesn't start with typical declarations
    if line[0].isalpha():
        # Ensure it is a valid top-level keyword
        if not any(line.startswith(k) for k in ['import', 'export', 'let', 'const', 'function']):
            print(f"POTENTIAL SIDE EFFECT AT LINE {i+1}: {line.rstrip()}")

print("--- ANALYSIS END ---")
