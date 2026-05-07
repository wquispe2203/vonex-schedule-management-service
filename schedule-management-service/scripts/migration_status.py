
from sqlalchemy import create_engine, text
from app.core.config import settings

def run_migration():
    engine = create_engine(settings.database_url)
    with engine.connect() as conn:
        print("Agregando columna 'status' a la tabla 'teachers'...")
        try:
            conn.execute(text("ALTER TABLE teachers ADD COLUMN status VARCHAR(50) DEFAULT 'ACTIVO'"))
            conn.commit()
            print("Columna 'status' agregada.")
        except Exception as e:
            print(f"Aviso: {e}")
        
        print("Indexando columna 'status'...")
        try:
            conn.execute(text("CREATE INDEX ix_teachers_status ON teachers (status)"))
            conn.commit()
            print("Índice creado.")
        except Exception as e:
            print(f"Aviso: {e}")

        print("Clasificando registros existentes...")
        # Marcar como INCOMPLETO los que no tienen DNI
        conn.execute(text("UPDATE teachers SET status = 'INCOMPLETO' WHERE dni IS NULL OR dni = ''"))
        # Marcar como ACTIVO los que sí tienen (default ya es ACTIVO, pero por si acaso)
        conn.execute(text("UPDATE teachers SET status = 'ACTIVO' WHERE dni IS NOT NULL AND dni != ''"))
        conn.commit()
        print("Clasificación inicial completada.")

if __name__ == "__main__":
    run_migration()
