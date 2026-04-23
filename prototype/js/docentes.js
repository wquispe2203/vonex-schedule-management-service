// Docentes Module - ES6
import api from './api.js';

export const docentes = {
    async list(params = {}) {
        const query = new URLSearchParams(params).toString();
        // Nota: Se podría usar ENDPOINTS.DOCENTES.BASE pero para mantener compatibilidad con este módulo ES6:
        return await api.authFetch(`/api/docentes?${query}`);
    },

    async get(id) {
        return await api.authFetch(`/api/docentes/${id}`);
    },

    async update(id, data) {
        return await api.authFetch(`/api/docentes/${id}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
    }
    // ... otros métodos según sea necesario
};

export function setupDocentesHandlers() {
    // Aquí registramos eventos para el módulo de docentes (delegación de eventos)
    document.addEventListener('click', async (e) => {
        const btn = e.target.closest('button');
        if (!btn) return;

        // Ejemplo: Botón editar en la tabla maestra
        if (btn.classList.contains('edit-teacher-btn')) {
            const id = btn.dataset.id;
            console.log(`[DOCENTES] Editando ${id}`);
            // Lógica para abrir modal, etc.
        }
    });
}
