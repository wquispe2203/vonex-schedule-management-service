from app.core.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    print("=== OBSERVATIONS INTEGRITY AUDIT ===")
    
    # 1. Group by observation types
    types = db.execute(text("SELECT type, COUNT(*) FROM observations GROUP BY type")).fetchall()
    print("Observations by type:")
    for t in types:
        print(f"Type: {t[0]} | Count: {t[1]}")
        
    # 2. Reemplazos activos
    replacements = db.execute(text("""
        SELECT COUNT(*) 
        FROM observations 
        WHERE replacement_teacher_id IS NOT NULL OR replacement_teacher_name IS NOT NULL
    """)).scalar()
    print(f"Observations with replacements (teacher_id or name): {replacements}")
    
    # Let's see some example observations with replacement teachers
    rep_details = db.execute(text("""
        SELECT id, type, replacement_teacher_id, replacement_teacher_name 
        FROM observations 
        WHERE replacement_teacher_id IS NOT NULL OR replacement_teacher_name IS NOT NULL 
        LIMIT 5
    """)).fetchall()
    print("Example replacements:")
    for rd in rep_details:
        print(f"ID: {rd[0]} | Type: {rd[1]} | RepID: {rd[2]} | RepName: {rd[3]}")
        
    # 3. Reference to teachers
    obs_ref_teachers = db.execute(text("""
        SELECT COUNT(DISTINCT teacher_id) 
        FROM observations
    """)).scalar()
    print(f"Distinct primary teachers referenced in observations: {obs_ref_teachers}")
    
    obs_ref_rep_teachers = db.execute(text("""
        SELECT COUNT(DISTINCT replacement_teacher_id) 
        FROM observations 
        WHERE replacement_teacher_id IS NOT NULL
    """)).scalar()
    print(f"Distinct replacement teachers referenced in observations: {obs_ref_rep_teachers}")
    
    # 4. Are there any observations associated with Excel-imported teachers?
    obs_excel_primary = db.execute(text("""
        SELECT COUNT(*) 
        FROM observations o 
        JOIN teachers t ON o.teacher_id = t.id 
        WHERE t.source_id LIKE 'EXCEL_%'
    """)).scalar()
    print(f"Observations where primary teacher is EXCEL-imported: {obs_excel_primary}")
    
    obs_excel_replacement = db.execute(text("""
        SELECT COUNT(*) 
        FROM observations o 
        JOIN teachers t ON o.replacement_teacher_id = t.id 
        WHERE t.source_id LIKE 'EXCEL_%'
    """)).scalar()
    print(f"Observations where replacement teacher is EXCEL-imported: {obs_excel_replacement}")
    
finally:
    db.close()
