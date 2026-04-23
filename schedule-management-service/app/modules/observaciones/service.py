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


def safe_int(val, name):
    if val is None or str(val).lower() in ['nan', 'null', 'undefined', '']:
        return None
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return None

def process_observation_creation(db: Session, payload: Dict[str, Any]) -> Observation:
    """Núcleo de lógicas compartidas para crear/actualizar observaciones."""
    print("DEBUG-POST-START: Payload recibido:", payload)
    
    s_id = payload.get("session_id")
    
    # Resolvores Universales (Fase 2)
    teacher_obj = resolve_teacher(db, payload.get("teacher_id"))
    t_id = teacher_obj.id if teacher_obj else None
    t_uid = teacher_obj.uid if teacher_obj else None

    # El reemplazo es opcional
    repl_id_raw = payload.get("replacement_teacher_id")
    replacement_obj = resolve_teacher(db, repl_id_raw) if repl_id_raw else None
    r_id = replacement_obj.id if replacement_obj else None
    r_uid = replacement_obj.uid if replacement_obj else None

    u_id = payload.get("user_id") or 1

    if s_id is None:
        raise ValueError("ID de sesión inválido o faltante.")

    obs_type = payload.get("type", "FALTA")
    discount_type = payload.get("discount_type", "SIMPLE")
    replacement_name = payload.get("replacement_teacher_name")
    r_last_name = payload.get("replacement_last_name")
    r_first_name = payload.get("replacement_first_name")
    description = payload.get("description", "")

    # --- LÓGICA DE REEMPLAZO Y DOCENTES NUEVOS (v3.10) ---
    if obs_type == 'REEMPLAZO':
        # Priorizar campos separados (v3.10)
        if r_last_name or r_first_name:
            ln = (r_last_name or "").strip().upper()
            fn = (r_first_name or "").strip().upper()
        elif replacement_name:
            # Fallback legacy (parseo de coma)
            raw_name = replacement_name.strip().upper()
            if ',' in raw_name:
                parts = raw_name.split(',', 1)
                ln, fn = parts[0].strip(), parts[1].strip()
            else:
                parts = raw_name.split()
                if len(parts) >= 2:
                    ln = f"{parts[0]} {parts[1]}" if len(parts) >= 3 else parts[0]
                    fn = " ".join(parts[2:]) if len(parts) >= 3 else parts[1]
                else:
                    ln, fn = raw_name, ""
        else:
            ln, fn = "", ""
        
        if ln or fn:
            formatted_full_name = f"{ln}, {fn}"
            norm = normalize_teacher_name(ln, fn)

            # B) Validación en Maestra (por normalized_name)
            existing_t = repository.fetch_teacher_by_normalized(db, norm)
            
            if existing_t:
                r_id = existing_t.id
                replacement_name = formatted_full_name
                print(f"DEBUG-POST: Docente encontrado en Maestra: {norm} (ID={r_id})")
            else:
                repository.upsert_sinasignar_from_obs(db, {
                    "apellidos": ln,
                    "nombres": fn,
                    "normalized_name": norm
                })
                r_id = None
                replacement_name = formatted_full_name
                print(f"DEBUG-POST: Docente nuevo registrado en SinAsignar: {norm}")
    
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

    # Avoid duplicate matches
    existing = repository.fetch_observation_by_session_type(db, s_id, obs_type, start_t_obj)
    
    if existing:
        print(f"DEBUG-POST-UPDATE: Existing ID={existing.id}")
        existing.teacher_id = t_id
        existing.teacher_uid = t_uid # Sincronizado Fase 2
        existing.discount_type = discount_type
        existing.replacement_teacher_name = replacement_name
        existing.replacement_teacher_id = r_id
        existing.replacement_teacher_uid = r_uid # Sincronizado Fase 2
        existing.description = description
        existing.start_time = start_t_obj
        existing.end_time = end_t_obj
        existing.user_id = u_id
        is_new = False
        target_obs = existing
    else:
        print("DEBUG-POST-NEW: Creating new observation")
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
            start_time=start_t_obj,
            end_time=end_t_obj,
            user_id=u_id
        )
        is_new = True
        target_obs = new_obs

    if is_new:
        saved_obs = repository.save_observation(db, True, target_obs)
    else:
        saved_obs = repository.update_observation(db, target_obs)
        
    print("DEBUG-POST-SUCCESS: Commited.")
    return saved_obs

