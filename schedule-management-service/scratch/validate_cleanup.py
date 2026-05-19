import os
import sys
from app.core.database import SessionLocal
from app.models import Teacher
from app.modules.docentes.service import get_active_teachers_for_rpt, get_all_teachers

db = SessionLocal()
try:
    print("Initiating programmatic cleanup validation...")

    # 1. Direct database check
    teacher_count = db.query(Teacher).count()
    print(f"Direct DB teacher count: {teacher_count}")
    
    # 2. Check for any remaining source_ids
    remaining_sources = db.query(Teacher.source_id, Teacher.last_name, Teacher.first_name).all()
    print(f"Residual source IDs: {remaining_sources}")

    # 3. Call get_active_teachers_for_rpt
    active_rpt_teachers = get_active_teachers_for_rpt(db)
    print(f"get_active_teachers_for_rpt count: {len(active_rpt_teachers)}")
    print(f"get_active_teachers_for_rpt details: {active_rpt_teachers}")

    # 4. Call get_all_teachers (Maestra view service layer)
    maestra_response = get_all_teachers(db, filter_mode="all", page=1, limit=20)
    # The return type is a StandardResponse object, we can access its fields
    maestra_data = maestra_response.data.data
    maestra_total = maestra_response.data.total
    print(f"Maestra view total records: {maestra_total}")
    print(f"Maestra view page data count: {len(maestra_data)}")
    print(f"Maestra response data: {maestra_data}")

    # 5. Core validation assertions
    if teacher_count == 0 and len(active_rpt_teachers) == 0 and maestra_total == 0:
        print("\n[CLEANUP VALIDATION PASSED]")
        print("- Database table 'teachers' is fully empty.")
        print("- /api/docentes for RPT reports returns [].")
        print("- Maestra view service returns 0 total records.")
        print("- The system is completely clean and ready for week-over-week XML and Excel reimports.")
    else:
        print("\n[CLEANUP VALIDATION FAILED]")
        sys.exit(1)

except Exception as e:
    print(f"ERROR running validation: {e}")
    sys.exit(1)
finally:
    db.close()
