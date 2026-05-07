
import api from './api.js';
import { ENDPOINTS } from './config.js';
import { extractList } from './ui_utils.js';

let currentXmlFile = null;
let pendingUploadData = null;

export function initXmlUploadView() {
    console.log('[XML UPLOAD] Inicializando vista...');
    resetXmlUploadState();
    setupXmlUploadHandlers();
    loadUploadHistory();
}

export function closeReportModal() {
    const modal = document.getElementById('report-modal');
    if (modal) modal.classList.add('hidden');
}

function resetXmlUploadState() {
    currentXmlFile = null;
    const fileNameDisplay = document.getElementById('file-name-display');
    if (fileNameDisplay) {
        fileNameDisplay.textContent = "Arrastra tu XML aquí";
        fileNameDisplay.classList.remove('text-indigo-600');
    }
    const fileInput = document.getElementById('file-upload');
    if (fileInput) fileInput.value = '';
    
    const progress = document.getElementById('upload-progress');
    if (progress) progress.classList.add('hidden');
}

export function setupXmlUploadHandlers() {
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-upload');
    const fileNameDisplay = document.getElementById('file-name-display');

    if (!dropZone || !fileInput) return;

    // Usar variables persistentes para evitar pérdida de estado
    const handleFile = (file) => {
        if (file && file.name.endsWith('.xml')) {
            currentXmlFile = file;
            if (fileNameDisplay) {
                fileNameDisplay.textContent = file.name;
                fileNameDisplay.classList.add('text-indigo-600');
            }
            console.log("[XML_UPLOAD] Archivo seleccionado:", file.name);
        } else {
            alert("Por favor seleccione un archivo XML válido (.xml)");
        }
    };

    // Evitar reapertura del selector: solo clickear si NO es el input el que disparó el evento
    dropZone.onclick = (e) => {
        if (e.target !== fileInput) {
            fileInput.click();
        }
    };

    fileInput.onchange = (e) => {
        if (e.target.files.length > 0) {
            handleFile(e.target.files[0]);
        }
    };

    dropZone.ondragover = (e) => {
        e.preventDefault();
        dropZone.classList.add('border-indigo-500', 'bg-indigo-50');
    };

    dropZone.ondragleave = () => {
        dropZone.classList.remove('border-indigo-500', 'bg-indigo-50');
    };

    dropZone.ondrop = (e) => {
        e.preventDefault();
        dropZone.classList.remove('border-indigo-500', 'bg-indigo-50');
        if (e.dataTransfer.files.length > 0) {
            handleFile(e.dataTransfer.files[0]);
        }
    };
}

