import psycopg
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

def execute_sovereign_purge():
    conn_str = SQLALCHEMY_DATABASE_URL.replace("postgresql://", "postgresql://")
    
    try:
        with psycopg.connect(conn_str) as conn:
            with conn.cursor() as cur:
                logger.info("--- INICIANDO PURGA ARQUITECTÓNICA SOBERANA (Fase Final) ---")

                # 1. Purgar IDs Legacy en Tablas Maestras y Derivadas (Soberanía UUID)
                sovereign_tables = ["subjects", "rpt_planilla", "grades", "buildings", "roles", "permissions", "break_config", "lunch_config"]
                for table in sovereign_tables:
                    logger.info(f"Procesando tabla soberana: {table}")
                    safe_drop(cur, table, "legacy_id")
                    # También purgamos cualquier rastro de 'uid' si quedó perdido
                    safe_drop(cur, table, "uid")

                # 2. Estandarización de Nomenclatura Global (Eliminación definitiva de sufijos _uid)
                logger.info("Estandarizando nomenclatura de relaciones...")
                
                # Classes: grade_uid -> grade_id (ya hecho en pasos previos but safer to check)
                safe_drop(cur, "classes", "grade_uid") 
                
                # Sessions: lesson_uid -> lesson_id
                safe_drop(cur, "schedule_sessions", "lesson_uid")
                
                # Observations: session_uid -> session_id
                safe_drop(cur, "observations", "session_uid")
                safe_drop(cur, "observations", "teacher_uid")
                safe_drop(cur, "observations", "user_uid")
                safe_drop(cur, "observations", "replacement_teacher_uid")

                # 3. Limpieza de Tabla de Auditoría (Estandarización de nombres de FK)
                if column_exists(cur, "audit_logs", "usuario_id"):
                    if column_exists(cur, "audit_logs", "user_id"):
                        safe_drop(cur, "audit_logs", "usuario_id")
                
                logger.info("--- PURGA SOBERANA COMPLETADA ---")
                conn.commit()

    except Exception as e:
        logger.error(f"FALLO CRÍTICO EN PURGA SOBERANA: {e}")
        raise

if __name__ == "__main__":
    execute_sovereign_purge()
