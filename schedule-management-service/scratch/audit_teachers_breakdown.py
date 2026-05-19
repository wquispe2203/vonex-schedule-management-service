from app.core.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    print("--- Teacher Status Breakdown ---")
    status_breakdown = db.execute(text("""
        SELECT status, COUNT(*), COUNT(DISTINCT dni) as unique_dnis, COUNT(*) FILTER (WHERE dni IS NULL) as null_dnis
        FROM teachers
        GROUP BY status
    """)).fetchall()
    for s in status_breakdown:
        print(s)

    print("\n--- Teacher Merge Info ---")
    merge_info = db.execute(text("""
        SELECT 
            (merged_into_id IS NOT NULL) as is_merged, 
            COUNT(*) 
        FROM teachers 
        GROUP BY (merged_into_id IS NOT NULL)
    """)).fetchall()
    for m in merge_info:
        print(m)

    print("\n--- Top 10 duplicate DNI teachers ---")
    dups = db.execute(text("""
        SELECT dni, COUNT(*), string_agg(last_name || ' ' || first_name, ' | ') 
        FROM teachers 
        WHERE dni IS NOT NULL
        GROUP BY dni 
        HAVING COUNT(*) > 1
        LIMIT 10
    """)).fetchall()
    for d in dups:
        print(d)
finally:
    db.close()
