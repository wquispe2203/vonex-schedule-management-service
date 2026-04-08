from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from . import service
from app.dependencies.auth import require_permission

router = APIRouter(prefix="/api/docentes", tags=["Docentes"])
router_mgmt = APIRouter(prefix="/api/mgmt/docentes", tags=["Gestión de Docentes"])

@router.get("/")
def list_docentes(db: Session = Depends(get_db), _ = Depends(require_permission("gestionar_docentes"))):
    return service.get_all_docentes(db)

@router_mgmt.post("/reprocesar-historico")
def run_reprocesar(db: Session = Depends(get_db), _ = Depends(require_permission("gestionar_docentes"))):
    return service.reprocesar_historico(db)
