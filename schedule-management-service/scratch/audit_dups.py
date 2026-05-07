import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    print("--- 1. XML UPLOADS ---")
    res = db.execute(text("SELECT filename, created_at, status, start_date, end_date FROM xml_uploads ORDER BY created_at DESC;")).fetchall()
    for row in res:
        print(row)

    print("\n--- 2. RPT PLANILLA COLUMNS ---")
    cols = db.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'rpt_planilla';")).fetchall()
    for col in cols:
        print(col)

    print("\n--- 3. DUPLICATE COUNT IN RPT_PLANILLA (fecha_clase, docente, hora_inicio) ---")
    dups = db.execute(text("""
        SELECT fecha_clase, docente, hora_inicio, COUNT(*) 
        FROM rpt_planilla 
        GROUP BY fecha_clase, docente, hora_inicio 
        HAVING COUNT(*) > 1 
        LIMIT 20;
    """)).fetchall()
    print(f"Total duplicate combinations found: {len(dups)}")
    for d in dups:
        print(d)

    print("\n--- 4. GENERAL TOTALS FOR 02/03 TO 08/03 AND BEYOND ---")
    tot_exact = db.execute(text("SELECT COUNT(*), SUM(horas_dictadas) FROM rpt_planilla WHERE fecha_clase BETWEEN '2026-03-02' AND '2026-03-08';")).fetchone()
    print(f"Exactly 02/03 to 08/03: {tot_exact}")
    tot_extended = db.execute(text("SELECT COUNT(*), SUM(horas_dictadas) FROM rpt_planilla WHERE fecha_clase BETWEEN '2026-03-02' AND '2026-03-13';")).fetchone()
    print(f"Extended 02/03 to 13/03: {tot_extended}")

finally:
    db.close()
