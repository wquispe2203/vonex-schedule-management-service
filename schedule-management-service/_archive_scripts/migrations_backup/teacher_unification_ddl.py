import psycopg
from app.database import SQLALCHEMY_DATABASE_URL

def final_teacher_schema_fix():
    conn_str = SQLALCHEMY_DATABASE_URL.replace("postgresql://", "postgresql://")
    try:
        with psycopg.connect(conn_str) as conn:
            with conn.cursor() as cur:
                print("--- UNIFICANDO ESQUEMA DE DOCENTES (DDL) ---")
                
                # Columnas de integración
                cur.execute("ALTER TABLE teachers ADD COLUMN IF NOT EXISTS is_assigned BOOLEAN DEFAULT TRUE;")
                cur.execute("ALTER TABLE teachers ADD COLUMN IF NOT EXISTS times_detected INTEGER DEFAULT 0;")
                cur.execute("ALTER TABLE teachers ADD COLUMN IF NOT EXISTS last_seen_at TIMESTAMP WITH TIME ZONE;")
                cur.execute("ALTER TABLE teachers ADD COLUMN IF NOT EXISTS source CHARACTER VARYING;")
                cur.execute("ALTER TABLE teachers ADD COLUMN IF NOT EXISTS possible_match_id UUID REFERENCES teachers(id) ON DELETE SET NULL;")
                
                print("  [SUCCESS] Tabla 'teachers' actualizada exitosamente.")
                conn.commit()
    except Exception as e:
        print(f"  [ERROR] Fallo en la actualización DDL: {e}")
        raise

if __name__ == "__main__":
    final_teacher_schema_fix()
