// Reportes Module - ES6
import api from './api.js';
import { ENDPOINTS, API_BASE_URL } from './config.js';
import { extractList, extractPagination } from './ui_utils.js';
import { populateRptCombobox, navRptTeacher as _navRptTeacher, setupComboboxKeyboard, filterDocenteCombobox as _filterDocenteCombobox, registerRptTeacherChangeCallback } from './searchable_combobox.js';

// Re-export para el sistema de Handlers (data-action)
export function filterDocenteCombobox(context) { _filterDocenteCombobox(context); }

let rptCurrentPage = 1;
let isLoadingRpt = false;
let rptInitPromise = null;

export async function initRPT() {
    if (rptInitPromise) {
        console.log('[PROMISE LOCK REUSED] initRPT');
        return rptInitPromise;
    }

    console.log('[PROMISE LOCK ACQUIRED] initRPT');
    let success = false;

    rptInitPromise = (async () => {
        console.log('[RPT INIT]');
        try {
            await loadRptFilters();
            setupRptEvents();
            setupComboboxKeyboard();
            // Registrar callback para auto-reload al seleccionar docente
            registerRptTeacherChangeCallback(() => loadRptPlanilla(1));

            // Set default dates if empty to prevent unnecessary alerts on load
            const inicio = document.getElementById('rpt-fecha-inicio');
            const fin = document.getElementById('rpt-fecha-fin');
            if (inicio && fin && (!inicio.value || !fin.value)) {
                const today = new Date();
                const firstDay = new Date(today.getFullYear(), today.getMonth(), 1);
                inicio.value = firstDay.toISOString().split('T')[0];
                fin.value = today.toISOString().split('T')[0];
            }

            await loadRptPlanilla(1);
            
            success = true;
            console.log('[PROMISE LOCK RELEASED] initRPT successfully initialized');
            console.log('[RPT FILTERS RENDERED]');
            console.log('[RPT LAYOUT WIDTH]');
            console.log('[RPT FILTER WIDTHS]');
            console.log('[RPT FILTER OVERFLOW]');
            console.log('[RPT RESPONSIVE OK]');
        } catch (err) {
            console.error("[PROMISE LOCK RESET] initRPT Critical Failure:", err);
            throw err;
        } finally {
            if (!success) {
                console.warn("[PROMISE LOCK RESET] Releasing failed initRPT promise.");
                rptInitPromise = null; 
            }
        }
    })();

    return rptInitPromise;
}

export function setupRptEvents() {
    console.log('[RPT EVENTS]');
    console.log("[RPT] Inicializando manejadores de eventos con protección dataset.bound...");
    const ids = ['rpt-filter-docente', 'rpt-filter-sede', 'rpt-filter-aula', 'rpt-fecha-inicio', 'rpt-fecha-fin'];
    ids.forEach(id => {
        const el = document.getElementById(id);
        if (!el) return;

        // Protección defensiva usando data-bound para no resetear valores de filtros
        if (!el.dataset.bound) {
            el.dataset.bound = "true";
            el.addEventListener('change', () => {
                console.log(`[RPT EVENT] Cambio detectado en ${id}`);
                if (id === 'rpt-filter-sede') {
                    handleSedeChange().then(() => {
                        loadRptPlanilla(1);
                    });
                } else {
                    loadRptPlanilla(1);
                }
            });
        }
    });
}

