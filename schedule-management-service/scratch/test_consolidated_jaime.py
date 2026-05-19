from app.core.database import SessionLocal
from app.modules.reportes.service import process_rpt_logic
from app.models import RptPlanilla
from datetime import date

db = SessionLocal()
try:
    # Obtener registros RPT de Jaime Asencio para el 2026-03-03
    records = db.query(RptPlanilla).filter(
        RptPlanilla.fecha_clase == date(2026, 3, 3),
        RptPlanilla.docente.like("%JAIME ASENCIO%")
    ).all()
    
    print(f"Total registros RPT encontrados: {len(records)}")
    
    # Procesar reporte
    result = process_rpt_logic(db, records, date(2026, 3, 3), date(2026, 3, 3))
    
    print("\n--- RESULTADOS DEL REPORTE CONSOLIDADO RPT ---")
    for row in result:
        print(f"Docente: {row.get('docente')} | Tipo: {row.get('obs_type', 'NORMAL')} | Sede: {row.get('sede')} | Curso: {row.get('curso')} | Inicio: {row.get('hora_inicio')} | Fin: {row.get('hora_fin')} | Horas: {row.get('horas_dictadas')} | Receso: {row.get('receso')}")
finally:
    db.close()
