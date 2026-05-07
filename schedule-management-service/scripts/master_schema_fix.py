import sys
import os
from sqlalchemy import create_engine, text

# Add project path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.config import settings

def fix_db(url, label):
    print(f"\n--- FIXING DATABASE: {label} ---")
    engine = create_engine(url)
    with engine.connect() as conn:
        
        # 1. Table: lessons
        print("Processing 'lessons'...")
        # Renaming columns
        for old, new in [('old_system_subject_id', 'legacy_subject_id'), 
                         ('old_system_teacher_id', 'legacy_teacher_id'), 
                         ('old_system_class_id', 'legacy_class_id')]:
            try:
                # Si existe el nuevo, lo borramos (solo si está vacío o si queremos priorizar el 'old_system')
                # En este caso, el usuario quiere estandarizar. 
                # Si ambos existen, el 'legacy_id' original suele ser el residuo.
                conn.execute(text(f"ALTER TABLE lessons RENAME COLUMN {old} TO {new}"))
                print(f"  [OK] Renamed {old} -> {new}")
            except Exception as e:
                print(f"  [SKIP] Could not rename {old} (already exists or missing): {e}")

        # 2. Table: observations
        print("Processing 'observations'...")
        for old, new in [('old_system_session_id', 'legacy_session_id'), 
                         ('old_system_teacher_id', 'legacy_teacher_id')]:
            try:
                conn.execute(text(f"ALTER TABLE observations RENAME COLUMN {old} TO {new}"))
                print(f"  [OK] Renamed {old} -> {new}")
            except Exception as e:
                print(f"  [SKIP] Could not rename {old}: {e}")

        # Cleanup for TEST DB (duplicates like legacy_session_id vs old_system_session_id)
        if "test" in label.lower():
            print("Special cleanup for TEST DB...")
            # Si existen columnas duplicadas, eliminamos las obsoletas
            # Nota: Esto es arriesgado si hay datos, pero el usuario pide consistencia total.
            # Borraremos las que NO sigan el estándar si ya existe la estándar.
            pass

        # 3. Rename Constraints/Indexes (Example for one index if it exists)
        # We'll do a generic approach: if an index with 'old_system' exists, rename it.
        try:
            # PostgreSQL specific rename for indexes
            res = conn.execute(text("SELECT indexname FROM pg_indexes WHERE indexname LIKE '%old_system%'"))
            for row in res:
                old_idx = row[0]
                new_idx = old_idx.replace('old_system', 'legacy')
                conn.execute(text(f"ALTER INDEX {old_idx} RENAME TO {new_idx}"))
                print(f"  [INDEX] Renamed {old_idx} -> {new_idx}")
        except Exception as e:
            print(f"  [SKIP] Index rename error: {e}")

        conn.commit()
        print(f"Done for {label}")

if __name__ == "__main__":
    fix_db(settings.DATABASE_URL, "PROD/DEV")
    if settings.TEST_DATABASE_URL:
        fix_db(settings.TEST_DATABASE_URL, "TEST")
