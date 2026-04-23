from sqlalchemy.orm import Session
from datetime import time
from uuid import UUID
from . import repository
from app.models import BreakConfig, LunchConfig
from typing import List, Dict, Any, Optional

def parse_time(t_str: str) -> time:
    try:
        if len(t_str) == 5: # HH:MM
            return time.fromisoformat(f"{t_str}:00")
        return time.fromisoformat(t_str)
    except ValueError:
        raise ValueError(f"Formato de hora inválido: {t_str}")

def get_active_gaps_rules(db: Session) -> List[Dict[str, Any]]:
    """Helper global para que otros módulos consuman reglas de receso/almuerzo sin N+1."""
    recesses = repository.fetch_all_recesses(db)
    lunches = repository.fetch_all_lunches(db)
    
    rules = []
    for r in recesses:
        rules.append({
            "type": "break",
            "description": r.description,
            "start_time": r.start_time,
            "end_time": r.end_time
        })
    for l in lunches:
        rules.append({
            "type": "lunch",
            "description": l.description,
            "start_time": l.start_time,
            "end_time": l.end_time
        })
    return rules

# --- Lógica de Recesos ---

def list_recesses(db: Session):
    return repository.fetch_all_recesses(db)

def create_recess(db: Session, description: Optional[str], start_str: str, end_str: str):
    start = parse_time(start_str)
    end = parse_time(end_str)
    if start >= end:
        raise ValueError("La hora de inicio debe ser menor a la hora de fin")
    
    config = BreakConfig(description=description, start_time=start, end_time=end)
    return repository.save_recess(db, config)

def update_recess(db: Session, recess_id: UUID, description: Optional[str], start_str: str, end_str: str):
    config = repository.fetch_recess_by_id(db, recess_id)
    if not config:
        raise ValueError("Receso no encontrado")
        
    start = parse_time(start_str)
    end = parse_time(end_str)
    if start >= end:
        raise ValueError("La hora de inicio debe ser menor a la hora de fin")
        
    config.description = description
    config.start_time = start
    config.end_time = end
    return repository.save_recess(db, config)

def delete_recess_logic(db: Session, recess_id: UUID):
    config = repository.fetch_recess_by_id(db, recess_id)
    if not config:
        raise ValueError("Receso no encontrado")
    repository.delete_recess(db, config)

# --- Lógica de Almuerzos ---

def list_lunches(db: Session):
    return repository.fetch_all_lunches(db)

def create_lunch(db: Session, description: Optional[str], start_str: str, end_str: str):
    start = parse_time(start_str)
    end = parse_time(end_str)
    if start >= end:
        raise ValueError("La hora de inicio debe ser menor a la hora de fin")
    
    config = LunchConfig(description=description, start_time=start, end_time=end)
    return repository.save_lunch(db, config)

def update_lunch(db: Session, lunch_id: UUID, description: Optional[str], start_str: str, end_str: str):
    config = repository.fetch_lunch_by_id(db, lunch_id)
    if not config:
        raise ValueError("Almuerzo no encontrado")
        
    start = parse_time(start_str)
    end = parse_time(end_str)
    if start >= end:
        raise ValueError("La hora de inicio debe ser menor a la hora de fin")
        
    config.description = description
    config.start_time = start
    config.end_time = end
    return repository.save_lunch(db, config)

def delete_lunch_logic(db: Session, lunch_id: UUID):
    config = repository.fetch_lunch_by_id(db, lunch_id)
    if not config:
        raise ValueError("Almuerzo no encontrado")
    repository.delete_lunch(db, config)
