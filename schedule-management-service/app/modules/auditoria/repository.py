from sqlalchemy.orm import Session
from sqlalchemy import text
from app.models import AuditLog
from fastapi.encoders import jsonable_encoder
from typing import Optional, Any
import traceback
from app.database import SessionLocal

def log_audit_action(accion: str, modulo: str, registro_id: int, datos_antes: Optional[Any], datos_despues: Optional[Any], usuario_id: int):
    """
    Inserta un registro de auditoría en una transacción INDEPENDIENTE.
    """
    print(f"--- [AUDITORIA] INICIANDO REGISTRO: {accion} en {modulo} ID {registro_id} ---")
    db = SessionLocal()
    try:
        print("DB AUDITORIA:", db.bind.url)
        
        antes_json = jsonable_encoder(datos_antes) if datos_antes else None
        despues_json = jsonable_encoder(datos_despues) if datos_despues else None
        
        print(f"--- [AUDITORIA] SERIALIZACION OK. Insertando en DB... ---")
        
        audit = AuditLog(
            usuario_id=usuario_id,
            accion=accion,
            modulo=modulo,
            registro_id=registro_id,
            datos_antes=antes_json,
            datos_despues=despues_json
        )
        db.add(audit)
        
        print("ANTES DEL COMMIT")
        db.commit()
        print("DESPUÉS DEL COMMIT")
        
        # Confirmación de inserción real
        result = db.execute(text("SELECT COUNT(*) FROM audit_logs"))
        print("TOTAL REGISTROS AUDITORIA:", result.scalar())
        
    except Exception as e:
        db.rollback()
        print(f"ERROR AUDITORIA (Causa Raíz SQL/JSON): {str(e)}")
        traceback.print_exc()
    finally:
        db.close()
