import re
import traceback

def refactor_html():
    path = r"d:\Desktop\MOD HOR\prototype\index.html"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Módulo 1 (BASE_URL unificada)
    content = content.replace("global.CONFIG = {", "global.window = global;\n        window.CONFIG = {")
    
    # 2. Reemplazo de BASE_URL global
    content = re.sub(r'(?:const|let|var)\s+API_BASE_URL\s*=\s*[\'"].*?[\'"];?', '', content)
    content = re.sub(r'(?:const|let|var)\s+API_DOC\s*=\s*[\'"].*?[\'"];?', '', content)
    
    content = content.replace("${API_BASE_URL}", "${window.CONFIG.BASE_URL}")
    content = content.replace("API_BASE_URL", "window.CONFIG.BASE_URL")
    
    content = content.replace("${API_DOC}", "${window.CONFIG.BASE_URL}/api/docentes")
    content = content.replace("API_DOC +", 'window.CONFIG.BASE_URL + "/api/docentes" +')
    content = re.sub(r'\bAPI_DOC\b', '`${window.CONFIG.BASE_URL}/api/docentes`', content)
    
    content = content.replace("global.CONFIG.BASE_URL", "window.CONFIG.BASE_URL")
    content = re.sub(r'const\s+BASE_URL\s*=\s*[\'"].*?[\'"];?', '', content)
    content = re.sub(r'\bBASE_URL\b(?!\')', 'window.CONFIG.BASE_URL', content)

    # 3. Desenvolver TODO EL CÓDIGO de DOMContentLoaded
    start_tag = 'document.addEventListener("DOMContentLoaded", () => {'
    
    # Podrían haber Varios (el original, y los inyectados nuestros)
    # Haremos Unwrap seguro de TODOS
    while True:
        idx = content.find(start_tag)
        if idx == -1:
            break
            
        brace_start = content.find('{', idx)
        open_b = 1
        curr = brace_start + 1
        
        while curr < len(content) and open_b > 0:
            if content[curr] == '{': open_b += 1
            elif content[curr] == '}': open_b -= 1
            curr += 1
            
        end_idx = curr # The character after matching '}'
        # the closing is usally `});`
        close_tag_end = end_idx
        if content[end_idx:end_idx+2] == ");":
            close_tag_end = end_idx + 2
            
        inner = content[brace_start+1:end_idx-1]
        
        # Eliminar las llamadas sueltas de inicio que el user puso en este bloque
        inner = inner.replace("loadUploadHistory();", "")
        inner = inner.replace("setInitialDates();", "")
        inner = inner.replace("loadRptCatalogs();", "")
        inner = inner.replace("loadObsLogs();", "")
        inner = inner.replace("initApp();", "")
        
        content = content[:idx] + "\n        // --- UNWRAPPED SCOPE ---\n" + inner + "\n" + content[close_tag_end:]

    # Remove that dynamic export module from our previous try to clean up
    content = re.sub(r'// ==========================================\n\s*// MÓDULO EXTRA: EXPORTADOR DINÁMICO HTML.*?\n\s*\}\)\(window\);', '', content, flags=re.DOTALL)
    
    # 4. FETCH
    lines = content.splitlines()
    for i in range(len(lines)):
        l = lines[i]
        if "function authFetch" in l or "nativeFetch" in l or "authFetch(" in l:
            continue
        if "fetch(" in l or ".fetch(" in l:
            l = re.sub(r'(?<!auth)(?<!native)(?<!\.)\bfetch\s*\(', 'window.authFetch(', l)
            lines[i] = l
            
    content = "\n".join(lines)

    # 5. Exportaciones
    html_part = content[:content.find("<script>")]
    handlers = re.findall(r'\bon[a-z]+=["\']([^"\']+)["\']', html_part)
    funcs_to_expose = set()
    for h in handlers:
        for match in re.finditer(r'([a-zA-Z0-9_]+)\s*\(', h):
            funcs_to_expose.add(match.group(1))

    for k in ['if', 'for', 'window', 'document', 'console', 'alert']:
        funcs_to_expose.discard(k)
        
    explicit_exports = "\n        // --- EXPLICIT HTML BINDINGS ---\n"
    for fn in sorted(list(funcs_to_expose)):
        explicit_exports += f"        if(typeof {fn} !== 'undefined') window.{fn} = {fn};\n"

    explicit_exports += "        window.authFetch = typeof authFetch !== 'undefined' ? authFetch : window.authFetch;\n"
    explicit_exports += "        if(typeof initApp !== 'undefined') window.initApp = initApp;\n"

    # Insertar exports antes del fin del script
    script_end = content.rfind("</script>")
    content = content[:script_end] + explicit_exports + "\n    " + content[script_end:]

    # 6. INITAPP y RACE CONDITION
    # Buscamos initApp function { showApp(); ... }
    # Reemplazaremos todo el bloque final de initApp para que maneje la carga
    
    init_body = """showApp();
                if(typeof applyRBAC !== 'undefined') applyRBAC();
                
                // DEFERRED DATA LOADS (RACE CONDITION PREVENTED)
                console.log("✅ Sesión y roles validados. Iniciando Cargas Generales...");
                if(typeof loadRptCatalogs !== 'undefined') await loadRptCatalogs();
                if(typeof loadObsLogs !== 'undefined') await loadObsLogs();
                if(typeof loadUploadHistory !== 'undefined') loadUploadHistory();
                if(typeof setInitialDates !== 'undefined') setInitialDates();
                
            } catch (e) {
"""

    content = re.sub(r'showApp\(\);[\s\S]*?\} catch \(e\) \{', init_body, content, count=1)
    
    # Inyectar el listener maestro
    mega_bootstrap = """
    // ==========================================
    // INICIALIZACIÓN ABSOLUTA E INMUTABLE
    // ==========================================
    document.addEventListener("DOMContentLoaded", async () => {
        if (window.initApp) {
            await window.initApp();
        }
    });
    """
    content = content[:script_end] + mega_bootstrap + "\n" + content[script_end:]

    # 7. Diagnóstico array(0)
    # Buscar parseos a JSON
    content = content.replace("lastMaestraData = data.data || [];", 'console.log("API RESPONSE (Docentes):", data);\n                lastMaestraData = data.data || [];')
    
    # Escribir
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
        
    print("Refactor HTML Arquitectural Finalizado.")

if __name__ == "__main__":
    try:
        refactor_html()
    except Exception as e:
        traceback.print_exc()

