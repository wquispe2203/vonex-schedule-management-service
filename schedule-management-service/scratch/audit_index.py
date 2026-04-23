import re

def audit_html(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        html = f.read()

    lines = html.split("\n")
    patterns = [
        (re.compile(r'parseInt\([^)]*id[^)]*\)', re.I), "parseInt detectado en ID"),
        (re.compile(r'Number\([^)]*id[^)]*\)', re.I), "Number detectado en ID"),
        (re.compile(r'on[A-Za-z]+=["\'][^"\']*?\([^"\'\n]*?\$\{.*?id.*?\}', re.I), "Inyección ID sin comillas en onclick (Interpolación)"),
        (re.compile(r'on[A-Za-z]+=["\'][^"\']*?\([^"\'\n]*?u\.id', re.I), "Inyección ID sin comillas en onclick (u.id)"),
        (re.compile(r'on[A-Za-z]+=["\'][^"\']*?\([^"\'\n]*?t\.uid', re.I), "Inyección ID sin comillas en onclick (t.uid)"),
    ]
    
    matches = []
    for i, line in enumerate(lines):
        for pattern, label in patterns:
            if pattern.search(line):
                matches.append(f"L{i+1} [{label}]: {line.strip()}")
    
    return matches

if __name__ == "__main__":
    results = audit_html("d:/Desktop/MOD HOR/prototype/index.html")
    for r in results:
        print(r)
