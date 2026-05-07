import os
import shutil
import tempfile
import urllib.parse
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from uuid import UUID
from app.core.database import get_db
from app.models import XmlUpload, User
from app.services.xml_upload import XMLUploadService
from typing import Optional, List
from . import schemas
from app.dependencies.auth import require_permission
from app.core.schemas import StandardResponse, PaginatedResponseData
# El service actual maneja grids y export, no upload. 
# Dejaremos la lógica de upload aquí por consistencia con el legacy o la moveremos a service luego.
from . import service

router = APIRouter(prefix="/api/schedule", tags=["Schedule Management"])

UPLOAD_DIR = "storage/xml_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
upload_service = XMLUploadService()

@router.post("/upload")
async def upload_xml(
    file: UploadFile = File(...),
    start_date: str = Form(...),
    end_date: str = Form(...),
    force_overwrite: str = Form("false"),
    usuario: str = Form("SISTEMA"),
    current_user: User = Depends(require_permission("subir_xml")),
    db: Session = Depends(get_db)
):
    if not file.filename.endswith(".xml"):
        raise HTTPException(status_code=400, detail="Solo se permiten archivos XML.")

    log_msg = f"[XML_UPLOAD] Usuario: {current_user.username} | Archivo: {file.filename} | Rango: {start_date} a {end_date}"
    print(log_msg)

    # Convert dates to check for overlap
    try:
        s_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        e_date = datetime.strptime(end_date, "%Y-%m-%d").date()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Formato de fecha inválido (debe ser YYYY-MM-DD): {str(e)}")

    ovw = force_overwrite.lower() == "true" if isinstance(force_overwrite, str) else bool(force_overwrite)

    # Overlap check
    overlapping = db.query(XmlUpload).filter(
        XmlUpload.status == "COMPLETED",
        XmlUpload.start_date <= e_date,
        XmlUpload.end_date >= s_date
    ).all()

    if overlapping and not ovw:
        print("[XML OVERLAP DETECTED]")
        import logging
        logging.getLogger(__name__).warning(f"[XML OVERLAP DETECTED] New Range: {start_date} to {end_date} overlaps with {len(overlapping)} completed uploads.")
        return {
            "success": True,
            "overlap_detected": True,
            "overlapping_uploads": [
                {
                    "id": str(u.id),
                    "filename": u.filename,
                    "start_date": str(u.start_date),
                    "end_date": str(u.end_date)
                } for u in overlapping
            ],
            "error": None
        }

    if overlapping and ovw:
        print("[XML OVERWRITE CONFIRMED]")
        print("[XML PREVIOUS UPLOADS ARCHIVED]")
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"[XML OVERWRITE CONFIRMED] User confirmed overwrite for range {start_date} to {end_date}.")
        for u in overlapping:
            logger.info(f"[XML PREVIOUS UPLOADS ARCHIVED] Archiving upload ID: {u.id}, Filename: {u.filename}")
            u.status = "ARCHIVED"
        db.commit()

    with tempfile.NamedTemporaryFile(delete=False, suffix=".xml") as tmp:
        shutil.copyfileobj(file.file, tmp)
        temp_path = tmp.name
    try:
        result = upload_service.process_upload(
            db=db,
            file_path=temp_path,
            start_date=start_date,
            end_date=end_date,
            overwrite=True,
            user_id=current_user.id,
            original_filename=file.filename,
            usuario=current_user.username
        )
        
        if not result.get("success"):
            db.rollback()
            # 400 para duplicados de rango o integridad
            if result.get("error_type") in ["DUPLICATE_RANGE", "INTEGRITY_ERROR"]:
                raise HTTPException(status_code=400, detail=result.get("message"))
            
            if result.get("conflicts"):
                raise HTTPException(status_code=409, detail=result)
            else:
                raise HTTPException(status_code=500, detail=result.get("message", "Internal Server Error"))
        
        final_path = os.path.join(UPLOAD_DIR, f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}")
        shutil.move(temp_path, final_path)
        
        # PERSISTIR PATH EN DB
        db.query(XmlUpload).filter(XmlUpload.id == result["upload_id"]).update({"storage_path": final_path})
        db.commit()

        result["storage_path"] = final_path
        return {"success": True, "data": result, "error": None}

    except HTTPException as he:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise he
    except Exception as e:
        db.rollback()
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/xml-uploads", response_model=StandardResponse[PaginatedResponseData[schemas.XmlUploadHistoryItem]])
def get_xml_uploads(page: int = Query(1, ge=1), limit: int = Query(5, ge=1, le=50), db: Session = Depends(get_db), _ = Depends(require_permission("ver_horarios"))):
    skip = (page - 1) * limit
    total_records = db.query(XmlUpload).count()
    total_pages = max(1, (total_records + limit - 1) // limit)
    
    uploads = db.query(
        XmlUpload.id,
        XmlUpload.filename,
        XmlUpload.status,
        XmlUpload.total_records,
        XmlUpload.processed_records,
        XmlUpload.fallback_count,
        XmlUpload.process_time_ms,
        XmlUpload.created_at
    ).order_by(XmlUpload.created_at.desc()).offset(skip).limit(limit).all()
    
    data_items = [
        schemas.XmlUploadHistoryItem(
            id=u.id,
            filename=u.filename,
            status=u.status,
            total_records=u.total_records,
            processed_records=u.processed_records,
            fallback_count=u.fallback_count,
            process_time_ms=u.process_time_ms,
            created_at=u.created_at.strftime("%Y-%m-%d %H:%M:%S") if u.created_at else None
        ) for u in uploads
    ]
    
    return schemas.StandardResponse(
        success=True,
        data=schemas.PaginatedResponseData(
            data=data_items,
            total=total_records,
            page=page,
            limit=limit,
            total_pages=total_pages
        )
    )

@router.get("/xml-uploads/{upload_id}/report", response_model=schemas.StandardResponse[schemas.XmlUploadReportResponse])
def get_xml_upload_report(upload_id: UUID, db: Session = Depends(get_db), _ = Depends(require_permission("ver_horarios"))):
    try:
        upload = db.query(XmlUpload).filter(XmlUpload.id == upload_id).first()
        if not upload:
            raise HTTPException(status_code=404, detail="Carga XML no encontrada")
        
        report_data = {
            "matched_exact": [],
            "matched_fuzzy": [],
            "unmatched_new": [],
            "duplicates": []
        }
        
        if upload.error_summary:
            import json
            try:
                raw_report = json.loads(upload.error_summary)
                # Normalización de contrato
                if isinstance(raw_report, dict):
                    inner = raw_report.get("teacher_report", raw_report)
                    report_data.update({
                        "matched_exact": inner.get("matched_exact", []),
                        "matched_fuzzy": inner.get("matched_fuzzy", []),
                        "unmatched_new": inner.get("unmatched_new", []),
                        "duplicates": inner.get("duplicates", [])
                    })
            except Exception:
                pass
                
        return {"success": True, "data": report_data, "error": None}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/teachers", response_model=StandardResponse[PaginatedResponseData[schemas.TeacherBasicResponse]])
def get_teachers(db: Session = Depends(get_db), _ = Depends(require_permission("ver_horarios"))):
    try:
        data = service.get_teachers_list(db)
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

@router.get("/classes", response_model=StandardResponse[PaginatedResponseData[schemas.ClassGroupResponse]])
def get_classes(db: Session = Depends(get_db), _ = Depends(require_permission("ver_horarios"))):
    try:
        data = service.get_classes_list(db)
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

@router.get("/teacher/{teacher_id}", response_model=StandardResponse[PaginatedResponseData[schemas.TeacherSessionResponse]])
def get_teacher_schedule(teacher_id: UUID, start_date: str, end_date: str, db: Session = Depends(get_db), _ = Depends(require_permission("ver_horarios"))):
    try:
        data = service.get_teacher_schedule_grid(db, teacher_id, start_date, end_date)
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

@router.get("/classroom/{class_id}", response_model=StandardResponse[PaginatedResponseData[schemas.ClassroomSessionResponse]])
def get_classroom_schedule(class_id: UUID, start_date: str, end_date: str, db: Session = Depends(get_db), _ = Depends(require_permission("ver_horarios"))):
    try:
        data = service.get_classroom_schedule_grid(db, class_id, start_date, end_date)
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

@router.get("/export")
def export_schedules(type: str, target_id: UUID, start_date: str, end_date: str, db: Session = Depends(get_db), _ = Depends(require_permission("ver_horarios"))):
    try:
        excel_file = service.get_export_excel_bytes(db, type, target_id, start_date, end_date)
        
        today_str = datetime.now().strftime("%Y%m%d")
        filename = f"horarios_export_{today_str}.xlsx"
        filename_encoded = urllib.parse.quote(filename)
        
        headers = {
            'Content-Disposition': f'attachment; filename*=UTF-8\'\'{filename_encoded}'
        }
        
        return StreamingResponse(
            excel_file, 
            headers=headers,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
