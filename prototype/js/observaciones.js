import api from './api.js';
import { ENDPOINTS, API_BASE_URL } from './config.js';
import { getCalculatedTime, cleanCycleName, getCourseColor, extractList } from './ui_utils.js';

// State
let currentSessionForObs = null;
let currentRowElementForObs = null;

// Mandatory Lifecycle Initialization
export async function initObservaciones() {
    console.log("[OBS MODULE INIT] Bootstrapping observations lifecycle.");
    try {
        // Set default dates if not present
        const startEl = document.getElementById('obs-date-start');
        const endEl = document.getElementById('obs-date-end');
        if (startEl && !startEl.value) {
            const curr = new Date();
            const mondayDiff = curr.getDate() - curr.getDay() + (curr.getDay() === 0 ? -6 : 1);
            const monday = new Date(new Date().setDate(mondayDiff));
            const sunday = new Date(monday);
            sunday.setDate(sunday.getDate() + 6);
            
            startEl.value = monday.toISOString().split('T')[0];
            if (endEl) endEl.value = sunday.toISOString().split('T')[0];
        }

        await loadObsTeacherList();
        console.log("[OBS MODULE READY] Lifecycle bootstrapped completely.");
    } catch (error) {
        console.error("[OBS ERROR] Failed to initialize module:", error);
    }
}

export function toggleObsTab(tabName) {
    const regTab = document.getElementById('obs-tab-register');
    const logsTab = document.getElementById('obs-tab-logs');
    const regBtn = document.getElementById('tab-btn-register');
    const logsBtn = document.getElementById('tab-btn-logs');

    if (!regTab || !logsTab) return;

    if (tabName === 'register') {
        regTab.classList.remove('hidden');
        logsTab.classList.add('hidden');
        if (regBtn) regBtn.className = "px-8 py-4 text-sm font-black border-b-2 border-indigo-600 text-indigo-600 transition-all uppercase tracking-widest";
        if (logsBtn) logsBtn.className = "px-8 py-4 text-sm font-black border-b-2 border-transparent text-slate-400 hover:text-slate-600 transition-all uppercase tracking-widest";
    } else {
        regTab.classList.add('hidden');
        logsTab.classList.remove('hidden');
        if (logsBtn) logsBtn.className = "px-8 py-4 text-sm font-black border-b-2 border-indigo-600 text-indigo-600 transition-all uppercase tracking-widest";
        if (regBtn) regBtn.className = "px-8 py-4 text-sm font-black border-b-2 border-transparent text-slate-400 hover:text-slate-600 transition-all uppercase tracking-widest";
        loadObsLogs();
    }
}

export async function loadObsTeacherList() {
    const select = document.getElementById('obs-filter-docente');
    const datalist = document.getElementById('teachers-datalist');
    if (!select) return;
    
    console.log("[OBS FETCH] Querying active instructional staff via HORARIOS API...");
    
    try {
        const response = await api.authFetch(`${ENDPOINTS.HORARIOS.BASE}/teachers`);
        
        console.log("[OBS RESPONSE] Data received:", response);

        // ✅ USO DE HELPER CENTRALIZADO
        const teachers = extractList(response);
        console.log(`[OBS REPLACEMENT TEACHERS] Scanning system for validated instructional personnel. Total Candidates: ${teachers.length}`);

        select.innerHTML = '<option value="">Selecciona un docente...</option>';
        if (datalist) datalist.innerHTML = '';

        if (Array.isArray(teachers) && teachers.length > 0) {
            teachers.forEach(t => {
                const fullName = `${t.last_name || ''}, ${t.first_name || ''}`.trim() || `Docente ${t.id}`;
                const opt = document.createElement('option');
                opt.value = t.id;
                opt.textContent = fullName;
                select.appendChild(opt);

                if (datalist) {
                    const dOpt = document.createElement('option');
                    dOpt.value = fullName;
                    dOpt.setAttribute('data-id', t.id);
                    datalist.appendChild(dOpt);
                }
            });
            console.log(`[OBS REPLACEMENT FILTERED] Successfully resolved and hydrated replacement datalists with ${teachers.length} verified entities.`);
            console.log(`[OBS FILTER RESULT] Found and injected ${teachers.length} potential candidates.`);
        } else {
            console.warn("[OBS EMPTY STATE] No actionable instructional personnel identified in scope.");
            select.innerHTML = '<option value="">No hay docentes activos</option>';
        }
    } catch (e) {
        console.error("[OBS ERROR] Failed loading teachers for obs:", e);
        select.innerHTML = '<option value="">Error al cargar docentes</option>';
    }
}

