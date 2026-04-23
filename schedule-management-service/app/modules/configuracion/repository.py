from sqlalchemy.orm import Session
from sqlalchemy import asc
from uuid import UUID
from app.models import BreakConfig, LunchConfig
from typing import List, Optional

# --- BreakConfig (Recesos) ---
def fetch_all_recesses(db: Session) -> List[BreakConfig]:
    return db.query(BreakConfig).order_by(asc(BreakConfig.start_time)).all()

def fetch_recess_by_id(db: Session, recess_id: UUID) -> Optional[BreakConfig]:
    return db.query(BreakConfig).filter(BreakConfig.id == recess_id).first()

def save_recess(db: Session, config: BreakConfig) -> BreakConfig:
    db.add(config)
    db.commit()
    db.refresh(config)
    return config

def delete_recess(db: Session, config: BreakConfig):
    db.delete(config)
    db.commit()

# --- LunchConfig (Almuerzos) ---
def fetch_all_lunches(db: Session) -> List[LunchConfig]:
    return db.query(LunchConfig).order_by(asc(LunchConfig.start_time)).all()

def fetch_lunch_by_id(db: Session, lunch_id: UUID) -> Optional[LunchConfig]:
    return db.query(LunchConfig).filter(LunchConfig.id == lunch_id).first()

def save_lunch(db: Session, config: LunchConfig) -> LunchConfig:
    db.add(config)
    db.commit()
    db.refresh(config)
    return config

def delete_lunch(db: Session, config: LunchConfig):
    db.delete(config)
    db.commit()
