import sys
import os
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.schema import MetaData

# Add project path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.config import settings
from app.models import Base

def audit_db(url, label):
    print(f"\n=== AUDIT: {label} ===")
    print(f"URL: {url}")
    
    engine = create_engine(url)
    inspector = inspect(engine)
    
    try:
        with engine.connect() as conn:
            version = conn.execute(text("SELECT version_num FROM alembic_version")).scalar()
            print(f"Current Alembic Version: {version}")
    except Exception as e:
        print(f"Could not get alembic version: {e}")
        
    db_tables = inspector.get_table_names()
    model_tables = Base.metadata.tables.keys()
    
    # Check tables
    missing_tables = set(model_tables) - set(db_tables)
    if missing_tables:
        print(f"[!] MISSING TABLES: {missing_tables}")
        
    # Check columns, types, and constraints
    for table_name in model_tables:
        if table_name not in db_tables:
            continue
            
        model_table = Base.metadata.tables[table_name]
        db_columns = {c['name']: c for c in inspector.get_columns(table_name)}
        model_columns = model_table.columns
        
        for col in model_columns:
            if col.name not in db_columns:
                print(f"[!] {table_name}: MISSING COLUMN '{col.name}'")
            else:
                # Basic type check
                db_type = str(db_columns[col.name]['type']).lower()
                model_type = str(col.type).lower()
                # Simplified check as types might vary slightly (e.g., VARCHAR vs String)
                if 'int' in model_type and 'int' not in db_type:
                    print(f"[!] {table_name}.{col.name}: TYPE MISMATCH (Model: {model_type}, DB: {db_type})")
        
        # Check PK
        pk = inspector.get_pk_constraint(table_name)
        if not pk.get('constrained_columns'):
            print(f"[!] {table_name}: NO PRIMARY KEY")
            
        # Check Indices
        indices = inspector.get_indexes(table_name)
        index_names = [idx['name'] for idx in indices]
        print(f"  {table_name} indices: {index_names}")

def main():
    # Prod/Dev DB
    audit_db(settings.DATABASE_URL, "PRODUCTION/DEV")
    
    # Test DB
    if settings.TEST_DATABASE_URL:
        audit_db(settings.TEST_DATABASE_URL, "TEST")

if __name__ == "__main__":
    main()
