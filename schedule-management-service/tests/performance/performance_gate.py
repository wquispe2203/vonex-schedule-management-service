import subprocess
import json
import sys
import os

# Configuración de Thresholds (Fase 6.5)
THRESHOLDS = {
    "RPT": {"p95": 1000, "error_rate": 0.01},
    "XML": {"p95": 2000, "error_rate": 0.01}, # XML es más pesado
    "AUTH": {"p95": 500, "error_rate": 0.01}
}

def run_and_validate():
    print("[LOAD TEST START] Running Locust Headless...")
    cmd = [
        "locust",
        "-f", "tests/performance/locustfile.py",
        "--headless",
        "-u", "5",
        "-r", "1",
        "--run-time", "15s", # Reducido para rapidez en validación
        "--host", "http://localhost:8002",
        "--json"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"[PERFORMANCE GATE] ERROR: Locust exited with code {result.returncode}")
            print(result.stderr)
            sys.exit(1)
            
        # El JSON está en stdout
        data = json.loads(result.stdout)
        validate_data(data)
    except Exception as e:
        print(f"[PERFORMANCE GATE] CRITICAL ERROR: {str(e)}")
        sys.exit(1)

def validate_data(data):
    failed = False
    print("\n--- [PERFORMANCE GATE] VALIDATION ---")
    
    for entry in data:
        name = entry.get("name", "")
        if name == "Aggregated": continue
        
        p95 = entry.get("percentile_95", 0)
        error_count = entry.get("num_failures", 0)
        request_count = entry.get("num_requests", 1)
        error_rate = error_count / request_count
        
        target = None
        if "rpt-planilla" in name: target = THRESHOLDS["RPT"]
        elif "upload" in name: target = THRESHOLDS["XML"]
        elif "login" in name or "me" in name: target = THRESHOLDS["AUTH"]
        
        if target:
            status = "PASS"
            if p95 > target["p95"]:
                status = "FAIL (LATENCY)"
                failed = True
            if error_rate > target["error_rate"]:
                status = "FAIL (ERRORS)"
                failed = True
                
            print(f"[{status}] {name:30} | P95: {p95:4.0f}ms (Target: {target['p95']}ms) | Error: {error_rate:.2%}")

    if failed:
        print("\n[PERF REGRESSION DETECTED] Performance thresholds exceeded.")
        sys.exit(1)
    else:
        print("\n[LOAD TEST SUCCESS] All performance gates passed.")
        sys.exit(0)

if __name__ == "__main__":
    run_and_validate()
