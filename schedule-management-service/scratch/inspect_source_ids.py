from app.core.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    print("=== Complete Teacher Origin Audit ===")
    
    # 1. Group by source and format pattern of source_id
    res = db.execute(text("""
        SELECT 
            source,
            CASE 
                WHEN source_id LIKE 'EXCEL_%' THEN 'EXCEL_IMPORTED'
                WHEN source_id LIKE 'GHOST_%' THEN 'GHOST_TEACHER'
                WHEN source_id LIKE 'PROMOTED_%' THEN 'PROMOTED_TEACHER'
                WHEN source_id IS NULL THEN 'NULL_SOURCE_ID'
                ELSE 'OTHER_HEX_FORMAT'
            END as id_pattern,
            status,
            COUNT(*) as count
        FROM teachers
        GROUP BY source, id_pattern, status
        ORDER BY count DESC
    """)).fetchall()
    
    print("Source | Pattern | Status | Count")
    print("---------------------------------")
    for r in res:
        print(f"{r[0]} | {r[1]} | {r[2]} | {r[3]}")
        
    print("\n--- Detailed counts ---")
    total = db.execute(text("SELECT COUNT(*) FROM teachers")).scalar()
    excel_count = db.execute(text("SELECT COUNT(*) FROM teachers WHERE source_id LIKE 'EXCEL_%'")).scalar()
    manual_ghost = db.execute(text("SELECT COUNT(*) FROM teachers WHERE source_id LIKE 'GHOST_%'")).scalar()
    manual_promoted = db.execute(text("SELECT COUNT(*) FROM teachers WHERE source_id LIKE 'PROMOTED_%'")).scalar()
    manual_hex = db.execute(text("SELECT COUNT(*) FROM teachers WHERE source_id NOT LIKE 'EXCEL_%' AND source_id NOT LIKE 'GHOST_%' AND source_id NOT LIKE 'PROMOTED_%' AND source_id IS NOT NULL")).scalar()
    print(f"Total: {total}")
    print(f"Excel: {excel_count}")
    print(f"Ghost: {manual_ghost}")
    print(f"Promoted: {manual_promoted}")
    print(f"Hex ID (Legacy/Imported from XML): {manual_hex}")
    
finally:
    db.close()
