from app.core.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    print("--- Teacher Source Info ---")
    sources = db.execute(text("SELECT DISTINCT source FROM teachers")).fetchall()
    print("Distinct sources in DB:")
    for s in sources:
        print(s)

    source_ids = db.execute(text("SELECT COUNT(*), source_id LIKE 'EXCEL_%' as is_excel, source_id LIKE 'XML_%' as is_xml, source_id IS NULL as is_null FROM teachers GROUP BY (source_id LIKE 'EXCEL_%'), (source_id LIKE 'XML_%'), (source_id IS NULL)")).fetchall()
    print("\nDistinct source_id formats in DB:")
    for si in source_ids:
        print(si)
finally:
    db.close()
