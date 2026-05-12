import api from './api.js';
import { ENDPOINTS } from './config.js';
import { getCalculatedTime, cleanCycleName, getCourseColor, extractList } from './ui_utils.js';

function formatDateLocal(date) {
    const yyyy = date.getFullYear();
    const mm = String(date.getMonth() + 1).padStart(2, '0');
    const dd = String(date.getDate()).padStart(2, '0');
    return `${yyyy}-${mm}-${dd}`;
}

function renderDynamicHeaders(daysInRange, showHours = false) {
    const theadTr = document.querySelector('#schedule table thead tr');
    if (!theadTr) return;

    let html = "";
    if (showHours) {
        html += `<th id="schedule-header-hour" class="px-4 py-3 w-28 text-center border-r border-slate-200 tracking-wider bg-slate-100">Horario</th>`;
    }

    const daysNames = ['DOM', 'LUN', 'MAR', 'MIÉ', 'JUE', 'VIE', 'SÁB'];
    daysInRange.forEach((dateStr, idx) => {
        const [y, m, d] = dateStr.split('-').map(Number);
        const localDt = new Date(y, m - 1, d);
        const dayLabel = daysNames[localDt.getDay()];
        const borderClass = (idx === daysInRange.length - 1) ? "" : "border-r border-slate-200";
        
        html += `<th class="px-4 py-3 ${borderClass} text-center tracking-wider bg-slate-100 min-w-[200px]">${dayLabel} ${d}</th>`;
    });
    
    theadTr.innerHTML = html;
}

/**
 * @description Populates the secondary select input (#schedule-filter-target) based on chosen Type (Teacher/Classroom).
 */
export async function fillTargetSelect() {
    const type = document.getElementById('schedule-filter-type')?.value;
    const select = document.getElementById('schedule-filter-target');
    if (!select) return;

    select.innerHTML = '<option value="">Cargando...</option>';

    try {
        let endpoint = "";
        if (type === 'teacher') {
            endpoint = ENDPOINTS.HORARIOS.TEACHERS;
        } else {
            endpoint = ENDPOINTS.HORARIOS.CLASSES;
        }

        console.log(`[HORARIOS INIT] Loading filter for type: ${type}`);
        const response = await api.authFetch(endpoint);
        const items = extractList(response);
        console.log(`[HORARIOS LOADED] Total items retrieved: ${items.length}`);

        select.innerHTML = `<option value="">Seleccione un ${type === 'teacher' ? 'Docente' : 'Aula'}...</option>`;

        if (Array.isArray(items) && items.length > 0) {
            items.forEach(item => {
                const opt = document.createElement('option');
                opt.value = item.id;
                if (type === 'teacher') {
                    opt.textContent = `${item.last_name || ''}, ${item.first_name || ''}`.trim();
                } else {
                    opt.textContent = item.name || 'Sin Nombre';
                }
                select.appendChild(opt);
            });
        } else {
            select.innerHTML = `<option value="">No se encontraron datos para ${type}</option>`;
        }
    } catch (e) {
        console.error("[HORARIOS ERROR] Failed loading target items:", e);
        select.innerHTML = '<option value="">Error al cargar</option>';
    }
}

/**
 * @description Handles the entry to the module, setting default dates and trigger select population.
 */
export async function initSchedule() {
    console.log("[HORARIOS INIT] Starting module initialization");
    
    const startEl = document.getElementById('schedule-start-date');
    const endEl = document.getElementById('schedule-end-date');

    if (startEl && !startEl.value) {
        // Pre-fill current week by default
        const curr = new Date();
        const day = curr.getDay(); 
        // Shift back to Monday
        const diff = curr.getDate() - day + (day === 0 ? -6 : 1); 
        const monday = new Date(curr.setDate(diff));
        const sunday = new Date(monday);
        sunday.setDate(sunday.getDate() + 6);

        startEl.value = monday.toISOString().split('T')[0];
        if (endEl) endEl.value = sunday.toISOString().split('T')[0];
    }

    await fillTargetSelect();
}

