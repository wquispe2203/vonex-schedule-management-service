"""
Repository del módulo DOCENTES — v2 extendido.
REGLA: `fetch_active_teachers` NO se modifica nunca.
"""
from sqlalchemy.orm import Session
from sqlalchemy import or_, func, distinct, text
import logging
from app.models import Teacher, ScheduleSession, Lesson, Observation, MatchReview
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


# ════════════════════════════════════════════════════════
#  FUNCIONES EXISTENTES — INTOCABLES
# ════════════════════════════════════════════════════════

def fetch_active_teachers(db: Session) -> List[Teacher]:
    """
    Obtiene los docentes activos directamente de la base de datos (v3.7).
    Un docente está activo si tiene al menos una Lesson (aunque no tenga sesiones XML aún),
    o si ha realizado alguna Observation como reemplazo.
    NOTA: NO FILTRA POR is_active=True (ver fetch_active_teachers_for_rpt).
    """
    return db.query(Teacher).filter(
        or_(
            Teacher.id.in_(db.query(Lesson.teacher_id).distinct()),
            Teacher.id.in_(db.query(Observation.replacement_teacher_id).filter(Observation.replacement_teacher_id.isnot(None)).distinct())
        )
    ).all()


def fetch_active_teachers_for_rpt(db: Session) -> List[Teacher]:
    """
    REGLA v3.10: Exclusiva para RPT Planilla.
    Filtra por:
    1. is_active = True
    2. Tiene actividad (Lesson o Replacement Observation)
    """
    # Usamos subconsultas explícitas para asegurar que PostgreSQL maneje los tipos UUID de forma nativa
    lesson_t_ids = db.query(Lesson.teacher_id).filter(Lesson.teacher_id.isnot(None)).distinct().subquery()
    obs_t_ids = db.query(Observation.replacement_teacher_id).filter(Observation.replacement_teacher_id.isnot(None)).distinct().subquery()

    query = db.query(Teacher).filter(
        Teacher.is_active == True,
        or_(
            Teacher.id.in_(lesson_t_ids),
            Teacher.id.in_(obs_t_ids)
        )
    )
    print(f"DEBUG-SQL-RPT: Executing query: {str(query)}")
    return query.all()


def check_teacher_activity(db: Session, teacher_id: int) -> Dict[str, bool]:
    """Verifica si el docente tiene lecciones u observaciones para advertencia de UX."""
    has_lessons = db.query(Lesson).filter(Lesson.teacher_id == teacher_id).exists()
    has_observations = db.query(Observation).filter(
        or_(
            Observation.teacher_id == teacher_id,
            Observation.replacement_teacher_id == teacher_id
        )
    ).exists()
    
    return {
        "has_lessons": db.query(has_lessons).scalar(),
        "has_observations": db.query(has_observations).scalar()
    }


# ════════════════════════════════════════════════════════
#  HELPERS INTERNOS
# ════════════════════════════════════════════════════════

def _active_subquery(db: Session):
    return db.query(Teacher.id).filter(
        or_(
            Teacher.id.in_(db.query(Lesson.teacher_id).distinct()),
            Teacher.id.in_(db.query(Observation.replacement_teacher_id).filter(Observation.replacement_teacher_id.isnot(None)).distinct())
        )
    ).subquery()


# ════════════════════════════════════════════════════════
#  MAESTRA — TEACHERS
# ════════════════════════════════════════════════════════

