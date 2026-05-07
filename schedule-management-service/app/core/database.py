import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import event
import contextvars
import logging
from app.core.config import settings

# Configuración de Logger para Auditoría SQL
audit_logger = logging.getLogger("sql_audit")
audit_logger.setLevel(logging.INFO)
if not audit_logger.handlers:
    fh = logging.FileHandler("sql_audit.log", encoding="utf-8")
    fh.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
    audit_logger.addHandler(fh)

# Variable de contexto para habilitar logging SQL selectivo
sql_logging_ctx = contextvars.ContextVar("sql_logging_ctx", default=False)

# Configuración de base de datos desde settings
SQLALCHEMY_DATABASE_URL = settings.database_url

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_size=20,
    max_overflow=40,
    pool_timeout=30,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

from app.models.base import Base

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- INSTRUMENTACIÓN DE DEBUG SQL ---
@event.listens_for(engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    if sql_logging_ctx.get():
        audit_logger.info("EJECTUANDO CONSULTA SQL")
        audit_logger.info(f"STMT: {statement}")
        audit_logger.info(f"PARAMS: {parameters}")
        
        if parameters:
            types_info = {k: type(v).__name__ for k, v in (parameters.items() if isinstance(parameters, dict) else enumerate(parameters))}
            audit_logger.info(f"PARAM_TYPES: {types_info}")
