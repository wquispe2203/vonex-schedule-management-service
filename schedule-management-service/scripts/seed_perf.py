import uuid
import random
from datetime import date, time, timedelta
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app.models import Teacher, Subject, ClassGroup, Lesson, ScheduleSession, Grade

def seed_performance_data():
    db: Session = SessionLocal()
    try:
        print("--- Iniciando Seed de Performance ---")
        
        # 1. Crear Grados
        grades = []
        for i in range(1, 6):
            grade = Grade(id=uuid.uuid4(), name=f"Grado {i}")
            db.add(grade)
            grades.append(grade)
        db.flush()
        
        # 2. Crear Materias (Subjects)
        subjects = []
        for i in range(20):
            subject = Subject(
                id=uuid.uuid4(),
                source_id=f"SUBJ-{i}",
                name=f"Materia de Prueba {i}",
                short_name=f"MP{i}"
            )
            db.add(subject)
            subjects.append(subject)
        db.flush()
            
        # 3. Crear Clases (ClassGroups)
        classes = []
        for i in range(30):
            class_obj = ClassGroup(
                id=uuid.uuid4(),
                source_id=f"CLASS-{i}",
                name=f"Sección {chr(65 + (i % 5))}",
                grade_id=random.choice(grades).id
            )
            db.add(class_obj)
            classes.append(class_obj)
        db.flush()
            
        # 4. Crear Docentes (Teachers) - 100
        teachers = []
        for i in range(100):
            teacher = Teacher(
                id=uuid.uuid4(),
                first_name=f"Nombre{i}",
                last_name=f"Apellido{i}",
                normalized_name=f"APELLIDO{i} NOMBRE{i}",
                dni=str(10000000 + i)
            )
            db.add(teacher)
            teachers.append(teacher)
        db.flush()
        
        # 5. Crear Lecciones (Lessons) - 500
        lessons = []
        for i in range(500):
            lesson = Lesson(
                id=uuid.uuid4(),
                source_id=f"LESSON-{i}",
                subject_id=random.choice(subjects).id,
                teacher_id=random.choice(teachers).id,
                class_id=random.choice(classes).id
            )
            db.add(lesson)
            lessons.append(lesson)
        db.flush()
        
        # 6. Crear Sesiones (Schedule Sessions) - 5,000
        start_date = date.today()
        for i in range(5000):
            lesson = random.choice(lessons)
            session_date = start_date + timedelta(days=random.randint(0, 30))
            hour = random.randint(7, 16)
            session = ScheduleSession(
                id=uuid.uuid4(),
                lesson_id=lesson.id,
                session_date=session_date,
                start_time=time(hour, 0),
                end_time=time(hour + 1, 0),
                status="ACTIVE"
            )
            db.add(session)
            if i % 1000 == 0:
                print(f"Generadas {i} sesiones...")
        
        db.commit()
        print("--- [SUCCESS] Seed de Performance completado: 5,000 sesiones creadas ---")
        
    except Exception as e:
        db.rollback()
        print(f"--- [ERROR] Fallo en Seed: {e} ---")
    finally:
        db.close()

if __name__ == "__main__":
    seed_performance_data()
