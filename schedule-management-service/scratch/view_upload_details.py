from app.core.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    print("--- DETAILED UPLOADS STATS ---")
    rows = db.execute(text("SELECT id, filename, status, total_records, processed_records, error_summary, created_at FROM xml_uploads ORDER BY created_at DESC;")).fetchall()
    for r in rows:
        print(f"ID: {r[0]} | File: {r[1]} | Status: {r[2]} | Total: {r[3]} | Processed: {r[4]} | Created: {r[6]}")
        if r[5]:
            print(f"  Error Summary (truncated): {str(r[5])[:200]}")
finally:
    db.close()
