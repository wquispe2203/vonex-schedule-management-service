import requests
import json

BASE_URL = "http://localhost:8000"

def verify_abanto_schedule():
    # 1. Get Abanto's ID
    res = requests.get(f"{BASE_URL}/api/schedule/teachers")
    teachers = res.json()["data"]
    teacher = next((t for t in teachers if "ABANTO HERRERA" in t["last_name"].upper()), None)
    
    if not teacher:
        print("Docente ABANTO HERRERA no encontrado.")
        return

    teacher_id = teacher["id"]
    print(f"Verificando para Docente: {teacher['first_name']} {teacher['last_name']} (ID: {teacher_id})")
    
    # Rango de prueba (Semana de Marzo)
    start_date = "2026-03-09"
    end_date = "2026-03-15"
    
    res = requests.get(f"{BASE_URL}/api/schedule/teacher/{teacher_id}?start_date={start_date}&end_date={end_date}")
    data = res.json()
    
    if not data["success"]:
        print("Error en el API:", data)
        return
        
    sessions = data["data"]
    total_hours = sum(s.get("horas_dictadas", 0) for s in sessions if not s.get("is_break"))
    
    print(f"Total sesiones encontradas: {len(sessions)}")
    print(f"Total Horas Dictadas (Sumatoria): {total_hours}")
    
    for s in sessions:
        if not s.get("is_break"):
            obs_str = ", ".join([o["type"] for o in s.get("observations", [])])
            print(f"[{s['date']}] {s['start_time']}-{s['end_time']} | {s['subject']} | Repl: {s['is_replacement']} | Obs: {obs_str} | Hours: {s['horas_dictadas']}")

    if abs(total_hours - 26.0) < 0.01:
        print("✅ TOTAL HORAS CORRECTO: 26.00")
    else:
        print(f"❌ TOTAL HORAS INCORRECTO: {total_hours} (Esperado 26.00)")

if __name__ == "__main__":
    verify_abanto_schedule()
