import psycopg
import logging
from app.database import SQLALCHEMY_DATABASE_URL

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("consolidation")

def column_exists(cur, table, column):
    cur.execute(f"SELECT 1 FROM information_schema.columns WHERE table_name='{table}' AND column_name='{column}'")
    return cur.fetchone() is not None

def safe_rename(cur, table, old_col, new_col):
    if column_exists(cur, table, old_col) and not column_exists(cur, table, new_col):
        logger.info(f"  -> Renombrando {old_col} a {new_col} en {table}")
        cur.execute(f"ALTER TABLE {table} RENAME COLUMN {old_col} TO {new_col};")
    else:
        logger.info(f"  -> Salteando rename {old_col} -> {new_col} en {table} (ya existe el destino o no existe el origen)")

def safe_drop(cur, table, col):
    if column_exists(cur, table, col):
        logger.info(f"  -> Eliminando columna {col} en {table}")
        cur.execute(f"ALTER TABLE {table} DROP COLUMN {col};")

def execute_final_consolidation():
    conn_str = SQLALCHEMY_DATABASE_URL.replace("postgresql://", "postgresql://")
    
    try:
        with psycopg.connect(conn_str) as conn:
            with conn.cursor() as cur:
                logger.info("--- INICIANDO CONSOLIDACIÓN FINAL (MODO RESILIENTE) ---")

                # 1. CLASSES
                logger.info("Estandarizando tabla CLASSES...")
                safe_rename(cur, "classes", "grade_id", "legacy_grade_id")
                safe_rename(cur, "classes", "grade_uid", "grade_id")
                
                # 2. SCHEDULE_SESSIONS
                logger.info("Estandarizando tabla SCHEDULE_SESSIONS...")
                safe_rename(cur, "schedule_sessions", "lesson_id", "legacy_lesson_id")
                safe_rename(cur, "schedule_sessions", "lesson_uid", "lesson_id")

                # 3. OBSERVATIONS
                logger.info("Estandarizando tabla OBSERVATIONS...")
                safe_rename(cur, "observations", "session_id", "legacy_session_id")
                safe_rename(cur, "observations", "session_uid", "session_id")
                safe_rename(cur, "observations", "teacher_id", "legacy_teacher_id")
                safe_rename(cur, "observations", "teacher_uid", "teacher_id")
                
                # 4. LIMPIEZA DE COLUMNAS UID RESIDUALES
                logger.info("Limpiando columnas UID/ID residuales...")
                tables = ["teachers", "users", "classes", "subjects", "lessons", "cards", "schedule_sessions"]
                for table in tables:
                    # Si 'uid' existe, ya no la necesitamos porque 'id' es el UUID
                    safe_drop(cur, table, "uid")

                logger.info("--- CONSOLIDACIÓN FÍSICA COMPLETADA ---")
                conn.commit()

    except Exception as e:
        logger.error(f"FALLO CRÍTICO EN CONSOLIDACIÓN: {e}")
        raise

if __name__ == "__main__":
    execute_final_consolidation()
