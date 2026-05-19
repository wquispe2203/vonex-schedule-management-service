import re
import os

path = r"d:\Desktop\MOD HOR\prototype\index.html"

with open(path, "r", encoding="utf-8") as f:
    html = f.read()

start_idx = html.find("<script>")
end_idx = html.find("</script>", start_idx)

if start_idx == -1 or end_idx == -1:
    print("Script tag not found")
    exit(1)

js_content = html[start_idx+8:end_idx]

new_js_structure = """
    // ==========================================
    // MÓDULO 1: CONFIGURACIÓN GLOBAL
    // ==========================================
    (function(global) {
        global.CONFIG = {
            BASE_URL: 'http://localhost:8000',
            API_DOC: 'http://127.0.0.1:8000/api/docentes'
        };
    })(window);

    // ==========================================
    // MÓDULO 2: AUTH JWT
    // ==========================================
    (function(global) {
        function getToken() { return localStorage.getItem('access_token'); }
        function setToken(token) { localStorage.setItem('access_token', token); }

        function parseJwt(token) {
            try { return JSON.parse(atob(token.split('.')[1])); } 
            catch (e) { return {}; }
        }

        const nativeFetch = window.fetch;

        async function authFetch(url, options = {}) {
            const token = getToken();
            if (!options.headers) options.headers = {};
            
            if (url.includes('/api/users/login')) {
                return nativeFetch(url, options);
            }

            if (token) {
                options.headers['Authorization'] = `Bearer ${token}`;
            }

            const res = await nativeFetch(url, options);

            if (res.status === 401 || res.status === 403) {
                console.error("⛔ Interceptor JWT disparado: Sesión Anulada.");
                global.logout();
                throw new Error("HTTP 401: Sin autorización.");
            }
            return res;
        }

        function logout() {
            localStorage.removeItem('access_token');
            global.currentUserContext = null;
            if(global.showLogin) global.showLogin();
        }

        // Expose
        global.getToken = getToken;
        global.setToken = setToken;
        global.parseJwt = parseJwt;
        global.authFetch = authFetch;
        global.logout = logout;
    })(window);

    // ==========================================
    // MÓDULO 3: APP CORE & NAVEGACIÓN
    // ==========================================
    (function(global) {
        global.currentUserContext = null;

        async function initApp() {
            const token = global.getToken();
            if (!token) {
                showLogin();
                return;
            }

            try {
                const res = await global.authFetch(global.CONFIG.BASE_URL + '/api/users/me');
                if (!res.ok) throw new Error("Token Inválido");
                
                global.currentUserContext = await res.json();
                
                document.getElementById('current-username-display').innerText = global.currentUserContext.username;
                console.log("✅ Sesión validada. Bienvenid@ " + global.currentUserContext.username);
                
                showApp();
                if(global.applyRBAC) global.applyRBAC();
                
            } catch (e) {
                console.warn("⚠️ Fallo en InitApp:", e.message);
                global.logout();
            }
        }

        function showLogin() {
            const app = document.getElementById('app-container');
            const login = document.getElementById('login-container');
            if(app) app.style.display = 'none';
            if(login) login.style.display = 'flex';
        }

        function showApp() {
            const app = document.getElementById('app-container');
            const login = document.getElementById('login-container');
            if(login) login.style.display = 'none';
            if(app) app.style.display = 'flex';
        }

        function nav(sectionId) {
            document.querySelectorAll('.nav-btn').forEach(btn => {
                btn.classList.remove('bg-indigo-600', 'text-white', 'shadow-md', 'shadow-indigo-900/50');
                if (!btn.classList.contains('text-slate-300')) {
                    btn.classList.add('text-slate-300', 'hover:bg-slate-800');
                }
            });

            const activeBtn = Array.from(document.querySelectorAll('.nav-btn')).find(b => b.getAttribute('onclick') === "nav('"+sectionId+"')");
            if (activeBtn) {
                activeBtn.classList.add('bg-indigo-600', 'text-white', 'shadow-md', 'shadow-indigo-900/50');
                activeBtn.classList.remove('text-slate-300', 'hover:bg-slate-800');
            }

            document.querySelectorAll('.section').forEach(el => el.classList.remove('active'));
            const targetSection = document.getElementById(sectionId);
            if (targetSection) {
                targetSection.classList.add('active');
                if (sectionId === 'usuarios-module' && global.loadUsuarios) global.loadUsuarios();
            }
        }

        // Expose
        global.initApp = initApp;
        global.showLogin = showLogin;
        global.showApp = showApp;
        global.nav = nav;
    })(window);

    // ==========================================
    // MÓDULO 4: RBAC SECURITY
    // ==========================================
    (function(global) {
        function applyRBAC() {
            if (!global.currentUserContext) return;
            const isManager = global.currentUserContext.roles.some(r => r.name === 'SISTEMAS' || r.name === 'SUPERADMIN');
            console.log("🛂 RBAC Manage Users:", isManager);
            
            const btn = document.getElementById('nav-btn-usuarios');
            if(btn) {
                if (isManager) {
                    btn.style.display = 'flex';
                } else {
                    btn.style.display = 'none';
                    const usersMod = document.getElementById('usuarios-module');
                    if (usersMod && usersMod.classList.contains('active')) {
                        global.nav('upload');
                    }
                }
            }
        }

        global.applyRBAC = applyRBAC;
    })(window);

    // ==========================================
    // MÓDULO 5: LOGIN UI (Encapsulado total)
    // ==========================================
    (function(global) {
        document.addEventListener('DOMContentLoaded', () => {
            const form = document.getElementById('login-form');
            if(!form) return;

            form.addEventListener('submit', async (e) => {
                e.preventDefault();
                const payload = new URLSearchParams();
                payload.append('username', document.getElementById('login-username').value.trim());
                payload.append('password', document.getElementById('login-password').value);
                
                const btn = document.getElementById('login-btn');
                const err = document.getElementById('login-error');
                err.classList.add('hidden');
                btn.disabled = true;
                btn.innerHTML = 'Validando <i class="fa-solid fa-spinner fa-spin"></i>';

                try {
                    const res = await global.authFetch(global.CONFIG.BASE_URL + '/api/users/login', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                        body: payload
                    });

                    const data = await res.json();
                    if (!res.ok) throw new Error(data.detail || 'Fallo de autenticación.');
                    
                    global.setToken(data.access_token);
                    await global.initApp();
                    global.nav('upload'); 

                } catch(e) {
                    err.innerText = e.message;
                    err.classList.remove('hidden');
                } finally {
                    btn.disabled = false;
                    btn.innerHTML = 'Ingresar <i class="fa-solid fa-arrow-right"></i>';
                }
            });
        });
    })(window);

    // ==========================================
    // MÓDULO 6: GESTIÓN DE SISTEMA (USERS)
    // ==========================================
    (function(global) {
        let globalRoles = [];

        async function loadSysRoles() {
            if(globalRoles.length > 0) return;
            const res = await global.authFetch(global.CONFIG.BASE_URL + '/api/users/roles');
            globalRoles = await res.json();
        }

        async function loadUsuarios() {
            const tbody = document.getElementById('usuarios-tbody');
            if(!tbody) return;
            tbody.innerHTML = '<tr><td colspan="5" class="px-5 py-8 text-center text-indigo-500"><i class="fa-solid fa-spinner fa-spin mr-2"></i>Cargando...</td></tr>';
            
            await loadSysRoles();

            try {
                const res = await global.authFetch(global.CONFIG.BASE_URL + '/api/users');
                const list = await res.json();
                tbody.innerHTML = '';
                
                list.forEach(u => {
                    const statusUI = u.is_active 
                        ? `<span class="bg-emerald-100 text-emerald-700 text-[10px] px-2 py-1 rounded-full font-black">ACTIVO</span>`
                        : `<span class="bg-rose-100 text-rose-700 text-[10px] px-2 py-1 rounded-full font-black">BLOQUEADO</span>`;
                    
                    const rolesUI = u.roles.map(r => `<span class="text-[10px] border border-slate-300 text-slate-600 bg-white px-2 py-0.5 rounded-lg font-bold">${r.name}</span>`).join(' ') || '<em class="text-xs text-slate-400">Sin roles</em>';

                    tbody.innerHTML += `
                    <tr class="hover:bg-slate-50 transition-colors">
                        <td class="px-5 py-4">
                            <p class="font-bold text-slate-800">${u.apellidos}, ${u.nombres}</p>
                            <p class="text-xs text-slate-500">${u.area || '-'}</p>
                        </td>
                        <td class="px-5 py-4 font-medium text-slate-700">${u.username}</td>
                        <td class="px-5 py-4 flex gap-1 flex-wrap">${rolesUI}</td>
                        <td class="px-5 py-4">${statusUI}</td>
                        <td class="px-5 py-4 text-right">
                            <button onclick='window.editUsuario(${JSON.stringify(u).replace(/'/g, "&#39;")})' class="bg-indigo-50 text-indigo-700 hover:bg-indigo-100 font-bold px-3 py-1.5 rounded-lg text-xs mr-1"><i class="fa-solid fa-pen"></i> Editar</button>
                            ${u.is_active ? `<button onclick="window.deleteUsuario(${u.id})" class="bg-rose-50 text-rose-700 hover:bg-rose-100 font-bold px-3 py-1.5 rounded-lg text-xs"><i class="fa-solid fa-ban"></i> Desactivar</button>` : ''}
                        </td>
                    </tr>
                    `;
                });
            } catch (e) {
                tbody.innerHTML = `<tr><td colspan="5" class="px-5 py-8 text-center text-rose-500 font-bold">Error: ${e.message}</td></tr>`;
            }
        }

        function buildRolesCheckboxes(activeIds = []) {
            const wrapper = document.getElementById('usr-roles-container');
            if(!wrapper) return;
            wrapper.innerHTML = '';
            globalRoles.forEach(r => {
                const checked = activeIds.includes(r.id) ? 'checked' : '';
                wrapper.innerHTML += `
                    <label class="flex items-center gap-2 cursor-pointer bg-slate-50 p-2 rounded border border-slate-200">
                        <input type="checkbox" name="rol_assign" value="${r.id}" ${checked}>
                        <span class="text-xs font-bold text-slate-700">${r.name}</span>
                    </label>
                `;
            });
        }

        function openUsuarioModal() {
            document.getElementById('usuario-form').reset();
            document.getElementById('usr-id').value = '';
            document.getElementById('usuario-modal-title').innerText = 'Nuevo Usuario';
            document.getElementById('usr-password').required = true;
            document.getElementById('usr-pwd-container').style.display = 'block';
            
            buildRolesCheckboxes();
            document.getElementById('usuario-modal').classList.remove('hidden');
        }

        function editUsuario(u) {
            document.getElementById('usuario-form').reset();
            document.getElementById('usr-id').value = u.id;
            document.getElementById('usr-nombres').value = u.nombres;
            document.getElementById('usr-apellidos').value = u.apellidos;
            document.getElementById('usr-email').value = u.username;
            document.getElementById('usr-area').value = u.area || '';
            
            document.getElementById('usuario-modal-title').innerText = 'Modificar Acceso';
            document.getElementById('usr-password').required = false;
            document.getElementById('usr-pwd-container').style.display = 'none'; 
            
            buildRolesCheckboxes(u.roles.map(r => r.id));
            document.getElementById('usuario-modal').classList.remove('hidden');
        }

        function closeUsuarioModal() {
            document.getElementById('usuario-modal').classList.add('hidden');
        }

        document.addEventListener('DOMContentLoaded', () => {
            document.getElementById('usuario-form')?.addEventListener('submit', async (e) => {
                e.preventDefault();
                const btn = document.getElementById('usr-save-btn');
                btn.disabled = true;

                const id = document.getElementById('usr-id').value;
                const payload = {
                    username: document.getElementById('usr-email').value,
                    nombres: document.getElementById('usr-nombres').value,
                    apellidos: document.getElementById('usr-apellidos').value,
                    area: document.getElementById('usr-area').value
                };
                if(!id) payload.password = document.getElementById('usr-password').value;

                try {
                    let targetId = id;
                    if(id) {
                        await global.authFetch(global.CONFIG.BASE_URL + '/api/users/' + id, {
                            method: 'PUT', headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify(payload)
                        });
                    } else {
                        const res = await global.authFetch(global.CONFIG.BASE_URL + '/api/users', {
                            method: 'POST', headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify(payload)
                        });
                        const created = await res.json();
                        targetId = created.id;
                    }

                    const roleIds = Array.from(document.querySelectorAll('input[name="rol_assign"]:checked')).map(cb => parseInt(cb.value));
                    await global.authFetch(global.CONFIG.BASE_URL + `/api/users/${targetId}/roles`, {
                        method: 'POST', headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({ role_ids: roleIds })
                    });

                    closeUsuarioModal();
                    loadUsuarios();
                    console.log("✅ Usuario guardado con éxito");
                } catch(e) {
                    alert("Error guardando usuario: " + e.message);
                } finally {
                    btn.disabled = false;
                }
            });
        });

        async function deleteUsuario(id) {
            if(!confirm('¿Desactivar y bloquear el acceso de este usuario?')) return;
            try {
                await global.authFetch(global.CONFIG.BASE_URL + '/api/users/' + id, { method: 'DELETE' });
                loadUsuarios();
            } catch (e) {
                alert('No se pudo desactivar: ' + e.message);
            }
        }

        // Expose Functions
        global.loadUsuarios = loadUsuarios;
        global.openUsuarioModal = openUsuarioModal;
        global.editUsuario = editUsuario;
        global.closeUsuarioModal = closeUsuarioModal;
        global.deleteUsuario = deleteUsuario;

    })(window);

"""

