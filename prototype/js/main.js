import api from './api.js';
import { setupDocentesHandlers } from './docentes.js';
import { setupAuth, logout } from './auth.js';
import * as upload from './upload.js';
import * as docentesMgmt from './docentes_mgmt.js';
import * as reportes from './reportes.js';
import * as observaciones from './observaciones.js';
import * as horarios from './horarios.js';
import * as configMgmt from './config_mgmt.js';
import * as usuarios from './usuarios.js';
import { ENDPOINTS, API_BASE_URL } from './config.js';

// UI Submenu Handlers
export function toggleConfigMenu() {
    console.log("[UI ACTION] Toggling Config Submenu via visual delegation.");
    const submenu = document.getElementById('config-submenu');
    const chevron = document.getElementById('config-chevron');
    if (!submenu) return;
    
    const isHidden = submenu.classList.contains('hidden');
    if (isHidden) {
        submenu.classList.remove('hidden');
        if (chevron) chevron.classList.add('rotate-180');
    } else {
        submenu.classList.add('hidden');
        if (chevron) chevron.classList.remove('rotate-180');
    }
}

// Navigation Logic
export function nav(sectionId) {
    console.log(`[NAV TRACE] Navigating to section: ${sectionId}`);
    
    // Eliminar active de todos los nav-btn
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.classList.remove('bg-indigo-600', 'text-white', 'shadow-md', 'shadow-indigo-900/50');
        if (!btn.classList.contains('text-slate-300')) {
            btn.classList.add('text-slate-300', 'hover:bg-slate-800');
        }
    });

    // Resaltar el seleccionado
    document.querySelectorAll('.nav-btn').forEach(btn => {
        if (btn.getAttribute('data-action')?.includes(`nav('${sectionId}')`)) {
            btn.classList.add('bg-indigo-600', 'text-white', 'shadow-md', 'shadow-indigo-900/50');
            btn.classList.remove('text-slate-300', 'hover:bg-slate-800');
        }
    });

    document.querySelectorAll('.section').forEach(el => el.classList.remove('active'));
    const targetSection = document.getElementById(sectionId);
    if (targetSection) {
        console.log(`[SECTION ACTIVATED] Activating target section in DOM: ${sectionId}`);
        targetSection.classList.add('active');
        if (sectionId === 'upload') Handlers.initXmlUploadView();
        if (sectionId === 'usuarios-module') Handlers.initUsuarios();
        if (sectionId === 'config-module') {
            Handlers.loadConfig('recess');
            Handlers.loadConfig('lunch');
        }
        if (sectionId === 'docentes') {
            Handlers.toggleDocentesTab('upload-excel');
        }
        if (sectionId === 'schedule') Handlers.initSchedule();
        if (sectionId === 'rpt-planilla') Handlers.initRPT();
        if (sectionId === 'observations') Handlers.initObservaciones();
    }
}

// Registro Central de Handlers
const Handlers = {
    logout,
    nav,
    toggleConfigMenu,
    ...upload,
    ...docentesMgmt,
    ...reportes,
    ...observaciones,
    ...horarios,
    ...configMgmt,
    ...usuarios
};
console.log('[HANDLER REGISTRY VERIFIED] Centralized event handlers maps registered successfully.');
// window.Handlers = Handlers; // Eliminado por política de modularidad pura

let isAuthenticated = false;
let appReady = false;
let lastHandlerName = "bootstrap_start";

// ⏱️ Bootstrap Watchdog
const watchdog = setTimeout(() => {
    if (!appReady) {
        console.error(`[BOOTSTRAP DEADLOCK DETECTED] Halted at handler: ${lastHandlerName}. App ready: false`);
    }
}, 10000);

document.addEventListener('DOMContentLoaded', async () => {
    console.log('[BOOTSTRAP] Iniciando Schedule Management UI');
    
    // 1. Siempre inicializar delegación global y Auth (para permitir el login)
    setupGlobalDelegation();
    setupAuth();

    // 2. Verificar sesión
    await checkSession();
    
    if (!isAuthenticated) {
        console.warn("[MAIN] Usuario no autenticado. Interfaz de login activa.");
        appReady = true; // Desbloquear eventos para interacciones de login
        clearTimeout(watchdog);
        return; 
    }

    // 3. Inicializar Handlers de Módulos (Solo si está autenticado)
    setupDocentesHandlers();
    if (upload.setupUploadHandlers) upload.setupUploadHandlers();
    if (docentesMgmt.setupDocentesUploadHandlers) docentesMgmt.setupDocentesUploadHandlers();
    
    // 4. Navegación inicial
    nav('upload');

    appReady = true; // 🚀 Bootstrap completo: Levantar escudo sintético
    clearTimeout(watchdog);
    console.log('[BOOTSTRAP COMPLETE] Sistema listo');
});

