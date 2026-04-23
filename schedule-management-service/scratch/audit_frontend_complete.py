import re
import os

def audit_file(file_path):
    print(f"--- Auditing: {file_path} ---")
    if not os.path.exists(file_path):
        print("File not found.")
        return
        
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    lines = content.split("\n")
    patterns = [
        (re.compile(r'parseInt\([^)]*id[^)]*\)', re.I), "parseInt en ID"),
        (re.compile(r'Number\([^)]*id[^)]*\)', re.I), "Number en ID"),
        (re.compile(r'on[A-Za-z]+=["\'][^"\']*?\([^"\'\n]*?\$\{.*?id.*?\}', re.I), "Inyección ID sin comillas (Interpolación)"),
        (re.compile(r'on[A-Za-z]+=["\'][^"\']*?\([^"\'\n]*?[utlc]\.(id|uid)', re.I), "Inyección ID sin comillas (Propiedad objeto)"),
    ]
    
    for i, line in enumerate(lines):
        for pattern, label in patterns:
            if pattern.search(line):
                print(f"L{i+1} [{label}]: {line.strip()}")

if __name__ == "__main__":
    audit_file("d:/Desktop/MOD HOR/prototype/js_dump.js")
    audit_file("d:/Desktop/MOD HOR/prototype/index.html")
    # Audit other active JS if any (e.g. from script tags)
