import api from './api.js';
import { ENDPOINTS, API_BASE_URL } from './config.js';
import { getCalculatedTime, cleanCycleName, getCourseColor, extractList } from './ui_utils.js';
import { loadRptPlanilla } from './reportes.js';

// State
let currentSessionForObs = null;
let currentRowElementForObs = null;

// --- HORARIOS (Schedule) logic ---

export async function loadSchedule() {
    const type = document.getElementById('schedule-filter-type')?.value;
    const targetId = document.getElementById('schedule-filter-target')?.value;
    const sDate = document.getElementById('schedule-start-date')?.value;
    const eDate = document.getElementById('schedule-end-date')?.value;

    if (!targetId || !sDate || !eDate) return;

    let endpoint = "";
    if (type === 'teacher') {
        endpoint = `${ENDPOINTS.HORARIOS.BASE}/teacher/${targetId}?start_date=${sDate}&end_date=${eDate}`;
    } else {
        endpoint = `${ENDPOINTS.HORARIOS.BASE}/classroom/${targetId}?start_date=${sDate}&end_date=${eDate}`;
    }

    try {
        const response = await api.authFetch(endpoint);
        
        // REGLA OBLIGATORIA: Log del response completo
        console.log("[SCHEDULE] Response recibida:", response);

        // ✅ USO DE HELPER CENTRALIZADO
        const list = extractList(response);
        console.log("[SCHEDULE] LIST:", list);

        if (response.success && list.length > 0) {
            renderScheduleGrid(list, new Date(sDate + 'T00:00:00'));
        }
    } catch (e) { console.error("Error loading schedule:", e); }
}

export async function exportSchedule() {
    const type = document.getElementById('schedule-filter-type')?.value;
    const targetId = document.getElementById('schedule-filter-target')?.value;
    const sDate = document.getElementById('schedule-start-date')?.value;
    const eDate = document.getElementById('schedule-end-date')?.value;

    if (!targetId || !sDate || !eDate) return alert("Por favor selecciona los filtros primero antes de exportar.");

    const btn = document.getElementById('export-excel-btn');
    if (btn) {
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Generando...';
        btn.disabled = true;
    }

    try {
        const endpoint = `${ENDPOINTS.HORARIOS.BASE}/export?type=${type}&target_id=${targetId}&start_date=${sDate}&end_date=${eDate}`;
        // Pedimos rawResponse para poder manejar el blob
        const res = await api.authFetch(endpoint, { rawResponse: true });

        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        const todayStr = new Date().toISOString().slice(0, 10).replace(/-/g, "");
        a.download = `horarios_export_${todayStr}.xlsx`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    } catch (e) {
        alert("Error descargando el archivo Excel: " + e.message);
    } finally {
        if (btn) {
            btn.innerHTML = '<i class="fa-solid fa-download"></i> Exportar a Excel';
            btn.disabled = false;
        }
    }
}

function renderScheduleGrid(sessions, mondayDate) {
    const filterType = document.getElementById('schedule-filter-type');
    if (!filterType) return;
    const type = filterType.value;
    const summaryPanel = document.getElementById('schedule-teacher-summary');

    if (type === 'teacher') {
        if (summaryPanel) summaryPanel.classList.remove('hidden');
        renderTeacherAgenda(sessions, mondayDate);
    } else {
        if (summaryPanel) summaryPanel.classList.add('hidden');
        renderClassroomCalendar(sessions, mondayDate);
    }
}

