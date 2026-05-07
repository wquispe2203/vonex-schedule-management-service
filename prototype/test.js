

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
                
                // Cargas Diferidas, solo si hay sesión
                if(typeof setInitialDates !== 'undefined') setInitialDates();
                else if(global.setInitialDates) global.setInitialDates();
                
                if(typeof loadRptCatalogs !== 'undefined') loadRptCatalogs();
                else if(global.loadRptCatalogs) global.loadRptCatalogs();
                
                if(typeof loadObsLogs !== 'undefined') loadObsLogs();
                else if(global.loadObsLogs) global.loadObsLogs();

                
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


    // ==========================================
    // MÓDULO 7: LEGACY BUSINESS LOGIC
    // ==========================================
    (function(global) {

        // --- Constants & Global State ---
        const API_BASE_URL = 'http://localhost:8000';

        // Navigation Logic
        
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


        function renderConfigTable(type) {
            const tbody = document.getElementById(`${type}-config-body`);
            tbody.innerHTML = '';
            const configs = currentConfigs[type];

            if (configs.length === 0) {
                tbody.innerHTML = '<tr><td colspan="5" class="py-12 text-center text-slate-400 italic">No hay registros configurados</td></tr>';
                return;
            }

            configs.forEach(c => {
                const tr = document.createElement('tr');
                tr.className = "hover:bg-slate-50 transition-colors border-b border-slate-50 text-slate-700 not-italic";

                // Calculate duration for display
                const dur = calculateDurationMinutes(c.start_time, c.end_time);

                tr.innerHTML = `
                    <td class="px-6 py-4 font-bold text-slate-800">${c.description}</td>
                    <td class="px-6 py-4 font-mono text-sm">${c.start_time.substring(0, 5)}</td>
                    <td class="px-6 py-4 font-mono text-sm">${c.end_time.substring(0, 5)}</td>
                    <td class="px-6 py-4 text-center">
                        <span class="bg-indigo-50 text-indigo-700 px-3 py-1 rounded-full text-xs font-black">${dur} min</span>
                    </td>
                    <td class="px-6 py-4 text-right space-x-2">
                        <button onclick="editConfig('${type}', ${c.id})" class="text-indigo-600 hover:text-indigo-800 p-2"><i class="fa-solid fa-pen-to-square"></i></button>
                        <button onclick="deleteConfig('${type}', ${c.id})" class="text-rose-600 hover:text-rose-800 p-2"><i class="fa-solid fa-trash"></i></button>
                    </td>
                `;
                tbody.appendChild(tr);
            });
        }

        function calculateDurationMinutes(start, end) {
            if (!start || !end) return 0;
            const [h1, m1] = start.split(':').map(Number);
            const [h2, m2] = end.split(':').map(Number);
            return (h2 * 60 + m2) - (h1 * 60 + m1);
        }

        function calculateDuration() {
            const start = document.getElementById('config-start').value;
            const end = document.getElementById('config-end').value;
            if (start && end) {
                const diff = calculateDurationMinutes(start, end);
                document.getElementById('config-duration').innerText = `${diff} min`;
                if (diff <= 0) document.getElementById('config-duration').classList.add('text-rose-600');
                else document.getElementById('config-duration').classList.remove('text-rose-600');
            }
        }

        function openConfigModal(type, id = null) {
            const isEdit = id !== null;
            document.getElementById('config-type').value = type;
            document.getElementById('config-id').value = id || '';
            document.getElementById('config-modal-title').innerText = `${isEdit ? 'Editar' : 'Agregar'} ${type === 'recess' ? 'Receso' : 'Almuerzo'}`;

            if (isEdit) {
                const config = currentConfigs[type].find(c => c.id === id);
                document.getElementById('config-name').value = config.description;
                document.getElementById('config-start').value = config.start_time.substring(0, 5);
                document.getElementById('config-end').value = config.end_time.substring(0, 5);
            } else {
                document.getElementById('config-name').value = '';
                document.getElementById('config-start').value = '';
                document.getElementById('config-end').value = '';
            }

            calculateDuration();
            document.getElementById('config-modal').classList.remove('hidden');
        }

        function closeConfigModal() {
            document.getElementById('config-modal').classList.add('hidden');
        }

        async function saveConfig() {
            const type = document.getElementById('config-type').value;
            const id = document.getElementById('config-id').value;
            const payload = {
                description: document.getElementById('config-name').value,
                start_time: document.getElementById('config-start').value,
                end_time: document.getElementById('config-end').value
            };

            if (!payload.description || !payload.start_time || !payload.end_time) {
                alert("Complete todos los campos.");
                return;
            }

            if (calculateDurationMinutes(payload.start_time, payload.end_time) <= 0) {
                alert("La hora de fin debe ser posterior a la de inicio.");
                return;
            }

            const endpoint = type === 'recess' ? 'recesos' : 'almuerzos';
            const method = id ? 'PUT' : 'POST';
            const url = id ? `${API_BASE_URL}/api/config/${endpoint}/${id}` : `${API_BASE_URL}/api/config/${endpoint}`;

            try {
                const res = await authFetch(url, {
                    method: method,
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });

                if (!res.ok) {
                    const err = await res.json();
                    console.error("Error saving:", err);
                    alert("Error al guardar: " + (typeof err.detail === 'string' ? err.detail : JSON.stringify(err.detail)));
                    return;
                }

                const data = await res.json();
                if (data.success) {
                    closeConfigModal();
                    loadConfig(type);
                    alert("Configuración guardada con éxito");
                }
            } catch (e) {
                console.error("Error saving config:", e);
                alert("Error de conexión: " + e.message);
            }
        }

        async function deleteConfig(type, id) {
            if (!confirm("¿Está seguro de eliminar este registro?")) return;
            const endpoint = type === 'recess' ? 'recesos' : 'almuerzos';
            try {
                const res = await authFetch(`${API_BASE_URL}/api/config/${endpoint}/${id}`, { method: 'DELETE' });
                const data = await res.json();
                if (data.success) loadConfig(type);
            } catch (e) {
                console.error("Error deleting config:", e);
            }
        }

        function editConfig(type, id) {
            openConfigModal(type, id);
        }

        // Upload Logic
        let currentHistoryPage = 1;

        async function loadUploadHistory(page = 1) {
            currentHistoryPage = page;
            const tbody = document.getElementById('upload-history-body');
            const prevBtn = document.getElementById('prev-page-btn');
            const nextBtn = document.getElementById('next-page-btn');
            const pageIndicator = document.getElementById('page-indicator');
            const totalCount = document.getElementById('history-total');

            try {
                const res = await authFetch(`${API_BASE_URL}/api/schedule/xml-uploads?page=${page}&limit=5`);
                const data = await res.json();
                if (data.success) {
                    tbody.innerHTML = '';
                    if (data.data.length === 0) {
                        tbody.innerHTML = '<tr><td colspan="4" class="px-4 py-8 text-center text-slate-400">No hay registros de subida aún.</td></tr>';
                        pageIndicator.innerText = `Página 1 de 1`;
                        totalCount.innerText = "0";
                        return;
                    }

                    // Update metadata
                    totalCount.innerText = data.total_records;
                    pageIndicator.innerText = `Página ${data.current_page} de ${data.total_pages}`;
                    prevBtn.disabled = data.current_page <= 1;
                    nextBtn.disabled = data.current_page >= data.total_pages;

                    data.data.forEach(u => {
                        const tr = document.createElement('tr');
                        tr.className = "hover:bg-slate-50 transition-colors";
                        tr.innerHTML = `
                            <td class="px-4 py-3 font-medium text-slate-700">${u.created_at}</td>
                            <td class="px-4 py-3 text-slate-600">${u.filename}</td>
                            <td class="px-4 py-3 text-slate-600">${u.start_date} a ${u.end_date}</td>
                            <td class="px-4 py-3 text-center">
                                ${u.is_force_overwrite
                                ? '<span class="bg-amber-100 text-amber-700 text-[10px] font-black px-2 py-0.5 rounded-full uppercase tracking-tighter">SÍ</span>'
                                : '<span class="bg-slate-100 text-slate-500 text-[10px] font-black px-2 py-0.5 rounded-full uppercase tracking-tighter">NO</span>'}
                            </td>
                            <td class="px-4 py-3 text-center">
                                <button onclick="viewUploadReport('${u.id}')" class="text-indigo-600 hover:text-indigo-900 bg-indigo-50 hover:bg-indigo-100 px-2 py-1 rounded text-xs font-bold transition-colors">
                                    <i class="fa-solid fa-chart-pie mr-1"></i> Reporte
                                </button>
                            </td>
                        `;
                        tbody.appendChild(tr);
                    });
                }
            } catch (e) {
                console.error("Error loading history:", e);
                tbody.innerHTML = '<tr><td colspan="4" class="px-4 py-8 text-center text-rose-500 font-bold">Error cargando historial</td></tr>';
            }
        }

        function changeHistoryPage(delta) {
            loadUploadHistory(currentHistoryPage + delta);
        }

        async function viewUploadReport(id) {
            try {
                const res = await authFetch(`${API_BASE_URL}/api/schedule/xml-uploads/${id}/report`);
                const data = await res.json();
                if (data.success && data.data) {
                    const r = data.data;
                    let html = `<div class="space-y-4">`;
                    if (r.matched_exact) {
                        html += `<div><h4 class="font-bold text-emerald-700 text-sm mb-1">✅ Coincidencia Exacta (${r.matched_exact.length})</h4>
                                 <ul class="text-xs text-slate-600 list-disc pl-4 h-max max-h-32 overflow-y-auto">${r.matched_exact.map(t => `<li>${t}</li>`).join('')}</ul></div>`;
                    }
                    if (r.matched_fuzzy) {
                        html += `<div><h4 class="font-bold text-amber-600 text-sm mb-1">⚠️ Coincidencia Fuzzy (${r.matched_fuzzy.length})</h4>
                                 <ul class="text-xs text-slate-600 list-disc pl-4 h-max max-h-32 overflow-y-auto">${r.matched_fuzzy.map(t => `<li>${t.xml_name} &rarr; <span class="font-bold">${t.db_name}</span> (score: ${t.score})</li>`).join('')}</ul></div>`;
                    }
                    if (r.unmatched_new) {
                        html += `<div><h4 class="font-bold text-indigo-600 text-sm mb-1">🆕 Nuevos / Sin Asignar (${r.unmatched_new.length})</h4>
                                 <ul class="text-xs text-slate-600 list-disc pl-4 h-max max-h-32 overflow-y-auto">${r.unmatched_new.map(t => `<li>${t}</li>`).join('')}</ul></div>`;
                    }
                    if (!r.matched_exact && !r.matched_fuzzy && !r.unmatched_new) {
                        html += `<div class="bg-slate-100 p-3 rounded text-sm font-mono whitespace-pre-wrap break-all">${JSON.stringify(r, null, 2)}</div>`;
                    }
                    html += `</div>`;
                    
                    document.getElementById('report-modal-body').innerHTML = html;
                    document.getElementById('report-modal').classList.remove('hidden');
                } else {
                    alert("No hay reporte detallado para esta subida.");
                }
            } catch (e) {
                console.error("Error loading report:", e);
                alert("Error cargando el reporte.");
            }
        }

        function closeReportModal() {
            document.getElementById('report-modal').classList.add('hidden');
        }

        // RPT Planilla Logic
        let rptCurrentPage = 1;

        function setInitialDates() {
            const now = new Date();
            const firstDay = new Date(now.getFullYear(), now.getMonth(), 1);

            document.getElementById('rpt-fecha-inicio').value = firstDay.toISOString().split('T')[0];
            document.getElementById('rpt-fecha-fin').value = now.toISOString().split('T')[0];
        }

        async function loadRptCatalogs() {
            try {
                const [resDoc, resSede] = await Promise.all([
                    authFetch(`${API_BASE_URL}/api/rpt-planilla/docentes`),
                    authFetch(`${API_BASE_URL}/api/rpt-planilla/sedes`)
                ]);

                const dataDoc = await resDoc.json();
                const dataSede = await resSede.json();

                if (dataDoc.success) {
                    const sel = document.getElementById('rpt-filter-docente');
                    sel.innerHTML = '<option value="Todos">Todos</option>';
                    dataDoc.data.forEach(d => {
                        const opt = document.createElement('option');
                        opt.value = d;
                        opt.textContent = d;
                        sel.appendChild(opt);
                    });
                }

                if (dataSede.success) {
                    const sel = document.getElementById('rpt-filter-sede');
                    sel.innerHTML = '<option value="Todas">Todas</option>';
                    dataSede.data.forEach(s => {
                        const opt = document.createElement('option');
                        opt.value = s;
                        opt.textContent = s;
                        sel.appendChild(opt);
                    });
                }
            } catch (e) {
                console.error("Error loading RPT catalogs:", e);
            }
        }

        async function handleSedeChange() {
            const sede = document.getElementById('rpt-filter-sede').value;
            const selAula = document.getElementById('rpt-filter-aula');

            if (sede === "Todas") {
                selAula.disabled = true;
                selAula.innerHTML = '<option value="Todos">Todos</option>';
                return;
            }

            selAula.disabled = false;
            selAula.innerHTML = '<option value="Todos">Cargando...</option>';

            try {
                const res = await authFetch(`${API_BASE_URL}/api/rpt-planilla/aulas?sede=${encodeURIComponent(sede)}`);
                const data = await res.json();

                if (data.success) {
                    selAula.innerHTML = '<option value="Todos">Todos</option>';
                    data.data.forEach(a => {
                        const opt = document.createElement('option');
                        opt.value = a;
                        opt.textContent = a;
                        selAula.appendChild(opt);
                    });
                }
            } catch (e) {
                console.error("Error loading aulas:", e);
            }
        }

        async function loadRptPlanilla(page = 1) {
            rptCurrentPage = page;
            const tbody = document.getElementById('rpt-planilla-body');
            const inicio = document.getElementById('rpt-fecha-inicio').value;
            const fin = document.getElementById('rpt-fecha-fin').value;
            const docente = document.getElementById('rpt-filter-docente').value;
            const sede = document.getElementById('rpt-filter-sede').value;
            const aula = document.getElementById('rpt-filter-aula').value;

            if (!inicio || !fin) {
                alert("Seleccione rango de fechas.");
                return;
            }

            tbody.innerHTML = '<tr><td colspan="9" class="px-4 py-12 text-center text-slate-400"><i class="fa-solid fa-spinner fa-spin text-2xl mb-3 block"></i>Filtrando...</td></tr>';

            try {
                let url = `${API_BASE_URL}/api/rpt-planilla/?fecha_inicio=${inicio}&fecha_fin=${fin}&page=${page}&limit=50`;
                if (docente !== "Todos") url += `&docente=${encodeURIComponent(docente)}`;
                if (sede !== "Todas") url += `&sede=${encodeURIComponent(sede)}`;
                if (aula !== "Todos") url += `&aula=${encodeURIComponent(aula)}`;

                const res = await authFetch(url);
                const data = await res.json();

                if (data.success) {
                    tbody.innerHTML = '';
                    if (data.data.length === 0) {
                        tbody.innerHTML = '<tr><td colspan="9" class="px-4 py-16 text-center text-slate-400 font-medium italic">" Todavía no se cargan estos datos a la bd "</td></tr>';
                        document.getElementById('rpt-total-records').innerText = "0";
                        document.getElementById('rpt-page-indicator').innerText = "Página 1 de 1";
                        document.getElementById('rpt-prev-btn').disabled = true;
                        document.getElementById('rpt-next-btn').disabled = true;
                        return;
                    }

                    // Summary Panel Update
                    document.getElementById('rpt-summary-panel').classList.remove('hidden');
                    document.getElementById('rpt-sum-hours').innerText = data.total_hours_sum.toFixed(2);
                    document.getElementById('rpt-count-recesos').innerText = data.total_receso_count;

                    // Metadata
                    document.getElementById('rpt-total-records').innerText = data.total_records;
                    document.getElementById('rpt-page-indicator').innerText = `Página ${data.current_page} de ${data.total_pages}`;
                    document.getElementById('rpt-prev-btn').disabled = data.current_page <= 1;
                    document.getElementById('rpt-next-btn').disabled = data.current_page >= data.total_pages;

                    data.data.forEach(r => {
                        const tr = document.createElement('tr');
                        const obs = r.observation;
                        const isRepl = r.is_replacement;

                        let rowClass = "hover:bg-slate-50 transition-colors border-b border-slate-50";
                        let extraInfo = "";
                        let hoursDisplay = r.horas_dictadas.toFixed(2);
                        let recesoDisplay = r.receso.toFixed(2);

                        // Visual markers for Titular's incidents
                        if (obs && !isRepl) {
                            const types = obs.type.split(', ');
                            const obsIds = obs.ids || []; // IDs array added in backend
                            let labelsHtml = '';

                            types.forEach((t, idx) => {
                                const currentObsId = obsIds[idx];
                                const deleteBtn = currentObsId ? `<button onclick="deleteObservation(${currentObsId})" class="ml-1 opacity-0 group-hover:opacity-100 hover:text-white transition-all" title="Eliminar ${t}"><i class="fa-solid fa-xmark"></i></button>` : '';

                                if (['FALTA', 'VACACIONES', 'DESCANSO_MEDICO'].includes(t)) {
                                    labelsHtml += `<span class="bg-rose-100 text-rose-700 px-1.5 py-0.5 rounded-md text-[9px] font-black uppercase inline-flex items-center gap-1 my-0.5 mr-1 group/tag"><i class="fa-solid fa-circle-exclamation"></i> ${t}${deleteBtn}</span>`;
                                } else if (t === 'REEMPLAZO') {
                                    labelsHtml += `<span class="bg-amber-100 text-amber-700 px-1.5 py-0.5 rounded-md text-[9px] font-black uppercase inline-flex items-center gap-1 my-0.5 mr-1 group/tag" title="Reemplazado por: ${obs.replacement_teacher_name || '---'}"><i class="fa-solid fa-user-group"></i> REEMPLAZO${deleteBtn}</span>`;
                                }
                            });

                            if (obs.has_discount_impact) {
                                rowClass = "bg-rose-50/50 text-rose-900 border-b border-rose-100";
                            }
                            extraInfo = `<div class="flex flex-wrap mt-1">${labelsHtml}</div>`;
                        }

                        // Special highlighting for the Replacement Teacher's record
                        if (isRepl) {
                            rowClass = "bg-amber-50 text-amber-900 border-b border-amber-100 font-medium";
                            extraInfo = `<div class="mt-1"><span class="bg-amber-600 text-white px-1.5 py-0.5 rounded-md text-[9px] font-black uppercase inline-flex items-center gap-1"><i class="fa-solid fa-award"></i> REEMPLAZO</span> <span class="text-[10px] opacity-70 italic ml-1">(Titular: ${r.titular_original})</span></div>`;
                        }

                        tr.className = rowClass;
                        tr.innerHTML = `
                            <td class="px-4 py-3 font-medium">${r.fecha_clase}</td>
                            <td class="px-4 py-3">${r.sede}</td>
                            <td class="px-4 py-3 font-bold">${r.ciclo}</td>
                            <td class="px-4 py-3 font-medium">
                                ${r.docente}
                                ${extraInfo}
                            </td>
                            <td class="px-4 py-3 text-xs">${r.curso}</td>
                            <td class="px-4 py-3 font-mono text-xs">${r.hora_inicio.substring(0, 5)}</td>
                            <td class="px-4 py-3 font-mono text-xs">${r.hora_fin.substring(0, 5)}</td>
                            <td class="px-4 py-3 text-center font-black">${hoursDisplay}</td>
                            <td class="px-4 py-3 text-center font-bold">${recesoDisplay}</td>
                        `;
                        tbody.appendChild(tr);
                    });
                }
            } catch (e) {
                console.error("Error loading RPT data:", e);
                tbody.innerHTML = '<tr><td colspan="9" class="px-4 py-12 text-center text-rose-500 font-bold">Error conectando con el servidor</td></tr>';
            }
        }

        function changeRptPage(delta) {
            loadRptPlanilla(rptCurrentPage + delta);
        }

        async function exportToExcel() {
            const inicio = document.getElementById('rpt-fecha-inicio').value;
            const fin = document.getElementById('rpt-fecha-fin').value;
            const docente = document.getElementById('rpt-filter-docente').value;
            const sede = document.getElementById('rpt-filter-sede').value;
            const aula = document.getElementById('rpt-filter-aula').value;

            if (!inicio || !fin) {
                alert("Seleccione rango de fechas para exportar.");
                return;
            }

            let url = `${API_BASE_URL}/api/rpt-planilla/export?fecha_inicio=${inicio}&fecha_fin=${fin}`;
            if (docente !== "Todos") url += `&docente=${encodeURIComponent(docente)}`;
            if (sede !== "Todas") url += `&sede=${encodeURIComponent(sede)}`;
            if (aula !== "Todos") url += `&aula=${encodeURIComponent(aula)}`;

            window.open(url, '_blank');
        }

        async function simulateUpload(overwrite = false) {
            const btn = document.getElementById('upload-btn');
            const fileInput = document.getElementById('file-upload');
            const startDate = document.getElementById('start-date').value;
            const endDate = document.getElementById('end-date').value;
            const progressFill = document.getElementById('progress-bar-fill');
            const statusLabel = document.getElementById('progress-status');

            if (!fileInput.files.length || !startDate || !endDate) {
                alert("Por favor selecciona un archivo XML, fecha inicio y fecha fin.");
                return;
            }

            btn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Procesando y Parseando...';
            btn.disabled = true;
            btn.classList.add('opacity-75');

            document.getElementById('upload-progress').classList.remove('hidden');
            document.getElementById('conflict-alert').classList.add('hidden');
            closeOverwriteModal();

            // Initial Animation
            progressFill.style.width = "20%";

            const formData = new FormData();
            formData.append("file", fileInput.files[0]);
            formData.append("start_date", startDate);
            formData.append("end_date", endDate);
            formData.append("force_overwrite", overwrite);

            // Simulate steps for UI feel
            setTimeout(() => {
                progressFill.style.width = "45%";
                document.getElementById('task-subjects').innerHTML = '<i class="fa-solid fa-check text-green-500 mr-2"></i> Extracción de Subjects';
            }, 800);

            setTimeout(() => {
                progressFill.style.width = "70%";
                document.getElementById('task-teachers').innerHTML = '<i class="fa-solid fa-check text-green-500 mr-2"></i> Extracción de Docentes';
            }, 1800);

            try {
                const response = await authFetch(`${API_BASE_URL}/api/schedule/upload`, {
                    method: "POST",
                    body: formData
                });

                const data = await response.json();

                if (!response.ok) {
                    document.getElementById('upload-progress').classList.add('hidden');

                    if (response.status === 400 && data.detail && data.detail.includes("force_overwrite=true")) {
                        // Caso específico de duplicados en rango
                        document.getElementById('overwrite-modal-msg').innerText = data.detail;
                        document.getElementById('overwrite-modal').classList.remove('hidden');
                        btn.innerHTML = '<i class="fa-solid fa-wand-magic-sparkles"></i> Vincular y Procesar';
                        btn.disabled = false;
                        btn.classList.remove('opacity-75');
                    } else {
                        console.error("Error 400/500 Detail:", data);
                        const detail = typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail);
                        alert("Error del Servidor: " + (detail || "Error desconocido. Revisa la consola y la terminal."));
                        resetUpload();
                    }
                } else {
                    progressFill.style.width = "100%";
                    statusLabel.innerText = "Finalizado";
                    document.getElementById('task-lessons').innerHTML = '<i class="fa-solid fa-check text-green-500 mr-2"></i> Generando Lesson Cards...';

                    setTimeout(() => {
                        alert(`¡Éxito! Horario procesado con ${data.records} sesiones.`);
                        resetUpload();
                        loadUploadHistory(); // Refrescar historial
                    }, 500);
                }
            } catch (error) {
                document.getElementById('upload-progress').classList.add('hidden');
                console.error("Upload error:", error);
                alert("Error de red conectando con el backend FastAPI. \nMensaje: " + error.message);
                resetUpload();
            }
        }

        function closeOverwriteModal() {
            document.getElementById('overwrite-modal').classList.add('hidden');
        }

        function confirmOverwrite() {
            simulateUpload(true);
        }

        function resetUpload() {
            const btn = document.getElementById('upload-btn');
            document.getElementById('conflict-alert').classList.add('hidden');
            document.getElementById('upload-progress').classList.add('hidden');
            btn.innerHTML = '<i class="fa-solid fa-wand-magic-sparkles"></i> Vincular y Procesar';
            btn.disabled = false;
            btn.classList.remove('opacity-75');
            document.getElementById('file-upload').value = null;
        }
        // Drag and drop logic and File Input change
        document.addEventListener("DOMContentLoaded", () => {
            loadUploadHistory(); // Cargar historial al inicio
            setInitialDates();
            const dropZone = document.getElementById('drop-zone');
            const fileInput = document.getElementById('file-upload');
            const fileNameDisplay = document.getElementById('file-name-display');

            if (dropZone) {
                ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
                    dropZone.addEventListener(eventName, e => {
                        e.preventDefault();
                        e.stopPropagation();
                    }, false);
                });

                ['dragenter', 'dragover'].forEach(eventName => {
                    dropZone.addEventListener(eventName, () => dropZone.classList.add('bg-indigo-50', 'border-indigo-400'), false);
                });

                ['dragleave', 'drop'].forEach(eventName => {
                    dropZone.addEventListener(eventName, () => dropZone.classList.remove('bg-indigo-50', 'border-indigo-400'), false);
                });

                dropZone.addEventListener('drop', (e) => {
                    const dt = e.dataTransfer;
                    fileInput.files = dt.files;
                    updateFileName();
                }, false);
            }

            if (fileInput) {
                fileInput.addEventListener('change', updateFileName);
            }

            function updateFileName() {
                if (fileInput && fileInput.files.length > 0) {
                    fileNameDisplay.textContent = fileInput.files[0].name;
                    fileNameDisplay.classList.add('text-indigo-600');
                } else if (fileNameDisplay) {
                    fileNameDisplay.textContent = "Arrastra tu XML aquí";
                    fileNameDisplay.classList.remove('text-indigo-600');
                }
            }

            window.resetUpload = function () {
                const btn = document.getElementById('upload-btn');
                if (document.getElementById('conflict-alert')) document.getElementById('conflict-alert').classList.add('hidden');
                if (document.getElementById('upload-progress')) document.getElementById('upload-progress').classList.add('hidden');
                if (btn) {
                    btn.innerHTML = '<i class="fa-solid fa-wand-magic-sparkles"></i> Vincular y Procesar';
                    btn.disabled = false;
                    btn.classList.remove('opacity-75');
                }
                if (fileInput) fileInput.value = null;
                updateFileName();
            };

            // Event Listeners for Visor
            document.getElementById('schedule-filter-type')?.addEventListener('change', fillTargetSelect);
            document.getElementById('schedule-filter-target')?.addEventListener('change', loadSchedule);
            document.getElementById('schedule-filter-type')?.addEventListener('change', fillTargetSelect);
            document.getElementById('schedule-filter-target')?.addEventListener('change', loadSchedule);
            // document.getElementById('schedule-week')?.addEventListener('change', loadSchedule); // Eliminado

            // Default dates for schedule visor (Current Monday to Friday)
            const now = new Date();
            const day = now.getDay() || 7;
            const mon = new Date(now); mon.setDate(now.getDate() - day + 1);
            const fri = new Date(mon); fri.setDate(mon.getDate() + 4);

            if (document.getElementById('schedule-start-date'))
                document.getElementById('schedule-start-date').value = mon.toISOString().split('T')[0];
            if (document.getElementById('schedule-end-date'))
                document.getElementById('schedule-end-date').value = fri.toISOString().split('T')[0];

            // Initial Loads
            loadConfig('recess');
            loadConfig('lunch');
            loadCatalogs();
            loadObsTeacherList();
        });

        // --- Visor de Horarios Logic ---
        let teachersData = [];
        let classesData = [];

        function getFactorMinutes(subject) {
            if (!subject) return 0;
            const match = subject.match(/\(F\+(\d+)\)/);
            return match ? parseInt(match[1]) : 0;
        }

        function getCalculatedTime(startTime, endTime, subject) {
            const factorMins = getFactorMinutes(subject);
            if (factorMins === 0) return `${startTime.substring(0, 5)} - ${endTime.substring(0, 5)}`;

            const [h, m] = endTime.split(':').map(Number);
            const date = new Date();
            date.setHours(h, m, 0);
            date.setMinutes(date.getMinutes() + factorMins);

            const newEnd = `${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`;
            return `${startTime.substring(0, 5)} - ${newEnd}`;
        }

        function cleanCycleName(name) {
            if (!name) return "";
            return name.replace(/\s*\([^)]*\)$/, '').trim();
        }

        function getCourseColor(subject, type) {
            if (type !== 'classroom') return 'bg-indigo-50 border-indigo-200 text-indigo-900 hover:border-indigo-300';

            const s = subject.toUpperCase();
            const math = ['ALGEBRA', 'GEOMETRIA', 'RAZ. MATEMATICO', 'ARITMETICA', 'TRIGONOMETRIA', 'RAZONAMIENTO MATEMATICO'];
            const letters = ['LENGUAJE', 'LITERATURA', 'FILOSOFIA', 'INGLES', 'HISTORIA', 'PSICOLOGIA', 'CIVICA'];
            const science = ['BIOLOGIA', 'QUIMICA', 'FISICA', 'GEOGRAFIA'];

            if (math.some(m => s.includes(m))) return 'bg-blue-50 border-blue-200 text-blue-900 hover:border-blue-300';
            if (letters.some(l => s.includes(l))) return 'bg-orange-50 border-orange-200 text-orange-900 hover:border-orange-300';
            if (science.some(sci => s.includes(sci))) return 'bg-green-50 border-green-200 text-green-900 hover:border-green-300';

            return 'bg-slate-50 border-slate-200 text-slate-900 hover:border-slate-300';
        }

        async function loadCatalogs() {
            try {
                const tRes = await authFetch(`${API_BASE_URL}/api/schedule/teachers`);
                const tData = await tRes.json();
                if (tData.success) teachersData = tData.data;

                const cRes = await authFetch(`${API_BASE_URL}/api/schedule/classes`);
                const cData = await cRes.json();
                if (cData.success) classesData = cData.data;

                fillTargetSelect();
            } catch (e) { console.error("Error loading catalogs:", e); }
        }

        function fillTargetSelect() {
            const type = document.getElementById('schedule-filter-type').value;
            const target = document.getElementById('schedule-filter-target');
            if (!target) return;
            target.innerHTML = '';

            let data = type === 'teacher' ? teachersData : classesData;

            // Debugging Ajuste 3: 
            console.log(`POBLANDO SELECT (${type}):`, data);

            data.forEach(item => {
                let opt = document.createElement('option');
                opt.value = item.id;

                // AJUSTE 3: Mapeo correcto para docentes (last_name, first_name)
                if (type === 'teacher') {
                    opt.textContent = `${item.last_name || ''}, ${item.first_name || ''}`.trim() || `ID: ${item.id}`;
                } else {
                    opt.textContent = item.name || `Aula ${item.id}`;
                }

                target.appendChild(opt);
            });

            if (data.length > 0) loadSchedule();
        }

        async function loadSchedule() {
            const type = document.getElementById('schedule-filter-type').value;
            const targetId = document.getElementById('schedule-filter-target').value;
            const sDate = document.getElementById('schedule-start-date').value;
            const eDate = document.getElementById('schedule-end-date').value;

            if (!targetId || !sDate || !eDate) return;

            const endpoint = type === 'teacher'
                ? `${API_BASE_URL}/api/schedule/teacher/${targetId}?start_date=${sDate}&end_date=${eDate}`
                : `${API_BASE_URL}/api/schedule/classroom/${targetId}?start_date=${sDate}&end_date=${eDate}`;

            try {
                const res = await authFetch(endpoint);
                const data = await res.json();
                if (data.success) {
                    renderScheduleGrid(data.data, new Date(sDate + 'T00:00:00'));
                }
            } catch (e) { console.error("Error loading schedule:", e); }
        }

        async function exportSchedule() {
            const type = document.getElementById('schedule-filter-type').value;
            const targetId = document.getElementById('schedule-filter-target').value;
            const sDate = document.getElementById('schedule-start-date').value;
            const eDate = document.getElementById('schedule-end-date').value;

            if (!targetId || !sDate || !eDate) return alert("Por favor selecciona los filtros primero antes de exportar.");

            const btn = document.getElementById('export-excel-btn');
            btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Generando...';
            btn.disabled = true;

            try {
                const endpoint = `${API_BASE_URL}/api/schedule/export?type=${type}&target_id=${targetId}&start_date=${sDate}&end_date=${eDate}`;

                const res = await authFetch(endpoint);
                if (!res.ok) {
                    const errorData = await res.json();
                    throw new Error(errorData.detail || "Error al exportar");
                }

                const blob = await res.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.style.display = 'none';
                a.href = url;

                const todayStr = new Date().toISOString().slice(0, 10).replace(/-/g, "");
                a.download = `horarios_export_${todayStr}.xlsx`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);

            } catch (e) {
                alert("Error descargando el archivo Excel: " + e.message);
            } finally {
                btn.innerHTML = '<i class="fa-solid fa-download"></i> Exportar a Excel';
                btn.disabled = false;
            }
        }

        function renderScheduleGrid(sessions, mondayDate) {
            const filterType = document.getElementById('schedule-filter-type');
            if (!filterType) return;
            const type = filterType.value;
            const summaryPanel = document.getElementById('schedule-teacher-summary');

            if (type === 'teacher') {
                if (summaryPanel) summaryPanel.classList.remove('hidden');
                renderTeacherAgenda(sessions, mondayDate);
            } else {
                if (summaryPanel) summaryPanel.classList.add('hidden');
                renderClassroomCalendar(sessions, mondayDate);
            }
        }

        function renderTeacherAgenda(sessions, startDate) {
            const tbody = document.getElementById('schedule-grid-body');
            const hourHeader = document.getElementById('schedule-header-hour');
            if (hourHeader) hourHeader.classList.add('hidden');

            if (!tbody) return;
            tbody.innerHTML = '';

            if (!sessions || sessions.length === 0) {
                tbody.innerHTML = `<tr class="border-b border-slate-200"><td colspan="5" class="p-12 text-center text-slate-400 font-medium italic">No hay clases programadas para este docente en el rango seleccionado.</td></tr>`;
                document.getElementById('sch-summary-name').innerText = "Sin Datos";
                document.getElementById('sch-summary-range').innerText = "---";
                document.getElementById('sch-summary-hours').innerText = "0.00";
                document.getElementById('sch-summary-breaks').innerText = "0";
                return;
            }

            // Inject Breaks (si aplica, manteniendo lógica legacy)
            injectBreaks(sessions, startDate, true);

            // Group by Day (Dynamic Range)
            const daysInRange = [];
            let curr = new Date(startDate);
            const endDateStr = document.getElementById('schedule-end-date').value;
            const endDate = new Date(endDateStr + 'T00:00:00');

            while (curr <= endDate) {
                daysInRange.push(curr.toISOString().split('T')[0]);
                curr.setDate(curr.getDate() + 1);
                if (daysInRange.length > 31) break; // Safety cap
            }

            let totalHours = 0;
            let totalBreaks = 0;
            let teacherName = "";

            const grouped = {};
            daysInRange.forEach(d => grouped[d] = []);

            sessions.forEach(s => {
                if (grouped[s.date]) grouped[s.date].push(s);
                if (!s.is_break && !teacherName) {
                    // Si es reemplazo, no tomamos el nombre del titular para el resumen
                    // pero rpt tiene el nombre del docente que buscamos
                }
            });

            // Re-fetch clean teacher name from select if empty
            const targetSelect = document.getElementById('schedule-filter-target');
            teacherName = targetSelect.options[targetSelect.selectedIndex]?.text || "Docente";

            // Calculate Totals using Backend Logic Sync
            sessions.forEach(s => {
                if (!s.is_break) {
                    totalHours += (s.horas_dictadas || 0);
                    if ((s.receso || 0) > 0) totalBreaks += 1; // CONTEO, no suma
                }
            });

            if (document.getElementById('sch-summary-name')) document.getElementById('sch-summary-name').innerText = teacherName;

            const moStr = new Date(startDate).toLocaleDateString('es-ES', { day: '2-digit', month: 'short' });
            const frStr = endDate.toLocaleDateString('es-ES', { day: '2-digit', month: 'short', year: 'numeric' });
            if (document.getElementById('sch-summary-range')) document.getElementById('sch-summary-range').innerText = `${moStr} - ${frStr}`;
            if (document.getElementById('sch-summary-hours')) document.getElementById('sch-summary-hours').innerText = totalHours.toFixed(2);
            if (document.getElementById('sch-summary-breaks')) document.getElementById('sch-summary-breaks').innerText = totalBreaks.toString();

            const tr = document.createElement('tr');
            tr.className = "align-top";

            daysInRange.forEach(dateStr => {
                const td = document.createElement('td');
                td.className = "p-3 border-r border-slate-200 min-w-[220px] bg-slate-50/10";

                const daySessions = grouped[dateStr].sort((a, b) => (a.start_time || "").localeCompare(b.start_time || ""));

                let html = "";
                daySessions.forEach(s => {
                    const timeRange = getCalculatedTime(s.start_time, s.end_time, s.subject || "");
                    const cleanedSubject = s.is_break ? (s.subject || "RECESO") : (s.subject || "").replace(/\s*\([^)]*\)$/, '').trim();

                    if (s.is_break) {
                        const isLunch = s.category === 'lunch';
                        html += `
                            <div class="mb-3 bg-amber-50 border border-amber-200 rounded-xl p-3 flex flex-col items-center justify-center text-center shadow-sm animate-in fade-in zoom-in duration-300">
                                <div class="text-amber-600 text-lg mb-1"><i class="fa-solid fa-${isLunch ? 'utensils' : 'mug-hot'}"></i></div>
                                <div class="font-black text-[10px] text-amber-900 uppercase tracking-widest">${cleanedSubject}</div>
                                <div class="text-[9px] font-bold text-amber-700/60 mt-0.5">${timeRange}</div>
                            </div>
                        `;
                    } else {
                        // AJUSTE 1: Estilo distintivo para reemplazos
                        let cardColor = getCourseColor(s.subject, 'teacher');
                        let replBadge = "";
                        if (s.is_replacement) {
                            cardColor = "bg-orange-50 border-orange-300 text-orange-900 hover:border-orange-400";
                            replBadge = `
                                <div class="mt-2 py-1 px-2 bg-orange-200/50 rounded-lg text-[9px] font-black text-orange-800 uppercase tracking-tighter">
                                    <i class="fa-solid fa-people-arrows"></i> REEMPLAZO (Titular: ${s.titular_name})
                                </div>
                            `;
                        }

                        const groupName = cleanCycleName(s.class_group);
                        const sedeName = s.sede || "S/S";
                        const tooltip = `Curso: ${s.subject}\nHora: ${timeRange}\nAula: ${s.class_group}\nSede: ${sedeName}`;

                        html += `
                            <div title="${tooltip}" class="mb-3 ${cardColor} border rounded-xl p-4 shadow-sm flex flex-col items-center justify-center text-center transition-all hover:scale-105 hover:shadow-lg hover:z-10 cursor-default group border-b-4">
                                <div class="font-black text-sm leading-tight uppercase tracking-tight text-slate-900">${cleanedSubject}</div>
                                <div class="text-[11px] font-bold text-slate-600 mt-2 bg-white/50 px-3 py-1 rounded-full"><i class="fa-regular fa-clock mr-1"></i> ${timeRange}</div>
                                
                                <div class="mt-2 flex flex-col items-center gap-1">
                                    <div class="text-[10px] font-black flex items-center justify-center gap-1 uppercase tracking-tighter opacity-60">
                                        <i class="fa-solid fa-layer-group"></i> ${groupName}
                                    </div>
                                    <div class="text-[9px] font-bold flex items-center justify-center gap-1 uppercase tracking-widest text-indigo-600/70">
                                        <i class="fa-solid fa-location-dot"></i> ${sedeName}
                                    </div>
                                </div>

                                ${replBadge}
                            </div>
                        `;
                    }
                });

                if (daySessions.length === 0) {
                    html = `<div class="h-64 flex items-center justify-center text-slate-300 italic text-xs uppercase tracking-widest">Sin Actividad</div>`;
                }

                td.innerHTML = html;
                tr.appendChild(td);
            });

            tbody.appendChild(tr);

            // Update Headers (Dynamic Day Names)
            const thead = document.querySelector('#schedule thead tr');
            if (thead) {
                // Keep the first th (Horario header) if classroom view, but in teacher agenda it's hidden
                thead.innerHTML = '';
                if (!hourHeader.classList.contains('hidden')) {
                    thead.appendChild(hourHeader);
                }

                daysInRange.forEach(d => {
                    const dateObj = new Date(d + 'T00:00:00');
                    const dayName = dateObj.toLocaleDateString('es-ES', { weekday: 'short' }).toUpperCase();
                    const dayNum = dateObj.getDate();
                    const monthName = dateObj.toLocaleDateString('es-ES', { month: 'short' }).toUpperCase();

                    const th = document.createElement('th');
                    th.className = "px-4 py-3 border-r border-slate-200 text-center tracking-wider bg-slate-100 min-w-[220px]";
                    th.innerHTML = `
                        <div class="flex flex-col items-center">
                            <span class="text-[10px] font-black tracking-widest text-slate-400">${dayName}</span>
                            <span class="text-lg font-black text-slate-800">${dayNum}</span>
                            <span class="text-[9px] font-bold opacity-50 uppercase">${monthName}</span>
                        </div>
                    `;
                    thead.appendChild(th);
                });
            }
        }

        function renderClassroomCalendar(sessions, startDate) {
            const tbody = document.getElementById('schedule-grid-body');
            const hourHeader = document.getElementById('schedule-header-hour');
            if (hourHeader) hourHeader.classList.remove('hidden');

            if (!tbody) return;
            tbody.innerHTML = '';
            if (!sessions || sessions.length === 0) {
                tbody.innerHTML = `<tr class="border-b border-slate-200"><td colspan="6" class="p-12 text-center text-slate-400 font-medium italic">No hay clases programadas para esta aula.</td></tr>`;
                return;
            }

            // Inject Breaks
            injectBreaks(sessions, startDate, false);

            const timeBlocks = {};
            sessions.forEach(s => {
                if (!timeBlocks[s.start_time]) {
                    timeBlocks[s.start_time] = { start_time: s.start_time, end_time: s.end_time, is_break: s.is_break, days: {} };
                }
                timeBlocks[s.start_time].days[s.date] = s;
            });

            const sortedStartTimes = Object.keys(timeBlocks).sort();

            const daysInRange = [];
            let curr = new Date(startDate);
            const endDate = new Date(document.getElementById('schedule-end-date').value + 'T00:00:00');
            while (curr <= endDate) {
                daysInRange.push(curr.toISOString().split('T')[0]);
                curr.setDate(curr.getDate() + 1);
                if (daysInRange.length > 31) break;
            }

            sortedStartTimes.forEach(time => {
                const block = timeBlocks[time];
                const tr = document.createElement('tr');

                if (block.is_break) {
                    const firstSession = Object.values(block.days)[0];
                    const isLunch = firstSession.category === 'lunch';
                    const icon = isLunch ? 'utensils' : 'mug-hot';
                    const label = firstSession.subject || (isLunch ? 'Almuerzo' : 'Receso');
                    const bgColor = isLunch ? 'bg-slate-100/80' : 'bg-amber-50/50';
                    const textColor = isLunch ? 'text-slate-500' : 'text-amber-900';

                    tr.className = `${bgColor} border-b border-slate-200`;
                    tr.innerHTML = `
                        <td class="px-2 py-1.5 text-center border-r border-slate-200 ${textColor}">
                            <div class="font-bold text-xs">${block.start_time}</div>
                            <div class="text-[10px] opacity-70">${block.end_time}</div>
                        </td>
                        <td colspan="${daysInRange.length}" class="py-2 text-center ${textColor} font-black tracking-[0.2em] uppercase text-[10px] flex items-center justify-center gap-2">
                            <i class="fa-solid fa-${icon}"></i> ${label}
                        </td>
                    `;
                } else {
                    tr.className = "border-b border-slate-200";
                    let rowHtml = `
                        <td class="px-2 py-2 font-black text-slate-800 text-center border-r border-slate-200 bg-slate-50/50">
                            <div class="text-sm">${block.start_time}</div>
                            <div class="text-[10px] text-slate-400 font-bold">${block.end_time}</div>
                        </td>
                    `;

                    daysInRange.forEach(dateStr => {
                        const session = block.days[dateStr];
                        if (session && !session.is_break && session.subject) {
                            const subLabel = session.teacher || "Sin Docente";
                            const cardColor = getCourseColor(session.subject, 'classroom');
                            const timeRange = getCalculatedTime(session.start_time, session.end_time, session.subject);
                            const tooltip = `Curso: ${session.subject}\nHora: ${timeRange}\nDocente: ${session.teacher}`;

                            rowHtml += `
                            <td class="p-1 border-r border-slate-200 align-middle h-20">
                                <div title="${tooltip}" class="${cardColor} border rounded-lg p-2 shadow-sm h-full flex flex-col items-center justify-center text-center transition-all hover:scale-105 hover:shadow-lg hover:z-10 cursor-default">
                                    <div class="font-black text-[10px] leading-tight uppercase tracking-tighter">${session.subject}</div>
                                    <div class="text-[9px] font-bold opacity-80 mt-1">${timeRange}</div>
                                    <div class="text-[8px] font-black mt-1 uppercase tracking-tighter opacity-60 truncate w-full">${subLabel}</div>
                                </div>
                            </td>
                            `;
                        } else {
                            rowHtml += `<td class="p-1 border-r border-slate-200 bg-slate-50/20"></td>`;
                        }
                    });
                    tr.innerHTML = rowHtml;
                }
                tbody.appendChild(tr);
            });

            const theadRows = document.querySelector('#schedule thead tr');
            if (theadRows) {
                theadRows.innerHTML = '';
                if (hourHeader) theadRows.appendChild(hourHeader);

                daysInRange.forEach(d => {
                    const dateObj = new Date(d + 'T00:00:00');
                    const th = document.createElement('th');
                    th.className = "px-4 py-3 border-r border-slate-200 text-center tracking-wider bg-slate-100 min-w-[150px]";
                    th.innerHTML = `
                        <div class="flex flex-col items-center">
                            <span class="text-xs font-black tracking-widest text-slate-500">${dateObj.toLocaleDateString('es-ES', { weekday: 'short' }).toUpperCase()}</span>
                            <span class="text-lg font-black text-slate-800">${dateObj.getDate()}</span>
                        </div>
                    `;
                    theadRows.appendChild(th);
                });
            }
        }

        function injectBreaks(sessions, startDate, isTeacherView) {
            let minStart = "23:59";
            let maxEnd = "00:00";
            sessions.forEach(s => {
                if (s.start_time < minStart) minStart = s.start_time;
                if (s.end_time > maxEnd) maxEnd = s.end_time;
            });

            const allConfigs = [
                ...currentConfigs.recess.map(r => ({ ...r, category: 'recess' })),
                ...currentConfigs.lunch.map(l => ({ ...l, category: 'lunch' }))
            ];

            const datesInRange = [];
            let curr = new Date(startDate);
            const endDate = new Date(document.getElementById('schedule-end-date').value + 'T00:00:00');
            while (curr <= endDate) {
                datesInRange.push(curr.toISOString().split('T')[0]);
                curr.setDate(curr.getDate() + 1);
                if (datesInRange.length > 31) break;
            }

            allConfigs.forEach(conf => {
                const bStart = conf.start_time.substring(0, 5);
                const bEnd = conf.end_time.substring(0, 5);
                if (bStart < minStart || bEnd > maxEnd) return;

                const hasCollision = sessions.some(s => {
                    if (s.is_break) return false;
                    return bStart < s.end_time && s.start_time < bEnd;
                });

                if (!hasCollision) {
                    datesInRange.forEach(dateStr => {
                        sessions.push({
                            date: dateStr,
                            start_time: bStart,
                            end_time: bEnd,
                            subject: "RECESO",
                            is_break: true,
                            category: conf.category
                        });
                    });
                }
            });
        }

        // --- Observations Module Logic ---
        function toggleObsTab(tabName) {
            const regTab = document.getElementById('obs-tab-register');
            const logsTab = document.getElementById('obs-tab-logs');
            const regBtn = document.getElementById('tab-btn-register');
            const logsBtn = document.getElementById('tab-btn-logs');

            if (tabName === 'register') {
                regTab.classList.remove('hidden');
                logsTab.classList.add('hidden');
                regBtn.className = "px-8 py-4 text-sm font-black border-b-2 border-indigo-600 text-indigo-600 transition-all uppercase tracking-widest";
                logsBtn.className = "px-8 py-4 text-sm font-black border-b-2 border-transparent text-slate-400 hover:text-slate-600 transition-all uppercase tracking-widest";
            } else {
                regTab.classList.add('hidden');
                logsTab.classList.remove('hidden');
                logsBtn.className = "px-8 py-4 text-sm font-black border-b-2 border-indigo-600 text-indigo-600 transition-all uppercase tracking-widest";
                regBtn.className = "px-8 py-4 text-sm font-black border-b-2 border-transparent text-slate-400 hover:text-slate-600 transition-all uppercase tracking-widest";
                loadObsLogs();
            }
        }

        async function loadObsTeacherList() {
            const select = document.getElementById('obs-filter-docente');
            const datalist = document.getElementById('teachers-datalist');
            if (!select) return;
            try {
                const res = await authFetch(`${API_BASE_URL}/api/schedule/teachers`);
                const json = await res.json();
                const teachers = json.data || [];

                // Fill the filter select
                select.innerHTML = '<option value="">Selecciona un docente...</option>';

                // Fill the datalist for replacement autocomplete
                if (datalist) datalist.innerHTML = '';

                teachers.forEach(t => {
                    const fullName = `${t.last_name || ''}, ${t.first_name || ''}`.trim() || `Docente ${t.id}`;

                    const opt = document.createElement('option');
                    opt.value = t.id;
                    opt.textContent = fullName;
                    select.appendChild(opt);

                    if (datalist) {
                        const dOpt = document.createElement('option');
                        dOpt.value = fullName;
                        // Store the ID in a data attribute to retrieve it later
                        dOpt.setAttribute('data-id', t.id);
                        datalist.appendChild(dOpt);
                    }
                });
            } catch (e) {
                console.error("Error loading teachers for obs:", e);
                select.innerHTML = '<option value="">Error al cargar</option>';
            }
        }

        async function searchClassesForObs() {
            console.log("Iniciando búsqueda de clases para el docente...");
            const selDoc = document.getElementById('obs-filter-docente');
            const teacherId = selDoc.value;
            const teacherName = selDoc.options[selDoc.selectedIndex]?.text || "Docente";
            const dateStart = document.getElementById('obs-date-start').value;
            const dateEnd = document.getElementById('obs-date-end').value;
            const tbody = document.getElementById('obs-search-body');

            if (!teacherId || !dateStart || !dateEnd) {
                alert("Por favor completa todos los filtros de búsqueda (Docente, Fecha Inicio y Fin).");
                return;
            }

            console.log(`Buscando clases para ID: ${teacherId} (${teacherName}) del ${dateStart} al ${dateEnd}`);
            tbody.innerHTML = '<tr><td colspan="5" class="px-4 py-12 text-center text-slate-400"><i class="fa-solid fa-spinner fa-spin text-xl mb-2"></i> Buscando clases...</td></tr>';

            try {
                const url = `${API_BASE_URL}/api/schedule/sessions-for-obs?teacher_id=${teacherId}&start_date=${dateStart}&end_date=${dateEnd}`;
                const res = await authFetch(url);
                if (!res.ok) {
                    const errorData = await res.json();
                    throw new Error(errorData.detail || `Error HTTP: ${res.status}`);
                }

                const json = await res.json();
                const sessions = json.data || [];
                console.log("Sesiones encontradas:", sessions.length);

                tbody.innerHTML = '';
                if (sessions.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="5" class="px-4 py-12 text-center text-slate-400 italic">No se encontraron clases en este rango para este docente.</td></tr>';
                    return;
                }

                sessions.forEach(s => {
                    const tr = document.createElement('tr');
                    // Usamos session_ids para bloques agrupados
                    const sids = (s.session_ids || [s.id]).join(',');
                    tr.setAttribute('data-session-ids', sids);
                    tr.className = "hover:bg-slate-50 transition-colors border-b border-slate-100 group";

                    const sessionData = {
                        ...s,
                        docente_name: teacherName,
                        teacher_id: teacherId
                    };

                    // Renderizar etiqueta si ya existen incidencias
                    let statusBadge = '';
                    const hasObs = s.badge && s.badge !== 'INGRESAR';

                    if (hasObs) {
                        let badgeColor = 'bg-rose-50 text-rose-700 border-rose-200'; // Default FALTA (Rose)
                        if (s.badge === 'REEMPLAZO') {
                            badgeColor = 'bg-amber-50 text-amber-700 border-amber-200'; // REEMPLAZO (Amber)
                        } else if (s.badge === 'FALTA/REEMP') {
                            badgeColor = 'bg-indigo-50 text-indigo-700 border-indigo-200'; // MIXTA (Indigo)
                        }

                        statusBadge = `
                            <span class="${badgeColor} px-2 py-0.5 rounded-lg text-[9px] font-black uppercase tracking-tighter border shadow-sm ml-2">
                                <i class="fa-solid fa-circle-check mr-1 text-[8px]"></i> ${s.badge}
                            </span>
                        `;
                    }

                    // BUG 4: Si tiene incidencia, mostramos badge en lugar de botón
                    let actionHtml = `
                        <button onclick='openRegisterObsModal(${JSON.stringify(sessionData).replace(/'/g, "&apos;")}, this.closest("tr"))' class="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-xl text-xs font-black uppercase tracking-widest transition-all hover:scale-105 active:scale-95 shadow-md hover:shadow-indigo-200">
                            Registrar
                        </button>
                    `;

                    if (hasObs) {
                        actionHtml = statusBadge; // Reemplazamos botón por el badge
                        statusBadge = ''; // No duplicar arriba
                    }

                    tr.innerHTML = `
                        <td class="px-4 py-4 font-bold text-slate-800 whitespace-nowrap">${s.date} ${statusBadge}</td>
                        <td class="px-4 py-4">${s.subject || '---'}</td>
                        <td class="px-4 py-4"><span class="bg-slate-100 px-2 py-1 rounded text-xs font-bold uppercase">${s.class_group || '---'}</span></td>
                        <td class="px-4 py-4 font-mono text-xs text-slate-500">${s.start_time.substring(0, 5)} - ${s.end_time.substring(0, 5)}</td>
                        <td class="px-4 py-4 text-right action-cell">
                            ${actionHtml}
                        </td>
                    `;
                    tbody.appendChild(tr);
                });
            } catch (e) {
                console.error("Error searching classes:", e);
                tbody.innerHTML = `<tr><td colspan="5" class="px-4 py-12 text-center text-rose-500 font-bold">Error al buscar clases: ${e.message}</td></tr>`;
            }
        }

        let currentSessionForObs = null;
        let currentRowElementForObs = null; // Bug 1 fix: referencia directa al <tr>

        function openRegisterObsModal(session, rowElement) {
            currentSessionForObs = session;
            currentRowElementForObs = rowElement || null; // guardar referencia directa al DOM
            document.getElementById('obs-form-session-id').value = session.id;
            document.getElementById('obs-form-teacher-id').value = session.teacher_id;
            document.getElementById('obs-modal-teacher-name').innerText = session.docente_name || "Docente";
            document.getElementById('obs-modal-date').innerText = `${session.date} (${session.start_time.substring(0, 5)} - ${session.end_time.substring(0, 5)})`;

            // Reset form
            document.querySelector('input[name="obs-block-mode"][value="full"]').checked = true;
            document.getElementById('obs-form-type').value = 'FALTA';
            document.getElementById('obs-form-discount').value = 'SIMPLE';
            document.getElementById('obs-form-replacement-last').value = '';
            document.getElementById('obs-form-replacement-first').value = '';
            document.getElementById('obs-form-description').value = '';

            toggleObsBlockMode(true);
            document.getElementById('obs-register-modal').classList.remove('hidden');
        }

        function toggleObsBlockMode(isFull) {
            const singleCont = document.getElementById('obs-single-mode-container');
            const splitCont = document.getElementById('obs-split-mode-container');

            if (isFull) {
                singleCont.classList.remove('hidden');
                splitCont.classList.add('hidden');
                handleObsTypeChange();
            } else {
                singleCont.classList.add('hidden');
                splitCont.classList.remove('hidden');
                renderPedagogicalSlots();
            }
        }

        function renderPedagogicalSlots() {
            const container = document.getElementById('obs-split-mode-container');
            if (!currentSessionForObs) return;

            const start = currentSessionForObs.start_time;
            const end = currentSessionForObs.end_time;

            // Generate 50 min slots
            const slots = splitIntoPedagogicalHours(start, end);

            container.innerHTML = `<p class="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2">Desglose de Bloque: ${slots.length} horas pedagógicas</p>`;

            slots.forEach((slot, idx) => {
                const slotDiv = document.createElement('div');
                slotDiv.className = "bg-white border border-slate-200 rounded-xl p-4 shadow-sm space-y-3";
                slotDiv.innerHTML = `
                    <div class="flex justify-between items-center">
                        <span class="text-xs font-black text-indigo-600 bg-indigo-50 px-2 py-1 rounded">Hora ${idx + 1}: ${slot.start} - ${slot.end}</span>
                        <select class="obs-slot-type text-[10px] font-bold border-none bg-slate-100 rounded-md px-2 py-1 focus:ring-0" onchange="toggleSlotReplacement(${idx}, this.value)">
                            <option value="NINGUNA">SIN INCIDENCIA</option>
                            <option value="FALTA" selected>FALTA</option>
                            <option value="REEMPLAZO">REEMPLAZO</option>
                        </select>
                    </div>
                    <div id="slot-replacement-container-${idx}" class="hidden mt-2 pt-2 border-t border-slate-100">
                        <div class="grid grid-cols-2 gap-3">
                            <input type="text" class="obs-slot-replacement-last w-full px-3 py-2 bg-amber-50 border border-amber-100 rounded-lg text-xs font-medium placeholder:text-amber-400 focus:bg-white" list="teachers-datalist" placeholder="Apellidos...">
                            <input type="text" class="obs-slot-replacement-first w-full px-3 py-2 bg-amber-50 border border-amber-100 rounded-lg text-xs font-medium placeholder:text-amber-400 focus:bg-white" placeholder="Nombres...">
                        </div>
                    </div>
                    <input type="hidden" class="obs-slot-start" value="${slot.start}">
                    <input type="hidden" class="obs-slot-end" value="${slot.end}">
                `;
                container.appendChild(slotDiv);
            });
        }

        function toggleSlotReplacement(idx, value) {
            const container = document.getElementById(`slot-replacement-container-${idx}`);
            if (value === 'REEMPLAZO') container.classList.remove('hidden');
            else container.classList.add('hidden');
        }

        function splitIntoPedagogicalHours(startTime, endTime) {
            const parse = t => {
                const [h, m] = t.split(':').map(Number);
                return h * 60 + m;
            };
            const format = m => {
                const h = Math.floor(m / 60);
                const mins = m % 60;
                return `${String(h).padStart(2, '0')}:${String(mins).padStart(2, '0')}`;
            };

            const startMins = parse(startTime);
            const endMins = parse(endTime);
            const totalMins = endMins - startMins;

            const slots = [];
            let current = startMins;

            while (current < endMins) {
                let next = current + 50;
                if (next > endMins) next = endMins;

                // If the remaining time is very small (e.g. 5-10 mins), merge it with the last slot
                // to avoid tiny fragments. But typically blocks are multiples of 50.
                if (endMins - next < 15 && endMins - next > 0) {
                    next = endMins;
                }

                slots.push({ start: format(current), end: format(next) });
                current = next;
            }
            return slots;
        }

        function closeObsRegisterModal() {
            document.getElementById('obs-register-modal').classList.add('hidden');
        }

        function handleObsTypeChange() {
            const type = document.getElementById('obs-form-type').value;
            const container = document.getElementById('obs-replacement-container');
            if (type === 'REEMPLAZO') {
                container.classList.remove('hidden');
            } else {
                container.classList.add('hidden');
            }
        }

        async function saveObservation() {
            const isFullBlock = document.querySelector('input[name="obs-block-mode"]:checked').value === 'full';
            // Leer directamente del objeto en memoria para garantizar el tipo correcto
            const sessionId = currentSessionForObs ? currentSessionForObs.id : null;
            const teacherId = currentSessionForObs ? currentSessionForObs.teacher_id : null;

            let payloads = [];

            if (isFullBlock) {
                const type = document.getElementById('obs-form-type').value;
                const discount = document.getElementById('obs-form-discount').value;
                const replLast = document.getElementById('obs-form-replacement-last').value;
                const replFirst = document.getElementById('obs-form-replacement-first').value;
                const description = document.getElementById('obs-form-description').value;

                let replId = null;
                if (type === 'REEMPLAZO') {
                    const datalist = document.getElementById('teachers-datalist');
                    const fullInput = `${replLast}, ${replFirst}`.trim();
                    const matched = Array.from(datalist.options).find(o => o.value === fullInput);
                    if (matched) replId = parseInt(matched.getAttribute('data-id'));
                }

                const sessionIds = currentSessionForObs.session_ids || [sessionId];

                sessionIds.forEach(sid => {
                    payloads.push({
                        session_id: sid,
                        teacher_id: teacherId,
                        type: type,
                        discount_type: discount,
                        replacement_last_name: type === 'REEMPLAZO' ? replLast : null,
                        replacement_first_name: type === 'REEMPLAZO' ? replFirst : null,
                        description: description,
                        start_time: currentSessionForObs.start_time,
                        end_time: currentSessionForObs.end_time
                    });
                });
            } else {
                const slotDivs = document.getElementById('obs-split-mode-container').querySelectorAll('.bg-white.border');
                const mainDescription = "Registro desglosado por horas";

                slotDivs.forEach((div, idx) => {
                    const type = div.querySelector('.obs-slot-type').value;
                    if (type === 'NINGUNA') return; // Skip hours with no incident

                    const replLast = div.querySelector('.obs-slot-replacement-last').value;
                    const replFirst = div.querySelector('.obs-slot-replacement-first').value;
                    const start = div.querySelector('.obs-slot-start').value;
                    const end = div.querySelector('.obs-slot-end').value;

                    let replId = null;
                    if (type === 'REEMPLAZO') {
                        const datalist = document.getElementById('teachers-datalist');
                        const fullInput = `${replLast}, ${replFirst}`.trim();
                        const matched = Array.from(datalist.options).find(o => o.value === fullInput);
                        if (matched) replId = parseInt(matched.getAttribute('data-id'));
                    }

                    payloads.push({
                        session_id: sessionId,
                        teacher_id: teacherId,
                        type: type,
                        discount_type: 'SIMPLE', // Default for split
                        replacement_last_name: type === 'REEMPLAZO' ? replLast : null,
                        replacement_first_name: type === 'REEMPLAZO' ? replFirst : null,
                        description: `${mainDescription} (Hora ${idx + 1})`,
                        start_time: start,
                        end_time: end
                    });
                });
            }

            if (payloads.length === 0) {
                alert("No hay incidencias para registrar.");
                return;
            }

            // Guard: si session_id es null, la fila del RPT no tiene sesión en la BD
            if (payloads.some(p => p.session_id === null || p.session_id === undefined)) {
                alert("⚠️ Esta fila no tiene una sesión registrada en el sistema (session_id nulo).\n\nEsto ocurre cuando el bloque aparece en el RPT de planillas pero no fue importado en el módulo de Horarios. Por favor, verifica la importación del horario para este docente y fecha.");
                return;
            }

            console.log("Enviando payloads:", payloads);

            try {
                // We send one by one as requested (multiples objetos)
                const promises = payloads.map(p => authFetch(`${API_BASE_URL}/api/schedule/observations`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(p)
                }));

                const results = await Promise.all(promises);
                const allOk = results.every(r => r.ok);

                if (allOk) {
                    closeObsRegisterModal();

                    // Bug 1 fix: usar la referencia directa al <tr> guardada al abrir el modal
                    const row = currentRowElementForObs;
                    currentRowElementForObs = null; // limpiar para el próximo uso
                    if (row) {
                        const actionCell = row.querySelector('.action-cell');
                        if (actionCell) {
                            const types = [...new Set(payloads.map(p => p.type))];
                            const label = types.length > 1 ? 'FALTA/REEMP' : types[0];
                            
                            let badgeColor = 'bg-rose-50 text-rose-700 border-rose-200';
                            if (label === 'REEMPLAZO') {
                                badgeColor = 'bg-amber-50 text-amber-700 border-amber-200';
                            } else if (label === 'FALTA/REEMP') {
                                badgeColor = 'bg-indigo-50 text-indigo-700 border-indigo-200';
                            }

                            actionCell.innerHTML = `
                                <span class="${badgeColor} px-2 py-0.5 rounded-lg text-[9px] font-black uppercase tracking-tighter border shadow-sm animate-pulse">
                                    <i class="fa-solid fa-circle-check mr-1 text-[8px]"></i> ${label}
                                </span>
                            `;
                        }
                    } else {
                        searchClassesForObs();
                    }

                    document.getElementById('obs-confirm-modal').classList.remove('hidden');
                } else {
                    alert("Algunas incidencias no pudieron registrarse. Revisa la consola.");
                }
            } catch (e) {
                console.error("Error saving observations:", e);
                alert("Error de conexión al guardar.");
            }
        }

        function closeObsConfirmModal() {
            document.getElementById('obs-confirm-modal').classList.add('hidden');
        }

        async function deleteObservation(obsId) {
            if (!confirm("¿Estás seguro de que deseas eliminar esta incidencia? Esta acción no se puede deshacer de forma sencilla.")) return;

            try {
                const res = await authFetch(`${API_BASE_URL}/api/schedule/observations/${obsId}`, {
                    method: 'DELETE'
                });
                const data = await res.json();

                if (data.success) {
                    alert("Incidencia eliminada con éxito.");
                    // Refrescar vistas
                    loadObsLogs();
                    if (document.getElementById('rpt-planilla-body').innerHTML !== '') {
                        loadRptPlanilla(rptCurrentPage);
                    }
                } else {
                    alert("Error al eliminar: " + data.message);
                }
            } catch (e) {
                console.error("Error deleting observation:", e);
                alert("Error de conexión al eliminar.");
            }
        }

        async function loadObsLogs() {
            const tbody = document.getElementById('obs-logs-body');
            if (!tbody) return;
            tbody.innerHTML = '<tr><td colspan="7" class="px-4 py-12 text-center text-slate-400"><i class="fa-solid fa-spinner fa-spin text-xl mb-2"></i> Cargando logs...</td></tr>';

            try {
                const res = await authFetch(`${API_BASE_URL}/api/schedule/observations/logs`);
                const json = await res.json();
                const logs = json.data || [];

                tbody.innerHTML = '';
                if (logs.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="7" class="px-4 py-12 text-center text-slate-400 italic">No hay registros de auditoría aún.</td></tr>';
                    return;
                }

                logs.forEach(l => {
                    const tr = document.createElement('tr');
                    tr.className = "hover:bg-slate-50 transition-colors border-b border-slate-100 last:border-0";

                    let typeBadge = '';
                    switch (l.type) {
                        case 'FALTA': typeBadge = '<span class="bg-rose-100 text-rose-700 px-2 py-1 rounded text-[10px] font-black underline">FALTA</span>'; break;
                        case 'REEMPLAZO': typeBadge = '<span class="bg-amber-100 text-amber-700 px-2 py-1 rounded text-[10px] font-black underline">REEMPLAZO</span>'; break;
                        case 'VACACIONES': typeBadge = '<span class="bg-indigo-100 text-indigo-700 px-2 py-1 rounded text-[10px] font-black underline">VACACIONES</span>'; break;
                        case 'DESCANSO_MEDICO': typeBadge = '<span class="bg-blue-100 text-blue-700 px-2 py-1 rounded text-[10px] font-black underline">DESC. MÉDICO</span>'; break;
                        default: typeBadge = `<span class="bg-slate-100 text-slate-700 px-2 py-1 rounded text-[10px] font-black">${l.type}</span>`;
                    }

                    tr.innerHTML = `
                        <td class="px-4 py-4 text-xs font-mono text-slate-500">${l.date_record}</td>
                        <td class="px-4 py-4 text-sm font-bold text-indigo-700">${l.user}</td>
                        <td class="px-4 py-4 text-sm text-slate-800">${l.teacher_affected}</td>
                        <td class="px-4 py-4">${typeBadge}</td>
                        <td class="px-4 py-4 text-xs text-slate-600">${l.class_date}</td>
                        <td class="px-4 py-4 text-xs italic text-slate-400 max-w-xs truncate" title="${l.description || ''}">${l.description || '---'}</td>
                        <td class="px-4 py-4 text-right">
                           <button onclick="deleteObservation(${l.id})" class="text-slate-300 hover:text-rose-600 transition-colors p-2" title="Eliminar Incidencia">
                               <i class="fa-solid fa-trash-can"></i>
                           </button>
                        </td>
                    `;
                    tbody.appendChild(tr);
                });
            } catch (e) {
                console.error("Error loading obs logs:", e);
                tbody.innerHTML = '<tr><td colspan="7" class="px-4 py-12 text-center text-rose-500 font-bold">Error al cargar el historial.</td></tr>';
            }
        }

        function toggleConfigMenu() {
            const submenu = document.getElementById('config-submenu');
            const chevron = document.getElementById('config-chevron');
            const isHidden = submenu.classList.contains('hidden');

            if (isHidden) {
                submenu.classList.remove('hidden');
                chevron.classList.add('rotate-180');
            } else {
                submenu.classList.add('hidden');
                chevron.classList.remove('rotate-180');
            }
        }

        // ═══════════════════════════════════════════════
        //  MÓDULO DOCENTES — JavaScript v2
        // ═══════════════════════════════════════════════
        const API_DOC = 'http://127.0.0.1:8000/api/docentes';
        const IMP_PAGE_SIZE = 20;

        let maestraPage = 1, maestraTotalPages = 1;
        let lastMaestraData = []; // Cache de la página actual de la maestra
        let currentMergeData = []; // Docentes seleccionados para fusión
        let sinAsignarPage = 1, sinAsignarTotalPages = 1;
        let importAllRows = [];   // todos los rows del excel
        let importPage = 1, importTotalPages = 1;
        let lastConflicts = [];   // cache del último reprocesamiento

        // ── Tab switcher ─────────────────────────────────
        const DOC_TABS = ['upload-excel', 'maestra', 'sinasignar', 'conflictos'];
        function toggleDocentesTab(tab) {
            DOC_TABS.forEach(t => {
                document.getElementById(`doc-tab-${t}`).classList.toggle('hidden', t !== tab);
                const btn = document.getElementById(`doc-tab-btn-${t}`);
                if (!btn) return;
                if (t === tab) {
                    btn.classList.add('border-indigo-600', 'text-indigo-600');
                    btn.classList.remove('border-transparent', 'text-slate-400');
                } else {
                    btn.classList.remove('border-indigo-600', 'text-indigo-600');
                    btn.classList.add('border-transparent', 'text-slate-400');
                }
            });
            if (tab === 'maestra') loadMaestra(1);
            if (tab === 'sinasignar') loadSinAsignar(1);
            if (tab === 'conflictos') renderConflictos(lastConflicts);
        }

        // ── File input label ─────────────────────────────
        
        
        // --- GLOBAL EXPORTS FOR LEGACY ACROSS HTML ---
        global.loadUploadHistory = loadUploadHistory;
        global.renderScheduleGrid = renderScheduleGrid;
        global.toggleSlotReplacement = toggleSlotReplacement;
        global.loadObsLogs = loadObsLogs;
        global.loadRptPlanilla = loadRptPlanilla;
        global.toggleObsTab = toggleObsTab;
        global.splitIntoPedagogicalHours = splitIntoPedagogicalHours;
        global.editConfig = editConfig;
        global.getFactorMinutes = getFactorMinutes;
        global.closeObsConfirmModal = closeObsConfirmModal;
        global.fillTargetSelect = fillTargetSelect;
        global.loadRptCatalogs = loadRptCatalogs;
        global.deleteConfig = deleteConfig;
        global.openConfigModal = openConfigModal;
        global.exportToExcel = exportToExcel;
        global.toggleDocentesTab = toggleDocentesTab;
        global.closeConfigModal = closeConfigModal;
        global.simulateUpload = simulateUpload;
        global.renderPedagogicalSlots = renderPedagogicalSlots;
        global.openRegisterObsModal = openRegisterObsModal;
        global.changeRptPage = changeRptPage;
        global.changeHistoryPage = changeHistoryPage;
        global.viewUploadReport = viewUploadReport;
        global.closeReportModal = closeReportModal;
        global.loadCatalogs = loadCatalogs;
        global.renderConfigTable = renderConfigTable;
        global.updateFileName = updateFileName;
        global.renderClassroomCalendar = renderClassroomCalendar;
        global.saveConfig = saveConfig;
        global.renderTeacherAgenda = renderTeacherAgenda;
        global.injectBreaks = injectBreaks;
        global.calculateDurationMinutes = calculateDurationMinutes;
        global.handleSedeChange = handleSedeChange;
        global.saveObservation = saveObservation;
        global.setInitialDates = setInitialDates;
        global.toggleObsBlockMode = toggleObsBlockMode;
        global.getCourseColor = getCourseColor;
        global.loadObsTeacherList = loadObsTeacherList;
        global.closeObsRegisterModal = closeObsRegisterModal;
        global.getCalculatedTime = getCalculatedTime;
        global.cleanCycleName = cleanCycleName;
        global.closeOverwriteModal = closeOverwriteModal;
        global.exportSchedule = exportSchedule;
        global.searchClassesForObs = searchClassesForObs;
        global.calculateDuration = calculateDuration;
        global.resetUpload = resetUpload;
        global.loadSchedule = loadSchedule;
        global.deleteObservation = deleteObservation;
        global.handleObsTypeChange = handleObsTypeChange;
        global.confirmOverwrite = confirmOverwrite;

        if(typeof toggleConfigMenu !== 'undefined') global.toggleConfigMenu = toggleConfigMenu;
    
        if(typeof calculateDuration !== 'undefined') global.calculateDuration = calculateDuration;
        if(typeof changeHistoryPage !== 'undefined') global.changeHistoryPage = changeHistoryPage;
        if(typeof changeImportPage !== 'undefined') global.changeImportPage = changeImportPage;
        if(typeof changeMaestraPage !== 'undefined') global.changeMaestraPage = changeMaestraPage;
        if(typeof changeRptPage !== 'undefined') global.changeRptPage = changeRptPage;
        if(typeof changeSinAsignarPage !== 'undefined') global.changeSinAsignarPage = changeSinAsignarPage;
        if(typeof closeConfigModal !== 'undefined') global.closeConfigModal = closeConfigModal;
        if(typeof closeMergeModal !== 'undefined') global.closeMergeModal = closeMergeModal;
        if(typeof closeObsConfirmModal !== 'undefined') global.closeObsConfirmModal = closeObsConfirmModal;
        if(typeof closeObsRegisterModal !== 'undefined') global.closeObsRegisterModal = closeObsRegisterModal;
        if(typeof closeOverwriteModal !== 'undefined') global.closeOverwriteModal = closeOverwriteModal;
        if(typeof closeSinAsignarModal !== 'undefined') global.closeSinAsignarModal = closeSinAsignarModal;
        if(typeof closeStatusModal !== 'undefined') global.closeStatusModal = closeStatusModal;
        if(typeof closeTeacherModal !== 'undefined') global.closeTeacherModal = closeTeacherModal;
        if(typeof closeUsuarioModal !== 'undefined') global.closeUsuarioModal = closeUsuarioModal;
        if(typeof confirmOverwrite !== 'undefined') global.confirmOverwrite = confirmOverwrite;
        if(typeof confirmStatusChange !== 'undefined') global.confirmStatusChange = confirmStatusChange;
        if(typeof executeMerge !== 'undefined') global.executeMerge = executeMerge;
        if(typeof exportSchedule !== 'undefined') global.exportSchedule = exportSchedule;
        if(typeof exportToExcel !== 'undefined') global.exportToExcel = exportToExcel;
        if(typeof getElementById !== 'undefined') global.getElementById = getElementById;
        if(typeof handleObsTypeChange !== 'undefined') global.handleObsTypeChange = handleObsTypeChange;
        if(typeof handleSedeChange !== 'undefined') global.handleSedeChange = handleSedeChange;
        if(typeof loadMaestra !== 'undefined') global.loadMaestra = loadMaestra;
        if(typeof loadRptPlanilla !== 'undefined') global.loadRptPlanilla = loadRptPlanilla;
        if(typeof loadSchedule !== 'undefined') global.loadSchedule = loadSchedule;
        if(typeof loadUploadHistory !== 'undefined') global.loadUploadHistory = loadUploadHistory;
        if(typeof logout !== 'undefined') global.logout = logout;
        if(typeof nav !== 'undefined') global.nav = nav;
        if(typeof openConfigModal !== 'undefined') global.openConfigModal = openConfigModal;
        if(typeof openMergeModal !== 'undefined') global.openMergeModal = openMergeModal;
        if(typeof openTeacherModal !== 'undefined') global.openTeacherModal = openTeacherModal;
        if(typeof openUsuarioModal !== 'undefined') global.openUsuarioModal = openUsuarioModal;
        if(typeof promoteSinAsignar !== 'undefined') global.promoteSinAsignar = promoteSinAsignar;
        if(typeof resetUpload !== 'undefined') global.resetUpload = resetUpload;
        if(typeof runReprocesarHistorico !== 'undefined') global.runReprocesarHistorico = runReprocesarHistorico;
        if(typeof saveConfig !== 'undefined') global.saveConfig = saveConfig;
        if(typeof saveObservation !== 'undefined') global.saveObservation = saveObservation;
        if(typeof saveSinAsignar !== 'undefined') global.saveSinAsignar = saveSinAsignar;
        if(typeof saveTeacher !== 'undefined') global.saveTeacher = saveTeacher;
        if(typeof searchClassesForObs !== 'undefined') global.searchClassesForObs = searchClassesForObs;
        if(typeof selectPrincipal !== 'undefined') global.selectPrincipal = selectPrincipal;
        if(typeof simulateUpload !== 'undefined') global.simulateUpload = simulateUpload;
        if(typeof toggleConfigMenu !== 'undefined') global.toggleConfigMenu = toggleConfigMenu;
        if(typeof toggleDocentesTab !== 'undefined') global.toggleDocentesTab = toggleDocentesTab;
        if(typeof toggleObsBlockMode !== 'undefined') global.toggleObsBlockMode = toggleObsBlockMode;
        if(typeof toggleObsTab !== 'undefined') global.toggleObsTab = toggleObsTab;
        if(typeof uploadDocentesExcel !== 'undefined') global.uploadDocentesExcel = uploadDocentesExcel;
    })(window);

    // ==========================================
    // INITIALIZATION BOOTSTRAP
    // ==========================================
    document.addEventListener('DOMContentLoaded', () => {
        if(window.initApp) window.initApp();
    });


    