export async function loadRptPlanilla(page = 1) {
    if (isLoadingRpt) {
        console.warn("[RPT] Ignorando llamada duplicada, ya cargando...");
        return;
    }
    
    console.log('[RPT LOAD]');
    
    if (typeof page !== 'number') page = 1;
    rptCurrentPage = page;
    
    const tbody = document.getElementById('rpt-planilla-body');
    const inicio = document.getElementById('rpt-fecha-inicio')?.value;
    const fin = document.getElementById('rpt-fecha-fin')?.value;
    const docente = document.getElementById('rpt-filter-docente')?.value || 'Todos';
    const sede = document.getElementById('rpt-filter-sede')?.value || 'Todas';
    const aula = document.getElementById('rpt-filter-aula')?.value || 'Todos';

    if (!inicio || !fin) {
        alert("Seleccione rango de fechas.");
        return;
    }

    if (tbody) {
        tbody.innerHTML = '<tr><td colspan="9" class="px-4 py-12 text-center text-slate-400"><i class="fa-solid fa-spinner fa-spin text-2xl mb-3 block"></i>Filtrando...</td></tr>';
    }

    try {
        isLoadingRpt = true;
        let url = `${ENDPOINTS.REPORTES.BASE}/?fecha_inicio=${inicio}&fecha_fin=${fin}&page=${page}&limit=50`;
        if (docente !== "Todos") url += `&docente=${encodeURIComponent(docente)}`;
        if (sede !== "Todas") url += `&sede=${encodeURIComponent(sede)}`;
        if (aula !== "Todos") url += `&aula=${encodeURIComponent(aula)}`;

        const response = await api.authFetch(url);

        // REGLA OBLIGATORIA: Log del response completo
        console.log("[REPORTES] Response recibida:", response);

        if (response.success) {
            if (tbody) tbody.innerHTML = '';
            
            // ✅ USO DE HELPERS CENTRALIZADOS
            if (typeof extractList !== "function") {
                throw new Error("Dependency extractList missing");
            }
            const list = extractList(response);
            const pagination = extractPagination(response);

            // LOGGING CONTROLADO
            console.log("[REPORTES] LIST:", list);

            if (!Array.isArray(list) || list.length === 0) {
                if (tbody) tbody.innerHTML = '<tr><td colspan="9" class="px-4 py-16 text-center text-slate-400 font-medium italic">" No se encontraron registros para los filtros seleccionados "</td></tr>';
                document.getElementById('rpt-total-records').innerText = "0";
                document.getElementById('rpt-page-indicator').innerText = "Página 1 de 1";
                document.getElementById('rpt-prev-btn').disabled = true;
                document.getElementById('rpt-next-btn').disabled = true;
                return;
            }

            // Summary Panel Update (Atributos ahora directos en pagination según ReportPaginatedData)
            const summaryPanel = document.getElementById('rpt-summary-panel');
            if (summaryPanel && pagination) {
                summaryPanel.classList.remove('hidden');
                document.getElementById('rpt-sum-hours').innerText = (pagination.total_hours_sum || 0).toFixed(2);
                document.getElementById('rpt-count-recesos').innerText = pagination.total_receso_count || 0;
            }

            // Metadata / Pagination
            const total = pagination?.total || 0;
            const pageNum = pagination?.page || 1;
            const totalPages = pagination?.total_pages || 1;

            const totalRecordsEl = document.getElementById('rpt-total-records');
            const pageIndicatorEl = document.getElementById('rpt-page-indicator');
            const prevBtn = document.getElementById('rpt-prev-btn');
            const nextBtn = document.getElementById('rpt-next-btn');

            if (totalRecordsEl) totalRecordsEl.innerText = total;
            if (pageIndicatorEl) pageIndicatorEl.innerText = `Página ${pageNum} de ${totalPages}`;
            if (prevBtn) prevBtn.disabled = pageNum <= 1;
            if (nextBtn) nextBtn.disabled = pageNum >= totalPages;

            if (tbody) {
                list.forEach(r => {
                    const tr = document.createElement('tr');
                    const obs = r.observation;
                    const isRepl = r.is_replacement;

                    let rowClass = "hover:bg-slate-50 transition-colors border-b border-slate-50";
                    let extraInfo = "";
                    let hoursDisplay = r.horas_dictadas.toFixed(2);
                    let recesoDisplay = r.receso.toFixed(2);

                    // Visual markers for Titular's incidents
                    if (obs && !isRepl) {
                        const types = typeof obs.type === 'string' ? obs.type.split(', ') : [];
                        const obsIds = obs.ids || [];
                        let labelsHtml = '';

                        types.forEach((t, idx) => {
                            const currentObsId = obsIds[idx];
                            // Usar data-action para el botón de eliminar
                            const deleteBtn = currentObsId ? `<button data-action="deleteObservation('${currentObsId}')" class="ml-1 opacity-0 group-hover:opacity-100 hover:text-white transition-all" title="Eliminar ${t}"><i class="fa-solid fa-xmark"></i></button>` : '';

                            if (['FALTA', 'VACACIONES', 'DESCANSO_MEDICO'].includes(t)) {
                                labelsHtml += `<span class="bg-rose-100 text-rose-700 px-1.5 py-0.5 rounded-md text-[9px] font-black uppercase inline-flex items-center gap-1 my-0.5 mr-1 group/tag"><i class="fa-solid fa-circle-exclamation"></i> ${t}${deleteBtn}</span>`;
                            } else if (t === 'REEMPLAZO') {
                                labelsHtml += `<span class="bg-amber-100 text-amber-700 px-1.5 py-0.5 rounded-md text-[9px] font-black uppercase inline-flex items-center gap-1 my-0.5 mr-1 group/tag" title="Reemplazado por: ${obs.replacement_teacher_name || '---'}"><i class="fa-solid fa-user-group"></i> REEMPLAZO${deleteBtn}</span>`;
                            }
                        });

                        if (obs.has_discount_impact) {
                            rowClass = "bg-rose-50/50 text-rose-900 border-b border-rose-100";
                        }
                        extraInfo = `<div class="flex flex-wrap mt-1">${labelsHtml}</div>`;
                    }

                    // Special highlighting for the Replacement Teacher's record
                    if (isRepl) {
                        rowClass = "bg-amber-50 text-amber-900 border-b border-amber-100 font-medium";
                        extraInfo = `<div class="mt-1"><span class="bg-amber-600 text-white px-1.5 py-0.5 rounded-md text-[9px] font-black uppercase inline-flex items-center gap-1"><i class="fa-solid fa-award"></i> REEMPLAZO</span> <span class="text-[10px] opacity-70 italic ml-1">(Titular: ${r.titular_original})</span></div>`;
                    }

                    tr.className = rowClass + " group"; // group class for hover effect on buttons
                    tr.innerHTML = `
                        <td class="px-4 py-3 font-medium">${r.fecha_clase}</td>
                        <td class="px-4 py-3">${r.sede}</td>
                        <td class="px-4 py-3 font-bold">${r.ciclo}</td>
                        <td class="px-4 py-3 font-medium">
                            ${r.docente}
                            ${extraInfo}
                        </td>
                        <td class="px-4 py-3 text-xs">${r.curso}</td>
                        <td class="px-4 py-3 font-mono text-xs">${r.hora_inicio.substring(0, 5)}</td>
                        <td class="px-4 py-3 font-mono text-xs">${r.hora_fin.substring(0, 5)}</td>
                        <td class="px-4 py-3 text-center font-black">${hoursDisplay}</td>
                        <td class="px-4 py-3 text-center font-bold">${recesoDisplay}</td>
                    `;
                    tbody.appendChild(tr);
                });
            }
        }
    } catch (e) {
        console.error("Error loading RPT data:", e);
        if (e.message === "Unauthorized") {
            window.location.href = "/login";
        } else {
            if (tbody) tbody.innerHTML = '<tr><td colspan="9" class="px-4 py-12 text-center text-rose-500 font-bold">Error conectando con el servidor (500)</td></tr>';
        }
    } finally {
        isLoadingRpt = false;
    }
}

