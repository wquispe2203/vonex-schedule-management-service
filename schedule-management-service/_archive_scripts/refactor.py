import os
import re

file_path = r"d:\Desktop\MOD HOR\prototype\index.html"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Replace fetch
content = re.sub(r'\bfetch\(', 'authFetch(', content)

# But wait, authFetch doesn't exist yet in the file, and we need to avoid replacing fetch inside authFetch itself!
# We will inject authFetch later and it will just use window.fetch or standard fetch intentionally.

# Let's wrap the app container.
# Find the start of the body content
body_start = content.find('<body')
body_end = content.find('>', body_start) + 1

# Inject Login HTML right after body opens
login_html = """
    <!-- ==============================================
         MÓDULO DE LOGIN
    =============================================== -->
    <div id="login-container" class="fixed inset-0 bg-slate-900 z-[9999] flex items-center justify-center">
        <div class="bg-white p-8 rounded-2xl shadow-2xl w-full max-w-sm animate-in zoom-in duration-300">
            <div class="text-center mb-8">
                <i class="fa-solid fa-shield-halved text-4xl text-indigo-600 mb-3 block"></i>
                <h2 class="text-2xl font-black text-slate-900 tracking-tight">Acceso Restringido</h2>
                <p class="text-slate-500 text-sm mt-1">Ingresa con tu cuenta @vonex.edu.pe</p>
            </div>
            <form id="login-form" autocomplete="off">
                <div class="mb-4">
                    <label class="block text-xs font-black text-slate-500 mb-2 uppercase tracking-wide">Usuario Institucional</label>
                    <input type="email" id="login-username" required class="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 font-medium text-slate-700" placeholder="ejemplo@vonex.edu.pe">
                </div>
                <div class="mb-6">
                    <label class="block text-xs font-black text-slate-500 mb-2 uppercase tracking-wide">Contraseña</label>
                    <input type="password" id="login-password" required class="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 font-medium text-slate-700" placeholder="••••••••">
                </div>
                <div id="login-error" class="hidden mb-4 bg-rose-50 border border-rose-200 text-rose-700 text-xs font-bold p-3 rounded-lg text-center"></div>
                <button type="submit" id="login-btn" class="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-black py-3.5 rounded-xl shadow-lg transition-all flex justify-center items-center gap-2">
                    Ingresar <i class="fa-solid fa-arrow-right"></i>
                </button>
            </form>
        </div>
    </div>
    
    <!-- ==============================================
         APP PRINCIPAL (OCULTA HASTA LOGIN)
    =============================================== -->
    <div id="app-container" class="flex w-full h-full" style="display: none;">
"""

if "id=\"login-container\"" not in content:
    content = content[:body_end] + "\n" + login_html + content[body_end:]
    # And close the app-container at the end before </body>
    content = content.replace("</body>", "</div>\n</body>")


# Find the sidebar to inject the User module button & logout
sidebar_marker = '<!-- Menú Desplegable Configuración -->'
user_nav_btn = """
                <!-- Módulo Usuarios -->
                <button id="nav-btn-usuarios" onclick="nav('usuarios-module')" style="display: none;"
                    class="nav-btn w-full flex items-center gap-3 px-4 py-3 hover:bg-slate-800 rounded-lg text-left transition-all text-slate-300 hover:text-white mt-1">
                    <i class="fa-solid fa-user-shield w-5 text-center"></i> Control de Usuarios
                </button>
"""
if "nav-btn-usuarios" not in content:
    content = content.replace(sidebar_marker, user_nav_btn + "\n" + sidebar_marker)

# Inject logout button in the top of the sidebar or profile section
profile_section = '<p class="text-sm font-bold text-slate-200">Admin_1</p>'
logout_html = '<p class="text-sm font-bold text-slate-200" id="current-username-display">Usuario</p><button onclick="logout()" class="text-xs text-rose-400 hover:text-rose-300 underline font-black">Cerrar Sesión</button>'
if "Cerrar Sesión" not in content:
    content = content.replace(profile_section, logout_html)


