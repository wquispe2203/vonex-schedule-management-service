from app.core.database import SessionLocal
from app.models import Teacher
from sqlalchemy import func
from collections import Counter

db = SessionLocal()
try:
    print("--- Teacher Statuses ---")
    status_counts = db.query(Teacher.status, func.count(Teacher.id)).group_by(Teacher.status).all()
    for s, c in status_counts:
        print(f"Status: {s}, Count: {c}")

    print("\n--- Teachers without DNI ---")
    no_dni = db.query(Teacher).filter((Teacher.dni == None) | (Teacher.dni == '')).all()
    for t in no_dni:
        print(f"ID: {t.id}, Name: {t.last_name} {t.first_name}, Status: {t.status}")

    print("\n--- Duplicates by Normalized Name ---")
    all_teachers = db.query(Teacher).all()
    norm_names = [t.normalized_name for t in all_teachers if t.normalized_name]
    norm_counts = Counter(norm_names)
    dup_norms = {name: count for name, count in norm_counts.items() if count > 1}
    print(f"Duplicate normalized names: {dup_norms}")

    print("\n--- Duplicates by DNI ---")
    dnis = [t.dni for t in all_teachers if t.dni and t.dni.strip()]
    dni_counts = Counter(dnis)
    dup_dnis = {dni: count for dni, count in dni_counts.items() if count > 1}
    print(f"Duplicate DNIs: {dup_dnis}")
    
finally:
    db.close()
