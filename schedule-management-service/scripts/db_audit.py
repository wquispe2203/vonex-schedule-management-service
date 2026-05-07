import sys
import os
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.schema import MetaData

# Añadir el path del proyecto para importar app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.config import settings
from app.models import Base

def audit_database():
    engine = create_engine(settings.DATABASE_URL)
    inspector = inspect(engine)
    
    # Obtener metadata de los modelos
    model_metadata = Base.metadata
    
    print("=== AUDITORÍA DE BASE DE DATOS ===")
    print(f"Database: {settings.DATABASE_URL.split('@')[-1]}")
    
    differences = []
    
    # 1. Verificar tablas
    db_tables = inspector.get_table_names()
    model_tables = model_metadata.tables.keys()
    
    missing_in_db = set(model_tables) - set(db_tables)
    extra_in_db = set(db_tables) - set(model_tables) - {'alembic_version'}
    
    if missing_in_db:
        print(f"\n[!] Tablas faltantes en DB: {missing_in_db}")
        for table in missing_in_db:
            differences.append(f"CREATE TABLE {table}")
    
    # 2. Verificar columnas en cada tabla
    for table_name in model_tables:
        if table_name in missing_in_db:
            continue
            
        model_table = model_metadata.tables[table_name]
        db_columns = {c['name']: c for c in inspector.get_columns(table_name)}
        model_columns = model_table.columns
        
        missing_cols = []
        for col in model_columns:
            if col.name not in db_columns:
                missing_cols.append(col.name)
                differences.append(f"ALTER TABLE {table_name} ADD COLUMN {col.name} {col.type}")
        
        if missing_cols:
            print(f"\n[!] Tabla '{table_name}' - Columnas faltantes: {missing_cols}")

    print("\n=== RESUMEN DE DIFERENCIAS ===")
    if not differences:
        print("No se encontraron discrepancias estructurales.")
    else:
        for diff in differences:
            print(f"- {diff}")
            
    # 3. Verificar Alembic Version
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version_num FROM alembic_version"))
            version = result.scalar()
            print(f"\n[i] Versión actual de Alembic en DB: {version}")
    except Exception as e:
        print("\n[!] No se pudo obtener la versión de Alembic.")

if __name__ == "__main__":
    audit_database()
