from app.database import SessionLocal
from sqlalchemy import text

def check():
    db = SessionLocal()
    rows = db.execute(text("SELECT * FROM break_config")).fetchall()
    for r in rows:
        print(r)
    db.close()

if __name__ == "__main__":
    check()
