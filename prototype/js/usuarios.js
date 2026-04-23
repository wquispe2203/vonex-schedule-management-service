// Gestión de Usuarios Module - ES6
import api from './api.js';
import { ENDPOINTS } from './config.js';

export async function loadUsuarios() {
    const tbody = document.getElementById('usuarios-body');
    if (!tbody) return;
    tbody.innerHTML = '<tr><td colspan="5" class="py-12 text-center text-slate-400 font-medium">Cargando usuarios...</td></tr>';

    try {
        // authFetch ya devuelve el JSON parseado y lanza error si !res.ok
        const json = await api.authFetch(ENDPOINTS.USERS.BASE);
        const users = json.data || json || []; // Flexibilidad para diferentes formatos de respuesta
        tbody.innerHTML = '';

        if (users.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="py-12 text-center text-slate-400 italic">No hay otros usuarios registrados</td></tr>';
            return;
        }

        const currentUserId = localStorage.getItem('user_id');

        users.forEach(u => {
            const tr = document.createElement('tr');
            tr.className = "hover:bg-slate-50 transition-colors border-b border-slate-50";
            const rolesHtml = u.roles.map(r => `<span class="bg-indigo-50 text-indigo-700 px-2 py-0.5 rounded text-[10px] font-black uppercase tracking-tight mr-1">${r.name}</span>`).join('');
            
            tr.innerHTML = `
                <td class="px-6 py-4">
                    <div class="flex items-center gap-3">
                        <div class="w-8 h-8 rounded-full bg-slate-200 flex items-center justify-center text-slate-500 font-black text-xs uppercase">${u.full_name?.substring(0, 2)}</div>
                        <div>
                            <div class="font-bold text-slate-800 text-sm">${u.full_name}</div>
                            <div class="text-[10px] text-slate-400 font-bold uppercase tracking-widest">${u.email}</div>
                        </div>
                    </div>
                </td>
                <td class="px-6 py-4">${rolesHtml}</td>
                <td class="px-6 py-4"><span class="text-[10px] font-mono text-slate-400">${u.id}</span></td>
                <td class="px-6 py-4 text-center">
                    ${u.is_active ? '<i class="fa-solid fa-circle-check text-emerald-500"></i>' : '<i class="fa-solid fa-circle-xmark text-slate-300"></i>'}
                </td>
                <td class="px-6 py-4 text-right">
                    ${u.id !== currentUserId ? `<button data-action="deleteUsuario('${u.id}')" class="text-rose-400 hover:text-rose-600 p-2 transition-colors"><i class="fa-solid fa-trash-can"></i></button>` : ''}
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (e) {
        console.error("Error loading users:", e);
        tbody.innerHTML = `<tr><td colspan="5" class="py-12 text-center text-rose-500">Error al cargar usuarios: ${e.message}</td></tr>`;
    }
}

export function openUsuarioModal() {
    const title = document.getElementById('user-modal-title');
    if (title) title.innerText = "Crear Nuevo Usuario";
    const form = document.getElementById('user-form');
    if (form) form.reset();
    const modal = document.getElementById('user-modal');
    if (modal) modal.classList.remove('hidden');
}

export function closeUsuarioModal() {
    const modal = document.getElementById('user-modal');
    if (modal) modal.classList.add('hidden');
}

export async function saveUsuario() {
    const payload = {
        email: document.getElementById('user-email').value,
        full_name: document.getElementById('user-name').value,
        password: document.getElementById('user-pass').value,
        is_active: true,
        role_ids: []
    };

    const roles = ['ADMINISTRADOR', 'SISTEMAS', 'PLANILLAS', 'BIENESTAR'];
    roles.forEach(role => {
        const checkbox = document.getElementById(`role-${role.toLowerCase()}`);
        if (checkbox && checkbox.checked) {
            payload.role_ids.push(role);
        }
    });

    if (!payload.email || !payload.full_name || !payload.password || payload.role_ids.length === 0) {
        alert("Completa todos los campos y selecciona al menos un rol.");
        return;
    }

    try {
        await api.authFetch(ENDPOINTS.USERS.BASE, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        closeUsuarioModal();
        loadUsuarios();
        alert("Usuario creado correctamente");
    } catch (e) {
        console.error("Error saving user:", e);
        alert("Error: " + e.message);
    }
}

export async function deleteUsuario(id) {
    if (!confirm("¿Desea eliminar este usuario permanentemente?")) return;
    try {
        await api.authFetch(`${ENDPOINTS.USERS.BASE}/${id}`, { method: 'DELETE' });
        loadUsuarios();
        alert("Usuario eliminado");
    } catch (e) {
        console.error("Error deleting user:", e);
        alert("Error al eliminar: " + e.message);
    }
}
