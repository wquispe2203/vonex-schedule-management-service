from app.core.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    print("--- Table Counts ---")
    tables = db.execute(text("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
    """)).fetchall()
    for t in tables:
        t_name = t[0]
        cnt = db.execute(text(f"SELECT COUNT(*) FROM {t_name}")).scalar()
        print(f"Table: {t_name} | Count: {cnt}")
finally:
    db.close()
