import time
import datetime
import re
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Dict, Any, List, Optional
from . import repository
from app.models import Teacher, Observation
from app.modules.horarios import repository as horarios_repo
from app.modules.docentes.service import normalize_teacher_name, resolve_teacher
from app.services.session_consolidator import consolidate_sessions


def safe_int(val, name):
    if val is None or str(val).lower() in ['nan', 'null', 'undefined', '']:
        return None
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return None

def process_observation_creation(db: Session, payload: Dict[str, Any], auto_commit: bool = True) -> Observation:
    """Núcleo de lógicas compartidas para crear/actualizar observaciones."""
    print("DEBUG-POST-START: Payload recibido:", payload)
    
    s_id = payload.get("session_id")
    
    # Resolvores Universales (Fase 2)
    teacher_obj = resolve_teacher(db, payload.get("teacher_id"))
    t_id = teacher_obj.id if teacher_obj else None
    t_uid = teacher_obj.id if teacher_obj else None # Synchronize correctly with UUID Primary Key

    # El reemplazo es opcional
    repl_id_raw = payload.get("replacement_teacher_id")
    replacement_obj = resolve_teacher(db, repl_id_raw) if repl_id_raw else None
    r_id = replacement_obj.id if replacement_obj else None
    r_uid = replacement_obj.id if replacement_obj else None # Synchronize correctly with UUID Primary Key

    u_id = payload.get("user_id")

    if s_id is None:
        raise ValueError("ID de sesión inválido o faltante.")

    obs_type = payload.get("type", "FALTA")
    discount_type = payload.get("discount_type", "SIMPLE")
    description = payload.get("description", "")
    is_external = payload.get("replacement_is_external", False)

    # --- HARDENED REPLACEMENT VALIDATION (STRUCTURAL RESTORATION) ---
    if obs_type == 'REEMPLAZO':
        if is_external:
            print(f"[OBS EXTERNAL TEACHER] External replacement declared for session {s_id}. Invalidating master references.")
            # For external teachers, ensure no reference to internal master data
            r_id = None
            r_uid = None
            
            # Use the provided external name or default
            ext_name = payload.get("replacement_teacher_name")
            replacement_name = ext_name.upper() if ext_name else "DOCENTE EXTERNO"
            
            # Strong enforcement: Require an external name or description
            if not ext_name and (not description or len(description.strip()) < 5):
                print("[OBS REPLACEMENT REJECTED] External teacher declared without name or specifying context in observation.")
                raise ValueError("Debe ingresar los Apellidos y Nombres del docente externo o proporcionar una descripción detallada.")
        else:
            # Validated internal teacher REQUIRED
            if not r_id and not r_uid:
                print("[OBS REPLACEMENT REJECTED] Internal replacement requested but no validated teacher selected.")
                raise ValueError("Debe seleccionar un docente de reemplazo válido de la maestra.")
            
            # Fetch the final confirmation
            v_teacher = resolve_teacher(db, r_id or r_uid)
            if not v_teacher:
                 print(f"[OBS REPLACEMENT REJECTED] Indicated replacement ID={r_id} does not resolve in validation database.")
                 raise ValueError("El docente de reemplazo seleccionado no es válido.")
            
            # Force naming sync
            replacement_name = f"{v_teacher.last_name}, {v_teacher.first_name}".upper()
            print(f"[OBS REPLACEMENT VALIDATED] Successfully tethered replacement ID={v_teacher.id} to session flow.")
    else:
        # Not a replacement, enforce empty replacement data
        r_id = None
        r_uid = None
        replacement_name = None
    
    start_t = payload.get("start_time")
    end_t = payload.get("end_time")

    print(f"DEBUG-POST-PARSED: sid={s_id}, tid={t_id}, rid={r_id}, uid={u_id}")

    start_t_obj = None
    end_t_obj = None
    try:
        if isinstance(start_t, str) and len(start_t) >= 5:
            start_t_obj = datetime.datetime.strptime(start_t[:5], "%H:%M").time()
        if isinstance(end_t, str) and len(end_t) >= 5:
            end_t_obj = datetime.datetime.strptime(end_t[:5], "%H:%M").time()
    except Exception as te:
        print("DEBUG-POST-TIME-ERROR:", str(te))

    # Real persistent logic using DB time slots
    existing = repository.fetch_observation_by_slot(db, s_id, obs_type, start_t_obj)
    
    if existing:
        print(f"DEBUG-POST-UPDATE: Existing ID={existing.id}")
        existing.teacher_id = t_id
        existing.teacher_uid = t_uid # Sincronizado Fase 2
        existing.discount_type = discount_type
        existing.replacement_teacher_name = replacement_name
        existing.replacement_teacher_id = r_id
        existing.replacement_teacher_uid = r_uid # Sincronizado Fase 2
        existing.description = description
        existing.user_id = u_id
        existing.start_time = start_t_obj
        existing.end_time = end_t_obj
        existing.type = obs_type # RECOVERY FIX: Force type persistence if overwriting existing record
        is_new = False
        target_obs = existing
    else:
        print("DEBUG-POST-NEW: Creating new observation with physical timestamps")
        new_obs = Observation(
            session_id=s_id,
            teacher_id=t_id,
            teacher_uid=t_uid, # Sincronizado Fase 2
            type=obs_type,
            discount_type=discount_type,
            replacement_teacher_name=replacement_name,
            replacement_teacher_id=r_id,
            replacement_teacher_uid=r_uid, # Sincronizado Fase 2
            description=description,
            user_id=u_id,
            start_time=start_t_obj,
            end_time=end_t_obj
        )
        is_new = True
        target_obs = new_obs

    print(f"[OBS OBSERVATION REGISTER] Persisting event: type={obs_type} teacher={t_id} session={s_id}")
    if is_new:
        saved_obs = repository.save_observation(db, True, target_obs, auto_commit=auto_commit)
    else:
        saved_obs = repository.update_observation(db, target_obs, auto_commit=auto_commit)
        
    print("DEBUG-POST-SUCCESS: Commited.")
    return saved_obs

