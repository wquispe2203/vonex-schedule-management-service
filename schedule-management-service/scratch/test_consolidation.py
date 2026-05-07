import os
import sys
from datetime import date
from app.core.database import SessionLocal
from app.modules.reportes import repository, service

def main():
    print("=== TESTING CONSOLIDATION AND RECESS LOGIC ===")
    db = SessionLocal()
    try:
        # Fetch records
        fecha_inicio = date(2026, 3, 2)
        fecha_fin = date(2026, 3, 8)
        
        records = repository.fetch_rpt_records(db, fecha_inicio, fecha_fin)
        print(f"Base RPT Records: {len(records)}")
        
        # Process logic with consolidation
        processed = service.process_rpt_logic(db, records, fecha_inicio, fecha_fin)
        print(f"Processed / Consolidated rows: {len(processed)}")
        
        # Check for breaks
        breaks_detected = [row for row in processed if row["receso"] > 0]
        print(f"Rows with breaks (receso > 0): {len(breaks_detected)}")
        if breaks_detected:
            print("Sample break rows:")
            for row in breaks_detected[:5]:
                print(f"  Docente: {row['docente']} | Horas: {row['horas_dictadas']} | Receso: {row['receso']} | Curso: {row['curso']} | Horario: {row['hora_inicio']}-{row['hora_fin']}")
                
        print("=== CONSOLIDATION TEST COMPLETED ===")
    finally:
        db.close()

if __name__ == "__main__":
    main()