export async function simulateUpload() {
    const fileInput = document.getElementById('file-upload');
    const startDate = document.getElementById('start-date').value;
    const endDate = document.getElementById('end-date').value;
    const progress = document.getElementById('upload-progress');
    const taskList = document.getElementById('upload-task-list');

    // Validar archivo: priorizar el guardado en memoria (drop) o el del input
    const fileToUpload = currentXmlFile || (fileInput && fileInput.files[0]);

    if (!fileToUpload || !startDate || !endDate) {
        alert("Por favor seleccione un archivo y el rango de fechas.");
        return;
    }

    if (progress) progress.classList.remove('hidden');
    if (taskList) {
        taskList.innerHTML = `
            <li class="flex items-center gap-3 text-slate-600 mb-3" id="task-norm">
                <i class="fa-solid fa-circle-notch fa-spin text-indigo-500"></i> Analizando estructura XML...
            </li>
            <li class="flex items-center gap-3 text-slate-400 mb-3" id="task-teachers">
                <i class="fa-solid fa-circle text-[8px]"></i> Vinculando Docentes...
            </li>
            <li class="flex items-center gap-3 text-slate-400" id="task-sessions">
                <i class="fa-solid fa-circle text-[8px]"></i> Generando Sesiones...
            </li>
        `;
    }

    const formData = new FormData();
    formData.append('file', fileToUpload);
    formData.append('start_date', startDate);
    formData.append('end_date', endDate);
    formData.append('force_overwrite', 'false');

    try {
        console.log("[XML_UPLOAD] Iniciando request POST...");
        const response = await api.authFetch(ENDPOINTS.HORARIOS.UPLOAD, {
            method: 'POST',
            body: formData
        });

        // REGLA OBLIGATORIA: Log del response completo
        console.log("[XML_UPLOAD] Response recibida:", response);

        if (response && response.overlap_detected) {
            console.log("[XML OVERLAP DETECTED] Interceptado en frontend");
            if (progress) progress.classList.add('hidden');
            pendingUploadData = { file: fileToUpload, start: startDate, end: endDate };
            
            const modal = document.getElementById('overwrite-modal');
            const modalMsg = document.getElementById('overwrite-modal-msg');
            if (modal) {
                if (modalMsg) {
                    modalMsg.textContent = `Ya existen datos cargados para este rango de fechas (${startDate} a ${endDate}). ¿Desea sobrescribir la información anterior?`;
                }
                modal.classList.remove('hidden');
            }
            return;
        }

        // ✅ USO DE HELPER CENTRALIZADO
        if (typeof extractList !== "function") {
            throw new Error("Dependency extractList missing");
        }
        const list = extractList(response);
        console.log("[XML_UPLOAD] LIST:", list);

        // En el caso del upload, si no es lista, puede ser el objeto de resultado directamente
        const result = list.length > 0 ? list : (response.data || {});
        const sessionsCount = result.processed_records || result.records || 0;

        // Actualizar UI de progreso a completado
        const taskNorm = document.getElementById('task-norm');
        const taskTeachers = document.getElementById('task-teachers');
        const taskSessions = document.getElementById('task-sessions');
        
        if (taskNorm) taskNorm.innerHTML = '<i class="fa-solid fa-check text-green-500"></i> Estructura validada';
        if (taskTeachers) taskTeachers.innerHTML = '<i class="fa-solid fa-check text-green-500"></i> Docentes vinculados';
        if (taskSessions) taskSessions.innerHTML = `<i class="fa-solid fa-check text-green-500"></i> ${sessionsCount} sesiones generadas`;

        setTimeout(() => {
            if (sessionsCount > 0) {
                alert("¡Éxito! Horario procesado con " + sessionsCount + " sesiones.");
            } else {
                alert("Atención: El proceso terminó pero se generaron 0 sesiones. Verifique el rango de fechas o el contenido del XML.");
            }
            resetXmlUploadState();
            loadUploadHistory();
        }, 1000);

    } catch (error) {
        console.error("[XML_UPLOAD] Error:", error);
        alert("Error al procesar el archivo: " + (error.message || "Error desconocido"));
        if (progress) progress.classList.add('hidden');
    }
}

export async function confirmOverwrite() {
    closeOverwriteModal();
    if (!pendingUploadData) return;

    const { file, start, end } = pendingUploadData;
    pendingUploadData = null;

    const progress = document.getElementById('upload-progress');
    if (progress) progress.classList.remove('hidden');

    const formData = new FormData();
    formData.append('file', file);
    formData.append('start_date', start);
    formData.append('end_date', end);
    formData.append('force_overwrite', 'true');

    try {
        console.log("[XML_UPLOAD] Iniciando re-envío con FORCE_OVERWRITE...");
        const response = await api.authFetch(ENDPOINTS.HORARIOS.UPLOAD, {
            method: 'POST',
            body: formData
        });

        console.log("[XML_UPLOAD] [XML OVERWRITE CONFIRMED] [XML PREVIOUS UPLOADS ARCHIVED] Response recibida:", response);

        if (typeof extractList !== "function") {
            throw new Error("Dependency extractList missing");
        }
        const list = extractList(response);
        const result = list.length > 0 ? list : (response.data || {});
        const sessionsCount = result.processed_records || result.records || 0;

        const taskNorm = document.getElementById('task-norm');
        const taskTeachers = document.getElementById('task-teachers');
        const taskSessions = document.getElementById('task-sessions');
        
        if (taskNorm) taskNorm.innerHTML = '<i class="fa-solid fa-check text-green-500"></i> Estructura validada';
        if (taskTeachers) taskTeachers.innerHTML = '<i class="fa-solid fa-check text-green-500"></i> Docentes vinculados';
        if (taskSessions) taskSessions.innerHTML = `<i class="fa-solid fa-check text-green-500"></i> ${sessionsCount} sesiones generadas`;

        setTimeout(() => {
            if (sessionsCount > 0) {
                alert("¡Éxito! Horario procesado con " + sessionsCount + " sesiones.");
            } else {
                alert("Atención: El proceso terminó pero se generaron 0 sesiones.");
            }
            resetXmlUploadState();
            loadUploadHistory();
        }, 1000);

    } catch (error) {
        console.error("[XML_UPLOAD] Error en FORCE overwrite:", error);
        alert("Error al procesar el archivo: " + (error.message || "Error desconocido"));
        if (progress) progress.classList.add('hidden');
    }
}

