import logging
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from uuid import UUID
from app.core.database import get_db
from app.dependencies.auth import get_current_active_user, require_permission
from app.core.schemas import StandardResponse, PaginatedResponseData
from .service import (
    get_active_teachers_list,
    get_active_teachers_for_rpt, # v3.10
    get_all_teachers,
    create_teacher_manual,
    update_teacher_data,
    update_teacher_status,
    get_teacher_activity_info,
    merge_teachers_logic,
    import_excel,
    cross_check_xml_teachers,
    reprocesar_historico,
    vincular_teacher_alias,
    get_sinasignar,
    get_sinasignar_crossed,
    get_conflictos_crossed,
    update_sinasignar_item,
    promote_sinasignar,
    delete_sinasignar_item,
    merge_teachers,
    get_matching_preview,
    resolve_conflict,
    undo_conflict,
)

from . import schemas
from .schemas import (
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


@router.get("", response_model=StandardResponse[PaginatedResponseData[schemas.TeacherHoursItem]])
def list_docentes(db: Session = Depends(get_db)):
    try:
        data = get_active_teachers_for_rpt(db)
        return {
            "success": True,
            "data": {
                "data": data,
                "total": len(data),
                "page": 1,
                "limit": len(data) if len(data) > 0 else 10,
                "total_pages": 1
            },
            "error": None
        }
    except Exception as e:
        logger.error(f"Error en docentes: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno")


router_mgmt = APIRouter(
    prefix="/api/docentes", 
    tags=["Docentes — Gestión"],
    dependencies=[Depends(require_permission("gestionar_docentes"))]
)


# ── Maestra ────────────────────────────────────────────

@router_mgmt.get("", response_model=schemas.DocenteListStandardResponse)
def list_all_teachers(
    filter: str = Query("all"),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None), # ACTIVO, INCOMPLETO, CONFLICTO, INVALIDO
    db: Session = Depends(get_db),
):
    try:
        return get_all_teachers(db, filter, search, page, limit, status)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router_mgmt.post("", response_model=schemas.DocenteStandardResponse, status_code=201)
def create_teacher(payload: TeacherCreate, db: Session = Depends(get_db)):
    try:
        if not payload.dni or payload.dni.strip() == "":
            raise HTTPException(status_code=400, detail="El DNI es obligatorio")
        data = create_teacher_manual(db, payload.model_dump())
        return {"success": True, "data": data, "error": None}
    except HTTPException as he:
        raise he
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router_mgmt.post("/merge", response_model=schemas.StandardResponse[Dict[str, Any]])
def merge_teachers_endpoint(payload: Dict[str, Any], db: Session = Depends(get_db)):
    try:
        primary_id = UUID(payload["primary_id"])
        secondary_id = UUID(payload["secondary_id"])
        data = merge_teachers_logic(db, primary_id, secondary_id)
        return {"success": True, "data": data, "error": None}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router_mgmt.put("/{teacher_id}", response_model=schemas.DocenteStandardResponse)
def update_teacher(teacher_id: UUID, payload: TeacherUpdate, db: Session = Depends(get_db)):
    try:
        if not payload.dni or payload.dni.strip() == "":
            raise HTTPException(status_code=400, detail="El DNI es obligatorio")
        data = update_teacher_data(db, teacher_id, payload.model_dump(exclude_none=True))
        return {"success": True, "data": data, "error": None}
    except HTTPException as he:
        raise he
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class StatusUpdate(BaseModel):
    is_active: bool

@router_mgmt.patch("/{teacher_id}/estado", response_model=schemas.DocenteStandardResponse)
def patch_teacher_status(teacher_id: UUID, payload: StatusUpdate, db: Session = Depends(get_db)):
    """Actualiza manualmente el estado is_active (v3.10)."""
    try:
        data = update_teacher_status(db, teacher_id, payload.is_active)
        return {"success": True, "data": data, "error": None}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router_mgmt.get("/{teacher_id}/actividad", response_model=schemas.StandardResponse[Dict[str, bool]])
def get_teacher_activity(teacher_id: UUID, db: Session = Depends(get_db)):
    """Verifica si el docente tiene carga académica o reemplazos (v3.10)."""
    try:
        info = get_teacher_activity_info(db, teacher_id)
        return {"success": True, "data": info, "error": None}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Excel Import ───────────────────────────────────────

@router_mgmt.post("/import-excel", response_model=schemas.ExcelImportStandardResponse)
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

@router_mgmt.post("/cross-check-xml", response_model=schemas.StandardResponse[XmlCrossCheckResult])
def cross_check_xml_endpoint(payload: List[Dict[str, str]], db: Session = Depends(get_db)):
    try:
        data = cross_check_xml_teachers(db, payload)
        return {"success": True, "data": data, "error": None}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Reprocesamiento Histórico ─────────────────────────

