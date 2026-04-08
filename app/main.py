import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base
import app.models

# Crear las tablas automáticamente si no existen
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Schedule Management Service", version="1.0.0")

# Permitir CORS para el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:5500",
        "http://127.0.0.1:5500"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- DOMAIN-DRIVEN MODULES (MIGRATED) ----
from app.modules.docentes.router import router as docentes_router, router_mgmt as docentes_mgmt_router
from app.modules.observaciones.router import router as observaciones_router
from app.modules.horarios.router import router as horarios_router
from app.modules.reportes.router import router as reportes_router
from app.modules.configuracion.router import router as configuracion_router
from app.modules.usuarios.router import router as usuarios_router, rbac_router

app.include_router(usuarios_router)
app.include_router(rbac_router)
app.include_router(docentes_router)
app.include_router(docentes_mgmt_router)
app.include_router(observaciones_router)
app.include_router(horarios_router)
app.include_router(reportes_router)
app.include_router(configuracion_router)

@app.get("/")
def read_root():
    return {"message": "Schedule Management Service API is running"}