def process_observation_batch(db: Session, payloads: List[Dict[str, Any]], affected_session_ids: List[Any] = []) -> int:
    """Procesa una lista de observaciones de forma transaccional, limpiando estados previos."""
    try:
        print(f"[OBS BATCH START] Processing {len(payloads)} payloads across {len(affected_session_ids)} affected sessions.")
        
        # 1. ELIMINACIÓN SEGURA DE ESTADOS PREVIOS PARA SESIONES AFECTADAS
        # Esto garantiza la "Conservación Matemática" y la limpieza de "ghost overlaps".
        from app.models import Observation
        
        # Si el usuario no envió affected_session_ids pero hay payloads, inferirlos
        session_universe = set(affected_session_ids)
        for p in payloads:
            if p.get("session_id"):
                session_universe.add(p.get("session_id"))
                
        for s_id in session_universe:
            # Obtener todas las observaciones de esta sesión para auditar y borrar limpiamente
            existing_obs = db.query(Observation).filter(Observation.session_id == s_id).all()
            if existing_obs:
                print(f"[OBS BATCH CLEAR] Cleaning {len(existing_obs)} existing observations for Session ID={s_id}")
                for obs in existing_obs:
                    repository.delete_observation(db, obs.id, auto_commit=False) # Hardened: defer commit to ensure atomic recovery
        
        # La auditoria interna genera flushes, mantenemos el lote suspendido hasta el fin.
        
        # 2. INSERCIÓN DE LAS NUEVAS OBSERVACIONES
        count = 0
        for payload in payloads:
            # Ignorar placeholders NINGUNA si llegan aquí
            if payload.get("type") == 'NINGUNA':
                continue
            
            process_observation_creation(db, payload, auto_commit=False)
            count += 1
            
        db.commit()
        print(f"[OBS BATCH SUCCESS] Atomically persisted {count} new observation nodes.")
        return count
        
    except Exception as e:
        db.rollback()
        print(f"[OBS BATCH ERROR] {str(e)}")
        raise e

def get_observations_list(db: Session, teacher_id: Optional[UUID] = None, start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Dict[str, Any]]:
    actual_tid = None
    if teacher_id:
        teacher = resolve_teacher(db, teacher_id)
        actual_tid = teacher.id if teacher else None

    obs_list = repository.fetch_observations(db, actual_tid, start_date, end_date)
    return [
        {
            "id": o.id,
            "uid": str(o.id),
            "session_id": o.session_id,
            "teacher_id": o.teacher_id,
            "teacher_uid": str(o.teacher_uid) if o.teacher_uid else None,
            "type": o.type,
            "discount_type": o.discount_type,
            "replacement_teacher_name": o.replacement_teacher_name,
            "replacement_teacher_id": o.replacement_teacher_id,
            "replacement_teacher_uid": str(o.replacement_teacher_uid) if o.replacement_teacher_uid else None,
            "description": o.description,
            "start_time": o.start_time.strftime("%H:%M:%S") if o.start_time else None,
            "end_time": o.end_time.strftime("%H:%M:%S") if o.end_time else None,
            "created_at": o.created_at.strftime("%Y-%m-%d %H:%M:%S")
        } for o in obs_list
    ]