export async function searchClassesForObs() {
    const selDoc = document.getElementById('obs-filter-docente');
    const teacherId = selDoc?.value;
    const teacherName = selDoc?.options[selDoc.selectedIndex]?.text || "Docente";
    const dateStart = document.getElementById('obs-date-start')?.value;
    const dateEnd = document.getElementById('obs-date-end')?.value;
    const tbody = document.getElementById('obs-search-body');

    if (!teacherId || !dateStart || !dateEnd) {
        alert("Por favor completa todos los filtros de búsqueda.");
        return;
    }
    
    console.log(`[OBS FETCH] Triggering session lookup for Docente=${teacherName} Range=${dateStart} to ${dateEnd}`);

    if (tbody) tbody.innerHTML = '<tr><td colspan="5" class="px-4 py-12 text-center text-slate-400"><i class="fa-solid fa-spinner fa-spin text-xl mb-2"></i> Buscando clases...</td></tr>';

    try {
        const url = `${ENDPOINTS.HORARIOS.BASE}/sessions-for-obs?teacher_id=${teacherId}&start_date=${dateStart}&end_date=${dateEnd}`;
        const response = await api.authFetch(url);
        
        console.log("[OBS RESPONSE] Grouped sessions dataset acquired:", response);

        // ✅ USO DE HELPER CENTRALIZADO
        const sessions = extractList(response);

        if (tbody) {
            tbody.innerHTML = '';
            if (sessions.length === 0) {
                console.log("[OBS EMPTY STATE] Filter constraints produced zero target sessions.");
                tbody.innerHTML = '<tr><td colspan="5" class="px-4 py-12 text-center text-slate-400 italic">No se encontraron sesiones en este rango de fechas.</td></tr>';
                return;
            }

            sessions.forEach(s => {
                const tr = document.createElement('tr');
                const sids = (s.session_ids || [s.id]).join(',');
                tr.setAttribute('data-session-ids', sids);
                tr.className = "hover:bg-slate-50 transition-colors border-b border-slate-100 group";

                const sessionData = { ...s, docente_name: teacherName, teacher_id: teacherId };
                const hasObs = s.badge && s.badge !== 'INGRESAR';

                let actionHtml = `
                    <button data-action="openRegisterObsModalClick" class="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-xl text-xs font-black uppercase tracking-widest transition-all">
                        Registrar
                    </button>
                `;

                if (hasObs) {
                    let badgeColor = 'bg-rose-50 text-rose-700 border-rose-200';
                    if (s.badge === 'REEMPLAZO') badgeColor = 'bg-amber-50 text-amber-700 border-amber-200';
                    else if (s.badge === 'FALTA/REEMP') badgeColor = 'bg-indigo-50 text-indigo-700 border-indigo-200';

                    actionHtml = `<span class="${badgeColor} px-2 py-0.5 rounded-lg text-[9px] font-black uppercase tracking-tighter border shadow-sm"><i class="fa-solid fa-circle-check mr-1 text-[8px]"></i> ${s.badge}</span>`;
                }

                tr.setAttribute('data-session-json', JSON.stringify(sessionData));

                tr.innerHTML = `
                    <td class="px-4 py-4 font-bold text-slate-800 whitespace-nowrap">${s.date}</td>
                    <td class="px-4 py-4">${s.subject || '---'}</td>
                    <td class="px-4 py-4"><span class="bg-slate-100 px-2 py-1 rounded text-xs font-bold uppercase">${s.class_group || '---'}</span></td>
                    <td class="px-4 py-4 font-mono text-xs text-slate-500">${s.start_time.substring(0, 5)} - ${s.end_time.substring(0, 5)}</td>
                    <td class="px-4 py-4 text-right action-cell">${actionHtml}</td>
                `;
                tbody.appendChild(tr);
            });
            console.log(`[OBS RENDER] Successfully rendered ${sessions.length} interactive scheduling entities.`);
        }
    } catch (e) { console.error("Error searching classes:", e); }
}

