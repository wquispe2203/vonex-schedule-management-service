# Simulación Dry-Run de Limpieza (Cleanup Dry-Run)

Este documento detalla la simulación **Dry-Run** de la fase previa de Reset Operativo Controlado. Muestra el número exacto de registros afectados, relaciones colapsadas en cascada y el estado final de las tablas de base de datos.

---

## 1. Resumen de Impacto en Base de Datos

El orden de ejecución de la limpieza está diseñado para respetar las dependencias relacionales y evitar violaciones de claves foráneas. A continuación se muestra la proyección exacta del impacto de la limpieza secuencial:

| Paso | Operación / Tabla | Criterio de Selección | Tipo de Impacto | Registros Afectados | Estado Final |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Paso 1** | `observations` | Todas las observaciones académicas | `TRUNCATE` / `DELETE` | **137** | **Vacía (0)** |
| **Paso 2** | `rpt_planilla` | `xml_upload_id = '8bc2c3a5-fa43-4cb2-8971-ebd07ccb5b84'` | `DELETE` | **4,819** | **Vacía (0)** |
| **Paso 3** | `schedule_sessions` | `xml_upload_id = '8bc2c3a5-fa43-4cb2-8971-ebd07ccb5b84'` | `DELETE` | **8,402** | **Vacía (0)** |
| **Paso 4** | `lessons` | Todas las lecciones asociadas en cascada | `DELETE` (Cascada de sesiones) | **3,715** | **Parcial (377)** |
| **Paso 5** | `teachers` (Excel) | `source_id LIKE 'EXCEL_%'` | `DELETE` | **159** | **Activa (31)** |
| **Paso 6** | `xml_uploads` | `id = '8bc2c3a5-fa43-4cb2-8971-ebd07ccb5b84'` | `DELETE` | **1** | **Vacía (0)** |
| **Paso 7** | Archivo Físico | `storage/xml_uploads/historical_xml_import_202603.xml` | Eliminación de Disco | **1** | **Eliminado** |

---

## 2. Detalle de Relaciones que Colapsan en Cascada

1. **Tabla `observations`**:
   - Al truncar esta tabla primero, se eliminan las 137 observaciones (123 asociadas a docentes de Excel y 14 a docentes no-Excel). Esto previene cualquier violación de clave externa o colapso no intencionado.
2. **Tabla `lessons`**:
   - Existen **4,092 lecciones** totales. De estas, **3,715 lecciones** corresponden a las sesiones del XML `historical_xml_import_202603.xml` y se eliminarán en cascada.
   - Las **377 lecciones** restantes corresponden a configuraciones del sistema o registros históricos manuales que no tienen sesiones de este XML, y permanecerán intactas.
3. **Tabla `teachers`**:
   - Se eliminan físicamente **159 docentes** importados desde Excel.
   - Se conservan **31 docentes** (27 activos, 4 incompletos) que corresponden a docentes creados manualmente o legados independientes.
4. **Tabla `xml_uploads`**:
   - Se elimina el único registro cargado. El sistema quedará en estado limpio, listo para recibir cargas de XML frescas sin superposiciones de datos históricos.
