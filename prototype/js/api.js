import { API_BASE_URL } from './config.js';

const api = {
    getToken: () => localStorage.getItem('token'),
    setToken: (token) => localStorage.setItem('token', token),
    clearToken: () => localStorage.removeItem('token'),

    async authFetch(endpoint, options = {}) {
        const token = this.getToken();
        
        // El merge de headers permite que el cliente pase su propio X-Request-ID
        const headers = {
            'X-Request-ID': crypto.randomUUID(),
            ...options.headers
        };

        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        // Construir URL final (Protección contra doble URL y rutas relativas)
        const url = endpoint.startsWith('http') 
            ? endpoint 
            : `${API_BASE_URL}${endpoint}`;
        
        try {
            const res = await fetch(url, { ...options, headers });
            
            // 🚨 MANEJO GLOBAL DE 401 (UNAUTHORIZED)
            if (res.status === 401) {
                this.clearToken();
                console.error("[API] Sesión expirada o inválida (401)");
                window.location.reload(); 
                return;
            }

            if (!res.ok) {
                const text = await res.text();
                let data = {};
                try { data = text ? JSON.parse(text) : {}; } catch { data = { detail: text }; }
                throw new Error(data.detail || `Error HTTP ${res.status}`);
            }

            // Si el llamador pide la respuesta cruda (ej. para blobs)
            if (options.rawResponse) return res;

            // 🛡️ SAFE PARSE (ANTI-CRASH)
            const text = await res.text();
            let data = {};
            try {
                data = text ? JSON.parse(text) : {};
            } catch (e) {
                data = { raw: text };
                console.warn("[API] Response is not JSON:", text.substring(0, 50));
            }
            
            return data;
        } catch (error) {
            console.error(`[API ERROR] ${endpoint}:`, error);
            throw error;
        }
    }
};

export default api;
