from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text, func
from app.core.database import get_db
from app.models import Teacher, Lesson, ScheduleSession, Subject, ClassGroup

router = APIRouter(
    prefix="/api/perf",
    tags=["Performance Testing"],
    include_in_schema=False  # Ocultar de Swagger/OpenAPI
)

@router.get("/slow")
def test_slow_query(db: Session = Depends(get_db)):
    """Simula una consulta lenta de 15 segundos para validar timeouts."""
    try:
        # Forzar sleep en PostgreSQL
        db.execute(text("SELECT pg_sleep(15)"))
        return {"message": "Finalizado después de 15s (no debería ocurrir con timeout de 10s)"}
    except Exception as e:
        # Este error será capturado por el Global Exception Handler y logueado
        raise e

@router.get("/intensive")
def test_intensive_query(db: Session = Depends(get_db)):
    """Ejecuta una consulta intensiva con múltiples joins y agregaciones."""
    try:
        # Consulta: Top 10 docentes con más sesiones programadas, incluyendo materia y grupo
        results = db.query(
            Teacher.last_name,
            Teacher.first_name,
            func.count(ScheduleSession.id).label("total_sessions")
        ).join(Lesson, Teacher.id == Lesson.teacher_id) \
         .join(ScheduleSession, Lesson.id == ScheduleSession.lesson_id) \
         .group_by(Teacher.id) \
         .order_by(text("total_sessions DESC")) \
         .limit(10) \
         .all()
        
        return {
            "success": True, 
            "data": [
                {"name": f"{r[0]}, {r[1]}", "sessions": r[2]} for r in results
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
