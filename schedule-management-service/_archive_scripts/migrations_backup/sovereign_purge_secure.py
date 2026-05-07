import psycopg
import datetime
import logging
from app.database import SQLALCHEMY_DATABASE_URL

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sovereign_purge")

def column_exists(cur, table, column):
    cur.execute(f"SELECT 1 FROM information_schema.columns WHERE table_name='{table}' AND column_name='{column}'")
    return cur.fetchone() is not None

def safe_drop(cur, table, col):
    if column_exists(cur, table, col):
        logger.info(f"  -> Eliminando columna '{col}' en '{table}'")
        cur.execute(f"ALTER TABLE {table} DROP COLUMN {col} CASCADE;")

def execute_sovereign_purge_secure():
    conn_str = SQLALCHEMY_DATABASE_URL.replace("postgresql://", "postgresql://")
    date_suffix = datetime.datetime.now().strftime("%Y_%m_%d")
    
    try:
        with psycopg.connect(conn_str) as conn:
            with conn.cursor() as cur:
                logger.info(f"--- FASE 0: SEGURIDAD (RESPALDO INTERNO {date_suffix}) ---")
                
                # Crear copias espejo con fecha
                for table in ["rpt_planilla", "subjects"]:
                    backup_table = f"backup_{table}_{date_suffix}"
                    cur.execute(f"DROP TABLE IF EXISTS {backup_table};")
                    cur.execute(f"CREATE TABLE {backup_table} AS SELECT * FROM {table};")
                    logger.info(f"  OK: {backup_table} creada.")

                logger.info("--- FASE 1: PURGA ARQUITECTÓNICA SOBERANA ---")

                # 1. Purgar IDs Legacy en Tablas Maestras (Sólo UUID)
                # Según plan: subjects, rpt_planilla, grades, etc.
                master_tables = ["subjects", "rpt_planilla", "grades", "buildings", "roles", "permissions", "break_config", "lunch_config"]
                for table in master_tables:
                    logger.info(f"Purgando tabla maestra: {table}")
                    safe_drop(cur, table, "legacy_id")
                    safe_drop(cur, table, "uid")

                # 2. Limpiar columnas residuales de transición en todo el esquema
                logger.info("Limpiando columnas residuales *_uid")
                
                # Tablas transaccionales
                trans_tables = ["teachers", "users", "lessons", "schedule_sessions", "observations", "classes"]
                for table in trans_tables:
                    safe_drop(cur, table, "uid")
                
                # Relaciones específicas
                safe_drop(cur, "classes", "grade_uid")
                safe_drop(cur, "schedule_sessions", "lesson_uid")
                safe_drop(cur, "observations", "session_uid")
                safe_drop(cur, "observations", "teacher_uid")
                safe_drop(cur, "observations", "user_uid")
                safe_drop(cur, "observations", "replacement_teacher_uid")

                logger.info("--- PURGA SOBERANA COMPLETADA CON ÉXITO ---")
                conn.commit()

    except Exception as e:
        logger.error(f"FALLO CRÍTICO EN LA PURGA: {e}")
        raise

if __name__ == "__main__":
    execute_sovereign_purge_secure()