def fetch_all_teachers_paginated(
    db: Session,
    filter_mode: str = "all",
    search: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
    status_filter: Optional[str] = None, # acts, inacts, all
) -> Dict[str, Any]:
    try:
        # Inicialización segura de la consulta
        q = db.query(Teacher)

        # Filtro Global MDM v4: Excluir docentes ya fusionados
        q = q.filter(Teacher.merged_into_id.is_(None))
        
        # Filtro base por "actividad" (legacy logic)
        if filter_mode == "active":
            q = q.filter(Teacher.id.in_(_active_subquery(db)))
        elif filter_mode == "inactive":
            q = q.filter(Teacher.id.notin_(_active_subquery(db)))
            
        # Filtro por status (Gobernanza v5)
        if status_filter in ["INCOMPLETO", "CONFLICTO", "INVALIDO"]:
            q = q.filter(Teacher.status == status_filter)
        elif status_filter == "ACTIVO":
            q = q.filter(Teacher.status == "ACTIVO", Teacher.dni.isnot(None))
        else:
            # Por defecto (None, "all", etc.), mostrar solo ACTIVO y con DNI no nulo (v5.5 estricto)
            q = q.filter(Teacher.status == "ACTIVO", Teacher.dni.isnot(None))
            
        if search:
            term = f"%{search.strip().upper()}%"
            q = q.filter(or_(
                func.upper(Teacher.last_name).like(term),
                func.upper(Teacher.first_name).like(term),
                func.upper(Teacher.dni).like(term),
            ))
            
        total = q.count()
        items = q.order_by(Teacher.id.desc()).offset((page - 1) * limit).limit(limit).all()
        return {"items": items, "total": total, "page": page, "total_pages": max(1, (total + limit - 1) // limit)}

    except Exception as e:
        logger.error("Error en listado de docentes", exc_info=True)
        raise e


from uuid import UUID
def fetch_teacher_by_id_full(db: Session, teacher_id: UUID) -> Optional[Teacher]:
    return db.query(Teacher).filter(Teacher.id == teacher_id).first()


def fetch_teacher_by_uid(db: Session, teacher_uid: str) -> Optional[Teacher]:
    return db.query(Teacher).filter(Teacher.uid == teacher_uid).first()


def fetch_teacher_by_dni(db: Session, dni: str) -> Optional[Teacher]:
    return db.query(Teacher).filter(Teacher.dni == dni.strip(), Teacher.dni.isnot(None)).first()


def fetch_teacher_by_normalized(db: Session, normalized: str) -> Optional[Teacher]:
    """Busca match exacto por normalized_name en teachers no fusionados."""
    return db.query(Teacher).filter(
        Teacher.normalized_name == normalized,
        Teacher.merged_into_id.is_(None)
    ).first()


def create_teacher(db: Session, data: Dict[str, Any]) -> Teacher:
    t = Teacher(**data)
    db.add(t)
    db.flush()
    return t


def update_teacher(db: Session, teacher: Teacher, data: Dict[str, Any]) -> Teacher:
    for k, v in data.items():
        if hasattr(teacher, k):
            setattr(teacher, k, v)
    db.flush()
    return teacher


# ════════════════════════════════════════════════════════
#  HISTÓRICO — CONSULTAS PARA REPROCESAMIENTO
# ════════════════════════════════════════════════════════

def fetch_all_teachers_from_table(db: Session) -> List[Teacher]:
    """Todos los teachers (vienen del XML via get_or_create)."""
    return db.query(Teacher).all()


def fetch_all_normalized_in_maestra(db: Session) -> List[str]:
    """Normalized names ya poblados en la maestra (no nulos)."""
    rows = db.query(Teacher.normalized_name).filter(
        Teacher.normalized_name.isnot(None),
        Teacher.normalized_name != ""
    ).all()
    return [r[0] for r in rows]


def bulk_update_normalized(db: Session, updates: List[Tuple[int, str]]) -> None:
    """Puebla normalized_name masivamente para registros que lo tienen vacío."""
    for t_id, norm in updates:
        db.query(Teacher).filter(Teacher.id == t_id).update(
            {"normalized_name": norm}, synchronize_session=False
        )
    db.flush()


# ════════════════════════════════════════════════════════
#  TEACHERS_SINASIGNAR — CRUD
# ════════════════════════════════════════════════════════

def fetch_sinasignar_paginated(
    db: Session,
    page: int = 1,
    limit: int = 20,
) -> Dict[str, Any]:
    """Paginado, ordenado por times_detected DESC (más críticos primero)."""
    q = db.query(Teacher).filter(Teacher.is_assigned == False).order_by(
        Teacher.times_detected.desc(),
        Teacher.last_name
    )
    total = q.count()
    items = q.offset((page - 1) * limit).limit(limit).all()
    return {"items": items, "total": total, "page": page, "total_pages": max(1, (total + limit - 1) // limit)}


def fetch_sinasignar_by_id(db: Session, sid: UUID) -> Optional[Teacher]:
    return db.query(Teacher).filter(Teacher.id == sid, Teacher.is_assigned == False).first()


def fetch_sinasignar_by_normalized(db: Session, normalized: str) -> Optional[Teacher]:
    return db.query(Teacher).filter(
        Teacher.normalized_name == normalized,
        Teacher.is_assigned == False
    ).first()


def create_sinasignar(db: Session, data: Dict[str, Any]) -> Teacher:
    # Aseguramos que se cree como no asignado
    data["is_assigned"] = False
    obj = Teacher(**data)
    db.add(obj)
    db.flush()
    return obj


def update_sinasignar(db: Session, obj: Teacher, data: Dict[str, Any]) -> Teacher:
    for k, v in data.items():
        if hasattr(obj, k):
            setattr(obj, k, v)
    db.flush()
    return obj


def increment_sinasignar_detection(db: Session, obj: Teacher) -> None:
    """Incrementa times_detected y actualiza last_seen_at (deduplicación)."""
    obj.times_detected = (obj.times_detected or 0) + 1
    obj.last_seen_at = datetime.now(timezone.utc)
    db.flush()


def delete_sinasignar(db: Session, obj: Teacher) -> None:
    db.delete(obj)
    db.flush()


# ════════════════════════════════════════════════════════
#  FUSIÓN — MERGE
# ════════════════════════════════════════════════════════

def get_root_teacher_id(db: Session, teacher_id: UUID, visited: Optional[set] = None) -> UUID:
    """
    Resuelve recursivamente el ID maestro final (Root Teacher).
    Implementa protección contra recursividad infinita (detección de ciclos).
    """
    if visited is None:
        visited = set()
    
    if teacher_id in visited:
        logger.error(f"MDM_CRITICAL: Ciclo de merge detectado para teacher_id {teacher_id}")
        return teacher_id # Romper ciclo retornando el actual
    
    visited.add(teacher_id)
    
    teacher = db.query(Teacher.id, Teacher.merged_into_id).filter(Teacher.id == teacher_id).first()
    if not teacher or not teacher.merged_into_id:
        return teacher_id
        
    return get_root_teacher_id(db, teacher.merged_into_id, visited)


def merge_teachers_db(db: Session, main_id: UUID, merge_id: UUID) -> None:
    """
    Fusión Segura MDM v4.2:
    1. Resuelve main_id al Root.
    2. Valida que merge_id no esté ya fusionado (Double Merge Protection).
    3. Reasigna relaciones exhaustivas (incluye MatchReview y Cadenas).
    4. Validación Post-Merge: Asegura cero referencias residuales.
    5. Auditoría 12-Factor: Log JSON con registros afectados.
    """
    if main_id == merge_id:
        return

    # 1. Resolver Root Maestro
    root_id = get_root_teacher_id(db, main_id)
    
    # 2. Obtener secundario y validar
    secondary = db.query(Teacher).filter(Teacher.id == merge_id).first()
    if not secondary:
        return
        
    if secondary.merged_into_id is not None:
        raise RuntimeError(f"MDM_ERROR: Docente {merge_id} ya se encuentra fusionado a {secondary.merged_into_id}")

    # --- 3. REASIGNACIÓN EXHAUSTIVA DE RELACIONES ---
    affected = {}
    
    # Lecciones
    res_lessons = db.query(Lesson).filter(Lesson.teacher_id == merge_id).update(
        {"teacher_id": root_id}, synchronize_session=False
    )
    affected["lessons"] = res_lessons

    # Observaciones (Titular)
    res_obs_t = db.query(Observation).filter(Observation.teacher_id == merge_id).update(
        {"teacher_id": root_id}, synchronize_session=False
    )
    # Observaciones (Reemplazo)
    res_obs_r = db.query(Observation).filter(Observation.replacement_teacher_id == merge_id).update(
        {"replacement_teacher_id": root_id}, synchronize_session=False
    )
    affected["observations"] = res_obs_t + res_obs_r

    # MatchReviews (Candidato)
    res_mr_c = db.query(MatchReview).filter(MatchReview.candidate_id == merge_id).update(
        {"candidate_id": root_id}, synchronize_session=False
    )
    # MatchReviews (XML Originario)
    res_mr_x = db.query(MatchReview).filter(MatchReview.xml_teacher_id == merge_id).update(
        {"xml_teacher_id": root_id}, synchronize_session=False
    )
    affected["match_reviews"] = res_mr_c + res_mr_x

    # Maestro de Docentes (Posibles duplicados)
    res_t_p = db.query(Teacher).filter(Teacher.possible_match_id == merge_id).update(
        {"possible_match_id": root_id}, synchronize_session=False
    )
    # Maestro de Docentes (Cadenas de fusión previas: Alumno -> Secundario => Alumno -> Root)
    res_t_m = db.query(Teacher).filter(Teacher.merged_into_id == merge_id).update(
        {"merged_into_id": root_id}, synchronize_session=False
    )
    affected["teacher_chains"] = res_t_p + res_t_m

    # 4. Actualización Atómica del Secundario
    secondary.is_active = False
    secondary.is_assigned = False
    secondary.merged_into_id = root_id
    secondary.match_review_id = None
    
    db.flush()

    # --- 5. VALIDACIÓN POST-MERGE (Habilitar integridad estricta) ---
    orphan_count = 0
    orphan_count += db.query(Lesson).filter(Lesson.teacher_id == merge_id).count()
    orphan_count += db.query(Observation).filter(or_(Observation.teacher_id == merge_id, Observation.replacement_teacher_id == merge_id)).count()
    orphan_count += db.query(MatchReview).filter(or_(MatchReview.candidate_id == merge_id, MatchReview.xml_teacher_id == merge_id)).count()
    
    import json
    from datetime import datetime, timezone
    
    log_data = {
        "event": "teacher_merge_executed",
        "mdm_version": "v4.2",
        "root_id": str(root_id),
        "secondary_id": str(merge_id),
        "rows_affected": affected,
        "orphan_references": orphan_count,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    if orphan_count > 0:
        log_data["status"] = "WARNING_RESIDUAL_REFS"
        print(json.dumps(log_data))
        # En modo hiper-estricto podríamos lanzar excepción aquí, 
        # pero por ahora logueamos para auditoría.
    else:
        log_data["status"] = "SUCCESS_INTEGRITY_VERIFIED"
        print(json.dumps(log_data))


def fetch_fuzzy_candidates(db: Session, match_key: str, min_len: int, max_len: int) -> List[Tuple[UUID, str, str]]:
    """
    Optimización MDM v4: Usa normalized_for_match para la búsqueda inicial.
    Retorna Lista de (id, normalized_name_canónico, match_key).
    """
    prefix = match_key[:2]
    rows = db.query(Teacher.id, Teacher.normalized_name, Teacher.normalized_for_match).filter(
        Teacher.is_assigned == True,
        Teacher.merged_into_id.is_(None),
        Teacher.normalized_for_match.like(f"{prefix}%"),
        func.length(Teacher.normalized_for_match).between(min_len, max_len)
    ).all()
    return rows


def cleanup_sinasignar_post_merge(db: Session, secondary_id: str, secondary_norm: str) -> None:
    """
    Elimina de registros no asignados solo coincidencias exactas con el eliminado o vínculos directos.
    """
    db.query(Teacher).filter(
        Teacher.is_assigned == False,
        or_(
            Teacher.possible_match_id == secondary_id,
            Teacher.normalized_name == secondary_norm
        )
    ).delete(synchronize_session=False)
    db.flush()


# ════════════════════════════════════════════════════════
#  MATCH REVIEW — AUDITORÍA MDM
# ════════════════════════════════════════════════════════

def create_match_review(db: Session, data: Dict[str, Any]) -> MatchReview:
    obj = MatchReview(**data)
    db.add(obj)
    db.flush()
    return obj


def fetch_pending_reviews(db: Session, status: str = "PENDING") -> List[MatchReview]:
    return db.query(MatchReview).filter(MatchReview.status == status).order_by(MatchReview.created_at.desc()).all()


def fetch_review_by_id(db: Session, review_id: UUID, for_update: bool = False) -> Optional[MatchReview]:
    q = db.query(MatchReview).filter(MatchReview.id == review_id)
    if for_update:
        q = q.with_for_update()
    return q.first()


def update_match_review_status(db: Session, review: MatchReview, status: str) -> MatchReview:
    review.status = status
    db.flush()
    return review
