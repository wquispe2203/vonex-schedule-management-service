from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.models import XmlUpload
from app.dependencies.auth import require_permission
from typing import Dict, Any

router = APIRouter(prefix="/api/system", tags=["System Monitoring"])

@router.get("/metrics", response_model=Dict[str, Any])
def get_system_metrics(
    db: Session = Depends(get_db), 
    _ = Depends(require_permission("ver_rpt"))
):
    """
    Retorna métricas críticas del pipeline de datos.
    """
    total_uploads = db.query(XmlUpload).count()
    
    # Métricas de calidad
    stats = db.query(
        func.sum(XmlUpload.total_records).label("total_rec"),
        func.sum(XmlUpload.fallback_count).label("total_fallback"),
        func.avg(XmlUpload.process_time_ms).label("avg_time")
    ).filter(XmlUpload.status.in_(['COMPLETED', 'DEGRADED'])).first()
    
    total_records = stats.total_rec or 0
    total_fallback = stats.total_fallback or 0
    avg_process_time = float(stats.avg_time or 0)
    
    fallback_rate = (total_fallback / total_records * 100) if total_records > 0 else 0
    
    errors_count = db.query(XmlUpload).filter(XmlUpload.status == 'FAILED').count()
    degraded_count = db.query(XmlUpload).filter(XmlUpload.status == 'DEGRADED').count()

    return {
        "success": True,
        "data": {
            "total_uploads": total_uploads,
            "total_records_processed": total_records,
            "fallback_rate": round(fallback_rate, 2),
            "avg_process_time_ms": round(avg_process_time, 2),
            "failed_uploads": errors_count,
            "degraded_uploads": degraded_count
        },
        "error": None
    }
