import os
import json
import uuid
import logging
import datetime
from contextvars import ContextVar
from .core.context import request_id_ctx
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from .database import engine, Base, sql_logging_ctx
import traceback
import app.models

# --- CONFIGURACIÓN DE LOGGING ESTRUCTURADO (12-FACTOR) ---

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": request_id_ctx.get(),
        }
        
        # Reservamos campos base para no sobreescribirlos con 'extra'
        base_fields = set(log_record.keys())
        
        # Campos estándar de logging que no queremos en el JSON final por defecto
        ignored_fields = {
            'args', 'asctime', 'created', 'exc_info', 'exc_text', 'filename',
            'funcName', 'levelname', 'levelno', 'lineno', 'module',
            'msecs', 'msg', 'name', 'pathname', 'process', 'processName',
            'relativeCreated', 'stack_info', 'thread', 'threadName'
        }

        # Incluir todos los campos extra dinámicamente
        for key, value in record.__dict__.items():
            if key not in ignored_fields and key not in base_fields:
                log_record[key] = value

        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
            
        return json.dumps(log_record)

# Configurar logger raíz para emitir solo a stdout
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
root_logger.handlers = [handler]

logger = logging.getLogger("app_main")

# Crear las tablas automáticamente si no existen
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Schedule Management Service", version="1.0.0")

from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
import traceback

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning(
        "Validation error", 
        extra={
            "path": request.url.path, 
            "method": request.method,
            "status_code": 422,
            "details": exc.errors()
        }
    )
    # FormData no es JSON serializable, lo removemos o convertimos si es necesario
    body = exc.body
    if hasattr(body, '__dict__') or not isinstance(body, (dict, list, str, int, float, bool, type(None))):
        body = "<Unserializable or Large Body>"

    return JSONResponse(
        status_code=422,
        content={
            "detail": exc.errors(), 
            "body": body,
            "request_id": request_id_ctx.get()
        },
    )

@app.exception_handler(Exception)
async def standard_exception_handler(request: Request, exc: Exception):
    logger.error(
        f"Unhandled exception: {str(exc)}", 
        exc_info=True,
        extra={
            "path": request.url.path, 
            "method": request.method,
            "status_code": 500
        }
    )
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Error interno del servidor. Por favor, contacte al soporte técnico.",
            "request_id": request_id_ctx.get()
        }
    )

# --- MIDDLEWARE DE DIAGNÓSTICO SQL ---
# --- MIDDLEWARE DE REQUEST-ID Y LOGGING ---
@app.middleware("http")
async def request_id_and_logging_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    token = request_id_ctx.set(request_id)
    
    start_time = datetime.datetime.now()
    try:
        response = await call_next(request)
        process_time = (datetime.datetime.now() - start_time).total_seconds()
        
        logger.info(
            f"Finished request",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "process_time": process_time
            }
        )
        response.headers["X-Request-ID"] = request_id
        return response
    except Exception as e:
        # El standard_exception_handler se encargará de esto si no se captura aquí
        raise e
    finally:
        request_id_ctx.reset(token)

# --- MIDDLEWARE DE DIAGNÓSTICO SQL ---
@app.middleware("http")
async def sql_audit_middleware(request: Request, call_next):
    # Definir rutas objetivo del audit
    target_paths = ["/api/rpt-planilla", "/api/schedule/observations"]
    
    should_log = any(request.url.path.startswith(tp) for tp in target_paths)
    
    if should_log:
        token = sql_logging_ctx.set(True)
        audit_logger = logging.getLogger("sql_audit")
        audit_logger.info(f"--- [AUDIT-START] Endpoint: {request.method} {request.url.path} ---")
        try:
            response = await call_next(request)
            return response
        finally:
            audit_logger.info(f"--- [AUDIT-END] Finalizada traza SQL ---\n")
            sql_logging_ctx.reset(token)
    else:
        return await call_next(request)

# Configuración de CORS
origins = [
    "http://127.0.0.1:5500",
    "http://localhost:5500",
    "http://127.0.0.1:8080",
    "http://localhost:8080",
    "http://127.0.0.1:8000",
    "http://localhost:8000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- DOMAIN-DRIVEN MODULES (MIGRATED) ----
from app.modules.docentes.router import router as docentes_router, router_mgmt as docentes_mgmt_router
from app.modules.docentes.mdm_router import router as mdm_router
from app.modules.observaciones.router import router as observaciones_router
from app.modules.horarios.router import router as horarios_router
from app.modules.reportes.router import router as reportes_router
from app.modules.configuracion.router import router as configuracion_router
from app.modules.usuarios.router import router as usuarios_router, rbac_router

app.include_router(usuarios_router)
app.include_router(rbac_router)
app.include_router(docentes_router)
app.include_router(docentes_mgmt_router)
app.include_router(mdm_router)
app.include_router(observaciones_router)
app.include_router(horarios_router)
app.include_router(reportes_router)
app.include_router(configuracion_router)

from fastapi.staticfiles import StaticFiles
import os

# Determinar ruta del prototipo (relativa a la ubicación del backend)
PROTO_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../prototype"))
if os.path.exists(PROTO_PATH):
    app.mount("/prototype", StaticFiles(directory=PROTO_PATH, html=True), name="prototype")
    print(f"DEBUG: Montado /prototype desde {PROTO_PATH}")
else:
    print(f"WARN: No se encontró el directorio /prototype en {PROTO_PATH}")

@app.get("/")
def read_root():
    return {"message": "Schedule Management Service API is running"}
