import psycopg
import logging
from app.database import SQLALCHEMY_DATABASE_URL

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("master_purge")

def column_exists(cur, table, column):
    cur.execute(f"SELECT 1 FROM information_schema.columns WHERE table_name='{table}' AND column_name='{column}'")
    return cur.fetchone() is not None

def safe_drop(cur, table, col):
    if column_exists(cur, table, col):
        logger.info(f"  -> Eliminando {col} en {table}")
        cur.execute(f"ALTER TABLE {table} DROP COLUMN {col} CASCADE;")

def execute_final_purge():
    conn_str = SQLALCHEMY_DATABASE_URL.replace("postgresql://", "postgresql://")
    
    try:
        with psycopg.connect(conn_str) as conn:
            with conn.cursor() as cur:
                logger.info("--- INICIANDO PURGA ARQUITECTÓNICA FINAL (FIX PK) ---")

                # 1. Tablas Maestras (Sólo UUID)
                master_tables = ["subjects", "grades", "buildings", "roles", "permissions", "break_config", "lunch_config"]
                for table in master_tables:
                    logger.info(f"Purgando tabla maestra: {table}")
                    safe_drop(cur, table, "legacy_id")
                    safe_drop(cur, table, "uid")

                # 2. Tablas Transaccionales (Híbridas)
                trans_tables = ["teachers", "users", "lessons", "cards", "schedule_sessions", "observations", "rpt_planilla", "classes"]
                for table in trans_tables:
                    logger.info(f"Limpiando residuos en tabla transaccional: {table}")
                    safe_drop(cur, table, "uid")
                
                # 3. Transformación de Tablas XML (Integer -> UUID)
                xml_tables = ["xml_uploads", "xml_upload_logs", "xml_change_logs"]
                for table in xml_tables:
                    logger.info(f"Transformando tabla XML a UUID: {table}")
                    if column_exists(cur, table, "id") and not column_exists(cur, table, "legacy_id"):
                        # PASO CRÍTICO: Drop existing PK before rename/add
                        cur.execute(f"ALTER TABLE {table} DROP CONSTRAINT IF EXISTS {table}_pkey CASCADE;")
                        cur.execute(f"ALTER TABLE {table} RENAME COLUMN id TO legacy_id;")
                        cur.execute(f"ALTER TABLE {table} ADD COLUMN id UUID PRIMARY KEY DEFAULT gen_random_uuid();")
                    
                    # Sincronizar FKs en logs
                    if table in ["xml_upload_logs", "xml_change_logs"]:
                         if column_exists(cur, table, "upload_id") and not column_exists(cur, table, "legacy_upload_id"):
                             cur.execute(f"ALTER TABLE {table} RENAME COLUMN upload_id TO legacy_upload_id;")
                             cur.execute(f"ALTER TABLE {table} ADD COLUMN upload_id UUID;")
                             cur.execute(f"UPDATE {table} t SET upload_id = x.id FROM xml_uploads x WHERE t.legacy_upload_id = x.legacy_id;")

                logger.info("--- PURGA FÍSICA COMPLETADA CON ÉXITO ---")
                conn.commit()

    except Exception as e:
        logger.error(f"FALLO CRÍTICO EN PURGA: {e}")
        raise

if __name__ == "__main__":
    execute_final_purge()
