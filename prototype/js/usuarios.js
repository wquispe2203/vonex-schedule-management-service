import api from './api.js';
import { ENDPOINTS } from './config.js';
import { extractList } from './ui_utils.js';

// State Encapsulado del Módulo
let loadedUsers = [];
let globalRoles = [];
let globalPermissions = [];
let currentResetUserId = null;

let usuariosInitPromise = null;

/**
 * [USERS MODULE INIT] Punto de entrada inicial del ciclo de vida del módulo.
 */
export async function initUsuarios(force = false) {
    if (force) {
        console.log('[USERS FORCE REFRESH] Reseteando usuariosInitPromise para forzar recarga reactiva.');
        usuariosInitPromise = null;
    }

    if (usuariosInitPromise) {
        console.log('[PROMISE LOCK REUSED] initUsuarios');
        return usuariosInitPromise;
    }

    console.log('[PROMISE LOCK ACQUIRED] initUsuarios');
    let success = false;

    usuariosInitPromise = (async () => {
        console.log("[USERS MODULE INIT] Iniciando ciclo de vida de usuarios y seguridad.");
        
        const tbody = document.getElementById('usuarios-tbody');
        if (!tbody) {
            console.error("[USERS ERROR] Elemento 'usuarios-tbody' no encontrado en el DOM.");
            throw new Error("Element 'usuarios-tbody' missing");
        }
        
        tbody.innerHTML = `<tr><td colspan="5" class="px-5 py-8 text-center text-indigo-500 font-bold">
            <i class="fa-solid fa-spinner fa-spin mr-2"></i>Cargando usuarios...
        </td></tr>`;

        try {
            // 1. Asegurar que los roles existan para los chips de la tabla y para futuros formularios
            await loadRoles();

            // 2. Realizar el fetch de usuarios del backend
            console.log("[USERS REFETCH] Consultando cuentas de usuario activas a la API...");
            const response = await api.authFetch(ENDPOINTS.USERS.BASE);
            
            // Extraer lista con helper centralizado
            const users = extractList(response);
            loadedUsers = users;

            // 3. Renderizar en el DOM
            renderUsuarios(users);
            console.log("[USERS TABLE UPDATED] Tabla de usuarios dibujada exitosamente en la SPA.");
            
            success = true;
            console.log("[PROMISE LOCK RELEASED] initUsuarios successfully initialized");
            console.log("[USERS MODULE READY] Módulo de usuarios inicializado y listo.");
        } catch (error) {
            console.error("[USERS ERROR] Error crítico inicializando el módulo:", error);
            tbody.innerHTML = `<tr><td colspan="5" class="px-5 py-8 text-center text-rose-500 font-black">
                Error al inicializar: ${error.message}
            </td></tr>`;
            throw error;
        } finally {
            if (!success) {
                console.warn("[PROMISE LOCK RESET] Releasing failed initUsuarios promise.");
                usuariosInitPromise = null;
            }
        }
    })();

    return usuariosInitPromise;
}

/**
 * [USERS LOADED] Dibuja la tabla de usuarios en el DOM.
 */
