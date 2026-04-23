import re

path = r"d:\Desktop\MOD HOR\prototype\index.html"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

script_start = content.find("<script>")
# Extract just HTML part for checking handlers
html_part = content[:script_start]
js_part = content[script_start:]

# 1. Encontrar todas las funciones de los manejadores HTML (onclick, onchange, etc)
handlers = re.findall(r'\bon[a-z]+=["\']([^"\']+)["\']', html_part)
funcs_to_expose = set()
# Also look for onXX='...'. Note we used ["\'] so it handles both
for h in handlers:
    # Handle multiple statements like "nav('upload'); loadConfig();"
    # Actually, simpler: find all words followed by (
    for match in re.finditer(r'([a-zA-Z0-9_]+)\s*\(', h):
        funcs_to_expose.add(match.group(1))

# Quitar posibles palabras clave reservadas de JS atrapadas por error
for k in ['if', 'for', 'window', 'document', 'console', 'alert']:
    if k in funcs_to_expose:
        funcs_to_expose.remove(k)

# 2. Exponer dinámicamente:
exports_block = "\n" + "\n".join([f"        if(typeof {fn} !== 'undefined') global.{fn} = {fn};" for fn in sorted(list(funcs_to_expose))]) + "\n"

# Vamos a inyectar esto justo antes del cierre del main wrapper (asumo Legacy Business Logic o global)
# Para ser más seguros, inyectaremos un nuevo bloque de exports al final del todo o en un nuevo script tag
global_exposer = f"""
    // ==========================================
    // MÓDULO EXTRA: EXPORTADOR DINÁMICO HTML
    // ==========================================
    (function(global) {{
{exports_block}
    }})(window);
"""
# Oops, las funciones legacy están dentro de la IIFE de MÓDULO 7, si las variables (arrow functions) no son globales (porque let/const no saltan la IIFE), no podemos exportarlas desde UNA IIFE DIFERENTE.
# TENEMOS QUE inyectar estos exports DENTRO del Módulo 7 (Legacy Business Logic) justo al final de su wrapper.

# Busquemos donde cierra Módulo 7
mod7_end = js_part.find("// --- GLOBAL EXPORTS FOR LEGACY ACROSS HTML ---")
if mod7_end != -1:
    mod7_closing = js_part.find("})(window);", mod7_end)
    if mod7_closing != -1:
        # Reemplazamos los viejos exports con la lista definitiva + extra dinámica (por si variables locales)
        # We will just append the safe ones directly before `})(window);`
        js_part = js_part[:mod7_closing] + exports_block + "    " + js_part[mod7_closing:]

# 3. Eliminar las cargas automáticas del Bootstrap
bootstrap_marker = "// INITIALIZATION BOOTSTRAP"
b_idx = js_part.find(bootstrap_marker)
if b_idx != -1:
    end_bootstrap = js_part.find("});", b_idx)
    # Reemplazamos ese bloque para que solo llame a initApp
    new_bootstrap = """// INITIALIZATION BOOTSTRAP
    // ==========================================
    document.addEventListener('DOMContentLoaded', () => {
        if(window.initApp) window.initApp();
    });
"""
    js_part = js_part[:b_idx] + new_bootstrap + js_part[end_bootstrap+3:]

# 4. Mover las cargas a la resolución de initApp() en Módulo 3
initapp_marker = "showApp();"
ia_idx = js_part.find(initapp_marker)
if ia_idx != -1:
    injection = """showApp();
                if(global.applyRBAC) global.applyRBAC();
                
                // Cargas Diferidas, solo si hay sesión
                if(typeof setInitialDates !== 'undefined') setInitialDates();
                else if(global.setInitialDates) global.setInitialDates();
                
                if(typeof loadRptCatalogs !== 'undefined') loadRptCatalogs();
                else if(global.loadRptCatalogs) global.loadRptCatalogs();
                
                if(typeof loadObsLogs !== 'undefined') loadObsLogs();
                else if(global.loadObsLogs) global.loadObsLogs();
"""
    # replacing properly
    js_part = js_part.replace("showApp();\n                if(global.applyRBAC) global.applyRBAC();", injection)


# 5. Reemplazar todos los fetch() huérfanos que hayan quedado por fallos previos, asegurando no dañar authFetch
# Reemplazamos "fetch(" con "global.authFetch(" EXCEPTO donde aparece "nativeFetch" o "window.fetch"
# Pero cuidado con "authFetch(url, options = {})" declaration.
# Ya usamos python nativo sin regex complejo

# Pasamos por líneas
lines = js_part.splitlines()
for i in range(len(lines)):
    line = lines[i]
    if "function authFetch" in line or "global.authFetch" in line or "authFetch =" in line:
        continue
    if "nativeFetch" in line or "window.fetch" in line:
        continue
    # reemplazar llamadas a fetch
    if " fetch(" in line or ".fetch(" in line or "fetch(" in line:
        line = re.sub(r'(?<!auth)(?<!native)fetch\s*\(', 'global.authFetch(', line)
        lines[i] = line

js_part = "\n".join(lines)


# Escribir todo devuelta
with open(path, "w", encoding="utf-8") as f:
    f.write(html_part + js_part)

print(f"Funciones Dinámicas a Exponer detectadas: {sorted(list(funcs_to_expose))}")
print("Fix aplicado exitosamente.")
