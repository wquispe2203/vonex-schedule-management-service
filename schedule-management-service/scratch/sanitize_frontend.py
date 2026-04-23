import re
import os

def sanitize_js(file_path):
    if not os.path.exists(file_path):
        print(f"File {file_path} not found.")
        return
        
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Replace onclick="fun(${id})" with onclick="fun('${id}')"
    # Handling both double and single quotes for the attribute
    content = re.sub(r'onclick="(.*?)\(\$\{([a-zA-Z0-9._]+id.*?)\}(.*?)\)"', r'onclick="\1(\'${\2}\'\3)"', content)
    content = re.sub(r"onclick='(.*?)\(\$\{([a-zA-Z0-9._]+id.*?)\}(.*?)\)'", r"onclick='\1(\'${\2}\'\3)'", content)
    
    # Special case for handleStatusClick which has multiple params
    # We find handleStatusClick(${id}, and wrap ${id}
    content = re.sub(r'handleStatusClick\(\$\{([a-zA-Z0-9._]+id.*?)\},', r"handleStatusClick('${\1}',", content)

    # 2. Remove parseInt(...) around id-like variables
    # This is trickier, let's look for known patterns
    content = re.sub(r'parseInt\(([a-zA-Z0-9._]+)\.getAttribute\([\'"]data-id[\'"]\)\)', r'\1.getAttribute("data-id")', content)
    content = re.sub(r'parseInt\((cb|u|t|s|c|id|uid)\.dataset\.id\)', r'\1.dataset.id', content)
    content = re.sub(r'parseInt\((.*?)\.id\)', r'\1.id', content)
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Sanitization complete for {file_path}")

if __name__ == "__main__":
    sanitize_js("d:/Desktop/MOD HOR/prototype/js_dump.js")
    sanitize_js("d:/Desktop/MOD HOR/prototype/index.html")
