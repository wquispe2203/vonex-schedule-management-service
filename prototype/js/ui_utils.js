// UI Utilities Module - ES6

export function getCalculatedTime(startTime, endTime, subject) {
    if (!startTime || !endTime) return "---";
    // Si es receso, mostramos hora exacta
    if (subject.includes("RECESO") || subject.includes("ALMUERZO")) {
        return `${startTime.substring(0, 5)} - ${endTime.substring(0, 5)}`;
    }
    // Lógica para bloques pedagógicos si fuera necesario
    return `${startTime.substring(0, 5)} - ${endTime.substring(0, 5)}`;
}

export function cleanCycleName(name) {
    if (!name) return "---";
    return name.replace(/\s*\([^)]*\)$/, '').trim();
}

export function getCourseColor(subject, type) {
    if (!subject) return 'bg-slate-50 border-slate-200';
    const s = subject.toUpperCase();
    if (s.includes('MATEMATICA')) return 'bg-blue-50 border-blue-200 text-blue-900';
    if (s.includes('LENGUAJE') || s.includes('VERBAL')) return 'bg-rose-50 border-rose-200 text-rose-900';
    if (s.includes('FISICA') || s.includes('QUIMICA')) return 'bg-emerald-50 border-emerald-200 text-emerald-900';
    if (s.includes('HISTORIA') || s.includes('GEOGRAFIA')) return 'bg-amber-50 border-amber-200 text-amber-900';
    if (s.includes('BIOLOGIA')) return 'bg-green-50 border-green-200 text-green-900';
    return 'bg-slate-50 border-slate-200 text-slate-800';
}

export function calculateDurationMinutes(start, end) {
    if (!start || !end) return 0;
    const [h1, m1] = start.split(':').map(Number);
    const [h2, m2] = end.split(':').map(Number);
    return (h2 * 60 + m2) - (h1 * 60 + m1);
}