# Inject the Usuarios Module HTML into the main content
main_end_marker = '</main>'
usuarios_module_html = """
        <!-- =================================================================
             MÓDULO DE USUARIOS
        ================================================================== -->
        <div id="usuarios-module" class="section max-w-7xl mx-auto">
            <div class="flex justify-between items-center mb-8">
                <div>
                    <h2 class="text-3xl font-extrabold text-slate-900 tracking-tight">Control de Usuarios y Roles</h2>
                    <p class="text-slate-500 mt-2">Gestión centralizada del sistema de permisos (RBAC).</p>
                </div>
                <button onclick="openUsuarioModal()"
                    class="bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-2.5 px-6 rounded-xl shadow-md transition-all flex items-center gap-2">
                    <i class="fa-solid fa-user-plus"></i> Nuevo Usuario
                </button>
            </div>

            <div class="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
                <div class="overflow-x-auto">
                    <table class="w-full text-sm text-left">
                        <thead class="bg-slate-50 border-b border-slate-200">
                            <tr>
                                <th class="px-5 py-4 text-xs font-black text-slate-500 uppercase tracking-tighter">Colaborador</th>
                                <th class="px-5 py-4 text-xs font-black text-slate-500 uppercase tracking-tighter">Cuenta / Email</th>
                                <th class="px-5 py-4 text-xs font-black text-slate-500 uppercase tracking-tighter">Roles de Seguridad</th>
                                <th class="px-5 py-4 text-xs font-black text-slate-500 uppercase tracking-tighter">Estado</th>
                                <th class="px-5 py-4 text-xs font-black text-slate-500 uppercase tracking-tighter text-right">Acciones</th>
                            </tr>
                        </thead>
                        <tbody id="usuarios-tbody" class="divide-y divide-slate-100">
                            <tr><td colspan="5" class="px-5 py-12 text-center text-slate-400"><i class="fa-solid fa-spinner fa-spin text-2xl mb-3 block text-indigo-500"></i>Cargando matriz...</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Modal Nuevo/Editar Usuario -->
            <div id="usuario-modal" class="hidden fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm">
                <div class="bg-white rounded-2xl shadow-2xl max-w-lg w-full overflow-hidden flex flex-col max-h-[90vh]">
                    <div class="p-6 border-b border-slate-100 flex justify-between items-center bg-slate-50">
                        <h3 id="usuario-modal-title" class="text-xl font-bold text-slate-900">Configurar Acceso</h3>
                        <button onclick="closeUsuarioModal()" class="text-slate-400 hover:text-slate-600"><i class="fa-solid fa-xmark text-xl"></i></button>
                    </div>
                    <form id="usuario-form" class="p-6 overflow-y-auto">
                        <input type="hidden" id="usr-id">
                        <div class="grid grid-cols-2 gap-4 mb-4">
                            <div>
                                <label class="block text-xs font-black text-slate-500 mb-1 uppercase tracking-wide">Nombres</label>
                                <input type="text" id="usr-nombres" required class="w-full px-3 py-2.5 bg-slate-50 border border-slate-200 rounded-lg text-sm text-slate-700 focus:border-indigo-500">
                            </div>
                            <div>
                                <label class="block text-xs font-black text-slate-500 mb-1 uppercase tracking-wide">Apellidos</label>
                                <input type="text" id="usr-apellidos" required class="w-full px-3 py-2.5 bg-slate-50 border border-slate-200 rounded-lg text-sm text-slate-700 focus:border-indigo-500">
                            </div>
                        </div>
                        <div class="mb-4">
                            <label class="block text-xs font-black text-slate-500 mb-1 uppercase tracking-wide">Correo Institucional</label>
                            <input type="email" id="usr-email" placeholder="@vonex.edu.pe" required pattern=".*@vonex\.edu\.pe" class="w-full px-3 py-2.5 bg-slate-50 border border-slate-200 rounded-lg text-sm text-slate-700 focus:border-indigo-500">
                        </div>
                        <div class="mb-4" id="usr-pwd-container">
                            <label class="block text-xs font-black text-slate-500 mb-1 uppercase tracking-wide">Contraseña Provisional</label>
                            <input type="password" id="usr-password" minlength="6" class="w-full px-3 py-2.5 bg-slate-50 border border-slate-200 rounded-lg text-sm text-slate-700 focus:border-indigo-500">
                            <p class="text-[10px] text-slate-400 mt-1">Requerido para cuentas nuevas (mín 6 caracts).</p>
                        </div>
                        <div class="mb-6">
                            <label class="block text-xs font-black text-slate-500 mb-1 uppercase tracking-wide">Área Operativa</label>
                            <input type="text" id="usr-area" class="w-full px-3 py-2.5 bg-slate-50 border border-slate-200 rounded-lg text-sm text-slate-700 focus:border-indigo-500">
                        </div>
                        
                        <!-- Checkboxes Roles -->
                        <div class="border-t border-slate-200 pt-4">
                            <label class="block text-xs font-black text-slate-800 mb-3 uppercase tracking-wider">Asignación de Roles</label>
                            <div id="usr-roles-container" class="grid grid-cols-2 gap-3">
                                <!-- render dynamically -->
                            </div>
                        </div>
                        <div class="mt-8 flex gap-3">
                            <button type="submit" id="usr-save-btn" class="flex-1 bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-3 rounded-xl transition-all">Guardar Credenciales</button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
"""
if "id=\"usuarios-module\"" not in content:
    content = content.replace(main_end_marker, usuarios_module_html + "\n" + main_end_marker)