export function openRegisterObsModalClick(e) {
    const tr = e.target.closest('tr');
    const data = JSON.parse(tr.getAttribute('data-session-json'));
    openRegisterObsModal(data, tr);
}

export function openRegisterObsModal(session, rowElement) {
    currentSessionForObs = session;
    currentRowElementForObs = rowElement || null;
    
    document.getElementById('obs-form-session-id').value = session.id;
    document.getElementById('obs-form-teacher-id').value = session.teacher_id;
    document.getElementById('obs-modal-teacher-name').innerText = session.docente_name || "Docente";
    document.getElementById('obs-modal-date').innerText = `${session.date} (${session.start_time.substring(0, 5)} - ${session.end_time.substring(0, 5)})`;

    document.querySelector('input[name="obs-block-mode"][value="full"]').checked = true;
    document.getElementById('obs-form-type').value = 'FALTA';
    document.getElementById('obs-form-discount').value = 'SIMPLE';
    
    // Clear replacement elements
    const searchInput = document.getElementById('obs-form-replacement-search');
    if (searchInput) {
        searchInput.value = '';
        searchInput.disabled = false;
    }
    const isNewCheck = document.getElementById('obs-form-replacement-is-new');
    if (isNewCheck) isNewCheck.checked = false;
    
    const infoBox = document.getElementById('obs-replacement-external-info');
    if (infoBox) infoBox.classList.add('hidden');

    document.getElementById('obs-form-description').value = '';

    toggleObsBlockMode(true);
    document.getElementById('obs-register-modal')?.classList.remove('hidden');
}

export function toggleObsBlockMode(isFull) {
    const singleCont = document.getElementById('obs-single-mode-container');
    const splitCont = document.getElementById('obs-split-mode-container');
    if (!singleCont || !splitCont) return;

    if (isFull === true || isFull === 'full') {
        singleCont.classList.remove('hidden');
        splitCont.classList.add('hidden');
        handleObsTypeChange();
    } else {
        console.log("[OBS SPLIT BLOCK] Attempting to decompose composite academic block into discrete temporal durations.");
        singleCont.classList.add('hidden');
        splitCont.classList.remove('hidden');
        renderPedagogicalSlots();
    }
}

function renderPedagogicalSlots() {
    const container = document.getElementById('obs-split-mode-container');
    if (!container || !currentSessionForObs) return;

    const start = currentSessionForObs.start_time;
    const end = currentSessionForObs.end_time;
    const slots = splitIntoPedagogicalHours(start, end);

    console.log(`[OBS LESSON GENERATED] Academic segmentator derived ${slots.length} elemental entities from temporal span ${start} to ${end}.`);

    container.innerHTML = `<p class="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2">Desglose: ${slots.length} h. pedagógicas</p>`;

    slots.forEach((slot, idx) => {
        const slotDiv = document.createElement('div');
        slotDiv.className = "obs-slot-item bg-white border border-slate-200 rounded-xl p-4 shadow-sm space-y-3 mb-2";
        slotDiv.innerHTML = `
            <div class="flex justify-between items-center">
                <span class="text-xs font-black text-indigo-600 bg-indigo-50 px-2 py-1 rounded">Hora ${idx + 1}: ${slot.start} - ${slot.end}</span>
                <select class="obs-slot-type text-[10px] font-bold border-none bg-slate-100 rounded-md px-2 py-1 focus:ring-0" data-idx="${idx}" data-action="toggleSlotReplacement">
                    <option value="NINGUNA">SIN INCIDENCIA</option>
                    <option value="FALTA" selected>FALTA</option>
                    <option value="REEMPLAZO">REEMPLAZO</option>
                </select>
            </div>
            <div id="slot-replacement-container-${idx}" class="hidden mt-2 pt-2 border-t border-slate-100 space-y-2">
                <input type="search" class="obs-slot-replacement-search w-full px-3 py-2 bg-white border border-slate-200 rounded-lg text-xs" list="teachers-datalist" placeholder="Buscar reemplazo...">
                <input type="text" class="obs-slot-replacement-external-name hidden w-full px-3 py-2 bg-amber-50 border border-amber-200 rounded-lg text-xs text-amber-800 placeholder:text-amber-400" placeholder="Apellidos y Nombres del docente externo">
                <div class="flex items-center gap-2 bg-slate-50 p-2 rounded-lg border border-slate-100">
                    <input type="checkbox" class="obs-slot-replacement-is-new w-3 h-3 text-indigo-600" data-idx="${idx}" data-action="toggleSlotNewTeacherMode">
                    <label class="text-[9px] font-bold text-slate-500 uppercase">¿Docente externo?</label>
                </div>
            </div>
            <input type="hidden" class="obs-slot-start" value="${slot.start}">
            <input type="hidden" class="obs-slot-end" value="${slot.end}">
        `;
        container.appendChild(slotDiv);
    });
}

