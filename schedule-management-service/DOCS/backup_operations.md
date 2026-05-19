# Backup Operations — Manual de Usuario

Este documento describe el funcionamiento de las herramientas de respaldo localizadas en `ops/scripts/`.

## 1. Backup de Base de Datos (PostgreSQL)

### Script: `ops/scripts/db_backup.py`
Realiza un volcado comprimido de la base de datos productiva.

**Requisitos**:
- Variable de entorno `PGPASSWORD` configurada.
- Acceso a `pg_dump.exe`.

**Ejecución Manual**:
```powershell
python ops/scripts/db_backup.py
```

**Automatización (Windows Task Scheduler)**:
1. Crear una tarea básica diaria.
2. Acción: Iniciar un programa.
3. Programa: `python.exe`
4. Argumentos: `C:\...\ops\scripts\db_backup.py`

---

## 2. Snapshot de Almacenamiento XML

### Script: `ops/scripts/xml_snapshot.py`
Genera un snapshot comprimido de `storage/xml_uploads/`.

**Ejecución Manual**:
```powershell
python ops/scripts/xml_snapshot.py
```

---

## 3. Logs y Auditoría
Todos los logs se encuentran en `ops/logs/`:
- `backup.log`: Trazabilidad de DB.
- `xml_snapshot.log`: Trazabilidad de archivos.
