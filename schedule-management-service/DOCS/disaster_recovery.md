# Disaster Recovery Plan — VONEX Schedule Management

## 1. Objetivos de Recuperación
- **RPO (Recovery Point Objective)**: 24 horas (Pérdida máxima de datos aceptable).
- **RTO (Recovery Time Objective)**: 4 horas (Tiempo máximo para restaurar el servicio).

## 2. Escenarios de Falla

| Escenario | Impacto | Estrategia de Mitigación |
| :--- | :--- | :--- |
| Corrupción de DB | Crítico | Restauración desde último backup diario (`ops/backups/`). |
| Pérdida de XMLs | Alto | Restauración desde snapshot (`ops/snapshots/`). |
| Fallo de Hardware | Total | Instalación limpia + Restauración completa de DB y XML. |

## 3. Matriz de Escalamiento
1. **Detección**: El sistema de logs (`ops/logs/`) reporta `[BACKUP FAILED]` o `[DATABASE_SCHEMA_INCONSISTENCY]`.
2. **Evaluación**: El administrador técnico verifica la integridad del último backup.
3. **Ejecución**: Se sigue el `Restore Runbook` para recuperar el estado operativo.

## 4. Estrategia de Rollback
Si una restauración falla, el sistema debe:
1. Eliminar la base de datos temporal `schedule_restore_tmp`.
2. Notificar error crítico al administrador.
3. Mantener la base de datos productiva intacta hasta que la validación en `tmp` sea exitosa.
