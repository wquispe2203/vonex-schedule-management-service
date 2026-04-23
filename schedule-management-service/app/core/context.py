from contextvars import ContextVar

# Variable de contexto para rastrear el ID de la solicitud en todos los hilos/corutinas
request_id_ctx: ContextVar[str] = ContextVar("request_id", default="n/a")