export function renderUsuarios(users) {
    const tbody = document.getElementById('usuarios-tbody');
    if (!tbody) return;

    tbody.innerHTML = '';

    if (!Array.isArray(users) || users.length === 0) {
        tbody.innerHTML = `<tr><td colspan="5" class="px-5 py-12 text-center text-slate-400 italic">
            No se encontraron usuarios registrados.
        </td></tr>`;
        return;
    }

    users.forEach(u => {
        const statusUI = u.is_active
            ? `<span class="bg-emerald-100 text-emerald-700 text-[10px] px-2 py-1 rounded-full font-black">ACTIVO</span>`
            : `<span class="bg-rose-100 text-rose-700 text-[10px] px-2 py-1 rounded-full font-black">BLOQUEADO</span>`;

        const rolesUI = (u.roles || []).map(r => 
            `<span class="text-[10px] border border-slate-300 text-slate-600 bg-white px-2 py-0.5 rounded-lg font-bold">${r.name}</span>`
        ).join(' ') || '<em class="text-xs text-slate-400">Sin roles</em>';

        const row = document.createElement('tr');
        row.className = "hover:bg-slate-50 transition-colors border-b border-slate-100 text-slate-700";
        row.innerHTML = `
            <td class="px-5 py-4">
                <p class="font-bold text-slate-800">${u.apellidos || ''}, ${u.nombres || ''}</p>
                <p class="text-xs text-slate-500">${u.area || '-'}</p>
            </td>
            <td class="px-5 py-4 font-medium text-slate-700">${u.username}</td>
            <td class="px-5 py-4"><div class="flex gap-1 flex-wrap">${rolesUI}</div></td>
            <td class="px-5 py-4">${statusUI}</td>
            <td class="px-5 py-4 text-right space-x-2 whitespace-nowrap">
                <button data-action="openResetPwdModal('${u.id}', '${u.username}')" class="text-rose-600 hover:bg-rose-50 border border-rose-100 font-bold px-3 py-1.5 rounded-lg text-[10px] uppercase tracking-tighter" title="Resetear Contraseña">
                    <i class="fa-solid fa-key"></i>
                </button>
                <button data-action="editUsuario('${u.id}')" class="bg-indigo-50 text-indigo-700 hover:bg-indigo-100 font-bold px-3 py-1.5 rounded-lg text-xs">
                    <i class="fa-solid fa-pen"></i> Editar
                </button>
                ${u.is_active && api.hasPermission('eliminar_usuarios') ? `<button data-action="deleteUsuario('${u.id}')" class="bg-rose-50 text-rose-700 hover:bg-rose-100 font-bold px-3 py-1.5 rounded-lg text-xs" title="Desactivar"><i class="fa-solid fa-ban"></i></button>` : ''}
            </td>
        `;
        tbody.appendChild(row);
    });

    console.log(`[USERS LOADED] Renderizadas exitosamente ${users.length} cuentas de usuario en el DOM.`);
}

/**
 * Carga la lista maestra de Roles.
 */
export async function loadRoles() {
    try {
        const res = await api.authFetch('/api/roles');
        globalRoles = extractList(res);
    } catch (error) {
        console.error("[USERS ERROR] Error al cargar roles del sistema:", error);
    }
}

/**
 * Carga la lista maestra de Permisos.
 */
export async function loadPermissions() {
    try {
        const res = await api.authFetch('/api/permissions');
        globalPermissions = extractList(res);
    } catch (error) {
        console.error("[USERS ERROR] Error al cargar permisos del sistema:", error);
    }
}

/**
 * Renderiza checkboxes de asignación de roles en el modal de usuario.
 */
function buildRolesCheckboxes(activeIds = []) {
    const container = document.getElementById('usr-roles-container');
    if (!container) return;
    
    container.innerHTML = '';
    globalRoles.forEach(r => {
        const isChecked = activeIds.includes(r.id) ? 'checked' : '';
        container.innerHTML += `
            <label class="flex items-center gap-2 cursor-pointer bg-slate-50 p-2.5 rounded-lg border border-slate-200 hover:bg-white transition-all select-none">
                <input type="checkbox" name="rol_assign" value="${r.id}" ${isChecked} class="rounded border-slate-300 text-indigo-600 focus:ring-indigo-500 w-4 h-4">
                <span class="text-[10px] font-black text-slate-700 uppercase tracking-wider">${r.name}</span>
            </label>
        `;
    });
    console.log("[USERS EVENT BIND] Eventos de asignación de checkboxes de rol generados.");
}

/**
 * [USERS MODAL OPEN] Abre modal en modo creación.
 */
