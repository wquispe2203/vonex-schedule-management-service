import pytest
from app.services.session_consolidator import consolidate_sessions
from datetime import time, date

@pytest.mark.benchmark
def test_consolidate_sessions_benchmark(benchmark):
    """
    BENCHMARK: Motor de Consolidación RPT.
    Valida el performance de la lógica O(N) optimizada con Hash Maps.
    """
    # Generar carga sintética: 1000 sesiones para un docente en un día
    test_data = []
    for i in range(1000):
        # 08:00 -> 08:50, 08:50 -> 09:40, etc... 
        # (Simulamos bloques contiguos para forzar el merge)
        start_m = (8 * 60) + (i * 50)
        end_m = start_m + 50
        
        test_data.append({
            "fecha_clase": date(2026, 3, 2),
            "hora_inicio": time((start_m // 60) % 24, start_m % 60),
            "hora_fin": time((end_m // 60) % 24, end_m % 60),
            "horas_dictadas": 1.0,
            "docente": "BENCHMARK, DOCENTE",
            "sede": "LIMA",
            "curso": "TEST",
            "ciclo": "C1",
            "is_replacement": False,
            "obs_type": "NORMAL"
        })

    def run_consolidation():
        return consolidate_sessions(
            test_data,
            date_key="fecha_clase",
            start_time_key="hora_inicio",
            end_time_key="hora_fin",
            hours_key="horas_dictadas",
            group_fields=["docente", "sede", "curso", "ciclo", "is_replacement", "obs_type"]
        )

    # Ejecutar benchmark
    result = benchmark(run_consolidation)
    
    # Validación de integridad post-benchmark
    assert len(result) > 0
