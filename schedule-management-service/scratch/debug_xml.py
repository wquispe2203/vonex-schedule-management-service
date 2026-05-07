
import os
import sys
from uuid import uuid4
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.services.xml_upload import XMLUploadService
from app.models.base import Base

def debug_xml_processing(file_path, start_date, end_date):
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    service = XMLUploadService()
    try:
        print(f"--- DEBUGGING XML: {file_path} ---")
        # No queremos persistir realmente en este debug si es posible, 
        # pero process_upload hace commits. 
        # Usaremos un try/finally con rollback si queremos evitar basura, 
        # pero el usuario quiere ver por qué falla.
        
        result = service.process_upload(
            db=db,
            file_path=file_path,
            start_date=start_date,
            end_date=end_date,
            overwrite=True,
            user_id=uuid4(),
            original_filename="DEBUG_FILE.xml"
        )
        print("RESULT:", result)
    except Exception as e:
        print("ERROR:", str(e))
        import traceback
        traceback.print_exc()
    finally:
        # Hacemos rollback para no ensuciar la DB de producción si el script corre ahí
        db.rollback()
        db.close()

if __name__ == "__main__":
    # Usar uno de los archivos encontrados en el listado previo
    xml_file = "storage/xml_uploads/asctt2012.xml" 
    if not os.path.exists(xml_file):
        print(f"File not found: {xml_file}")
        sys.exit(1)
    
    debug_xml_processing(xml_file, "2026-03-01", "2026-03-31")