def get_observations_list(db: Session, teacher_id: Optional[UUID] = None, start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Dict[str, Any]]:
    actual_tid = None
    if teacher_id:
        teacher = resolve_teacher(db, teacher_id)
        actual_tid = teacher.id if teacher else None

    obs_list = repository.fetch_observations(db, actual_tid, start_date, end_date)
    return [
        {
            "id": o.id,
            "uid": str(o.uid),
            "session_id": o.session_id,
            "teacher_id": o.teacher_id,
            "teacher_uid": str(o.teacher_uid) if o.teacher_uid else None,
            "type": o.type,
            "discount_type": o.discount_type,
            "replacement_teacher_name": o.replacement_teacher_name,
            "replacement_teacher_id": o.replacement_teacher_id,
            "replacement_teacher_uid": str(o.replacement_teacher_uid) if o.replacement_teacher_uid else None,
            "description": o.description,
            "created_at": o.created_at.strftime("%Y-%m-%d %H:%M:%S")
        } for o in obs_list
    ]

def get_observation_logs_list(db: Session) -> List[Dict[str, Any]]:
    logs = repository.fetch_observation_logs(db)
    return [
        {
            "id": l.id,
            "date_record": l.created_at.strftime("%Y-%m-%d %H:%M:%S") if l.created_at else "---",
            "user": l.user.username if l.user else "SISTEMA",
            "teacher_affected": f"{l.teacher.first_name} {l.teacher.last_name}" if l.teacher else "N/A",
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
    
    # 2. Obtener sesiones brutas usando ID legacy interno
    sessions = horarios_repo.fetch_teacher_combined_sessions(db, actual_id, start_date, end_date, teacher_full_name)
    if not sessions:
        return []

    # 3. Ordenar por fecha y hora
    sessions.sort(key=lambda x: (x.session_date, x.start_time))

    grouped = []
    
    for s in sessions:
        # LIMPIEZA DE NOMBRE DEL CURSO (BUG 2)
        subject_name = s.lesson.subject.name if s.lesson and s.lesson.subject else "---"
        clean_subject = re.sub(r'\(.*?\)', '', subject_name).strip()
        
        class_group = s.lesson.class_group.name if s.lesson and s.lesson.class_group else "---"
        session_date_str = s.session_date.strftime("%Y-%m-%d")
        start_t_str = s.start_time.strftime("%H:%M:%S")
        end_t_str = s.end_time.strftime("%H:%M:%S")

        # Intentar fusionar con el último bloque (BUG 1)
        can_merge = False
        if grouped:
            last = grouped[-1]
            if (last["date"] == session_date_str and
                last["subject_raw"] == subject_name and
                last["class_group"] == class_group and
                last["end_time"] == start_t_str):
                can_merge = True

        if can_merge:
            grouped[-1]["end_time"] = end_t_str
            grouped[-1]["session_ids"].append(s.id)
            for o in s.observations:
                obs_map = {
                    "id": o.id,
                    "session_id": o.session_id,
                    "type": o.type,
                    "start_time": o.start_time.strftime("%H:%M") if o.start_time else None,
                    "end_time": o.end_time.strftime("%H:%M") if o.end_time else None
                }
                if obs_map not in grouped[-1]["observations"]:
                    grouped[-1]["observations"].append(obs_map)
        else:
            # ✅ BUG CRÍTICO CORREGIDO: Faltaba este grouped.append()
            obs_data = []
            for o in s.observations:
                obs_data.append({
                    "id": o.id,
                    "session_id": o.session_id,
                    "type": o.type,
                    "start_time": o.start_time.strftime("%H:%M") if o.start_time else None,
                    "end_time": o.end_time.strftime("%H:%M") if o.end_time else None
                })
            grouped.append({
                "id": s.id,
                "session_ids": [s.id],
                "date": session_date_str,
                "subject": clean_subject,
                "subject_raw": subject_name,
                "class_group": class_group,
                "start_time": start_t_str,
                "end_time": end_t_str,
                "observations": obs_data,
                "badge": "INGRESAR"  # Se sobreescribe abajo
            })

    # 4. Post-procesar etiquetas (Badges) para cada bloque agrupado
    for g in grouped:
        badge = "INGRESAR"
        if g["observations"]:
            types = set(o["type"] for o in g["observations"])
            if len(types) == 1:
                badge = list(types)[0]
            else:
                badge = "FALTA/REEMP"
        g["badge"] = badge

    return grouped
