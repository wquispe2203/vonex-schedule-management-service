from app.core.database import SessionLocal
from app.models import RptPlanilla, Lesson, ScheduleSession, XmlUpload
from app.modules.reportes.service import get_planilla_data, process_rpt_logic
from datetime import date, time
from sqlalchemy import text
import math
import logging

# Disable logging to keep stdout clean
logging.getLogger("app.modules.reportes.service").setLevel(logging.ERROR)
logging.getLogger("app.services.session_consolidator").setLevel(logging.ERROR)

def run():
    out_file = "scratch/audit_rpt_math_results.txt"
    with open(out_file, "w", encoding="utf-8") as f:
        f.write("====================================================\n")
        f.write("      FORENSIC MATHEMATICAL AUDIT: RPT PLANILLAS     \n")
        f.write("====================================================\n")
        
        db = SessionLocal()
        try:
            start_date = date(2026, 3, 1)
            end_date = date(2026, 3, 31)
            
            db_records = db.query(RptPlanilla).filter(
                RptPlanilla.fecha_clase >= start_date,
                RptPlanilla.fecha_clase <= end_date
            ).all()
            
            f.write(f"Total physical RptPlanilla records in March 2026: {len(db_records)}\n")
            db_total_dictadas = sum(float(r.horas_dictadas or 0.0) for r in db_records)
            f.write(f"DB Persisted Totals: dictadas={db_total_dictadas:.2f}\n")
            
            # API Totals
            api_res = get_planilla_data(db, start_date, end_date, page=1, limit=10000)
            api_data = api_res["data"]
            api_total_hours = api_data["total_hours_sum"]
            api_total_receso_count = api_data["total_receso_count"]
            processed_blocks = api_data["data"]
            
            f.write(f"API Returned Totals: total_hours_sum={api_total_hours:.2f}, total_receso_count={api_total_receso_count:.1f}, total_blocks={len(processed_blocks)}\n")
            
            # B. DISTRIBUTION OF DECIMALS IN PERSISTED HOURS
            decimal_distribution = {}
            for r in db_records:
                h = float(r.horas_dictadas or 0.0)
                dec = round(h - math.floor(h), 2)
                decimal_distribution[dec] = decimal_distribution.get(dec, 0) + 1
                
            f.write("\nDecimal Distribution in persisted 'horas_dictadas' in DB:\n")
            for dec, count in sorted(decimal_distribution.items()):
                f.write(f"  - Decimal part .{int(dec*100):02d}: {count} records\n")
                
            # C. DISTRIBUTION OF DECIMALS IN CONSOLIDATED BLOCKS (API level)
            decimal_distribution_api = {}
            for b in processed_blocks:
                h = float(b["horas_dictadas"] or 0.0)
                dec = round(h - math.floor(h), 2)
                decimal_distribution_api[dec] = decimal_distribution_api.get(dec, 0) + 1
                
            f.write("\nDecimal Distribution in API consolidated 'horas_dictadas':\n")
            for dec, count in sorted(decimal_distribution_api.items()):
                f.write(f"  - Decimal part .{int(dec*100):02d}: {count} records\n")
                
            # D. Examples of records with decimal parts in API consolidated list
            f.write("\nExamples of consolidated blocks causing decimals:\n")
            examples_count = 0
            for b in processed_blocks:
                h = float(b["horas_dictadas"] or 0.0)
                dec = round(h - math.floor(h), 2)
                if dec in (0.2, 0.4, 0.6, 0.8) and examples_count < 10:
                    f.write(f"  - Docente: '{b['docente']}', Sede: '{b['sede']}', Curso: '{b['curso']}', Fecha: {b['fecha_clase']}, Timing: {b['hora_inicio']}-{b['hora_fin']}, Horas: {b['horas_dictadas']}\n")
                    examples_count += 1
                    
            # E. DETAILED MATHEMATICAL RECONSTRUCTION OF 5 REPRESENTATIVE TEACHERS
            teachers_dict = {}
            for r in db_records:
                teachers_dict[r.docente] = teachers_dict.get(r.docente, 0) + 1
                
            sorted_teachers = sorted(teachers_dict.items(), key=lambda x: x[1], reverse=True)
            # Select 5 diverse teachers
            target_teachers = [
                "CARLOS DANIEL PALOMINO LESCANO",
                "NILTON CESAR CASTILLO JAYME",
                "VICTOR ANGEL CARDENAS HUAYTAYA",
                "DAN NEIL SANTIAGO SAAVEDRA LEANO",
                "SHEILLA EVELYN BARRETO GONZALES"
            ]
            
            f.write("\n====================================================\n")
            f.write("     STEP-BY-STEP RECONSTRUCTION FOR 5 TEACHERS      \n")
            f.write("====================================================\n")
            
            for name in target_teachers:
                f.write(f"\n>>> Teacher: {name}\n")
                t_records = [r for r in db_records if r.docente == name]
                f.write(f"Total database records: {len(t_records)}\n")
                
                # Let's call process_rpt_logic specifically for this teacher
                t_processed = process_rpt_logic(db, t_records, start_date, end_date, target_docente=name)
                f.write(f"Total consolidated blocks: {len(t_processed)}\n")
                
                total_persisted_h = sum(float(r.horas_dictadas or 0.0) for r in t_records)
                total_processed_h = sum(float(b["horas_dictadas"]) for b in t_processed)
                total_processed_r = sum(float(b["receso"]) for b in t_processed)
                
                f.write(f"Summary: Persisted Hours={total_persisted_h:.2f}\n")
                f.write(f"Summary: Processed Hours={total_processed_h:.2f}, Processed Recess={total_processed_r:.2f}\n")
                
                # Reconstruct first 3 blocks step-by-step
                for idx, b in enumerate(t_processed[:3]):
                    f.write(f"\n  Block #{idx+1}:\n")
                    f.write(f"    - Date: {b['fecha_clase']}\n")
                    f.write(f"    - Sede: {b['sede']}, Curso: {b['curso']}, Ciclo: {b['ciclo']}\n")
                    f.write(f"    - Timing: {b['hora_inicio']} to {b['hora_fin']}\n")
                    
                    # Get difference in minutes
                    from app.services.session_consolidator import get_time_diff_minutes
                    mins = get_time_diff_minutes(b['hora_inicio'], b['hora_fin'])
                    raw_hours = mins / 50.0
                    normalized_hours = round(raw_hours, 2)
                    
                    f.write(f"    - Raw Minutes: {mins} mins\n")
                    f.write(f"    - Academic Hours Formula: {mins} mins / 50 = {raw_hours:.4f} academic hours\n")
                    f.write(f"    - Processed/Normalized Hours: {normalized_hours:.2f} academic hours\n")
                    f.write(f"    - Recess Value: {b['receso']:.2f}\n")
                    
                    if b.get("is_replacement"):
                        f.write(f"    - Replacement Status: YES (Replaced {b.get('titular_original')})\n")
                    if b.get("observation"):
                        f.write(f"    - Observation: {b['observation']}\n")
                        
        finally:
            db.close()
            
    print(f"Audit completed! Results written to {out_file}")

if __name__ == "__main__":
    run()
