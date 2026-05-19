# Auditoría de Dependencias del XML Histórico (Historical XML Dependency Audit)

Este documento detalla la auditoría de dependencias y el impacto relacional del archivo **`historical_xml_import_202603.xml`** en la base de datos de **Vonex Schedule Management Service**.

---

## 1. Inventario e Identificación del Archivo XML Histórico

* **Nombre de Archivo**: `historical_xml_import_202603.xml`
* **UUID de Registro en BD (`xml_uploads.id`)**: `8bc2c3a5-fa43-4cb2-8971-ebd07ccb5b84`
* **Estado de Carga**: `COMPLETED`
* **Fecha de Registro**: `2026-04-08 00:00:00-05:00`
* **Ruta de Almacenamiento en Disco**: `storage/xml_uploads/historical_xml_import_202603.xml`
* **Verificación de Archivo Físico**: **EXISTENTE (True)**

---

## 2. Conteos de Dependencias Asociadas Directas e Indirectas

Se ha realizado una consulta exhaustiva a la base de datos para mapear cada registro de las tablas de negocio vinculado con esta carga. El inventario exacto es el siguiente:

### A. Sesiones de Horario (`schedule_sessions`)
* **Registros Relacionados**: **8,402**
* **Criterio de Asociación**: `xml_upload_id = '8bc2c3a5-fa43-4cb2-8971-ebd07ccb5b84'`
* **Impacto de Eliminación**: Remoción física completa de las 8,402 sesiones.

### B. Reportes de Planillas Consolidadas (`rpt_planilla`)
* **Registros Relacionados**: **4,819**
* **Criterio de Asociación**: `xml_upload_id = '8bc2c3a5-fa43-4cb2-8971-ebd07ccb5b84'`
* **Impacto de Eliminación**: Remoción física completa de las 4,819 planillas asociadas.

### C. Observaciones Académicas (`observations`)
* **Registros Relacionados**: **137** (25 Faltas y 112 Reemplazos)
* **Criterio de Asociación**: Vinculadas a través de `session_id` con `schedule_sessions` pertenecientes a este XML.
* **Impacto de Eliminación**: Remoción física completa de las 137 observaciones.

### D. Lecciones Académicas (`lessons`)
* **Registros Relacionados**: **3,715**
* **Criterio de Asociación**: Lecciones referenciadas en las sesiones de este XML.
* **Impacto de Eliminación**: Cascada directa de eliminación a través de `lesson_id` en las sesiones.

### E. Mappings y Overrides (`teacher_name_overrides`)
* **Registros Relacionados**: **0**
* **Impacto de Eliminación**: Ninguno.

---

## 3. Estrategia de Eliminación Quirúrgica

Para realizar la remoción del XML histórico sin dejar datos huérfanos ni romper restricciones de clave ajena:
1. Se limpia la tabla de observaciones (`observations`) para desvincular las referencias cruzadas de docentes de reemplazo.
2. Se eliminan los reportes consolidados (`rpt_planilla`) asociados al ID del XML.
3. Se eliminan las sesiones de horario (`schedule_sessions`) asociadas al ID del XML, lo que a su vez elimina las lecciones y tarjetas asociadas por cascada.
4. Se elimina el registro de `xml_uploads`.
5. Se remueve el archivo físico del disco `storage/xml_uploads/historical_xml_import_202603.xml` de forma segura.
