import psycopg
import logging
from app.database import SQLALCHEMY_DATABASE_URL

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("grand_swap")

def column_exists(cur, table, column):
    cur.execute(f"SELECT 1 FROM information_schema.columns WHERE table_name='{table}' AND column_name='{column}'")
    return cur.fetchone() is not None

def get_column_type(cur, table, column):
    cur.execute(f"SELECT data_type FROM information_schema.columns WHERE table_name='{table}' AND column_name='{column}'")
    res = cur.fetchone()
    return res[0] if res else None

def execute_grand_swap():
    conn_str = SQLALCHEMY_DATABASE_URL.replace("postgresql://", "postgresql://")
    
    try:
        with psycopg.connect(conn_str) as conn:
            with conn.cursor() as cur:
                logger.info("--- INICIANDO EL GRAN SWAP DE IDENTIDAD (MODO RESILIENTE) ---")
                
                tables_to_migrate = ["teachers", "users", "classes", "subjects", "lessons", "observations", "schedule_sessions"]

                for table in tables_to_migrate:
                    logger.info(f"Evaluando tabla: {table}")
                    
                    # 1. ¿Ya tiene legacy_id?
                    has_legacy = column_exists(cur, table, "legacy_id")
                    id_type = get_column_type(cur, table, "id")
                    
                    if id_type == 'integer' and not has_legacy:
                        logger.info(f"  -> Renombrando ID (int) a legacy_id en {table}")
                        cur.execute(f"ALTER TABLE {table} DROP CONSTRAINT IF EXISTS {table}_pkey CASCADE;")
                        cur.execute(f"ALTER TABLE {table} RENAME COLUMN id TO legacy_id;")
                    
                    # 2. ¿Tiene uid que deba ser id?
                    has_uid = column_exists(cur, table, "uid")
                    if has_uid:
                        logger.info(f"  -> Promoviendo UID a ID (uuid) en {table}")
                        if column_exists(cur, table, "id"):
                            # Si 'id' ya existe (porque el rename anterior falló a mitad), validamos tipo
                            if get_column_type(cur, table, "id") == 'uuid':
                                logger.info(f"  -> ID ya es UUID en {table}, ignorando rename de UID.")
                            else:
                                logger.warning(f"  -> Conflicto de columnas en {table}. Revisión manual sugerida.")
                        else:
                            cur.execute(f"ALTER TABLE {table} RENAME COLUMN uid TO id;")
                    
                    # 3. Asegurar Primary Key
                    if column_exists(cur, table, "id"):
                        cur.execute(f"ALTER TABLE {table} DROP CONSTRAINT IF EXISTS {table}_pkey CASCADE;")
                        cur.execute(f"ALTER TABLE {table} ADD PRIMARY KEY (id);")

                # ─── SINCRONIZACIÓN DE CLAVES FORÁNEAS (MODO RESILIENTE) ───
                logger.info("Sincronizando Claves Foráneas...")

                # LESSONS
                if column_exists(cur, "lessons", "subject_id"):
                    if get_column_type(cur, "lessons", "subject_id") == 'integer':
                        cur.execute("ALTER TABLE lessons RENAME COLUMN subject_id TO legacy_subject_id;")
                        cur.execute("ALTER TABLE lessons ADD COLUMN subject_id UUID;")
                
                if column_exists(cur, "lessons", "class_id"):
                    if get_column_type(cur, "lessons", "class_id") == 'integer':
                        cur.execute("ALTER TABLE lessons RENAME COLUMN class_id TO legacy_class_id;")
                        cur.execute("ALTER TABLE lessons ADD COLUMN class_id UUID;")

                if column_exists(cur, "lessons", "teacher_id"):
                    if get_column_type(cur, "lessons", "teacher_id") == 'integer':
                        cur.execute("ALTER TABLE lessons RENAME COLUMN teacher_id TO legacy_teacher_id;")
                        cur.execute("ALTER TABLE lessons ADD COLUMN teacher_id UUID;")

                # Poblar UUID FKs en Lessons
                cur.execute("UPDATE lessons l SET subject_id = s.id FROM subjects s WHERE l.legacy_subject_id = s.legacy_id AND l.subject_id IS NULL;")
                cur.execute("UPDATE lessons l SET class_id = c.id FROM classes c WHERE l.legacy_class_id = c.legacy_id AND l.class_id IS NULL;")
                cur.execute("UPDATE lessons l SET teacher_id = t.id FROM teachers t WHERE l.legacy_teacher_id = t.legacy_id AND l.teacher_id IS NULL;")

                # OBSERVATIONS
                logger.info("Sincronizando Claves Foráneas en Observations...")
                for col in ["teacher_id", "user_id", "replacement_teacher_id"]:
                    if column_exists(cur, "observations", col):
                        if get_column_type(cur, "observations", col) == 'integer':
                            cur.execute(f"ALTER TABLE observations RENAME COLUMN {col} TO legacy_{col};")
                            cur.execute(f"ALTER TABLE observations ADD COLUMN {col} UUID;")
                
                cur.execute("UPDATE observations o SET teacher_id = t.id FROM teachers t WHERE o.legacy_teacher_id = t.legacy_id AND o.teacher_id IS NULL;")
                cur.execute("UPDATE observations o SET user_id = u.id FROM users u WHERE o.legacy_user_id = u.legacy_id AND o.user_id IS NULL;")
                cur.execute("UPDATE observations o SET replacement_teacher_id = t.id FROM teachers t WHERE o.legacy_replacement_teacher_id = t.legacy_id AND o.replacement_teacher_id IS NULL;")

                logger.info("--- EL GRAN SWAP (RESILIENTE) HA SIDO COMPLETADO ---")
                conn.commit()

    except Exception as e:
        logger.error(f"FALLO CRÍTICO EN EL SWAP: {e}")
        raise

if __name__ == "__main__":
    execute_grand_swap()
