from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, func
from app.models import Observation, ScheduleSession, Teacher
from typing import Optional, List, Dict, Any
import datetime
from fastapi.encoders import jsonable_encoder
from app.modules.auditoria.service import create_audit_log

def fetch_observations(db: Session, teacher_id: Any = None, start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Observation]:
    try:
        query = db.query(Observation).join(ScheduleSession)
        
        if teacher_id:
            query = query.filter(Observation.teacher_id == teacher_id)
        if start_date:
            query = query.filter(ScheduleSession.session_date >= start_date)
        if end_date:
            query = query.filter(ScheduleSession.session_date <= end_date)
            
        print(f"DEBUG-SQL-OBS: Fetching observations. Query: {str(query)}")
        return query.all()
    except Exception as e:
        raise RuntimeError(f"Error fetching observations: {str(e)}")

def fetch_observation_logs(db: Session) -> List[Observation]:
    try:
        query = db.query(Observation).options(
            joinedload(Observation.teacher),
            joinedload(Observation.user),
            joinedload(Observation.session)
        ).order_by(desc(Observation.created_at))
        print(f"DEBUG-SQL-LOGS: Fetching observation logs. Query: {str(query)}")
        return query.all()
    except Exception as e:
        raise RuntimeError(f"Error fetching observation logs: {str(e)}")

def fetch_teacher_by_normalized(db: Session, norm: str) -> Optional[Teacher]:
    try:
        return db.query(Teacher).filter(Teacher.normalized_name == norm).first()
    except Exception as e:
        raise RuntimeError(f"Error fetching teacher by normalized: {str(e)}")

def upsert_sinasignar_from_obs(db: Session, data: Dict[str, Any]) -> None:
    """Registra docente nuevo como no asignado o incrementa el contador si ya existe."""
    try:
        norm = data["normalized_name"]
        existing = db.query(Teacher).filter(
            Teacher.normalized_name == norm,
            Teacher.is_assigned == False
        ).first()
        
        if existing:
            existing.times_detected = (existing.times_detected or 0) + 1
            existing.last_seen_at = func.now()
        else:
            new_sa = Teacher(
                last_name=data["apellidos"],
                first_name=data["nombres"],
                normalized_name=norm,
                source="observacion",
                times_detected=1,
                is_assigned=False,
                last_seen_at=func.now()
            )
            db.add(new_sa)
        db.flush()
    except Exception as e:
        raise RuntimeError(f"Error upserting teacher (unassigned): {str(e)}")

def sync_teacher_id_by_name(db: Session, teacher_id: Any, normalized_name: str) -> int:
    """
    Busca observaciones con replacement_teacher_id nulo y las vincula al teacher_id real
    si coinciden en nombre normalizado (v3.6).
    """
    try:
        from app.modules.docentes.service import normalize_teacher_name
        # Solo auditar si hay match
        unlinked = db.query(Observation).filter(
            Observation.replacement_teacher_id == None,
            Observation.replacement_teacher_name != None
        ).all()
        
        updated_count = 0
        for obs in unlinked:
            # Parsear el nombre guardado en texto
            raw = obs.replacement_teacher_name
            if ',' in raw:
                parts = raw.split(',', 1)
                ln, fn = parts[0].strip(), parts[1].strip()
            else:
                parts = raw.split()
                ln = f"{parts[0]} {parts[1]}" if len(parts) >= 3 else parts[0]
                fn = " ".join(parts[2:]) if len(parts) >= 3 else (parts[1] if len(parts) > 1 else "")
            
            if normalize_teacher_name(ln, fn) == normalized_name:
                obs.replacement_teacher_id = teacher_id
                updated_count += 1
        
        db.flush()
        return updated_count
    except Exception as e:
        raise RuntimeError(f"Error syncing teacher observations: {str(e)}")

def fetch_observation_by_session_type(db: Session, session_id: Any, obs_type: str, start_time: Optional[datetime.time] = None) -> Optional[Observation]:
    try:
        query = db.query(Observation).filter(
            Observation.session_id == session_id,
            Observation.type == obs_type
        )
        if start_time:
            query = query.filter(Observation.start_time == start_time)
        return query.first()
    except Exception as e:
        raise RuntimeError(f"Error fetching observation by session: {str(e)}")

def save_observation(db: Session, is_new: bool, obs: Observation) -> Observation:
    """Consolida Inserts y Updates resolviendo COMMIT estricto, anexando Auditoría Post-Commit."""
    try:
        if is_new:
            db.add(obs)
            accion_audit = "CREATE"
        else:
            accion_audit = "UPDATE"
            
        db.commit()
        db.refresh(obs)
        
        # Auditoria Integrada
        print("🔥 AUDITORIA OBSERVACIONES EJECUTADA")
        try:
            obs_dict = {c.name: getattr(obs, c.name) for c in obs.__table__.columns}
            json_despues = jsonable_encoder(obs_dict)
        except Exception as se:
            print(f"DEBUG-OBSERVACIONES: Error de serialización = {str(se)}")
            json_despues = {"error": "Fallo serialización"}

        create_audit_log(
            db=db, 
            accion=accion_audit, 
            modulo="observaciones", 
            registro_id=obs.id, 
            datos_antes=None, 
            datos_despues=json_despues,
            usuario_id=1
        )
        return obs
    except Exception as e:
        db.rollback()
        raise RuntimeError(f"Database error saving observation: {str(e)}")

def update_observation(db: Session, obs: Observation) -> Observation:
    """Wrapper explícito para UPDATES según requerimiento de auditoría."""
    return save_observation(db, is_new=False, obs=obs)

def delete_observation(db: Session, obs_id: Any) -> bool:
    try:
        obs = db.query(Observation).filter(Observation.id == obs_id).first()
        if not obs:
            return False
            
        try:
            obs_dict = {c.name: getattr(obs, c.name) for c in obs.__table__.columns}
            json_antes = jsonable_encoder(obs_dict)
        except Exception as se:
            print(f"DEBUG-OBSERVACIONES: Error de serialización en Objeto DELETE = {str(se)}")
            json_antes = {"error": "Fallo serialización"}

        db.delete(obs)
        db.commit()
        
        # Auditoria Integrada
        print("🔥 AUDITORIA OBSERVACIONES EJECUTADA")
        create_audit_log(
            db=db, 
            accion="DELETE", 
            modulo="observaciones", 
            registro_id=obs_id, 
            datos_antes=json_antes, 
            datos_despues=None,
            usuario_id=1
        )
        return True
    except Exception as e:
        db.rollback()
        raise RuntimeError(f"Database error deleting observation: {str(e)}")
