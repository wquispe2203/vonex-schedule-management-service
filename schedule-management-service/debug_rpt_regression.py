import os
import sys
from app.core.database import SessionLocal
from app.modules.reportes.service import get_planilla_data

db = SessionLocal()
try:
    print("Executing RPT Planilla basic lookup...")
    # Fetching active range from known XML data
    result = get_planilla_data(db, "2026-03-01", "2026-03-08")
    print("SUCCESS: RPT successfully retrieved data count:", len(result))
except Exception as e:
    import traceback
    print("FAILURE: Regresion detected in RPT module!")
    traceback.print_exc()
finally:
    db.close()
