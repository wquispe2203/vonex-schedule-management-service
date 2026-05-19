# Auditoría de Integridad de Observaciones (Observations Integrity Audit)

Este documento detalla la auditoría funcional y relacional de la tabla `observations` antes de proceder con el proceso de vaciado seguro para el **Reset Operativo Controlado**.

---

## 1. Mapeo y Clasificación de Observaciones

Actualmente existen **137 observaciones** académicas registradas en la base de datos. Se clasifican bajo los siguientes tipos funcionales:

* **FALTA**: **25** registros.
  * Representan las ausencias registradas de docentes primarios.
* **REEMPLAZO**: **112** registros.
  * Representan las ausencias que cuentan con una asignación de reemplazo.

---

## 2. Auditoría de Reemplazos Activos y Referencias de Docentes

Se ha verificado la vinculación de cada observación con las entidades de la Maestra de Docentes (`teachers`):

1. **Docentes Primarios de Referencia**: Existen **23 docentes primarios únicos** asociados a estas 137 observaciones.
2. **Docentes de Reemplazo de Referencia**: Existen **18 docentes de reemplazo únicos** asignados a las 112 observaciones de tipo `REEMPLAZO`.
3. **Referencias a Docentes de Excel**:
   * **123 observaciones** tienen como docente primario a un docente importado de Excel.
   * **48 observaciones** tienen como docente de reemplazo a un docente importado de Excel.
4. **Overrides y Reglas Activas**: No se identificaron overrides locales ni globales que afecten a los reemplazos activos o requieran preservarse de forma independiente, ya que toda la data proviene del XML de marzo de 2026.

---

## 3. Impacto en Motores de Reglas y RPT Planillas

El vaciado completo de la tabla `observations` es una medida fundamental de cara al reset por las siguientes razones:

* **Previene Violaciones de Clave Foránea**: Al eliminar la referencia a los docentes importados de Excel (que figuran en 123 y 48 registros como docente primario y de reemplazo respectivamente), se puede proceder con la eliminación física de estos docentes de manera limpia y sin errores de integridad.
* **Reseteo del Motor de Conflictos y Reemplazos**: Al no haber observaciones activas registradas, el motor de conflictos iniciará en un estado purgado, eliminando alertas de dobles asignaciones o cruces de horarios inválidos del periodo histórico.
* **Cero Impacto en Reglas Académicas y RPT**: El truncado no altera las fórmulas del cálculo RPT, la lógica de recesos, el cálculo F+30 ni el esquema de la base de datos. Simplemente limpia el histórico operacional para preparar el sistema para la nueva planificación limpia.
