---
trigger: always_on
---

# VONEX SCHEDULE MANAGEMENT SERVICE — GLOBAL ENGINEERING RULES

## 1. Arquitectura General

El proyecto sigue arquitectura modular desacoplada basada en FastAPI.

Cada módulo debe respetar estrictamente:

- router.py → endpoints HTTP
- service.py → reglas de negocio
- repository.py → acceso a datos
- schemas.py → validaciones Pydantic
- models.py → SQLAlchemy ORM

Reglas:
- Nunca colocar lógica de negocio en routers.
- Nunca realizar queries SQL directas desde routers.
- Nunca acceder a DB desde frontend.
- Mantener separación estricta de capas.
- Evitar dependencias cruzadas innecesarias entre módulos.

---

## 2. Protección de Arquitectura

Antes de modificar código:

- Analizar impacto completo del cambio.
- Detectar dependencias indirectas.
- Detectar imports circulares.
- Detectar side effects.
- Validar compatibilidad con:
  - XML Upload
  - RPT Planillas
  - Docentes
  - Observaciones
  - Auth/RBAC
  - Configuración

Nunca romper:
- multi-upload architecture
- upload history
- XML overlap handling
- RPT consolidation
- teacher assignment integrity
- UUID integrity
- RBAC permissions

---

## 3. Reglas de Refactorización

Toda refactorización debe:

- Mantener compatibilidad backward.
- No romper endpoints existentes.
- No cambiar contratos JSON sin aprobación.
- No modificar nombres de tablas sin migración formal.
- No eliminar logs estructurales.
- No alterar lógica validada en producción.

Antes de refactorizar:
- analizar riesgos
- validar impacto
- proponer plan
- ejecutar pruebas

---

## 4. XML Upload Rules

El sistema XML es crítico.

Reglas:
- Todo upload debe ser idempotente.
- Detectar overlaps de fechas.
- Solicitar confirmación antes de overwrite.
- Archivar uploads previos al sobrescribir.
- Mantener trazabilidad histórica.
- Nunca duplicar sesiones.
- Nunca duplicar horas dictadas.
- Nunca mezclar uploads de distintas semanas.

Validaciones obligatorias:
- fecha_inicio
- fecha_fin
- xml_upload_id
- estado upload
- consolidación por semana

---

## 5. RPT Planillas Rules

El RPT debe respetar:

- consolidación de bloques
- F+30
- overlaps reales
- recesos oficiales
- single break per teacher/day

Receso oficial:
- RECESO 1 → 09:40–10:00
- RECESO 2 → 10:30–10:50
- CORTE FINAL → 11:40
- Máximo 1 receso por docente/día
- Valor → 0.33

Nunca:
- generar 0.66
- duplicar bloques
- partir bloques F+30 incorrectamente
- generar recesos en tarde/noche

---

## 6. Frontend Rules

Frontend modular Vanilla JS.

Reglas:
- No duplicar listeners.
- Usar dataset.bound.
- Evitar cloneNode(true).
- Mantener delegación centralizada.
- No romper navegación SPA.
- Mantener filtros persistentes.
- Mantener responsive layout.

Toda modificación visual debe:
- evitar overflow
- evitar overlap
- usar grid/flex correctamente
- mantener compatibilidad 1366px+

---

## 7. Logging Obligatorio

Toda lógica compleja debe incluir logs estructurados.

Formato:
- [MODULE ACTION]
- [RPT XML MERGED]
- [RPT BREAK WINDOW]
- [UPLOAD OVERLAP]
- etc.

Nunca usar logs ambiguos.

---

## 8. Testing Obligatorio

Todo código nuevo o modificado debe incluir:

- prueba unitaria
o
- prueba de integración

Si no existe validación:
- el cambio NO debe considerarse completo.

Validaciones mínimas:
- happy path
- edge cases
- duplicate handling
- overlap handling
- null safety
- retry safety

---

## 9. Database Rules

Nunca:
- hacer DELETE masivo sin auditoría
- romper foreign keys
- eliminar UUIDs
- alterar constraints sin migración

Toda migración:
- debe ser reversible
- debe validarse antes
- debe registrar impacto

---

## 10. Anti-Regressions

Antes de finalizar cualquier tarea:

Verificar:
- uploads XML
- RPT totals
- filtros frontend
- docentes sin asignar
- consolidación
- recesos
- exportaciones
- auth
- navegación SPA

Nunca asumir que algo funciona:
siempre validar.

---

## 11. Circular Imports Prevention

Detectar y prevenir:
- circular imports
- recursive services
- repository cross-calls
- module dependency leaks

Preferir:
- dependency injection
- utility services
- isolated repositories
- shared helpers

---

## 12. Estilo de Trabajo Esperado

Siempre:
- explicar causa raíz
- proponer solución estructural
- evitar hotfixes frágiles
- priorizar estabilidad
- mantener observabilidad
- documentar cambios importantes

El objetivo principal es:
ESTABILIDAD + TRAZABILIDAD + ESCALABILIDAD.