import logging
import json
import datetime
import uuid
import sys
import os
from logging.handlers import RotatingFileHandler
from contextvars import ContextVar
from pathlib import Path

# --- CONFIGURATION ---
BASE_DIR = Path(__file__).resolve().parent.parent.parent
LOG_DIR = BASE_DIR / "ops" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# ContextVar for Trace ID (Thread-safe/Async-safe)
trace_id_var: ContextVar[str] = ContextVar("trace_id", default="N/A")
user_id_var: ContextVar[str] = ContextVar("user_id", default="ANONYMOUS")

# Log File Paths
BACKEND_LOG = LOG_DIR / "backend.log"
XML_LOG = LOG_DIR / "xml_pipeline.log"
SECURITY_LOG = LOG_DIR / "security.log"
RPT_LOG = LOG_DIR / "rpt_engine.log"

class JsonFormatter(logging.Formatter):
    def format(self, record):
        context = getattr(record, "context", {})
        log_record = {
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "trace_id": trace_id_var.get(),
            "user_id": user_id_var.get(),
            "module": record.name,
            "event": context.get("event", "GENERAL"),
            "message": record.getMessage(),
            "duration_ms": context.get("duration_ms", 0.0)
        }
        
        # Include extra context if not empty
        remaining_context = {k: v for k, v in context.items() if k not in ["event", "duration_ms"]}
        if remaining_context:
            log_record["context"] = remaining_context
            
        # Add exception info if present
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
            
        return json.dumps(log_record)

def setup_logger(name, log_file, level=logging.INFO):
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Prevent duplicate handlers
    if not logger.handlers:
        # Rotating File Handler (10MB per file, keep 5 backups)
        handler = RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5, encoding="utf-8")
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)
        
        # Console Handler
        console = logging.StreamHandler(sys.stdout)
        console.setFormatter(JsonFormatter())
        logger.addHandler(console)
        
    return logger

# Pre-defined Loggers
logger = setup_logger("backend", BACKEND_LOG)
xml_logger = setup_logger("xml_pipeline", XML_LOG)
security_logger = setup_logger("security", SECURITY_LOG)
rpt_logger = setup_logger("rpt_engine", RPT_LOG)

# --- UTILITIES ---

def set_trace_id(t_id=None):
    if not t_id:
        t_id = str(uuid.uuid4())
    token = trace_id_var.set(t_id)
    return t_id, token

def set_user_id(u_id):
    token = user_id_var.set(str(u_id))
    return token

def log_event(target_logger, level, event, message, context=None):
    extra = {"context": context or {}}
    extra["context"]["event"] = event
    
    if level.upper() == "INFO":
        target_logger.info(message, extra=extra)
    elif level.upper() == "ERROR":
        target_logger.error(message, extra=extra)
    elif level.upper() == "WARNING":
        target_logger.warning(message, extra=extra)
    elif level.upper() == "DEBUG":
        target_logger.debug(message, extra=extra)

# Initialization Logs
log_event(logger, "INFO", "[JSON LOGGER READY]", "Structured logging subsystem initialized")
log_event(logger, "INFO", "[OBSERVABILITY ACTIVE]", "Enterprise observability layer is now operational")

# Sanitization Helper (for privacy)
def sanitize_data(data):
    if not isinstance(data, dict):
        return data
    sensitive_keys = ["password", "token", "jwt", "access_token", "refresh_token", "cookie"]
    return {k: ("***" if k.lower() in sensitive_keys else v) for k, v in data.items()}