def get_observation_logs_list(db: Session) -> List[Dict[str, Any]]:
    print("[OBS AUDIT FETCH] Querying global observation dataset for unified audit reconstruction.")
    logs = repository.fetch_observation_logs(db)
    return [
        {
            "id": l.id,
            "date_record": l.created_at.strftime("%Y-%m-%d %H:%M:%S") if l.created_at else "---",
            "user": l.user.username if l.user else "SISTEMA",
            "teacher_affected": f"{l.teacher.last_name}, {l.teacher.first_name}" if l.teacher else "N/A",
            "type": l.type,
            "replacement_teacher_name": l.replacement_teacher_name,
            "class_date": l.session.session_date.strftime("%Y-%m-%d") if (l.session and l.session.session_date) else "N/A",
            "description": l.description
        } for l in logs
    ]

def delete_observation_logic(db: Session, obs_id: UUID) -> bool:
    success = repository.delete_observation(db, obs_id)
    if not success:
        raise ValueError("Incidencia no encontrada")
    return True



def get_grouped_sessions_for_incidencias(db: Session, teacher_id: UUID, start_date: str, end_date: str) -> List[Dict[str, Any]]:
    # 1. Resolución Universal del Docente
    teacher = resolve_teacher(db, teacher_id)
    if not teacher:
        return []
        
    actual_id = teacher.id
    teacher_full_name = f"{teacher.first_name} {teacher.last_name}"
    
    # B. Logs estructurales obligatorios (v3.0 audit)
    active_uploads = horarios_repo._get_completed_upload_ids(db, start_date, end_date)
    print(f"[OBS ACTIVE XML] Looking for scheduled sessions. Active uploads found: {len(active_uploads)}")
    
    # 2. Obtener sesiones brutas usando ID legacy interno
    sessions = horarios_repo.fetch_teacher_combined_sessions(db, actual_id, start_date, end_date, teacher_full_name)
    if not sessions:
        return []

    # 3. Convertir a dicts para el consolidator unificado
    session_dicts = []
    for s in sessions:
        subject_name = s.lesson.subject.name if s.lesson and s.lesson.subject else "---"
        clean_subject = re.sub(r'\(.*?\)', '', subject_name).strip()
        class_group = s.lesson.class_group.name if s.lesson and s.lesson.class_group else "---"
        
        obs_data = []
        for o in s.observations:
            obs_data.append({
                "id": o.id,
                "session_id": o.session_id,
                "type": o.type,
                "start_time": o.start_time.strftime("%H:%M:%S") if o.start_time else None,
                "end_time": o.end_time.strftime("%H:%M:%S") if o.end_time else None
            })

        session_dicts.append({
            "id": s.id,
            "session_ids": [s.id],
            "date": s.session_date,
            "start_time": s.start_time,
            "end_time": s.end_time,
            "subject": clean_subject,
            "subject_raw": subject_name,
            "class_group": class_group,
            "observations": obs_data,
            "horas_dictadas": 1.0,  # Peso base
            "docente": teacher_full_name  # Requerido por log de consolidator
        })

    # 4. Ejecutar consolidación académica unificada (REUSO RPT)
    consolidated = consolidate_sessions(
        session_dicts,
        date_key="date",
        start_time_key="start_time",
        end_time_key="end_time",
        hours_key="horas_dictadas",
        group_fields=["subject", "class_group"], # Mantenemos los bloques agrupados por curso/aula
        module_tag="OBS"
    )

    # 5. Dar formato final y calcular Badges
    result = []
    for c in consolidated:
        # Calcular Badge unificado
        badge = "INGRESAR"
        obs_list = c.get("observations", [])
        if obs_list:
            types = set(o["type"] for o in obs_list)
            if len(types) == 1:
                badge = list(types)[0]
            else:
                badge = "FALTA/REEMP"

        # Asegurar compatibilidad JSON
        s_ids = []
        # Recoger session_ids acumulados por el consolidator
        # En session_consolidator.py no acumulamos 'session_ids' explícitamente en la estructura original, 
        # pero sí 'observations' que tienen el session_id real!
        
        # Sin embargo, para robustez, reconstruimos los IDs de las observaciones o del bloque actual.
        block_session_ids = list(set(o["session_id"] for o in obs_list))
        if not block_session_ids and c.get("id"):
            block_session_ids = [c["id"]]

        result.append({
            "id": c.get("id"),
            "session_ids": block_session_ids,
            "date": c["date"].strftime("%Y-%m-%d") if isinstance(c["date"], (datetime.date, datetime.datetime)) else str(c["date"]),
            "subject": c["subject"],
            "subject_raw": c["subject_raw"],
            "class_group": c["class_group"],
            "start_time": c["start_time"].strftime("%H:%M:%S") if isinstance(c["start_time"], datetime.time) else str(c["start_time"]),
            "end_time": c["end_time"].strftime("%H:%M:%S") if isinstance(c["end_time"], datetime.time) else str(c["end_time"]),
            "observations": obs_list,
            "badge": badge
        })

    return result
