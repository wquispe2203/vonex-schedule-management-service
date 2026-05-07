from sqlalchemy import MetaData, text
from app.core.database import engine

def cleanup_database():
    print("--- Iniciando limpieza total de Base de Datos ---")
    metadata = MetaData()
    metadata.reflect(bind=engine)
    
    with engine.connect() as conn:
        trans = conn.begin()
        try:
            # Desactivar FK checks temporalmente para facilitar el drop si hay dependencias circulares
            conn.execute(text("DROP SCHEMA public CASCADE;"))
            conn.execute(text("CREATE SCHEMA public;"))
            conn.execute(text("GRANT ALL ON SCHEMA public TO postgres;"))
            conn.execute(text("GRANT ALL ON SCHEMA public TO public;"))
            
            trans.commit()
            print("--- [SUCCESS] Esquema 'public' recreado. Base de datos limpia. ---")
        except Exception as e:
            trans.rollback()
            print(f"--- [ERROR] Fallo en Cleanup: {e} ---")

if __name__ == "__main__":
    cleanup_database()