export async function loadSchedule() {
    const type = document.getElementById('schedule-filter-type')?.value;
    const targetId = document.getElementById('schedule-filter-target')?.value;
    const sDate = document.getElementById('schedule-start-date')?.value;
    const eDate = document.getElementById('schedule-end-date')?.value;

    const tbody = document.getElementById('schedule-grid-body');

    if (!targetId || !sDate || !eDate) {
        if (tbody) tbody.innerHTML = '<tr><td colspan="6" class="p-12 text-center text-slate-400 font-medium italic">Selecciona una opción para visualizar el horario.</td></tr>';
        return;
    }

    let endpoint = "";
    if (type === 'teacher') {
        endpoint = `${ENDPOINTS.HORARIOS.BASE}/teacher/${targetId}?start_date=${sDate}&end_date=${eDate}`;
        
        // Sync name into summary panel
        const select = document.getElementById('schedule-filter-target');
        const name = select.options[select.selectedIndex].text;
        const nameEl = document.getElementById('sch-summary-name');
        if (nameEl) nameEl.textContent = name;

        // Refresh summary panels
        const rangeEl = document.getElementById('sch-summary-range');
        if (rangeEl) rangeEl.textContent = `${sDate} al ${eDate}`;
    } else {
        endpoint = `${ENDPOINTS.HORARIOS.BASE}/classroom/${targetId}?start_date=${sDate}&end_date=${eDate}`;
    }

    try {
        console.log("[HORARIOS REQUEST] Fetching from:", endpoint);
        const response = await api.authFetch(endpoint);
        
        // REGLA OBLIGATORIA: Log del response completo
        console.log("[HORARIOS API] Full response:", response);

        const list = extractList(response);
        console.log("[HORARIOS DATA] Session count:", list.length);

        renderScheduleGrid(list, new Date(sDate + 'T00:00:00'));
    } catch (e) { 
        console.error("[HORARIOS LOAD ERROR]:", e); 
    }
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
        console.log("[HORARIOS EXPORT] Fetching export...");
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

    if (!tbody) return;
    tbody.innerHTML = '';

    const daysInRange = [];
    let currDay = new Date(startDate);
    const endDateStr = document.getElementById('schedule-end-date')?.value;
    const endDate = new Date(endDateStr + 'T00:00:00');

    while (currDay <= endDate) {
        daysInRange.push(formatDateLocal(currDay));
        currDay.setDate(currDay.getDate() + 1);
        if (daysInRange.length > 31) break;
    }

    // Apply Dynamic Headers to fix layout matching
    renderDynamicHeaders(daysInRange, false);

    if (!sessions || sessions.length === 0) {
        tbody.innerHTML = `<tr class="border-b border-slate-200"><td colspan="${daysInRange.length}" class="p-12 text-center text-slate-400 font-medium italic">No hay clases programadas para este docente en el rango seleccionado.</td></tr>`;
        
        // Update statistics to zero
        const hoursEl = document.getElementById('sch-summary-hours');
        if (hoursEl) hoursEl.textContent = "0.00";
        return;
    }

    // Compute stats
    let totalHours = 0;
    sessions.forEach(s => {
        if (!s.is_break) {
            totalHours += (s.horas_dictadas || 1);
        }
    });
    const hoursEl = document.getElementById('sch-summary-hours');
    if (hoursEl) hoursEl.textContent = totalHours.toFixed(2);


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
            const isReplTag = s.is_replacement ? `<div class="absolute top-1 right-1 bg-amber-500 text-white text-[7px] font-black px-1.5 rounded-full border border-white shadow-sm">REEMPLAZO</div>` : '';
            
            html += `
                <div class="relative mb-3 ${cardColor} border rounded-xl p-4 shadow-sm flex flex-col items-center justify-center text-center transition-all hover:scale-105 border-b-4">
                    ${isReplTag}
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
        daysInRange.push(formatDateLocal(curr));
        curr.setDate(curr.getDate() + 1);
        if (daysInRange.length > 31) break;
    }

    // Apply Dynamic Headers to fix layout matching
    renderDynamicHeaders(daysInRange, true);

    if (sortedStartTimes.length === 0) {
        tbody.innerHTML = `<tr class="border-b border-slate-200"><td colspan="${daysInRange.length + 1}" class="p-12 text-center text-slate-400 font-medium italic">No hay actividades en este aula.</td></tr>`;
        return;
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
