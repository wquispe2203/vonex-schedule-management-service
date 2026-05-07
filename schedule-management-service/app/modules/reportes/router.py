from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import date
import io
from fastapi.responses import StreamingResponse
from app.core.database import get_db
from . import schemas
from . import service
from . import repository
from app.dependencies.auth import require_permission, get_current_active_user
from app.core.schemas import StandardResponse, PaginatedResponseData

router = APIRouter(prefix="/api/rpt-planilla", tags=["RPT Planilla"])

@router.get("/", response_model=schemas.ReportFullResponse)
def list_rpt_planilla(
    fecha_inicio: date,
    fecha_fin: date,
    docente: Optional[str] = Query(None),
    sede: Optional[str] = Query(None),
    aula: Optional[str] = Query(None),
    xml_upload_id: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    _ = Depends(require_permission("ver_rpt"))
):
    try:
        data = service.get_planilla_data(db, fecha_inicio, fecha_fin, docente, sede, aula, page, limit, xml_upload_id)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error interno al generar el reporte")

from app.modules.docentes.service import get_active_teachers_for_rpt
from app.modules.docentes.schemas import TeacherHoursItem

@router.get("/docentes", response_model=StandardResponse[PaginatedResponseData[TeacherHoursItem]])
def get_docentes(db: Session = Depends(get_db), _ = Depends(require_permission("ver_docentes"))):
    docentes = get_active_teachers_for_rpt(db)
    return {
        "success": True,
        "data": {
            "data": docentes,
            "total": len(docentes),
            "page": 1,
            "limit": len(docentes) if len(docentes) > 0 else 10,
            "total_pages": 1
        },
        "error": None
    }

@router.get("/sedes", response_model=schemas.SedeListResponse)
def list_sedes(db: Session = Depends(get_db), _ = Depends(require_permission("ver_rpt"))):
    sedes = repository.fetch_distinct_sedes(db)
    return {
        "success": True,
        "data": {
            "data": sedes,
            "total": len(sedes),
            "page": 1,
            "limit": len(sedes),
            "total_pages": 1
        },
        "error": None
    }

@router.get("/aulas", response_model=schemas.AulaListResponse)
def list_aulas(sede: str, db: Session = Depends(get_db), _ = Depends(require_permission("ver_rpt"))):
    aulas = repository.fetch_distinct_aulas(db, sede)
    return {
        "success": True,
        "data": {
            "data": aulas,
            "total": len(aulas),
            "page": 1,
            "limit": len(aulas),
            "total_pages": 1
        },
        "error": None
    }

@router.get("/export")
def export_rpt_planilla(
    fecha_inicio: date,
    fecha_fin: date,
    docente: Optional[str] = Query(None),
    sede: Optional[str] = Query(None),
    aula: Optional[str] = Query(None),
    xml_upload_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    _ = Depends(require_permission("exportar_rpt"))
):
    try:
        # 1. Obtener la data completa (sin paginación para export)
        raw_data = service.get_planilla_data(db, fecha_inicio, fecha_fin, docente, sede, aula, page=1, limit=100000, xml_upload_id=xml_upload_id)
        
        if not raw_data.get("data"):
            raise HTTPException(status_code=404, detail="No hay datos para exportar")

        # 2. Generar archivo en el service (puro Python)
        excel_io = service.generate_excel_file(raw_data["data"])
        
        filename = f"RPT_Planilla_{fecha_inicio}_al_{fecha_fin}.xlsx"
        return StreamingResponse(
            excel_io,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting Excel: {str(e)}")
