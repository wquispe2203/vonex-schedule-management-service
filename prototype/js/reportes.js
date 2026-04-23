// Reportes Module - ES6
import api from './api.js';
import { ENDPOINTS, API_BASE_URL } from './config.js';

let rptCurrentPage = 1;

export async function loadRptPlanilla(page = 1) {
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
        let url = `${ENDPOINTS.REPORTES.BASE}/?fecha_inicio=${inicio}&fecha_fin=${fin}&page=${page}&limit=50`;
        if (docente !== "Todos") url += `&docente=${encodeURIComponent(docente)}`;
        if (sede !== "Todas") url += `&sede=${encodeURIComponent(sede)}`;
        if (aula !== "Todos") url += `&aula=${encodeURIComponent(aula)}`;

        const data = await api.authFetch(url);

        if (data.success) {
            if (tbody) tbody.innerHTML = '';
            
            if (data.data.length === 0) {
                if (tbody) tbody.innerHTML = '<tr><td colspan="9" class="px-4 py-16 text-center text-slate-400 font-medium italic">" Todavía no se cargan estos datos a la bd "</td></tr>';
                document.getElementById('rpt-total-records').innerText = "0";
                document.getElementById('rpt-page-indicator').innerText = "Página 1 de 1";
                document.getElementById('rpt-prev-btn').disabled = true;
                document.getElementById('rpt-next-btn').disabled = true;
                return;
            }

            // Summary Panel Update
            const summaryPanel = document.getElementById('rpt-summary-panel');
            if (summaryPanel) {
                summaryPanel.classList.remove('hidden');
                document.getElementById('rpt-sum-hours').innerText = data.total_hours_sum.toFixed(2);
                document.getElementById('rpt-count-recesos').innerText = data.total_receso_count;
            }

            // Metadata
            document.getElementById('rpt-total-records').innerText = data.total_records;
            document.getElementById('rpt-page-indicator').innerText = `Página ${data.current_page} de ${data.total_pages}`;
            document.getElementById('rpt-prev-btn').disabled = data.current_page <= 1;
            document.getElementById('rpt-next-btn').disabled = data.current_page >= data.total_pages;

            if (tbody) {
                data.data.forEach(r => {
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
        if (tbody) tbody.innerHTML = '<tr><td colspan="9" class="px-4 py-12 text-center text-rose-500 font-bold">Error conectando con el servidor</td></tr>';
    }
}

export function changeRptPage(delta) {
    loadRptPlanilla(rptCurrentPage + delta);
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