injection_marker = "// ==========================================\n        // 1. JWT & SECURITY GLOBAL"
legacy_code_end = js_content.find(injection_marker)
if legacy_code_end != -1:
    legacy_code = js_content[:legacy_code_end]
else:
    legacy_code = ""

funcs = re.findall(r'^(?:async\s+)?function\s+([A-Za-z0-9_]+)\(', legacy_code, re.MULTILINE)
all_funcs = set(re.findall(r'function\s+([A-Za-z0-9_]+)\s*\(', legacy_code))
excludes = ('authFetch', 'initApp', 'logout', 'showLogin', 'showApp', 'getToken', 'setToken', 'parseJwt', 'nav', 'applyRBAC', 'toggleConfigMenu')
exports = "".join(["        global." + fn + " = " + fn + ";\n" for fn in all_funcs if fn not in excludes])

legacy_js_structure = """
    // ==========================================
    // MÓDULO 7: LEGACY BUSINESS LOGIC
    // ==========================================
    (function(global) {
""" + legacy_code + """
        // --- GLOBAL EXPORTS FOR LEGACY ACROSS HTML ---
""" + exports + """
        if(typeof toggleConfigMenu !== 'undefined') global.toggleConfigMenu = toggleConfigMenu;
    })(window);
"""

init_block = """
    // ==========================================
    // INITIALIZATION BOOTSTRAP
    // ==========================================
    document.addEventListener('DOMContentLoaded', () => {
        if(window.initApp) window.initApp();
        if(window.setInitialDates) window.setInitialDates();
        if(window.loadRptCatalogs) window.loadRptCatalogs();
        if(window.loadObsLogs) window.loadObsLogs();
    });
"""

final_js = new_js_structure + legacy_js_structure + init_block

html = html[:start_idx+8] + "\n" + final_js + "\n    " + html[end_idx:]

with open(path, "w", encoding="utf-8") as f:
    f.write(html)
print("Modular Refactoring Completed!")