export function openUsuarioModal() {
    console.log("[USERS MODAL OPEN] Abriendo modal para registro de nuevo usuario.");
    const form = document.getElementById('usuario-form');
    if (form) form.reset();
    
    document.getElementById('usr-id').value = '';
    document.getElementById('usuario-modal-title').innerText = 'Registrar Nuevo Usuario';
    
    const pwdInput = document.getElementById('usr-password');
    if (pwdInput) pwdInput.required = true;
    
    const pwdContainer = document.getElementById('usr-pwd-container');
    if (pwdContainer) pwdContainer.style.display = 'block';

    buildRolesCheckboxes([]);
    document.getElementById('usuario-modal').classList.remove('hidden');
}

/**
 * [USERS MODAL OPEN] Abre modal en modo edición de un usuario existente.
 */
export function editUsuario(id) {
    console.log(`[USERS MODAL OPEN] Abriendo modal de edición para el usuario ID: ${id}`);
    const u = loadedUsers.find(usr => usr.id === id);
    if (!u) {
        console.error(`[USERS ERROR] No se encontró el usuario local con ID: ${id}`);
        return;
    }

    const form = document.getElementById('usuario-form');
    if (form) form.reset();

    document.getElementById('usr-id').value = u.id;
    document.getElementById('usr-nombres').value = u.nombres || '';
    document.getElementById('usr-apellidos').value = u.apellidos || '';
    
    // ✅ COMPATIBILIDAD RETROACTIVA: Aceptar 'usr-email' como source of truth mapeando a 'u.username'
    document.getElementById('usr-email').value = u.username || '';
    document.getElementById('usr-area').value = u.area || '';

    document.getElementById('usuario-modal-title').innerText = 'Modificar Cuenta';
    
    const pwdInput = document.getElementById('usr-password');
    if (pwdInput) pwdInput.required = false;
    
    const pwdContainer = document.getElementById('usr-pwd-container');
    if (pwdContainer) pwdContainer.style.display = 'none';

    const activeRoleIds = (u.roles || []).map(r => r.id);
    buildRolesCheckboxes(activeRoleIds);

    document.getElementById('usuario-modal').classList.remove('hidden');
}

/**
 * [USERS MODAL CLOSE] Cierra el modal de usuario.
 */
export function closeUsuarioModal() {
    console.log("[USERS MODAL CLOSE] Cerrando modal de usuario.");
    document.getElementById('usuario-modal').classList.add('hidden');
}

/**
 * [USERS SAVE] / [USERS UPDATE] Recolecta datos y persiste en la API.
 */
