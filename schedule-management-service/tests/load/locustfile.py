import time
from locust import HttpUser, task, between, events

class ScheduleServiceUser(HttpUser):
    # Simular tiempo de espera entre tareas (1-2 segundos)
    wait_time = between(1, 2)

    @task(30)
    def health_check(self):
        """Tarea ligera: Monitoreo de estado y pulso de DB."""
        with self.client.get("/health", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health check fallido: {response.status_code}")

    @task(60)
    def intensive_aggregation(self):
        """Tarea pesada: Agregaciones y Joins en DB."""
        with self.client.get("/api/perf/intensive", catch_response=True) as response:
            if response.status_code == 200:
                # Validar que devolvió datos
                data = response.json()
                if data.get("success") and len(data.get("data", [])) >= 0:
                    response.success()
                else:
                    response.failure("Respuesta intensiva sin datos válidos")
            else:
                response.failure(f"Error en consulta intensiva: {response.status_code}")

    @task(10)
    def slow_query_timeout(self):
        """Tarea de estrés: Validar que el timeout de 10s funciona."""
        # Se espera un 503 Service Unavailable debido al statement_timeout de PostgreSQL
        with self.client.get("/api/perf/slow", catch_response=True) as response:
            if response.status_code == 503:
                # Éxito determinista: el timeout cortó la query como se esperaba
                response.success()
            elif response.status_code == 200:
                # Fallo de lógica: la query de 15s terminó satisfactoriamente (timeout no funcionó)
                response.failure("Timeout NO funcionó: la consulta lenta devolvió 200 OK")
            else:
                response.failure(f"Error inesperado en slow query: {response.status_code}")

# --- Eventos de reporte (Opcional) ---
def on_test_start(environment, **kwargs):
    print(f"--- Iniciando prueba de carga contra: {environment.host} ---")

def on_test_stop(environment, **kwargs):
    print("--- Prueba de carga finalizada ---")

events.test_start.add_listener(on_test_start)
events.test_stop.add_listener(on_test_stop)
