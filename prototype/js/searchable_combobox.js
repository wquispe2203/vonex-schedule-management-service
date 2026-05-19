// ============================================================
// Searchable Combobox — Módulo reutilizable VONEX
// Aplica en: OBSERVACIONES (obs) y RPT PLANILLAS (rpt)
// REGLA: NO modificar lógica RPT ni matching engine.
// ============================================================

/**
 * Estado interno por instancia de combobox.
 * @type {{ obs: {items: Array, selectedId: string, selectedName: string},
 *          rpt: {items: Array, selectedValue: string, selectedName: string} }}
 */
const comboboxState = {
    obs: { items: [], selectedId: '', selectedName: '' },
    rpt: { items: [], selectedValue: 'Todos', selectedName: 'Todos los Docentes' },
    obs_repl: { items: [], selectedId: '', selectedName: '' }
};

/** Callback registrado por reportes.js para auto-recargar al cambiar docente RPT */
let _onRptTeacherChange = null;

/**
 * Registra el callback que se llama al seleccionar un docente en RPT.
 * @param {Function} fn - Función a llamar (normalmente loadRptPlanilla(1))
 */
export function registerRptTeacherChangeCallback(fn) {
    _onRptTeacherChange = fn;
}

/**
 * Obtiene los elementos del DOM asociados a un contexto dado.
 * @param {'obs'|'rpt'|'obs_repl'} context
 */
function getElements(context) {
    if (context === 'obs') {
        return {
            input: document.getElementById('obs-docente-search'),
            dropdown: document.getElementById('obs-docente-dropdown'),
            hidden: document.getElementById('obs-filter-docente')
        };
    } else if (context === 'rpt') {
        return {
            input: document.getElementById('rpt-docente-search'),
            dropdown: document.getElementById('rpt-docente-dropdown'),
            hidden: document.getElementById('rpt-filter-docente')
        };
    } else if (context === 'obs_repl') {
        return {
            input: document.getElementById('obs-form-replacement-search'),
            dropdown: document.getElementById('obs-form-replacement-dropdown'),
            hidden: document.getElementById('obs-form-replacement-id')
        };
    }
    return { input: null, dropdown: null, hidden: null };
}

// ── OBS Repl Combobox ─────────────────────────────────────────────

/**
 * Popula el combobox de DOCENTE REEMPLAZANTE (obs_repl) a partir de la lista
 * de teachers ya cargada en la maestra.
 */
export function populateObsReplCombobox(teachers) {
    if (!Array.isArray(teachers)) return;

    comboboxState.obs_repl.items = teachers.map(t => ({
        id: t.id,
        label: `${t.last_name || ''}, ${t.first_name || ''}`.trim() || `Docente ${t.id}`
    }));

    // Limpiar selección anterior
    comboboxState.obs_repl.selectedId = '';
    comboboxState.obs_repl.selectedName = '';

    const inputEl = document.getElementById('obs-form-replacement-search');
    if (inputEl) inputEl.value = '';

    // Mantener el hidden select sincronizado
    const hiddenSelect = document.getElementById('obs-form-replacement-id');
    if (hiddenSelect) {
        hiddenSelect.innerHTML = '<option value="">Selecciona un docente...</option>';
        comboboxState.obs_repl.items.forEach(item => {
            const opt = document.createElement('option');
            opt.value = item.id;
            opt.textContent = item.label;
            hiddenSelect.appendChild(opt);
        });
    }
}

/**
 * Restablece y limpia la selección de un combobox.
 * @param {'obs'|'rpt'|'obs_repl'} context
 */
export function clearComboboxSelection(context) {
    const { input: inputEl, dropdown: dropdownEl, hidden: hiddenSelect } = getElements(context);

    if (context === 'obs') {
        comboboxState.obs.selectedId = '';
        comboboxState.obs.selectedName = '';
        if (inputEl) inputEl.value = '';
        if (hiddenSelect) hiddenSelect.value = '';
    } else if (context === 'obs_repl') {
        comboboxState.obs_repl.selectedId = '';
        comboboxState.obs_repl.selectedName = '';
        if (inputEl) inputEl.value = '';
        if (hiddenSelect) hiddenSelect.value = '';
    } else {
        comboboxState.rpt.selectedValue = 'Todos';
        comboboxState.rpt.selectedName = 'Todos los Docentes';
        if (inputEl) inputEl.value = 'Todos los Docentes';
        if (hiddenSelect) hiddenSelect.value = 'Todos';
        _updateRptNavState();
    }

    if (dropdownEl) dropdownEl.classList.add('hidden');
}

// ── OBS Combobox ─────────────────────────────────────────────────

/**
 * Popula el combobox de OBS a partir de la lista de teachers ya cargada
 * en el select oculto #obs-filter-docente.
 */
