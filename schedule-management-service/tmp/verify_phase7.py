import requests
import json

BASE_URL = "http://localhost:8000"

def test_teacher_schedule():
    # Buscamos al docente "VEGA MONTES" (sabemos que tiene reemplazos por la auditoría anterior)
    # Primero obtenemos su ID
    res = requests.get(f"{BASE_URL}/api/schedule/teachers")
    teachers = res.json()["data"]
    teacher = next((t for t in teachers if "VEGA MONTES" in t["last_name"].upper()), None)
    
    if not teacher:
        print("Docente VEGA MONTES no encontrado.")
        return

    teacher_id = teacher["id"]
    print(f"Probando para Docente: {teacher['first_name']} {teacher['last_name']} (ID: {teacher_id})")
    
    # Rango de prueba
    start_date = "2026-03-09"
    end_date = "2026-03-15"
    
    res = requests.get(f"{BASE_URL}/api/schedule/teacher/{teacher_id}?start_date={start_date}&end_date={end_date}")
    data = res.json()
    
    if not data["success"]:
        print("Error en el API:", data)
        return
        
    sessions = data["data"]
    print(f"Total sesiones encontradas: {len(sessions)}")
    
    replacements = [s for s in sessions if s.get("is_replacement")]
    print(f"Sesiones Marcadas como REEMPLAZO: {len(replacements)}")
    
    for r in replacements[:3]:
        print(f" - Reemplazo en {r['date']} {r['start_time']} - {r['end_time']} | Titular: {r['titular_name']} | Sede: {r['sede']}")
        
    has_receso = [s for s in sessions if s.get("receso", 0) > 0]
    print(f"Sesiones con receso > 0: {len(has_receso)}")
    if has_receso:
        print(f" - Ejemplo receso: {has_receso[0]['receso']}")

if __name__ == "__main__":
    test_teacher_schedule()
