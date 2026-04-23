import os
import shutil
import tempfile
import urllib.parse
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from uuid import UUID
from app.database import get_db
from app.models import XmlUpload, User
from app.services.xml_upload import XMLUploadService
from typing import Optional, List
from . import schemas
from app.dependencies.auth import require_permission
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

    with tempfile.NamedTemporaryFile(delete=False, suffix=".xml") as tmp:
        shutil.copyfileobj(file.file, tmp)
        temp_path = tmp.name
    try:
        ovw = force_overwrite.lower() == "true" if isinstance(force_overwrite, str) else bool(force_overwrite)

        result = upload_service.process_upload(
            db=db,
            file_path=temp_path,
            start_date=start_date,
            end_date=end_date,
            overwrite=ovw,
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
        result["storage_path"] = final_path
        return result

    except HTTPException as he:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise he
    except Exception as e:
        db.rollback()
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/xml-uploads")
def get_xml_uploads(page: int = 1, limit: int = 5, db: Session = Depends(get_db), _ = Depends(require_permission("ver_horarios"))):
    skip = (page - 1) * limit
    total_records = db.query(XmlUpload).count()
    total_pages = (total_records + limit - 1) // limit if total_records > 0 else 1
    
    uploads = db.query(
        XmlUpload.id,
        XmlUpload.filename,
        XmlUpload.start_date,
        XmlUpload.end_date,
        XmlUpload.is_force_overwrite,
        XmlUpload.created_at
    ).order_by(XmlUpload.created_at.desc()).offset(skip).limit(limit).all()
    
    return {
        "success": True, 
        "data": [
            {
                "id": u.id,
                "filename": u.filename,
                "start_date": u.start_date.strftime("%Y-%m-%d"),
                "end_date": u.end_date.strftime("%Y-%m-%d"),
                "is_force_overwrite": u.is_force_overwrite,
                "created_at": u.created_at.strftime("%Y-%m-%d %H:%M:%S")
            } for u in uploads
        ],
        "total_records": total_records,
        "total_pages": total_pages,
        "current_page": page
    }

@router.get("/teachers", response_model=schemas.SuccessResponse[schemas.TeacherBasicResponse])
def get_teachers(db: Session = Depends(get_db), _ = Depends(require_permission("ver_horarios"))):
    try:
        data = service.get_teachers_list(db)
        return {"success": True, "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/classes", response_model=schemas.SuccessResponse[schemas.ClassGroupResponse])
def get_classes(db: Session = Depends(get_db), _ = Depends(require_permission("ver_horarios"))):
    try:
        data = service.get_classes_list(db)
        return {"success": True, "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/teacher/{teacher_id}", response_model=schemas.SuccessResponse[schemas.TeacherSessionResponse])
def get_teacher_schedule(teacher_id: UUID, start_date: str, end_date: str, db: Session = Depends(get_db), _ = Depends(require_permission("ver_horarios"))):
    try:
        data = service.get_teacher_schedule_grid(db, teacher_id, start_date, end_date)
        return {"success": True, "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/classroom/{class_id}", response_model=schemas.SuccessResponse[schemas.ClassroomSessionResponse])
def get_classroom_schedule(class_id: UUID, start_date: str, end_date: str, db: Session = Depends(get_db), _ = Depends(require_permission("ver_horarios"))):
    try:
        data = service.get_classroom_schedule_grid(db, class_id, start_date, end_date)
        return {"success": True, "data": data}
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
