# Seguridad de Reimportación Futura (Reimport Safety Validation)

Este documento detalla la validación de seguridad para garantizar que tras la ejecución del **Reset Operativo Controlado**, las reimportaciones de XML y Excel se realicen sin conflictos de claves únicas, índices corruptos o duplicidad de registros.

---

## 1. Estado de Restricciones e Índices en la Base de Datos

Se ha auditado la integridad física de las restricciones únicas en la base de datos PostgreSQL. Los resultados confirman un estado de salud excelente:

* **Duplicados en DNI Activos**: **0**
* **Duplicados en Nombre Normalizado Activos**: **0**
* **Duplicados en `source_id`**: **0**

Esto asegura que la base de datos se encuentra libre de corrupción relacional y lista para el proceso de limpieza y posterior importación limpia.

---

## 2. Salvaguardas para Importaciones de Excel Futuras

Para evitar colisiones de datos tras el reset, el importador de Excel de docentes (`import_excel` en `service.py`) y la creación manual aplican un protocolo estricto:

1. **Búsqueda por DNI**: 
   Antes de insertar un nuevo docente, el sistema busca en la base de datos si existe algún docente con el mismo DNI. Si se detecta, se actualiza el registro existente en lugar de duplicarlo:
   ```python
   if dni:
       existing = repository.fetch_teacher_by_dni(db, dni)
   ```
2. **Búsqueda por Nombre Normalizado**:
   Si no tiene DNI, el sistema realiza una normalización fonética y de caracteres del nombre del docente y busca coincidencias exactas para prevenir duplicados por variaciones ortográficas:
   ```python
   existing = repository.fetch_teacher_by_normalized(db, norm)
   ```
3. **Generación Segura de `source_id`**:
   Los docentes creados por Excel generan un identificador único basado en la marca de tiempo de alta resolución y el número de fila:
   `EXCEL_[timestamp]_[row_idx]`. Esto garantiza la total inmunidad frente a colisiones físicas de claves primarias.

---

## 3. Salvaguardas para Importaciones de XML Futuras

El motor de cruce y consolidación semanal de XML está protegido mediante:

1. **Normalización Estricta de Nombres**:
   El motor utiliza `normalize_name()` con comparación por tokens y similitud estricta difflib para emparejar la base de datos de la Maestra con el XML entrante. Esto evita la duplicidad física de sesiones o docentes.
2. **Restricción Única de Sesión**:
   La tabla `schedule_sessions` cuenta con una clave única compuesta `uq_session_lesson_time`:
   ```sql
   UNIQUE CONSTRAINT uq_session_lesson_time (lesson_id, session_date, start_time)
   ```
   Esto impide a nivel de base de datos la creación de sesiones duplicadas para la misma lección en la misma fecha y hora.
3. **Protección de Overlaps por `xml_upload_id`**:
   Las nuevas sesiones creadas estarán asociadas a un nuevo `xml_upload_id`, lo que permite un control total y aislar históricamente cada importación semanal de forma segura.
