import { API_BASE_URL, ENDPOINTS } from './config.js';

let isUnauthorized = false;

const api = {
    getToken: () => localStorage.getItem('token'),
    setToken: (token) => localStorage.setItem('token', token),
    clearToken: () => localStorage.removeItem('token'),

    async authFetch(endpoint, options = {}) {
        // 🚫 CORTE INMEDIATO DE REQUESTS (CLAVE PARA MATAR LA TORMENTA)
        if (isUnauthorized) {
            return Promise.reject(new Error("Blocked due to unauthorized state"));
        }

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
            console.log(`[NATIVE FETCH RESTORED] Triggering fetch sequence to URL: ${url}`);
            const res = await fetch(url, { ...options, headers });
            
            // 🚨 MANEJO GLOBAL DE 401 (UNAUTHORIZED)
            if (res.status === 401) {
                // No redirigir si el error viene del endpoint de login (para permitir mostrar "Credenciales incorrectas")
                const isLoginEndpoint = url.includes(ENDPOINTS.AUTH.LOGIN);
                
                if (!isUnauthorized && !isLoginEndpoint) {
                    isUnauthorized = true;
                    console.warn("[API] Sesión expirada o inválida (401) — redirigiendo a login");
                    localStorage.clear();
                    window.location.href = "/login";
                }
                return Promise.reject(new Error("Unauthorized"));
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
            
            console.log(`[API RESPONSE VERIFIED] Successfully validated structure for endpoint: ${endpoint}`);
            return data;
        } catch (error) {
            console.error(`[API ERROR] ${endpoint}:`, error);
            throw error;
        }
    }
};

export default api;
