import os
import sys
from sqlalchemy import create_engine, text

db_url = "postgresql://postgres:C%40rden4s2k24@localhost:5432/schedule_db"
print(f"Attempting to connect to Postgres: {db_url}")

try:
    engine = create_engine(db_url)
    with engine.connect() as conn:
        print("[OK] Successfully connected to Postgres!")
        
        tables = ['users', 'roles', 'teachers', 'xml_uploads', 'schedule_sessions', 'rpt_planilla']
        for t in tables:
            try:
                result = conn.execute(text(f"SELECT COUNT(*) FROM {t}"))
                count = result.scalar()
                print(f"Table '{t}': {count} records")
            except Exception as e:
                print(f"Table '{t}' read failed: {e}")
                
        print("\n--- SAMPLE XML UPLOADS ---")
        try:
            res = conn.execute(text("SELECT id, filename, start_date, end_date FROM xml_uploads ORDER BY created_at DESC LIMIT 3"))
            for r in res.fetchall():
                print(r)
        except Exception as e:
            print(f"Failed: {e}")

        print("\n--- SAMPLE TEACHERS (Top 5) ---")
        try:
            res = conn.execute(text("SELECT id, name, short_name FROM teachers LIMIT 5"))
            for r in res.fetchall():
                print(r)
        except Exception as e:
            print(f"Failed: {e}")
            
except Exception as err:
    print(f"[ERROR] FAILED to connect to Postgres! Error: {err}")
