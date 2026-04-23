import re
import os
import json

file_path = r'd:\Desktop\MOD HOR\prototype\index.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update HTML inline callers to pass 'this' if appropriate
# For handleObsTypeChange
content = re.sub(
    r'id="obs-form-type"\s+onchange="handleObsTypeChange\(\)"',
    r'id="obs-form-type" onchange="handleObsTypeChange(this)"',
    content
)

# 2. Re-write handleObsTypeChange function implementation
old_func = """                function handleObsTypeChange() {
                    const type = document.getElementById('obs-form-type').value;
                    const replContainer = document.getElementById('obs-replacement-fields');
                    if (!replContainer) return;

                    if (type === 'REEMPLAZO') {
                        replContainer.classList.remove('hidden');
                    } else {
                        replContainer.classList.add('hidden');
                    }
                }"""

new_func = """                function handleObsTypeChange(selectElem) {
                    // Try to read from selectElem, otherwise fallback to DOM element directly
                    let type = '';
                    if (selectElem && selectElem.value) {
                        type = selectElem.value;
                    } else {
                        const el = document.getElementById('obs-form-type');
                        if (el) type = el.value;
                    }
                    
                    const replContainer = document.getElementById('obs-replacement-fields');
                    if (!replContainer) return;

                    if (type === 'REEMPLAZO') {
                        replContainer.classList.remove('hidden');
                    } else {
                        replContainer.classList.add('hidden');
                    }
                }"""

content = content.replace(old_func, new_func)

# 3. Prevent functions strictly from being trapped inside DOMContentLoaded
# We will use Regex to warn, but the standard structure previously was IIFE.
# There shouldn't be UI functions inside DOMContentLoaded, we'll check it manually later.

# 4. Auditoría Global de Handlers: Extract all inline handlers from HTML
html_block_match = re.search(r'<body.*?>(.*?)<script>', content, re.DOTALL | re.IGNORECASE)
html_block = html_block_match.group(1) if html_block_match else content

handlers_in_html = set()
for m in re.finditer(r'\bon[a-z]+="([^"]+)"', html_block):
    call_str = m.group(1)
    # Extract function name (e.g. nav('rpt') -> nav)
    fm = re.match(r'^\s*([a-zA-Z0-9_]+)\s*\(', call_str)
    if fm:
        handlers_in_html.add(fm.group(1))

# Write out the detected HTML handlers
with open(r'd:\Desktop\MOD HOR\tmp\detected_html_handlers.json', 'w') as f:
    json.dump(sorted(list(handlers_in_html)), f)

# 5. Extract ALL defined functions in the JS block inside the IIFE or globally
js_block_match = re.search(r'<script>(.*?)</script>', content, re.DOTALL | re.IGNORECASE)
js_block = js_block_match.group(1) if js_block_match else content

functions_in_js = set()
for m in re.finditer(r'\b(?:async\s+)?function\s+([a-zA-Z0-9_]+)\s*\(', js_block):
    functions_in_js.add(m.group(1))

# Any variable assigned a function or async function
for m in re.finditer(r'\b(const|let|var)\s+([a-zA-Z0-9_]+)\s*=\s*(async\s*)?(function|\([^)]*\)\s*=>|[a-zA-Z0-9_]+\s*=>)', js_block):
    functions_in_js.add(m.group(2))

with open(r'd:\Desktop\MOD HOR\tmp\detected_js_functions.json', 'w') as f:
    json.dump(sorted(list(functions_in_js)), f)

# Find missing handlers (used in HTML but not defined in JS)
missing = handlers_in_html - functions_in_js
with open(r'd:\Desktop\MOD HOR\tmp\missing_handlers.json', 'w') as f:
    json.dump(sorted(list(missing)), f)

# 6. Estandarización Global - Build window.APP_HANDLERS
# To be safe, only include handlers that exist in JS and are used in HTML, or just all HTML handlers that exist.
handlers_to_export = handlers_in_html.intersection(functions_in_js)

