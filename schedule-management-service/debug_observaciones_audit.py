import sys
import os
from app.core.database import SessionLocal
from app.modules.horarios.service import get_teachers_list
from app.modules.observaciones.service import get_grouped_sessions_for_incidencias

db = SessionLocal()
try:
    print("\n--- 1. Verificando get_teachers_list ---")
    data = get_teachers_list(db)
    print(f"SUCCESS: Recibidos {len(data)} docentes activos.")
    if len(data) > 0:
         sample = data[0]
         print("Sample Docente:", sample)
         
         print("\n--- 2. Verificando get_grouped_sessions_for_incidencias ---")
         teacher_id = sample['id']
         # A wide range to ensure hits
         sessions = get_grouped_sessions_for_incidencias(db, teacher_id, "2024-01-01", "2027-01-01")
         print(f"SUCCESS: Agrupadas {len(sessions)} sesiones para el docente.")
    else:
         print("WARNING: No hay docentes para testear.")

finally:
    db.close()
