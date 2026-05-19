import os
import sys
import json
from pathlib import Path
from sqlalchemy import create_engine, text

# Add project path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from app.core.config import settings
    db_url = settings.DATABASE_URL
except Exception as e:
    db_url = os.getenv("DATABASE_URL", "postgresql://postgres:C%40rden4s2k24@localhost:5432/schedule_db")

engine = create_engine(db_url)
backup_file = Path("d:/Desktop/MOD HOR/schedule-management-service/backup_json/pre_cleanup_academic_backup.json")

if not backup_file.exists():
    print(f"[ERROR] Backup snapshot not found at {backup_file}")
    sys.exit(1)

with open(backup_file, "r", encoding="utf-8") as f:
    snapshot = json.load(f)

# Tables in strict hierarchical order of dependencies for restoration
tables_to_restore = [
    'permissions', 'roles', 'users', 'user_roles', 'role_permissions',
    'xml_uploads', 'teacher_name_overrides', 'cards', 'teachers', 
    'grades', 'classes', 'subjects', 'lessons', 'schedule_sessions', 
    'observations', 'rpt_planilla', 'lunch_config', 'buildings', 
    'break_config', 'recess_rules'
]

print("--- [EMERGENCY ROLLBACK IN PROGRESS] ---")
print("Opening transaction block...")

with engine.begin() as conn:
    # Disable triggers/constraints for simple restoration if supported, or truncate in reverse order
    print("Step 1: Truncating tables in reverse order...")
    for table in reversed(tables_to_restore):
        try:
            conn.execute(text(f"TRUNCATE TABLE {table} CASCADE"))
            print(f"  Truncated '{table}' successfully.")
        except Exception as e:
            print(f"  Failed to truncate '{table}': {e}")
            
    # Insert rows in forward order
    print("\nStep 2: Restoring data rows from JSON snapshot...")
    for table in tables_to_restore:
        rows = snapshot.get(table, [])
        if not rows:
            print(f"  No data rows to restore for table '{table}'.")
            continue
            
        # Get column list
        cols = list(rows[0].keys())
        cols_str = ", ".join(cols)
        bind_str = ", ".join([f":{c}" for c in cols])
        
        insert_query = text(f"INSERT INTO {table} ({cols_str}) VALUES ({bind_str})")
        
        try:
            conn.execute(insert_query, rows)
            print(f"  Successfully restored {len(rows)} rows to '{table}'.")
        except Exception as e:
            print(f"  Failed to restore rows to '{table}': {e}")
            raise e

print("\n--- [EMERGENCY ROLLBACK SUCCESSFUL] ---")
print("Database has been completely reverted to its pre-cleanup state!")
