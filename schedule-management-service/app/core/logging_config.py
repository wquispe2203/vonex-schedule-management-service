import json
import logging
import sys
from datetime import datetime
from typing import Any

class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_record = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "name": record.name,
        }
        
        # Agregar información de excepción si existe
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
            
        # Agregar atributos extra si existen y no colisionan
        for key, value in record.__dict__.items():
            if key not in ["args", "asctime", "created", "exc_info", "exc_text", "filename", "funcName", "levelname", "levelno", "lineno", "module", "msecs", "message", "msg", "name", "pathname", "process", "processName", "relativeCreated", "stack_info", "thread", "threadName"]:
                log_record[key] = value

        return json.dumps(log_record)

def setup_logging():
    # Remover handlers existentes de la raíz
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Configurar el handler de consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(JSONFormatter())

    # Configuración base del root logger
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)

    # Silenciar logs ruidosos de terceros si es necesario
    logging.getLogger("uvicorn.error").handlers = [console_handler]
    logging.getLogger("uvicorn.access").handlers = [console_handler]
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING) # SQL logging se maneja por audit_logger
    return root_logger