export function populateObsCombobox(teachers) {
    if (!Array.isArray(teachers)) return;

    comboboxState.obs.items = teachers.map(t => ({
        id: t.id,
        label: `${t.last_name || ''}, ${t.first_name || ''}`.trim() || `Docente ${t.id}`
    }));

    // Limpiar selección
    comboboxState.obs.selectedId = '';
    comboboxState.obs.selectedName = '';

    const inputEl = document.getElementById('obs-docente-search');
    if (inputEl) inputEl.value = '';

    // Mantener el hidden select sincronizado (para searchClassesForObs)
    const hiddenSelect = document.getElementById('obs-filter-docente');
    if (hiddenSelect) {
        hiddenSelect.innerHTML = '<option value="">Selecciona un docente...</option>';
        comboboxState.obs.items.forEach(item => {
            const opt = document.createElement('option');
            opt.value = item.id;
            opt.textContent = item.label;
            hiddenSelect.appendChild(opt);
        });
    }
}

// ── RPT Combobox ──────────────────────────────────────────────────

/**
 * Popula el combobox de RPT a partir de la lista de nombres ya cargada.
 */
export function populateRptCombobox(teachers) {
    if (!Array.isArray(teachers)) return;

    comboboxState.rpt.items = [
        { value: 'Todos', label: 'Todos los Docentes' },
        ...teachers.map(d => {
            const val = typeof d === 'object' && d !== null ? (d.name || '') : d;
            return { value: val, label: val };
        })
    ];

    comboboxState.rpt.selectedValue = 'Todos';
    comboboxState.rpt.selectedName = 'Todos los Docentes';

    const inputEl = document.getElementById('rpt-docente-search');
    if (inputEl) inputEl.value = 'Todos los Docentes';

    // Sincronizar hidden select para loadRptPlanilla
    const hiddenSelect = document.getElementById('rpt-filter-docente');
    if (hiddenSelect) {
        hiddenSelect.innerHTML = '<option value="Todos">Todos los Docentes</option>';
        comboboxState.rpt.items.slice(1).forEach(item => {
            const opt = document.createElement('option');
            opt.value = item.value;
            opt.textContent = item.label;
            hiddenSelect.appendChild(opt);
        });
    }

    _updateRptNavState();
}

// ── Shared Filter Logic ───────────────────────────────────────────

/**
 * Filtra el dropdown del combobox según lo que escribe el usuario.
 * @param {'obs'|'rpt'|'obs_repl'} context
 */
export function filterDocenteCombobox(context) {
    const { input: inputEl, dropdown: dropdownEl } = getElements(context);
    if (!inputEl || !dropdownEl) return;

    // Si el valor del input coincide exactamente con la sugerencia seleccionada, ocultar el dropdown y no filtrar
    const state = comboboxState[context];
    if (state && (inputEl.value === state.selectedName || inputEl.value === state.selectedValue) && inputEl.value !== '') {
        dropdownEl.classList.add('hidden');
        return;
    }

    const query = inputEl.value.trim().toLowerCase();
    const items = comboboxState[context]?.items || [];

    // Si vacío, mostrar todos
    const filtered = query
        ? items.filter(item => item.label.toLowerCase().includes(query))
        : items;

    if (filtered.length === 0) {
        dropdownEl.innerHTML = `<div class="px-4 py-3 text-sm text-slate-400 italic">Sin resultados para "${inputEl.value}"</div>`;
        dropdownEl.classList.remove('hidden');
        return;
    }

    dropdownEl.innerHTML = '';
    filtered.forEach((item) => {
        const div = document.createElement('div');
        div.className = 'px-4 py-2.5 text-sm text-slate-700 hover:bg-indigo-50 hover:text-indigo-700 cursor-pointer font-medium transition-colors';
        div.textContent = item.label;
        div.setAttribute('data-value', item.value || item.id);
        div.setAttribute('data-label', item.label);
        div.setAttribute('tabindex', '-1');
        div.addEventListener('mousedown', (e) => {
            e.preventDefault(); // evita que el input pierda foco antes del click
            _selectComboboxItem(context, item.value || item.id, item.label);
        });
        dropdownEl.appendChild(div);
    });

    dropdownEl.classList.remove('hidden');
}

/**
 * Selecciona un item del combobox y sincroniza el hidden select.
 */
function _selectComboboxItem(context, value, label) {
    const { input: inputEl, dropdown: dropdownEl, hidden: hiddenSelect } = getElements(context);

    if (inputEl) inputEl.value = label;
    if (dropdownEl) dropdownEl.classList.add('hidden');

    if (context === 'obs') {
        comboboxState.obs.selectedId = value;
        comboboxState.obs.selectedName = label;
        if (hiddenSelect) hiddenSelect.value = value;
    } else if (context === 'obs_repl') {
        comboboxState.obs_repl.selectedId = value;
        comboboxState.obs_repl.selectedName = label;
        if (hiddenSelect) hiddenSelect.value = value;
        
        // Disparar evento de input nativo para que otros listeners (como validaciones) se enteren del cambio
        if (inputEl) {
            inputEl.dispatchEvent(new Event('input', { bubbles: true }));
            inputEl.dispatchEvent(new Event('change', { bubbles: true }));
        }
    } else {
        comboboxState.rpt.selectedValue = value;
        comboboxState.rpt.selectedName = label;
        if (hiddenSelect) hiddenSelect.value = value;
        _updateRptNavState();
        // Disparar reload del RPT automáticamente al seleccionar docente
        if (typeof _onRptTeacherChange === 'function') {
            _onRptTeacherChange();
        }
    }
}