function renderTeacherAgenda(sessions, startDate) {
    const tbody = document.getElementById('schedule-grid-body');
    const hourHeader = document.getElementById('schedule-header-hour');
    if (hourHeader) hourHeader.classList.add('hidden');

    if (!tbody) return;
    tbody.innerHTML = '';

    if (!sessions || sessions.length === 0) {
        tbody.innerHTML = `<tr class="border-b border-slate-200"><td colspan="5" class="p-12 text-center text-slate-400 font-medium italic">No hay clases programadas para este docente en el rango seleccionado.</td></tr>`;
        return;
    }

    // Dynamic Range
    const daysInRange = [];
    let currDay = new Date(startDate);
    const endDateStr = document.getElementById('schedule-end-date')?.value;
    const endDate = new Date(endDateStr + 'T00:00:00');

    while (currDay <= endDate) {
        daysInRange.push(currDay.toISOString().split('T')[0]);
        currDay.setDate(currDay.getDate() + 1);
        if (daysInRange.length > 31) break;
    }

    const grouped = {};
    daysInRange.forEach(d => grouped[d] = []);
    sessions.forEach(s => {
        if (grouped[s.date]) grouped[s.date].push(s);
    });

    const tr = document.createElement('tr');
    tr.className = "align-top";

    daysInRange.forEach(dateStr => {
        const td = document.createElement('td');
        td.className = "p-3 border-r border-slate-200 min-w-[220px] bg-slate-50/10";

        const daySessions = grouped[dateStr].sort((a, b) => (a.start_time || "").localeCompare(b.start_time || ""));
        let html = "";
        
        daySessions.forEach(s => {
            const timeRange = getCalculatedTime(s.start_time, s.end_time, s.subject || "");
            const cleanedSubject = s.is_break ? (s.subject || "RECESO") : (s.subject || "").replace(/\s*\([^)]*\)$/, '').trim();
            const cardColor = getCourseColor(s.subject, 'teacher');
            
            html += `
                <div class="mb-3 ${cardColor} border rounded-xl p-4 shadow-sm flex flex-col items-center justify-center text-center transition-all hover:scale-105 border-b-4">
                    <div class="font-black text-sm leading-tight uppercase tracking-tight text-slate-900">${cleanedSubject}</div>
                    <div class="text-[11px] font-bold text-slate-600 mt-2 bg-white/50 px-3 py-1 rounded-full">${timeRange}</div>
                    <div class="mt-2 text-[10px] font-black opacity-60 uppercase">${cleanCycleName(s.class_group)}</div>
                </div>
            `;
        });

        if (daySessions.length === 0) {
            html = `<div class="h-64 flex items-center justify-center text-slate-300 italic text-xs uppercase tracking-widest">Sin Actividad</div>`;
        }
        td.innerHTML = html;
        tr.appendChild(td);
    });
    tbody.appendChild(tr);
}

function renderClassroomCalendar(sessions, startDate) {
    const tbody = document.getElementById('schedule-grid-body');
    const hourHeader = document.getElementById('schedule-header-hour');
    if (hourHeader) hourHeader.classList.remove('hidden');
    if (!tbody) return;
    tbody.innerHTML = '';

    const timeBlocks = {};
    sessions.forEach(s => {
        if (!timeBlocks[s.start_time]) {
            timeBlocks[s.start_time] = { start_time: s.start_time, end_time: s.end_time, is_break: s.is_break, days: {} };
        }
        timeBlocks[s.start_time].days[s.date] = s;
    });

    const sortedStartTimes = Object.keys(timeBlocks).sort();
    const daysInRange = [];
    let curr = new Date(startDate);
    const endDate = new Date(document.getElementById('schedule-end-date')?.value + 'T00:00:00');
    while (curr <= endDate) {
        daysInRange.push(curr.toISOString().split('T')[0]);
        curr.setDate(curr.getDate() + 1);
        if (daysInRange.length > 31) break;
    }

    sortedStartTimes.forEach(time => {
        const block = timeBlocks[time];
        const tr = document.createElement('tr');
        tr.className = "border-b border-slate-200";
        let rowHtml = `<td class="px-2 py-2 font-black text-slate-800 text-center border-r border-slate-200 bg-slate-50/50">
                        <div class="text-sm">${block.start_time}</div>
                        <div class="text-[10px] text-slate-400 font-bold">${block.end_time}</div></td>`;

        daysInRange.forEach(dateStr => {
            const session = block.days[dateStr];
            if (session && session.subject) {
                const cardColor = getCourseColor(session.subject, 'classroom');
                rowHtml += `<td class="p-1 border-r border-slate-200 align-middle h-20">
                            <div class="${cardColor} border rounded-lg p-2 shadow-sm h-full flex flex-col items-center justify-center text-center transition-all hover:scale-105">
                                <div class="font-black text-[10px] leading-tight uppercase tracking-tighter">${session.subject}</div>
                                <div class="text-[9px] font-bold opacity-80 mt-1">${session.start_time} - ${session.end_time}</div>
                                <div class="text-[8px] font-black mt-1 uppercase tracking-tighter opacity-60 truncate w-full">${session.teacher || ""}</div>
                            </div></td>`;
            } else {
                rowHtml += `<td class="p-1 border-r border-slate-200 bg-slate-50/20"></td>`;
            }
        });
        tr.innerHTML = rowHtml;
        tbody.appendChild(tr);
    });
}

