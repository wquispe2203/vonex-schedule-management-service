import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Configuración - Tomada de app/database.py
DATABASE_URL = "postgresql://postgres:C%40rden4s2k24@localhost/schedule_db"
SQL_FILE = os.path.join(os.path.dirname(__file__), "migration_fase1_uuid.sql")

def run_migration():
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    print(f"Leyendo script: {SQL_FILE}")
    try:
        with open(SQL_FILE, 'r', encoding='utf-8') as f:
            sql_script = f.read()

        print("Iniciando migracion Fase 1...")
        
        connection = engine.raw_connection()
        try:
            cursor = connection.cursor()
            cursor.execute(sql_script)
            connection.commit()
            print("Migracion finalizada con exito.")
        finally:
            connection.close()

        # Generación de Reporte Post-Migración
        print("\nGENERANDO REPORTE POST-MIGRACION...")
        
        # Consultamos las estadísticas solicitadas
        total_migrated = session.execute(text("SELECT count(*) FROM teachers WHERE source = 'xml_unassigned'")).scalar()
        total_duplicates = session.execute(text("SELECT count(*) FROM teachers WHERE possible_duplicate = true")).scalar()
        total_teachers = session.execute(text("SELECT count(*) FROM teachers")).scalar()
        
        print(f"-------------------------------------------")
        print(f"Total Docentes Unificados (SinAsignar): {total_migrated}")
        print(f"Posibles Duplicados Detectados:        {total_duplicates}")
        print(f"Total General en Tabla Teachers:       {total_teachers}")
        print(f"Inconsistencias de Integridad:         0 (Validado por EXCEPTION)")
        print(f"-------------------------------------------")

    except Exception as e:
        print(f"ERROR CRITICO durante la ejecucion: {str(e)}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    run_migration()
