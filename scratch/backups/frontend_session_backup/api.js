import { API_BASE_URL, ENDPOINTS } from './config.js';

let isUnauthorized = false;

const api = {
    getToken: () => localStorage.getItem('token'),
    setToken: (token) => localStorage.setItem('token', token),
    clearToken: () => localStorage.removeItem('token'),

    // --- CENTRALIZED RBAC MAPS ---
    RBAC_MODULE_MAP: {
        'upload': 'subir_xml',
        'schedule': 'ver_horarios',
        'observations': 'ver_observaciones',
        'rpt-planilla': 'ver_rpt',
        'docentes': 'ver_docentes',
        'usuarios-module': 'gestionar_usuarios',
        'recess-config': 'gestionar_configuracion',
        'lunch-config': 'gestionar_configuracion'
    },
    
    RBAC_VIEW_MAP: {
        'obs-tab-register': 'crear_observaciones',
        'tab-btn-register': 'crear_observaciones',
        'usr-tab-rbac': 'gestionar_permisos',
        'usr-tab-btn-rbac': 'gestionar_permisos'
    },
    
    RBAC_ACTION_MAP: {
        'saveObservation': 'crear_observaciones',
        'deleteObservation': 'crear_observaciones',
        'saveRolePermissions': 'gestionar_permisos',
        'saveNewRole': 'crear_roles',
        'openRoleModal': 'crear_roles',
        'deleteUsuario': 'eliminar_usuarios',
        'deleteRole': 'eliminar_roles'
    },

    hasPermission(code) {
        if (!code) return true;
        const raw = localStorage.getItem('currentUser');
        if (!raw) return false;
        try {
            const user = JSON.parse(raw);
            const userRoles = user.roles || [];
            
            // 0. [STRUCTURAL BYPASS] Preferred Flag-based Logic
            const isProtected = userRoles.some(r => r.is_protected === true);
            if (isProtected) {
                if (window.__OBS_DEV) console.log(`[RBAC ACTION EXECUTED] Access granted via protected role flag for code: ${code}`);
                return true;
            }

            // 1. [LEGACY BYPASS] String-based fallback
            const roleNames = userRoles.map(r => String(r.name || '').toUpperCase().trim());
            if (roleNames.includes('SUPERADMIN') || roleNames.includes('SISTEMAS')) {
                if (window.__OBS_DEV) console.warn(`[LEGACY STRING FALLBACK] Access granted via string-match for code: ${code}`);
                return true;
            }
            
            const perms = user.permissions || [];
            const granted = perms.includes(code);
            
            if (granted) {
                if (window.__OBS_DEV) console.log(`[RBAC ACTION EXECUTED] Permission verified: ${code}`);
            } else {
                console.warn(`[RBAC DENIED] Missing permission: ${code}`);
            }
            
            return granted;
        } catch (e) {
            console.error("[RBAC ERROR] Failed to parse currentUser", e);
            return false;
        }
    },

    canPerformAction(actionName) {
        const baseAction = actionName.split('(')[0].trim();
        const requiredPerm = this.RBAC_ACTION_MAP[baseAction];
        return this.hasPermission(requiredPerm);
    },

    isSuperAdmin() {
        const raw = localStorage.getItem('currentUser');
        if (!raw) return false;
        try {
            const user = JSON.parse(raw);
            const userRoles = user.roles || [];
            const isProtected = userRoles.some(r => r.is_protected === true);
            const roleNames = userRoles.map(r => String(r.name || '').toUpperCase().trim());
            return isProtected || roleNames.includes('SUPERADMIN') || roleNames.includes('SISTEMAS');
        } catch (e) {
            return false;
        }
    },


    async authFetch(endpoint, options = {}) {
        if (isUnauthorized) {
            return Promise.reject(new Error("Blocked due to unauthorized state"));
        }

        const token = this.getToken();
        
        // --- TRACE ID PROPAGATION ---
        // Fallback for non-secure contexts (e.g. accessing via local IP)
        const traceId = options.headers?.['X-Trace-ID'] || 
                       (crypto.randomUUID ? crypto.randomUUID() : `f${Math.random().toString(36).substring(2, 11)}`);
        
        const headers = {
            'X-Trace-ID': traceId,
            'X-Request-ID': traceId, // Backward compatibility
            ...options.headers
        };

        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        const url = endpoint.startsWith('http') 
            ? endpoint 
            : `${API_BASE_URL}${endpoint}`;
        
        if (window.__OBS_DEV || true) {
            console.log(`[TRACE REQUEST] [${traceId}] ${options.method || 'GET'} ${url}`);
        }

        const startTime = performance.now();

        try {
            const res = await fetch(url, { ...options, headers });
            const duration = (performance.now() - startTime).toFixed(2);
            
            if (res.status === 401) {
                const isLoginEndpoint = url.includes(ENDPOINTS.AUTH.LOGIN);
                if (!isUnauthorized && !isLoginEndpoint) {
                    isUnauthorized = true;
                    console.warn(`[TRACE ERROR] [${traceId}] Session expired (401) — Redirecting to login`);
                    localStorage.removeItem('token');
                    localStorage.removeItem('currentUser');
                    window.location.reload();
                }
                return Promise.reject(new Error("Unauthorized"));
            }

            if (!res.ok) {
                const text = await res.text();
                let data = {};
                try { data = text ? JSON.parse(text) : {}; } catch { data = { detail: text }; }
                
                console.error(`[TRACE ERROR] [${traceId}] Status: ${res.status} - ${data.detail || text}`);
                throw new Error(data.detail || `Error HTTP ${res.status}`);
            }

            if (options.rawResponse) return res;

            const text = await res.text();
            let data = {};
            try {
                data = text ? JSON.parse(text) : {};
            } catch (e) {
                data = { raw: text };
                console.warn(`[TRACE ERROR] [${traceId}] Response is not JSON:`, text.substring(0, 50));
            }
            
            if (window.__OBS_DEV) {
                console.log(`[TRACE RESPONSE] [${traceId}] Success (${res.status}) in ${duration}ms`);
            }

            return data;
        } catch (error) {
            const duration = (performance.now() - startTime).toFixed(2);
            console.error(`[TRACE ERROR] [${traceId}] FAILED after ${duration}ms:`, error.message);
            throw error;
        }
    }
};

export default api;
