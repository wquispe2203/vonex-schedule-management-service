// Configuration Module - Environment Aware
const isLocal = window.location.hostname === '127.0.0.1' || window.location.hostname === 'localhost';

export const API_BASE_URL = window.VONEX_API_URL || window.location.origin;

export const ENDPOINTS = {
    AUTH: {
        LOGIN: "/api/users/login",
        ME: "/api/users/me"
    },
    USERS: {
        BASE: "/api/users"
    },
    DOCENTES: {
        BASE: "/api/docentes",
        LIST: "/api/docentes",
        IMPORT: "/api/docentes/import-excel",
        SIN_ASIGNAR: "/api/docentes/sinasignar",
        CONFLICTOS: "/api/docentes/conflictos",
        RESOLVE_CONFLICT: "/api/docentes/resolve-conflict",
        ALL: "/api/docentes/all",
        BULK_DELETE_EXCEL: "/api/docentes/bulk-delete-excel"
    },
    MDM: {
        REVIEWS: "/api/mdm/reviews",
        STATS: "/api/mdm/stats"
    },
    OBSERVACIONES: {
        BASE: "/api/schedule/observations",
        LIST: "/api/schedule/observations",
        LOGS: "/api/schedule/observations/logs"
    },
    HORARIOS: {
        BASE: "/api/schedule",
        UPLOAD: "/api/schedule/upload",
        TEACHERS: "/api/schedule/teachers",
        CLASSES: "/api/schedule/classes",
        TEACHER_GRID: "/api/schedule/teacher",
        CLASS_GRID: "/api/schedule/classroom",
        HISTORY: "/api/schedule/xml-uploads"
    },
    REPORTES: {
        BASE: "/api/rpt-planilla",
        PLANILLA: "/api/rpt-planilla",
        EXPORT: "/api/rpt-planilla/export"
    },
    CONFIG: {
        BASE: "/api/config",
        RECESOS: "/api/config/recesos",
        ALMUERZOS: "/api/config/almuerzos"
    }
};
