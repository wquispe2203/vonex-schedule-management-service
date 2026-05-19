# Seguridad y Hardening del Botón SUPERADMIN (Superadmin Delete Security)

Este documento detalla los controles de seguridad y hardening técnico aplicados a la acción **"Eliminar docentes importados"** para evitar ejecuciones accidentales, bypasses de frontend o accesos no autorizados.

---

## 1. Validación de Seguridad de Doble Capa

El sistema implementa seguridad en profundidad (Defense in Depth) para garantizar que la acción destructiva solo sea ejecutable bajo condiciones legítimas.

### A. Frontend Hardening (Capa de Presentación)
1. **Control de Visibilidad**: El botón `#btn-delete-excel-teachers` en la interfaz de usuario se renderiza de forma condicional. Solo es visible si el token de autenticación del usuario actual decodifica con el rol `SUPERADMIN`.
2. **Doble Confirmación Visual**: 
   * Al hacer clic, se abre un modal de advertencia crítica explicando el impacto.
   * El usuario debe ingresar la palabra de confirmación exacta: `"RESET"` en un campo de texto para habilitar el botón físico de ejecución.

### B. Backend Hardening (Capa de Servicio)
1. **Protección de Ruta con RBAC**:
   El endpoint `/api/docentes/bulk-delete-excel` requiere autenticación por token JWT y valida de forma estricta que el usuario posea el rol de `SUPERADMIN` o el permiso correspondiente:
   ```python
   @router.post("/bulk-delete-excel")
   async def bulk_delete_excel(
       current_user: User = Depends(get_current_active_superadmin),
       db: Session = Depends(get_db)
   ):
   ```
2. **Inmunidad a Manipulaciones de Cliente**: Si un atacante altera el DOM o realiza un bypass del frontend para invocar el endpoint directamente, el backend rechazará la petición con un error HTTP `403 Forbidden` al no poseer el rol verificado en el token de sesión seguro.

---

## 2. Trazabilidad y Registro de Auditoría Obligatorio

Cada ejecución exitosa del Reset Operativo Controlado quedará registrada en el sistema de auditoría estructurado del backend:

```python
logger.info(
    "[SUPERADMIN OPERATION SUCCESS] | User: %s | Action: BULK_DELETE_EXCEL_TEACHERS | "
    "Timestamp: %s | Deleted Count: %d | Trace ID: %s",
    current_user.email,
    datetime.utcnow().isoformat(),
    deleted_count,
    trace_id
)
```

### Campos Registrados:
* **Usuario Ejecutor**: Dirección de correo electrónico / ID del SUPERADMIN autenticado.
* **Timestamp**: Marca de tiempo exacta en formato ISO UTC.
* **Cantidad Eliminada**: Número exacto de registros `teachers` removidos físicamente.
* **Trace ID**: Identificador único de transacción generado automáticamente para la correlación en logs de infraestructura.
