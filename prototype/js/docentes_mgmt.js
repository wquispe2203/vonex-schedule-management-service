// Docentes Management Module - ES6
import api from './api.js';
import { ENDPOINTS } from './config.js';
import { extractList, extractPagination } from './ui_utils.js';

let currentStatusTarget = null;
let currentRequestId = 0;

// Sin Asignar pagination state
let sinAsignarPage = 1;
let sinAsignarTotalPages = 1;
let lastConflicts = [];

// State management for Maestra Tab
let docentesState = {
    page: 1,
    per_page: 20,
    total: 0,
    totalPages: 1,
    search: '',
    status: 'all', // acts, inacts, all
    data: [] // local cache for the current page
};




// Tab management
const DOC_TABS = ['upload-excel', 'maestra', 'sinasignar', 'conflictos'];
let currentUploadFile = null;
let isImporting = false;

function resetUploadState() {
    currentUploadFile = null;
    isImporting = false;
    const dropzone = document.querySelector('[data-upload="docentes"]');
    if (!dropzone) return;

    const input = dropzone.querySelector('input[type="file"]');
    if (input) input.value = '';
    
    const nameEl = dropzone.querySelector('[data-file-name]');
    if (nameEl) {
        nameEl.textContent = 'Arrastra tu Excel o haz clic aquí';
        nameEl.classList.remove('text-indigo-600', 'text-emerald-600');
    }
}

export function initSubirDocentesView() {
    console.log('[INIT] Subir Docentes');
    resetUploadState();
    setupDocentesUploadHandlers();
}

export function safeRenderDocentes(actionFn) {
    try {
        if (typeof actionFn === 'function') actionFn();
    } catch (error) {
        console.error('[RENDER ERROR]', error);
        const appContainer = document.getElementById('app-container');
        if (appContainer) {
            appContainer.innerHTML = `
                <div style="padding:40px; color:#e11d48; background: white; border-radius: 24px; margin: 40px auto; max-width: 600px; border: 1px solid #fecdd3; shadow: 0 20px 25px -5px rgb(0 0 0 / 0.1); text-align: center;">
                    <i class="fa-solid fa-triangle-exclamation" style="font-size: 48px; margin-bottom: 20px;"></i>
                    <h2 style="font-size: 24px; font-weight: 900; margin-bottom: 10px;">Error Crítico de UI</h2>
                    <p style="font-size: 14px; font-weight: 500; opacity: 0.8;">No se pudo renderizar el módulo de docentes correctamente.</p>
                    <button onclick="window.location.reload()" style="margin-top: 24px; background: #4f46e5; color: white; padding: 12px 24px; border-radius: 12px; font-weight: bold; border: none; cursor: pointer;">
                        Refrescar Aplicación
                    </button>
                </div>
            `;
        }
    }
}


export function toggleDocentesTab(tab) {
    safeRenderDocentes(() => {
        DOC_TABS.forEach(t => {
            const el = document.getElementById(`doc-tab-${t}`);
            if (el) el.classList.toggle('hidden', t !== tab);
            
            const btn = document.getElementById(`doc-tab-btn-${t}`);
            if (!btn) return;
            if (t === tab) {
                btn.classList.add('border-indigo-600', 'text-indigo-600');
                btn.classList.remove('border-transparent', 'text-slate-500');
            } else {
                btn.classList.remove('border-indigo-600', 'text-indigo-600');
                btn.classList.add('border-transparent', 'text-slate-500');
            }
        });

        if (tab === 'upload-excel') initSubirDocentesView();
        
        if (tab === 'maestra') {
            docentesState.status = 'all';
            loadDocentes(1);
        }
        if (tab === 'sinasignar') {
            loadSinAsignar(1);
        }
        if (tab === 'conflictos') {
            loadConflictos();
        }
    });
}



// Maestra Table - Centralized Loader
export async function loadDocentes(page = null) {
    if (page !== null) docentesState.page = page;
    
    const requestId = ++currentRequestId;
    setLoading(true);
    toggleControls(true);

    console.log('[DOCENTES] Cargando página:', docentesState.page, '(ID:', requestId, ')');

    try {
        const searchVal = document.getElementById('doc-search')?.value.trim() || '';
        const statusVal = document.getElementById('doc-status-filter')?.value || 'all';
        
        docentesState.search = searchVal;
        docentesState.status = statusVal;

        const paramsObj = {
            page: docentesState.page,
            limit: docentesState.per_page,
            status: 'all' // Force backend to return ACTIVO, INCOMPLETO, etc.
        };
        if (docentesState.search) paramsObj.search = docentesState.search;
        if (docentesState.status && docentesState.status !== 'all') {
            paramsObj.filter = docentesState.status; // It expects filter=acts/inacts
        }

        const params = new URLSearchParams(paramsObj);

        const response = await api.authFetch(`${ENDPOINTS.DOCENTES.BASE}?${params}`);

        // REGLA OBLIGATORIA: Log del response completo
        console.log('[DOCENTES] Response recibida:', response);

        // Control de Concurrencia (Ignorar respuestas antiguas)
        if (requestId !== currentRequestId) {
            console.warn('[DOCENTES] Ignorando respuesta antigua del request ID:', requestId);
            return;
        }

        // Pipeline de Hardening (v3.15)
        if (typeof extractList !== "function") {
            throw new Error("Dependency extractList missing");
        }

        const list = extractList(response);
        const pagination = extractPagination(response);

        // LOGGING CONTROLADO
        console.log('[DOCENTES] LIST:', list);

        docentesState.total = pagination?.total || 0;
        docentesState.totalPages = pagination?.total_pages || Math.ceil(docentesState.total / docentesState.per_page) || 1;

        if (list.length === 0) {
            renderEmptyState();
            updatePagination(1);
        } else {
            safeRenderDocentesTable(list);
            updatePagination(docentesState.totalPages);
        }

    } catch (error) {
        if (requestId === currentRequestId) {
            console.error('[DOCENTES ERROR]', error);
            renderErrorState('Error cargando docentes: ' + error.message);
        }
    } finally {
        if (requestId === currentRequestId) {
            setLoading(false);
            toggleControls(false);
        }
    }
}

