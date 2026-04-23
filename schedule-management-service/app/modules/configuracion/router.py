from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from app.database import get_db
from app.dependencies.auth import require_permission
from . import schemas
from . import service

router = APIRouter(
    prefix="/api/config", 
    tags=["Configuration"],
    dependencies=[Depends(require_permission("gestionar_configuracion"))]
)

# --- Recesos ---

@router.get("/recesos", response_model=schemas.SuccessResponse[schemas.ConfigResponse])
def get_recesses(db: Session = Depends(get_db)):
    try:
        data = service.list_recesses(db)
        return {"success": True, "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/recesos", response_model=schemas.SuccessResponse[schemas.ConfigResponse])
def create_recess(payload: schemas.ConfigSchema, db: Session = Depends(get_db)):
    try:
        new_config = service.create_recess(db, payload.description, payload.start_time, payload.end_time)
        return {"success": True, "data": new_config}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/recesos/{id}", response_model=schemas.SuccessResponse[schemas.ConfigResponse])
def update_recess(id: UUID, payload: schemas.ConfigSchema, db: Session = Depends(get_db)):
    try:
        updated = service.update_recess(db, id, payload.description, payload.start_time, payload.end_time)
        return {"success": True, "data": updated}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/recesos/{id}")
def delete_recess(id: UUID, db: Session = Depends(get_db)):
    try:
        service.delete_recess_logic(db, id)
        return {"success": True, "message": "Receso eliminado"}
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Almuerzos ---

@router.get("/almuerzos", response_model=schemas.SuccessResponse[schemas.ConfigResponse])
def get_lunches(db: Session = Depends(get_db)):
    try:
        data = service.list_lunches(db)
        return {"success": True, "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/almuerzos", response_model=schemas.SuccessResponse[schemas.ConfigResponse])
def create_lunch(payload: schemas.ConfigSchema, db: Session = Depends(get_db)):
    try:
        new_config = service.create_lunch(db, payload.description, payload.start_time, payload.end_time)
        return {"success": True, "data": new_config}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/almuerzos/{id}", response_model=schemas.SuccessResponse[schemas.ConfigResponse])
def update_lunch(id: UUID, payload: schemas.ConfigSchema, db: Session = Depends(get_db)):
    try:
        updated = service.update_lunch(db, id, payload.description, payload.start_time, payload.end_time)
        return {"success": True, "data": updated}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/almuerzos/{id}")
def delete_lunch(id: UUID, db: Session = Depends(get_db)):
    try:
        service.delete_lunch_logic(db, id)
        return {"success": True, "message": "Almuerzo eliminado"}
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
