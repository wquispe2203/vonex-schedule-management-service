import psycopg
import logging
from app.database import SQLALCHEMY_DATABASE_URL

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("migration")

def run_final_uuid_migration():
    # Convertir URL de SQLAlchemy a formato libpq de psycopg
    # postgresql://user:pass@host/db -> host=... dbname=... user=... password=...
    conn_str = SQLALCHEMY_DATABASE_URL.replace("postgresql://", "postgresql://")
    
    try:
        with psycopg.connect(conn_str) as conn:
            with conn.cursor() as cur:
                logger.info("--- Iniciando Migración Estructural UUID (Fase Final) ---")
                
                # 1. Preparar campos UID en tablas que faltan
                logger.info("Fase 1: Preparando columnas UUID en tablas secundarias...")
                cur.execute("ALTER TABLE classes ADD COLUMN IF NOT EXISTS uid UUID DEFAULT gen_random_uuid();")
                cur.execute("ALTER TABLE schedule_sessions ADD COLUMN IF NOT EXISTS uid UUID DEFAULT gen_random_uuid();")
                
                # 2. Migración de TEACHERS (EL CORE)
                logger.info("Fase 2: Transformando Identidad de TEACHERS...")
                # Eliminar restricciones antiguas (asumiendo nombres estándar de SQLAlchemy/Alembic)
                cur.execute("ALTER TABLE teachers DROP CONSTRAINT IF EXISTS teachers_pkey CASCADE;")
                cur.execute("ALTER TABLE teachers RENAME COLUMN id TO legacy_id;")
                cur.execute("ALTER TABLE teachers RENAME COLUMN uid TO id;")
                cur.execute("ALTER TABLE teachers ADD PRIMARY KEY (id);")
                
                # 3. Migración de CLASSES
                logger.info("Fase 3: Transformando Identidad de CLASSES...")
                cur.execute("ALTER TABLE classes DROP CONSTRAINT IF EXISTS classes_pkey CASCADE;")
                cur.execute("ALTER TABLE classes RENAME COLUMN id TO legacy_id;")
                cur.execute("ALTER TABLE classes RENAME COLUMN uid TO id;")
                cur.execute("ALTER TABLE classes ADD PRIMARY KEY (id);")
                
                # 4. Migración de SCHEDULE_SESSIONS
                logger.info("Fase 4: Transformando Identidad de SESSIONS...")
                cur.execute("ALTER TABLE schedule_sessions DROP CONSTRAINT IF EXISTS schedule_sessions_pkey CASCADE;")
                cur.execute("ALTER TABLE schedule_sessions RENAME COLUMN id TO legacy_id;")
                cur.execute("ALTER TABLE schedule_sessions RENAME COLUMN uid TO id;")
                cur.execute("ALTER TABLE schedule_sessions ADD PRIMARY KEY (id);")

                # 5. Migración de OBSERVATIONS
                logger.info("Fase 5: Transformando Identidad de OBSERVATIONS...")
                cur.execute("ALTER TABLE observations DROP CONSTRAINT IF EXISTS observations_pkey CASCADE;")
                cur.execute("ALTER TABLE observations RENAME COLUMN id TO legacy_id;")
                cur.execute("ALTER TABLE observations RENAME COLUMN uid TO id;")
                cur.execute("ALTER TABLE observations ADD PRIMARY KEY (id);")
                
                # 6. Sincronización de Foreign Keys (Mantenimiento de compatibilidad)
                logger.info("Fase 6: Actualizando referencias cruzadas...")
                # Ejemplo: Lesson.teacher_id -> Lesson.legacy_teacher_id
                cur.execute("ALTER TABLE lessons RENAME COLUMN teacher_id TO legacy_teacher_id;")
                cur.execute("ALTER TABLE lessons ADD COLUMN teacher_id UUID;")
                cur.execute("UPDATE lessons l SET teacher_id = t.id FROM teachers t WHERE l.legacy_teacher_id = t.legacy_id;")
                
                # Observations -> session_id
                cur.execute("ALTER TABLE observations RENAME COLUMN session_id TO legacy_session_id;")
                cur.execute("ALTER TABLE observations ADD COLUMN session_id UUID;")
                cur.execute("UPDATE observations o SET session_id = s.id FROM schedule_sessions s WHERE o.legacy_session_id = s.legacy_id;")

                logger.info("--- Migración Completada Exitosamente ---")
                conn.commit()
                
    except Exception as e:
        logger.error(f"Fallo crítico en migración: {str(e)}")
        raise

if __name__ == "__main__":
    run_final_uuid_migration()
