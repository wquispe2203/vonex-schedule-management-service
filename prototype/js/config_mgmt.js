import api from './api.js';
import { ENDPOINTS } from './config.js';
import { calculateDurationMinutes, extractList } from './ui_utils.js';

let currentConfigs = {
    recess: [],
    lunch: []
};

export async function loadConfig(type) {
    const endpoint = type === 'recess' ? 'recesos' : 'almuerzos';
    try {
        const response = await api.authFetch(`${ENDPOINTS.CONFIG.BASE}/${endpoint}`);
        
        // REGLA OBLIGATORIA: Log del response completo
        console.log(`[CONFIG_${type.toUpperCase()}] Response recibida:`, response);

        // ✅ USO DE HELPER CENTRALIZADO
        const list = extractList(response);
        console.log(`[CONFIG_${type.toUpperCase()}] LIST:`, list);

        if (response.success && Array.isArray(list)) {
            currentConfigs[type] = list;
            renderConfigTable(type);
        }
    } catch (e) { console.error("Error loading config:", e); }
}

function renderConfigTable(type) {
    const tbody = document.getElementById(`${type}-config-body`);
    if (!tbody) return;
    tbody.innerHTML = '';
    const configs = currentConfigs[type];

    if (configs.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="py-12 text-center text-slate-400 italic">No hay registros configurados</td></tr>';
        return;
    }

    configs.forEach(c => {
        const tr = document.createElement('tr');
        tr.className = "hover:bg-slate-50 transition-colors border-b border-slate-50 text-slate-700 not-italic";
        const dur = calculateDurationMinutes(c.start_time, c.end_time);

        tr.innerHTML = `
            <td class="px-6 py-4 font-bold text-slate-800">${c.description}</td>
            <td class="px-6 py-4 font-mono text-sm">${c.start_time.substring(0, 5)}</td>
            <td class="px-6 py-4 font-mono text-sm">${c.end_time.substring(0, 5)}</td>
            <td class="px-6 py-4 text-center">
                <span class="bg-indigo-50 text-indigo-700 px-3 py-1 rounded-full text-xs font-black">${dur} min</span>
            </td>
            <td class="px-6 py-4 text-right space-x-2">
                <button data-action="editConfig('${type}', '${c.id}')" class="text-indigo-600 hover:text-indigo-800 p-2"><i class="fa-solid fa-pen-to-square"></i></button>
                <button data-action="deleteConfig('${type}', '${c.id}')" class="text-rose-600 hover:text-rose-800 p-2"><i class="fa-solid fa-trash"></i></button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

export function openConfigModal(type, id = null) {
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

    calculateDurationInModal();
    document.getElementById('config-modal').classList.remove('hidden');
}

export function calculateDurationInModal() {
    const start = document.getElementById('config-start').value;
    const end = document.getElementById('config-end').value;
    const durLabel = document.getElementById('config-duration');
    if (start && end && durLabel) {
        const diff = calculateDurationMinutes(start, end);
        durLabel.innerText = `${diff} min`;
        if (diff <= 0) durLabel.classList.add('text-rose-600');
        else durLabel.classList.remove('text-rose-600');
    }
}

export function closeConfigModal() {
    document.getElementById('config-modal')?.classList.add('hidden');
}

export async function saveConfig() {
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
    const url = id ? `${ENDPOINTS.CONFIG.BASE}/${endpoint}/${id}` : `${ENDPOINTS.CONFIG.BASE}/${endpoint}`;

    try {
        const response = await api.authFetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        // REGLA OBLIGATORIA: Log del response completo
        console.log(`[CONFIG_SAVE] Response recibida:`, response);

        if (response.success) {
            closeConfigModal();
            loadConfig(type);
            alert("Configuración guardada con éxito");
        }
    } catch (e) {
        alert("Error de conexión");
    }
}

export async function deleteConfig(type, id) {
    if (!confirm("¿Está seguro de eliminar este registro?")) return;
    const endpoint = type === 'recess' ? 'recesos' : 'almuerzos';
    try {
        const data = await api.authFetch(`${ENDPOINTS.CONFIG.BASE}/${endpoint}/${id}`, { method: 'DELETE' });
        if (data.success) loadConfig(type);
    } catch (e) { console.error("Error deleting config:", e); }
}

export function editConfig(type, id) {
    openConfigModal(type, id);
}
