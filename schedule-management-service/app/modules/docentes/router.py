import logging
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from uuid import UUID
from app.database import get_db
from app.dependencies.auth import get_current_active_user, require_permission
from .service import (
    get_active_teachers_list,
    get_active_teachers_for_rpt, # v3.10
    get_all_teachers,
    create_teacher_manual,
    update_teacher_data,
    update_teacher_status,       # v3.10
    get_teacher_activity_info,   # v3.10
    import_excel,
    cross_check_xml_teachers,
    reprocesar_historico,
    vincular_teacher_alias,
    get_sinasignar,
    update_sinasignar_item,
    promote_sinasignar,
    delete_sinasignar_item,
    merge_teachers,
)
from .schemas import (
    SuccessResponse,
    TeacherCreate,
    TeacherUpdate,
    SinAsignarUpdate,
    ExcelImportResult,
    XmlCrossCheckResult,
)
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/rpt-planilla/docentes", 
    tags=["Docentes"],
    dependencies=[Depends(require_permission("ver_docentes"))]
)


@router.get("", response_model=SuccessResponse[str])
def list_docentes(db: Session = Depends(get_db)):
    try:
        # REGLA v3.10: Cambiado a get_active_teachers_for_rpt
        data = get_active_teachers_for_rpt(db)
        return {"success": True, "data": data}
    except Exception as e:
        logger.error(f"Error en docentes: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno")


router_mgmt = APIRouter(
    prefix="/api/docentes", 
    tags=["Docentes — Gestión"],
    dependencies=[Depends(require_permission("gestionar_docentes"))]
)


# ── Maestra ────────────────────────────────────────────

@router_mgmt.get("")
def list_all_teachers(
    filter: str = Query("all"),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None), # acts, inacts
    db: Session = Depends(get_db),
):
    try:
        return get_all_teachers(db, filter, search, page, limit, status_filter)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router_mgmt.post("", status_code=201)
def create_teacher(payload: TeacherCreate, db: Session = Depends(get_db)):
    try:
        return create_teacher_manual(db, payload.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router_mgmt.put("/{teacher_id}")
def update_teacher(teacher_id: UUID, payload: TeacherUpdate, db: Session = Depends(get_db)):
    try:
        return update_teacher_data(db, teacher_id, payload.model_dump(exclude_none=True))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class StatusUpdate(BaseModel):
    is_active: bool

@router_mgmt.patch("/{teacher_id}/estado")
def patch_teacher_status(teacher_id: UUID, payload: StatusUpdate, db: Session = Depends(get_db)):
    """Actualiza manualmente el estado is_active (v3.10)."""
    try:
        data = update_teacher_status(db, teacher_id, payload.is_active)
        return {"success": True, "data": data}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router_mgmt.get("/{teacher_id}/actividad")
def get_teacher_activity(teacher_id: UUID, db: Session = Depends(get_db)):
    """Verifica si el docente tiene carga académica o reemplazos (v3.10)."""
    try:
        info = get_teacher_activity_info(db, teacher_id)
        return {"success": True, "data": info}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Excel Import ───────────────────────────────────────

@router_mgmt.post("/import-excel", response_model=ExcelImportResult)
async def import_excel_endpoint(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.lower().endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="Solo se permiten archivos Excel (.xlsx / .xls)")
    try:
        content = await file.read()
        return import_excel(db, content)
    except RuntimeError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Cross-check XML (manual) ──────────────────────────

@router_mgmt.post("/cross-check-xml", response_model=XmlCrossCheckResult)
def cross_check_xml_endpoint(payload: List[Dict[str, str]], db: Session = Depends(get_db)):
    try:
        return cross_check_xml_teachers(db, payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Reprocesamiento Histórico ─────────────────────────

@router_mgmt.post("/reprocesar-historico")
def reprocesar_historico_endpoint(db: Session = Depends(get_db)):
    """
    Procesa todos los docentes en la BD (XML históricos).
    1. Puebla normalized_name donde falta.
    2. Detecta teachers XML-only sin enriquecimiento Excel.
    3. Fuzzy match ≥ 90% → conflictos (para revisión humana).
    4. Sin match → inserta/actualiza en teachers_sinasignar.
    """
    try:
        return reprocesar_historico(db)
    except Exception as e:
        logger.error(f"[reprocesar_historico] Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ── Resolución de conflictos fuzzy ────────────────────

class VincularPayload(BaseModel):
    teacher_id: UUID
    target_norm: str


@router_mgmt.post("/vincular-alias")
def vincular_alias_endpoint(payload: VincularPayload, db: Session = Depends(get_db)):
    """Vincula el normalized_name de un teacher XML al del docente maestra sugerido."""
    try:
        return vincular_teacher_alias(db, payload.teacher_id, payload.target_norm)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Sin Asignar ───────────────────────────────────────

@router_mgmt.get("/sinasignar")
def list_sinasignar(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    try:
        return get_sinasignar(db, page, limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router_mgmt.put("/sinasignar/{sid}")
def update_sinasignar(sid: UUID, payload: SinAsignarUpdate, db: Session = Depends(get_db)):
    try:
        return update_sinasignar_item(db, sid, payload.model_dump(exclude_none=True))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router_mgmt.post("/sinasignar/{sid}/promote")
def promote_sinasignar_endpoint(sid: UUID, db: Session = Depends(get_db)):
    try:
        return promote_sinasignar(db, sid)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router_mgmt.delete("/sinasignar/{sid}", status_code=204)
def delete_sinasignar_endpoint(sid: UUID, db: Session = Depends(get_db)):
    try:
        delete_sinasignar_item(db, sid)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Fusión ─────────────────────────────────────────────

class MergeTeachersPayload(BaseModel):
    teacher_main_uid: UUID
    teacher_merge_uid: UUID


@router_mgmt.post("/fusionar")
def merge_teachers_endpoint(payload: MergeTeachersPayload, db: Session = Depends(get_db)):
    """
    Fusiona dos docentes en uno solo.
    Reasigna relaciones (Lessons, Observations) y elimina al secundario.
    """
    try:
        return merge_teachers(db, payload.teacher_main_uid, payload.teacher_merge_uid)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[merge_teachers] Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router_mgmt.get("/audit/duplicates")
def list_potential_duplicates(db: Session = Depends(get_db)):
    """Lista docentes marcados como posibles duplicados para revisión administrativa (v3.2)."""
    try:
        data = service.get_potential_duplicates(db)
        return {"success": True, "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
