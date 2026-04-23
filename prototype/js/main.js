import api from './api.js';
import { setupDocentesHandlers } from './docentes.js';
import { setupAuth, logout } from './auth.js';
import * as upload from './upload.js';
import * as docentesMgmt from './docentes_mgmt.js';
import * as reportes from './reportes.js';
import * as observaciones from './observaciones.js';
import * as configMgmt from './config_mgmt.js';
import * as usuarios from './usuarios.js';
import { ENDPOINTS } from './config.js';

// Navigation Logic
export function nav(sectionId) {
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
        targetSection.classList.add('active');
        if (sectionId === 'usuarios-module') Handlers.loadUsuarios();
        if (sectionId === 'config-module') {
            Handlers.loadConfig('recess');
            Handlers.loadConfig('lunch');
        }
        if (sectionId === 'docentes-module') Handlers.loadDocentesMaestra();
        if (sectionId === 'horarios-visor-module') Handlers.loadSchedule();
    }
}

// Registro Central de Handlers
const Handlers = {
    logout,
    nav,
    ...upload,
    ...docentesMgmt,
    ...reportes,
    ...observaciones,
    ...configMgmt,
    ...usuarios
};

document.addEventListener('DOMContentLoaded', () => {
    console.log('[BOOTSTRAP] Iniciando Schedule Management UI');
    
    // 1. Verificar sesión y alternar UI
    checkSession();

    // 2. Inicializar Handlers de Módulos
    setupDocentesHandlers();
    setupAuth();
    if (upload.setupUploadHandlers) upload.setupUploadHandlers();
    if (docentesMgmt.setupDocentesUploadHandlers) docentesMgmt.setupDocentesUploadHandlers();
    
    // 3. Delegation Central
    setupGlobalDelegation();

    // 4. Initial Load
    nav('upload');

    console.log('[BOOTSTRAP] Sistema listo');
});

async function checkSession() {
    const token = api.getToken();
    const loginUI = document.getElementById('login-container');
    const appUI = document.getElementById('app-container');

    if (!token) {
        if (loginUI) loginUI.classList.remove('hidden');
        if (appUI) appUI.style.display = 'none';
        return;
    }

    // Token existe: Mostrar App
    if (loginUI) loginUI.classList.add('hidden');
    if (appUI) appUI.style.display = 'flex';

    try {
        // Obtener info del usuario logueado
        const user = await api.authFetch(ENDPOINTS.AUTH.ME);
        const nameDisplay = document.getElementById('current-username-display');
        if (nameDisplay && user.full_name) {
            nameDisplay.innerText = user.full_name;
        }
        
        // RBAC: Mostrar control de usuarios solo si es administrador
        const navUsers = document.getElementById('nav-btn-usuarios');
        const isAdmin = user.roles?.some(r => r.name === 'ADMINISTRADOR');
        if (navUsers && isAdmin) navUsers.style.display = 'flex';

    } catch (e) {
        console.error("[SESSION] Error validando sesión:", e);
        // api.authFetch ya maneja el 401 recargando la página, 
        // lo que disparará checkSession de nuevo sin token.
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
        
        const fn = Handlers[fnName] || window[fnName];
        
        if (!fn) {
            console.error(`Handler no registrado: ${fnName} (Acción: ${actionString})`);
            return;
        }

        if (typeof fn === 'function') {
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