export function closeOverwriteModal() {
    const modal = document.getElementById('overwrite-modal');
    if (modal) modal.classList.add('hidden');
    pendingUploadData = null;
    const progress = document.getElementById('upload-progress');
    if (progress) progress.classList.add('hidden');
}

export async function loadUploadHistory() {
    const tbody = document.getElementById('upload-history-body');
    if (!tbody) return;

    try {
        console.log("[HISTORY] Cargando historial...");
        // Contrato Estricto: El backend devuelve StandardResponse[PaginatedResponseData[XmlUploadHistoryItem]]
        const response = await api.authFetch(`${ENDPOINTS.HORARIOS.HISTORY}?page=1&limit=5`);
        
        // REGLA OBLIGATORIA: Log del response completo
        console.log("[HISTORY] Response recibida:", response);

        // ✅ USO DE HELPER CENTRALIZADO
        if (typeof extractList !== "function") {
            throw new Error("Dependency extractList missing");
        }
        const history = extractList(response);
        console.log("[HISTORY] LIST:", history);

        // REGLA OBLIGATORIA: Limpiar tbody antes de renderizar
        tbody.innerHTML = "";

        if (!Array.isArray(history) || history.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="4" class="p-10 text-center text-slate-400">
                        <div class="flex flex-col items-center">
                            <i class="fa-solid fa-history text-4xl mb-4 opacity-20 block"></i>
                            <p class="text-sm">No hay historial de subidas reciente</p>
                        </div>
                    </td>
                </tr>
            `;
            return;
        }

        // REGLA OBLIGATORIA: Renderizar TRs (sin usar +=)
        const rowsHtml = history.map(h => {
            const statusClass = h.status === 'COMPLETED' ? 'bg-emerald-100 text-emerald-700' : (h.status === 'FAILED' ? 'bg-rose-100 text-rose-700' : 'bg-amber-100 text-amber-700');
            const icon = h.status === 'COMPLETED' ? 'fa-check-circle' : (h.status === 'FAILED' ? 'fa-times-circle' : 'fa-spinner fa-spin');
            
            return `
                <tr class="hover:bg-slate-50 transition-colors border-b border-slate-100">
                    <td class="px-4 py-4">
                        <div class="flex items-center gap-3">
                            <div class="w-8 h-8 rounded-lg bg-slate-100 flex items-center justify-center text-slate-400">
                                <i class="fa-solid fa-file-code"></i>
                            </div>
                            <div>
                                <h4 class="font-bold text-slate-800 text-xs">${h.filename}</h4>
                                <p class="text-[10px] text-slate-500">${h.created_at}</p>
                            </div>
                        </div>
                    </td>
                    <td class="px-4 py-4 text-center font-bold text-slate-700 text-xs">
                        ${h.total_records || 0}
                    </td>
                    <td class="px-4 py-4 text-center text-xs text-slate-500 font-mono">
                        ${h.process_time_ms ? (h.process_time_ms / 1000).toFixed(1) + 's' : '---'}
                    </td>
                    <td class="px-4 py-4 text-right">
                        <span class="px-2 py-0.5 rounded-full text-[9px] font-black uppercase tracking-wider ${statusClass} inline-flex items-center gap-1">
                            <i class="fa-solid ${icon}"></i> ${h.status}
                        </span>
                    </td>
                </tr>
            `;
        }).join('');

        tbody.innerHTML = rowsHtml;

    } catch (error) {
        console.error("[HISTORY] Error:", error);
    }
}
