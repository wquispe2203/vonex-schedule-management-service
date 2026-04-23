# 🚀 Checklist Final de Producción

Este documento resume los pasos necesarios para desplegar el servicio de forma segura en un entorno de producción.

## 1. Configuración de Entorno (.env)
Asegúrate de que las siguientes variables estén definidas en el servidor:
- [ ] `DATABASE_URL`: URI completa de PostgreSQL (ej: `postgresql://user:pass@host:5432/db`).
- [ ] `ENVIRONMENT`: Debe ser `production` para activar restricciones de CORS y logging restrictivo.
- [ ] `CORS_ORIGINS`: Lista separada por comas de dominios permitidos (ej: `https://app.midominio.com,https://api.midominio.com`).

## 2. Base de Datos y Migraciones
- [ ] **Instalación**: `pip install -r requirements.txt`.
- [ ] **Baseline (Solo una vez)**: `python -m alembic revision --autogenerate -m "baseline_v1"`.
- [ ] **Sincronización**:
  - Si la base ya existe: `python -m alembic stamp head`.
  - Si la base es nueva: `python -m alembic upgrade head`.
- [ ] **Timeouts**: Verificados en `app/database.py` (`statement_timeout=10000`).

## 3. Despliegue y Escalado
- [ ] **Comando de Arranque**:
  ```bash
  gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app --bind 0.0.0.0:8000
  ```
- [ ] **Cálculo de Workers**: Recomendado `(2 * núcleos_cpu) + 1`. 
- [ ] **Límite de Conexiones**: Verifica que `max_connections` en Postgres sea mayor a `(workers * 60)`.

## 4. Observabilidad y Resiliencia
- [ ] **Logs**: Verifique que la salida de la consola sea JSON válido.
- [ ] **Health**: El endpoint `/health` debe integrarse con el el *liveness/readiness probe* de tu orquestador (K8s/Docker).
- [ ] **Latencia**: Monitorear logs con nivel `WARNING` (>2s) y `ERROR` (>5s).
- [ ] **Punto de Extensión**: El `metrics_middleware` en `main.py` está listo para ser conectado a un exportador de Prometheus si se requiere en el futuro.

---
**Arquitectura Base Cerrada y Estabilizada.**