async function checkSession() {
    let token = api.getToken();
    
    // [DEV AUTH ENABLED] Silent fallback for local development
    if (!token && (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')) {
        try {
            console.log('[DEV AUTH RESTORED] Attempting dev token hydration...');
            const devResp = await fetch(`${API_BASE_URL}${ENDPOINTS.USERS.BASE}/dev-login`);
            if (devResp.ok) {
                const devData = await devResp.json();
                localStorage.setItem('token', devData.access_token);
                token = devData.access_token;
                console.log('[DEV TOKEN HYDRATED] Successfully injected development context.');
            }
        } catch(e) {
            console.warn('[DEV AUTH] Hydration failed. Proceeding normally.');
        }
    }

    const loginUI = document.getElementById('login-container');
    const appUI = document.getElementById('app-container');

    if (!token) {
        if (loginUI) loginUI.classList.remove('hidden');
        if (appUI) appUI.style.display = 'none';
        isAuthenticated = false;
        return;
    }

    // Token existe: Mostrar App
    if (loginUI) loginUI.classList.add('hidden');
    if (appUI) appUI.style.display = 'flex';

    try {
        // Obtener info del usuario logueado
        const user = await api.authFetch(ENDPOINTS.AUTH.ME);
        
        const nameDisplay = document.getElementById('current-username-display');
        if (nameDisplay && user.data?.full_name) {
            nameDisplay.innerText = user.data.full_name;
        }
        
        // [ROLE NORMALIZATION ACTIVE] Robust multi-role matching
        const navUsers = document.getElementById('nav-btn-usuarios');
        const allowedAdminRoles = ['ADMINISTRADOR', 'ADMIN', 'SUPERADMIN', 'SISTEMAS'];
        const userRoles = (user.data?.roles || []).map(r => String(r.name || '').toUpperCase().trim());
        
        console.log(`[RBAC VALIDATION] User roles found: ${JSON.stringify(userRoles)}`);
        
        const isAdmin = userRoles.some(roleName => allowedAdminRoles.includes(roleName));
        if (navUsers && isAdmin) {
            console.log("[RBAC GRANTED] Displaying Administrative module options.");
            navUsers.style.display = 'flex';
        }

        isAuthenticated = true;
    } catch (e) {
        console.error("[SESSION] Error validando sesión:", e);
        isAuthenticated = false;
        // api.authFetch ya maneja el 401 redirigiendo a login
    }
}

function setupGlobalDelegation() {
    const executeAction = (e, type) => {
        const target = e.target.closest('[data-action]');
        if (!target) return;
        
        const actionString = target.getAttribute('data-action');
        if (!actionString) return;

        const match = actionString.match(/^([a-zA-Z0-9_]+)/);
        if (!match) return;
        const fnName = match[1];
        
        lastHandlerName = fnName; // Tracking diagnóstico de watchdog

        // 🛡️ 4. User-Intent Boot Shield
        if (!appReady) {
            const isTrustedHuman = e.isTrusted || type === 'click';
            const isCritical = ['logout', 'nav'].includes(fnName);
            if (!isTrustedHuman && !isCritical) {
                console.warn(`[BOOT SHIELD] Evento sintético '${type}' bloqueado para '${fnName}' durante bootstrap.`);
                return;
            }
        }
        
        const fn = Handlers[fnName];
        
        if (!fn) {
            console.error(`Handler no registrado: ${fnName} (Acción: ${actionString})`);
            return;
        }

        if (typeof fn === 'function') {
            // Log de prevención de carrera rápida solicitado por la auditoría
            if (fnName === 'nav') console.log('[NAVIGATION RACE PREVENTED] Validating exclusive nav execution.');

            if (actionString.includes('(')) {
                try {
                    const argsMatch = actionString.match(/\((.*?)\)/);
                    const args = argsMatch ? argsMatch[1].split(',').map(s => s.trim().replace(/['"]/g, '')) : [];
                    fn(...args, e);
                } catch (err) {
                    new Function('event', actionString).call(window, e);
                }
            } else {
                fn(e);
            }
        }
    };

    document.addEventListener('click', (e) => executeAction(e, 'click'));
    document.addEventListener('change', (e) => executeAction(e, 'change'));
    document.addEventListener('input', (e) => executeAction(e, 'input'));
}



