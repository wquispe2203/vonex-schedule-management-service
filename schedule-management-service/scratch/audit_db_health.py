from app.core.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    print("=== DATABASE HEALTH & INTEGRITY AUDIT ===")
    
    # 1. Check for orphaned observations (if any)
    orphan_obs = db.execute(text("""
        SELECT COUNT(*) 
        FROM observations o 
        LEFT JOIN teachers t ON o.teacher_id = t.id 
        WHERE t.id IS NULL
    """)).scalar()
    print(f"Orphaned observations (no primary teacher): {orphan_obs}")
    
    # 2. Check for orphaned lessons
    orphan_lessons = db.execute(text("""
        SELECT COUNT(*) 
        FROM lessons l 
        LEFT JOIN teachers t ON l.teacher_id = t.id 
        WHERE t.id IS NULL AND l.teacher_id IS NOT NULL
    """)).scalar()
    print(f"Orphaned lessons (no teacher): {orphan_lessons}")
    
    # 3. Check for active database constraints & index status
    # In PostgreSQL, we can check for duplicate entries that might violate future unique index additions
    print("\n--- Unique constraint duplicates check ---")
    
    # Check for DNI duplicates in teachers (excluding incomplete/nulls)
    dni_dups = db.execute(text("""
        SELECT dni, COUNT(*) 
        FROM teachers 
        WHERE dni IS NOT NULL AND status = 'ACTIVO'
        GROUP BY dni 
        HAVING COUNT(*) > 1
    """)).fetchall()
    print(f"Duplicate DNIs in active teachers: {len(dni_dups)}")
    
    # Check for normalized name duplicates
    norm_dups = db.execute(text("""
        SELECT normalized_name, COUNT(*) 
        FROM teachers 
        WHERE normalized_name IS NOT NULL AND status = 'ACTIVO'
        GROUP BY normalized_name 
        HAVING COUNT(*) > 1
    """)).fetchall()
    print(f"Duplicate normalized_names in active teachers: {len(norm_dups)}")
    
    # Check for source_id duplicates
    source_dups = db.execute(text("""
        SELECT source_id, COUNT(*) 
        FROM teachers 
        WHERE source_id IS NOT NULL
        GROUP BY source_id 
        HAVING COUNT(*) > 1
    """)).fetchall()
    print(f"Duplicate source_ids in teachers: {len(source_dups)}")
    
finally:
    db.close()
