from app.core.database import SessionLocal
from app.models import RptPlanilla, Lesson, ScheduleSession, XmlUpload
from app.modules.reportes.service import get_planilla_data, process_rpt_logic
from datetime import date, time
from sqlalchemy import text
import math

def run():
    print("====================================================")
    print("      FORENSIC MATHEMATICAL AUDIT: RPT PLANILLAS     ")
    print("====================================================")
    db = SessionLocal()
    try:
        # A. GENERAL DATABASE METRICS FOR MARCH 2026
        start_date = date(2026, 3, 1)
        end_date = date(2026, 3, 31)
        
        # We query the DB directly first
        db_records = db.query(RptPlanilla).filter(
            RptPlanilla.fecha_clase >= start_date,
            RptPlanilla.fecha_clase <= end_date
        ).all()
        
        print(f"Total physical RptPlanilla records in March 2026: {len(db_records)}")
        db_total_dictadas = sum(float(r.horas_dictadas or 0.0) for r in db_records)
        print(f"DB Persisted Totals: dictadas={db_total_dictadas:.2f}")
        
        # Let's simulate calling get_planilla_data to see what the API returns in total
        api_res = get_planilla_data(db, start_date, end_date, page=1, limit=10000)
        api_data = api_res["data"]
        api_total_hours = api_data["total_hours_sum"]
        api_total_receso_count = api_data["total_receso_count"]
        processed_blocks = api_data["data"]
        
        print(f"API Returned Totals: total_hours_sum={api_total_hours:.2f}, total_receso_count={api_total_receso_count:.1f}, total_blocks={len(processed_blocks)}")
        
        # B. DISTRIBUTION OF DECIMALS IN PERSISTED HOURS
        decimal_distribution = {}
        for r in db_records:
            h = float(r.horas_dictadas or 0.0)
            dec = round(h - math.floor(h), 2)
            decimal_distribution[dec] = decimal_distribution.get(dec, 0) + 1
            
        print("\nDecimal Distribution in persisted 'horas_dictadas' in DB:")
        for dec, count in sorted(decimal_distribution.items()):
            print(f"  - Decimal part .{int(dec*100):02d}: {count} records")
            
        # C. DISTRIBUTION OF DECIMALS IN CONSOLIDATED BLOCKS (API level)
        decimal_distribution_api = {}
        for b in processed_blocks:
            h = float(b["horas_dictadas"] or 0.0)
            dec = round(h - math.floor(h), 2)
            decimal_distribution_api[dec] = decimal_distribution_api.get(dec, 0) + 1
            
        print("\nDecimal Distribution in API consolidated 'horas_dictadas':")
        for dec, count in sorted(decimal_distribution_api.items()):
            print(f"  - Decimal part .{int(dec*100):02d}: {count} records")
            
        # D. CAUSE OF DECIMALS ANALYSIS
        # Let's print unique names in db_records to see if they use commas
        unique_db_names = list({r.docente for r in db_records})
        print(f"\nTotal unique teacher names in RptPlanilla: {len(unique_db_names)}")
        print("Sample unique names in DB:")
        for name in sorted(unique_db_names)[:10]:
            print(f"  - '{name}'")
            
        # E. DETAILED MATHEMATICAL RECONSTRUCTION OF 5 REPRESENTATIVE TEACHERS
        # Let's choose 5 teachers who actually exist in unique_db_names
        # Let's see: CARLOS DANIEL PALOMINO LESCANO is a perfect choice
        # Let's pick 5 names from the sorted list
        teachers_dict = {}
        for r in db_records:
            teachers_dict[r.docente] = teachers_dict.get(r.docente, 0) + 1
            
        sorted_teachers = sorted(teachers_dict.items(), key=lambda x: x[1], reverse=True)
        target_teachers = [t[0] for t in sorted_teachers[:5]]
        
        print("\n====================================================")
        print("     STEP-BY-STEP RECONSTRUCTION FOR 5 TEACHERS      ")
        print("====================================================")
        
        for name in target_teachers:
            print(f"\n>>> Teacher: {name}")
            t_records = [r for r in db_records if r.docente == name]
            print(f"Total database records: {len(t_records)}")
            
            # Let's call process_rpt_logic specifically for this teacher
            t_processed = process_rpt_logic(db, t_records, start_date, end_date, target_docente=name)
            print(f"Total consolidated blocks: {len(t_processed)}")
            
            total_persisted_h = sum(float(r.horas_dictadas or 0.0) for r in t_records)
            total_processed_h = sum(float(b["horas_dictadas"]) for b in t_processed)
            total_processed_r = sum(float(b["receso"]) for b in t_processed)
            
            print(f"Summary: Persisted Hours={total_persisted_h:.2f}")
            print(f"Summary: Processed Hours={total_processed_h:.2f}, Processed Recess={total_processed_r:.2f}")
            
            # Reconstruct first 3 blocks step-by-step
            for idx, b in enumerate(t_processed[:3]):
                print(f"\n  Block #{idx+1}:")
                print(f"    - Date: {b['fecha_clase']}")
                print(f"    - Sede: {b['sede']}, Curso: {b['curso']}, Ciclo: {b['ciclo']}")
                print(f"    - Timing: {b['hora_inicio']} to {b['hora_fin']}")
                
                # Get difference in minutes
                from app.services.session_consolidator import get_time_diff_minutes
                mins = get_time_diff_minutes(b['hora_inicio'], b['hora_fin'])
                raw_hours = mins / 50.0
                normalized_hours = round(raw_hours, 2)
                
                print(f"    - Raw Minutes: {mins} mins")
                print(f"    - Academic Hours Formula: {mins} mins / 50 = {raw_hours:.4f} academic hours")
                print(f"    - Processed/Normalized Hours: {normalized_hours:.2f} academic hours")
                print(f"    - Recess Value: {b['receso']:.2f}")
                
                if b.get("is_replacement"):
                    print(f"    - Replacement Status: YES (Replaced {b.get('titular_original')})")
                if b.get("observation"):
                    print(f"    - Observation: {b['observation']}")
                    
    finally:
        db.close()

if __name__ == "__main__":
    run()