function setLoading(isLoading) {
    const loader = document.getElementById('doc-maestra-loading');
    if (loader) {
        loader.classList.toggle('hidden', !isLoading);
    }
}

function toggleControls(disabled) {
    const btns = ['doc-maestra-next', 'doc-maestra-prev', 'btn-doc-filtrar'];
    btns.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.disabled = disabled;
    });
}


// Eliminadas validateDocentesResponse y normalizeResponse a favor de ui_utils.js

function updatePagination(totalPages) {
    const nextBtn = document.getElementById('doc-maestra-next');
    const prevBtn = document.getElementById('doc-maestra-prev');
    const indicatorEl = document.getElementById('doc-maestra-indicator');
    const totalEl = document.getElementById('doc-maestra-total');

    if (nextBtn) nextBtn.disabled = docentesState.page >= totalPages;
    if (prevBtn) prevBtn.disabled = docentesState.page <= 1;
    if (indicatorEl) indicatorEl.textContent = `${docentesState.page} / ${totalPages}`;
    if (totalEl) totalEl.textContent = docentesState.total;
}

function renderEmptyState() {
    const tbody = document.getElementById('doc-maestra-body');
    if (tbody) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" class="px-4 py-12 text-center text-slate-400">
                    <i class="fa-solid fa-magnifying-glass text-3xl mb-3 block opacity-20"></i>
                    No se encontraron docentes que coincidan con los criterios.
                </td>
            </tr>
        `;
    }
}

function safeRenderDocentesTable(rows) {
    try {
        renderDocentesTable(rows);
    } catch (err) {
        console.error('[RENDER ERROR]', err);
        renderErrorState('Error renderizando tabla');
    }
}

function renderDocentesTable(rows) {
    const tbody = document.getElementById('doc-maestra-body');
    if (!tbody) return;

    tbody.innerHTML = '';
    docentesState.data = rows;

    rows.forEach(t => {
        console.log("[RENDER] Procesando docente:", t);
        const activeBadge = t.is_active
            ? `<button data-action="handleStatusClick('${t.id}', true, '${t.apellidos}, ${t.nombres}')" class="bg-emerald-100 text-emerald-700 text-[10px] font-black px-3 py-1 rounded-full border border-emerald-200 hover:bg-emerald-200 transition-colors shadow-sm">ACTIVO</button>`
            : `<button data-action="handleStatusClick('${t.id}', false, '${t.apellidos}, ${t.nombres}')" class="bg-rose-100 text-rose-700 text-[10px] font-black px-3 py-1 rounded-full border border-rose-200 hover:bg-rose-200 transition-colors shadow-sm">INACTIVO</button>`;

        tbody.insertAdjacentHTML('beforeend', `
            <tr class="hover:bg-slate-50 transition-colors" data-teacher-id="${t.id}">
                <td class="px-4 py-3 w-10">
                    <input type="checkbox" data-id="${t.id}" data-action="updateMergeSelection" class="merge-checkbox rounded border-slate-300 text-indigo-600 focus:ring-indigo-500">
                </td>
                <td class="px-4 py-3 font-bold text-slate-800">
                    ${t.apellidos}
                    ${t.is_potential_duplicate ? '<i class="fa-solid fa-triangle-exclamation text-amber-500 ml-1" title="Posible duplicado detectado"></i>' : ''}
                </td>
                <td class="px-4 py-3 text-slate-700">${t.nombres}</td>
                <td class="px-4 py-3 font-mono text-xs text-slate-500">${t.dni || '—'}</td>
                <td class="px-4 py-3 text-xs text-slate-500">${t.razon_social || '—'}</td>
                <td class="px-4 py-3 text-center status-cell">${activeBadge}</td>
                <td class="px-4 py-3 text-right">
                    <button data-action="openTeacherModalClick('${t.id}')"
                        class="text-indigo-600 hover:bg-indigo-50 border border-indigo-100 text-xs font-bold px-3 py-1.5 rounded-lg">
                        <i class="fa-solid fa-pen"></i> Editar
                    </button>
                </td>
            </tr>`);
    });
}


function renderErrorState(message) {
    const tbody = document.getElementById('doc-maestra-body');
    if (tbody) {
        tbody.innerHTML = `<tr><td colspan="7" class="px-4 py-10 text-center text-rose-600 font-bold">${message}</td></tr>`;
    }
}

export function nextPage() {
    if (docentesState.page < docentesState.totalPages) {
        docentesState.page++;
        loadDocentes();
    }
}

export function prevPage() {
    if (docentesState.page > 1) {
        docentesState.page--;
        loadDocentes();
    }
}

export function applyFilters() {
    currentRequestId++; // Invalida cualquier request en vuelo
    docentesState.page = 1;
    loadDocentes();
}

export function changeSinAsignarPage(offset) {
    const targetPage = sinAsignarPage + parseInt(offset);
    if (targetPage >= 1 && targetPage <= sinAsignarTotalPages) {
        loadSinAsignar(targetPage);
    }
}

export function vincularTeacherClick(nombreXml, teacherId, apellidos, nombres, dni) {
    const t = {
        id: teacherId || '',
        last_name: apellidos || '',
        first_name: nombres || '',
        dni: dni || '',
        razon_social: ''
    };
    if (!t.last_name && !t.first_name && nombreXml) {
        // Pre-populate with XML name
        const parts = nombreXml.trim().split(' ');
        if (parts.length >= 3) {
            t.last_name = parts.slice(parts.length - 2).join(' ');
            t.first_name = parts.slice(0, parts.length - 2).join(' ');
        } else if (parts.length === 2) {
            t.last_name = parts[1];
            t.first_name = parts[0];
        } else {
            t.first_name = nombreXml;
        }
    }
    openTeacherModal(t);
}



// Merge Logic
export function updateMergeSelection() {
    const selected = document.querySelectorAll('input.merge-checkbox:checked');
    const count = selected.length;
    const btn = document.getElementById('btn-merge-docentes');
    if (btn) {
        btn.disabled = count !== 2;
        btn.innerHTML = `<i class="fa-solid fa-code-merge mr-1"></i> Fusionar (${count})`;
    }
}

export function openMergeModal() {
    const selectedCheckBoxes = [...document.querySelectorAll('input.merge-checkbox:checked')];
    const selectedIds = selectedCheckBoxes.map(cb => cb.dataset.id);
    
    if (selectedIds.length !== 2) {
        alert('Debes seleccionar exactamente 2 docentes para fusionar.');
        return;
    }

    const teachers = docentesState.data.filter(t => selectedIds.includes(t.id));

    if (teachers.length !== 2) {
        alert('Error al cargar datos. Por favor, refresca la tabla e intenta de nuevo.');
        return;
    }
    
    currentMergeData = teachers;
    
    [0, 1].forEach(i => {
        const t = teachers[i];
        document.getElementById(`merge-name-${i}`).textContent = `${t.apellidos}, ${t.nombres}`;
        document.getElementById(`merge-dni-${i}`).textContent = t.dni || 'SIN DNI';
        document.getElementById(`merge-rs-${i}`).textContent = t.razon_social || '—';
        
        const badgeContainer = document.getElementById(`merge-badge-${i}`);
        if (badgeContainer) {
            badgeContainer.innerHTML = t.status === 'CONFLICTO' 
                ? '<span class="bg-amber-100 text-amber-700 text-[10px] font-black px-2 py-0.5 rounded-full">CONFLICTO</span>'
                : '';
        }
    });

    let preselectIdx = -1;
    const hasDni0 = !!teachers[0].dni;
    const hasDni1 = !!teachers[1].dni;

    if (hasDni0 && !hasDni1) preselectIdx = 0;
    else if (!hasDni0 && hasDni1) preselectIdx = 1;

    resetMergeUI();
    if (preselectIdx !== -1) selectPrincipal(preselectIdx);

    document.getElementById('merge-modal')?.classList.remove('hidden');
}

function resetMergeUI() {
    [0, 1].forEach(i => {
        const card = document.getElementById(`merge-card-${i}`);
        if (card) {
            card.classList.remove('border-indigo-600', 'bg-indigo-50/30', 'ring-4', 'ring-indigo-100');
            card.classList.add('border-slate-100');
        }
        const radio = document.getElementById(`radio-p-${i}`);
        if (radio) radio.checked = false;
    });
    const confirmBtn = document.getElementById('btn-confirm-merge');
    if (confirmBtn) confirmBtn.disabled = true;
}

export function selectPrincipal(idx) {
    resetMergeUI();
    const card = document.getElementById(`merge-card-${idx}`);
    if (card) {
        card.classList.remove('border-slate-100');
        card.classList.add('border-indigo-600', 'bg-indigo-50/30', 'ring-4', 'ring-indigo-100');
    }
    const radio = document.getElementById(`radio-p-${idx}`);
    if (radio) radio.checked = true;
    const confirmBtn = document.getElementById('btn-confirm-merge');
    if (confirmBtn) confirmBtn.disabled = false;
}

export function closeMergeModal() { 
    document.getElementById('merge-modal')?.classList.add('hidden'); 
}

export async function executeMerge() {
    const radio0 = document.getElementById('radio-p-0');
    if (!radio0) return;
    const idx = radio0.checked ? 0 : 1;
    const main = currentMergeData[idx];
    const merge = currentMergeData[1 - idx];

    if (!confirm(`¿Confirmar fusión?\n\nPrincipal: ${main.apellidos} (SE CONSERVA)\nSecundario: ${merge.apellidos} (SE ELIMINA)`)) return;

    const btn = document.getElementById('btn-confirm-merge');
    if (!btn) return;
    const origText = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin mr-1"></i> Iniciando fusión...';

    try {
        const response = await api.authFetch(`${ENDPOINTS.DOCENTES.BASE}/merge`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ primary_id: main.id, secondary_id: merge.id })
        });
        // El wrapper authFetch ya lanza error si !res.ok
        
        alert('✅ Fusión exitosa. El sistema ha consolidado las lecciones y eliminado el registro duplicado.');
        closeMergeModal();
        loadDocentes();
        updateMergeSelection();
    } catch(e) { 
        alert('❌ Error de conexión: ' + e.message); 
    } finally { 
        btn.disabled = false; 
        btn.innerHTML = origText;
    }
}

// Status Toggle
export async function handleStatusClick(id, currentStatus, name) {
    currentStatusTarget = { id, currentStatus, name };
    const modal = document.getElementById('teacher-status-modal');
    const title = document.getElementById('status-modal-title');
    const msg = document.getElementById('status-modal-msg');
    const icon = document.getElementById('status-modal-icon');
    const warning = document.getElementById('status-activity-warning');
    const btn = document.getElementById('btn-status-confirm');

    if (!modal) return;

    warning.classList.add('hidden');
    btn.innerHTML = 'Cargando...';
    btn.disabled = true;

    title.textContent = currentStatus ? '¿Desactivar Docente?' : '¿Activar Docente?';
    msg.innerHTML = currentStatus 
        ? `Vas a desactivar a <strong>${name}</strong>. No aparecerá en el RPT Planilla.`
        : `Vas a reactivar a <strong>${name}</strong>. Volverá a aparecer en el RPT Planilla.`;
    
    icon.className = `w-20 h-20 mx-auto rounded-full flex items-center justify-center mb-6 text-3xl shadow-lg animate-bounce-slow ${currentStatus ? 'bg-rose-100 text-rose-600' : 'bg-emerald-100 text-emerald-600'}`;
    
    modal.classList.remove('hidden');

    try {
        const json = await api.authFetch(`${ENDPOINTS.DOCENTES.BASE}/${id}/actividad`);
        if (json.success && currentStatus) {
            const hasActivity = json.data.has_lessons || json.data.has_observations;
            if (hasActivity) warning.classList.remove('hidden');
        }
    } catch (e) { console.error("Error checking activity:", e); }

    btn.innerHTML = 'SÍ, CONFIRMAR';
    btn.disabled = false;
}

export function closeStatusModal() {
    document.getElementById('teacher-status-modal')?.classList.add('hidden');
    currentStatusTarget = null;
}

export async function confirmStatusChange() {
    if (!currentStatusTarget) return;
    const { id, currentStatus } = currentStatusTarget;
    const btn = document.getElementById('btn-status-confirm');
    const origText = btn.innerHTML;
    
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin mr-1"></i> Procesando...';
    btn.disabled = true;

    try {
        const data = await api.authFetch(`${ENDPOINTS.DOCENTES.BASE}/${id}/estado`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ is_active: !currentStatus })
        });
        if (data.success) {
            closeStatusModal();
            const row = document.querySelector(`tr[data-teacher-id="${id}"]`);
            if (row) {
                const cell = row.querySelector('.status-cell');
                const newStatus = !currentStatus;
                const teacherName = currentStatusTarget.name;
                cell.innerHTML = newStatus
                    ? `<button data-action="handleStatusClick('${id}', true, '${teacherName}')" class="bg-emerald-100 text-emerald-700 text-[10px] font-black px-3 py-1 rounded-full border border-emerald-200 hover:bg-emerald-200 transition-colors shadow-sm scale-in">ACTIVO</button>`
                    : `<button data-action="handleStatusClick('${id}', false, '${teacherName}')" class="bg-rose-100 text-rose-700 text-[10px] font-black px-3 py-1 rounded-full border border-rose-200 hover:bg-rose-200 transition-colors shadow-sm scale-in">INACTIVO</button>`;
            } else {
                loadDocentes();
            }
        } else {
            alert('Error: ' + (data.detail || 'No se pudo actualizar el estado.'));
        }
    } catch (e) {
        alert('Error de conexión: ' + e.message);
    } finally {
        btn.innerHTML = origText;
        btn.disabled = false;
    }
}

// Teacher CRUD Modal
export function openTeacherModalClick(id) {
    const teacher = docentesState.data.find(t => t.id === id);
    if (teacher) {
        openTeacherModal(teacher);
    } else {
        // Fallback if not found in current page
        openTeacherModal({id});
    }
}



export function openTeacherModal(t = null) {
    const idInput = document.getElementById('teacher-modal-id');
    if (!idInput) return;
    
    idInput.value = t?.id || '';
    document.getElementById('teacher-modal-title').textContent = t ? 'Editar Docente' : 'Nuevo Docente';
    document.getElementById('teacher-modal-lastname').value = t?.last_name || '';
    document.getElementById('teacher-modal-firstname').value = t?.first_name || '';
    document.getElementById('teacher-modal-dni').value = t?.dni || '';
    document.getElementById('teacher-modal-razon').value = t?.razon_social || '';
    document.getElementById('teacher-modal').classList.remove('hidden');
}

export function closeTeacherModal() { 
    document.getElementById('teacher-modal')?.classList.add('hidden'); 
}

export async function saveTeacher() {
    const idInput = document.getElementById('teacher-modal-id');
    const lastNameInput = document.getElementById('teacher-modal-lastname');
    const firstNameInput = document.getElementById('teacher-modal-firstname');
    const dniInput = document.getElementById('teacher-modal-dni');
    const razonInput = document.getElementById('teacher-modal-razon');

    if (!lastNameInput || !firstNameInput) {
        console.warn('[DOM WARNING] Essential inputs not found: teacher-modal-lastname or teacher-modal-firstname');
        return;
    }

    const id = idInput ? idInput.value : '';
    const body = {
        last_name:    lastNameInput.value.trim(),
        first_name:   firstNameInput.value.trim(),
        dni:          dniInput ? dniInput.value.trim() : '',
        razon_social: razonInput ? razonInput.value.trim() : '',
    };

    if (!body.last_name || !body.first_name) {
        alert("Apellidos y Nombres son obligatorios.");
        return;
    }

    // STEP 2 — DNI REQUIRED (FRONTEND)
    if (!body.dni || body.dni.trim() === "") {
        alert("El DNI es obligatorio");
        return;
    }

    // STEP 3 — LOADING STATE (BUTTON LOCK)
    const btn = document.getElementById('btn-save-teacher');
    const origText = btn ? btn.innerHTML : "Guardar";
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin mr-1"></i> Guardando...';
    } else {
        console.warn('[DOM WARNING] Save button not found: btn-save-teacher');
    }

    // STEP 5 — ERROR HANDLING (Wrap in try/catch)
    try {
        const method = id ? 'PUT' : 'POST';
        const url = id ? `${ENDPOINTS.DOCENTES.BASE}/${id}` : ENDPOINTS.DOCENTES.BASE;
        const data = await api.authFetch(url, {
            method,
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(body)
        });

        // STEP 1 — API RESPONSE VALIDATION
        if (!data || !data.success) {
            throw new Error(data?.detail || data?.error || "Error al guardar docente");
        }

        // STEP 4 — SUCCESS FEEDBACK
        alert("Docente guardado correctamente");

        // STEP 6 — SAFE UI FLOW
        closeTeacherModal();
        await loadSinAsignar(sinAsignarPage);
        await loadDocentes(docentesState.page);

    } catch(err) {
        console.error("[SAVE ERROR]", err);
        alert(err.message || "Error al guardar docente");
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = origText;
        }
    }
}

// Sin Asignar Table
export async function loadSinAsignar(page = 1) {
    sinAsignarPage = page;
    try {
        const response = await api.authFetch(`${ENDPOINTS.DOCENTES.SIN_ASIGNAR}?page=${page}&limit=20`);

        // REGLA OBLIGATORIA: Log del response completo
        console.log('[SIN ASIGNAR] Response recibida:', response);

        // ✅ USO DE HELPERS CENTRALIZADOS
        const list = extractList(response);
        const pagination = extractPagination(response);

        console.log('[SIN ASIGNAR] LIST:', list);

        const total = pagination?.total || list.length || 0;
        sinAsignarTotalPages = pagination?.total_pages || Math.ceil(total / 20) || 1;

        const sinTotal = document.getElementById('doc-sinasignar-total');
        const sinIndicator = document.getElementById('doc-sa-indicator');
        const sinPrev = document.getElementById('doc-sa-prev');
        const sinNext = document.getElementById('doc-sa-next');

        if (sinTotal) sinTotal.textContent = total;
        if (sinIndicator) sinIndicator.textContent = `${page} / ${sinAsignarTotalPages}`;
        if (sinPrev) sinPrev.disabled = page <= 1;
        if (sinNext) sinNext.disabled = page >= sinAsignarTotalPages;
        
        const tbody = document.getElementById('doc-sinasignar-body');
        if (!tbody) return;
        
        tbody.innerHTML = '';
        if (list.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="px-4 py-10 text-center text-slate-400">Todo al día</td></tr>';
            return;
        }

        list.forEach(t => {
            const dateStr = t.last_seen_at ? t.last_seen_at : '—';
            
            let dbDetails = '—';
            if (t.apellidos || t.nombres) {
                dbDetails = `<span class="font-semibold text-slate-700">${t.apellidos || ''}, ${t.nombres || ''}</span>`;
                if (t.dni) dbDetails += ` <br><span class="text-[10px] font-mono text-slate-400">DNI: ${t.dni}</span>`;
            }

            let reasonBadge = '';
            if (t.reason === 'DATOS_INCOMPLETOS') {
                reasonBadge = '<span class="bg-amber-50 text-amber-700 border border-amber-200 text-[10px] uppercase font-bold px-2 py-1 rounded-xl">Datos incompletos (sin DNI)</span>';
            } else {
                reasonBadge = '<span class="bg-slate-50 text-slate-600 border border-slate-200 text-[10px] uppercase font-bold px-2 py-1 rounded-xl">No existe en BD</span>';
            }

            tbody.insertAdjacentHTML('beforeend', `<tr>
                <td class="px-4 py-3 font-bold text-slate-800">${t.nombre_xml || t.normalized_name}</td>
                <td class="px-4 py-3 text-slate-500 text-xs">${dbDetails}</td>
                <td class="px-4 py-3 text-center">${reasonBadge}</td>
                <td class="px-4 py-3 text-slate-500 font-mono text-xs">${dateStr}</td>
                <td class="px-4 py-3 text-right">
                    <button data-action="openTeacherModalClick('${t.id || ''}')" class="text-indigo-600 hover:underline text-xs font-bold">Vincular/Crear</button>
                </td>
            </tr>`);
        });
    } catch(e) { console.error('loadSinAsignar:', e); }
}

// Import Logic
let importData = [];
let importPage = 1;
const importLimit = 10;
// Note: currentUploadFile and isImporting moved to top level for global control


export async function uploadDocentesExcel() {
    if (isImporting) return;

    const dropzone = document.querySelector('[data-upload="docentes"]');
    const fileInput = dropzone?.querySelector('input[type="file"]');
    const file = currentUploadFile || fileInput?.files[0];

    console.log("[IMPORT] Iniciando proceso...");
    console.log("[IMPORT] File:", file ? `${file.name} (${file.size} bytes)` : "No file");

    if (!file) {
        alert("Por favor, seleccione un archivo Excel antes de importar.");
        return;
    }

    const btn = document.querySelector('[data-action="uploadDocentesExcel()"]');
    if (!btn) return;

    const origText = btn.innerHTML;
    isImporting = true;
    btn.disabled = true;
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin mr-2"></i> Procesando datos...';

    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await api.authFetch(ENDPOINTS.DOCENTES.IMPORT, {
            method: 'POST',
            body: formData
        });

        // REGLA OBLIGATORIA: Log del response completo
        console.log("[IMPORT] Response recibida:", response);

        // El payload real esta en response.data
        const payload = response.data || {};
        
        // ✅ USO DE HELPER PARA LA LISTA
        const rows = extractList(response);
        console.log("[IMPORT] ROWS:", rows);
        importData = rows;
        importPage = 1;

        // Renderizar resultado
        try {
            renderImportResult(payload);
            const resultContainer = document.getElementById('doc-import-result');
            if (resultContainer) {
                resultContainer.classList.remove('hidden');
                resultContainer.scrollIntoView({ behavior: 'smooth' });
            }
        } catch (renderErr) {
            console.error("[IMPORT] Error en renderizacion:", renderErr);
            alert("Importacion completada. inserted=" + (importResult.inserted||0) + " updated=" + (importResult.updated||0));
        }

        // Limpiar estado
        currentUploadFile = null;
        if (fileInput) fileInput.value = '';

        const nameEl = dropzone?.querySelector('[data-file-name]');
        if (nameEl) {
            nameEl.textContent = 'Carga completada con exito!';
            nameEl.classList.remove('text-indigo-600');
            nameEl.classList.add('text-emerald-600');
            setTimeout(() => {
                nameEl.textContent = 'Arrastra tu Excel o haz clic aqui';
                nameEl.classList.remove('text-emerald-600');
            }, 5000);
        }

        // Refrescar la vista Maestra
        if (typeof loadDocentes === 'function') loadDocentes(1);

    } catch (e) {
        console.error("[IMPORT] Error critico:", e);
        // Dar mensaje claro si es problema de columnas
        const msg = e.message || "";
        if (msg.includes("APELLIDOS") || msg.includes("columnas") || msg.includes("NOMBRES")) {
            alert("El archivo Excel no tiene el formato correcto.\n\nColumnas requeridas:\n- APELLIDOS (o APELLIDO)\n- NOMBRES (o NOMBRE)\n- DNI (opcional)\n- RAZON SOCIAL (opcional)\n\nDetalle: " + msg);
        } else {
            alert("Error al importar docentes: " + msg);
        }
    } finally {
        isImporting = false;
        btn.disabled = false;
        btn.innerHTML = origText;
    }
}

let dropzoneInitialized = false;

export function setupDocentesUploadHandlers() {
    // 1. Obtener referencias directas dentro del módulo
    const dropzone = document.querySelector('[data-upload="docentes"]');
    if (!dropzone) {
        console.warn("[UPLOAD_SETUP] Dropzone [data-upload='docentes'] no encontrado");
        return;
    }

    const input = dropzone.querySelector('input[type="file"]');
    const nameEl = dropzone.querySelector('[data-file-name]');

    if (!input) {
        console.warn("[UPLOAD_SETUP] Input file no encontrado dentro del dropzone");
        return;
    }

    // Guard para evitar duplicar eventos si se llama varias veces (ej. al cambiar de pestaña)
    if (dropzoneInitialized) {
        console.log("[UPLOAD_SETUP] Dropzone ya inicializado anteriormente.");
        return;
    }

    console.log("[UPLOAD_SETUP] Vinculando eventos directos al dropzone...");

    // 2. Vincular evento directo de click
    dropzone.addEventListener("click", (e) => {
        // Evitar recursión si el click proviene del input
        if (e.target === input) return;
        input.click();
    });

    // 3. Capturar archivo (change)
    input.addEventListener("change", (e) => {
        if (e.target.files && e.target.files.length) {
            handleFileChange(e.target.files[0]);
        }
    });

    // 4. Drag & Drop (Vínculos directos)
    ['dragover', 'dragenter', 'dragleave', 'drop'].forEach(evt => {
        dropzone.addEventListener(evt, (e) => {
            e.preventDefault();
            e.stopPropagation();
        }, false);
    });

    dropzone.addEventListener('dragenter', () => {
        dropzone.classList.add('bg-indigo-50', 'border-indigo-400', 'ring-4', 'ring-indigo-100');
    });

    ['dragleave', 'dragend', 'drop'].forEach(evt => {
        dropzone.addEventListener(evt, () => {
            dropzone.classList.remove('bg-indigo-50', 'border-indigo-400', 'ring-4', 'ring-indigo-100');
        });
    });

    dropzone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files && files.length) {
            input.files = files; // Sincronizar input real
            handleFileChange(files[0]);
        }
    });

    function handleFileChange(file) {
        currentUploadFile = file;
        console.log("[UPLOAD] Archivo capturado:", file.name);
        if (nameEl) {
            nameEl.textContent = `Archivo seleccionado: ${file.name}`;
            nameEl.classList.add('text-indigo-600');
            nameEl.classList.remove('text-emerald-600');
        }
    }

    dropzoneInitialized = true;
}


function renderImportResult(payload) {
    // payload = response.data
    const { inserted = 0, updated = 0, skipped = 0 } = payload;
    const total_rows = payload.total || (inserted + updated + skipped);

    const elInserted = document.getElementById('doc-imp-inserted');
    const elUpdated  = document.getElementById('doc-imp-updated');
    const elTotal    = document.getElementById('doc-imp-total');

    if (elInserted) elInserted.textContent = inserted;
    if (elUpdated)  elUpdated.textContent  = updated;
    if (elTotal)    elTotal.textContent    = total_rows;

    renderImportTable();
}

function renderImportTable() {
    const tbody = document.getElementById('doc-import-preview');
    if (!tbody) return;
    
    if (!importData || !importData.length) {
        tbody.innerHTML = '<tr><td colspan="6" class="px-4 py-8 text-center text-slate-400">Sin detalles de filas</td></tr>';
        return;
    }

    const start = (importPage - 1) * importLimit;
    const end = start + importLimit;
    const pageItems = importData.slice(start, end);
    const totalPages = Math.ceil(importData.length / importLimit) || 1;
    
    const pgEl = document.getElementById('doc-imp-pg');
    const pgTotalEl = document.getElementById('doc-imp-pgtotal');
    const prevBtn = document.getElementById('doc-imp-prev');
    const nextBtn = document.getElementById('doc-imp-next');

    if (pgEl) pgEl.textContent = importPage;
    if (pgTotalEl) pgTotalEl.textContent = totalPages;
    if (prevBtn) prevBtn.disabled = importPage <= 1;
    if (nextBtn) nextBtn.disabled = importPage >= totalPages;
    
    tbody.innerHTML = '';
    pageItems.forEach(row => {
        const actionBadge = row.action === 'inserted' 
            ? '<span class="bg-emerald-100 text-emerald-700 text-[10px] font-black px-2 py-0.5 rounded border border-emerald-200">NUEVO</span>'
            : '<span class="bg-amber-100 text-amber-700 text-[10px] font-black px-2 py-0.5 rounded border border-amber-200">UPDATE</span>';
            
        const statusBadge = row.status === 'ACTIVO'
            ? '<span class="bg-indigo-100 text-indigo-700 text-[10px] font-black px-2 py-0.5 rounded border border-indigo-200">ACTIVO</span>'
            : `<span class="bg-rose-100 text-rose-700 text-[10px] font-black px-2 py-0.5 rounded border border-rose-200">${row.status}</span>`;

        tbody.insertAdjacentHTML('beforeend', `
            <tr class="hover:bg-slate-50 transition-colors">
                <td class="px-3 py-2 text-slate-400 font-mono text-[10px]">${row.row}</td>
                <td class="px-3 py-2 font-bold text-slate-700 uppercase">${row.apellidos}</td>
                <td class="px-3 py-2 text-slate-600 uppercase">${row.nombres}</td>
                <td class="px-3 py-2 font-mono text-xs text-slate-500">${row.dni || '—'}</td>
                <td class="px-3 py-2 text-center">${statusBadge}</td>
                <td class="px-3 py-2 text-center">${actionBadge}</td>
            </tr>
        `);
    });
}

export function changeImportPage(delta) {
    importPage += delta;
    renderImportTable();
}

// ==========================================
// CONFLICTOS & OVERRIDES
// ==========================================

export async function loadConflictos() {
    const tbody = document.getElementById('doc-conflictos-body');
    const msg = document.getElementById('conflictos-count-msg');
    const emptyState = document.getElementById('conflictos-empty');
    const infoState = document.getElementById('conflictos-info');

    if (!tbody) return;
    tbody.innerHTML = '<tr><td colspan="4" class="px-4 py-10 text-center text-slate-400"><i class="fa-solid fa-spinner fa-spin mr-2"></i>Cargando conflictos...</td></tr>';

    try {
        const payload = await api.authFetch(`${ENDPOINTS.DOCENTES.CONFLICTOS}?page=1&limit=100`);
        
        if (!payload.success) {
            tbody.innerHTML = `<tr><td colspan="4" class="px-4 py-10 text-center text-rose-500 font-bold">${payload.detail || 'Error al cargar conflictos'}</td></tr>`;
            return;
        }

        console.log('[CONFLICTOS] RAW:', payload);
        const list = extractList(payload);
        console.log('[CONFLICTOS] LIST:', list);
        console.log('[CONFLICTOS] RESPONSE:', payload);

        if (!Array.isArray(list)) {
            throw new Error('Formato inválido en conflictos');
        }

        console.log('[CONFLICTOS] ITEMS:', list.length);

        const conflictos = list;
        lastConflicts = conflictos;
        renderConflictosTable(conflictos);

        if (conflictos.length === 0) {
            emptyState?.classList.remove('hidden');
            infoState?.classList.add('hidden');
        } else {
            emptyState?.classList.add('hidden');
            infoState?.classList.remove('hidden');
            if (msg) msg.innerHTML = `Se encontraron <strong>${conflictos.length}</strong> conflictos que requieren resolución.`;
        }
    } catch (e) {
        console.error('Error cargando conflictos:', e);
        tbody.innerHTML = '<tr><td colspan="4" class="px-4 py-10 text-center text-rose-500 font-bold">Error de conexión</td></tr>';
    }
}

export const runReprocesarHistorico = loadConflictos;

export function renderConflictosTable(conflictos) {
    const tbody = document.getElementById('doc-conflictos-body');
    if (!tbody) return;
    tbody.innerHTML = '';

    if (conflictos.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" class="px-4 py-10 text-center text-slate-400">Sin conflictos detectados.</td></tr>';
        return;
    }

    conflictos.forEach((c, idx) => {
        let candidatesHtml = '';
        
        c.posibles_coincidencias.forEach(cand => {
            candidatesHtml += `
                <div class="flex items-center justify-between p-2 border border-slate-100 rounded-lg mb-1 bg-white hover:border-indigo-200 transition-colors">
                    <div>
                        <div class="font-bold text-xs text-slate-800">${cand.name}</div>
                        <div class="text-[10px] text-slate-500 font-mono">DNI: ${cand.dni || '---'}</div>
                    </div>
                    <div class="flex items-center gap-2">
                        <span class="text-[10px] font-black ${cand.score >= 0.9 ? 'text-emerald-600 bg-emerald-50' : 'text-amber-600 bg-amber-50'} px-2 py-0.5 rounded border border-transparent shadow-sm">
                            ${Math.round(cand.score * 100)}%
                        </span>
                        <div class="flex flex-col gap-1">
                            <button onclick="resolveConflict('${c.nombre_xml}', '${cand.teacher_id}', false, this)" class="bg-indigo-600 text-white text-[9px] px-2 py-1 rounded shadow hover:bg-indigo-700 transition-colors uppercase font-bold tracking-tighter" title="Resolver solo para este archivo Excel">
                                Local
                            </button>
                            <button onclick="resolveConflict('${c.nombre_xml}', '${cand.teacher_id}', true, this)" class="bg-slate-700 text-white text-[9px] px-2 py-1 rounded shadow hover:bg-slate-800 transition-colors uppercase font-bold tracking-tighter" title="Resolver para siempre (Global)">
                                Global
                            </button>
                        </div>
                    </div>
                </div>
            `;
        });

        tbody.insertAdjacentHTML('beforeend', `
            <tr class="hover:bg-slate-50 transition-colors group">
                <td class="px-4 py-3 font-bold text-rose-700 text-sm align-top">
                    <div class="flex items-center gap-2">
                        <i class="fa-solid fa-file-excel opacity-50"></i> ${c.nombre_xml}
                    </div>
                    <div class="text-[9px] text-rose-500 uppercase mt-1">${c.motivo}</div>
                </td>
                <td class="px-4 py-3 align-top" colspan="3">
                    ${candidatesHtml}
                </td>
            </tr>
        `);
    });
}

export async function resolveConflict(xmlName, teacherId, isGlobal, btnElement) {
    const originalText = btnElement.innerHTML;
    btnElement.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>';
    btnElement.disabled = true;

    try {
        const payload = await api.authFetch(ENDPOINTS.DOCENTES.RESOLVE_CONFLICT, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                xml_name_raw: xmlName,
                teacher_id: teacherId,
                is_global: isGlobal
            })
        });

        if (payload.success) {
            // Remove the row
            const tr = btnElement.closest('tr');
            if (tr) {
                tr.classList.add('opacity-0', 'scale-95');
                setTimeout(() => {
                    tr.remove();
                    // Optional: show Toast for Undo
                    showUndoToast(payload.data.override_id, xmlName);
                    
                    // AUTO REFRESH AFTER RESOLUTION
                    if (typeof loadConflictos === 'function') loadConflictos();
                    if (typeof loadSinAsignar === 'function') loadSinAsignar();
                    if (typeof loadDocentes === 'function') loadDocentes();
                }, 300);
            }
        } else {
            alert("Error: " + payload.detail);
            btnElement.innerHTML = originalText;
            btnElement.disabled = false;
        }
    } catch (e) {
        console.error("Error resolviendo conflicto:", e);
        alert("Error de conexión");
        btnElement.innerHTML = originalText;
        btnElement.disabled = false;
    }
}
window.resolveConflict = resolveConflict;

export async function undoConflict(overrideId, toastElement) {
    try {
        const payload = await api.authFetch(`${ENDPOINTS.DOCENTES.RESOLVE_CONFLICT}/${overrideId}`, {
            method: 'DELETE'
        });
        if (payload.success) {
            if (toastElement) toastElement.remove();
            
            // AUTO REFRESH AFTER UNDO
            if (typeof loadConflictos === 'function') loadConflictos();
            if (typeof loadSinAsignar === 'function') loadSinAsignar();
            if (typeof loadDocentes === 'function') loadDocentes();
        } else {
            alert("Error al deshacer: " + payload.detail);
        }
    } catch(e) {
        console.error("Error deshaciendo:", e);
    }
}
window.undoConflict = undoConflict;

function showUndoToast(overrideId, xmlName) {
    // Check if toast container exists, if not create it
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'fixed bottom-4 right-4 z-50 flex flex-col gap-2';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = 'bg-slate-800 text-white px-4 py-3 rounded-xl shadow-2xl flex items-center gap-4 text-sm font-medium animate-slide-up border border-slate-700';
    toast.innerHTML = `
        <span>Resuelto: <span class="text-emerald-400 font-bold">${xmlName}</span></span>
        <button onclick="undoConflict('${overrideId}', this.parentElement)" class="text-xs uppercase font-black text-slate-300 hover:text-white underline decoration-slate-500 hover:decoration-white transition-all ml-4">
            Deshacer
        </button>
    `;
    
    container.appendChild(toast);
    
    // Auto-remove after 8 seconds
    setTimeout(() => {
        if (toast.parentElement) {
            toast.classList.add('opacity-0');
            setTimeout(() => toast.remove(), 300);
        }
    }, 8000);
}

window.changeSinAsignarPage = changeSinAsignarPage;
window.vincularTeacherClick = vincularTeacherClick;
