import sqlite3
import os
import sys

# Añadir el path base para importar el motor de DB si fuera necesario
# Pero para migrations simples de SQLite/PG usamos comandos directos.

def migrate():
    # En este entorno se usa uvicorn/sqlalchemy, asumimos PostgreSQL o SQLite según el repo.
    # Detectamos la BD:
    # (En este caso, basado en la estructura de carpetas y el uso de SQLAlchemy con uvicorn)
    # Si es SQLite:
    db_path = "app/test.db" 
    if os.path.exists(db_path):
        print(f"Migrating SQLite DB: {db_path}")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("ALTER TABLE teachers_sinasignar ADD COLUMN is_possible_duplicate BOOLEAN DEFAULT FALSE;")
            cursor.execute("ALTER TABLE teachers_sinasignar ADD COLUMN possible_match_id INTEGER;")
            conn.commit()
            print("Migration v3 successful (SQLite).")
        except Exception as e:
            print(f"Migration error (could be already migrated): {e}")
        finally:
            conn.close()
    else:
        # Si es PostgreSQL (asumido por el stack), el usuario debería ejecutar una migración manual 
        # o puedo intentar usar el motor de sqlalchemy.
        print("DATABASE_URL no encontrada en entorno simple. Por favor ejecute:")
        print("ALTER TABLE teachers_sinasignar ADD COLUMN is_possible_duplicate BOOLEAN DEFAULT FALSE;")
        print("ALTER TABLE teachers_sinasignar ADD COLUMN possible_match_id INTEGER REFERENCES teachers(id) ON DELETE SET NULL;")

if __name__ == "__main__":
    migrate()
