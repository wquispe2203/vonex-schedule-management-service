from sqlalchemy.orm import Session
from typing import Optional, Any
from .repository import log_audit_action

def create_audit_log(db: Session, accion: str, modulo: str, registro_id: int, datos_antes: Optional[Any] = None, datos_despues: Optional[Any] = None, usuario_id: int = 1):
    """
    Wrapper del Domain de Auditoría. No exporta errores HTTP ni detiene
    las transacciones en curso. Es un "dispara y olvida".
    """
    print(f"AUDITORIA EJECUTADA: Intentando loguear {accion} en {modulo} {registro_id}")
    try:
        log_audit_action(
            accion=accion,
            modulo=modulo,
            registro_id=registro_id,
            datos_antes=datos_antes,
            datos_despues=datos_despues,
            usuario_id=usuario_id
        )
    except Exception as e:
        print(f"ERROR AUDITORIA (service layer): {str(e)}")

