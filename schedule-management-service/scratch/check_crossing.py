from app.core.database import SessionLocal
from app.modules.docentes.service import _run_crossing_engine

def run():
    db = SessionLocal()
    try:
        res = _run_crossing_engine(db)
        print(f"Matched: {len(res['matched'])}")
        print(f"Sin Asignar: {len(res['sin_asignar'])}")
        print(f"Conflictos: {len(res['conflictos'])}")
        
        # Are there any without DNI in matched?
        for name, t in res['matched']:
            if not t.dni or not t.dni.strip():
                print(f"MATCHED WITHOUT DNI: {name} -> {t.id}")
                
    finally:
        db.close()

if __name__ == "__main__":
    run()
