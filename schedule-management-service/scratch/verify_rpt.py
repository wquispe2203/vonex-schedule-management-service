from app.core.database import SessionLocal
from app.modules.docentes.service import get_sinasignar_crossed
from app.modules.reportes.repository import fetch_rpt_records
from datetime import date

db = SessionLocal()
try:
    print("=== RUNNING VERIFICATION CHECK ===")
    
    # 1. Verify "Sin Asignar" Crossed
    print("\n1. Verifying 'Sin Asignar' crossed list...")
    sa_response = get_sinasignar_crossed(db, page=1, limit=100)
    sa_data = sa_response.data.data
    print(f"Total unassigned teachers found: {len(sa_data)}")
    
    sannchez_found = False
    marya_found = False
    for item in sa_data:
        name = item.get("nombre_xml") or ""
        if "SANNCHEZ" in name.upper() or "MARYA" in name.upper():
            print(f"  [ERROR] Ghost teacher found: {name}")
            sannchez_found = True
            
    if not sannchez_found:
        print("  [SUCCESS] No ghost teachers (Sannchez/Marya) found in 'Sin Asignar' crossed list.")
        
    # 2. Verify RPT records for 02/03 -> 08/03
    print("\n2. Verifying RPT records for 02/03 -> 08/03...")
    start_date = date(2026, 3, 2)
    end_date = date(2026, 3, 8)
    records = fetch_rpt_records(db, start_date, end_date)
    print(f"Total RPT records fetched for 02/03 -> 08/03: {len(records)}")
    
    if len(records) > 0:
        print("  [SUCCESS] RPT records fetched successfully!")
        # Let's inspect unique active teachers in RPT
        teachers = {r.docente for r in records if r.docente}
        print(f"  Unique teachers in report: {len(teachers)}")
        print(f"  Sample teachers: {list(teachers)[:5]}")
    else:
        print("  [ERROR] No RPT records returned!")

    print("\n=== VERIFICATION COMPLETED ===")
finally:
    db.close()
