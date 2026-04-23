from sqlalchemy import or_, func, and_, select
from sqlalchemy.orm import Session, joinedload
from uuid import UUID
from app.models import Teacher, ClassGroup, RptPlanilla, ScheduleSession, Lesson, Observation
from typing import List, Optional

def fetch_all_teachers(db: Session) -> List[Teacher]:
    return db.query(Teacher).order_by(Teacher.last_name).all()

def fetch_all_classes(db: Session) -> List[ClassGroup]:
    return db.query(ClassGroup).order_by(ClassGroup.name).all()

def fetch_teacher_by_id(db: Session, teacher_id: UUID) -> Optional[Teacher]:
    return db.query(Teacher).filter(Teacher.id == teacher_id).first()

def fetch_replacement_sessions_ids(db: Session, teacher_id: Optional[UUID], search_name: str) -> List[UUID]:
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

def fetch_rpt_rows(db: Session, teacher_fullname: str, teacher_last_name: str, start_date: str, end_date: str, teacher_id: Optional[UUID] = None) -> List[RptPlanilla]:
    # 1. Buscar registros donde es titular
    # Usamos normalize_name similar a reportes para mayor precisión si fuera necesario, 
    # pero aquí mantendremos la lógica de búsqueda por nombre exacto o last_name para no romper compatibilidad.
    
    # 2. Buscar sesiones donde fue reemplazo (si aplica)
    replacement_ids = fetch_replacement_sessions_ids(db, teacher_id, teacher_fullname)
    
    # 3. Query unificada o incremental
    # Para mantener consistencia con el visor, buscaremos por nombre directo en RptPlanilla 
    # (Ya que RptPlanilla tiene el nombre del docente que REALMENTE dictó la clase)
    
    rpt_rows = db.query(RptPlanilla).filter(
        or_(
            RptPlanilla.docente == teacher_fullname,
            RptPlanilla.docente.ilike(f"%{teacher_last_name}%")
        ),
        RptPlanilla.fecha_clase >= start_date,
        RptPlanilla.fecha_clase <= end_date
    ).order_by(RptPlanilla.fecha_clase.asc(), RptPlanilla.hora_inicio.asc()).all()

    return rpt_rows

def fetch_teacher_combined_sessions(db: Session, teacher_id: UUID, start_date: str, end_date: str, teacher_name: Optional[str] = None) -> List[ScheduleSession]:
    # 1. Identificar IDs candidatos por nombre (para manejar duplicados/variaciones)
    candidate_ids = [teacher_id]
    search_name = teacher_name.strip().upper() if teacher_name else None
    
    if search_name:
        no_comma = search_name.replace(',', '').strip()
        alt_ids = db.query(Teacher.id).filter(
            or_(
                func.concat(Teacher.first_name, ' ', Teacher.last_name).ilike(f"%{no_comma}%"),
                func.concat(Teacher.last_name, ' ', Teacher.first_name).ilike(f"%{no_comma}%")
            )
        ).all()
        candidate_ids = list(set(candidate_ids + [r[0] for r in alt_ids]))

    # 2. Subquery para reemplazos (por ID o por Nombre)
    repl_filter = [Observation.type == 'REEMPLAZO']
    if search_name:
        no_comma = search_name.replace(',', '').strip()
        repl_filter.append(or_(
            Observation.replacement_teacher_id.in_(candidate_ids),
            func.upper(func.trim(Observation.replacement_teacher_name)).ilike(f"%{no_comma}%")
        ))
    else:
        repl_filter.append(Observation.replacement_teacher_id.in_(candidate_ids))

    replacement_session_ids = (
        select(Observation.session_id)
        .where(*repl_filter)
    )

    # 3. Query final unificada
    return (
        db.query(ScheduleSession)
        .join(Lesson, ScheduleSession.lesson_id == Lesson.id)
        .filter(
            ScheduleSession.session_date >= start_date,
            ScheduleSession.session_date <= end_date,
            or_(
                Lesson.teacher_id.in_(candidate_ids),
                ScheduleSession.id.in_(replacement_session_ids)
            )
        )
        .options(
            joinedload(ScheduleSession.lesson).joinedload(Lesson.subject),
            joinedload(ScheduleSession.lesson).joinedload(Lesson.class_group),
            joinedload(ScheduleSession.lesson).joinedload(Lesson.teacher),
            joinedload(ScheduleSession.observations).joinedload(Observation.replacement_teacher)
        )
        .order_by(ScheduleSession.session_date.asc(), ScheduleSession.start_time.asc())
        .all()
    )

def fetch_sessions_with_observations(db: Session, start_date: str, end_date: str) -> List[ScheduleSession]:
# ... (rest of the file stays same)
    return (
        db.query(ScheduleSession)
        .join(Lesson)
        .outerjoin(ClassGroup, Lesson.class_id == ClassGroup.id)
        .filter(
            ScheduleSession.session_date >= start_date,
            ScheduleSession.session_date <= end_date,
        )
        .options(
            joinedload(ScheduleSession.observations),
            joinedload(ScheduleSession.lesson).joinedload(Lesson.class_group)
        )
        .all()
    )

def fetch_classroom_sessions(db: Session, class_id: UUID, start_date: str, end_date: str) -> List[ScheduleSession]:
    return db.query(ScheduleSession).join(Lesson).filter(
        Lesson.class_id == class_id,
        ScheduleSession.session_date >= start_date,
        ScheduleSession.session_date <= end_date
    ).options(
        joinedload(ScheduleSession.lesson).joinedload(Lesson.subject),
        joinedload(ScheduleSession.lesson).joinedload(Lesson.teacher),
        joinedload(ScheduleSession.observations)
    ).all()

def fetch_export_sessions(db: Session, export_type: str, target_id: UUID, start_date: str, end_date: str) -> List[ScheduleSession]:
    if export_type == "teacher":
        return db.query(ScheduleSession).join(Lesson).filter(
            Lesson.teacher_id == target_id,
            ScheduleSession.session_date >= start_date,
            ScheduleSession.session_date <= end_date
        ).options(
            joinedload(ScheduleSession.lesson).joinedload(Lesson.subject),
            joinedload(ScheduleSession.lesson).joinedload(Lesson.class_group),
            joinedload(ScheduleSession.lesson).joinedload(Lesson.teacher)
        ).all()
    else:
        return db.query(ScheduleSession).join(Lesson).filter(
            Lesson.class_id == target_id,
            ScheduleSession.session_date >= start_date,
            ScheduleSession.session_date <= end_date
        ).options(
            joinedload(ScheduleSession.lesson).joinedload(Lesson.subject),
            joinedload(ScheduleSession.lesson).joinedload(Lesson.class_group),
            joinedload(ScheduleSession.lesson).joinedload(Lesson.teacher)
        ).all()
