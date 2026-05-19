# Restore Runbook — Guía de Recuperación

Instrucciones para la restauración segura de datos ante incidentes.

## 1. Restauración de Base de Datos

### Script: `ops/restore/restore_db.py`

**Paso 1: Dry-Run (Recomendado)**
Valida que el archivo de backup sea legible sin modificar nada.
```powershell
python ops/restore/restore_db.py <nombre_backup>.sql.gz
```

**Paso 2: Restauración Completa en Temp**
Restaura en la base de datos `schedule_restore_tmp` para validar integridad.
```powershell
python ops/restore/restore_db.py <nombre_backup>.sql.gz --full
```

**Paso 3: Promoción a Producción (Manual)**
Una vez validado el paso 2, se puede proceder a restaurar sobre la DB principal.

---

## 2. Restauración de Almacenamiento XML

### Script: `ops/restore/restore_xml.py`

**Ejecución**:
```powershell
python ops/restore/restore_xml.py <nombre_snapshot>.zip --full
```
Esto extraerá los archivos en `ops/restore/xml_tmp/` para su inspección manual antes de moverlos a `storage/`.

---

## 3. Resolución de Problemas (Troubleshooting)

- **Error: Lock file exists**: Si el backup falló anteriormente, elimine manualmente `ops/scripts/backup.lock`.
- **Error: Integrity check failed**: El archivo de backup podría estar corrupto o incompleto. Intente con el backup del día anterior.
