import os
import re

JS_DIR = r'd:\Desktop\MOD HOR\prototype\js'
js_files = [f for f in os.listdir(JS_DIR) if f.endswith('.js')]

print("=== JS FILES IN DIR ===")
for f in js_files:
    print(f"- {f}")

print("\n=== EXTRACTING IMPORTS & EXPORTS ===")
for filename in js_files:
    filepath = os.path.join(JS_DIR, filename)
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f"\n--- File: {filename} ---")
    
    # Extract Imports
    imports = re.findall(r'^import\s+(.*?)\s+from\s+[\'"](.*?)[\'"]', content, re.MULTILINE)
    if imports:
        print("  Imports:")
        for imp, src in imports:
            print(f"    - {imp.strip()} FROM '{src}'")
    else:
        print("  Imports: None")

    # Extract Exports
    exports = re.findall(r'^export\s+(const|let|var|function|async\s+function|class)\s+([a-zA-Z0-9_]+)', content, re.MULTILINE)
    default_export = re.search(r'^export\s+default\s+(.*)', content, re.MULTILINE)
    if exports or default_export:
        print("  Exports:")
        for kind, name in exports:
            print(f"    - {kind} {name}")
        if default_export:
            print(f"    - DEFAULT: {default_export.group(1).strip()}")
    else:
        print("  Exports: None")
        
    # Extract event listeners
    listeners = re.findall(r'\b(addEventListener|[\w]+\.on[\w]+)\s*\(', content)
    if listeners:
        print("  Listeners:")
        for line_no, line in enumerate(content.split('\n'), 1):
            if 'addEventListener' in line or '.on' in line:
                if 'import' not in line and 'export' not in line:
                    print(f"    - L{line_no}: {line.strip()}")

    # Check for top-level (self-executing) code
    # Simple check: code outside functions/objects that isn't import/export
    # We'll skip for now, but we'll look for specific bootstrap functions called directly
    self_invocations = re.findall(r'^[a-zA-Z0-9_]+\s*\(.*?\)\s*;', content, re.MULTILINE)
    if self_invocations:
        print("  Possible self-invoking top-level code:")
        for inv in self_invocations:
            print(f"    - {inv}")