export function toggleSlotReplacement(e) {
    const idx = e.target.getAttribute('data-idx');
    const value = e.target.value;
    const container = document.getElementById(`slot-replacement-container-${idx}`);
    if (container) container.classList.toggle('hidden', value !== 'REEMPLAZO');
}

export function toggleSlotNewTeacherMode(e) {
    const idx = e.target.getAttribute('data-idx');
    const isChecked = e.target.checked;
    const container = document.getElementById(`slot-replacement-container-${idx}`);
    if (container) {
        const search = container.querySelector('.obs-slot-replacement-search');
        const extName = container.querySelector('.obs-slot-replacement-external-name');
        if (search) {
            search.classList.toggle('hidden', isChecked);
            if (isChecked) search.value = '';
        }
        if (extName) {
            extName.classList.toggle('hidden', !isChecked);
            if (!isChecked) extName.value = '';
        }
    }
}

export function toggleNewTeacherMode() {
    const isNew = document.getElementById('obs-form-replacement-is-new')?.checked;
    const searchInput = document.getElementById('obs-form-replacement-search');
    const extNameInput = document.getElementById('obs-form-replacement-external-name');
    
    if (searchInput) {
        searchInput.classList.toggle('hidden', !!isNew);
        if (isNew) searchInput.value = '';
    }
    if (extNameInput) {
        extNameInput.classList.toggle('hidden', !isNew);
        if (!isNew) extNameInput.value = '';
    }
}

function getTeacherIdFromSearch(searchValue) {
    if (!searchValue) return null;
    const dl = document.getElementById('teachers-datalist');
    if (!dl) return null;
    const option = Array.from(dl.options).find(o => o.value === searchValue);
    return option ? option.getAttribute('data-id') : null;
}

function splitIntoPedagogicalHours(startTime, endTime) {
    const parse = t => {
        const [h, m] = t.split(':').map(Number);
        return h * 60 + m;
    };
    const format = m => {
        const h = Math.floor(m / 60);
        const mins = m % 60;
        return `${String(h).padStart(2, '0')}:${String(mins).padStart(2, '0')}`;
    };

    const startMins = parse(startTime);
    const endMins = parse(endTime);
    const slots = [];
    let current = startMins;

    while (current < endMins) {
        let next = current + 50;
        if (next > endMins) next = endMins;
        if (endMins - next < 15 && endMins - next > 0) next = endMins;
        slots.push({ start: format(current), end: format(next) });
        current = next;
    }
    return slots;
}

export function handleObsTypeChange() {
    const type = document.getElementById('obs-form-type')?.value;
    const container = document.getElementById('obs-replacement-container');
    if (container) container.classList.toggle('hidden', type !== 'REEMPLAZO');
}

