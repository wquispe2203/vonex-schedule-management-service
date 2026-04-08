from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from . import repository
from app.modules.observaciones import repository as obs_repo
import time as time_lib
import logging

logger = logging.getLogger(__name__)

def normalize_teacher_name(last: str, first: str) -> str:
    l = (last or "").strip().lower().replace(",", " ")
    f = (first or "").strip().lower().replace(",", " ")
    words = [w for w in (l + " " + f).split() if w]
    words.sort()
    return " ".join(words)

def _teacher_to_dict(t) -> Dict[str, Any]:
    return {
        "id": t.id,
        "source_id": t.source_id,
        "first_name": t.first_name or "",
        "last_name": t.last_name or "",
        "short_name": t.short_name or "",
        "dni": t.dni or "",
        "razon_social": t.razon_social or "",
        "normalized_name": t.normalized_name or "",
        "is_active": t.is_active
    }

def _sinasignar_to_dict(s) -> Dict[str, Any]:
    return {
        "id": s.id,
        "dni": s.dni or "",
        "apellidos": s.apellidos or "",
        "nombres": s.nombres or "",
        "razon_social": s.razon_social or "",
        "normalized_name": s.normalized_name or "",
        "created_at": s.created_at.strftime("%Y-%m-%d %H:%M:%S") if s.created_at else ""
    }

def get_all_docentes(db: Session):
    return [_teacher_to_dict(t) for t in repository.fetch_all_teachers(db)]

def update_docente(db: Session, tid: int, payload: Dict[str, Any]):
    obj = repository.fetch_teacher_by_id(db, tid)
    if not obj:
        raise ValueError("Docente no encontrado")
    
    repository.update_teacher(db, obj, payload)
    
    # Si cambiaron nombres, actualizar normalized_name
    if "first_name" in payload or "last_name" in payload:
        new_norm = normalize_teacher_name(obj.last_name, obj.first_name)
        repository.update_teacher(db, obj, {"normalized_name": new_norm})
    
    db.commit()
    return _teacher_to_dict(obj)

def register_single_teacher(db: Session, payload: Dict[str, Any]):
    norm = normalize_teacher_name(payload.get("last_name", ""), payload.get("first_name", ""))
    existing = repository.fetch_teacher_by_normalized(db, norm)
    if existing:
        raise ValueError(f"Ya existe un docente con el nombre '{norm}' (id={existing.id})")
    
    # Generar source_id si no viene
    if not payload.get("source_id"):
        payload["source_id"] = f"MANUAL_{int(time_lib.time())}"
    
    payload["normalized_name"] = norm
    new_obj = repository.create_teacher(db, payload)
    db.commit()
    return _teacher_to_dict(new_obj)

def reprocesar_historico(db: Session):
    # Lógica para normalizar todos los nombres en DB
    teachers = repository.fetch_all_teachers(db)
    count = 0
    for t in teachers:
        new_norm = normalize_teacher_name(t.last_name, t.first_name)
        if t.normalized_name != new_norm:
            repository.update_teacher(db, t, {"normalized_name": new_norm})
            count += 1
    db.commit()
    return {"success": True, "updated": count}

def get_sinasignar_paged(db: Session, page: int = 1, limit: int = 50):
    objs, total = repository.fetch_sinasignar_paged(db, page, limit)
    return {
        "success": True,
        "data": [_sinasignar_to_dict(s) for s in objs],
        "total": total,
        "page": page,
        "total_pages": (total + limit - 1) // limit
    }

def update_sinasignar(db: Session, sid: int, payload: Dict[str, Any]):
    obj = repository.fetch_sinasignar_by_id(db, sid)
    if not obj:
        raise ValueError("Registro no encontrado")
    
    nombres = payload.get("nombres", obj.nombres)
    apellidos = payload.get("apellidos", obj.apellidos)
    norm = normalize_teacher_name(apellidos, nombres)
    
    repository.update_sinasignar(db, obj, {
        "dni":             payload.get("dni", obj.dni),
        "apellidos":       apellidos,
        "nombres":         nombres,
        "razon_social":    (payload.get("razon_social") or "").strip() or None,
        "normalized_name": norm,
    })
    db.commit()
    return _sinasignar_to_dict(obj)

def promote_sinasignar(db: Session, sid: int) -> Dict[str, Any]:
    obj = repository.fetch_sinasignar_by_id(db, sid)
    if not obj:
        raise ValueError("Registro no encontrado en sinasignar")

    if not obj.apellidos or not obj.nombres:
        raise ValueError("Se requieren APELLIDOS y NOMBRES para promover")

    norm = normalize_teacher_name(obj.apellidos, obj.nombres)
    existing = repository.fetch_teacher_by_normalized(db, norm)
    if existing:
        repository.delete_sinasignar(db, obj)
        db.commit()
        return {"action": "merged", "message": f"Ya existía en maestra (id={existing.id}).", "teacher": _teacher_to_dict(existing)}

    new_teacher = repository.create_teacher(db, {
        "source_id":       f"PROMOTED_{int(time_lib.time())}",
        "first_name":      obj.nombres,
        "last_name":       obj.apellidos,
        "short_name":      "",
        "dni":             obj.dni,
        "razon_social":    obj.razon_social,
        "normalized_name": norm,
    })
    repository.delete_sinasignar(db, obj)
    
    # Sincronizar incidencias registradas solo con nombre
    synced = obs_repo.sync_teacher_id_by_name(db, new_teacher.id, norm)
    
    db.commit()
    msg = "Docente promovido exitosamente"
    if synced > 0:
        msg += f" ({synced} incidencias vinculadas automáticamente)"
        
    return {"action": "promoted", "message": msg, "teacher": _teacher_to_dict(new_teacher)}

def merge_teachers(db: Session, main_id: int, merge_id: int) -> Dict[str, Any]:
    if main_id == merge_id:
        raise ValueError("No se puede fusionar un docente con el mismo registro.")

    t_main = repository.fetch_teacher_by_id_full(db, main_id)
    t_merge = repository.fetch_teacher_by_id_full(db, merge_id)

    if not t_main or not t_merge:
        raise ValueError("Uno o ambos docentes no existen.")

    try:
        secondary_norm_copy = t_merge.normalized_name
        secondary_id_copy   = t_merge.id
        
        repository.merge_teachers_db(db, main_id, merge_id)

        new_norm = normalize_teacher_name(t_main.last_name or "", t_main.first_name or "")
        repository.update_teacher(db, t_main, {"normalized_name": new_norm})

        repository.cleanup_sinasignar_post_merge(db, secondary_id_copy, secondary_norm_copy)
        repository.cleanup_sinasignar_post_merge(db, main_id, new_norm)

        synced_sec = obs_repo.sync_teacher_id_by_name(db, main_id, secondary_norm_copy)
        
        db.commit()
        return {
            "success": True,
            "message": f"Fusión completada. {synced_sec} incidencias reconectadas.",
            "teacher": _teacher_to_dict(t_main)
        }
    except Exception as e:
        db.rollback()
        raise RuntimeError(f"Error crítico en la fusión: {str(e)}")
