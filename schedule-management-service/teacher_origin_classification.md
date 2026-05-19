# Clasificación del Origen de Docentes (Teacher Origin Classification)

Este documento detalla la auditoría y clasificación rigurosa del origen de los docentes almacenados actualmente en la base de datos de **Vonex Schedule Management Service**.

---

## 1. Evidencia Exacta de Clasificación

Para garantizar que no haya eliminaciones accidentales de docentes esenciales, se ha analizado exhaustivamente la estructura de datos. Las columnas que determinan de manera definitiva el origen de cada registro son:
1. `source`: Columna que denota si el registro se creó manualmente (`manual`).
2. `source_id`: Identificador de origen asignado al momento de la creación o importación. Presenta prefijos y formatos de longitud fija consistentes.
3. `status`: Estado de validación del docente (`ACTIVO` o `INCOMPLETO`).
4. `dni`: Documento Nacional de Identidad.

### Cantidades y Categorías Identificadas

| Origen / Categoría | Columna Determinante | Patrón / Formato Detectado | Estado (`status`) | Cantidad Exacta | Uso y Significado |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Docentes Importados por Excel** | `source_id` | `EXCEL_[timestamp]_[fila]` (Ej. `EXCEL_1774469594_12`) | `ACTIVO` | **159** | Carga masiva de docentes a la Maestra por administradores. |
| **Docentes Históricos / XML** | `source_id` | Hexadecimal de 16 caracteres (Longitud fija 16) | `ACTIVO` | **21** | Docentes consolidados del XML histórico de marzo. |
| **Docentes de XML Incompletos** | `source_id` | Hexadecimal de 16 caracteres (Longitud fija 16) | `INCOMPLETO` | **4** | Docentes del XML con datos faltantes (sin DNI). |
| **Docentes Fantasma (Ghost)** | `source_id` | `GHOST_[timestamp]` | `ACTIVO` | **5** | Docentes virtuales o provisionales del sistema. |
| **Docentes Promocionados** | `source_id` | `PROMOTED_[timestamp]` | `ACTIVO` | **1** | Docentes promovidos internamente. |

**Total General de Docentes en el Sistema: 190**

---

## 2. Definición Estricta de Criterio de Eliminación

Para el proceso de **Reset Operativo Controlado**, la condición de eliminación física de los docentes importados por Excel se define **estrictamente** de la siguiente manera:

```sql
DELETE FROM teachers 
WHERE source_id LIKE 'EXCEL_%' 
  AND source = 'manual';
```

Esta regla garantiza al 100% que:
1. Ninguno de los 25 docentes heredados o consolidados mediante XML (`OTHER_HEX_FORMAT`) sea afectado.
2. Ningún docente fantasma (`GHOST_*`) o promocionado (`PROMOTED_*`) sea eliminado.
3. Se proteja la integridad de los docentes creados bajo otros flujos.