/**
 * Cierra el dropdown al hacer blur sobre el input.
 */
function _closeDropdown(context) {
    const { dropdown: dropdownEl } = getElements(context);
    if (dropdownEl) setTimeout(() => dropdownEl.classList.add('hidden'), 150);
}

// ── RPT Navigation ────────────────────────────────────────────────

/**
 * Navega al docente anterior (-1) o siguiente (+1) en la lista del combobox RPT.
 * Mejora: indicador de posición + disabled en extremos.
 */
export function navRptTeacher(delta) {
    const items = comboboxState.rpt.items;
    if (!items || items.length <= 1) return;

    const currentIdx = items.findIndex(i => i.value === comboboxState.rpt.selectedValue);
    let nextIdx = currentIdx + delta;

    if (nextIdx < 0) nextIdx = items.length - 1;
    if (nextIdx >= items.length) nextIdx = 0;

    const item = items[nextIdx];
    _selectComboboxItem('rpt', item.value, item.label);
}

/**
 * Actualiza el indicador de posición y el estado disabled de los botones nav.
 */
function _updateRptNavState() {
    const items = comboboxState.rpt.items;
    const currentIdx = items.findIndex(i => i.value === comboboxState.rpt.selectedValue);
    const total = items.length;

    const posEl = document.getElementById('rpt-teacher-pos');
    const totalEl = document.getElementById('rpt-teacher-total');
    const indicatorEl = document.getElementById('rpt-teacher-indicator');
    const prevBtn = document.getElementById('rpt-nav-prev');
    const nextBtn = document.getElementById('rpt-nav-next');

    if (total > 1) {
        if (indicatorEl) indicatorEl.classList.remove('hidden');
        if (posEl) posEl.textContent = currentIdx + 1;
        if (totalEl) totalEl.textContent = total;
    } else {
        if (indicatorEl) indicatorEl.classList.add('hidden');
    }

    if (prevBtn) prevBtn.disabled = total <= 1;
    if (nextBtn) nextBtn.disabled = total <= 1;
}

// ── Keyboard Navigation ───────────────────────────────────────────

/**
 * Maneja navegación por teclado (ENTER, ESC, Flechas) en los comboboxes.
 */
export function setupComboboxKeyboard() {
    ['obs', 'rpt', 'obs_repl'].forEach(context => {
        const { input: inputEl, dropdown: dropdownEl } = getElements(context);
        if (!inputEl || inputEl.dataset.kbBound) return;
        inputEl.dataset.kbBound = 'true';

        inputEl.addEventListener('input', () => filterDocenteCombobox(context));

        inputEl.addEventListener('blur', () => _closeDropdown(context));

        inputEl.addEventListener('keydown', (e) => {
            const items = dropdownEl?.querySelectorAll('[data-value]');

            if (e.key === 'Escape') {
                _closeDropdown(context);
                inputEl.blur();
                return;
            }

            if (e.key === 'Enter') {
                e.preventDefault();
                // Seleccionar primer resultado visible
                const first = dropdownEl?.querySelector('[data-value]');
                if (first) {
                    _selectComboboxItem(context, first.dataset.value, first.dataset.label);
                }
                return;
            }

            if (e.key === 'ArrowDown' && items?.length) {
                e.preventDefault();
                items[0]?.focus();
            }
        });

        // Navegación teclado dentro del dropdown
        if (dropdownEl) {
            dropdownEl.addEventListener('keydown', (e) => {
                const focused = document.activeElement;
                const items = [...dropdownEl.querySelectorAll('[data-value]')];
                const idx = items.indexOf(focused);

                if (e.key === 'ArrowDown') {
                    e.preventDefault();
                    items[Math.min(idx + 1, items.length - 1)]?.focus();
                } else if (e.key === 'ArrowUp') {
                    e.preventDefault();
                    if (idx <= 0) inputEl.focus();
                    else items[idx - 1]?.focus();
                } else if (e.key === 'Enter') {
                    e.preventDefault();
                    if (focused.dataset.value) {
                        _selectComboboxItem(context, focused.dataset.value, focused.dataset.label);
                    }
                } else if (e.key === 'Escape') {
                    _closeDropdown(context);
                    inputEl.focus();
                }
            });
        }
    });
}
