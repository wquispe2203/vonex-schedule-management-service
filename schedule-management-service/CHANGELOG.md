# Historial de Cambios (CHANGELOG.md)
**Proyecto:** Sistema de Gestión Académica (Schedule Management Service)

Todas las modificaciones notables a este proyecto serán documentadas en este archivo siguiendo el estándar de **Auditoría Técnica**.

---

## [1.1.0] - Seguridad y Módulo RBAC - 2024-04-06

### Módulo: Usuarios y Seguridad (NUEVO)
*   **Modelo RBAC Relacional:** Migración de estructura heredada (`role` string temporal) a un esquema formal `User-Role-Permission` de relaciones Muchos-a-Muchos (`user_roles`, `role_permissions`).
*   **Autenticación JWT:** Implementación de `OAuth2PasswordBearer`, firma HS256 y parseo del campo `sub` asegurando acceso confiado y hashing robusto vía `bcrypt` (mitigación de conflictos con `passlib`).
*   **Validación Estricta de Dominio:** Capa lógica en `crear_usuario` y `login` que rechaza transaccionalmente cualquier e-mail no terminado en `@vonex.edu.pe` (Seguridad Perimetral Lógica).
*   **Bypass Seguro:** Dependencia `require_permission` estructurada con eager-loading de roles (evita N+1). Reconoce de manera automatizada (case-insensitive) una omisión de chequeo para los roles maestros `SISTEMAS` o `SUPERADMIN`.
*   **Hardening Endpoints:** Interceptadas todas las peticiones con requisitos de autorización per-funcionalidad (ej. `ver_rpt`, `exportar_rpt`, `subir_xml`). Permisos asignados por defecto mediante Bootstrapping local de seguridad (`seed_rbac.py`).

---

## [1.0.0] - Versión Inicial "Core System" - 2024-04-06

### Módulo: Docentes (MDM)
*   **Normalización:** Implementación de algoritmo `NFKD` para limpieza de nombres y eliminación de tildes.
*   **Fuzzy Matching:** Motor de búsqueda de similitud (90% threshold) para detección de duplicados en XML.
*   **Staging:** Creación de la tabla `teachers_sinasignar` para manejo de docentes XML no identificados.
*   **Fusión:** Lógica de `Merge` transaccional para consolidar registros históricos y reasignar relaciones (Lessons/Observations).
*   **Importación:** Soporte para carga masiva desde Excel con mapeo dinámico de columnas (DNI, Nombres, Razón Social).

### Módulo: Horarios
*   **Parser XML:** Motor de importación para archivos aSc Horarios.
*   **Generador de Sesiones:** Lógica de expansión de `Cards` en sesiones físicas por rango de fechas.
*   **Validador de Conflictos:** Detección de traslapes horarios y duplicidad de aulas.

### Módulo: Observaciones (Incidencias)
*   **Registro Dual:** Soporte para incidencias tipo FALTA (descuento) y REEMPLAZO (pago).
*   **Agrupador UI:** Lógica para mostrar sesiones continuas como un solo bloque para el usuario final.
*   **Vinculación Dinámica:** Capacidad de registrar reemplazos con nombres manuales que alimentan el Master Data Management (MDM).

### Módulo: Reportes (RPT Planilla)
*   **Lógica Binaria:** Implementación de cálculo 0/100 para horas de reemplazo en tiempo real.
*   **Exportación:** Generación de archivos Excel (`openpyxl`) para validación de planilla de pagos.
*   **Lógica de Recesos:** Cálculo automatizado de 0.33 horas de receso asignadas al primer bloque de clase del día.

---

## Estándar de Registro Futuro
Para cada nueva versión o cambio, se deberá registrar:
1.  **Fecha**
2.  **Módulo afectado**
3.  **Cambio:** Descripción técnica.
4.  **Motivo:** Justificación de negocio o bug fix.
5.  **Impacto:** Qué partes del sistema se ven afectadas.
6.  **Riesgos:** Posibles efectos secundarios tras el cambio.
