from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import sys
import os

# Añadir el path para importar normalize_teacher_name
sys.path.append(os.path.join(os.getcwd(), 'app'))
from modules.docentes.service import normalize_teacher_name

SQLALCHEMY_DATABASE_URL = "postgresql://postgres:C%40rden4s2k24@localhost/schedule_db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def run_manual_sync_all():
    db = SessionLocal()
    try:
        print("--- Running Manual Sync for ALL Unlinked Observations ---")
        
        # 1. Get all unlinked replacement observations
        query = text("""
            SELECT id, replacement_teacher_name 
            FROM observations 
            WHERE replacement_teacher_id IS NULL 
              AND replacement_teacher_name IS NOT NULL
        """)
        observations = db.execute(query).fetchall()
        print(f"Found {len(observations)} unlinked observations.")

        synced_count = 0
        for obs_id, raw_name in observations:
            # Parsear el nombre guardado en texto (Misma lógica que el repositorio)
            if ',' in raw_name:
                parts = raw_name.split(',', 1)
                ln, fn = parts[0].strip(), parts[1].strip()
            else:
                parts = raw_name.split()
                ln = f"{parts[0]} {parts[1]}" if len(parts) >= 3 else parts[0]
                fn = " ".join(parts[2:]) if len(parts) >= 3 else (parts[1] if len(parts) > 1 else "")
            
            norm = normalize_teacher_name(ln, fn)
            
            # Buscar el docente en la tabla teachers
            teacher_query = text("SELECT id FROM teachers WHERE normalized_name = :norm")
            teacher = db.execute(teacher_query, {"norm": norm}).fetchone()
            
            if teacher:
                t_id = teacher[0]
                print(f"Match Found! Obs ID {obs_id}: '{raw_name}' -> Teacher ID {t_id}")
                update_query = text("UPDATE observations SET replacement_teacher_id = :tid WHERE id = :oid")
                db.execute(update_query, {"tid": t_id, "oid": obs_id})
                synced_count += 1
        
        db.commit()
        print(f"DONE. Total synchronized: {synced_count}")

    except Exception as e:
        db.rollback()
        print(f"FATAL ERROR: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    run_manual_sync_all()
