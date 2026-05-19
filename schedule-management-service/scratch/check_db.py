import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
db_url = os.getenv('DATABASE_URL')
test_db_url = os.getenv('TEST_DATABASE_URL')
testing = os.getenv('TESTING', 'False').lower() == 'true'

active_url = test_db_url if testing else db_url
print(f"DEBUG: Testing={testing}")
print(f"DEBUG: Active URL={active_url}")

for name, url in [("PRODUCTION", db_url), ("TEST", test_db_url)]:
    print(f"\n--- CHECKING {name} DB ---")
    if not url:
        print("URL not set.")
        continue
    try:
        engine = create_engine(url)
        with engine.connect() as conn:
            res = conn.execute(text("SELECT count(*) FROM teachers"))
            print(f"COUNT_TEACHERS: {res.fetchone()[0]}")
            
            res = conn.execute(text("SELECT status, count(*) FROM teachers GROUP BY status"))
            print(f"STATUS_DISTRIBUTION: {res.fetchall()}")
            
            res = conn.execute(text("SELECT count(*) FROM teachers WHERE dni IS NOT NULL AND dni != ''"))
            print(f"COUNT_WITH_DNI: {res.fetchone()[0]}")
            
            res = conn.execute(text("SELECT id, filename, status, start_date, end_date FROM xml_uploads"))
            uploads = res.fetchall()
            print(f"COUNT_XML: {len(uploads)}")
            for u in uploads:
                print(f"  - {u.filename}: {u.status} ({u.start_date} to {u.end_date})")
    except Exception as e:
        print(f"ERROR: {str(e)}")
