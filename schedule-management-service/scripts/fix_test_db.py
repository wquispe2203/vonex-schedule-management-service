import sys
import os
from sqlalchemy import create_engine, text

# Añadir el path del proyecto para importar app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.config import settings

def fix_test_db():
    url = settings.TEST_DATABASE_URL
    if not url:
        print("No TEST_DATABASE_URL defined.")
        return
        
    print(f"Sincronizando DB de Prueba: {url}")
    engine = create_engine(url)
    
    with engine.connect() as conn:
        # 1. Tabla lessons: Renombrar o Agregar
        print("Corrigiendo tabla 'lessons'...")
        # Renombrar si existen bajo el nombre antiguo
        try:
            conn.execute(text("ALTER TABLE lessons RENAME COLUMN legacy_subject_id TO old_system_subject_id"))
            print("  - Renombrado legacy_subject_id -> old_system_subject_id")
        except: pass
        try:
            conn.execute(text("ALTER TABLE lessons RENAME COLUMN legacy_teacher_id TO old_system_teacher_id"))
            print("  - Renombrado legacy_teacher_id -> old_system_teacher_id")
        except: pass
        try:
            conn.execute(text("ALTER TABLE lessons RENAME COLUMN legacy_class_id TO old_system_class_id"))
            print("  - Renombrado legacy_class_id -> old_system_class_id")
        except: pass
        
        # Asegurar que existen (por si no se renombraron)
        conn.execute(text("ALTER TABLE lessons ADD COLUMN IF NOT EXISTS old_system_subject_id INTEGER"))
        conn.execute(text("ALTER TABLE lessons ADD COLUMN IF NOT EXISTS old_system_teacher_id INTEGER"))
        conn.execute(text("ALTER TABLE lessons ADD COLUMN IF NOT EXISTS old_system_class_id INTEGER"))

        # 2. Tabla observations: Agregar faltantes
        print("Corrigiendo tabla 'observations'...")
        conn.execute(text("ALTER TABLE observations ADD COLUMN IF NOT EXISTS old_system_session_id INTEGER"))
        conn.execute(text("ALTER TABLE observations ADD COLUMN IF NOT EXISTS old_system_teacher_id INTEGER"))
        conn.execute(text("ALTER TABLE observations ADD COLUMN IF NOT EXISTS discount_type VARCHAR(50) DEFAULT 'SIMPLE'"))
        conn.execute(text("ALTER TABLE observations ADD COLUMN IF NOT EXISTS teacher_uid UUID"))
        conn.execute(text("ALTER TABLE observations ADD COLUMN IF NOT EXISTS replacement_teacher_uid UUID"))
        conn.execute(text("ALTER TABLE observations ADD COLUMN IF NOT EXISTS description TEXT"))
        conn.execute(text("ALTER TABLE observations ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()"))

        # 3. Tabla teachers: Índice para matching
        print("Corrigiendo tabla 'teachers'...")
        try:
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_teachers_normalized_for_match ON teachers (normalized_for_match)"))
            print("  - Índice ix_teachers_normalized_for_match creado.")
        except: pass

        conn.commit()
        print("\nSincronización finalizada.")

if __name__ == "__main__":
    fix_test_db()
