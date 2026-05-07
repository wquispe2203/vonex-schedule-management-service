import sys
import os
from sqlalchemy import create_engine, inspect, text

# Añadir el path del proyecto para importar app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.config import settings
from app.models import Base
import app.models.schedule

def audit_test_db():
    url = settings.TEST_DATABASE_URL
    print(f"URL de Prueba: {url}")
    if not url:
        print("No hay URL de prueba configurada.")
        return

    engine = create_engine(url)
    inspector = inspect(engine)
    
    db_tables = inspector.get_table_names()
    print(f"Tablas en DB de Prueba: {db_tables}")
    
    if 'lessons' in db_tables:
        db_cols = [c['name'] for c in inspector.get_columns('lessons')]
        print(f"Columnas en DB de Prueba (lessons): {db_cols}")
        
        model_table = Base.metadata.tables['lessons']
        model_cols = [c.name for c in model_table.columns]
        
        missing = set(model_cols) - set(db_cols)
        print(f"FALTANTES en Prueba: {missing}")
    else:
        print("La tabla 'lessons' no existe en la DB de prueba.")

if __name__ == "__main__":
    audit_test_db()
