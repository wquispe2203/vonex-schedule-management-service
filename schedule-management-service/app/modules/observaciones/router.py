from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from uuid import UUID
from app.core.database import get_db
from typing import Optional, List, Dict, Any
from . import schemas
from . import service
from app.dependencies.auth import require_permission
from app.core.schemas import StandardResponse, PaginatedResponseData

router = APIRouter(prefix="/api/schedule", tags=["Schedule Observations"])

@router.get("/observations", response_model=schemas.ObservationListStandardResponse)
def list_observations(
    teacher_id: Optional[UUID] = None, 
    start_date: Optional[str] = None, 
    end_date: Optional[str] = None, 
    db: Session = Depends(get_db),
    _ = Depends(require_permission("ver_observaciones"))
):
    try:
        data = service.get_observations_list(db, teacher_id, start_date, end_date)
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

@router.get("/observations/logs", response_model=schemas.ObservationLogListStandardResponse)
def list_observation_logs(db: Session = Depends(get_db), _ = Depends(require_permission("ver_observaciones"))):
    try:
        data = service.get_observation_logs_list(db)
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

@router.post("/observations", response_model=schemas.StandardResponse[schemas.ObservationResponse])
def create_observation(payload: schemas.ObservationPayload, db: Session = Depends(get_db), _ = Depends(require_permission("crear_observaciones"))):
    try:
        saved_obs = service.process_observation_creation(db, payload.model_dump(exclude_unset=True))
        
        resp = schemas.ObservationResponse(
            id=saved_obs.id,
            session_id=saved_obs.session_id,
            teacher_id=saved_obs.teacher_id,
            type=saved_obs.type,
            discount_type=saved_obs.discount_type,
            replacement_teacher_name=saved_obs.replacement_teacher_name,
            replacement_teacher_id=saved_obs.replacement_teacher_id,
            description=saved_obs.description or "",
            created_at=saved_obs.created_at.strftime("%Y-%m-%d %H:%M:%S") if saved_obs.created_at else ""
        )
        
        return {"success": True, "data": resp, "error": None}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/observations/batch", response_model=schemas.StandardResponse[int])
def create_observation_batch(payload: schemas.ObservationBatchPayload, db: Session = Depends(get_db), _ = Depends(require_permission("crear_observaciones"))):
    try:
        obs_list = [p.model_dump(exclude_unset=True) for p in payload.observations]
        affected = payload.affected_session_ids or []
        count = service.process_observation_batch(db, obs_list, affected)
        return {"success": True, "data": count, "error": None}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/observations/{observation_id}", response_model=schemas.StandardResponse[UUID])
def delete_observation(observation_id: UUID, db: Session = Depends(get_db), _ = Depends(require_permission("editar_observaciones"))):
    try:
        service.delete_observation_logic(db, observation_id)
        return {"success": True, "data": observation_id, "error": None}
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sessions-for-obs", response_model=StandardResponse[PaginatedResponseData[Dict[str, Any]]])
def list_sessions_for_obs(
    teacher_id: UUID,
    start_date: str,
    end_date: str,
    db: Session = Depends(get_db),
    _ = Depends(require_permission("ver_observaciones"))
):
    try:
        data = service.get_grouped_sessions_for_incidencias(db, teacher_id, start_date, end_date)
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
