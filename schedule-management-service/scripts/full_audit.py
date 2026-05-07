import sys
import os
from sqlalchemy import create_engine, inspect, text

# Añadir el path del proyecto para importar app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.config import settings
from app.models import Base
import app.models # Cargar todos

def full_audit(url, label):
    print(f"\n=== AUDITORÍA {label} ===")
    print(f"URL: {url}")
    
    engine = create_engine(url)
    inspector = inspect(engine)
    db_tables = inspector.get_table_names()
    
    differences = []
    
    for table_name, model_table in Base.metadata.tables.items():
        if table_name not in db_tables:
            differences.append(f"MISSING TABLE: {table_name}")
            continue
            
        db_cols = {c['name']: c for c in inspector.get_columns(table_name)}
        model_cols = model_table.columns
        
        for col in model_cols:
            if col.name not in db_cols:
                differences.append(f"MISSING COLUMN in {table_name}: {col.name} ({col.type})")
                
    if not differences:
        print("Todo sincronizado.")
    else:
        for diff in differences:
            print(f"[!] {diff}")

if __name__ == "__main__":
    full_audit(settings.DATABASE_URL, "PRODUCCIÓN/DEV")
    if settings.TEST_DATABASE_URL:
        full_audit(settings.TEST_DATABASE_URL, "TEST")
