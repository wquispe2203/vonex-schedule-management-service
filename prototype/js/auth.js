// Authentication Module - ES6
import api from './api.js';
import { API_BASE_URL, ENDPOINTS } from './config.js';

export function setupAuth() {
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.removeEventListener('submit', handleLogin); // Evitar duplicados si re-registra
        loginForm.addEventListener('submit', handleLogin);
    }

    // Delegación para acciones de autenticación
    document.addEventListener('click', (e) => {
        const actionBtn = e.target.closest('[data-action="logout()"]');
        if (actionBtn) {
            logout();
            e.preventDefault();
            e.stopPropagation();
        }
    });
}

async function handleLogin(e) {
    e.preventDefault();
    
    // Protocolo OBLIGATORIO: application/x-www-form-urlencoded
    const payload = new URLSearchParams();
    payload.append('username', document.getElementById('login-username').value.trim());
    payload.append('password', document.getElementById('login-password').value);
    
    const btn = document.getElementById('login-btn');
    const err = document.getElementById('login-error');
    if (!err || !btn) return;

    err.classList.add('hidden');
    btn.disabled = true;
    btn.innerHTML = 'Validando <i class="fa-solid fa-spinner fa-spin"></i>';

    try {
        // Uso de authFetch con URL centralizada y protocolo Form-Data
        const data = await api.authFetch(ENDPOINTS.AUTH.LOGIN, {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: payload
        });
        
        console.log("LOGIN RESPONSE:", data);

        // El wrapper ya validó res.ok y parseó el JSON
        api.setToken(data.access_token);
        
        console.log("[LOGIN SUCCESS] User successfully authenticated.");
        sessionStorage.removeItem('explicit_logout');
        
        // Logged in! Reload to let main.js handle the bootstrap
        window.location.reload();

    } catch (error) {
        console.error("[AUTH] Error en login:", error);
        err.innerText = error.message.includes("401") ? "Credenciales incorrectas" : error.message;
        err.classList.remove('hidden');
    } finally {
        btn.disabled = false;
        btn.innerHTML = 'Ingresar <i class="fa-solid fa-arrow-right"></i>';
    }
}

export function logout() {
    console.log("[LOGOUT START] Purging local session context...");
    sessionStorage.setItem('explicit_logout', 'true');
    console.log("[SESSION PURGE] Removing authentication credentials...");
    api.clearToken();
    localStorage.removeItem('currentUser');
    console.log("[LOGOUT SUCCESS] Token and user profile successfully removed.");
    console.log("[SESSION DESTROYED] All transient auth caches have been destroyed.");
    window.location.reload();
}