// --- OBSERVACIONES (Observations) logic ---

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
    try {
        const response = await api.authFetch(`${ENDPOINTS.HORARIOS.BASE}/teachers`);
        
        // REGLA OBLIGATORIA: Log del response completo
        console.log("[OBS_TEACHERS] Response recibida:", response);

        // ✅ USO DE HELPER CENTRALIZADO
        const teachers = extractList(response);
        console.log("[OBS_TEACHERS] LIST:", teachers);

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
        }
    } catch (e) {
        console.error("Error loading teachers for obs:", e);
        select.innerHTML = '<option value="">Error al cargar</option>';
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

    if (tbody) tbody.innerHTML = '<tr><td colspan="5" class="px-4 py-12 text-center text-slate-400"><i class="fa-solid fa-spinner fa-spin text-xl mb-2"></i> Buscando clases...</td></tr>';

    try {
        const url = `${ENDPOINTS.HORARIOS.BASE}/sessions-for-obs?teacher_id=${teacherId}&start_date=${dateStart}&end_date=${dateEnd}`;
        const response = await api.authFetch(url);
        
        // REGLA OBLIGATORIA: Log del response completo
        console.log("[OBS_SESSIONS] Response recibida:", response);

        // ✅ USO DE HELPER CENTRALIZADO
        const sessions = extractList(response);
        console.log("[OBS_SESSIONS] LIST:", sessions);

        if (tbody) {
            tbody.innerHTML = '';
            if (sessions.length === 0) {
                tbody.innerHTML = '<tr><td colspan="5" class="px-4 py-12 text-center text-slate-400 italic">No se encontraron clases en este rango para este docente.</td></tr>';
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
    document.getElementById('obs-form-replacement-last').value = '';
    document.getElementById('obs-form-replacement-first').value = '';
    document.getElementById('obs-form-description').value = '';

    toggleObsBlockMode(true);
    document.getElementById('obs-register-modal')?.classList.remove('hidden');
}

export function toggleObsBlockMode(isFull) {
    const singleCont = document.getElementById('obs-single-mode-container');
    const splitCont = document.getElementById('obs-split-mode-container');
    if (!singleCont || !splitCont) return;

    if (isFull) {
        singleCont.classList.remove('hidden');
        splitCont.classList.add('hidden');
        handleObsTypeChange();
    } else {
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

    container.innerHTML = `<p class="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2">Desglose: ${slots.length} h. pedagógicas</p>`;

    slots.forEach((slot, idx) => {
        const slotDiv = document.createElement('div');
        slotDiv.className = "bg-white border border-slate-200 rounded-xl p-4 shadow-sm space-y-3 mb-2";
        slotDiv.innerHTML = `
            <div class="flex justify-between items-center">
                <span class="text-xs font-black text-indigo-600 bg-indigo-50 px-2 py-1 rounded">Hora ${idx + 1}: ${slot.start} - ${slot.end}</span>
                <select class="obs-slot-type text-[10px] font-bold border-none bg-slate-100 rounded-md px-2 py-1 focus:ring-0" data-idx="${idx}" data-action="toggleSlotReplacement">
                    <option value="NINGUNA">SIN INCIDENCIA</option>
                    <option value="FALTA" selected>FALTA</option>
                    <option value="REEMPLAZO">REEMPLAZO</option>
                </select>
            </div>
            <div id="slot-replacement-container-${idx}" class="hidden mt-2 pt-2 border-t border-slate-100">
                <div class="grid grid-cols-2 gap-3">
                    <input type="text" class="obs-slot-replacement-last w-full px-3 py-2 bg-amber-50 border border-amber-100 rounded-lg text-xs" list="teachers-datalist" placeholder="Apellidos...">
                    <input type="text" class="obs-slot-replacement-first w-full px-3 py-2 bg-amber-50 border border-amber-100 rounded-lg text-xs" placeholder="Nombres...">
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
    if (isFullBlock) {
        const type = document.getElementById('obs-form-type').value;
        const discount = document.getElementById('obs-form-discount').value;
        const replLast = document.getElementById('obs-form-replacement-last').value;
        const replFirst = document.getElementById('obs-form-replacement-first').value;
        const description = document.getElementById('obs-form-description').value;

        const sessionIds = currentSessionForObs.session_ids || [sessionId];
        sessionIds.forEach(sid => {
            payloads.push({
                session_id: sid,
                teacher_id: teacherId,
                type,
                discount_type: discount,
                replacement_last_name: type === 'REEMPLAZO' ? replLast : null,
                replacement_first_name: type === 'REEMPLAZO' ? replFirst : null,
                description,
                start_time: currentSessionForObs.start_time,
                end_time: currentSessionForObs.end_time
            });
        });
    } else {
        const slotDivs = document.getElementById('obs-split-mode-container').querySelectorAll('.bg-white.border');
        slotDivs.forEach((div, idx) => {
            const type = div.querySelector('.obs-slot-type').value;
            if (type === 'NINGUNA') return;

            payloads.push({
                session_id: sessionId,
                teacher_id: teacherId,
                type,
                discount_type: 'SIMPLE',
                replacement_last_name: type === 'REEMPLAZO' ? div.querySelector('.obs-slot-replacement-last').value : null,
                replacement_first_name: type === 'REEMPLAZO' ? div.querySelector('.obs-slot-replacement-first').value : null,
                description: `Desglosado (Hora ${idx + 1})`,
                start_time: div.querySelector('.obs-slot-start').value,
                end_time: div.querySelector('.obs-slot-end').value
            });
        });
    }

    if (payloads.length === 0) return alert("No hay incidencias para registrar.");
    if (payloads.some(p => !p.session_id)) return alert("⚠️ Error: Session ID no válido.");

    try {
        const promises = payloads.map(p => api.authFetch(`${ENDPOINTS.HORARIOS.BASE}/observations`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(p)
        }));

        await Promise.all(promises);
        
        closeObsRegisterModal();
        const row = currentRowElementForObs;
        if (row) {
            const actionCell = row.querySelector('.action-cell');
            const types = [...new Set(payloads.map(p => p.type))];
            const label = types.length > 1 ? 'FALTA/REEMP' : types[0];
            let badgeColor = label === 'REEMPLAZO' ? 'bg-amber-50 text-amber-700 border-amber-200' : (label === 'FALTA/REEMP' ? 'bg-indigo-50 text-indigo-700 border-indigo-200' : 'bg-rose-50 text-rose-700 border-rose-200');
            if (actionCell) actionCell.innerHTML = `<span class="${badgeColor} px-2 py-0.5 rounded-lg text-[9px] font-black uppercase tracking-tighter border shadow-sm"><i class="fa-solid fa-circle-check mr-1 text-[8px]"></i> ${label}</span>`;
        } else {
            searchClassesForObs();
        }
    } catch (e) { alert("Error de conexión"); }
}

export function closeObsRegisterModal() {
    document.getElementById('obs-register-modal')?.classList.add('hidden');
}

export async function deleteObservation(obsId) {
    if (!confirm("¿Eliminar esta incidencia?")) return;
    try {
        const data = await api.authFetch(`${ENDPOINTS.HORARIOS.BASE}/observations/${obsId}`, { method: 'DELETE' });
        if (data.success) {
            if (typeof loadRptPlanilla === 'function') loadRptPlanilla(); 
            loadObsLogs();
        }
    } catch (e) { alert("Error al eliminar"); }
}

export async function loadObsLogs() {
    const tbody = document.getElementById('obs-logs-body');
    if (!tbody) return;
    try {
        const response = await api.authFetch(`${ENDPOINTS.HORARIOS.BASE}/observations/logs?limit=50`);
        
        // REGLA OBLIGATORIA: Log del response completo
        console.log("[OBS_LOGS] Response recibida:", response);

        // ✅ USO DE HELPER CENTRALIZADO
        const logs = extractList(response);
        console.log("[OBS_LOGS] LIST:", logs);
        
        tbody.innerHTML = '';
        if (logs.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="p-10 text-center text-slate-400 italic">No hay logs de incidencias</td></tr>';
            return;
        }
        logs.forEach(log => {
            tbody.insertAdjacentHTML('beforeend', `
                <tr class="hover:bg-slate-50 transition-colors border-b border-slate-100">
                    <td class="px-4 py-3 font-medium">${log.fecha}</td>
                    <td class="px-4 py-3 font-bold">${log.docente}</td>
                    <td class="px-4 py-3"><span class="bg-rose-100 text-rose-700 px-2 py-0.5 rounded text-[10px] font-black uppercase">${log.tipo}</span></td>
                    <td class="px-4 py-3 text-xs text-slate-500">${log.descripcion || '---'}</td>
                    <td class="px-4 py-3 text-xs font-mono">${log.usuario || 'SISTEMA'}</td>
                    <td class="px-4 py-3 text-right">
                        <button data-action="deleteObservation('${log.id}')" class="text-rose-600 hover:text-rose-800"><i class="fa-solid fa-trash"></i></button>
                    </td>
                </tr>
            `);
        });
    } catch (e) { console.error("Error logs:", e); }
}