export async function saveObservation() {
    const isFullBlock = document.querySelector('input[name="obs-block-mode"]:checked').value === 'full';
    const sessionId = currentSessionForObs?.id;
    const teacherId = currentSessionForObs?.teacher_id;

    let payloads = [];
    const sessionIds = currentSessionForObs?.session_ids || (sessionId ? [sessionId] : []);
    
    if (sessionIds.length === 0) return alert("⚠️ Error fatal: Bloque sin identificador de sesión.");

    if (isFullBlock) {
        const type = document.getElementById('obs-form-type').value;
        const discount = document.getElementById('obs-form-discount').value;
        const description = document.getElementById('obs-form-description').value;
        
        const isExternal = document.getElementById('obs-form-replacement-is-new')?.checked || false;
        const searchVal = document.getElementById('obs-form-replacement-search')?.value;
        const extNameVal = document.getElementById('obs-form-replacement-external-name')?.value;
        const replId = type === 'REEMPLAZO' && !isExternal ? getTeacherIdFromSearch(searchVal) : null;

        if (type === 'REEMPLAZO' && !isExternal && !replId) {
            return alert("Debe seleccionar un docente válido del buscador.");
        }
        if (type === 'REEMPLAZO' && isExternal && (!extNameVal || extNameVal.trim().length < 5)) {
            return alert("Para docentes externos es obligatorio ingresar sus Apellidos y Nombres.");
        }

        // Solo empujar payloads si NO es NINGUNA
        if (type !== 'NINGUNA') {
            sessionIds.forEach(sid => {
                payloads.push({
                    session_id: sid,
                    teacher_id: teacherId,
                    type,
                    discount_type: discount,
                    replacement_teacher_id: replId,
                    replacement_teacher_name: isExternal ? extNameVal.trim() : null,
                    replacement_is_external: isExternal,
                    description,
                    start_time: currentSessionForObs.start_time,
                    end_time: currentSessionForObs.end_time
                });
            });
        }
    } else {
        const slotDivs = document.getElementById('obs-split-mode-container').querySelectorAll('.obs-slot-item');
        console.log(`[OBS PARTIAL ABSENCE] Analyzing ${slotDivs.length} segmented instances for partial incidence injection.`);
        
        for (let i = 0; i < slotDivs.length; i++) {
            const div = slotDivs[i];
            const type = div.querySelector('.obs-slot-type').value;
            if (type === 'NINGUNA') continue;

            const isExt = div.querySelector('.obs-slot-replacement-is-new')?.checked || false;
            const sVal = div.querySelector('.obs-slot-replacement-search')?.value;
            const extNameVal = div.querySelector('.obs-slot-replacement-external-name')?.value;
            const rId = type === 'REEMPLAZO' && !isExt ? getTeacherIdFromSearch(sVal) : null;

            if (type === 'REEMPLAZO' && !isExt && !rId) {
                alert(`Hora ${i + 1}: Debe seleccionar un docente válido del buscador.`);
                return;
            }
            if (type === 'REEMPLAZO' && isExt) {
                if (!extNameVal || extNameVal.trim().length < 5) {
                    alert(`Hora ${i + 1}: Es obligatorio ingresar los Apellidos y Nombres del docente externo.`);
                    return;
                }
                payloads.push({
                    session_id: sessionIds[0] || sessionId,
                    teacher_id: teacherId,
                    type,
                    discount_type: 'SIMPLE',
                    replacement_teacher_id: null,
                    replacement_teacher_name: extNameVal.trim(),
                    replacement_is_external: true,
                    description: `Desglosado (Hora ${i + 1})`,
                    start_time: div.querySelector('.obs-slot-start').value,
                    end_time: div.querySelector('.obs-slot-end').value
                });
                continue;
            }

            payloads.push({
                session_id: sessionIds[0] || sessionId,
                teacher_id: teacherId,
                type,
                discount_type: 'SIMPLE',
                replacement_teacher_id: rId,
                replacement_teacher_name: null,
                replacement_is_external: false,
                description: `Desglosado (Hora ${i + 1})`,
                start_time: div.querySelector('.obs-slot-start').value,
                end_time: div.querySelector('.obs-slot-end').value
            });
        }
    }

    // Permitir limpiar bloque completo si no quedan incidencias
    if (payloads.length === 0) {
        if (!confirm("Ha configurado el bloque sin incidencias activas. Esto ELIMINARÁ definitivamente cualquier falta o reemplazo registrado previamente para estas horas. ¿Desea proceder?")) {
            return;
        }
    }

    if (payloads.length > 0 && payloads.some(p => !p.session_id)) {
        return alert("⚠️ Error fatal: Faltan IDs de sesión en los segmentos.");
    }

    try {
        await api.authFetch(`${ENDPOINTS.HORARIOS.BASE}/observations/batch`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                observations: payloads,
                affected_session_ids: sessionIds
            })
        });

        console.log(`[OBS BATCH SAVED] Propagated successfully across ${sessionIds.length} sessions.`);
        closeObsRegisterModal();
        
        const row = currentRowElementForObs;
        if (row) {
            const actionCell = row.querySelector('.action-cell');
            if (payloads.length === 0) {
                // Restaurar botón Registrar
                if (actionCell) actionCell.innerHTML = `<button data-action="registerObs" class="text-[10px] font-bold text-indigo-600 hover:text-indigo-800 bg-indigo-50 hover:bg-indigo-100 px-2.5 py-1.5 rounded-lg transition-colors"><i class="fa-solid fa-plus-circle mr-1"></i> Registrar</button>`;
            } else {
                const types = [...new Set(payloads.map(p => p.type))];
                const label = types.length > 1 ? 'FALTA/REEMP' : types[0];
                let badgeColor = label === 'REEMPLAZO' ? 'bg-amber-50 text-amber-700 border-amber-200' : (label === 'FALTA/REEMP' ? 'bg-indigo-50 text-indigo-700 border-indigo-200' : 'bg-rose-50 text-rose-700 border-rose-200');
                if (actionCell) actionCell.innerHTML = `<span class="${badgeColor} px-2 py-0.5 rounded-lg text-[9px] font-black uppercase tracking-tighter border shadow-sm"><i class="fa-solid fa-circle-check mr-1 text-[8px]"></i> ${label}</span>`;
            }
        } else {
            searchClassesForObs();
        }
    } catch (e) { 
        console.error("[OBS BATCH PERSISTENCE ERROR]", e);
        alert("Error de conexión o persistencia al guardar las incidencias."); 
    }
}

