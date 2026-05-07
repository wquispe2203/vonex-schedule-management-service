from app.core.database import SessionLocal
from app.modules.docentes.service import get_sinasignar_crossed, get_conflictos_crossed, get_latest_completed_upload
import logging

logging.basicConfig(level=logging.INFO)

db = SessionLocal()
latest = get_latest_completed_upload(db)
print(f"LATEST UPLOAD: {latest.id}")

print("\n--- TEST SIN ASIGNAR ---")
res_sa = get_sinasignar_crossed(db)
print(f"Total Sin Asignar: {res_sa.data.total}")

print("\n--- TEST CONFLICTOS ---")
res_cf = get_conflictos_crossed(db)
print(f"Total Conflictos: {res_cf.data.total}")
if res_cf.data.data:
    print(f"Ejemplo Conflicto: {res_cf.data.data[0]}")

db.close()
