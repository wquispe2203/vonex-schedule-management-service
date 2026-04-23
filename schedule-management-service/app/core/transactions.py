import time
import logging
import functools
from sqlalchemy.exc import InternalError, OperationalError

logger = logging.getLogger(__name__)

def with_retry_on_deadlock(max_retries: int = 3, initial_delay: float = 0.5):
    """
    Decorador para reintentar transacciones que fallan por Deadlocks o Lock Timeouts.
    Usa backoff exponencial.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            delay = initial_delay
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except (InternalError, OperationalError) as e:
                    # Verificar si es un error de deadlock o lock timeout (PostgreSQL)
                    # 40P01: DEADLOCK DETECTED
                    # 55P03: LOCK NOT AVAILABLE
                    err_msg = str(e).upper()
                    if "DEADLOCK" in err_msg or "SERIALIZATION" in err_msg or "LOCK NOT AVAILABLE" in err_msg:
                        retries += 1
                        if retries >= max_retries:
                            logger.error(f"MDM_CRITICAL: Máximo de reintentos ({max_retries}) alcanzado tras Deadlock.")
                            raise
                        
                        logger.warning(f"MDM_RETRY: Deadlock detectado. Reintento {retries}/{max_retries} en {delay}s...")
                        time.sleep(delay)
                        delay *= 2 # Backoff exponencial
                    else:
                        # Si no es un error de concurrencia reintentable, propagar
                        raise
            return func(*args, **kwargs)
        return wrapper
    return decorator
