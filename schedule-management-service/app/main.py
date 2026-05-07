import os
import json
import uuid
import logging
import datetime
import traceback
from contextvars import ContextVar

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles

# --- Imports Locales Core ---
from app.core.context import request_id_ctx
from app.core.database import sql_logging_ctx
from app.core.schema_validator import validate_db_schema

# --- CONFIGURACIÓN DE LOGGING ESTRUCTURADO (12-FACTOR) ---
from app.core.logging_config import setup_logging
logger = setup_logging()

def setup_middlewares(application: FastAPI):
    # CORS Configuration
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @application.middleware("http")
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
            raise e
        finally:
            request_id_ctx.reset(token)

    @application.middleware("http")
    async def sql_audit_middleware(request: Request, call_next):
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

def setup_exception_handlers(application: FastAPI):
    @application.exception_handler(RequestValidationError)
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
        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "data": None,
                "error": "Validation Error: " + str(exc.errors())
            },
        )

    @application.exception_handler(Exception)
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
                "success": False,
                "data": None,
                "error": "Error interno del servidor. Por favor, contacte al soporte técnico."
            }
        )

def setup_routers(application: FastAPI):
    # Importaciones de routers DENTRO de la función para evitar dependencias circulares e imports tempranos
    from app.modules.docentes.router import router as docentes_router, router_mgmt as docentes_mgmt_router
    from app.modules.docentes.mdm_router import router as mdm_router
    from app.modules.observaciones.router import router as observaciones_router
    from app.modules.horarios.router import router as horarios_router
    from app.modules.reportes.router import router as reportes_router
    from app.modules.configuracion.router import router as configuracion_router
    from app.modules.usuarios.router import router as usuarios_router, rbac_router
    from app.modules.auditoria.router import router as auditoria_router

    application.include_router(usuarios_router)
    application.include_router(rbac_router)
    application.include_router(docentes_router)
    application.include_router(docentes_mgmt_router)
    application.include_router(mdm_router)
    application.include_router(observaciones_router)
    application.include_router(horarios_router)
    application.include_router(reportes_router)
    application.include_router(configuracion_router)
    application.include_router(auditoria_router)

def create_app() -> FastAPI:
    """
    Application Factory Pattern.
    Crea, configura y retorna la instancia ASGI (FastAPI).
    Garantiza aislamiento entre entornos y trabajadores (Gunicorn/Uvicorn).
    """
    application = FastAPI(title="Schedule Management Service", version="1.0.0")

    # 1. Configurar Middlewares
    setup_middlewares(application)

    # 2. Configurar Manejo de Excepciones
    setup_exception_handlers(application)

    # 3. Registrar Routers
    setup_routers(application)

    # 4. Registrar Eventos del Ciclo de Vida
    @application.on_event("startup")
    async def startup_event():
        if not validate_db_schema():
            logger.critical("DATABASE_SCHEMA_INCONSISTENCY: El esquema de la base de datos no coincide con los modelos.")
        else:
            logger.info("DATABASE_SCHEMA_VALIDATED: Paridad total entre modelos y base de datos.")

    # 5. Montar Archivos Estáticos (Frontend)
    PROTO_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../prototype"))
    if os.path.exists(PROTO_PATH):
        application.mount("/prototype", StaticFiles(directory=PROTO_PATH, html=True), name="prototype")
        logger.info(f"Montado /prototype desde {PROTO_PATH}")
    else:
        logger.warning(f"No se encontró el directorio /prototype en {PROTO_PATH}")

    # 6. Endpoints Base
    @application.get("/")
    def read_root():
        return {"message": "Schedule Management Service API is running"}

    # ROOT CAUSE FIX: Retornar EXPRESAMENTE la instancia ASGI, no el módulo 'app'
    return application