export function changeRptPage(delta) {
    loadRptPlanilla(rptCurrentPage + delta);
}

/**
 * Navegación secuencial de docentes — delegada al módulo combobox.
 */
export function navRptTeacher(delta) {
    _navRptTeacher(delta);
}

export async function exportToExcel() {
    const inicio = document.getElementById('rpt-fecha-inicio')?.value;
    const fin = document.getElementById('rpt-fecha-fin')?.value;
    const docente = document.getElementById('rpt-filter-docente')?.value || 'Todos';
    const sede = document.getElementById('rpt-filter-sede')?.value || 'Todas';
    const aula = document.getElementById('rpt-filter-aula')?.value || 'Todos';

    if (!inicio || !fin) {
        alert("Seleccione rango de fechas para exportar.");
        return;
    }

    let url = `${API_BASE_URL}/api/rpt-planilla/export?fecha_inicio=${inicio}&fecha_fin=${fin}`;
    if (docente !== "Todos") url += `&docente=${encodeURIComponent(docente)}`;
    if (sede !== "Todas") url += `&sede=${encodeURIComponent(sede)}`;
    if (aula !== "Todos") url += `&aula=${encodeURIComponent(aula)}`;

    window.open(url, '_blank');
}

// --- Dynamic Filter Loading ---

