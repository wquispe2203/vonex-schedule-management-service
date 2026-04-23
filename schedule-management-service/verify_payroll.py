from app.database import SessionLocal
from app.models import RptPlanilla, RptPlanillaLog, Teacher, ClassGroup, Subject, Lesson, ScheduleSession
from app.services.xml_upload import XMLUploadService
from datetime import date, time

def verify_payroll():
    db = SessionLocal()
    service = XMLUploadService()
    
    print("--- Verificando Tabla RptPlanilla ---")
    count = db.query(RptPlanilla).count()
    print(f"Total registros en RptPlanilla: {count}")
    
    print("\n--- Verificando Tabla RptPlanillaLog ---")
    log_count = db.query(RptPlanillaLog).count()
    print(f"Total registros en RptPlanillaLog: {log_count}")
    
    # Probar lógica de transformación aislada
    print("\n--- Probando Transformación de Datos ---")
    test_aula = "SMINT1025P1A"
    sede = service._get_sede(test_aula)
    print(f"Aula: {test_aula} -> Sede: {sede} (Esperado: LIMA CERCADO)")
    
    test_curso = "ALGEBRA(E0)"
    curso_clean = service._clean_curso(test_curso)
    print(f"Curso: {test_curso} -> Limpio: {curso_clean} (Esperado: ALGEBRA)")
    
    h_inicio = time(8, 0)
    h_fin = time(11, 40)
    horas = service._calculate_hours(h_inicio, h_fin)
    print(f"Horas: {h_inicio} a {h_fin} -> {horas} horas (Esperado: ~3.67)")

    db.close()

if __name__ == "__main__":
    verify_payroll()
