from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import unicodedata
import re

SQLALCHEMY_DATABASE_URL = "postgresql://postgres:C%40rden4s2k24@localhost/schedule_db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def normalize_teacher_name_local(apellidos: str, nombres: str) -> str:
    """Misma lógica que la app para consistencia."""
    raw = f"{apellidos or ''} {nombres or ''}".strip()
    nfkd = unicodedata.normalize("NFKD", raw)
    no_accent = "".join(c for c in nfkd if not unicodedata.combining(c))
    clean = re.sub(r"\s+", " ", no_accent.lower().replace(",", " ")).strip()
    return clean

def run_manual_sync_all_v2():
    db = SessionLocal()
    try:
        print("--- Running Manual Sync (Safe) for ALL Unlinked Observations ---")
        
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
        for r_obs in observations:
            obs_id = r_obs[0]
            raw_name = r_obs[1]
            
            # Parsear el nombre guardado en texto
            if ',' in raw_name:
                parts = raw_name.split(',', 1)
                ln, fn = parts[0].strip(), parts[1].strip()
            else:
                # Fallback names
                parts = raw_name.split()
                ln = f"{parts[0]} {parts[1]}" if len(parts) >= 2 else parts[0]
                fn = " ".join(parts[2:]) if len(parts) > 2 else ""
            
            norm = normalize_teacher_name_local(ln, fn)
            
            # Buscar el docente en la tabla teachers
            teacher_query = text("SELECT id, last_name, first_name FROM teachers WHERE normalized_name = :norm")
            teacher = db.execute(teacher_query, {"norm": norm}).fetchone()
            
            if teacher:
                t_id = teacher[0]
                print(f"MATCH FOUND! Obs ID {obs_id}: '{raw_name}' -> Teacher ID {t_id} ({teacher[1]} {teacher[2]})")
                update_query = text("UPDATE observations SET replacement_teacher_id = :tid WHERE id = :oid")
                db.execute(update_query, {"tid": t_id, "oid": obs_id})
                synced_count += 1
        
        db.commit()
        print(f"\nDONE. Total synchronized: {synced_count}")

    except Exception as e:
        db.rollback()
        print(f"FATAL ERROR: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    run_manual_sync_all_v2()
