import psycopg
import logging
from app.database import SQLALCHEMY_DATABASE_URL

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("secure_purge")

def column_exists(cur, table, column):
    cur.execute(f"SELECT 1 FROM information_schema.columns WHERE table_name='{table}' AND column_name='{column}'")
    return cur.fetchone() is not None

def safe_drop(cur, table, col):
    if column_exists(cur, table, col):
        logger.info(f"  -> Eliminando columna '{col}' en '{table}'")
        cur.execute(f"ALTER TABLE {table} DROP COLUMN {col} CASCADE;")

def execute_final_secure_purge():
    conn_str = SQLALCHEMY_DATABASE_URL.replace("postgresql://", "postgresql://")
    
    try:
        with psycopg.connect(conn_str) as conn:
            with conn.cursor() as cur:
                logger.info("--- INICIANDO FASE DE SEGURIDAD (TABLAS TEMPORALES) ---")
                
                # 0. Crear tablas de respaldo internas
                cur.execute("DROP TABLE IF EXISTS backup_rpt_planilla;")
                cur.execute("CREATE TABLE backup_rpt_planilla AS SELECT * FROM rpt_planilla;")
                logger.info("  OK: backup_rpt_planilla creada.")
                
                cur.execute("DROP TABLE IF EXISTS backup_subjects;")
                cur.execute("CREATE TABLE backup_subjects AS SELECT * FROM subjects;")
                logger.info("  OK: backup_subjects creada.")

                logger.info("--- INICIANDO PURGA ARQUITECTÓNICA FINAL ---")

                # 1. Tablas Maestras (Sólo UUID)
                # Purgamos legacy_id en las tablas listadas por el usuario
                master_tables = ["subjects", "rpt_planilla", "grades", "buildings", "roles", "permissions", "break_config", "lunch_config"]
                for table in master_tables:
                    logger.info(f"Procesando tabla soberana: {table}")
                    safe_drop(cur, table, "legacy_id")
                    safe_drop(cur, table, "uid")

                # 2. Tablas Transaccionales (Híbridas)
                # Nos aseguramos de limpiar residuos *_uid que ya fueron migrados a *_id (UUID)
                # Nota: El Grand Swap anterior ya debería haber renombrado la mayoría.
                trans_tables = ["teachers", "users", "lessons", "schedule_sessions", "observations", "classes"]
                for table in trans_tables:
                    logger.info(f"Limpiando residuos en tabla transaccional: {table}")
                    safe_drop(cur, table, "uid")
                
                # Relaciones específicas residuales
                safe_drop(cur, "classes", "grade_uid")
                safe_drop(cur, "schedule_sessions", "lesson_uid")
                safe_drop(cur, "observations", "session_uid")
                safe_drop(cur, "observations", "teacher_uid")
                safe_drop(cur, "observations", "user_uid")
                safe_drop(cur, "observations", "replacement_teacher_uid")

                logger.info("--- PURGA FÍSICA SOBERANA COMPLETADA ---")
                conn.commit()

    except Exception as e:
        logger.error(f"FALLO CRÍTICO EN PURGA: {e}")
        raise

if __name__ == "__main__":
    execute_final_secure_purge()
