import sys
import os
from sqlalchemy import create_engine, inspect, text

# Añadir el path del proyecto para importar app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.config import settings
from app.models import Base
import app.models.schedule # Asegurar que Lesson está cargado

def audit_lessons():
    engine = create_engine(settings.DATABASE_URL)
    inspector = inspect(engine)
    
    print(f"URL: {settings.DATABASE_URL}")
    
    model_table = Base.metadata.tables['lessons']
    model_cols = [c.name for c in model_table.columns]
    print(f"Columnas en MODELO (Lesson): {model_cols}")
    
    db_cols = [c['name'] for c in inspector.get_columns('lessons')]
    print(f"Columnas en DB (lessons): {db_cols}")
    
    missing = set(model_cols) - set(db_cols)
    print(f"FALTANTES: {missing}")

if __name__ == "__main__":
    audit_lessons()