export async function saveUsuario(e) {
    if (e && e.preventDefault) e.preventDefault();

    const btn = document.getElementById('usr-save-btn');
    const origContent = btn.innerHTML;
    
    const id = document.getElementById('usr-id').value;
    
    // ✅ CAPTURA DOM CON IMPACTO CERO: 'usr-email' mapea lógicamente a 'username' del Payload
    const payload = {
        username: document.getElementById('usr-email').value.trim(),
        nombres: document.getElementById('usr-nombres').value.trim(),
        apellidos: document.getElementById('usr-apellidos').value.trim(),
        area: document.getElementById('usr-area').value.trim()
    };

    // Validaciones básicas frontend
    if (!payload.username || !payload.nombres || !payload.apellidos) {
        alert("Por favor, complete los campos obligatorios (Nombres, Apellidos y Correo).");
        return;
    }

    if (!payload.username.endsWith('@vonex.edu.pe')) {
        alert("El correo institucional debe terminar en @vonex.edu.pe");
        return;
    }

    // Si es nuevo usuario, la contraseña es obligatoria
    if (!id) {
        const rawPwd = document.getElementById('usr-password').value;
        if (!rawPwd || rawPwd.length < 6) {
            alert("La contraseña provisional es requerida y debe tener mínimo 6 caracteres.");
            return;
        }
        payload.password = rawPwd;
    }

    console.log("[USERS PAYLOAD VERIFIED] Structuring final payload for API transport:", payload);

    try {
        btn.disabled = true;
        btn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin mr-2"></i>Procesando...';

        let savedUserId = id;

        if (id) {
            // Acción de Actualización
            console.log(`[USERS UPDATE] Enviando actualización del usuario ${id} a la API...`);
            const updateRes = await api.authFetch(`${ENDPOINTS.USERS.BASE}/${id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            console.log("[USERS UPDATE] Respuesta del backend recibida:", updateRes);
        } else {
            // Acción de Creación
            console.log("[USERS SAVE] Registrando nuevo usuario en la API...");
            const createRes = await api.authFetch(ENDPOINTS.USERS.BASE, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            console.log("[USERS SAVE] Usuario creado exitosamente en Backend:", createRes);
            // Obtener el ID generado (viene en response.data.id)
            savedUserId = createRes.data?.id;
        }

        // 2. Guardar la relación de Roles asignados al usuario
        if (savedUserId) {
            const checkedRoles = Array.from(document.querySelectorAll('input[name="rol_assign"]:checked'));
            const roleIds = checkedRoles.map(cb => cb.value); // UUIDs directos del DOM
            
            console.log(`[USERS UPDATE] Actualizando matriz de roles para usuario ID ${savedUserId}:`, roleIds);
            
            await api.authFetch(`${ENDPOINTS.USERS.BASE}/${savedUserId}/roles`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ role_ids: roleIds })
            });
        }

        // Finalizar y recargar reactivamente
        closeUsuarioModal();
        // Recargar listado reactivamente
        await initUsuarios(true);
        
        alert("✅ Usuario guardado correctamente.");
    } catch (error) {
        console.error("[USERS ERROR] Error guardando usuario:", error);
        alert(`❌ Error guardando usuario: ${error.message}`);
    } finally {
        btn.disabled = false;
        btn.innerHTML = origContent;
    }
}

/**
 * [USERS DELETE] Desactiva un usuario.
 */
export async function deleteUsuario(id) {
    if (!confirm("¿Está seguro de desactivar y bloquear el acceso a este usuario?")) return;
    
    console.log(`[USERS DELETE] Solicitando deactivación de usuario ID: ${id}`);
    try {
        await api.authFetch(`${ENDPOINTS.USERS.BASE}/${id}`, { method: 'DELETE' });
        console.log("[USERS DELETE] Usuario desactivado en Backend correctamente.");
        // Recargar listado reactivamente
        await initUsuarios(true);
    } catch (error) {
        console.error("[USERS ERROR] No se pudo desactivar el usuario:", error);
        alert(`❌ Error al desactivar usuario: ${error.message}`);
    }
}

/**
 * Conmuta entre las sub-pestañas de Lista de Usuarios y Matriz RBAC.
 */
export function toggleUsuariosTab(tab) {
    console.log(`[USERS ROUTE] Cambiando a sub-vista de usuarios: ${tab.toUpperCase()}`);
    
    document.querySelectorAll('.usr-tab-btn').forEach(b => {
        b.classList.remove('border-indigo-600', 'text-indigo-600');
        b.classList.add('border-transparent', 'text-slate-400');
    });
    
    const targetBtn = document.getElementById(`usr-tab-btn-${tab}`);
    if (targetBtn) {
        targetBtn.classList.add('border-indigo-600', 'text-indigo-600');
        targetBtn.classList.remove('border-transparent', 'text-slate-400');
    }

    const listTab = document.getElementById('usr-tab-list');
    const rbacTab = document.getElementById('usr-tab-rbac');
    
    if (tab === 'list') {
        if (listTab) listTab.classList.remove('hidden');
        if (rbacTab) rbacTab.classList.add('hidden');
    } else if (tab === 'rbac') {
        if (listTab) listTab.classList.add('hidden');
        if (rbacTab) rbacTab.classList.remove('hidden');
        loadRBACMatrix();
    }
}

/**
 * [USERS RBAC MATRIX] Carga y renderiza dinámicamente la matriz de permisos por rol.
 */
async function loadRBACMatrix() {
    console.log("[USERS RBAC MATRIX] Iniciando construcción cruzada de la matriz de permisos.");
    
    const thead = document.getElementById('rbac-thead');
    const tbody = document.getElementById('rbac-tbody');
    if (!thead || !tbody) return;

    thead.innerHTML = '<tr><th class="px-6 py-4 text-indigo-500 font-bold">Cargando...</th></tr>';
    tbody.innerHTML = '';

    try {
        // Fetch paralelo de roles y permisos para construir la grilla
        await Promise.all([loadRoles(), loadPermissions()]);

        // 1. Render del Cabezal (Roles del sistema)
        let headerHTML = `<tr>
            <th class="px-6 py-4 text-xs font-black text-slate-500 uppercase tracking-widest bg-slate-50 sticky left-0 z-10 w-72 border-b border-slate-200">
                Permisos / Funcionalidad
            </th>`;
        
        globalRoles.forEach(r => {
            const isStructural = ['SUPERADMIN', 'SISTEMAS'].includes(r.name.toUpperCase());
            const canDelete = api.hasPermission('eliminar_roles') && !isStructural;
            
            headerHTML += `<th class="px-4 py-4 text-center text-[10px] font-black text-slate-600 uppercase tracking-tighter w-36 border-l border-b border-slate-200">
                <div class="flex flex-col items-center gap-2">
                    ${r.name}
                    ${canDelete ? `<button data-action="deleteRole('${r.id}', '${r.name}')" class="text-slate-300 hover:text-rose-600 transition-colors" title="Eliminar Rol"><i class="fa-solid fa-trash-can"></i></button>` : ''}
                </div>
            </th>`;
        });
        headerHTML += `</tr>`;
        thead.innerHTML = headerHTML;

        // 2. Render de Filas (Permisos cruzados)
        if (globalPermissions.length === 0) {
            tbody.innerHTML = `<tr><td colspan="${globalRoles.length + 1}" class="px-6 py-12 text-center text-slate-400 italic">No hay permisos declarados en el sistema.</td></tr>`;
            return;
        }

        globalPermissions.forEach(p => {
            let rowHTML = `<tr class="hover:bg-slate-50 transition-colors">
                <td class="px-6 py-4 bg-white sticky left-0 z-10 border-r border-slate-100 shadow-[2px_0_5px_rgba(0,0,0,0.01)]">
                    <p class="font-extrabold text-slate-800 text-sm">${p.description || p.code}</p>
                    <p class="text-[10px] text-slate-400 font-mono">${p.code}</p>
                </td>`;
            
            globalRoles.forEach(r => {
                // Verificar si el rol ya posee este permiso (comparamos por code o id)
                const hasPerm = (r.permissions || []).some(rp => rp.id === p.id);
                rowHTML += `<td class="px-4 py-4 text-center border-l border-slate-100">
                    <input type="checkbox" class="rbac-check w-5 h-5 rounded border-slate-300 text-emerald-600 focus:ring-emerald-500 cursor-pointer"
                           data-role-id="${r.id}" data-perm-id="${p.id}" ${hasPerm ? 'checked' : ''}>
                </td>`;
            });
            
            rowHTML += `</tr>`;
            tbody.insertAdjacentHTML('beforeend', rowHTML);
        });

        console.log(`[USERS RBAC RENDER] Matriz visualizada con ${globalRoles.length} roles y ${globalPermissions.length} permisos.`);
    } catch (error) {
        console.error("[USERS ERROR] Falló la construcción de matriz RBAC:", error);
        thead.innerHTML = '<tr><th class="px-6 py-4 text-rose-500 font-black">Error al cargar matriz</th></tr>';
    }
}

/**
 * Persiste en masa los cambios realizados en la Matriz de Permisos.
 */
export async function saveRolePermissions() {
    const btn = document.getElementById('btn-save-rbac');
    if (!btn) return;
    
    const origInner = btn.innerHTML;
    
    try {
        btn.disabled = true;
        btn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin mr-2"></i>Guardando...';

        const checkBoxes = document.querySelectorAll('.rbac-check');
        const mapping = {};

        // Agrupar arrays de ids de permisos por id de rol
        checkBoxes.forEach(c => {
            const roleId = c.dataset.roleId;
            const permId = c.dataset.permId;
            if (!mapping[roleId]) mapping[roleId] = [];
            if (c.checked) {
                mapping[roleId].push(permId);
            }
        });

        console.log("[USERS RBAC MATRIX] Persistiendo asignación masiva de permisos por rol...", mapping);

        // Generar peticiones en paralelo por cada rol
        const requests = Object.entries(mapping).map(([roleId, permIds]) => {
            return api.authFetch(`/api/roles/${roleId}/permissions`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ permission_ids: permIds })
            });
        });

        await Promise.all(requests);
        console.log("[USERS RBAC MATRIX] Sincronización de permisos exitosa en base de datos.");
        alert("✅ Matriz de permisos actualizada con éxito para todos los roles.");
        
        // Volver a pintar para refrescar datos en la memoria local
        await loadRBACMatrix();
    } catch (error) {
        console.error("[USERS ERROR] Error al persistir matriz de permisos:", error);
        alert(`❌ Error al guardar matriz de permisos: ${error.message}`);
    } finally {
        btn.disabled = false;
        btn.innerHTML = origInner;
    }
}

// --- BLOQUE: RESTABLECER CONTRASEÑA (ADMIN) ---

/**
 * [USERS MODAL OPEN] Abre el modal de reseteo de password.
 */
export function openResetPwdModal(id, username) {
    console.log(`[USERS MODAL OPEN] Abriendo diálogo de reset password para el usuario: ${username}`);
    currentResetUserId = id;
    
    const userSpan = document.getElementById('reset-pwd-user');
    if (userSpan) userSpan.textContent = username;
    
    const input = document.getElementById('new-pwd-input');
    if (input) input.value = '';
    
    const modal = document.getElementById('reset-pwd-modal');
    if (modal) modal.classList.remove('hidden');
}

/**
 * [USERS MODAL CLOSE] Cierra el diálogo de reseteo.
 */
export function closeResetPwdModal() {
    console.log("[USERS MODAL CLOSE] Cerrando modal de reset password.");
    const modal = document.getElementById('reset-pwd-modal');
    if (modal) modal.classList.add('hidden');
}

/**
 * [USERS PASSWORD RESET] Valida y despacha la solicitud de cambio forzado de contraseña.
 */
export async function confirmResetPassword() {
    const input = document.getElementById('new-pwd-input');
    if (!input) return;
    
    const newPwd = input.value.trim();
    if (!newPwd || newPwd.length < 6) {
        alert("La nueva contraseña es requerida y debe poseer al menos 6 caracteres.");
        return;
    }

    const btn = document.getElementById('btn-confirm-reset-pwd');
    const origContent = btn ? btn.innerHTML : '';

    try {
        if (btn) {
            btn.disabled = true;
            btn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin mr-2"></i>Actualizando...';
        }

        console.log(`[USERS PASSWORD RESET] Solicitando cambio forzado de clave para el usuario ID ${currentResetUserId}...`);
        
        const res = await api.authFetch(`${ENDPOINTS.USERS.BASE}/${currentResetUserId}/password`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ new_password: newPwd })
        });

        console.log("[USERS PASSWORD RESET] Contraseña renovada con éxito.");
        alert("✅ Contraseña restablecida correctamente.");
        closeResetPwdModal();
    } catch (error) {
        console.error("[USERS ERROR] Error restableciendo contraseña:", error);
        alert(`❌ Error al restablecer contraseña: ${error.message}`);
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = origContent;
        }
    }
}

/**
 * Abre el modal para la creación de un nuevo Rol de sistema.
 */
export function openRoleModal() {
    const modal = document.getElementById('role-modal');
    if (modal) modal.classList.remove('hidden');
    const input = document.getElementById('role-new-name');
    if (input) {
        input.value = '';
        input.focus();
    }
}

/**
 * Cierra el modal de nuevo Rol.
 */
export function closeRoleModal() {
    const modal = document.getElementById('role-modal');
    if (modal) modal.classList.add('hidden');
}

/**
 * Envía la petición para crear un nuevo rol en la base de datos.
 */
export async function saveNewRole() {
    const input = document.getElementById('role-new-name');
    if (!input) return;
    
    const name = input.value.trim().toUpperCase();
    if (!name) {
        alert("Por favor, ingresa un nombre válido para el nuevo rol.");
        return;
    }
    
    const btn = document.getElementById('btn-save-new-role');
    const origHtml = btn ? btn.innerHTML : '';
    
    try {
        if (btn) {
            btn.disabled = true;
            btn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin mr-2"></i>Guardando...';
        }
        
        console.log(`[USERS RBAC NEW ROLE] Iniciando registro de rol: ${name}`);
        
        const res = await api.authFetch('/api/roles', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: name })
        });
        
        console.log("[USERS RBAC NEW ROLE] Servidor confirmó la creación del rol:", res);
        alert(`✅ El rol "${name}" fue creado exitosamente.`);
        closeRoleModal();
        
        // Refrescar la matriz para desplegar la nueva columna del rol
        loadRBACMatrix();
    } catch (error) {
        console.error("[USERS ERROR] Falló el registro del rol:", error);
        alert(`❌ Error al crear rol: ${error.message}`);
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = origHtml;
        }
    }
}
/**
 * [USERS RBAC DELETE ROLE] Ejecuta la eliminación de un rol tras validar salvaguardas.
 */
export async function deleteRole(roleId, roleName) {
    console.log(`[ROLE DELETE CASCADE CHECK] Initiating deletion workflow for: ${roleName}`);
    
    // 1. Safeguard: Structural Roles (Extra check despite UI gating)
    const protectedNames = ['SUPERADMIN', 'SISTEMAS'];
    if (protectedNames.includes(roleName.toUpperCase())) {
        console.warn(`[ROLE DELETE BLOCKED] Attempt to delete structural role: ${roleName}`);
        alert("❌ No se puede eliminar un rol estructural del sistema.");
        return;
    }

    // 2. Safeguard: Active Users check
    const usersWithRole = loadedUsers.filter(u => (u.roles || []).some(r => r.id === roleId));
    if (usersWithRole.length > 0) {
        console.warn(`[ROLE DELETE BLOCKED] Role "${roleName}" has ${usersWithRole.length} active users.`);
        alert(`❌ El rol "${roleName}" tiene ${usersWithRole.length} usuarios asignados. Desasigne a los usuarios antes de eliminar el rol.`);
        return;
    }

    if (!confirm(`¿Está seguro de eliminar permanentemente el rol "${roleName}"?\n\nEsta acción no se puede deshacer y eliminará todas sus asociaciones en la matriz RBAC.`)) {
        return;
    }

    try {
        console.log(`[ROLE DELETE SAFE] Proceeding with API deletion for role: ${roleId}`);
        await api.authFetch(`/api/roles/${roleId}`, { method: 'DELETE' });
        
        console.log("[ROLE DELETE SUCCESS] Role purged from system.");
        alert(`✅ Rol "${roleName}" eliminado correctamente.`);
        
        // Refrescar estado local y matriz
        await loadRoles();
        await loadRBACMatrix();
    } catch (error) {
        console.error("[USERS ERROR] Failed to delete role:", error);
        alert(`❌ Error al eliminar rol: ${error.message}`);
    }
}

