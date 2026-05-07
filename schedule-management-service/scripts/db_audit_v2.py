import sys
import os
from sqlalchemy import create_engine, inspect, text

# Añadir el path del proyecto para importar app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.config import settings
from app.models import Base
# Importar explícitamente para asegurar registro en Base.metadata
import app.models.user
import app.models.teacher
import app.models.schedule
import app.models.config
import app.models.reports
import app.models.infrastructure

def audit_database():
    engine = create_engine(settings.DATABASE_URL)
    inspector = inspect(engine)
    
    print("=== AUDITORÍA PROFUNDA DE BASE DE DATOS ===")
    print(f"Database: {settings.DATABASE_URL.split('@')[-1]}")
    
    differences = []
    
    # Tablas en DB
    db_tables = inspector.get_table_names()
    
    # Tablas en Modelos
    model_tables = Base.metadata.tables
    
    print(f"Tablas detectadas en modelos: {list(model_tables.keys())}")
    
    for table_name, model_table in model_tables.items():
        print(f"\nAnalizando tabla: {table_name}")
        
        if table_name not in db_tables:
            print(f"  [CRÍTICO] Tabla '{table_name}' no existe en la base de datos.")
            differences.append(f"CREATE TABLE {table_name}")
            continue
            
        db_cols = {c['name']: c for c in inspector.get_columns(table_name)}
        model_cols = model_table.columns
        
        for col in model_cols:
            if col.name not in db_cols:
                print(f"  [ERROR] Columna '{col.name}' faltante en DB.")
                differences.append(f"ALTER TABLE {table_name} ADD COLUMN {col.name} {col.type}")
            else:
                # Opcional: verificar tipos si es necesario
                pass
                
        # Verificar columnas extra en DB (posibles residuos)
        extra_cols = set(db_cols.keys()) - set(c.name for c in model_cols)
        if extra_cols:
            print(f"  [AVISO] Columnas extra en DB: {extra_cols}")

    print("\n=== SCRIPT DE CORRECCIÓN SUGERIDO ===")
    if not differences:
        print("-- No se requieren cambios.")
    else:
        for diff in differences:
            print(f"{diff};")

if __name__ == "__main__":
    audit_database()
