// Docentes Management Module - ES6
import api from './api.js';
import { ENDPOINTS } from './config.js';

let maestraPage = 1, maestraTotalPages = 1;
let lastMaestraData = [];
let currentMergeData = [];
let sinAsignarPage = 1, sinAsignarTotalPages = 1;
let currentStatusTarget = null;

// Tab management
const DOC_TABS = ['upload-excel', 'maestra', 'sinasignar', 'conflictos'];

export function toggleDocentesTab(tab) {
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

    if (tab === 'maestra') loadMaestra(1);
    if (tab === 'sinasignar') loadSinAsignar(1);
}

// Maestra Table
export async function loadMaestra(page = 1) {
    maestraPage = page;
    const statusFilter = document.getElementById('doc-status-filter')?.value || 'all';
    const search = encodeURIComponent(document.getElementById('doc-search')?.value.trim() || '');
    
    try {
        const data = await api.authFetch(`${ENDPOINTS.DOCENTES.BASE}?status_filter=${statusFilter}&search=${search}&page=${page}&limit=20`);
        
        lastMaestraData = data.data || [];
        maestraTotalPages = data.total_pages || 1;
        
        const totalEl = document.getElementById('doc-maestra-total');
        if (totalEl) totalEl.textContent = data.total || 0;
        
        const indicatorEl = document.getElementById('doc-maestra-indicator');
        if (indicatorEl) indicatorEl.textContent = `${page} / ${maestraTotalPages}`;
        
        const prevBtn = document.getElementById('doc-maestra-prev');
        if (prevBtn) prevBtn.disabled = page <= 1;
        
        const nextBtn = document.getElementById('doc-maestra-next');
        if (nextBtn) nextBtn.disabled = page >= maestraTotalPages;
        
        const tbody = document.getElementById('doc-maestra-body');
        if (!tbody) return;
        
        tbody.innerHTML = '';
        if (!lastMaestraData.length) {
            tbody.innerHTML = '<tr><td colspan="7" class="px-4 py-10 text-center text-slate-400">Sin resultados</td></tr>';
            return;
        }

        lastMaestraData.forEach(t => {
            const activeBadge = t.is_active
                ? `<button data-action="handleStatusClick('${t.id}', true, '${t.last_name}, ${t.first_name}')" class="bg-emerald-100 text-emerald-700 text-[10px] font-black px-3 py-1 rounded-full border border-emerald-200 hover:bg-emerald-200 transition-colors shadow-sm">ACTIVO</button>`
                : `<button data-action="handleStatusClick('${t.id}', false, '${t.last_name}, ${t.first_name}')" class="bg-rose-100 text-rose-700 text-[10px] font-black px-3 py-1 rounded-full border border-rose-200 hover:bg-rose-200 transition-colors shadow-sm">INACTIVO</button>`;

            tbody.insertAdjacentHTML('beforeend', `
                <tr class="hover:bg-slate-50 transition-colors" data-teacher-id="${t.id}">
                    <td class="px-4 py-3 w-10">
                        <input type="checkbox" data-id="${t.id}" data-action="updateMergeSelection" class="merge-checkbox rounded border-slate-300 text-indigo-600 focus:ring-indigo-500">
                    </td>
                    <td class="px-4 py-3 font-bold text-slate-800">
                        ${t.last_name}
                        ${t.is_potential_duplicate ? '<i class="fa-solid fa-triangle-exclamation text-amber-500 ml-1" title="Posible duplicado detectado"></i>' : ''}
                    </td>
                    <td class="px-4 py-3 text-slate-700">${t.first_name}</td>
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
    } catch(e) { console.error('loadMaestra:', e); }
}

export function changeMaestraPage(delta) { 
    loadMaestra(maestraPage + delta); 
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

    const teachers = lastMaestraData.filter(t => selectedIds.includes(t.id));
    if (teachers.length !== 2) {
        alert('Error al cargar datos. Por favor, refresca la tabla e intenta de nuevo.');
        return;
    }
    
    currentMergeData = teachers;
    
    [0, 1].forEach(i => {
        const t = teachers[i];
        document.getElementById(`merge-name-${i}`).textContent = `${t.last_name}, ${t.first_name}`;
        document.getElementById(`merge-dni-${i}`).textContent = t.dni || 'SIN DNI';
        document.getElementById(`merge-rs-${i}`).textContent = t.razon_social || '—';
        
        const badgeContainer = document.getElementById(`merge-badge-${i}`);
        if (badgeContainer) {
            badgeContainer.innerHTML = t.is_potential_duplicate 
                ? '<span class="bg-amber-100 text-amber-700 text-[10px] font-black px-2 py-0.5 rounded-full">POSIBLE DUPLICADO</span>'
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

    if (!confirm(`¿Confirmar fusión?\n\nPrincipal: ${main.last_name} (SE CONSERVA)\nSecundario: ${merge.last_name} (SE ELIMINA)`)) return;

    const btn = document.getElementById('btn-confirm-merge');
    if (!btn) return;
    const origText = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin mr-1"></i> Iniciando fusión...';

    try {
        const data = await api.authFetch(`${ENDPOINTS.DOCENTES.BASE}/fusionar`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ teacher_main_id: main.id, teacher_merge_id: merge.id })
        });
        // El wrapper authFetch ya lanza error si !res.ok
        
        alert('✅ Fusión exitosa. El sistema ha consolidado las lecciones y eliminado el registro duplicado.');
        closeMergeModal();
        loadMaestra(maestraPage);
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
                loadMaestra(maestraPage);
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
    const teacher = lastMaestraData.find(t => t.id === id);
    openTeacherModal(teacher);
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
    const id = document.getElementById('teacher-modal-id').value;
    const body = {
        last_name:    document.getElementById('teacher-modal-lastname').value.trim(),
        first_name:   document.getElementById('teacher-modal-firstname').value.trim(),
        dni:          document.getElementById('teacher-modal-dni').value.trim(),
        razon_social: document.getElementById('teacher-modal-razon').value.trim(),
    };

    if (!body.last_name || !body.first_name) {
        alert("Apellidos y Nombres son obligatorios.");
        return;
    }

    const btn = document.getElementById('btn-save-teacher');
    const origText = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = "Guardando...";

    try {
        const method = id ? 'PUT' : 'POST';
        const url = id ? `${ENDPOINTS.DOCENTES.BASE}/${id}` : ENDPOINTS.DOCENTES.BASE;
        const data = await api.authFetch(url, {
            method,
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(body)
        });
        if (data.success) {
            closeTeacherModal();
            loadMaestra(maestraPage);
        } else {
            alert('Error: ' + (data.detail || 'No se pudo guardar.'));
        }
    } catch(e) {
        alert('Error de conexión');
    } finally {
        btn.disabled = false;
        btn.innerHTML = origText;
    }
}

// Sin Asignar Table
export async function loadSinAsignar(page = 1) {
    sinAsignarPage = page;
    try {
        const data = await api.authFetch(`${ENDPOINTS.DOCENTES.SIN_ASIGNAR}?page=${page}&limit=20`);
        
        sinAsignarTotalPages = data.total_pages || 1;
        document.getElementById('doc-sin-total').textContent = data.total || 0;
        document.getElementById('doc-sin-indicator').textContent = `${page} / ${sinAsignarTotalPages}`;
        document.getElementById('doc-sin-prev').disabled = page <= 1;
        document.getElementById('doc-sin-next').disabled = page >= sinAsignarTotalPages;
        
        const tbody = document.getElementById('doc-sin-body');
        if (!tbody) return;
        
        tbody.innerHTML = '';
        if (!data.data.length) {
            tbody.innerHTML = '<tr><td colspan="5" class="px-4 py-10 text-center text-slate-400">Todo al día</td></tr>';
            return;
        }

        data.data.forEach(t => {
            const dateStr = t.last_seen_at ? new Date(t.last_seen_at).toLocaleDateString() : '—';
            const fuzzyBadge = t.possible_duplicate 
                ? '<span class="bg-amber-100 text-amber-700 text-[10px] px-2 py-0.5 rounded-full ml-1">Fuzzy-Match Detectado</span>' 
                : '';
            
            tbody.insertAdjacentHTML('beforeend', `<tr>
                <td class="px-4 py-3 font-bold text-slate-800">${t.last_name}, ${t.first_name} ${fuzzyBadge}</td>
                <td class="px-4 py-3 text-center text-slate-500">${t.times_detected}</td>
                <td class="px-4 py-3 text-center text-slate-500 font-mono text-xs">${dateStr}</td>
                <td class="px-4 py-3 text-center"><span class="bg-slate-100 text-slate-600 text-[10px] uppercase font-bold px-2 py-1 rounded">${t.source}</span></td>
                <td class="px-4 py-3 text-right">
                    <button data-action="openTeacherModal" class="text-indigo-600 hover:underline text-xs font-bold">Vincular/Crear</button>
                </td>
            </tr>`);
        });
    } catch(e) { console.error('loadSinAsignar:', e); }
}

// Import Logic
let importData = [];
let importPage = 1;
const importLimit = 10;
let isImporting = false;
let currentUploadFile = null;

export async function uploadDocentesExcel() {
    if (isImporting) return;

    const fileInput = document.getElementById('doc-file-upload');
    // Prioridad al archivo capturado por eventos (Drag&Drop/Change)
    const file = currentUploadFile || fileInput?.files[0];
    
    console.log("[IMPORT] Iniciando proceso...");
    console.log("[IMPORT] File Status:", file ? `${file.name} (${file.size} bytes)` : "No file");

    if (!file) {
        alert("⚠️ Por favor, seleccione un archivo Excel antes de importar.");
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
        const data = await api.authFetch(ENDPOINTS.DOCENTES.IMPORT, {
            method: 'POST',
            body: formData
        });

        console.log("[IMPORT] Respuesta del servidor:", data);
        
        // Validación de datos antes de renderizar
        if (!data || typeof data !== 'object') {
            throw new Error("Respuesta inválida del servidor");
        }

        importData = data.detail_rows || [];
        importPage = 1;
        
        // Renderizado Seguro
        try {
            renderImportResult(data);
            const resultContainer = document.getElementById('doc-import-result');
            if (resultContainer) {
                resultContainer.classList.remove('hidden');
                resultContainer.scrollIntoView({ behavior: 'smooth' });
            }
        } catch (renderErr) {
            console.error("[IMPORT] Error en renderización:", renderErr);
            alert("✅ Importación completada, pero hubo un problema al mostrar los resultados. Por favor, verifique la pestaña 'MAESTRA'.");
        }
        
        // Limpiar estado de selección
        currentUploadFile = null;
        if (fileInput) fileInput.value = '';
        
        const nameEl = document.getElementById('doc-file-name');
        if (nameEl) {
            nameEl.textContent = '¡Carga completada con éxito!';
            nameEl.classList.remove('text-indigo-600');
            nameEl.classList.add('text-emerald-600');
            
            setTimeout(() => {
                nameEl.textContent = 'Arrastra tu Excel o haz clic aquí';
                nameEl.classList.remove('text-emerald-600');
            }, 5000);
        }

    } catch (e) {
        console.error("[IMPORT] Error crítico:", e);
        alert("❌ Error al importar docentes: " + e.message);
    } finally {
        isImporting = false;
        btn.disabled = false;
        btn.innerHTML = origText;
    }
}

export function setupDocentesUploadHandlers() {
    const dropzone = document.getElementById('doc-drop-zone');
    const input = document.getElementById('doc-file-upload');
    const nameEl = document.getElementById('doc-file-name');

    if (!dropzone || !input) {
        console.warn("[UPLOAD_SETUP] Elementos no encontrados para Docentes Upload");
        return;
    }

    // 1. Click -> Trigger Input
    dropzone.onclick = (e) => {
        e.preventDefault();
        input.click();
    };

    // 2. Drag & Drop con protección total
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

    // 3. Input Change
    input.onchange = (e) => {
        if (e.target.files && e.target.files.length) {
            handleFileChange(e.target.files[0]);
        }
    };

    function handleFileChange(file) {
        currentUploadFile = file;
        console.log("[UPLOAD] Archivo capturado:", file.name);
        if (nameEl) {
            nameEl.textContent = `Archivo seleccionado: ${file.name}`;
            nameEl.classList.add('text-indigo-600');
            nameEl.classList.remove('text-emerald-600');
        }
    }
}

function renderImportResult(data) {
    const elInserted = document.getElementById('doc-imp-inserted');
    const elUpdated = document.getElementById('doc-imp-updated');
    const elTotal = document.getElementById('doc-imp-total');

    if (elInserted) elInserted.textContent = data.inserted ?? 0;
    if (elUpdated) elUpdated.textContent = data.updated ?? 0;
    if (elTotal) elTotal.textContent = data.total_rows ?? 0;
    
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
        const actionBadge = row.action === 'INSERT' 
            ? '<span class="bg-emerald-100 text-emerald-700 text-[10px] font-black px-2 py-0.5 rounded border border-emerald-200">NUEVO</span>'
            : '<span class="bg-amber-100 text-amber-700 text-[10px] font-black px-2 py-0.5 rounded border border-amber-200">UPDATE</span>';
            
        tbody.insertAdjacentHTML('beforeend', `
            <tr class="hover:bg-slate-50 transition-colors">
                <td class="px-3 py-2 text-slate-400 font-mono text-[10px]">${row.row_index}</td>
                <td class="px-3 py-2 font-bold text-slate-700 uppercase">${row.last_name}</td>
                <td class="px-3 py-2 text-slate-600 uppercase">${row.first_name}</td>
                <td class="px-3 py-2 font-mono text-xs text-slate-500">${row.dni || '—'}</td>
                <td class="px-3 py-2 text-xs text-slate-400 max-w-[150px] truncate">${row.razon_social || '—'}</td>
                <td class="px-3 py-2 text-center">${actionBadge}</td>
            </tr>
        `);
    });
}

export function changeImportPage(delta) {
    importPage += delta;
    renderImportTable();
}