export function closeObsRegisterModal() {
    document.getElementById('obs-register-modal')?.classList.add('hidden');
}

export async function deleteObservation(obsId) {
    if (!confirm("¿Eliminar esta incidencia?")) return;
    try {
        const data = await api.authFetch(`${ENDPOINTS.HORARIOS.BASE}/observations/${obsId}`, { method: 'DELETE' });
        if (data.success) {
            // Decoupled from cross-module refreshes to enforce pure modular bounds
            loadObsLogs();
        }
    } catch (e) { alert("Error al eliminar"); }
}

export async function loadObsLogs() {
    const tbody = document.getElementById('obs-logs-body');
    if (!tbody) return;
    try {
        console.log("[OBS FETCH] Fetching recent transaction logs...");
        const response = await api.authFetch(`${ENDPOINTS.HORARIOS.BASE}/observations/logs?limit=50`);
        console.log("[OBS RESPONSE] Activity logs stream retrieved.", response);

        // ✅ USO DE HELPER CENTRALIZADO
        const logs = extractList(response);
        
        tbody.innerHTML = '';
        if (logs.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="p-10 text-center text-slate-400 italic">No hay logs de incidencias</td></tr>';
            return;
        }
        logs.forEach(log => {
            let typeBadge = 'bg-rose-100 text-rose-700';
            if (log.type === 'REEMPLAZO') typeBadge = 'bg-amber-100 text-amber-700';
            
            tbody.insertAdjacentHTML('beforeend', `
                <tr class="hover:bg-slate-50 transition-colors border-b border-slate-100">
                    <td class="px-4 py-3 text-xs font-medium text-slate-600">${log.date_record || '---'}</td>
                    <td class="px-4 py-3 text-xs font-mono">${log.user || 'SISTEMA'}</td>
                    <td class="px-4 py-3 font-bold text-slate-800">${log.teacher_affected || 'N/A'}</td>
                    <td class="px-4 py-3"><span class="${typeBadge} px-2 py-0.5 rounded text-[10px] font-black uppercase">${log.type}</span></td>
                    <td class="px-4 py-3 font-bold text-indigo-600">${log.class_date || 'N/A'}</td>
                    <td class="px-4 py-3 text-xs text-slate-500">${log.description || '---'}</td>
                    <td class="px-4 py-3 text-right">
                        <button data-action="deleteObservation('${log.id}')" class="text-slate-300 hover:text-rose-600 p-1 transition-colors" title="Eliminar"><i class="fa-solid fa-trash text-sm"></i></button>
                    </td>
                </tr>
            `);
        });
        console.log(`[OBS RENDER] Visualized ${logs.length} audited interaction entries.`);
    } catch (e) { console.error("[OBS ERROR] Event stream rendering fault:", e); }
}

