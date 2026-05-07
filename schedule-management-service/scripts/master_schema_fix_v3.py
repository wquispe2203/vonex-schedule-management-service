import sys
import os
from sqlalchemy import create_engine, text

# Add project path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.config import settings

def run_sql(conn, sql):
    try:
        conn.execute(text(sql))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"  [ERROR SQL] {sql}: {e}")
        return False

def fix_db(url, label):
    print(f"\n--- FIXING DATABASE: {label} ---")
    engine = create_engine(url)
    conn = engine.connect()
    
    tasks = {
        'lessons': [
            ('old_system_subject_id', 'legacy_subject_id'),
            ('old_system_teacher_id', 'legacy_teacher_id'),
            ('old_system_class_id', 'legacy_class_id')
        ],
        'observations': [
            ('old_system_session_id', 'legacy_session_id'),
            ('old_system_teacher_id', 'legacy_teacher_id')
        ]
    }

    for table, columns in tasks.items():
        print(f"Table: {table}")
        for old, new in columns:
            # Query columns exactly as they are in DB
            q = text(f"SELECT column_name FROM information_schema.columns WHERE table_name=:t AND column_name=:c")
            res_old = conn.execute(q, {"t": table, "c": old}).first()
            res_new = conn.execute(q, {"t": table, "c": new}).first()
            
            if res_old:
                if res_new:
                    print(f"  [CLEANUP] Both '{old}' and '{new}' exist in '{table}'. Migrating data and dropping '{old}'...")
                    # Opcional: Migrar datos si el nuevo está nulo
                    run_sql(conn, f"UPDATE {table} SET {new} = {old} WHERE {new} IS NULL")
                    run_sql(conn, f"ALTER TABLE {table} DROP COLUMN {old}")
                else:
                    print(f"  [RENAME] '{old}' -> '{new}' in '{table}'")
                    run_sql(conn, f"ALTER TABLE {table} RENAME COLUMN {old} TO {new}")
            else:
                if res_new:
                    print(f"  [OK] '{new}' already exists in '{table}'.")
                else:
                    print(f"  [WARN] Neither '{old}' nor '{new}' found in '{table}'.")

    conn.close()
    print(f"Done for {label}")

if __name__ == "__main__":
    fix_db(settings.DATABASE_URL, "PROD/DEV")
    if settings.TEST_DATABASE_URL:
        fix_db(settings.TEST_DATABASE_URL, "TEST")