# We also need to extract existing `global.XXX = XXX;` exports to make sure we don't drop any that might be called from somewhere else.
existing_exports = set()
for m in re.finditer(r'global\.([a-zA-Z0-9_]+)\s*=\s*[a-zA-Z0-9_]+;', js_block):
    existing_exports.add(m.group(1))

final_exports = handlers_to_export.union(existing_exports).intersection(functions_in_js)

# We will remove the old `global.XXX = XXX;` block
new_js_block = re.sub(r'// --- GLOBAL EXPORTS:.*?global\.[a-zA-Z0-9_]+\s*=\s*[a-zA-Z0-9_]+;(\s*global\.[a-zA-Z0-9_]+\s*=\s*[a-zA-Z0-9_]+;)*\s*', '', js_block, flags=re.DOTALL)
# Also remove any remaining global assignments
new_js_block = re.sub(r'^\s*global\.[a-zA-Z0-9_]+\s*=\s*[a-zA-Z0-9_]+;\n?', '', new_js_block, flags=re.MULTILINE)

# Build APP_HANDLERS block
app_handlers_str = """
                // ==========================================
                // GLOBAL EXPORTS REGISTRY (APP_HANDLERS)
                // ==========================================
                window.APP_HANDLERS = {
"""
for fn in sorted(list(final_exports)):
    if fn != 'if': # Sanity check
        app_handlers_str += f"                    {fn},\n"
app_handlers_str += "                };\n"
app_handlers_str += "                Object.assign(window, window.APP_HANDLERS);\n"

# 7. Validación Post-Carga
validation_script = """

            // ==========================================
            // SMART RUNTIME VALIDATOR
            // ==========================================
            document.addEventListener('DOMContentLoaded', () => {
                console.log("🔍 [Auditoría] Detectando handlers inline en el HTML...");
                
                const allElements = document.querySelectorAll('*');
                const usedHandlers = new Set();
                
                allElements.forEach(el => {
                    Array.from(el.attributes).forEach(attr => {
                        if (attr.name.startsWith('on')) {
                            const match = attr.value.match(/^\s*([a-zA-Z0-9_]+)\s*\(/);
                            if (match) usedHandlers.add(match[1]);
                        }
                    });
                });

                let missingCount = 0;
                let okCount = 0;
                
                console.group("🛡️ Resultados de Validación de Scope UI");
                usedHandlers.forEach(fn => {
                    if (typeof window[fn] !== "function") {
                        console.error(`❌ Handler faltante en runtime (ReferenceError risk): ${fn}`);
                        missingCount++;
                    } else if (!window.APP_HANDLERS || !window.APP_HANDLERS[fn]) {
                        console.warn(`⚠️ Handler existente pero NO registrado en APP_HANDLERS: ${fn}`);
                        okCount++;
                    } else {
                        // console.log(`✅ Handler validado y exportado: ${fn}`);
                        okCount++;
                    }
                });
                
                if (missingCount === 0) {
                    console.log(`✅ Todos los ${okCount} handlers inline están correctamente definidos y accesibles globalmente.`);
                } else {
                    console.error(`🚨 PELIGRO: Se detectaron ${missingCount} handlers rotos que causarán ReferenceError.`);
                }
                console.groupEnd();
            });
"""

# Inject before `})(window);`
if "})(window);" in new_js_block:
    new_js_block = new_js_block.replace("})(window);", app_handlers_str + "\n            })(window);")
else:
    # If not found for some reason, append to end
    new_js_block += app_handlers_str

# Inject validation script after `})(window);` before final initialization
if "// INITIALIZATION BOOTSTRAP" in new_js_block:
    new_js_block = new_js_block.replace("// INITIALIZATION BOOTSTRAP", validation_script + "\n            // INITIALIZATION BOOTSTRAP")
else:
    new_js_block += validation_script

new_content = content.replace(js_block, new_js_block)

# Backup original and write new content
import shutil
shutil.copy(file_path, file_path + ".bak")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(new_content)

print("SUCCESS: Refactored UI Handlers. Backup created at " + file_path + ".bak")
