from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_, and_, asc
from app.models import RptPlanilla, Observation, ScheduleSession, Lesson, Teacher
from typing import List, Optional, Tuple
from datetime import date

def fetch_rpt_records(
    db: Session, 
    fecha_inicio: date, 
    fecha_fin: date, 
    sede: Optional[str] = None, 
    aula: Optional[str] = None
) -> List[RptPlanilla]:
    """Obtiene los registros base de RptPlanilla filtrados por fecha y ubicación."""
    query = db.query(RptPlanilla).filter(
        RptPlanilla.fecha_clase >= fecha_inicio,
        RptPlanilla.fecha_clase <= fecha_fin
    )
    if sede and sede != "Todas":
        query = query.filter(RptPlanilla.sede == sede)
    if aula and aula != "Todos":
        query = query.filter(RptPlanilla.ciclo == aula)
    
    return query.order_by(asc(RptPlanilla.fecha_clase), asc(RptPlanilla.hora_inicio)).all()

def fetch_context_data(db: Session, fecha_init: date, fecha_end: date):
    """
    Obtiene Sessions y Observations en bloques optimizados (Anti N+1).
    """
    # Observations con su sesión para evitar sub-queries
    observations = (
        db.query(Observation)
        .join(ScheduleSession, Observation.session_id == ScheduleSession.id)
        .filter(
            ScheduleSession.session_date >= fecha_init,
            ScheduleSession.session_date <= fecha_end
        )
        .all()
    )

    # Sessions con Lesson y ClassGroup para metadata
    sessions = (
        db.query(
            ScheduleSession.id, 
            ScheduleSession.session_date,
            ScheduleSession.start_time, 
            ScheduleSession.end_time, 
            Lesson.teacher_id
        )
        .join(Lesson)
        .filter(
            ScheduleSession.session_date >= fecha_init, 
            ScheduleSession.session_date <= fecha_end
        )
        .all()
    )

    return observations, sessions

def fetch_teachers_lookup(db: Session) -> List[Teacher]:
    return db.query(Teacher.id, Teacher.uid, Teacher.first_name, Teacher.last_name).all()

def fetch_distinct_sedes(db: Session) -> List[str]:
    results = db.query(RptPlanilla.sede).distinct().order_by(RptPlanilla.sede).all()
    return [r[0] for r in results if r[0]]

def fetch_distinct_aulas(db: Session, sede: str) -> List[str]:
    results = db.query(RptPlanilla.ciclo).filter(RptPlanilla.sede == sede).distinct().order_by(RptPlanilla.ciclo).all()
    return [r[0] for r in results if r[0]]

def fetch_teacher_by_name_flexible(db: Session, search_term: str) -> Optional[Teacher]:
    clean = search_term.strip().upper()
    no_comma = clean.replace(',', '').strip()
    
    # Intento de parseo básico si hay coma
    parts = clean.split(',')
    last = parts[0].strip() if len(parts) == 2 else no_comma
    first = parts[1].strip() if len(parts) == 2 else ""

    filters = [
        func.concat(Teacher.first_name, ' ', Teacher.last_name).ilike(f"%{no_comma}%"),
        func.concat(Teacher.last_name, ' ', Teacher.first_name).ilike(f"%{no_comma}%")
    ]
    if first and last:
        filters.append(and_(Teacher.last_name.ilike(f"%{last}%"), Teacher.first_name.ilike(f"%{first}%")))

    return db.query(Teacher).filter(or_(*filters)).first()

def fetch_replacement_sessions_ids(db: Session, teacher_id: Optional[int], search_name: str) -> List[int]:
    """Busca sesiones donde el docente actuó como reemplazo."""
    repl_filter = [Observation.type == 'REEMPLAZO']
    if teacher_id:
        repl_filter.append(or_(
            Observation.replacement_teacher_id == teacher_id,
            func.upper(func.trim(Observation.replacement_teacher_name)) == search_name.strip().upper()
        ))
    else:
        repl_filter.append(
            func.upper(func.trim(Observation.replacement_teacher_name)) == search_name.strip().upper()
        )

    results = db.query(Observation.session_id).filter(*repl_filter).all()
    return [r[0] for r in results]

def fetch_sessions_info(db: Session, session_ids: List[int], start_date: date, end_date: date):
    return db.query(
        ScheduleSession.session_date,
        ScheduleSession.start_time,
        ScheduleSession.end_time,
        Lesson.teacher_id
    ).join(Lesson).filter(
        ScheduleSession.id.in_(session_ids),
        ScheduleSession.session_date >= start_date,
        ScheduleSession.session_date <= end_date
    ).all()