# Inject the JS 
js_logic = """
        // ==========================================
        // 1. JWT & SECURITY GLOBAL
        // ==========================================
        const BASE_URL = 'http://localhost:8000';
        let currentUserContext = null;

        function getToken() { return localStorage.getItem('access_token'); }
        function setToken(token) { localStorage.setItem('access_token', token); }

        function parseJwt(token) {
            try {
                return JSON.parse(atob(token.split('.')[1]));
            } catch (e) {
                return {};
            }
        }

        // IMPORTANT OVERRIDE OF fetch TO PREVENT INFINITE RECURSION
        // We will call the native windw.fetch inside authFetch
        const nativeFetch = window.fetch;

        async function authFetch(url, options = {}) {
            const token = getToken();
            if (!options.headers) options.headers = {};
            
            // Si la URL es login, no usamos token
            if (url.includes('/api/users/login')) {
                return nativeFetch(url, options);
            }

            if (token) {
                options.headers['Authorization'] = `Bearer ${token}`; // El bracket interpolation causaba error de syntax en regex
            }

            const res = await nativeFetch(url, options);

            if (res.status === 401 || res.status === 403) {
                console.error("⛔ Interceptor JWT disparado: Sesión Anulada.");
                logout();
                throw new Error("HTTP 401: Sin autorización.");
            }
            
            return res;
        }

        async function initApp() {
            const token = getToken();
            if (!token) {
                console.log("No hay token, abriendo login.");
                showLogin();
                return;
            }

            try {
                const res = await authFetch(BASE_URL + '/api/users/me');
                if (!res.ok) throw new Error("Token Inválido");
                
                currentUserContext = await res.json();
                
                document.getElementById('current-username-display').innerText = currentUserContext.username;
                console.log("✅ Sesión validada. Bienvenid@ " + currentUserContext.username);
                
                showApp();
                applyRBAC();
                
            } catch (e) {
                console.warn("⚠️ Fallo en InitApp:", e.message);
                logout();
            }
        }

        function showLogin() {
            document.getElementById('app-container').style.display = 'none';
            document.getElementById('login-container').style.display = 'flex';
        }

        function showApp() {
            document.getElementById('login-container').style.display = 'none';
            document.getElementById('app-container').style.display = 'flex'; // Usan flex en el DOM
        }

        function logout() {
            localStorage.removeItem('access_token');
            currentUserContext = null;
            showLogin();
        }

        function applyRBAC() {
            if (!currentUserContext) return;
            // Verificar si tiene SISTEMAS o SUPERADMIN
            const isManager = currentUserContext.roles.some(r => r.name === 'SISTEMAS' || r.name === 'SUPERADMIN');
            console.log("🛂 RBAC Manage Users:", isManager);
            
            const btn = document.getElementById('nav-btn-usuarios');
            if (isManager) {
                btn.style.display = 'flex';
            } else {
                btn.style.display = 'none';
                if (document.getElementById('usuarios-module').classList.contains('active')) {
                    nav('upload');
                }
            }
        }

        document.getElementById('login-form')?.addEventListener('submit', async (e) => {
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
                const res = await authFetch(BASE_URL + '/api/users/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                    body: payload
                });

                const data = await res.json();
                if (!res.ok) throw new Error(data.detail || 'Fallo de autenticación.');
                
                setToken(data.access_token);
                await initApp();
                nav('upload'); // Go to default module

            } catch(e) {
                err.innerText = e.message;
                err.classList.remove('hidden');
            } finally {
                btn.disabled = false;
                btn.innerHTML = 'Ingresar <i class="fa-solid fa-arrow-right"></i>';
            }
        });

        // ==========================================
        // 2. MÓDULO DE USUARIOS (FRONTEND LOGIC)
        // ==========================================
        let globalRoles = [];

        async function loadSysRoles() {
            if(globalRoles.length > 0) return;
            const res = await authFetch(BASE_URL + '/api/users/roles');
            globalRoles = await res.json();
        }

        async function loadUsuarios() {
            const tbody = document.getElementById('usuarios-tbody');
            tbody.innerHTML = '<tr><td colspan="5" class="px-5 py-8 text-center text-indigo-500"><i class="fa-solid fa-spinner fa-spin mr-2"></i>Cargando...</td></tr>';
            
            await loadSysRoles();

            try {
                const res = await authFetch(BASE_URL + '/api/users');
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
                            <button onclick='editUsuario(${JSON.stringify(u)})' class="bg-indigo-50 text-indigo-700 hover:bg-indigo-100 font-bold px-3 py-1.5 rounded-lg text-xs mr-1"><i class="fa-solid fa-pen"></i> Editar</button>
                            ${u.is_active ? `<button onclick="deleteUsuario(${u.id})" class="bg-rose-50 text-rose-700 hover:bg-rose-100 font-bold px-3 py-1.5 rounded-lg text-xs"><i class="fa-solid fa-ban"></i> Desactivar</button>` : ''}
                        </td>
                    </tr>
                    `;
                });
            } catch (e) {
                tbody.innerHTML = `<tr><td colspan="5" class="px-5 py-8 text-center text-rose-500 font-bold">Error: ${e.message}</td></tr>`;
            }
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
            document.getElementById('usr-pwd-container').style.display = 'none'; // ocultar en edición
            
            buildRolesCheckboxes(u.roles.map(r => r.id));
            document.getElementById('usuario-modal').classList.remove('hidden');
        }

        function closeUsuarioModal() {
            document.getElementById('usuario-modal').classList.add('hidden');
        }

        function buildRolesCheckboxes(activeIds = []) {
            const wrapper = document.getElementById('usr-roles-container');
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
                    await authFetch(BASE_URL + '/api/users/' + id, {
                        method: 'PUT', headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify(payload)
                    });
                } else {
                    const res = await authFetch(BASE_URL + '/api/users', {
                        method: 'POST', headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify(payload)
                    });
                    const created = await res.json();
                    targetId = created.id;
                }

                // Asignar roles elegidos
                const roleIds = Array.from(document.querySelectorAll('input[name="rol_assign"]:checked')).map(cb => parseInt(cb.value));
                await authFetch(BASE_URL + `/api/users/${targetId}/roles`, {
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

        async function deleteUsuario(id) {
            if(!confirm('¿Desactivar y bloquear el acceso de este usuario?')) return;
            try {
                await authFetch(BASE_URL + '/api/users/' + id, { method: 'DELETE' });
                loadUsuarios();
            } catch (e) {
                alert('No se pudo desactivar: ' + e.message);
            }
        }
"""
if "function authFetch" not in content:
    content = content.replace("document.addEventListener('DOMContentLoaded', () => {", js_logic + "\n        document.addEventListener('DOMContentLoaded', () => {\n            initApp();")

    # In my JS i also hooked the nav logic to call loadUsuarios
    nav_fn = """
        function nav(sectionId) {
            // Eliminar active de todos los nav-btn salvo config
            document.querySelectorAll('.nav-btn').forEach(btn => {
                btn.classList.remove('bg-indigo-600', 'text-white', 'shadow-md', 'shadow-indigo-900/50');
                if (!btn.classList.contains('text-slate-300')) {
                    btn.classList.add('text-slate-300', 'hover:bg-slate-800');
                }
            });

            // Resaltar el seleccionado
            const activeBtn = Array.from(document.querySelectorAll('.nav-btn')).find(b => b.getAttribute('onclick') === "nav('"+sectionId+"')");
            if (activeBtn) {
                activeBtn.classList.add('bg-indigo-600', 'text-white', 'shadow-md', 'shadow-indigo-900/50');
                activeBtn.classList.remove('text-slate-300', 'hover:bg-slate-800');
            }

            document.querySelectorAll('.section').forEach(el => el.classList.remove('active'));
            const targetSection = document.getElementById(sectionId);
            if (targetSection) {
                targetSection.classList.add('active');
                if (sectionId === 'usuarios-module') loadUsuarios();
            }
        }
"""
    # Replace the existing nav function
    content = re.sub(r'function nav\(sectionId\)\s*{[\s\S]*?(?=\n\s*function )', nav_fn, content, count=1)


with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("done")