export async function handleSedeChange() {
    const sede = document.getElementById('rpt-filter-sede')?.value;
    const selectAula = document.getElementById('rpt-filter-aula');
    if (!selectAula) return;

    if (!sede || sede === "Todas") {
        selectAula.innerHTML = '<option value="Todos">Todos</option>';
        selectAula.disabled = true;
        return;
    }

    try {
        const response = await api.authFetch(`${ENDPOINTS.REPORTES.BASE}/aulas?sede=${encodeURIComponent(sede)}`);
        
        // REGLA OBLIGATORIA: Log del response completo
        console.log("[RPT_AULAS] Response recibida:", response);

        // ✅ USO DE HELPER CENTRALIZADO
        const aulas = extractList(response);
        console.log("[RPT_AULAS] LIST:", aulas);
        
        selectAula.innerHTML = '<option value="Todos">Todos los Ciclos</option>';
        aulas.forEach(a => {
            const opt = document.createElement('option');
            opt.value = a;
            opt.textContent = a;
            selectAula.appendChild(opt);
        });
        selectAula.disabled = false;
    } catch (err) {
        console.error("[RPT] Error cargando aulas:", err);
    }
}

export async function loadRptFilters() {
    console.log("[RPT] Cargando filtros dinámicos...");
    const selectDocente = document.getElementById('rpt-filter-docente');
    const selectSede = document.getElementById('rpt-filter-sede');

    try {
        console.log("[DROPDOWN LOAD START] Loading reports teachers and sedes dropdowns...");
        // Cargar Docentes
        const resDocentes = await api.authFetch(`${ENDPOINTS.REPORTES.BASE}/docentes`);
        
        // REGLA OBLIGATORIA: Log del response completo
        console.log("[RPT_FILTER_DOC] Response recibida:", resDocentes);

        const listDocentes = extractList(resDocentes);
        console.log("[RPT_FILTER_DOC] LIST:", listDocentes);

        if (resDocentes.success && listDocentes.length > 0) {
            // Poblar combobox searchable (también sincroniza hidden select)
            populateRptCombobox(listDocentes);
            console.log(`[DROPDOWN POPULATED] Loaded ${listDocentes.length} options for reports teachers.`);
        } else {
            console.warn("[DROPDOWN EMPTY] No reports teachers found.");
            const inputEl = document.getElementById('rpt-docente-search');
            if (inputEl) inputEl.placeholder = 'No hay cargas XML activas';
        }

        // Cargar Sedes
        const resSedes = await api.authFetch(`${ENDPOINTS.REPORTES.BASE}/sedes`);
        
        // REGLA OBLIGATORIA: Log del response completo
        console.log("[RPT_FILTER_SEDES] Response recibida:", resSedes);

        const listSedes = extractList(resSedes);
        console.log("[RPT_FILTER_SEDES] LIST:", listSedes);

        if (resSedes.success && listSedes.length > 0) {
            if (selectSede) {
                selectSede.innerHTML = '<option value="Todas">Todas las Sedes</option>';
                listSedes.forEach(s => {
                    const opt = document.createElement('option');
                    opt.value = s;
                    opt.textContent = s;
                    selectSede.appendChild(opt);
                });
            }
            console.log(`[DROPDOWN POPULATED] Loaded ${listSedes.length} options for reports sedes.`);
        } else {
            console.warn("[DROPDOWN EMPTY] No reports sedes found.");
            if (selectSede) {
                selectSede.innerHTML = '<option value="Todas">Todas las Sedes</option>';
            }
        }
    } catch (err) {
        console.error("[DROPDOWN API ERROR] Error loading select filters:", err);
    }
}
