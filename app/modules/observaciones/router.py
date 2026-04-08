from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from typing import Optional, List, Dict, Any
from . import schemas
from . import service
from app.dependencies.auth import require_permission

router = APIRouter(prefix="/api/schedule", tags=["Schedule Observations"])

@router.get("/observations", response_model=schemas.SuccessResponse[schemas.ObservationResponse])
def list_observations(
    teacher_id: Optional[int] = None, 
    start_date: Optional[str] = None, 
    end_date: Optional[str] = None, 
    db: Session = Depends(get_db),
    _ = Depends(require_permission("ver_observaciones"))
):
    try:
        data = service.get_observations_list(db, teacher_id, start_date, end_date)
        return {"success": True, "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/observations", response_model=schemas.SuccessResponse[schemas.ObservationResponse])
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
        
        return {"success": True, "data": resp}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/observations/{observation_id}", response_model=schemas.SuccessResponse[int])
def delete_observation(observation_id: int, db: Session = Depends(get_db), _ = Depends(require_permission("editar_observaciones"))):
    try:
        service.delete_observation_logic(db, observation_id)
        return {"success": True, "data": observation_id}
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
