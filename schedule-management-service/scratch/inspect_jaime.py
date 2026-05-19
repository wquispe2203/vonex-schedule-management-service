import sys
import os

# Configurar path para importar app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import SessionLocal
from app.models import ScheduleSession, Observation, Teacher, RptPlanilla, Lesson

db = SessionLocal()

try:
    # Buscar docente
    teacher = db.query(Teacher).filter(Teacher.last_name.ilike("%Asencio%")).first()
    if not teacher:
        print("Docente Jaime Asencio no encontrado en Teachers.")
        sys.exit(0)

    print(f"Docente: {teacher.id} - {teacher.last_name}, {teacher.first_name}")

    # Buscar sesiones del 2026-03-03
    sessions = db.query(ScheduleSession).join(Lesson).filter(
        Lesson.teacher_id == teacher.id,
        ScheduleSession.session_date == "2026-03-03"
    ).all()

    print("\n--- SESIONES EN SCHEDULE_SESSIONS ---")
    for s in sessions:
        print(f"ID: {s.id} | Date: {s.session_date} | Start: {s.start_time} | End: {s.end_time} | Status: {s.status}")

    # Buscar observaciones del 2026-03-03 para este docente
    observations = db.query(Observation).filter(
        Observation.teacher_id == teacher.id,
        Observation.session_id.in_([s.id for s in sessions]) if sessions else [0]
    ).all()

    print("\n--- OBSERVACIONES ---")
    for o in observations:
        print(f"ID: {o.id} | SessionID: {o.session_id} | Type: {o.type} | Time: {o.start_time} - {o.end_time} | Repl: {o.replacement_teacher_name} | ReplID: {o.replacement_teacher_id}")

    # Buscar registros en RPT Planilla del 2026-03-03
    rpt_records = db.query(RptPlanilla).filter(
        RptPlanilla.docente.ilike("%Asencio%"),
        RptPlanilla.fecha_clase == "2026-03-03"
    ).all()

    print("\n--- REGISTROS BASE RPT_PLANILLA (EXCEL) ---")
    for r in rpt_records:
        print(f"ID: {r.id} | Sede: {r.sede} | Ciclo: {r.ciclo} | Curso: {r.curso} | Time: {r.hora_inicio} | Hours: {r.horas_dictadas}")

finally:
    db.close()
