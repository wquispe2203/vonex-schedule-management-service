# Informe de Bloqueos de Investigación (QA Validation)

Se han detectado los siguientes bloqueos críticos que impiden la validación E2E del sistema:

1. **Desincronización de Base de Datos**: 
   - El modelo espera la columna `old_system_id`, pero la base de datos aún tiene `legacy_id`.
   - La migración `18d9f168a2eb` está pendiente según `alembic current`.
   - **Consecuencia**: Todos los endpoints de Usuarios, Docentes y Login están caídos con `ProgrammingError`.

2. **Fugas de Seguridad/Sintaxis en Frontend**:
   - `js_dump.js` y `index.html` inyectan UUIDs en atributos `onclick` sin comillas.
   - **Consecuencia**: El navegador arroja errores de sintaxis al intentar interpretar los guiones como operadores matemáticos.

3. **Bloqueo de Autenticación para Tests 422**:
   - No se puede validar el rechazo de IDs numéricos (422) sin un token, y no se puede obtener el token porque el login está roto por el punto #1.

## Propuestas de Desbloqueo:
- Ejecutar `alembic upgrade head` inmediatamente.
- Saneamiento masivo de `index.html` y `js_dump.js`.
- Uso de un endpoint "bypass" temporal para verificar la lógica de Pydantic si se prefiere no usar credenciales reales en scripts de test.
