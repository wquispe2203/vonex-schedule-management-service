from app.core.database import SessionLocal
from app.modules.docentes.service import get_active_teachers_for_rpt, get_sinasignar_crossed

def run():
    db = SessionLocal()
    try:
        rpt_teachers = get_active_teachers_for_rpt(db)
        print(f"RPT Teachers count: {len(rpt_teachers)}")
        
        sin_asignar_result = get_sinasignar_crossed(db)
        # sin_asignar_result is a StandardResponse object
        # its data is a PaginatedResponseData object
        print(f"SIN ASIGNAR count: {sin_asignar_result.data.total}")
        
    finally:
        db.close()

if __name__ == "__main__":
    run()
