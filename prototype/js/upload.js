// Upload Module - ES6
import api from './api.js';
import { ENDPOINTS } from './config.js';

export function setupUploadHandlers() {
    const fileInput = document.getElementById('file-upload');
    if (fileInput) {
        fileInput.addEventListener('change', updateFileName);
    }

    const dropZone = document.getElementById('drop-zone');
    if (dropZone) {
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, e => {
                e.preventDefault();
                e.stopPropagation();
            }, false);
        });

        ['dragenter', 'dragover'].forEach(eventName => {
            dropZone.addEventListener(eventName, () => dropZone.classList.add('bg-indigo-50', 'border-indigo-400'), false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, () => dropZone.classList.remove('bg-indigo-50', 'border-indigo-400'), false);
        });

        dropZone.addEventListener('drop', (e) => {
            const dt = e.dataTransfer;
            if (fileInput) {
                fileInput.files = dt.files;
                updateFileName();
            }
        }, false);
    }
}

function updateFileName() {
    const fileInput = document.getElementById('file-upload');
    const fileNameDisplay = document.getElementById('file-name-display');
    if (fileInput && fileInput.files.length > 0) {
        fileNameDisplay.textContent = fileInput.files[0].name;
        fileNameDisplay.classList.add('text-indigo-600');
    } else if (fileNameDisplay) {
        fileNameDisplay.textContent = "Arrastra tu XML aquí";
        fileNameDisplay.classList.remove('text-indigo-600');
    }
}

export async function simulateUpload(overwrite = false) {
    const btn = document.getElementById('upload-btn');
    const fileInput = document.getElementById('file-upload');
    const startDate = document.getElementById('start-date').value;
    const endDate = document.getElementById('end-date').value;
    const progressFill = document.getElementById('progress-bar-fill');
    const statusLabel = document.getElementById('progress-status');

    if (!fileInput.files.length || !startDate || !endDate) {
        alert("Por favor selecciona un archivo XML, fecha inicio y fecha fin.");
        return;
    }

    btn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Procesando y Parseando...';
    btn.disabled = true;
    btn.classList.add('opacity-75');

    document.getElementById('upload-progress').classList.remove('hidden');
    const conflictAlert = document.getElementById('conflict-alert');
    if (conflictAlert) conflictAlert.classList.add('hidden');
    
    closeOverwriteModal();

    progressFill.style.width = "20%";

    const formData = new FormData();
    formData.append("file", fileInput.files[0]);
    formData.append("start_date", startDate);
    formData.append("end_date", endDate);
    formData.append("force_overwrite", overwrite);

    // Simulated progress steps
    setTimeout(() => {
        progressFill.style.width = "45%";
        document.getElementById('task-subjects').innerHTML = '<i class="fa-solid fa-check text-green-500 mr-2"></i> Extracción de Subjects';
    }, 800);

    setTimeout(() => {
        progressFill.style.width = "70%";
        document.getElementById('task-teachers').innerHTML = '<i class="fa-solid fa-check text-green-500 mr-2"></i> Extracción de Docentes';
    }, 1800);

    try {
        const data = await api.authFetch(ENDPOINTS.HORARIOS.UPLOAD, {
            method: "POST",
            body: formData
            // Nota: FormData no requiere header Content-Type manual (el navegador lo genera con boundary)
        });

        // Si llegamos aquí, res.ok es true y data está parseado
        progressFill.style.width = "100%";
        statusLabel.innerText = "Finalizado";
        document.getElementById('task-lessons').innerHTML = '<i class="fa-solid fa-check text-green-500 mr-2"></i> Generando Lesson Cards...';

        setTimeout(() => {
            alert(`¡Éxito! Horario procesado con ${data.records} sesiones.`);
            resetUpload();
            if (typeof window.loadUploadHistory === 'function') window.loadUploadHistory();
        }, 500);
    } catch (error) {
        document.getElementById('upload-progress').classList.add('hidden');
        
        // Manejo específico de error 400 por sobrescritura (ahora el error vive en error.message o r.data)
        // Nota: El wrapper actual lanza un Error con message = data.detail.
        if (error.message.includes("force_overwrite=true")) {
            document.getElementById('overwrite-modal-msg').innerText = error.message;
            document.getElementById('overwrite-modal').classList.remove('hidden');
            btn.innerHTML = '<i class="fa-solid fa-wand-magic-sparkles"></i> Vincular y Procesar';
            btn.disabled = false;
            btn.classList.remove('opacity-75');
        } else {
            alert("Error: " + error.message);
            resetUpload();
        }
    }
}

export function resetUpload() {
    const btn = document.getElementById('upload-btn');
    const conflictAlert = document.getElementById('conflict-alert');
    if (conflictAlert) conflictAlert.classList.add('hidden');
    document.getElementById('upload-progress').classList.add('hidden');
    btn.innerHTML = '<i class="fa-solid fa-wand-magic-sparkles"></i> Vincular y Procesar';
    btn.disabled = false;
    btn.classList.remove('opacity-75');
    const fileInput = document.getElementById('file-upload');
    if (fileInput) fileInput.value = null;
    updateFileName();
}

export function closeOverwriteModal() {
    const modal = document.getElementById('overwrite-modal');
    if (modal) modal.classList.add('hidden');
}

export function confirmOverwrite() {
    simulateUpload(true);
}
