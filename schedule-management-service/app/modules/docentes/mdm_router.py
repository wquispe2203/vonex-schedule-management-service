from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone, timedelta
from app.database import get_db
from app.dependencies.auth import require_permission
from . import schemas, repository
from app.models import Teacher, MatchReview, User
from app.core.transactions import with_retry_on_deadlock
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/mdm", tags=["MDM - Master Data Management"])

@router.get("/reviews", response_model=List[schemas.MatchReviewOut])
def get_pending_reviews(
    status: str = "PENDING", 
    db: Session = Depends(get_db),
    _ = Depends(require_permission("gestionar_docentes"))
):
    """Obtiene la lista de revisiones de matching pendientes/resueltas."""
    # Aplicar filtro global implícito para asegurar consistencia
    return repository.fetch_pending_reviews(db, status=status)

@router.post("/reviews/{review_id}/resolve")
@with_retry_on_deadlock(max_retries=3)
def resolve_match(
    review_id: UUID, 
    note: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("gestionar_docentes"))
):
    """
    Resolución Atómica e Idempotente (v4.2):
    - Reintentos automáticos ante Deadlocks.
    - Bloqueo FOR UPDATE sobre la revisión.
    - Validación Post-Merge exhaustiva.
    """
    with db.begin():
        # 1. Bloqueo Pesimista
        review = repository.fetch_review_by_id(db, review_id, for_update=True)
        if not review:
            raise HTTPException(status_code=404, detail="Revisión no encontrada")
        
        # 2. Idempotencia: Si ya está resuelto, devolver estado actual
        if review.status != "PENDING":
            return {"success": True, "message": f"La revisión ya fue procesada como {review.status}", "status": review.status, "mdm_version": "v4.2"}

        # 3. Datos del docente XML
        xml_teacher = review.xml_teacher
        if not xml_teacher:
            # Fallback legacy
            xml_teacher = db.query(Teacher).filter(Teacher.match_review_id == review_id).first()
            
        if not xml_teacher:
             raise HTTPException(status_code=404, detail="Docente XML originario no encontrado")

        try:
            start_time = review.created_at
            now = datetime.now(timezone.utc)
            
            # Fusión Segura MDM v4.2 (incluye validación interna)
            repository.merge_teachers_db(db, review.candidate_id, xml_teacher.id)
            
            # 4. Auditoría Extendida
            review.status = "RESOLVED"
            review.resolved_by = current_user.id
            review.resolved_by_snapshot = current_user.username
            review.resolved_at = now
            review.resolution_note = note
            review.resolution_type = "MANUAL_MATCH"
            if start_time:
                review.resolution_time_seconds = int((now - start_time).total_seconds())

            logger.info(json.dumps({
                "event": "mdm_resolution_success",
                "mdm_version": "v4.2",
                "review_id": str(review_id),
                "type": "RESOLVE",
                "resolved_by": current_user.username,
                "request_id": str(review.request_id or "n/a"),
                "timestamp": now.isoformat()
            }))
            
            return {"success": True, "message": "Match resuelto y docente unificado correctamente", "mdm_version": "v4.2"}
        except Exception as e:
            logger.error(f"MDM_ERROR: Error resolviendo {review_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error durante la resolución: {str(e)}")

@router.post("/reviews/{review_id}/reject")
@with_retry_on_deadlock(max_retries=3)
def reject_match(
    review_id: UUID, 
    note: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("gestionar_docentes"))
):
    """
    Rechazo Atómico e Idempotente.
    """
    with db.begin():
        review = repository.fetch_review_by_id(db, review_id, for_update=True)
        if not review:
            raise HTTPException(status_code=404, detail="Revisión no encontrada")
        
        if review.status != "PENDING":
            return {"success": True, "message": f"La revisión ya fue procesada como {review.status}", "status": review.status, "mdm_version": "v4.2"}

        now = datetime.now(timezone.utc)
        review.status = "REJECTED"
        review.resolved_by = current_user.id
        review.resolved_by_snapshot = current_user.username
        review.resolved_at = now
        review.resolution_note = note
        review.resolution_type = "MANUAL_REJECT"
        
        return {"success": True, "message": "Match rechazado", "mdm_version": "v4.2"}

@router.get("/stats", response_model=schemas.MdmStatsOut)
def get_mdm_stats(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    upload_id: Optional[UUID] = Query(None),
    db: Session = Depends(get_db),
    _ = Depends(require_permission("gestionar_docentes"))
):
    """
    Métricas de Calidad MDM (v4.2):
    - Ventana temporal o por lote XML específico.
    - Alerta si % Dudosos > 40% (Solo si total >= 30).
    """
    if not start_date:
        start_date = datetime.now(timezone.utc) - timedelta(days=30)
    if not end_date:
        end_date = datetime.now(timezone.utc)

    query = db.query(MatchReview)
    
    if upload_id:
        query = query.filter(MatchReview.upload_id == upload_id)
    else:
        query = query.filter(MatchReview.created_at.between(start_date, end_date))
    
    total = query.count()
    if total == 0:
        return {
            "total_reviews": 0, "pending": 0, "resolved": 0, "rejected": 0,
            "percentage_manual": 0, "percentage_dudosos": 0, "avg_resolution_time_minutes": 0,
            "alert_quality": False, "data_points": []
        }

    pending = query.filter(MatchReview.status == "PENDING").count()
    resolved = query.filter(MatchReview.status == "RESOLVED").count()
    rejected = query.filter(MatchReview.status == "REJECTED").count()
    
    percentage_dudosos = (pending / total) * 100 if total > 0 else 0
    
    # Alerta v4.2: Solo si Muestra es Significativa (>= 30)
    alert = (total >= 30 and percentage_dudosos > 40)

    from sqlalchemy import func
    avg_sec = db.query(func.avg(MatchReview.resolution_time_seconds)).filter(
        MatchReview.status == "RESOLVED",
        MatchReview.created_at.between(start_date, end_date)
    ).scalar() or 0

    return {
        "total_reviews": total,
        "pending": pending,
        "resolved": resolved,
        "rejected": rejected,
        "percentage_manual": ((resolved + rejected) / total * 100) if total > 0 else 0,
        "percentage_dudosos": percentage_dudosos,
        "avg_resolution_time_minutes": round(float(avg_sec) / 60.0, 2),
        "alert_quality": alert,
        "data_points": [] 
    }
