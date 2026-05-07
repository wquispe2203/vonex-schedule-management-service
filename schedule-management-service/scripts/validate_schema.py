import sys
import os
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.schema import MetaData

# Add project path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.config import settings
from app.models import Base

def validate_schema(url, label, fail_on_diff=False):
    print(f"\n[AUDIT] Validating: {label}")
    try:
        engine = create_engine(url)
        inspector = inspect(engine)
    except Exception as e:
        print(f"X Connection failed: {e}")
        if fail_on_diff: sys.exit(1)
        return

    db_tables = inspector.get_table_names()
    model_tables = Base.metadata.tables.keys()
    
    errors = []
    
    # 1. Missing Tables
    missing_tables = set(model_tables) - set(db_tables)
    if missing_tables:
        errors.append(f"Missing tables in DB: {missing_tables}")
        
    # 2. Column Audit
    for table_name in model_tables:
        if table_name not in db_tables: continue
        
        model_table = Base.metadata.tables[table_name]
        db_cols = {c['name']: c for c in inspector.get_columns(table_name)}
        
        for col in model_table.columns:
            if col.name not in db_cols:
                errors.append(f"Table '{table_name}': Missing column '{col.name}'")
            else:
                # Type check
                db_type = str(db_cols[col.name]['type']).lower()
                model_type = str(col.type).lower()
                # Simplified type check
                if 'uuid' in model_type and 'uuid' not in db_type:
                    errors.append(f"Table '{table_name}': Type mismatch for '{col.name}' (Model: UUID, DB: {db_type})")

    # 3. Naming Convention Check (STRICT)
    # Ensure no 'old_system_' columns exist if we expect 'legacy_'
    for table_name in db_tables:
        db_cols = [c['name'] for c in inspector.get_columns(table_name)]
        bad_cols = [c for c in db_cols if c.startswith('old_system_')]
        if bad_cols:
            errors.append(f"Table '{table_name}': Found legacy naming convention in columns: {bad_cols}")

    if errors:
        print(f"\n--- {label} ERRORS DETECTED ---")
        for err in errors:
            print(f"X {err}")
        if fail_on_diff:
            print(f"\n[FAIL] Validation for {label} failed.")
            sys.exit(1)
    else:
        print(f"--- {label} SCHEMA IS 100% VALID ---")

def main():
    fail_fast = "--fail" in sys.argv
    validate_schema(settings.DATABASE_URL, "PRODUCTION/DEV", fail_on_diff=fail_fast)
    if settings.TEST_DATABASE_URL:
        validate_schema(settings.TEST_DATABASE_URL, "TEST", fail_on_diff=fail_fast)

if __name__ == "__main__":
    main()
