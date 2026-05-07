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
        # print(f"  [ERROR] {sql}: {e}")
        return False

def fix_db(url, label):
    print(f"\n--- FIXING DATABASE: {label} ---")
    engine = create_engine(url)
    conn = engine.connect()
    
    # Tables and their renames
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
            # Check if old exists
            res = conn.execute(text(f"SELECT 1 FROM information_schema.columns WHERE table_name='{table}' AND column_name='{old}'")).first()
            if res:
                # Check if new exists
                res_new = conn.execute(text(f"SELECT 1 FROM information_schema.columns WHERE table_name='{table}' AND column_name='{new}'")).first()
                if res_new:
                    print(f"  [CLEANUP] Both {old} and {new} exist. Dropping {old}...")
                    run_sql(conn, f"ALTER TABLE {table} DROP COLUMN {old}")
                else:
                    print(f"  [RENAME] {old} -> {new}")
                    run_sql(conn, f"ALTER TABLE {table} RENAME COLUMN {old} TO {new}")
            else:
                print(f"  [SKIP] Column {old} not found.")

    # Index rename
    print("Renaming indexes...")
    try:
        res = conn.execute(text("SELECT indexname FROM pg_indexes WHERE indexname LIKE '%old_system%'")).all()
        for row in res:
            old_idx = row[0]
            new_idx = old_idx.replace('old_system', 'legacy')
            print(f"  [INDEX] {old_idx} -> {new_idx}")
            run_sql(conn, f"ALTER INDEX {old_idx} RENAME TO {new_idx}")
    except: pass

    conn.close()
    print(f"Done for {label}")

if __name__ == "__main__":
    fix_db(settings.DATABASE_URL, "PROD/DEV")
    if settings.TEST_DATABASE_URL:
        fix_db(settings.TEST_DATABASE_URL, "TEST")
