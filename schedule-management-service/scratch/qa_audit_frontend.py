import re

def audit_frontend():
    file_path = "d:/Desktop/MOD HOR/prototype/index.html"
    with open(file_path, "r", encoding="utf-8") as f:
        html = f.read()

    lines = html.split("\n")
    issues = []
    
    # regex to find potential unquoted JS injections like \$\{.*?id.*?\} inside onclick or dataset bindings
    # examples: onclick="myFunc(${u.id})"  (BAD) -> onclick="myFunc('${u.id}')" (GOOD)
    pattern_onclick = re.compile(r'on[A-Za-z]+=(["\'])(.*?)\1')
    pattern_parseint = re.compile(r'parseInt\([^)]*id[^)]*\)', re.IGNORECASE)
    pattern_number = re.compile(r'Number\([^)]*id[^)]*\)', re.IGNORECASE)
    
    for i, line in enumerate(lines):
        # Check parseInt and Number
        if pattern_parseint.search(line):
            issues.append({"type": "Frontend - Casteo Numérico", "line": i+1, "content": line.strip()})
        if pattern_number.search(line):
            issues.append({"type": "Frontend - Casteo Numérico", "line": i+1, "content": line.strip()})
            
        # Check unquoted JS interpolation of IDs
        matches = pattern_onclick.findall(line)
        for quote, onclick_content in matches:
            # Look for ${var.id} inside onclick_content
            # It's bad if it's NOT surrounded by quotes inside the interpolation string.
            # But the onclick itself is a string. Wait, if it's evaluated in a template literal `... ${u.id} ...`
            # For this basic script let's just find any ${...id...} without quotes around the ${...}
            # Like \(\{.*?id.*?\}\) without preceding quote. By regex: (?<!['"])\$\{.*?id.*?\}(?!['"])
            if re.search(r'(?<![\'"])\$\{.*?id.*?\}(?![\'"])', onclick_content, re.IGNORECASE):
                 issues.append({"type": "Frontend - Inyección UUID Expuesta (Syntax Error UX)", "line": i+1, "content": onclick_content})

            # Check for legacy passing like `function(item.id)`
            if re.search(r'\([^\'"]*?id[^\'"]*?\)', onclick_content, re.IGNORECASE):
                # if there is an id without quotes being passed
                 issues.append({"type": "Frontend - Función nativa JS ID sin string literal", "line": i+1, "content": onclick_content})

    return issues

if __name__ == "__main__":
    issues = audit_frontend()
    for issue in issues:
        print(f"L{issue['line']} [{issue['type']}]: {issue['content']}")
    if not issues:
        print("Frontend Audit: SUCCESS. No unquoted IDs or parseInt found.")