@router_mgmt.post("/reprocesar-historico", response_model=schemas.StandardResponse[Dict[str, Any]])
def reprocesar_historico_endpoint(db: Session = Depends(get_db)):
    try:
        data = reprocesar_historico(db)
        return {"success": True, "data": data, "error": None}
    except Exception as e:
        logger.error(f"[reprocesar_historico] Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ── Resolución de conflictos fuzzy ────────────────────

class VincularPayload(BaseModel):
    teacher_id: UUID
    target_norm: str


@router_mgmt.post("/vincular-alias", response_model=schemas.StandardResponse[Dict[str, str]])
def vincular_alias_endpoint(payload: VincularPayload, db: Session = Depends(get_db)):
    """Vincula el normalized_name de un teacher XML al del docente maestra sugerido."""
    try:
        data = vincular_teacher_alias(db, payload.teacher_id, payload.target_norm)
        return {"success": True, "data": data, "error": None}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Sin Asignar ───────────────────────────────────────

@router_mgmt.get("/sinasignar", response_model=schemas.SinAsignarListStandardResponse)
def list_sinasignar(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    try:
        return get_sinasignar_crossed(db, page, limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router_mgmt.get("/conflictos", response_model=schemas.ConflictoListStandardResponse)
def list_conflictos(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    try:
        return get_conflictos_crossed(db, page, limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router_mgmt.put("/sinasignar/{sid}", response_model=schemas.StandardResponse[Dict[str, Any]])
def update_sinasignar(sid: UUID, payload: SinAsignarUpdate, db: Session = Depends(get_db)):
    try:
        data = update_sinasignar_item(db, sid, payload.model_dump(exclude_none=True))
        return {"success": True, "data": data, "error": None}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router_mgmt.post("/sinasignar/{sid}/promote", response_model=schemas.StandardResponse[Dict[str, Any]])
def promote_sinasignar_endpoint(sid: UUID, db: Session = Depends(get_db)):
    try:
        data = promote_sinasignar(db, sid)
        return {"success": True, "data": data, "error": None}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router_mgmt.post("/resolve-conflict", response_model=schemas.StandardResponse[schemas.ResolveConflictResponse])
def resolve_conflict_endpoint(
    payload: schemas.ResolveConflictRequest,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_active_user)
):
    try:
        override_id = resolve_conflict(
            db=db,
            xml_name_raw=payload.xml_name_raw,
            teacher_id=payload.teacher_id,
            is_global=payload.is_global,
            current_user_id=current_user.id
        )
        return {
            "success": True,
            "data": {"override_id": override_id, "message": "Conflicto resuelto exitosamente"},
            "error": None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router_mgmt.delete("/resolve-conflict/{override_id}", response_model=schemas.StandardResponse[Dict[str, Any]])
def delete_conflict_override(
    override_id: UUID,
    db: Session = Depends(get_db)
):
    try:
        undo_conflict(db, override_id)
        return {"success": True, "data": {"message": "Override revertido correctamente"}, "error": None}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@router_mgmt.delete("/sinasignar/{sid}", response_model=schemas.StandardResponse[None], status_code=200)
def delete_sinasignar_endpoint(sid: UUID, db: Session = Depends(get_db)):
    try:
        delete_sinasignar_item(db, sid)
        return {"success": True, "data": None, "error": None}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Fusión ─────────────────────────────────────────────

class MergeTeachersPayload(BaseModel):
    teacher_main_uid: UUID
    teacher_merge_uid: UUID


@router_mgmt.post("/fusionar", response_model=schemas.StandardResponse[Dict[str, Any]])
def merge_teachers_endpoint(payload: MergeTeachersPayload, db: Session = Depends(get_db)):
    """
    Fusiona dos docentes en uno solo.
    Reasigna relaciones (Lessons, Observations) y elimina al secundario.
    """
    try:
        data = merge_teachers(db, payload.teacher_main_uid, payload.teacher_merge_uid)
        return {"success": True, "data": data, "error": None}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[merge_teachers] Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router_mgmt.get("/audit/duplicates", response_model=schemas.DocenteListStandardResponse)
def list_potential_duplicates(db: Session = Depends(get_db)):
    """Lista docentes marcados como posibles duplicados para revisión administrativa (v3.2)."""
    try:
        data = service.get_potential_duplicates(db)
        return {
            "success": True,
            "data": {
                "data": data,
                "total": len(data),
                "page": 1,
                "limit": len(data),
                "total_pages": 1
            },
            "error": None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router_mgmt.get("/matching-preview", response_model=schemas.MatchReviewListStandardResponse)
def matching_preview_endpoint(db: Session = Depends(get_db)):
    """Diagnóstico de matching sin automatización (v4.5)."""
    try:
        data = get_matching_preview(db)
        return {
            "success": True,
            "data": {
                "data": data,
                "total": len(data),
                "page": 1,
                "limit": len(data),
                "total_pages": 1
            },
            "error": None
        }
    except Exception as e:
        logger.error(f"[matching_preview] Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

